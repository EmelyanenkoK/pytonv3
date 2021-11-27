from .client import TonlibClient
from .address_utils import detect_address as _detect_address, prepare_address as _prepare_address
from .wallet_utils import wallets as known_wallets, sha256
import json, asyncio
from aiohttp import web
import base64, argparse, os, codecs

import importlib.resources
from tvm_valuetypes.cell import deserialize_cell_from_object
import warnings, traceback

default_config = {
  "liteservers": [
    {
      "ip": 1137658550,
      "port": 4924,
      "id": {
        "@type": "pub.ed25519",
        "key": "peJTw/arlRfssgTuf9BMypJzqOi7SXEqSPSWiEw2U1M="
      }
    },
    {
      "ip": 84478511,
      "port": 19949,
      "id": {
        "@type": "pub.ed25519",
        "key": "n4VDnSCUuSpjnCyUk9e3QOOd6o0ItSWYbTnW3Wnn8wk="
      }
    },
    {
      "ip": 84478479,
      "port": 48014,
      "id": {
        "@type": "pub.ed25519",
        "key": "3XO67K/qi+gu3T9v8G2hx1yNmWZhccL3O7SoosFo8G0="
      }
    },
    {
      "ip": -2018135749,
      "port": 53312,
      "id": {
        "@type": "pub.ed25519",
        "key": "aF91CuUHuuOv9rm2W5+O/4h38M3sRm40DtSdRxQhmtQ="
      }
    },
    {
      "ip": -2018145068,
      "port": 13206,
      "id": {
        "@type": "pub.ed25519",
        "key": "K0t3+IWLOXHYMvMcrGZDPs+pn58a17LFbnXoQkKc2xw="
      }
    },
    {
      "ip": -2018145059,
      "port": 46995,
      "id": {
        "@type": "pub.ed25519",
        "key": "wQE0MVhXNWUXpWiW5Bk8cAirIh5NNG3cZM1/fSVKIts="
      }
    },
    {
      "ip": 868462740,
      "port": 4194,
      "id": {
        "@type": "pub.ed25519",
        "key": "8sEr/sw8EmFyuJaOQlbNbT0IKj8NtoCsFw5052hVvHw="
      }
    },
    {
      "ip": 1091931625,
      "port": 30131,
      "id": {
        "@type": "pub.ed25519",
        "key": "wrQaeIFispPfHndEBc0s0fx7GSp8UFFvebnytQQfc6A="
      }
    },
    {
      "ip": 1091931590,
      "port": 47160,
      "id": {
        "@type": "pub.ed25519",
        "key": "vOe1Xqt/1AQ2Z56Pr+1Rnw+f0NmAA7rNCZFIHeChB7o="
      }
    },
    {
      "ip": 1091931623,
      "port": 17728,
      "id": {
        "@type": "pub.ed25519",
        "key": "BYSVpL7aPk0kU5CtlsIae/8mf2B/NrBi7DKmepcjX6Q="
      }
    },
    {
      "ip": 1091931589,
      "port": 13570,
      "id": {
        "@type": "pub.ed25519",
        "key": "iVQH71cymoNgnrhOT35tl/Y7k86X5iVuu5Vf68KmifQ="
      }
    },
    {
      "ip": -1539021362,
      "port": 52995,
      "id": {
        "@type": "pub.ed25519",
        "key": "QnGFe9kihW+TKacEvvxFWqVXeRxCB6ChjjhNTrL7+/k="
      }
    },
    {
      "ip": -1539021936,
      "port": 20334,
      "id": {
        "@type": "pub.ed25519",
        "key": "gyLh12v4hBRtyBygvvbbO2HqEtgl+ojpeRJKt4gkMq0="
      }
    },
    {
      "ip": -1136338705,
      "port": 19925,
      "id": {
        "@type": "pub.ed25519",
        "key": "ucho5bEkufbKN1JR1BGHpkObq602whJn3Q3UwhtgSo4="
      }
    },
    {
      "ip": 868465979,
      "port": 52888,
      "id": {
        "@type": "pub.ed25519",
        "key": "MhrcOEIlxMNe34cfb4GMmMl0OoPKe3HSDGl8miK5rRU="
      }
    },
    {
      "ip": 868466060,
      "port": 48621,
      "id": {
        "@type": "pub.ed25519",
        "key": "z0eg+Dll54aUJFc8WvU8CZP6CUKPqUcra+zJLxti5wU="
      }
    },
    {
      "ip": -2018147130,
      "port": 53560,
      "id": {
        "@type": "pub.ed25519",
        "key": "NlYhh/xf4uQpE+7EzgorPHqIaqildznrpajJTRRH2HU="
      }
    },
    {
      "ip": -2018147075,
      "port": 46529,
      "id": {
        "@type": "pub.ed25519",
        "key": "jLO6yoooqUQqg4/1QXflpv2qGCoXmzZCR+bOsYJ2hxw="
      }
    }
  ],
  "validator": {
    "@type": "validator.config.global",
    "zero_state": {
      "workchain": -1,
      "shard": -9223372036854775808,
      "seqno": 0,
      "root_hash": "F6OpKZKqvqeFp6CQmFomXNMfMj2EnaUSOXN+Mh+wVWk=",
      "file_hash": "XplPz01CXAps5qeSWUtxcyBfdAo5zVb1N979KLSKD24="
    },
    "init_block": {
      "root_hash": "irEt9whDfgaYwD+8AzBlYzrMZHhrkhSVp3PU1s4DOz4=",
      "seqno": 10171687,
      "file_hash": "lay/bUKUUFDJXU9S6gx9GACQFl+uK+zX8SqHWS9oLZc=",
      "workchain": -1,
      "shard": -9223372036854775808
    },
    "hardforks": [
      {
        "file_hash": "t/9VBPODF7Zdh4nsnA49dprO69nQNMqYL+zk5bCjV/8=",
        "seqno": 8536841,
        "root_hash": "08Kpc9XxrMKC6BF/FeNHPS3MEL1/Vi/fQU/C9ELUrkc=",
        "workchain": -1,
        "shard": -9223372036854775808
      }
    ]
  }
}

async def main(loop):
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p', default=8000, type=int)
    parser.add_argument('--getmethods', '-g', default=False, type=bool)
    parser.add_argument('--jsonrpc', '-j', default=True, type=bool)
    parser.add_argument('--liteserverconfig', '-l', default=None, type=str)
	parser.add_argument('--libtonlibjson', '-b', default=None, type=str)
    args = parser.parse_args()
    port = args.port
	libtonlibjson = args.libtonlibjson
    routes = web.RouteTableDef()
    lite_server_config = default_config
    if args.liteserverconfig:
      try:
        with open(args.liteserverconfig, "r") as f:
          lite_server_config = json.loads(f.read())
      except Exception as e:
        print("Can't read provided lite_server_config (%s): %s", args.liteserverconfig, str(e))

    keystore= os.path.expanduser('ton_keystore')
    if not os.path.exists(keystore):
        os.makedirs(keystore)
    tonlib = TonlibClient(loop, lite_server_config, keystore, libtonlibjson)
    await tonlib.init_tonlib()

    def detect_address(address):
        try:
            return _detect_address(address)
        except:
            raise web.HTTPRequestRangeNotSatisfiable()

    def prepare_address(address):
        try:
            return _prepare_address(address)
        except:
            raise web.HTTPRequestRangeNotSatisfiable()

    def wrap_result(func, high_timeout = False):
      cors_origin_header = ("Access-Control-Allow-Origin", "*")
      cors_headers_header = ("Access-Control-Allow-Headers", "*")
      headers = [cors_origin_header, cors_headers_header]
      async def wrapper(*args, **kwargs):
        try:
          return web.json_response( { "ok": True, "result": await asyncio.wait_for(func(*args, **kwargs), 100 if high_timeout else 5) }, headers=headers)
        except Exception as e:
          try:
            traceback.print_exc()
            return web.json_response( { "ok": False, "code": e.status_code if hasattr(e,"status_code") else None,"error": str(e) }, headers=headers)
          except:
            warnings.warn("Unknown exception", SyntaxWarning)
            traceback.print_exc()
            return web.json_response( { "ok": False, "error": str(e) }, headers=headers)
      return wrapper

    json_rpc_methods = {}

    def json_rpc(method, style='post'):
      def g(func):
        async def f(request):
          if isinstance(request, web.Request):
            return await func(request)
          pseudo_request = request
          response = await func(pseudo_request)
          if pseudo_request._id:
            data = json.loads(response.text)
            data.update({'id':pseudo_request._id})
            response.text = json.dumps(data)
          return response
        json_rpc_methods[method] = (f, style)
        return f
      return g

    def address_state(account_info):
      if isinstance(account_info.get("code",""), int) or len(account_info.get("code","")) == 0:
        if len(account_info.get("frozen_hash","")) == 0:
          return "uninitialized"
        else:
          return "frozen"
      return "active"

    @routes.get('/')
    async def index(request):
        with importlib.resources.path('pyTON.webserver', 'index.html') as path:
          return web.FileResponse(path)

    @routes.get('/application.js')
    async def index_js(request):
        with importlib.resources.path('pyTON.webserver', 'application.js') as path:
          return web.FileResponse(path)

    @routes.get('/application.css')
    async def index_css(request):
        with importlib.resources.path('pyTON.webserver', 'application.css') as path:
          return web.FileResponse(path)


    @routes.get('/getAddressInformation')
    @json_rpc('getAddressInformation', 'get')
    @wrap_result
    async def getAddressInformation(request):
      address = prepare_address(request.query['address'])
      result = await tonlib.raw_get_account_state(address)
      result["state"] = address_state(result)
      if "balance" in result and int(result["balance"])<0:
        result["balance"] = 0
      return result

    @routes.get('/getExtendedAddressInformation')
    @json_rpc('getExtendedAddressInformation', 'get')
    @wrap_result
    async def getExtendedAddressInformation(request):
      address = prepare_address(request.query['address'])
      result = await tonlib.generic_get_account_state(address)
      return result

    @routes.get('/getWalletInformation')
    @json_rpc('getWalletInformation', 'get')
    @wrap_result
    async def getWalletInformation(request):
      address = prepare_address(request.query['address'])
      result = await tonlib.raw_get_account_state(address)
      if not "@type" in result or result["@type"]=="error":
        result = await tonlib.raw_get_account_state(address)
      if not "@type" in result:
        raise Exception("Unknown answer from lite server")
      if result["@type"]=="error":
        raise Exception(result["message"])
      res = {'wallet':False, 'balance': 0, 'account_state':None, 'wallet_type':None, 'seqno':None}
      res["account_state"] = address_state(result)
      res["balance"] = result["balance"] if (result["balance"] and int(result["balance"])>0) else 0
      if "last_transaction_id" in result:
        res["last_transaction_id"] = result["last_transaction_id"]
      ci = sha256(result["code"])
      if ci in known_wallets:
          res["wallet"] = True
          wallet_handler = known_wallets[ci]
          res["wallet_type"] = wallet_handler["type"]
          wallet_handler["data_extractor"](res, result)
      return res

    @routes.get('/getTransactions')
    @json_rpc('getTransactions', 'get')
    @wrap_result
    async def getTransactions(request):
      address = prepare_address(request.query['address'])
      limit = int(request.query.get('limit', 10))
      lt = request.query.get('lt', None)
      lt = lt if not lt else int(lt)
      tx_hash = request.query.get('hash', None)
      to_lt = request.query.get('to_lt', 0)
      to_lt = to_lt if not to_lt else int(to_lt)
      return await tonlib.get_transactions(address, from_transaction_lt = lt, from_transaction_hash = tx_hash, to_transaction_lt = to_lt, limit = limit)

    @routes.get('/getAddressBalance')
    @json_rpc('getAddressBalance', 'get')
    @wrap_result
    async def getAddressBalance(request):
      address = prepare_address(request.query['address'])
      result = await tonlib.raw_get_account_state(address)
      if "balance" in result and int(result["balance"])<0:
        result["balance"] = 0
      return result["balance"]

    @routes.get('/getAddressState')
    @json_rpc('getAddressState', 'get')
    @wrap_result
    async def getAddress(request):
      address = prepare_address(request.query['address'])
      result = await tonlib.raw_get_account_state(address)
      return address_state(result)

    @routes.get('/packAddress')
    @json_rpc('packAddress', 'get')
    @wrap_result
    async def packAddress(request):
      return prepare_address(request.query['address'])

    @routes.get('/unpackAddress')
    @json_rpc('unpackAddress', 'get')
    @wrap_result
    async def unpackAddress(request):
      return detect_address(request.query['address'])["raw_form"]

    @routes.get('/getMasterchainInfo')
    @json_rpc('getMasterchainInfo', 'get')
    @wrap_result
    async def getMasterchainInfo(request):
      return await tonlib.getMasterchainInfo()

    @routes.get('/lookupBlock')
    @json_rpc('lookupBlock', 'get')
    @wrap_result
    async def lookupBlock(request):
      workchain = int(request.query['workchain'])
      shard = int(request.query['shard'])
      seqno = request.query.get('seqno', None)
      seqno = int(seqno) if seqno else None
      lt = request.query.get('lt', None)
      lt = int(lt) if lt else None
      unixtime = request.query.get('unixtime', None)
      unixtime = int(unixtime) if unixtime else None
      return await tonlib.lookupBlock(workchain, shard, seqno, lt, unixtime)


    @routes.get('/shards')
    @json_rpc('shards', 'get')
    @wrap_result
    async def lookupBlock(request):
      seqno = request.query.get('seqno', None)
      seqno = int(seqno) if seqno else None
      return await tonlib.getShards(seqno)

    @routes.get('/getBlockTransactions')
    @json_rpc('getBlockTransactions', 'get')
    @wrap_result
    async def getBlockTransactions(request):
      workchain = int(request.query['workchain'])
      shard = int(request.query['shard'])
      seqno = int(request.query['seqno'])
      root_hash = request.query.get('root_hash', None)
      file_hash = request.query.get('file_hash', None)
      after_lt = request.query.get('after_lt')
      after_lt = int(after_lt) if after_lt else after_lt
      after_hash = request.query.get('after_hash')
      count = request.query.get('count')
      count = int(count) if count else count
      return await tonlib.getBlockTransactions(workchain, shard, seqno, root_hash, file_hash, count, after_lt, after_hash)

    @routes.get('/getBlockHeader')
    @json_rpc('getBlockHeader', 'get')
    @wrap_result
    async def getBlockHeader(request):
      workchain = int(request.query['workchain'])
      shard = int(request.query['shard'])
      seqno = int(request.query['seqno'])
      root_hash = request.query.get('root_hash', None)
      file_hash = request.query.get('file_hash', None)
      return await tonlib.getBlockHeader(workchain, shard, seqno, root_hash, file_hash)

    @routes.get('/detectAddress')
    @json_rpc('detectAddress', 'get')
    @wrap_result
    async def detectAddress(request):
      return detect_address(request.query['address'])

    @routes.post('/sendBoc')
    @json_rpc('sendBoc', 'post')
    @wrap_result
    async def send_boc(request):
      data = await request.json()
      boc = base64.b64decode(data['boc'])
      return await tonlib.raw_send_message(boc)

    @routes.post('/sendCellSimple')
    @json_rpc('sendCellSimple', 'post')
    @wrap_result
    async def send_cell(request):
      data = await request.json()
      try:
        cell = deserialize_cell_from_object(data['cell'])
        boc = codecs.encode(cell.serialize_boc(), 'base64')
      except:
        raise web.HTTPBadRequest(text = "Wrong cell object")
      return await tonlib.raw_send_message(boc)

    @routes.post('/sendQuery')
    @json_rpc('sendQuery', 'post')
    @wrap_result
    async def send_query(request):
      data = await request.json()
      address = prepare_address(data['address'])
      body = codecs.decode(codecs.encode(data['body'], "utf-8"), 'base64').replace("\n",'') 
      code = codecs.decode(codecs.encode(data.get('init_code', b''), "utf-8"), 'base64').replace("\n",'') 
      data = codecs.decode(codecs.encode(data.query.get('init_data', b''), "utf-8"), 'base64').replace("\n",'')
      return await tonlib.raw_create_and_send_query(address, body, init_code=code, init_data=data)

    @routes.post('/sendQuerySimple')
    @json_rpc('sendQuerySimple', 'post')
    @wrap_result
    async def send_query_cell(request):
      data = await request.json()
      address = prepare_address(data['address'])
      try:
        body = deserialize_cell_from_object(data['body']).serialize_boc(has_idx=False)
        qcode, qdata = b'', b''
        if 'init_code' in data:
          qcode = deserialize_cell_from_object(data['init_code']).serialize_boc(has_idx=False)
        if 'init_data' in data:
          qdata = deserialize_cell_from_object(data['init_data']).serialize_boc(has_idx=False)
      except:
        raise web.HTTPBadRequest(text = "Can't serialize cell object")
      return await tonlib.raw_create_and_send_query(address, body, init_code=qcode, init_data=qdata)

    @routes.post('/estimateFee')
    @json_rpc('estimateFee', 'post')
    @wrap_result
    async def estimate_fee(request):
      data = await request.json()
      address = prepare_address(data['address'])
      addr_info = await tonlib.raw_get_account_state(address)
      assert address_state(addr_info)=='active', "Address is not active"
      body = codecs.decode(codecs.encode(data['body'], "utf-8"), 'base64').replace("\n",'') 
      code = codecs.decode(codecs.encode(data.get('init_code', b''), "utf-8"), 'base64').replace("\n",'') 
      data = codecs.decode(codecs.encode(data.get('init_data', b''), "utf-8"), 'base64').replace("\n",'')
      ignore_chksig = data.get('ignore_chksig', True)
      return await tonlib.raw_estimate_fees(address, body, init_code=code, init_data=data, ignore_chksig=ignore_chksig)

    @routes.post('/estimateFeeSimple')
    @json_rpc('estimateFeeSimple', 'post')
    @wrap_result
    async def estimate_fee_cell(request):
      data = await request.json()
      address = prepare_address(data['address'])
      addr_info = await tonlib.raw_get_account_state(address)
      assert address_state(addr_info)=='active', "Address is not active"
      try:
        body = deserialize_cell_from_object(data['body']).serialize_boc(has_idx=False)
        qcode, qdata = b'', b''
        if 'init_code' in data:
          qcode = deserialize_cell_from_object(data['init_code']).serialize_boc(has_idx=False)
        if 'init_data' in data:
          qdata = deserialize_cell_from_object(data['init_data']).serialize_boc(has_idx=False)
        ignore_chksig = data.get('ignore_chksig', True)
      except:
        raise web.HTTPBadRequest(text = "Can't serialize cell object")
      return await tonlib.raw_estimate_fees(address, body, init_code=qcode, init_data=qdata, ignore_chksig=ignore_chksig)

    if args.getmethods:
        @routes.post('/runGetMethod')
        @json_rpc('runGetMethod', 'post')
        @wrap_result
        async def getAddress(request):
          data = await request.json()
          address = prepare_address(data['address'])
          method = data['method']
          stack = data['stack']
          return await tonlib.raw_run_method(address, method, stack)
    if args.jsonrpc:
        @routes.post('/jsonRPC')
        async def jsonrpc_handler(request):
          data = await request.json()
          params = data['params']
          method = data['method']
          _id = data.get('id', None)
          if not method in json_rpc_methods:
            return web.json_response( { "ok": False, "error": 'Unknown method'})
          handler, style = json_rpc_methods[method]
          class PseudoRequest:
            def __init__(self,query={}, json={}, id=None):
              self.query, self._json, self._id = query, json, id
            async def json(self):
              return self._json
          if style == 'get':
             return await handler(PseudoRequest(query=params, id=_id))
          else:
             return await handler(PseudoRequest(json=params, id=_id))

    app = web.Application()
    app.add_routes(routes)
    def cors_handler(*args, **kwargs):
      cors_origin_header = ("Access-Control-Allow-Origin", "*")
      cors_headers_header = ("Access-Control-Allow-Headers", "*")
      return web.Response(headers=[cors_origin_header, cors_headers_header])
    for route in list(routes):
      if not isinstance(route, web.StaticDef):
        app.router.add_route(method="OPTIONS", path=route.path, handler=cors_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    while True:
      await asyncio.sleep(1)
    await runner.cleanup()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
