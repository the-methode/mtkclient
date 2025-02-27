import os
import sys
import mock
import time
from PySide6.QtCore import Slot, QObject
from mtkclient.gui.toolkit import convert_size, FDialog, trap_exc_during_debug, asyncThread

sys.excepthook = trap_exc_during_debug

class ReadFlashWindow(QObject):
    def __init__(self, ui, parent, devhandler, da_handler, sendToLog):  # def __init__(self, *args, **kwargs):
        self.mtkClass = devhandler.mtkClass
        self.parent = parent
        self.sendToLog = sendToLog
        self.Status = {}
        self.fdialog = FDialog(parent)
        self.da_handler = da_handler
        self.ui = parent.ui

    # Partition

    def dumpPartDone(self):
        self.sendToLogSignal.emit("dump done!")

    def selectAll(self):
        if self.ui.readselectallcheckbox.isChecked():
            for partition in self.parent.readpartitionCheckboxes:
                self.parent.readpartitionCheckboxes[partition]['box'].setChecked(True)
        else:
            for partition in self.parent.readpartitionCheckboxes:
                self.parent.readpartitionCheckboxes[partition]['box'].setChecked(False)

    def dumpPartition(self):
        self.ui.readpreloaderbtn.setEnabled(False)
        self.ui.readpartitionsbtn.setEnabled(False)
        self.ui.readboot2btn.setEnabled(False)
        self.ui.readrpmbbtn.setEnabled(False)
        self.dumpFolder = self.fdialog.opendir(self.tr("Select output directory"))
        if self.dumpFolder:
            self.parent.disablebuttons()
            thread = asyncThread(parent=self.parent, n=0, function=self.dumpPartitionAsync,parameters=[])
            thread.sendToLogSignal.connect(self.sendToLog)
            thread.sendUpdateSignal.connect(self.parent.updateState)
            thread.sendToProgressSignal.connect(self.parent.updateProgress)
            thread.start()
        else:
            self.parent.enablebuttons()

    def dumpPartitionAsync(self, toolkit, parameters):
        self.parent.timeEst.init()
        self.parent.timeEstTotal.init()
        self.sendToLogSignal = toolkit.sendToLogSignal
        toolkit.sendToLogSignal.emit("test")
        self.parent.Status["done"] = False
        thread = asyncThread(self.parent.parent(), 0, self.parent.updateStateAsync, [])
        thread.sendUpdateSignal.connect(self.parent.updateState)
        thread.sendToProgressSignal.connect(self.parent.updateProgress)
        thread.start()
        # calculate total bytes
        self.parent.Status["allPartitions"] = {}
        for partition in self.parent.readpartitionCheckboxes:
            if self.parent.readpartitionCheckboxes[partition]['box'].isChecked():
                self.parent.Status["allPartitions"][partition] = {"size": self.parent.readpartitionCheckboxes[partition]['size'],
                                                               "done": False}
        for partition in self.parent.readpartitionCheckboxes:
            if self.parent.readpartitionCheckboxes[partition]['box'].isChecked():
                variables = mock.Mock()
                variables.partitionname = partition
                variables.filename = os.path.join(self.dumpFolder, partition + ".bin")
                variables.parttype = None
                self.parent.Status["currentPartitionSize"] = self.parent.readpartitionCheckboxes[partition]['size']
                self.parent.Status["currentPartition"] = partition
                self.parent.Status["currentPartitionFile"] = variables.filename
                self.da_handler.close = self.dumpPartDone  # Ignore the normally used sys.exit
                self.da_handler.handle_da_cmds(self.mtkClass, "r", variables)
                self.parent.Status["allPartitions"][partition]['done'] = True
                # MtkTool.cmd_stage(mtkClass, None, None, None, False)
        if self.ui.readDumpGPTCheckbox.isChecked():
            #also dump the GPT
            variables = mock.Mock()
            variables.directory = self.dumpFolder
            variables.parttype = None
            self.parent.Status["allPartitions"]["GPT"] = {}
            self.parent.Status["allPartitions"]["GPT"]['size'] = 17
            self.parent.Status["currentPartition"] = "GPT"
            self.da_handler.close = self.dumpPartDone  # Ignore the normally used sys.exit
            self.da_handler.handle_da_cmds(self.mtkClass, "gpt", variables)
            self.parent.Status["allPartitions"]["GPT"]['done'] = True
        self.parent.Status["done"] = True
        thread.wait()


    def dumpFlash(self, parttype):
        self.parttype=parttype
        self.parent.disablebuttons()
        if self.parttype == "user":
            self.flashsize = self.mtkClass.daloader.daconfig.flashsize
        elif self.parttype == "rpmb":
            self.flashsize = self.mtkClass.daloader.daconfig.rpmbsize
        elif self.parttype == "boot1":
            self.flashsize = self.mtkClass.daloader.daconfig.boot1size
        elif self.parttype == "boot2":
            self.flashsize = self.mtkClass.daloader.daconfig.boot2size
        self.parent.Status["currentPartitionSize"] = self.flashsize
        self.parent.Status["currentPartition"] = parttype
        self.ui.partProgressText.setText(self.tr("Ready to dump ") + convert_size(self.flashsize))
        self.dumpFile = self.fdialog.save(self.parttype+".bin")
        if self.dumpFile:
            thread = asyncThread(parent=self.parent, n=0, function=self.dumpFlashAsync, parameters=[self.parttype])
            thread.sendToLogSignal.connect(self.sendToLog)
            thread.sendUpdateSignal.connect(self.parent.updateState)
            thread.start()
        else:
            self.parent.enablebuttons()

    def dumpFlashAsync(self, toolkit, parameters):
        self.parent.timeEst.init()
        self.parent.timeEstTotal.init()
        self.sendToLogSignal = toolkit.sendToLogSignal
        self.parent.Status["done"] = False
        thread = asyncThread(self.parent, 0, self.parent.updateStateAsync, [])
        #thread.sendUpdateSignal.connect(self.updateDumpState)
        thread.start()
        variables = mock.Mock()
        variables.filename = self.dumpFile
        variables.parttype = None
        self.parent.Status["dumpFile"] = variables.filename
        self.da_handler.close = self.dumpPartDone  # Ignore the normally used sys.exit
        if "rpmb" in parameters:
            self.mtkClass.daloader.read_rpmb(variables.filename)
        else:
            if "boot1" in parameters:
                variables.parttype = "boot1"
            elif "boot2" in parameters:
                variables.parttype = "boot2"
            else:
                variables.parttype = "user"
            self.da_handler.handle_da_cmds(self.mtkClass, "rf", variables)
        if self.ui.readDumpGPTCheckbox.isChecked():
            # also dump the GPT
            variables = mock.Mock()
            variables.directory = os.path.dirname(self.dumpFile)
            variables.parttype = None
            self.da_handler.close = self.dumpPartDone  # Ignore the normally used sys.exit
            self.da_handler.handle_da_cmds(self.mtkClass, "gpt", variables)
        self.parent.Status["done"] = True
        thread.wait()
