import os
import sys
import logging
from binascii import hexlify
from mtkclient.Library.utils import LogBase
from mtkclient.Library.settings import hwparam
from mtkclient.config.brom_config import chipconfig, damodes, hwconfig

class Mtk_Config(metaclass=LogBase):
    def __init__(self, loglevel=logging.INFO, gui=None, guiprogress=None):
        self.gui = gui
        self.guiprogress = guiprogress
        self.pid = -1
        self.vid = -1
        self.var1 = 0xA
        self.is_brom = False
        self.skipwdt = False
        self.interface = -1
        self.readsocid = False
        self.enforcecrash = False
        self.debugmode = False
        self.preloader = None
        self.preloader_filename = None
        self.payloadfile = None
        self.loader = None
        if sys.platform.startswith('darwin'):
            self.ptype = "kamakiri"
        else:
            self.ptype = "kamakiri2"
        self.generatekeys = None
        self.bmtflag = None
        self.bmtblockcount = None
        self.bmtpartsize = None
        self.packetsizeread = 0x400
        self.flashinfo = None
        self.readsize = 0
        self.sparesize = 16
        self.plcap = None
        self.blver = -2
        self.da = None
        self.gcpu = None
        self.pagesize = 512
        self.SECTOR_SIZE_IN_BYTES = 4096  # fixme
        self.baudrate = 115200
        self.flash = "emmc"
        self.cpu = ""
        self.hwcode = None
        self.meid = None
        self.socid = None
        self.target_config = None
        self.chipconfig = chipconfig()
        self.gpt_settings = None
        self.hwparam = None
        self.hwparam_path = "logs"
        if loglevel == logging.DEBUG:
            logfilename = os.path.join("logs", "log.txt")
            fh = logging.FileHandler(logfilename)
            self.__logger.addHandler(fh)
            self.__logger.setLevel(logging.DEBUG)
        else:
            self.__logger.setLevel(logging.INFO)

    def set_meid(self,meid):
        self.hwparam = hwparam(meid, self.hwparam_path)
        self.meid = meid
        self.hwparam.writesetting("meid", hexlify(meid).decode('utf-8'))

    def get_meid(self):
        if self.meid is None and self.hwparam is not None:
            self.meid = self.hwparam.loadsetting("meid")
        return self.meid

    def set_socid(self,socid):
        self.socid = socid
        self.hwparam.writesetting("socid",hexlify(socid).decode('utf-8'))

    def get_socid(self):
        if self.socid is None and self.hwparam is not None:
            self.socid = self.hwparam.loadsetting("socid")
        return self.socid

    def set_hwparam_path(self, path):
        if path is None:
            path = "logs"
        self.hwparam_path = path

    def default_values(self, hwcode):
        if self.chipconfig.var1 is None:
            self.chipconfig.var1 = 0xA
        if self.chipconfig.watchdog is None:
            self.chipconfig.watchdog = 0x10007000
        if self.chipconfig.uart is None:
            self.chipconfig.uart = 0x11002000
        if self.chipconfig.brom_payload_addr is None:
            self.chipconfig.brom_payload_addr = 0x100A00
        if self.chipconfig.da_payload_addr is None:
            self.chipconfig.da_payload_addr = 0x200000
        if self.chipconfig.cqdma_base is None:
            self.chipconfig.cqdma_base = None
        if self.chipconfig.gcpu_base is None:
            self.chipconfig.gcpu_base = None
        if self.chipconfig.sej_base is None:
            self.chipconfig.sej_base = None
        if self.chipconfig.dacode is None:
            self.chipconfig.dacode = hwcode
        if self.chipconfig.ap_dma_mem is None:
            self.chipconfig.ap_dma_mem = 0x11000000 + 0x1A0
        if self.chipconfig.damode is None:
            self.chipconfig.damode = damodes.DEFAULT
        if self.chipconfig.dxcc_base is None:
            self.chipconfig.dxcc_base = None
        if self.chipconfig.meid_addr is None:
            self.chipconfig.meid_addr = None
        if self.chipconfig.socid_addr is None:
            self.chipconfig.socid_addr = None
        if self.chipconfig.prov_addr is None:
            self.chipconfig.prov_addr = None

    def init_hwcode(self, hwcode):
        self.hwcode = hwcode
        if hwcode in hwconfig:
            self.chipconfig = hwconfig[hwcode]
        else:
            self.chipconfig = chipconfig()
        self.default_values(hwcode)

    def get_watchdog_addr(self):
        wdt = self.chipconfig.watchdog
        if wdt != 0:
            if wdt == 0x10007000:
                return [wdt, 0x22000064]
            elif wdt == 0x10212000:
                return [wdt, 0x22000000]
            elif wdt == 0x10211000:
                return [wdt, 0x22000064]
            elif wdt == 0x10007400:
                return [wdt, 0x22000000]
            elif wdt == 0xC0000000:
                return [wdt, 0x0]
            elif wdt == 0x2200:
                if self.hwcode == 0x6276 or self.hwcode == 0x8163:
                    return [wdt, 0x610C0000]
                elif self.hwcode == 0x6251 or self.hwcode == 0x6516:
                    return [wdt, 0x80030000]
                elif self.hwcode == 0x6255:
                    return [wdt, 0x701E0000]
                else:
                    return [wdt, 0x70025000]
            else:
                return [wdt, 0x22000064]

    def bmtsettings(self, hwcode):
        bmtflag = 1
        bmtblockcount = 0
        bmtpartsize = 0
        if hwcode in [0x6592, 0x6582, 0x8127, 0x6571]:
            if self.flash == "emmc":
                bmtflag = 1
                bmtblockcount = 0xA8
                bmtpartsize = 0x1500000
        elif hwcode in [0x6570, 0x8167, 0x6580, 0x6735, 0x6753, 0x6755, 0x6752, 0x6595, 0x6795, 0x6767, 0x6797, 0x8163]:
            bmtflag = 1
            bmtpartsize = 0
        elif hwcode in [0x6571]:
            if self.flash == "nand":
                bmtflag = 0
                bmtblockcount = 0x38
                bmtpartsize = 0xE00000
            elif self.flash == "emmc":
                bmtflag = 1
                bmtblockcount = 0xA8
                bmtpartsize = 0x1500000
        elif hwcode in [0x6575]:
            if self.flash == "nand":
                bmtflag = 0
                bmtblockcount = 0x50
            elif self.flash == "emmc":
                bmtflag = 1
                bmtblockcount = 0xA8
                bmtpartsize = 0x1500000
        elif hwcode in [0x6572]:
            if self.flash == "nand":
                bmtflag = 0
                bmtpartsize = 0xA00000
                bmtblockcount = 0x50
            elif self.flash == "emmc":
                bmtflag = 0
                bmtpartsize = 0xA8
                bmtblockcount = 0x50
        elif hwcode in [0x6577, 0x6583, 0x6589]:
            if self.flash == "nand":
                bmtflag = 0
                bmtpartsize = 0xA00000
                bmtblockcount = 0xA8
        self.bmtflag = bmtflag
        self.bmtblockcount = bmtblockcount
        self.bmtpartsize = bmtpartsize
        return bmtflag, bmtblockcount, bmtpartsize
