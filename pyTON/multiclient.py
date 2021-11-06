from pathlib import Path
from .client import TonlibClient, b64str_bytes, b64str_str, b64str_hex, h2b64
import random
import inspect
import copy
import asyncio
import time
from datetime import datetime

from aiocache import cached, Cache

def current_function_name():
  return inspect.stack()[1].function

async def drop_awaited_exceptions(crts):
        for tsk in crts:
            try:
                await tsk
            except Exception as e:
                pass

async def drop_pending(crts):
  for tsk in crts:
    tsk.cancel()

async def handle_coroutines(done, pending):
  await drop_awaited_exceptions(done)
  await drop_pending(pending)

class TonlibMultiClient:
    def __init__(self, loop, config, keystore, cdll_path=None):
        self.loop = loop
        self.config = config
        self.keystore = keystore
        self.all_clients = []
        self.cdll_path = cdll_path
        self.current_consensus_block = 0
        self.stats = {}
        self.archive_stats = {}

    async def init_tonlib(self):
        '''
          Try to init as many tonlib clients as there are liteservers in config
        '''
        for i,ls in enumerate(self.config["liteservers"]):
          c = copy.deepcopy(self.config)
          c["liteservers"] = [ls]
          keystore = self.keystore + str(i)
          Path(keystore).mkdir(parents=True, exist_ok=True)
          client = TonlibClient(self.loop, c, keystore=keystore, cdll_path=self.cdll_path)
          client.is_working = False
          client.is_archival = False
          self.all_clients.append(client)
        done, pending = await asyncio.wait( [ i.init_tonlib() for i in self.all_clients] )
        await handle_coroutines(done, pending)
        self.loop_task = asyncio.ensure_future(self.checking_loop(), loop=self.loop)

    def print_stats(self):
        print(time.time(), datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%SZ'))
        for i in self.stats:
            print(i, self.stats[i])

    async def checking_loop(self):
        mandatory_check = True
        while True:
            ts = time.time()
            await self.detect_working()
            #if mandatory_check or not (int(ts) % 600):
            #  await self.detect_archival()
            #  mandatory_check = False
            nts = time.time()
            if nts-ts<1:
              await asyncio.sleep(1+ts-nts)

    async def detect_working(self):
      last_blocks = {}
      async def f(l):
        result = await self.all_clients[l].getMasterchainInfo()
        #print(result)
        last_blocks[l] = result["last"]["seqno"]
      done, pending = await asyncio.wait( [ f(i) for i in range(len(self.all_clients))], timeout= 1.3)
      await handle_coroutines(done, pending)
      if not len(last_blocks):
        return
      best_block = max([last_blocks[i] for i in last_blocks])
      consensus_block = 0
      #detect 'consensus':
      # it is no more than 3 blocks less than best block
      # at least 60% of ls know it
      # it is not earlier than prev
      strats = [ sum([1 if last_blocks[ls]==(best_block-i) else 0 for ls in last_blocks]) for i in range(4)]
      total_suitable = sum(strats)
      sm=0
      for i, am in enumerate(strats):
        sm += am
        if sm >= total_suitable*0.6:
          consensus_block = best_block - i
          break
      if consensus_block >= self.current_consensus_block:
        self.current_consensus_block = consensus_block
      for i in range(len(self.all_clients)):
        self.all_clients[i].is_working = last_blocks.get(i,0) >= self.current_consensus_block

    async def detect_archival(self):
      success = {}
      async def f(l):
        result = await self.all_clients[l].getBlockTransactions( -1, -9223372036854775808, 2)
        success[l] = result["ok"] == True
      done, pending = await asyncio.wait( [ f(i) for i in range(len(self.all_clients))], timeout= 2)
      await handle_coroutines(done, pending)
      for i in range(len(self.all_clients)):
        self.all_clients[i].is_archival = success.get(i, False)

    async def dispatch_request(self, method, *args, **kwargs):
      self.stats[method] = self.stats.get(method,0) + 1
      self.archive_stats[0] = self.archive_stats.get(0,0) + 1
      client = random.choice([cl for cl in self.all_clients if cl.is_working])
      client.consensus_block = self.current_consensus_block
      result =  await client.__getattribute__(method)(*args, **kwargs)
      return result

    async def dispatch_archive_request(self, method, *args, **kwargs):
      self.stats[method] = self.stats.get(method,0) + 1
      self.archive_stats[1] = self.archive_stats.get(1,0) + 1
      clnts = [cl for cl in self.all_clients if cl.is_working and cl.is_archival]
      if not len(clnts):
        clnts = [cl for cl in self.all_clients if cl.is_working]
      client = random.choice(clnts)
      client.consensus_block = self.current_consensus_block
      return await client.__getattribute__(method)(*args, **kwargs)

    @cached(ttl=5, cache=Cache.MEMORY)
    async def raw_get_transactions(self, account_address: str, from_transaction_lt: str, from_transaction_hash: str, archival: bool):
        if archival:
          return await self.dispatch_archive_request(current_function_name(), account_address, from_transaction_lt, from_transaction_hash)
        else:
          return await self.dispatch_request(current_function_name(), account_address, from_transaction_lt, from_transaction_hash)

    @cached(ttl=15, cache=Cache.MEMORY)
    async def get_transactions(self, account_address, from_transaction_lt=None, from_transaction_hash=None, to_transaction_lt=0, limit = 10, archival = False):
      """
       Return all transactions between from_transaction_lt and to_transaction_lt
       if to_transaction_lt and to_transaction_hash are not defined returns all transactions
       if from_transaction_lt and from_transaction_hash are not defined checks last
      """
      method = "get_transactions"
      self.stats[method] = self.stats.get(method,0) + 1
      if (from_transaction_lt==None) or (from_transaction_hash==None):
        addr = await self.raw_get_account_state(account_address)
        if '@type' in addr and addr['@type']=="error":
          addr = await self.raw_get_account_state(account_address)
        if '@type' in addr and addr['@type']=="error":
          raise Exception(addr["message"])
        try:
          from_transaction_lt, from_transaction_hash = int(addr["last_transaction_id"]["lt"]), b64str_hex(addr["last_transaction_id"]["hash"])
        except KeyError:
          raise Exception("Can't get last_transaction_id data")
      reach_lt = False
      all_transactions = []
      current_lt, curret_hash = from_transaction_lt, from_transaction_hash
      while (not reach_lt) and (len(all_transactions)<limit):
        raw_transactions = await self.raw_get_transactions(account_address, current_lt, curret_hash, archival)
        if(raw_transactions['@type']) == 'error':
          break
          #TODO probably we should chenge get_transactions API
          #if 'message' in raw_transactions['message']:
          #  raise Exception(raw_transactions['message'])
          #else:
          #  raise Exception("Can't get transactions")
        transactions, next = raw_transactions['transactions'], raw_transactions.get("previous_transaction_id", None)
        for t in transactions:
          tlt = int(t['transaction_id']['lt'])
          if tlt <= to_transaction_lt:
            reach_lt = True
            break
          all_transactions.append(t)
        if next:
          current_lt, curret_hash = int(next["lt"]), b64str_hex(next["hash"])
        else:
          break
        if current_lt==0:
          break
      for t in all_transactions:
        try:
          if "in_msg" in t:
            if "source" in t["in_msg"]:
              t["in_msg"]["source"] = t["in_msg"]["source"]["account_address"]
            if "destination" in t["in_msg"]:
              t["in_msg"]["destination"] = t["in_msg"]["destination"]["account_address"]
            try:
              if "msg_data" in t["in_msg"]:
                msg_cell_boc = codecs.decode(codecs.encode(t["in_msg"]["msg_data"]["body"],'utf8'), 'base64')
                message_cell = deserialize_boc(msg_cell_boc)
                msg = message_cell.data.data.tobytes()
                t["in_msg"]["message"] = codecs.decode(codecs.encode(msg,'base64'), "utf8")
            except:
              t["in_msg"]["message"]=""
          if "out_msgs" in t:
            for o in t["out_msgs"]:
              if "source" in o:
                o["source"] = o["source"]["account_address"]
              if "destination" in o:
                o["destination"] = o["destination"]["account_address"]
              try:
                if "msg_data" in o:
                  msg_cell_boc = codecs.decode(codecs.encode(o["msg_data"]["body"],'utf8'), 'base64')
                  message_cell = deserialize_boc(msg_cell_boc)
                  msg = message_cell.data.data.tobytes()
                  o["message"] = codecs.decode(codecs.encode(msg,'base64'), "utf8")
              except:
                 o["message"]=""
        except Exception as e:
          print("getTransaction exception", e)
      return all_transactions

    @cached(ttl=5, cache=Cache.MEMORY)
    async def raw_get_account_state(self, address: str):
        return await self.dispatch_request(current_function_name(), address)
    @cached(ttl=5, cache=Cache.MEMORY)
    async def generic_get_account_state(self, address: str):
        return await self.dispatch_request(current_function_name(), address)
    @cached(ttl=5, cache=Cache.MEMORY)
    async def raw_run_method(self, address, method, stack_data, output_layout=None):
        return await self.dispatch_request(current_function_name(), address, method, stack_data, output_layout)
    async def raw_send_message(self, serialized_boc):
        method = "rew_send_message"
        self.stats[method] = self.stats.get(method,0) + 1
        working = [cl for cl in self.all_clients if cl.is_working]
        async def f(cl):
          return await cl.raw_send_message(serialized_boc)
        done, pending = await asyncio.wait( [ f(cl) for cl in random.sample(working, min(4, len(working)))], timeout = 5)
        for i in done:
          try:
            return await i
          except:
            pass
    async def _raw_create_query(self, destination, body, init_code=b'', init_data=b''):
        return await self.dispatch_request(current_function_name(), destination, body, init_code, init_data)
    async def _raw_send_query(self, query_info): 
        return await self.dispatch_request(current_function_name(), query_info)
    async def raw_create_and_send_query(self, destination, body, init_code=b'', init_data=b''):
        return await self.dispatch_request(current_function_name(), destination, body, init_code, init_data)
    async def raw_create_and_send_message(self, destination, body, initial_account_state=b''):
        return await self.dispatch_request(current_function_name(), destination, body, initial_account_state)
    @cached(ttl=5, cache=Cache.MEMORY)
    async def raw_estimate_fees(self, destination, body, init_code=b'', init_data=b'', ignore_chksig=True):
        return await self.dispatch_request(current_function_name(), destination, body, init_code, init_data, ignore_chksig)
    @cached(ttl=1, cache=Cache.MEMORY)
    async def getMasterchainInfo(self):
        return await self.dispatch_request(current_function_name())
    @cached(ttl=600, cache=Cache.MEMORY)
    async def lookupBlock(self, workchain, shard, seqno=None, lt=None, unixtime=None):
        if workchain == -1 and seqno and self.current_consensus_block - master_seqno < 2000:
          return await self.dispatch_request(current_function_name(), workchain, shard, seqno, lt, unixtime)
        else:
          return await self.dispatch_archive_request(current_function_name(), workchain, shard, seqno, lt, unixtime)
    @cached(ttl=600, cache=Cache.MEMORY)
    async def getShards(self, master_seqno):
        if self.current_consensus_block - master_seqno > 2000:
          return await self.dispatch_archive_request(current_function_name(), master_seqno)
        else:
          return await self.dispatch_request(current_function_name(), master_seqno)
    @cached(ttl=600, cache=Cache.MEMORY)
    async def raw_getBlockTransactions(self, fullblock, count, after_tx):
        return await self.dispatch_archive_request(current_function_name(), fullblock, count, after_tx)
    @cached(ttl=600, cache=Cache.MEMORY)
    async def getBlockTransactions(self, workchain, shard, seqno, root_hash=None, file_hash=None, count=None, after_lt=None, after_hash=None):
      method = "getBlockTransactions"
      self.stats[method] = self.stats.get(method,0) + 1
      fullblock={}
      if root_hash and file_hash:
        fullblock = {
          '@type':'ton.blockIdExt',
          'workchain':workchain,
          'shard':shard,
          'seqno':seqno,
          'root_hash':root_hash,
          'file_hash':file_hash
        }
      else:
        fullblock = await self.lookupBlock(workchain, shard, seqno)
        if fullblock.get('@type', 'error') == 'error':
          return fullblock
      after_tx = {
        '@type':'blocks.accountTransactionId',
        'account':after_hash if after_hash else 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=',
        'lt':after_lt if after_lt else 0
      }
      total_result = None
      incomplete = True
      req_count = count if count else 40
      while incomplete:
        result = await self.raw_getBlockTransactions(fullblock, req_count, after_tx)
        if not total_result:
          total_result = result
        else:
          total_result["transactions"]+=result["transactions"]
          total_result["incomplete"] = result["incomplete"]
        incomplete = result["incomplete"]
        if incomplete:
          after_tx['account'] = result["transactions"][-1]["account"]
          after_tx['lt'] = result["transactions"][-1]["lt"]
      # TODO automatically check incompleteness and download all txes
      for tx in total_result["transactions"]:
        try:
          tx["account"] = "%d:%s"%(result["id"]["workchain"],b64str_hex(tx["account"]))
        except:
          pass
      return total_result

    @cached(ttl=600, cache=Cache.MEMORY)
    async def getBlockHeader(self, workchain, shard, seqno, root_hash=None, file_hash=None):
        if workchain == -1 and seqno and self.current_consensus_block - master_seqno < 2000:
          return await self.dispatch_request(current_function_name(), workchain, shard, seqno, root_hash, file_hash)
        else: 
          return await self.dispatch_archive_request(current_function_name(), workchain, shard, seqno, root_hash, file_hash)

    @cached(ttl=600, cache=Cache.MEMORY)
    async def tryLocateTxByOutcomingMessage(self, source, destination, creation_lt):
          return await self.dispatch_archive_request(current_function_name(),  source, destination, creation_lt)

    @cached(ttl=600, cache=Cache.MEMORY)
    async def tryLocateTxByIncomingMessage(self, source, destination, creation_lt):
          return await self.dispatch_archive_request(current_function_name(),  source, destination, creation_lt)

