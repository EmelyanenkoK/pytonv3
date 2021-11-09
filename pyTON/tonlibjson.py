import json
from ctypes import *
import platform
import pkg_resources
import random
import asyncio
import time
import functools

def get_tonlib_path():
    arch_name = platform.system().lower()
    if arch_name == 'darwin':
        lib_name = 'libtonlibjson.dylib'
    elif arch_name == 'linux':
        lib_name = 'libtonlibjson.so'
    else:
        raise RuntimeError('Platform could not be identified')
    return pkg_resources.resource_filename(
        'pyTON',
        'distlib/'+arch_name+'/'+lib_name)

class TonLib:
    def __init__(self, loop, cdll_path=None):
        cdll_path = get_tonlib_path() if not cdll_path else cdll_path
        tonlib = CDLL(cdll_path)

        tonlib_json_client_create = tonlib.tonlib_client_json_create
        tonlib_json_client_create.restype = c_void_p
        tonlib_json_client_create.argtypes = []
        try:
          self._client = tonlib_json_client_create()
        except Exception:
          asyncio.ensure_future(self.restart_hook(), loop=self.loop)

        tonlib_json_client_receive = tonlib.tonlib_client_json_receive
        tonlib_json_client_receive.restype = c_char_p
        tonlib_json_client_receive.argtypes = [c_void_p, c_double]
        self._tonlib_json_client_receive = tonlib_json_client_receive

        tonlib_json_client_send = tonlib.tonlib_client_json_send
        tonlib_json_client_send.restype = None
        tonlib_json_client_send.argtypes = [c_void_p, c_char_p]
        self._tonlib_json_client_send = tonlib_json_client_send

        tonlib_json_client_execute = tonlib.tonlib_client_json_execute
        tonlib_json_client_execute.restype = c_char_p
        tonlib_json_client_execute.argtypes = [c_void_p, c_char_p]
        self._tonlib_json_client_execute = tonlib_json_client_execute

        tonlib_json_client_destroy = tonlib.tonlib_client_json_destroy
        tonlib_json_client_destroy.restype = None
        tonlib_json_client_destroy.argtypes = [c_void_p]
        self._tonlib_json_client_destroy = tonlib_json_client_destroy
        
        self.futures = {}
        self.loop = loop
        self.loop_task = asyncio.ensure_future(self.tl_loop(), loop=self.loop)
        self.shutdown_state = False # False, "started", "finished"
        self.request_num = 0
        self.max_requests = None


    def __del__(self):
        try:
          self._tonlib_json_client_destroy(self._client)
        except Exception:
          asyncio.ensure_future(self.restart_hook(), loop=self.loop)

    def send(self, query):
        query = json.dumps(query).encode('utf-8')
        try:
          self._tonlib_json_client_send(self._client, query)
        except Exception:
          asyncio.ensure_future(self.restart_hook(), loop=self.loop)

    def receive(self, timeout=10):
        try:
          result = self._tonlib_json_client_receive(self._client, timeout)
        except Exception:
          asyncio.ensure_future(self.restart_hook(), loop=self.loop)
        if result:
            result = json.loads(result.decode('utf-8'))
        return result

    def set_restart_hook(self, hook, max_requests):
        self.max_requests = max_requests
        self.restart_hook = hook

    def execute(self, query, timeout=10):
        extra_id = "%s:%s"%(time.time()+timeout,random.random())
        query["@extra"] = extra_id
        self.loop.run_in_executor(None, lambda: self.send(query))
        future_result = self.loop.create_future()
        self.futures[extra_id] = future_result
        self.request_num += 1
        if self.max_requests and self.max_requests < self.request_num:
            asyncio.ensure_future(self.restart_hook(), loop=self.loop)
        return future_result

    async def tl_loop(self):
      while True:
        result = True
        autorestart = False
        while result:
          try:
              f = functools.partial(self.receive, 0)
              result = await asyncio.wait_for(self.loop.run_in_executor(None, f), timeout=3.0)
          except asyncio.TimeoutError:
              print("Timeout")
              autorestart = True
              result = False
          except Exception:
              # tonlib itself may crash
              autorestart = True
              result = False
          if result and isinstance(result, dict) and ("@extra" in result) and (result["@extra"] in self.futures):
             try:
               if not self.futures[result["@extra"]].done():
                 self.futures[result["@extra"]].set_result(result)
                 del self.futures[result["@extra"]]
             except Exception as e:
               print(e)
        now = time.time()
        to_del = []
        for i in self.futures:
          if float(i.split(":")[0]) > now:
            break
          autorestart = True
          if self.futures[i].done():
            to_del.append(i)
            continue
          to_del.append(i)
          self.futures[i].cancel()
        for i in to_del:
          del self.futures[i]
        if autorestart:
          asyncio.ensure_future(self.restart_hook(), loop=self.loop)
        if (not len(self.futures)) and (self.shutdown_state in ["started","finished"]):
          break
        await asyncio.sleep(0.05)
      self.shutdown_state = "finished"
