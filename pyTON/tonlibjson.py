import json
from ctypes import *
import platform
import pkg_resources
import random
import asyncio

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
        self._client = tonlib_json_client_create()

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


    def __del__(self):
        self._tonlib_json_client_destroy(self._client)

    def send(self, query):
        query = json.dumps(query).encode('utf-8')
        self._tonlib_json_client_send(self._client, query)

    def receive(self, timeout=10):
        result = self._tonlib_json_client_receive(self._client, timeout)
        if result:
            result = json.loads(result.decode('utf-8'))
        return result

    def execute(self, query, timeout=10):
        extra_id = "%s"%random.random()
        query["@extra"] = extra_id
        self.send(query)
        future_result = self.loop.create_future()
        self.futures[extra_id] = future_result
        return future_result

    async def tl_loop(self):
      while True:
        result = self.receive(0) # get result if ready
        if result and isinstance(result, dict) and ("@extra" in result) and (result["@extra"] in self.futures):
          self.futures[result["@extra"]].set_result(result)
          del self.futures[result["@extra"]]
        await asyncio.sleep(0.05) 
