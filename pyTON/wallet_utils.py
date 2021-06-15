from hashlib import sha256 as hasher
import codecs

from tvm_valuetypes.cell import deserialize_boc

def seqno_extractor(result, data):
  data_cell = deserialize_boc(codecs.decode(codecs.encode(data["data"], 'utf-8'), 'base64'))
  seqno = int.from_bytes(data_cell.data.data[0:32].tobytes(), 'big')
  result['seqno'] = seqno

def v3_extractor(result, data):
  seqno_extractor(result, data)
  data_cell = deserialize_boc(codecs.decode(codecs.encode(data["data"], 'utf-8'), 'base64'))
  wallet_id = int.from_bytes(data_cell.data.data[32:64].tobytes(), 'big')
  result['wallet_id'] = wallet_id
  

def sha256(x):
  if not isinstance(x, bytes):
    x = codecs.encode(x, 'utf-8')
  h = hasher()
  h.update(x)
  return h.digest()

simple_wallet_code = "te6cckEBAQEARAAAhP8AIN2k8mCBAgDXGCDXCx/tRNDTH9P/0VESuvKhIvkBVBBE+RDyovgAAdMfMSDXSpbTB9QC+wDe0aTIyx/L/8ntVEH98Ik="
simple_wallet_code_r2 = "te6cckEBAQEAUwAAov8AIN0gggFMl7qXMO1E0NcLH+Ck8mCBAgDXGCDXCx/tRNDTH9P/0VESuvKhIvkBVBBE+RDyovgAAdMfMSDXSpbTB9QC+wDe0aTIyx/L/8ntVNDieG8="
simple_wallet_code_r3 = "te6cckEBAQEAXwAAuv8AIN0gggFMl7ohggEznLqxnHGw7UTQ0x/XC//jBOCk8mCBAgDXGCDXCx/tRNDTH9P/0VESuvKhIvkBVBBE+RDyovgAAdMfMSDXSpbTB9QC+wDe0aTIyx/L/8ntVLW4bkI="
wallet_code2 = "te6cckEBAQEAVwAAqv8AIN0gggFMl7qXMO1E0NcLH+Ck8mCDCNcYINMf0x8B+CO78mPtRNDTH9P/0VExuvKhA/kBVBBC+RDyovgAApMg10qW0wfUAvsA6NGkyMsfy//J7VShNwu2"
wallet_code2_r2 = "te6cckEBAQEAYwAAwv8AIN0gggFMl7ohggEznLqxnHGw7UTQ0x/XC//jBOCk8mCDCNcYINMf0x8B+CO78mPtRNDTH9P/0VExuvKhA/kBVBBC+RDyovgAApMg10qW0wfUAvsA6NGkyMsfy//J7VQETNeh"
wallet_v3_code = "te6cckEBAQEAYgAAwP8AIN0gggFMl7qXMO1E0NcLH+Ck8mCDCNcYINMf0x/TH/gjE7vyY+1E0NMf0x/T/9FRMrryoVFEuvKiBPkBVBBV+RDyo/gAkyDXSpbTB9QC+wDo0QGkyMsfyx/L/8ntVD++buA="
wallet_v3_r2 = "te6cckEBAQEAcQAA3v8AIN0gggFMl7ohggEznLqxn3Gw7UTQ0x/THzHXC//jBOCk8mCDCNcYINMf0x/TH/gjE7vyY+1E0NMf0x/T/9FRMrryoVFEuvKiBPkBVBBV+RDyo/gAkyDXSpbTB9QC+wDo0QGkyMsfyx/L/8ntVBC9ba0="

wallets = { sha256(simple_wallet_code): {'type': 'wallet v1 r1', 'data_extractor':seqno_extractor},
            sha256(simple_wallet_code_r2): {'type': 'wallet v1 r2', 'data_extractor':seqno_extractor},
            sha256(simple_wallet_code_r3): {'type': 'wallet v1 r3', 'data_extractor':seqno_extractor},
            sha256(wallet_code2): {'type': 'wallet v2 r1', 'data_extractor':seqno_extractor},
            sha256(wallet_code2_r2): {'type': 'wallet v2 r2', 'data_extractor':seqno_extractor},
            sha256(wallet_v3_code): {'type': 'wallet v3 r1', 'data_extractor':v3_extractor},
            sha256(wallet_v3_r2): {'type': 'wallet v3 r2', 'data_extractor':v3_extractor},
}

