import json
import os.path
from binascii import hexlify

class hwparam:
    paramsetting = None
    hwcode = None

    def __init__(self, meid:str, path:str="logs"):
        self.paramfile = os.path.join(path, "hwparam.json")
        self.hwparampath = path
        if isinstance(meid,bytearray) or isinstance(meid,bytes):
            meid=hexlify(meid).decode('utf-8')
        if meid is None:
            self.paramsetting = None
        if os.path.exists(self.paramfile):
            self.paramsetting = json.loads(open(self.paramfile, "r").read())
            if "meid" in self.paramsetting:
                if meid!=self.paramsetting["meid"]:
                    self.paramsetting = {}
        else:
            self.paramsetting = {}
            self.paramsetting["meid"] = meid
            open(self.paramfile, "w").write(json.dumps(self.paramsetting))

    def loadsetting(self,key:str):
        if self.paramsetting is not None:
            if key in self.paramsetting:
                return self.paramsetting[key]
        return None

    def writesetting(self, key:str,value:str):
        if self.paramsetting is not None:
            self.paramsetting[key]=value
            self.write_json()

    def write_json(self):
        if self.paramsetting is not None:
            if not os.path.exists(self.hwparampath):
                os.mkdir(self.hwparampath)
            open(self.paramfile, "w").write(json.dumps(self.paramsetting))
