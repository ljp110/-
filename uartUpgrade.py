#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import wx
import serial
import os
import time

VERSION_STR = "v1.1"

HelpContext = "选择串口-> 打开串口 -> 单击下载按钮 -> 给板卡上电"

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        c_x, c_y, c_w, c_h = wx.ClientDisplayRect()
        screenSize = (wx.Size(c_w*1/4, c_h*3/5))
        posLeftTop = (0, 0)

        wx.Frame.__init__(self, parent, title=title, style=wx.DEFAULT_FRAME_STYLE, pos=posLeftTop, size=screenSize)

        self.scroller = wx.ScrolledWindow(self, -1, size=screenSize)
        self.panel = self.scroller

        import serial.tools.list_ports
        comport_list = []
        original_comports_list = list(serial.tools.list_ports.comports())
        if original_comports_list is not None:
            for i in range(len(original_comports_list)):
                comports = str(original_comports_list[i]).split('-')
                comport_list.append(comports[0])
        else:
            print("no comports")
            print(comport_list)

        self.comPortChoice = wx.Choice(self.panel, -1, choices=comport_list)
        # self.comPortChoice.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.testComPortChoiceFunc, self.comPortChoice)

        self.testText = wx.TextCtrl(self.panel, -1, (""), size=(int(c_w*1/4), int(c_h*3/5)), style=wx.TE_MULTILINE)

        self.serialBtn = wx.Button(self.panel, -1, "打开")
        self.Bind(wx.EVT_BUTTON, self.serialBtnFunc, self.serialBtn)

        self.downloadBtn = wx.Button(self.panel, -1, "下载")
        self.Bind(wx.EVT_BUTTON, self.downloadBtnFunc, self.downloadBtn)

        self.clearDisplaynewBtn = wx.Button(self.panel, -1, "清除")
        self.Bind(wx.EVT_BUTTON, self.clearDisplaynewBtnFunc, self.clearDisplaynewBtn)

        self.helpBtn = wx.Button(self.panel, -1, "帮助")
        self.Bind(wx.EVT_BUTTON, self.helpBtnFunc, self.helpBtn)

        self.DbgChkbox = wx.CheckBox(self.panel, -1, label='DBG')
        self.Bind(wx.EVT_CHECKBOX, self.DbgChkboxFunc, self.DbgChkbox)
        self.DbgChkbox.Hide()

        self.filePathText = wx.TextCtrl(self.panel, -1, (""), size=(c_w*1/4, 30), style=wx.TE_MULTILINE)

        self.changePathBtn = wx.Button(self.panel, -1, "改变路径")
        self.Bind(wx.EVT_BUTTON, self.changePathBtnFunc, self.changePathBtn)

        leftVSizer = wx.BoxSizer(wx.VERTICAL)
        rightTopHSizer = wx.BoxSizer(wx.HORIZONTAL)
        rightTopHSizer3 = wx.BoxSizer(wx.HORIZONTAL)

        rightTopHSizer.Add(self.DbgChkbox, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)
        rightTopHSizer.Add(self.comPortChoice, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)
        rightTopHSizer.Add(self.serialBtn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)
        rightTopHSizer.Add(self.downloadBtn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)
        rightTopHSizer.Add(self.clearDisplaynewBtn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)
        rightTopHSizer.Add(self.helpBtn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)

        rightTopHSizer3.Add(self.filePathText, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)
        rightTopHSizer3.Add(self.changePathBtn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        leftVSizer.Add(rightTopHSizer, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)
        leftVSizer.Add(rightTopHSizer3, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)
        leftVSizer.Add(self.testText, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)

        self.ser = None
        self.recvFlags = 1
        self.forcedUpgradeflags = 0
        self.powerOnAndDownloadflags = 0
        self.Dbgflags = 0
        self.varAll = ''
        self.fristPackFlags = 0
        self.secondPackFlags = 0
        self.displayThreadLen = 0
        self.thirdPackFlags = 0
        self.fileName = ''
        self.cmdRunFlags = 0
        self.foldername = ''
        self.filePackNumber = 0
        self.serialStatus = 0
        self.serialOccupyFlags = 0

        self.panel.SetSizerAndFit(leftVSizer)
        self.panel.Layout()
        self.Fit()
        self.Center()
        self.Show(True)

    def serialInit(self):
        str = self.comPortChoice.GetString(self.comPortChoice.GetSelection())
        try:
            self.ser = serial.Serial(port=str, baudrate=115200, timeout=0.2)
            self.serialBtn.SetLabel("关闭")
            self.serialStatus = 1
            self.comPortChoice.Disable()
        except (OSError, serial.SerialException):
            self.displayNew("串口被占用\r\n")

        return 0

    def serialBtnFunc(self, event):
        if self.serialStatus == 1:
            self.ser.close()
            self.serialBtn.SetLabel("打开")
            self.serialStatus = 0
            self.comPortChoice.Enable()
        elif self.serialStatus == 0:
            self.serialInit()

    def clearDisplaynewBtnFunc(self, event):
        self.varAll = ""
        self.testText.SetValue("")

    def waitAndYield(self, sec):
        nowTime = time.monotonic()
        nextStart = nowTime + sec
        while (nowTime <= nextStart):
            if (None != wx.Yield):
                wx.Yield()
            nowTime = time.monotonic()
            if (None != wx.Yield):
                wx.Yield()

    def helpBtnFunc(self, event):
        global HelpContext
        dlg = wx.MessageDialog(self, HelpContext, "软件使用说明", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def displayNew(self, var):
        self.varAll+=var
        dislen=len(self.varAll)

        # add some roll back...
        if(dislen>32000):
            if(0==self.displayThreadLen):
                self.displayThreadLen=dislen
            else:
                if(dislen>64000):
                    self.varAll=self.varAll[self.displayThreadLen:]
                    self.displayThreadLen=0
                else:
                    pass
        else:
            pass

        self.testText.SetValue(self.varAll)
        self.testText.ShowPosition(self.testText.GetLastPosition())

        return

    def testComPortChoiceFunc(self, event):
        # self.serialInit()
        pass

    def readUartData(self):

        self.displayNew('升级开始\r\n')
        self.ser.reset_output_buffer()
        self.ser.reset_input_buffer()
        dataAll = []
        count = 0
        startTime = time.monotonic()
        spendTime = 20
        endTime = startTime + spendTime
        recvFristPackAll = ''
        
        self.displayNew("开始发送reboot\r\n")
        self.ser.write("reboot".encode('utf-8'))
        # 50 43 45 44  PCED
        # 52 54 45 44  RTED
        # self.waitAndYield(3)
        
        while (time.monotonic() <= endTime):
            # self.displayNew("while\r\n")
            data = self.ser.read()
            # self.displayNew("1\r\n")
            # self.displayNew(data)
            
            #if (data < 0) or (data == ' '):
            #    self.displayNew("请按下载按钮重新发送reboot\r\n")
            #    return 0
                
            # self.displayNew("2\r\n")

            data = int.from_bytes(data, byteorder='big', signed=False)
            # self.displayNew("3\r\n")
            dataAll.append(data)
            # self.displayNew("4\r\n")

            count += 1
            if self.Dbgflags == 1:
                self.displayNew('recv = %02x\r\n' % data)

            if data == 0x44:
                if dataAll[count-2] == 0x45  and dataAll[count-3] == 0x54 and dataAll[count-4] == 0x52:
                    self.displayNew("接收到下载请求信号\r\n")
                    if self.Dbgflags == 1:
                        self.displayNew('跳出串口接收循环\r\n')
                    self.fristPackFlags = 1
                    i = 0
                    while len(dataAll) > i:
                        i += 1
                    dataAll.clear()
                    break
            self.waitAndYield(0.01)
        if self.fristPackFlags == 0:
            if self.Dbgflags == 1:
                self.displayNew('板卡发送给PC第一包未接收到\r\n')
            self.displayNew('升级结束TIMEOUT\r\n')
            # self.ser.close()
            return 0
        self.fristPackFlags = 0
        if self.Dbgflags == 1:
            if dataAll[count -9] == 0x0a:
                self.displayNew('每包1024个字节\r\n')
            if dataAll[count - 8] == 0x17:
                self.displayNew('无线电量\r\n')
            if dataAll[count - 7] == 0x01:
                self.displayNew('bin文件下载\r\n')

        self.displayNew("发送2号数据包\r\n")
        # 接受到RTED结束标志后, 向板卡发送第一包数据
        # b'\x50\x43\x53\x54'<=>'PCST'  b'\x50\x43\x45\x44'<=>'PCED'

        fileNameLen = len(self.fileName)

        PcstData = bytearray(b'\x50\x43\x53\x54')
        # self.ser.write(PcstData)

        NumNumberData = bytearray(b'\x01')# 0x0C
        # self.ser.write(NumNumberData)

        infoLen = 2 + 1 + 2 + 4 + 1 + 1 + fileNameLen
        allLen = 2 + 2 + 2 + 2 + infoLen

        LenData = allLen.to_bytes(2, byteorder='big', signed=False)
        if self.Dbgflags == 1:
            self.displayNew('frist lenData = %s\r\n' % LenData)
        # self.ser.write(LenData)

        DesIdData = bytearray(b'\xff\xff')
        # self.ser.write(DesIdData)

        SrcIdData = bytearray(b'\x00\x00')
        # self.ser.write(SrcIdData)

        CommAndIdData = bytearray(b'\x00\x69')
        # self.ser.write(CommAndIdData)

        pathStr = self.foldername
        '''
        if getattr(sys, 'frozen', False):
            pathStr = os.path.dirname(sys.executable)
        elif __file__:
            pathStr = os.path.dirname(__file__)
        pathStr = os.path.join(pathStr, self.fileName + '.bin')
        '''
        fopen = open(pathStr, 'rb+')
        fcontent = fopen.read()
        fileLen = len(fcontent)
        filePackNumber = int(fileLen / 1024) + 1


        InfoData = bytearray(b'\x00\x00\x01')
        # self.ser.write(InfoData)

        # 程序总包数
        filePackNumber = (filePackNumber - 1) * 4 + 2
        filePackNumber = filePackNumber & 0xffff
        self.filePackNumber = filePackNumber
        filePackNumber2 = filePackNumber.to_bytes(2, byteorder='little', signed=False)
        # self.ser.write(filePackNumber2)

        # 程序总字节数
        fileLen = fileLen & 0xffffffff
        fileLen2 = fileLen.to_bytes(4, byteorder='little', signed=False)
        # self.ser.write(fileLen2)

        InfoData2 = bytearray(b'\x00\x01')
        # self.ser.write(InfoData2)

        # self.ser.write(self.fileName.encode())


        ckeckAllStr = LenData + DesIdData + SrcIdData + CommAndIdData + InfoData + \
                      filePackNumber2 + fileLen2 + InfoData2 + bytearray(self.fileName.encode())

        ckeckAllStrArray =bytearray(ckeckAllStr)

        if self.Dbgflags == 1:
            self.displayNew('ckeckAllStr = %s' % ckeckAllStr)
            # print(ckeckAllStr)
        ckeckAllStrLen = len(ckeckAllStr)
        if self.Dbgflags == 1:
            self.displayNew('ckeckAllStrLen = %s' % ckeckAllStrLen)
            # print(ckeckAllStrLen)
        sum = 0
        for i in range(0, ckeckAllStrLen):
            if self.Dbgflags == 1:
                pass
                # print(ckeckAllStrArray[i])
            sum = sum + ckeckAllStrArray[i]
        # print('sum = %02x\r\n' % sum)
        checkSumData = sum & 0xff
        checkSumData = checkSumData.to_bytes(1, byteorder='big', signed=False)
        if self.Dbgflags == 1:
            self.displayNew('ckeckSumData = %s\r\n' % checkSumData)
        # self.ser.write(checkSumData)

        PcedData = bytearray(b'\x50\x43\x45\x44')
        # self.ser.write(PcedData)
        if self.Dbgflags == 1:
            self.displayNew('PC第一次数据发送成功\r\n')
        fristPackAll = PcstData + NumNumberData + LenData + DesIdData + SrcIdData \
                       + CommAndIdData + InfoData + filePackNumber2 + fileLen2 + InfoData2 \
                       + self.fileName.encode() + checkSumData + PcedData
        # print('fristPackAll = ', fristPackAll)
        self.ser.write(fristPackAll)
        # 循环接受来自板卡的第二包数据
        count = 0
        dataAll2 = []

        startTime = time.monotonic()
        spendTime = 20
        endTime = startTime + spendTime
        recvSecondPack = ''
        while (time.monotonic() <= endTime):
            data = self.ser.read()
            data = int.from_bytes(data, byteorder='big', signed=False)
            dataAll2.append(data)
            count += 1
            if self.Dbgflags == 1:
                self.displayNew('recv = %02x\r\n' % data)
            if data == 0x44:
                if dataAll2[count-2] == 0x45 and dataAll2[count-3] == 0x54 and dataAll2[count-4] == 0x52:
                    self.displayNew("开始传输数据\r\n")
                    # 判断板卡发来的数据是否为READY,若为READY则可以发送数据给板卡
                    if dataAll2[count - 8] == 0x0b:
                        if self.Dbgflags == 1:
                            self.displayNew('跳出串口接受循环\r\n')
                        self.secondPackFlags = 1
                        i = 0
                        while len(dataAll2) > i:
                            # print('dataAll2[] = ', hex(dataAll2[i]))
                            i += 1
                        dataAll2.clear()
                        break
            self.waitAndYield(0.01)

        if self.secondPackFlags == 0:
            if self.Dbgflags == 1:
                self.displayNew('板卡发送给PC第二包未接收到\r\n')
            self.displayNew('升级结束TIMEOUT\r\n')
            return 0


        fcontentArray = bytearray(fcontent)
        ckeckAllStr = b''

        self.secondPackFlags = 0
        i = 1
        packNumber = 1

        startCount = 0
        cmpFileContent = bytearray(b'')
        NumNumberDatasz = 2
        while 1:
            self.displayNew("%s    发送包号：%d/%d    下载进度：%d%s%s\r\n" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            packNumber, (self.filePackNumber - 1), (packNumber * 100) / (self.filePackNumber - 1), "%", "100"))

            # 向板卡发送第二包数据
            PcstData = bytearray(b'\x50\x43\x53\x54')
            # self.ser.write(PcstData)

            NumNumberData = bytearray(NumNumberDatasz.to_bytes(1, byteorder='big', signed=False) )# \x0C
            # self.ser.write(NumNumberData)

            infoLen = 1030
            allLen = 2 + 2 + 2 + 2 + infoLen

            # print(allLen)
            LenData = allLen.to_bytes(2, byteorder='big', signed=False)
            # print(LenData)

            if self.Dbgflags == 1:
                self.displayNew('lenData = %s\r\n' % LenData)
            # self.ser.write(LenData)

            DesIdData = bytearray(b'\xff\xff')
            # self.ser.write(DesIdData)

            SrcIdData = bytearray(b'\x00\x00')
            # self.ser.write(SrcIdData)

            CommAndIdData = bytearray(b'\x00\x69')
            # self.ser.write(CommAndIdData)

            ps = packNumber.to_bytes(2, byteorder='little', signed=False)
            # self.ser.write(ps)
            packNumber = packNumber + 4

            # self.ser.write(b'\xff\xff\xff\xff')

            if self.Dbgflags == 1:
                self.displayNew('fileLen = %s\r\n' % fileLen)

            j = 0
            supplementFlags = 0
            # for i in range(0, filePackNumber):
            # for j in range(startCount, startCount + 1024):
            if i < (filePackNumber - 1):
                if self.Dbgflags == 1:
                    pass
                    # self.displayNew('send = %s ,i = %s\r\n' % (fcontentArray[startCount:startCount+1023], i))
                    # print('send = %s ,i = %s\r\n' % (fcontentArray[startCount:startCount+1024], i))
                    # print('run to here 3\r\n')
                # self.ser.write(fcontentArray[startCount:startCount+1024])
                ckeckAllStr = LenData + DesIdData + SrcIdData + CommAndIdData + ps + bytearray(b'\xff\xff\xff\xff') +fcontentArray[startCount:startCount+1024]
                cmpFileContent = cmpFileContent + fcontentArray[startCount:startCount+1024]
            startCount += 1024
            if self.Dbgflags == 1:
                self.displayNew('startCount = %s\r\n' % startCount)
                self.displayNew('fileLen = %s\r\n' % fileLen)
                self.displayNew('filePackNumber-1 = %s\r\n' % (filePackNumber-1))
                self.displayNew('i = %s\r\n' % i)
            bcarrary = b''
            if i >= (filePackNumber - 1):
                ckeckAllStr = LenData + DesIdData + SrcIdData + CommAndIdData + ps + bytearray(b'\xff\xff\xff\xff')
                if startCount - 1024 != fileLen:
                    # print('startCount = %s, fileLen = %s' % (startCount - 1024, fileLen))
                    # self.ser.write(fcontentArray[(startCount - 1024):(fileLen + 1)])
                    ckeckAllStr += fcontentArray[(startCount - 1024):(fileLen + 1)]
                    cmpFileContent = cmpFileContent + fcontentArray[(startCount - 1024):(fileLen + 1)]
                # self.displayNew('fileLen = %s, startCount = %s' % (fileLen, startCount))
                for l in range(fileLen, startCount):

                    bcarrary = bcarrary + b'\xff'
                # self.ser.write(bcarrary)  # 用\x00补足最后一包不足的字节
                # self.displayNew('bcarrary = %s' % bcarrary)
                ckeckAllStr += bcarrary

            if self.Dbgflags == 1:
                self.displayNew('really ckeckAllStr = %s\r\n' % ckeckAllStr)
            # print(ckeckAllStr)
            ckeckAllStrArray = bytearray(ckeckAllStr)

            ckeckAllStrLen = len(ckeckAllStr)
            # print(ckeckAllStrLen)
            sum = 0
            for j in range(0, ckeckAllStrLen):
                # print(ckeckAllStrArray[i])
                sum = sum + ckeckAllStrArray[j]
            # print('sum = %02x\r\n' % sum)
            checkSumData = sum & 0xff
            checkSumData = checkSumData.to_bytes(1, byteorder='big', signed=False)
            if self.Dbgflags == 1:
                self.displayNew('ckeckSumData = %s\r\n' % checkSumData)
                self.displayNew('ckeckSumData = %02x\r\n' % int.from_bytes(checkSumData, byteorder='big', signed=False))
            # self.ser.write(checkSumData)

            PcEndData = bytearray(b'\x50\x43\x45\x44')
            # self.ser.write(PcEndData)

            secondPackAll = PcstData + NumNumberData + ckeckAllStr + checkSumData + PcEndData
            # print('secondPackAll = ', secondPackAll)
            self.ser.write(secondPackAll)

            ckeckAllStr = b''
            if self.Dbgflags == 1:
                self.displayNew('clear ckeckAllStr = %s\r\n' % ckeckAllStr)

            # self.ser.write('\n'.encode())

            NumNumberDatasz += 1
            if self.Dbgflags == 1:
                # self.displayNew('supplementFlags = %s\r\n' % supplementFlags)
                self.displayNew('第二包发送完成\r\n')
            i += 4

            # print(cmpFileContent)
            # print(fcontentArray)
            if fcontentArray == cmpFileContent:
                # print('内容一致\r\n')
                # print('download success\r\n')
                self.displayNew('下载完成\r\n')
                startTime = time.monotonic()
                spendTime = 3
                endTime = startTime + spendTime
                reAll = ''
                while (time.monotonic() <= endTime):
                    re = self.ser.readline()
                    reAll = reAll + re.decode('utf-8', 'ignore')
                # print(reAll)
                # self.ser.close()
                return 0
            else:
                pass
                # print('内容不同\r\n')

            self.waitAndYield(0.01)

            # 第三次接收来自板卡的数据包
            count = 0
            dataAll3 = []
            startTime = time.monotonic()
            spendTime = 20
            endTime = startTime + spendTime
            recvsThirdPack = ''
            j = 0

            while (time.monotonic() <= endTime):
                data = self.ser.read()
                data = int.from_bytes(data, byteorder='big', signed=False)
                dataAll3.append(data)

                count += 1
                if self.Dbgflags == 1:
                    self.displayNew('recv = %02x\r\n' % data)
                if (data == 0x44) and (len(dataAll3) >= 24):
                    if dataAll3[count-2] == 0x45 and dataAll3[count-3] == 0x54 and dataAll3[count-4] == 0x52:

                        '''
                        if dataAll3[count - 7] == 15:
                            self.displayNew('下载完成\r\n')
                            self.ser.close()
                            return 0
            
                        '''

                        while len(dataAll3) > j:
                            # print('dataAll2[] = ', hex(dataAll3[j]))
                            j += 1
                        # print('**************baosuhao = ', hex((dataAll3[count - 6]<<8) + dataAll3[count - 7]))
                        if packNumber == ((dataAll3[count - 6]<<8) + dataAll3[count - 7]):
                            if self.Dbgflags == 1:
                                self.displayNew('跳出串口接受循环\r\n')
                            self.thirdPackFlags = 1
                            # print('#############################')
                            k = 0
                            while len(dataAll3) > k:
                                # print('dataAll3[] = ', hex(dataAll3[k]))
                                k += 1
                            dataAll3.clear()
                            # print('#############################')
                            break
                        # dataAll3.clear()
                self.waitAndYield(0.01)
            if self.thirdPackFlags == 0:
                if self.Dbgflags == 1:
                    self.displayNew('板卡发送给PC第三包未接收到\r\n')
                self.displayNew('升级结束TIMEOUT\r\n')
                # self.ser.close()
                return 0
            self.thirdPackFlags = 0



        # for i in (0, count):
        #    self.displayNew('recv = %sx' % dataAll[i])

    def downloadBtnFunc(self, event):
        if self.cmdRunFlags == 1:
            self.displayNew('请等待程序运行完成\r\n')
            return 0

        if self.forcedUpgradeflags == 1 and self.powerOnAndDownloadflags == 1:
            self.displayNew('请勿同时选择强制更新和上电下载选项\r\n')
            return 0

        if self.comPortChoice.GetSelection() == -1:
            self.displayNew('请选择串口\r\n')
            return 0

        if self.serialStatus == 0:
            self.displayNew('请先打开串口\r\n')
            return 0

        if self.fileName == '':
            self.displayNew('请选择烧写文件\r\n')
            return 0

        self.cmdRunFlags = 1

        self.displayNew('开始下载\r\n')

        self.serialBtn.Disable()

        self.readUartData()

        self.serialBtn.Enable()

        self.cmdRunFlags = 0

    def powerOnAndDownloadChkboxFunc(self, event):
        cb = event.GetEventObject()
        if cb.IsChecked():
            self.powerOnAndDownloadflags = 1
            if self.Dbgflags == 1:
                self.displayNew('上电下载准备完毕\r\n')
        else:
            self.powerOnAndDownloadflags = 0


    def forcedUpgradeChkboxFunc(self, event):
        cb = event.GetEventObject()
        if cb.IsChecked():
            self.forcedUpgradeflags = 1
            if self.Dbgflags == 1:
                self.displayNew('强制下载准备完毕\r\n')
        else:
            self.forcedUpgradeflags = 0

    def DbgChkboxFunc(self, event):
        cb = event.GetEventObject()
        if cb.IsChecked():
            self.Dbgflags = 1
            self.displayNew('打印调试信息\r\n')
        else:
            self.Dbgflags = 0

    def changePathBtnFunc(self, event):
        foldername = ''
        dialog = wx.FileDialog(None, "Choose a file",
                              style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            foldername= dialog.GetPath()
        self.filePathText.SetValue(foldername)
        self.foldername = foldername
        a = os.path.basename(foldername)
        self.fileName = a.split('.')[0]
        if self.Dbgflags == 1:
            self.displayNew('filePath = %s\r\n' % foldername)
            self.displayNew('self.fileName = %s\r\n' % self.fileName)
        pass

if __name__=='__main__':
    app = wx.App(False)
    frame = MyFrame(None, 'serial port upgrade 捷世智通 '+VERSION_STR)
    app.MainLoop()

