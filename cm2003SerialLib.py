#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Total 5 boot option
Boot Option #1          [SanDisk]
Boot Option #2          [UEFI OS (P0: SM651G...]
Boot Option #3          [UEFI: SanDisk, Part...]
Boot Option #4          [SATA  PM: SM651GE4 ...]
Boot Option #5          [UEFI: Built-in EFI ...]
'''

import serial
import os
import datetime
import ctypes
import time
import struct
import operator
import re

import locale

KEY_DEL=bytearray(b'\x1B\x5B\x33\x7E')

KEY_UP=bytearray(b'\x1B\x5B\x41')
KEY_DOWN=bytearray(b'\x1B\x5B\x42')
KEY_RIGHT=bytearray(b'\x1B\x5B\x43')
KEY_LEFT=bytearray(b'\x1B\x5B\x44')

KEY_PLUS=bytearray(b'\x2B')
KEY_MINUS=bytearray(b'\x2D')
KEY_ENTER=bytearray(b'\x0D')

KEY_ENTER_MINIOS=bytearray(b'\x0d')
KEY_UP_MINIOS=bytearray(b'\x1B\x4F\x41')
KEY_DOWN_MINIOS=bytearray(b'\x1B\x4F\x42')
KEY_RIGHT_MINIOS=bytearray(b'\x1B\x4F\x43')
KEY_LEFT_MINIOS=bytearray(b'\x1B\x4F\x44')


KEY_F4=bytearray(b'\x1B\x4F\x53')


SET_BOLD=bytearray(b'\x1B\x5B\x31\x6D')

SET_UNBOLD=bytearray(b'\x1B\x5B\x30\x6D')

setBoldStr=SET_BOLD.decode('utf-8','ignore')
setUnboldStr=SET_UNBOLD.decode('utf-8','ignore')


CLS_TERMINAL=bytearray(b'\x0C')


TIME_DIFF_THRESHOLD=60

bios_boot_keyword = [
    "Setup Prompt",
    "Bootup NumLock",
    "Quiet Boot",
    "Fast Boot",
    "Boot Option",
    "Hard Drive BBS",
    "USB Device BBS",
]

bash_keyword = [
    "@JOB",
    "grep",
    "echo",
    "flash",
    "vfat",
]

preBIOS_keyword = [
    b'Press',
    b'<DEL>',
    b'BIOS',
]

setupBIOS_keyword = [
    b'><: Select Screen',
    b'^v: Select Item',
    b'Enter: Select',
    b'+/-: Change Opt',
    b'F1: General Help',
    b'F2: Previous Values',
    b'F3: Optimized Defaults',
    b'F4: Save & Exit',
    b'ESC: Exit',
]

bootBIOS_keyword = [
    b'Setup Prompt',
    b'Bootup NumLock',
    b'Quiet Boot',
    b'Fast Boot',
    b'Boot Option',
    b'Hard Drive BBS',
    b'USB Device BBS',
]

DOS_keyword = [
    b'DOS',
    b'C:\>',
]

linux_keyword = [
    'buildroot',
    'Welcome',
    '@JOB',
    'root',
]

cm2003SerialDebug=0

def cm2003SerialDebugFunc(endis):
    #global is needed......
    global cm2003SerialDebug
    cm2003SerialDebug=int(endis)
    return


class cm2003SerialTarget(object):

    def __init__(self,comStr,baudrate=115200,timeout=0.5,dbgPtr=print,yieldPtr=time.sleep):
        self.comStr=comStr
        self.baudrate=baudrate
        self.timeout=timeout
        self.serialOpened=0
        self.dbgPtr = dbgPtr
        self.ser=None
        self.yieldPtr=yieldPtr
        
        #
        # sad......
        #
        
        locale.setlocale(locale.LC_TIME, 'C')

    def __del__(self):
        if 0!= self.serialOpened :
            self.serialCloseFunc()

    def comClear(self, delay=0.1):
        while (len(self.ser.readline()) > 0):
            time.sleep(delay)
            self.ser.reset_input_buffer()

    def serialOpenFunc(self):
        if 0!=self.serialOpened:
            # self.dbgPtr("?????????"+ self.comStr+"???????????????\r\n")
            # return -1
            return 0

        comstr=self.comStr
        try:
            self.ser=serial.Serial(port=comstr, baudrate=self.baudrate, timeout=self.timeout)
            self.ser.reset_output_buffer()
            self.ser.reset_input_buffer()
        except OSError as err:
            self.dbgPtr("#?????? ??????????????????????????????????????? %s \r\n"%err)
            return -2
        if 1==cm2003SerialDebug:
            self.dbgPtr("???????????????????????????"+ self.ser.portstr+"\r\n")
        self.serialOpened=1

        return 0

    def serialCloseFunc(self):
        if 1!=self.serialOpened:
            #self.dbgPtr("#????????????????????? ?????????\r\n")
            return -1

        self.ser.close()
        self.serialOpened=0
        return 0

    def serialIsInBiosNow(self):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        retry=0

        while(1):
            ret=self.ser.write(KEY_LEFT)
            self.waitAndYield(0.1)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')

            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+'\r\n')

            if rxstr.find('F4: Save & Exit') >=0 :
                if 1==cm2003SerialDebug:
                    self.dbgPtr("?????????????????????BIOS \r\n")
                return 1

            retry=retry+1
            if 1==cm2003SerialDebug:
                self.dbgPtr("??????bios ?????? %d\r\n"%retry)
            if retry>2:
                if 1==cm2003SerialDebug:
                    self.dbgPtr("serialIsInBiosNow ??????????????????BIOS???\r\n")
                break

        return 0

    def serialEnterBiosFunc(self):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.serialIsInBiosNow()
        if(1==ret):
            return 0

        startTime=time.monotonic()
        nowTime=startTime
        waitTime=30
        endTime=nowTime+waitTime
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)

            ret=self.ser.write(KEY_DEL)
            if 1==cm2003SerialDebug:
                self.dbgPtr("?????? DEL ????????????BIOS \r\n")
            data = self.ser.readline()
            rxstr=data.decode('utf-8','ignore')

            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('F4: Save & Exit') >=0 :
                if 1==cm2003SerialDebug:
                    self.dbgPtr("\r\n?????????????????????BIOS \r\n")
                stageSuccess=1
                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? %d ???????????????BIOS????????? ???1????????????\r\n"%waitTime)
            return -5

        return 0

    def serialScanForBootList(self,strInput):
        self.bootlist=[]

        str=strInput

        while 1:
            ret=str.find('Boot Option #')
            if ret<0:
                # print("No more Boot Option")
                break

            #cut before
            str2=str[ret:]

            ret=str2.find(']')
            if ret<0:
                # print("No more Boot Option ]")
                break

            ret=ret+1
            newStr=str2[:ret]

            ret2=newStr.find(setBoldStr)
            if ret2>=0:
                newStr2=newStr[0:ret2]+newStr[ret2+4:]
                # self.dbgPtr("change2:"+newStr2+"\r\n")
                newStr=newStr2


            ret2=newStr.find(setUnboldStr)
            if ret2>=0:
                newStr2=newStr[0:ret2]+newStr[ret2+4:]
                # self.dbgPtr("change2:"+newStr2+"\r\n")
                newStr=newStr2

            # print(newStr)
            # self.dbgPtr(newStr+'\r\n')
            self.bootlist.append(newStr)
            # print("get valid option:"+newStr)
            str=str2[ret:]

        if 1==cm2003SerialDebug:
            self.dbgPtr("Total %d boot option\r\n"%len(self.bootlist))
            for i in self.bootlist:
                self.dbgPtr(i+'\r\n')

        return 0


    def serialFindBootPageFunc(self):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.serialIsInBiosNow()
        if(1!=ret):
            self.dbgPtr("#?????? ????????????BIOS??????????????????BIOS\r\n")
            return -2

        trytry = 0
        while 1:
            self.comClear()
            if 1==cm2003SerialDebug:
                self.dbgPtr("??????BIOS????????? ??????=%d\r\n"%trytry)
            trytry += 1
            if trytry > 20:
                self.dbgPtr("#?????? ??????%d ?????????????????????BIOS????????????????????????\r\n"%trytry)
                return -3
            self.ser.write(KEY_LEFT)
            self.ser.write(KEY_UP)
            self.waitAndYield(0.1)
            rxstr = self.ser.readline().decode('utf-8','ignore')
            if (len(rxstr) < 2):
                continue
            if any(word in rxstr for word in bios_boot_keyword):
                if 1==cm2003SerialDebug:
                    self.dbgPtr("????????????????????? Boot ????????????\r\n")
                self.serialScanForBootList(rxstr)
                return 0

        return  0


    def serialGetBiosTimeFunc(self):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1
        if 1==cm2003SerialDebug:
            self.dbgPtr("????????????BIOS\r\n")
        ret=self.serialEnterBiosFunc()
        if ret<0:
            return -2

        # scan for our info
        strReturn=''
        while 1:
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????????????? ?????????\r\n")
            ret=self.ser.write(KEY_RIGHT)
            data = self.ser.readline()
            rxstr=data.decode('utf-8','ignore')

            if len(rxstr)>0 :
                pass
                #self.dbgPtr("???????????????"+rxstr+  "\r\n")

            self.waitAndYield(0.01)

            ret=rxstr.find('System Date')
            if  ret>=0 :
                newstr=rxstr[ret:]
                ret=newstr.find(']')
                strReturn=strReturn+ newstr[:ret+1]+"\r\n"

                #find  System Time
                newstr=newstr[ret+1:]
                ret=newstr.find('System Time')
                if  ret>=0 :
                    newstr=newstr[ret:]
                    ret=newstr.find(']')
                    strReturn=strReturn+ newstr[:ret+1]+"\r\n"
                break

        #self.dbgPtr("???????????????\r\n")
        return strReturn


    def serialGetFwInfoButtonFunc(self):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1
        if 1==cm2003SerialDebug:
            self.dbgPtr("????????????BIOS\r\n")
        ret=self.serialEnterBiosFunc()
        if ret<0 :
            return ret

        # scan for our info
        strReturn=''
        while 1:
            if 1==cm2003SerialDebug:
                self.dbgPtr("?????????????????????????????? ?????????\r\n")
            ret=self.ser.write(KEY_RIGHT)
            data = self.ser.readline()
            rxstr=data.decode('utf-8','ignore')

            if len(rxstr)>0 :
                pass
                #self.dbgPtr("???????????????"+rxstr+  "\r\n")

            self.waitAndYield(0.01)

            ret=rxstr.find('BIOS Version')
            if  ret>=0 :
                newstr=rxstr[ret:]
                ret=newstr.find('|')
                strReturn=strReturn+ newstr[:ret]+"\r\n"

                #find  Build Date and Time
                newstr=newstr[ret+1:]
                ret=newstr.find('Build Date and Time')
                if  ret>=0 :
                    newstr=newstr[ret:]
                    ret=newstr.find('|')
                    strReturn=strReturn+ newstr[:ret]+"\r\n"

                #find  EC Version
                newstr=newstr[ret+1:]
                ret=newstr.find('EC Version')
                if  ret>=0 :
                    newstr=newstr[ret:]
                    ret=newstr.find('|')
                    strReturn=strReturn+ newstr[:ret]+"\r\n"
                break
        #need to delete every  [0m   [1m

        while(1):
            ret2=strReturn.find(setBoldStr)
            if ret2>=0:
                newStr2=strReturn[0:ret2]+strReturn[ret2+4:]
                strReturn=newStr2
            else:
                break

        while(1):
            ret2=strReturn.find(setUnboldStr)
            if ret2>=0:
                newStr2=strReturn[0:ret2]+strReturn[ret2+4:]
                strReturn=newStr2
            else:
                break


        #self.dbgPtr("???????????????\r\n")
        return strReturn




    def serialKeyUpFunc(self):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.ser.write(KEY_UP)
        data = self.ser.readline()
        rxstr=data.decode('utf-8','ignore')
        if 1==cm2003SerialDebug:
            self.dbgPtr("\r\nserialKeyUpFunc ?????? %d???"%len(rxstr)+rxstr+  "\r\n")

        return rxstr


    def serialKeyDownFunc(self):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.ser.write(KEY_DOWN)
        data = self.ser.readline()
        rxstr=data.decode('utf-8','ignore')
        if 1==cm2003SerialDebug:
            self.dbgPtr("???????????? ?????? %d???"%len(rxstr)+rxstr+  "\r\n")

        return rxstr


    def serialScan(self,txArray,rxExpect,timeoutSec=60.0):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        timeStarted=time.clock()

        while(1):
            if None!=txArray:
                self.ser.write(txArray)

            data = self.ser.readline()
            rxstr=data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????? ?????? %d???"%len(rxstr)+rxstr+  "\r\n")

            ret=rxstr.find(rxExpect)
            if ret>=0:
                self.dbgPtr("\r\n??????????????????????????? \" %s \" ??????\r\n"%rxExpect)
                return 0

            #self.waitAndYield(0.1)

            self.waitAndYield(0.01)

            timeNow=time.clock()
            timediff=timeNow-timeStarted
            if timediff>timeoutSec:
                self.dbgPtr("\r\n#???????????????????????????????????????????????????\r\n")
                return -2


    def serialBiosWriteF4SaveAndExit(self):
        self.ser.reset_output_buffer()
        self.ser.reset_input_buffer()
        self.ser.readline()
        self.ser.write(KEY_F4)
        self.waitAndYield(0.5)
        self.ser.write(KEY_ENTER)
        # print('Enter F4 Save and Exit')
        # return 0


    def serialSetFirstBoot(self,str):
        currentFirst=self.bootlist[0]
        if currentFirst.find(str) >=0:
            if currentFirst.find("Boot Option #1") >=0:
                if 1==cm2003SerialDebug:
                    self.dbgPtr("Boot Option #1 ??????????????????\r\n")
                    self.dbgPtr("?????? F4 ??????????????????????????????\r\n")
                self.serialBiosWriteF4SaveAndExit()
                return 1

        count=0
        while 1:
            strRet=self.serialKeyUpFunc()
            '''
            [1mBoot Option #2[0m          [1m[UEFI: SanDisk, Part...]
            part 1   bold start, unbold end
            part 2   bold start, ] end
            '''
            strReal=''

            ret=strRet.find(setBoldStr)
            if ret >=0:
                tmpStr=strRet[ret+4:]
                ret=tmpStr.find(setUnboldStr)
                if ret >=0:
                    strPart1=tmpStr[0:ret]
                    strReal+=strPart1
                    tmpStr=tmpStr[ret+4:]

                    ret=tmpStr.find(setBoldStr)
                    if ret >=0:
                        tmpStr=tmpStr[ret+4:]
                        ret=tmpStr.find(']')
                        if ret >=0:
                            strPart1=tmpStr[0:ret+1]
                            strReal+=strPart1


            if 0==(len(strReal)):
                continue


            if(strReal.find('Boot Option')<0):
                if 1==cm2003SerialDebug:
                    self.dbgPtr("Bad Current Option :"+strReal+"\r\n")
                if any(word in strReal for word in bios_boot_keyword):
                    continue
                else :
                    self.dbgPtr("#?????? ??????BIOS??????????????????????????????????????? \r\n")
                    return -2

            if 1==cm2003SerialDebug:
                self.dbgPtr("CurrentOption :"+strReal+"\r\n")

            #if(strReal.find('Boot Option')<0):
            #    if(strReal.find('Hard Drive BB')<0):
            #        self.dbgPtr("#?????? ???????????????????????????????????? \r\n")
            #       return -2


            ret=strRet.find(str)
            if ret >=0:
                ret2=strRet.find('Boot Option #1')
                if ret2 >=0:
                    if 1==cm2003SerialDebug:
                        self.dbgPtr("????????? Boot Option #1 !!\r\n" + "?????? F4 ???????????????????????????\r\n")

                    self.serialBiosWriteF4SaveAndExit()
                    return 1
                else :
                    if 1== cm2003SerialDebug:
                        self.dbgPtr("???????????????"+strRet+"  ?????? KEY_PLUS  \r\n")

                    self.ser.write(KEY_PLUS)

            self.waitAndYield(0.1)

            count=count+1
            if count >10:
                self.dbgPtr("#?????? ???????????????????????????????????? \r\n")
                return -2

        return 0


    def serialCheckIfInDosNow(self):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? serialCheckIfInDosNow ???????????????\r\n")
            return -1

        self.ser.write(KEY_ENTER)
        data = self.ser.readline()
        rxstr=data.decode('utf-8','ignore')
        if 1==cm2003SerialDebug:
            self.dbgPtr("????????????: "+rxstr+  "\r\n")

        ret=rxstr.find("C:\>")
        if ret>=0:
            if 1==cm2003SerialDebug:
                self.dbgPtr("\r\n????????? \"C:\>\"  ???????????????DOS??????????????????\r\n")
            return 1
        if 1==cm2003SerialDebug:
            self.dbgPtr("\r\n???????????? \"C:\>\"  ????????????DOS??????????????????\r\n")

        # if we get bios time or ec version, then press ENTER
        # language will pop out.....so write a enter again to avoid this
        ret=rxstr.find("System Language")
        if ret>=0:
            if 1==cm2003SerialDebug:
                self.dbgPtr("\r\n?????????System Language write ENTER again\"  ???????????????DOS??????????????????\r\n")
            self.ser.write(KEY_ENTER)
            data = self.ser.readline()


        return 0


    def serialWaitBootUC(self,skipBios):

        #OK, we are rebooting
        bootTime=time.monotonic()
        #stage 1 wait BIOS 60 second
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+60
        stageSuccess=0

        if 0==skipBios:
            while(nowTime<=endTime):
                nowTime=time.monotonic()
                self.waitAndYield(0.01)
                data = self.ser.readline()
                rxstr = data.decode('utf-8','ignore')
                if 1==cm2003SerialDebug:
                    self.dbgPtr("???????????????"+rxstr+  "\r\n")

                if rxstr.find('BIOS') >=0 :
                    stageSuccess=1
                    if 1==cm2003SerialDebug:
                        self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? BIOS??????\r\n"%(nowTime-bootTime,nowTime-startTime))
                    break

            if 0==stageSuccess:
                self.dbgPtr("#?????? ????????????????????? BIOS?????? ?????????\r\n")
                self.serialCloseFunc()
                return -3

        #stage 2 wait DOS for 30 sec
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+30
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('C:\>') >=0 :
                stageSuccess=1
                if 1==cm2003SerialDebug:
                    self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? DOS ?????? \r\n"%(nowTime-bootTime,nowTime-startTime))
                break

            if rxstr.find('DOS') >=0 :
                stageSuccess=1
                #if 1==cm2003SerialDebug:
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? DOS ?????? [DOS]\r\n"%(nowTime-bootTime,nowTime-startTime))
                self.waitAndYield(0.5)
                break


            if rxstr.find('GRUB') >=0 :
                self.dbgPtr("#?????? ?????? %f ??? (?????? %f ???) ????????? GRUB?????? ???????????????????????????DOS!\r\n"%(nowTime-bootTime,nowTime-startTime))
                self.dbgPtr("#?????? ???????????????????????? \"??????U???DOS??????\" ???????????? ????????????U???DOS?????????\r\n")
                return -5

            if rxstr.find('Linux version') >=0 :
                self.dbgPtr("#?????? ?????? %f ??? (?????? %f ???) ????????? Linux ?????? ???????????????????????????DOS!\r\n"%(nowTime-bootTime,nowTime-startTime))
                self.dbgPtr("#?????? ???????????????????????? \"??????U???DOS??????\" ???????????? ????????????U???DOS?????????\r\n")
                return -5

        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? DOS?????? ?????????\r\n")
            self.serialCloseFunc()
            return -4

        self.dbgPtr("[ OK ] DOS????????????\r\n")

        return 0


    def serialBootUCFunc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.serialCheckIfInDosNow()
        if(ret==1):
            self.dbgPtr("[ OK ] DOS????????????\r\n")
            self.serialCloseFunc()
            return 0

        if 1==cm2003SerialDebug:
            self.dbgPtr("?????????DOS???????????????  ?????????????????????????????? \r\n")

        ret=self.serialEnterBiosFunc()
        if ret<0 :
            return ret

        self.serialFindBootPageFunc()

        bootStr=''

        for i in self.bootlist:
            ret=i.find('UEFI')
            if ret >=0:
                continue

            ret=i.find('SATA')
            if ret >=0:
                continue

            bootStr=i
            break

        if 0==len(bootStr):
            self.dbgPtr("#?????? ?????????U???DOS????????????"+"\r\n")
            return -10

        #self.dbgPtr("??????????????? "+bootStr +"\r\n")
        ret=bootStr.find('[')
        str2=bootStr[ret:]

        ret=str2.find(']')
        ret=ret+1
        newStr=str2[:ret]
        if 1==cm2003SerialDebug:
            self.dbgPtr("??????????????? "+newStr+"\r\n")

        #self.serialFindBootPageFunc()
        ret=self.serialSetFirstBoot(newStr)

        if(ret<0):
            self.serialCloseFunc()
            return ret
        '''
        self.serialScan(KEY_ENTER,"C:\>")

        ret=self.serialCheckIfInDosNow()
        if(1==ret):
            self.dbgPtr("??????????????????DOS ????????????\r\n")
        else :
            self.dbgPtr("#?????? ??????????????????DOS??? ????????????\r\n")
        '''
        ret=self.serialWaitBootUC(1)
        self.serialCloseFunc()

        return ret


    def serialCheckIfInUEFIUDISK(self):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        retry=0

        while(1):
            ret=self.ser.write(KEY_ENTER)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')

            self.waitAndYield(0.5)
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")
            '''
            if 0 == len(rxstr):
                #self.dbgPtr("serialIsInBiosNow rx ?????????0 ?????? 0\r\n")
                retry=retry+1
                if retry< 5:
                    continue

                self.dbgPtr("?????????????????? # ???????????? LINUX?????????\r\n")
                return 0
            '''

            if rxstr.find('#') >=0 :
                if 1==cm2003SerialDebug:
                    self.dbgPtr("?????? # ????????? ???????????? LINUX ??????\r\n")
                return 1
            elif rxstr.find('MODE=C') >=0 :
                self.dbgPtr("#?????? ?????????GPIO???????????? ????????? ????????????\r\n")
                self.serialCloseFunc()
                return -10
            else:
                retry=retry+1
                if retry< 5:
                    continue
                self.dbgPtr("?????????????????? # ???????????? LINUX?????????\r\n")
                return 0

        return 0

    def serialCheckMountSdb1InLinux(self):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1
        cmdStr="mount\r\n"
        cmdArray=cmdStr.encode()


        retry=0
        ret=self.ser.write(cmdArray)
        while(1):
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1== cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('/dev/sdb1') >=0 :
                if 1==cm2003SerialDebug:
                    self.dbgPtr("/dev/sdb1 ????????????\r\n")
                return 1

        return 0

    # waitType type=0 normal
    # waitType type=0xa  MODE-A
    # waitType type=0xb  MODE-B
    # waitType type=0xc  ignore type print, MODE-A MODE-B MODE-C all OK
    def serialWaitBootUU(self,waitType):
        #OK, we are rebooting
        bootTime=time.monotonic()
        #stage 1 wait grub for 10 second
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+10
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('GRUB') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? GRUB??????\r\n"%(nowTime-bootTime,nowTime-startTime))
                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? GRUB?????? ?????????\r\n")
            self.serialCloseFunc()
            return -3

        #stage 2 wait linux for 40 sec
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+60
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('Linux version') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? LINUX???????????????\r\n"%(nowTime-bootTime,nowTime-startTime))
                break

            if rxstr.find('Zone ranges') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? LINUX??????????????? (Zone ranges) \r\n"%(nowTime-bootTime,nowTime-startTime))
                break

            if rxstr.find('[    0.000000]') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? LINUX??????????????? ([    0.000000])\r\n"%(nowTime-bootTime,nowTime-startTime))
                break



        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? LINUX???????????? ?????????\r\n")
            self.serialCloseFunc()
            return -4


        #stage 3 wait buildroot for 30 sec
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+30
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            rxstr = self.ser.readline().decode('utf-8','ignore')
            if (len(rxstr) < 1):
                continue
            if 1==cm2003SerialDebug:
                self.dbgPtr("HERE???????????????"+rxstr+  "\r\n")
            if any(word in rxstr for word in linux_keyword):
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? buildroot ??????\r\n"%(nowTime-bootTime,nowTime-startTime))
                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? buildroot ?????? ?????????\r\n")
            self.serialCloseFunc()
            return -5

        #stage 4 wait usb-once.sh for 40 sec
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+40
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('usb-once.sh') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? usb-once.sh \r\n"%(nowTime-bootTime,nowTime-startTime))
                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? usb-once.sh ???????????? sata ????????? ???????????????????????????\r\n")
            cmdStr="/root/mnt-usb/usb-jobs/flash-vfat.sh \n"
            cmdArray=cmdStr.encode()
            self.ser.write(cmdArray)


            startTime=time.monotonic()
            nowTime=startTime
            endTime=nowTime+20
            stageSuccess=0

            while(nowTime<=endTime):
                nowTime=time.monotonic()
                self.waitAndYield(0.01)
                data = self.ser.readline()
                rxstr = data.decode('utf-8','ignore')
                if 1==cm2003SerialDebug:
                    self.dbgPtr("???????????????"+rxstr+  "\r\n")

                if rxstr.find('/root/mnt-usb/usb-jobs/flash-vfat.sh FINISH!') >=0 :
                    stageSuccess=1
                    self.dbgPtr("?????? %f ??? (?????? %f ???) ????????????????????????USB?????????\r\n"%(nowTime-bootTime,nowTime-startTime))
                    break


            self.serialCloseFunc()
            return -10

        #stage 5 wait MODE=X for 40 sec
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+40
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if (rxstr.find('MODE=A') >=0) :
                if 0xb==waitType:
                    self.dbgPtr("#?????? ???B??????????????????  MODE=A ??????GPI?????? \r\n")
                    return -9

                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? MODE=A \r\n"%(nowTime-bootTime,nowTime-startTime))
                break

            elif (rxstr.find('MODE=B') >=0) :
                if 0xa==waitType:
                    self.dbgPtr("#?????? ???A??????????????????  MODE=B ??????GPI?????? \r\n")
                    return -10

                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? MODE=B \r\n"%(nowTime-bootTime,nowTime-startTime))
                break

            elif (rxstr.find('MODE=C') >=0) :
                if 0xc==waitType:
                    stageSuccess=1
                    self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? MODE=C \r\n"%(nowTime-bootTime,nowTime-startTime))
                    break

                self.dbgPtr("##?????? ?????? %f ??? (?????? %f ???) ????????? MODE=C ??????GPIO???????????????????????????????????????\r\n"%(nowTime-bootTime,nowTime-startTime))
                self.serialCloseFunc()
                return -6

        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? MODE=?? ?????????\r\n")
            self.serialCloseFunc()
            return -7


        self.waitAndYield(2)

        mountSuccess=0
        count=0
        startTime=time.monotonic()
        while(1):
            ret=self.serialCheckMountSdb1InLinux()
            self.waitAndYield(0.5)
            if(1==ret):
                mountSuccess=1
                nowTime=time.monotonic()
                # self.dbgPtr("?????? %f ??? (?????? %f ???) ?????????U??????????????????LINUX???????????????\r\n"%(nowTime-bootTime,nowTime-startTime))
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? U?????????\r\n"%(nowTime-bootTime,nowTime-startTime))
                self.dbgPtr("[ OK ] LINUX????????????\r\n")
                break;
            else :
                count=count+1
                if(count>5):
                    self.dbgPtr("#?????? ????????????????????????U????????? ??????????????????\r\n")
                    self.serialCloseFunc()
                    return -8

        return 0



    def serialBootUUFunc(self,isModeCok):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        if 1==cm2003SerialDebug:
            self.dbgPtr("????????????BIOS ???????????????????????????\r\n")

        ret=self.serialEnterBiosFunc()
        if ret<0 :
            return ret

        self.serialFindBootPageFunc()
        bootStr=''

        for i in self.bootlist:
            ret=i.find('UEFI')
            if ret <0:
                continue

            ret=i.find('Built-in')
            if ret >=0:
                continue

            ret=i.find('SM651')
            if ret >=0:
                continue

            bootStr=i
            break

        if 0==len(bootStr):
            self.dbgPtr("#?????? ?????????U???UEFI????????????"+"\r\n")
            self.serialCloseFunc()
            return -2

        #self.dbgPtr("??????????????? "+bootStr +"\r\n")
        ret=bootStr.find('[')
        str2=bootStr[ret:]

        ret=str2.find(']')
        ret=ret+1
        newStr=str2[:ret]
        if 1==cm2003SerialDebug:
            self.dbgPtr("??????????????? "+newStr+"\r\n")

        #self.serialFindBootPageFunc()
        ret=self.serialSetFirstBoot(newStr)
        if(ret<0):
            self.serialCloseFunc()
            return ret
        '''
        self.serialScan(KEY_ENTER,"login:")
        '''

        if 1==isModeCok:
            ret=self.serialWaitBootUU(0xc)
        else:
            ret=self.serialWaitBootUU(0)
        self.serialCloseFunc()

        return ret


    def serialWaitBootLC(self):
        #OK, we are rebooting
        bootTime=time.monotonic()
        #stage 1 wait grub for 10 second
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+10
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('GRUB') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? GRUB??????\r\n"%(nowTime-bootTime,nowTime-startTime))
                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? GRUB?????? ?????????\r\n")
            self.serialCloseFunc()
            return -3

        #stage 2 wait linux for 40 sec
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+40
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('Linux version') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? MINIOS?????????\r\n"%(nowTime-bootTime,nowTime-startTime))
                break

            if rxstr.find('Zone ranges') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? MINIOS????????? (Zone ranges) \r\n"%(nowTime-bootTime,nowTime-startTime))
                break

            if rxstr.find('Initmem setup') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? MINIOS????????? (Initmem setup) \r\n"%(nowTime-bootTime,nowTime-startTime))
                break


        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? MINIOS?????? ?????????\r\n")
            self.serialCloseFunc()
            return -4


        #stage 3 wait miniOS login: for 40 sec
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+40
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('miniOS login:') >=0 :
                stageSuccess=1
                # self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? miniOS login: minios??????????????????\r\n"%(nowTime-bootTime,nowTime-startTime))
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? MINIOS????????????\r\n"%(nowTime-bootTime,nowTime-startTime))

                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? miniOS login: ?????? ?????????\r\n")
            self.serialCloseFunc()
            return -5


        # self.dbgPtr("?????????????????? ??????????????????(minios) ????????????\r\n")
        self.dbgPtr("[ OK ] MINIOS????????????\r\n")

        return 0

    def serialBootLCFunc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1
        if 1==cm2003SerialDebug:
            self.dbgPtr("??????????????????\r\n")

        ret=self.serialEnterBiosFunc()
        if ret<0 :
            return ret

        self.serialFindBootPageFunc()

        bootStr=''

        for i in self.bootlist:
            ret=i.find('UEFI')
            if ret >=0:
                continue

            ret=i.find('SM651')
            if ret >=0:
                bootStr=i
                break

        if 0==len(bootStr):
            self.dbgPtr("#?????? ?????????????????????????????????"+"\r\n")
            return -10

        #self.dbgPtr("??????????????? "+bootStr +"\r\n")
        ret=bootStr.find('[')
        str2=bootStr[ret:]

        ret=str2.find(']')
        ret=ret+1
        newStr=str2[:ret]
        if 1==cm2003SerialDebug:
            self.dbgPtr("??????????????? "+newStr+"\r\n")

        #self.serialFindBootPageFunc()

        #self.serialSetFirstBoot(newStr)
        ret=self.serialSetFirstBoot(newStr)
        if(ret<0):
            self.serialCloseFunc()
            return ret

        '''
        ret=self.serialScan(KEY_ENTER,"miniOS login: ",40.0)

        if(0==ret):
            self.dbgPtr("?????????????????? ??????????????????(minios) ????????????\r\n")
        else :
            self.dbgPtr("#?????? ?????????????????? ??????????????????(minios) ????????????\r\n")
        '''

        ret=self.serialWaitBootLC()
        self.serialCloseFunc()
        return ret

    # waitType type=0 normal
    # waitType type=0xa  MODE-A
    # waitType type=0xb  MODE-B

    def serialWaitBootLU(self,waitType):

        #OK, we are rebooting
        bootTime=time.monotonic()
        #stage 1 wait grub for 10 second
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+10
        stageSuccess=0
        currentMode=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('GRUB') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? GRUB??????\r\n"%(nowTime-bootTime,nowTime-startTime))
                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? GRUB?????? ?????????\r\n")
            self.serialCloseFunc()
            return -3

        #stage 2 wait linux for 60 sec
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+60
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('Linux version') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? LINUX???????????????\r\n"%(nowTime-bootTime,nowTime-startTime))
                break
            if rxstr.find('Zone ranges') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? LINUX??????????????? (Zone ranges) \r\n"%(nowTime-bootTime,nowTime-startTime))
                break
            if rxstr.find('[    0.000000]') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? LINUX??????????????? ([    0.000000])\r\n"%(nowTime-bootTime,nowTime-startTime))
                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? LINUX???????????? ?????????\r\n")
            self.serialCloseFunc()
            return -4


        #stage 3 wait buildroot for 40 sec
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+40
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('Welcome to Buildroot') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? buildroot ??????\r\n"%(nowTime-bootTime,nowTime-startTime))
                break

            if rxstr.find('buildroot login') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? buildroot ?????? (buildroot login)\r\n"%(nowTime-bootTime,nowTime-startTime))
                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? buildroot ?????? ?????????\r\n")
            self.serialCloseFunc()
            return -5

        #stage 4 wait flash-once.sh for 40 sec
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+40
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('flash-once.sh') >=0 :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? flash-once.sh \r\n"%(nowTime-bootTime,nowTime-startTime))
                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? flash-once.sh ?????????\r\n")
            self.dbgPtr("#?????? ????????????????????????U???????????????U????????????????????????\r\n")
            self.serialCloseFunc()
            return -5

        #stage 5 wait MODE=X for 30 sec
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+30
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if (rxstr.find('MODE=A') >=0) :
                stageSuccess=1
                currentMode=0xa
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? MODE=A \r\n"%(nowTime-bootTime,nowTime-startTime))
                if 0xb==waitType:
                    self.dbgPtr("#?????? ???B??????????????????  MODE=A ??????GPI?????? \r\n")
                    return -9

                break

            elif (rxstr.find('MODE=B') >=0) :
                stageSuccess=1
                currentMode=0xb
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? MODE=B \r\n"%(nowTime-bootTime,nowTime-startTime))
                if 0xa==waitType:
                    self.dbgPtr("#?????? ???A??????????????????  MODE=B ??????GPI?????? \r\n")
                    return -10
                break

            elif (rxstr.find('MODE=C') >=0) :
                stageSuccess=1
                self.dbgPtr("##?????? ?????? %f ??? (?????? %f ???) ????????? MODE=C ??????GPIO???????????????????????????????????????\r\n"%(nowTime-bootTime,nowTime-startTime))
                self.serialCloseFunc()
                return -6

        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? MODE=?? ?????????\r\n")
            self.serialCloseFunc()
            return -7


        #stage 6 wait TEST-TIME for 50 sec
        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+50
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if (rxstr.find('TEST-TIME') >=0) :
                stageSuccess=1
                self.dbgPtr("?????? %f ??? (?????? %f ???) ????????? TEST-TIME ???????????????????????????\r\n"%(nowTime-bootTime,nowTime-startTime))

                #@   DATE=2019/01/14-16:34:56            TEST-TIME=130 s
                #parse the time!
                ret=rxstr.find('DATE=')
                if ret>0:

                    timeStr=rxstr[ret+5:]
                    #self.dbgPtr("timeStr %s\r\n"%(timeStr))
                    ret=timeStr.find('-')
                    if ret >=0:
                        t1Str=timeStr[:ret]
                        #self.dbgPtr("t1Str %s\r\n"%(t1Str))
                        timeStr=timeStr[ret+1:]

                        ret=timeStr.find(' ')
                        if ret>0:
                            #self.dbgPtr("timeStr %s\r\n"%(timeStr))
                            timeStr=timeStr[:ret]
                            timeStr=timeStr.rstrip()
                            t1Str=t1Str+' '+timeStr

                            self.dbgPtr("???????????? %s\r\n"%(t1Str))
                            
                            
                            '''
                            ???????????????????????????????????????
                            Unable to set default locale: 'unsupported locale setting'
                            ???????????????????????????
                            
                            '''
                            
                            
                            time_locale = locale.setlocale(locale.LC_TIME)
                            
                            #locale.setlocale(locale.LC_ALL, 'C')
                            
                            locale.setlocale(locale.LC_TIME, 'C')
                            boardtime=datetime.datetime.strptime(t1Str,"%Y/%m/%d %H:%M:%S")
                            
                            
                            #locale.setlocale(locale.LC_TIME, time_locale)

                            
                            nowtime=datetime.datetime.now()
                            
                            str=nowtime.strftime('%Y/%m/%d %H:%M:%S')
                            self.dbgPtr("???????????? %s\r\n"%(str))

                            if boardtime>=nowtime:
                                diff=boardtime-nowtime
                                boardLater=1
                            else:
                                diff=nowtime-boardtime
                                boardLater=0


                            if 1==boardLater:
                                op=' >= '
                            else:
                                op=' <  '

                            if diff.days>0:
                                # self.dbgPtr("#????????? ????????????%s???????????? %d ??? %d ???  ?????? %d ???\r\n"%(op,diff.days,diff.seconds,TIME_DIFF_THRESHOLD))
                                self.dbgPtr("[ !! ] ????????????-?????????!!!! ????????????%s???????????? %d ??? %d ???  ?????? %d ???\r\n"%(op,diff.days,diff.seconds,TIME_DIFF_THRESHOLD))
                                ret=-11
                                return ret
                            else:
                                if diff.seconds>TIME_DIFF_THRESHOLD:
                                    # self.dbgPtr("#????????? ????????????%s???????????? 0 ??? %d ???  ?????? %d ???\r\n"%(op,diff.seconds,TIME_DIFF_THRESHOLD))
                                    self.dbgPtr("[ !! ] ????????????-?????????!!!! ????????????%s???????????? 0 ??? %d ???  ?????? %d ???\r\n"%(op,diff.seconds,TIME_DIFF_THRESHOLD))
                                    ret=-110
                                    return ret
                                else:
                                    # self.dbgPtr("   ?????? ????????????%s???????????? 0 ??? %d ???  ????????? %d ???\r\n"%(op,diff.seconds,TIME_DIFF_THRESHOLD))
                                    self.dbgPtr("[ OK ] ????????????-??????\r\n")
                                    ret=0



                #parse the time ends

                if 0xa==currentMode:
                    self.dbgPtr("[ OK ] LINUX??????????????????\r\n")
                elif 0xb==currentMode:
                    self.dbgPtr("[ OK ] LINUX?????????????????? MODE=B ???????????????????????????????????????\r\n")
                else:
                    self.dbgPtr("\r\n[ ??? ] MODE ?????? A ????????? B?? ??????\r\n")
                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? TEST-TIME ?????????????????????????????????????????????????????????LINUX\r\n")
            self.serialCloseFunc()
            return -8

        return 0

    # waitType type=0 normal
    # waitType type=0xa  MODE-A
    # waitType type=0xb  MODE-B
    def serialBootLUFunc(self,waitType):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        self.dbgPtr("!!!!> ????????????U??? <!!!!\r\n!!!!> ????????????U??? <!!!!\r\n!!!!> ????????????U??? <!!!!\r\n")

        ret=self.serialEnterBiosFunc()
        if ret<0 :
            return ret

        self.serialFindBootPageFunc()

        bootStr=''

        for i in self.bootlist:
            ret=i.find('UEFI')
            if ret <0:
                continue

            ret=i.find('Built-in')
            if ret >=0:
                continue

            ret=i.find('SM651')
            if ret >=0:
                bootStr=i
                break

        if 0==len(bootStr):
            self.dbgPtr("#?????? ???????????????UEFI????????????"+"\r\n")
            return -10

        #self.dbgPtr("??????????????? "+bootStr +"\r\n")
        ret=bootStr.find('[')
        str2=bootStr[ret:]

        ret=str2.find(']')
        ret=ret+1
        newStr=str2[:ret]
        if 1==cm2003SerialDebug:
            self.dbgPtr("??????????????? "+newStr+"\r\n")

        #self.serialFindBootPageFunc()
        #self.serialSetFirstBoot(newStr)
        ret=self.serialSetFirstBoot(newStr)
        if(ret<0):
            self.serialCloseFunc()
            return ret


        ret=self.serialWaitBootLU(waitType)

        self.serialCloseFunc()

        return  ret



    def dosExecCmdFunc(self,cmdStr,waitSec=0):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1
        if 1==cm2003SerialDebug:
            self.dbgPtr("??????DOS??????:"+cmdStr+"\r\n")

        cmdStr=cmdStr+'\r\n'
        cmdArray=cmdStr.encode()
        self.ser.write(cmdArray)

        data = self.ser.readline()
        rxstr=data.decode('utf-8','ignore')
        if 1==cm2003SerialDebug:
            self.dbgPtr("????????????:"+rxstr+  "\r\n")

        ret=0
        for i in range (60):
            self.waitAndYield(0.5)
            ret=self.serialCheckIfInDosNow()
            if (1==ret):
                if 1==cm2003SerialDebug:
                    self.dbgPtr("??????????????????\r\n")
                break

        if 0==ret:
             self.dbgPtr("#?????? ?????????????????????\r\n")

        return ret

    def dosWriteFirmwareSerdesFunc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.serialCheckIfInDosNow()
        if(ret!=1):
            self.dbgPtr("#?????? ????????????DOS?????????????????????????????????\r\n")
            self.serialCloseFunc()
            return -2

        self.dosExecCmdFunc("cls")
        cmd="eeupdate /nic=1 /d SERDES.bin"
        ret=self.dosExecCmdFunc(cmd)
        if 1!=ret:
            self.dbgPtr("#?????? ????????????:"+cmd+" ?????? ?????? %d ????????????\r\n"%ret)
            self.serialCloseFunc()
            return -3

        #self.dosExecCmdFunc("cls")
        cmd="eeupdate /nic=2 /d SERDES.bin"
        ret=self.dosExecCmdFunc(cmd)
        if 1!=ret:
            self.dbgPtr("#?????? ????????????:"+cmd+" ?????? ?????? %d ????????????\r\n"%ret)
            self.serialCloseFunc()
            return -4

        #self.dosExecCmdFunc("cls")
        cmd="eeupdate /nic=3 /d SERDES.bin"
        ret=self.dosExecCmdFunc(cmd)
        if 1!=ret:
            self.dbgPtr("#?????? ????????????:"+cmd+" ?????? ?????? %d ????????????\r\n"%ret)
            self.serialCloseFunc()
            return -5


        self.dbgPtr("?????? SERDES ???????????????????????? ????????????\r\n")
        self.serialCloseFunc()
        return  0

    def dosWriteFirmwareFiberFunc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.serialCheckIfInDosNow()
        if(ret!=1):
            self.dbgPtr("#?????? ????????????DOS?????????????????????????????????\r\n")
            self.serialCloseFunc()
            return -2

        self.dosExecCmdFunc("cls")
        cmd="eeupdate /nic=1 /d I210IS4.bin"
        ret=self.dosExecCmdFunc(cmd)
        if 1!=ret:
            self.dbgPtr("#?????? ????????????:"+cmd+" ?????? ?????? %d ????????????\r\n"%ret)
            self.serialCloseFunc()
            return -3

        #self.dosExecCmdFunc("cls")
        cmd="eeupdate /nic=2 /d I210IS4.bin"
        ret=self.dosExecCmdFunc(cmd)
        if 1!=ret:
            self.dbgPtr("#?????? ????????????:"+cmd+" ?????? ?????? %d ????????????\r\n"%ret)
            self.serialCloseFunc()
            return -4

        #self.dosExecCmdFunc("cls")
        cmd="eeupdate /nic=3 /d I210IS4.bin"
        ret=self.dosExecCmdFunc(cmd)
        if 1!=ret:
            self.dbgPtr("#?????? ????????????:"+cmd+" ?????? ?????? %d ????????????\r\n"%ret)
            self.serialCloseFunc()
            return -5


        self.dbgPtr("?????? FIBER ???????????????????????? ????????????\r\n")
        self.serialCloseFunc()
        return  0

    def dosWriteFirmwareHalfSerdesFunc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.serialCheckIfInDosNow()
        if(ret!=1):
            self.dbgPtr("#?????? ????????????DOS?????????????????????????????????\r\n")
            self.serialCloseFunc()
            return -2

        self.dosExecCmdFunc("cls")
        cmd="eeupdate /nic=1 /d half.bin"
        ret=self.dosExecCmdFunc(cmd)
        if 1!=ret:
            self.dbgPtr("#?????? ????????????:"+cmd+" ?????? ?????? %d ????????????\r\n"%ret)
            self.serialCloseFunc()
            return -3

        self.dosExecCmdFunc("cls")
        cmd="eeupdate /nic=2 /d half.bin"
        ret=self.dosExecCmdFunc(cmd)
        if 1!=ret:
            self.dbgPtr("#?????? ????????????:"+cmd+" ?????? ?????? %d ????????????\r\n"%ret)
            self.serialCloseFunc()
            return -4

        self.dosExecCmdFunc("cls")
        cmd="eeupdate /nic=3 /d half.bin"
        ret=self.dosExecCmdFunc(cmd)
        if 1!=ret:
            self.dbgPtr("#?????? ????????????:"+cmd+" ?????? ?????? %d ????????????\r\n"%ret)
            self.serialCloseFunc()
            return -5


        self.dbgPtr("?????? HALF-SERDES ???????????????????????? ????????????\r\n")
        self.serialCloseFunc()
        return  0

    def dosWriteFirmwareNew(self,filename):
        filename=filename.upper()

        if 0!=operator.eq(filename,'SERDES.BIN') \
            and 0!=operator.eq(filename,'I210IS4.BIN') \
            and 0!=operator.eq(filename,'HALF.BIN') :

            self.dbgPtr("#?????? ???????????????????????? %s\r\n"%filename)
            return -1


        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -2

        # self.dbgPtr("?????????????????? %s ????????????\r\n"%filename)
        self.dbgPtr("\r\n%s????????????, ????????????, ???????????????\r\n"%filename)

        #macStr=maclist[0]
        startTime=time.monotonic()

        for i in range(3):
            nicNum=i+1
            cmd="eeupdate /nic=%d /d %s"%(nicNum,filename)
            beginTime=time.monotonic()

            #stage 1 write cmd and wait for 8086-xxxx

            nowTime=time.monotonic()
            endTime=nowTime+30
            stageSuccess=0


            #cmd=cmd+'\r\n'
            cmdArray=cmd.encode()
            #self.dbgPtr("%f???????????? %s"%(nowTime-startTime,cmd))

            self.ser.write(cmdArray)

            self.waitAndYield(0.1)
            self.ser.write('\r\n'.encode())
            foundinfo=0
            infostr=''



            updateImageDone=0


            while(nowTime<=endTime):
                self.waitAndYield(0.1)
                data = self.ser.readline()
                nowTime=time.monotonic()
                rxstr = data.decode('utf-8','ignore')

                if 1==cm2003SerialDebug:
                    rxlen=len(rxstr)
                    if rxlen>0:
                        self.dbgPtr(("%f ????????????(%d)???"%(nowTime-startTime,rxlen))+rxstr+  "\r\n")

                str=rxstr
                if 0==foundinfo :
                    for i in range (3):
                        ret=str.find('8086')
                        if ret >=16:
                            macStr=str[ret-16:]
                            ret=macStr.find('Connection')
                            if ret >=0:
                                str=macStr[ret:]
                                macStr=macStr[:ret]
                                infostr=infostr+(macStr+"\r\n")
                                if 2==i:
                                    foundinfo=1
                                    self.dbgPtr(("[%f]\r\n%s"%(nowTime-startTime,infostr)))


                ret= str.find("Shared Flash image updated ")
                if ret>=4:
                    ret=ret-4
                    str2=str[ret:]
                    ret= str2.find("successfully")
                    if ret>=0:
                        ret=ret+len("successfully")
                        info=str2[:ret]
                        self.dbgPtr(("[%f] %s"%(nowTime-startTime,info))+"\r\n")
                        updateImageDone=1
                        stageSuccess=1
                        break

            if 0==stageSuccess:
                self.dbgPtr("#?????? ????????????????????????%d ??????\r\n"%nicNum)
                self.serialCloseFunc()
                return -3
        # self.dbgPtr("?????? %s ???????????????????????? ????????????\r\n"%filename)
        self.dbgPtr("[ OK ] %s????????????\r\n"%filename)
        self.serialCloseFunc()
        return 0


    def dosWriteFirmwareSerdesFuncNew(self):
        return self.dosWriteFirmwareNew("SERDES.bin")

    def dosWriteFirmwareFiberFuncNew(self):
        return self.dosWriteFirmwareNew("I210IS4.bin")

    def dosWriteFirmwareHalfSerdesFuncNew(self):
        return self.dosWriteFirmwareNew("HALF.bin")




    def dosWriteMacAddrFuncNew(self,maclist):
        if None==maclist:
            self.dbgPtr("#?????? dosWriteMacAddrFunc ?????? None\r\n")
            return -1

        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -2

        self.dbgPtr("\r\nMAC????????????, ????????????, ???????????????\r\n")
        nicNum=0
        #macStr=maclist[0]
        startTime=time.monotonic()

        for macStr in maclist:
            nicNum=nicNum+1

            mac=macStr.replace(':','')
            cmd="eeupdate /nic=%d /MAC=%s"%(nicNum,mac)

            beginTime=time.monotonic()

            #stage 1 write cmd and wait for 8086-xxxx

            nowTime=time.monotonic()
            endTime=nowTime+10
            stageSuccess=0

            #cmd=cmd+'\r\n'
            cmdArray=cmd.encode()
            #self.dbgPtr("%f???????????? %s"%(nowTime-startTime,cmd))
            self.ser.write(cmdArray)

            self.waitAndYield(0.1)
            self.ser.write('\r\n'.encode())
            foundinfo=0
            infostr=''


            updateMacDone=0
            updateCrcDone=0


            while(nowTime<=endTime):
                self.waitAndYield(0.1)
                data = self.ser.readline()
                nowTime=time.monotonic()
                rxstr = data.decode('utf-8','ignore')

                if 1==cm2003SerialDebug:
                    rxlen=len(rxstr)
                    if rxlen>0:
                        self.dbgPtr(("%f ????????????(%d)???"%(nowTime-startTime,rxlen))+rxstr+  "\r\n")

                str=rxstr

                if 0==foundinfo :
                    for i in range (3):
                        ret=str.find('8086')
                        if ret >=16:
                            macStr=str[ret-16:]
                            ret=macStr.find('Connection')
                            if ret >=0:
                                str=macStr[ret:]
                                macStr=macStr[:ret]
                                infostr=infostr+(macStr+"\r\n")
                                if 2==i:
                                    foundinfo=1
                                    self.dbgPtr(("[%f]\r\n%s"%(nowTime-startTime,infostr)))


                ret= str.find("Updating MAC Address to")
                if ret>=4:
                    ret=ret-4
                    str2=str[ret:]
                    ret= str2.find("Done.")
                    if ret>=0:
                        ret=ret+5
                        str=str2[ret:]
                        info=str2[:ret]
                        self.dbgPtr(("[%f] %s"%(nowTime-startTime,info))+"\r\n")
                        updateMacDone=1

                if 1==updateMacDone:
                    ret= str.find("Updating Checksum")
                    if ret>=4:
                        ret=ret-4
                        str2=str[ret:]
                        ret= str2.find("Done.")
                        if ret>=0:
                            ret=ret+5
                            str=str2[ret:]
                            info=str2[:ret]
                            self.dbgPtr(("[%f] %s"%(nowTime-startTime,info))+"\r\n")
                            updateCrcDone=1
                            stageSuccess=1
                            break
                '''
                if 1==updateCrcDone:
                    ret= str.find("C:\>")
                    if ret>=0:
                        stageSuccess=1
                        break
                '''

            if 0==stageSuccess:
                self.dbgPtr("#?????? ????????????????????????%dMAC\r\n"%nicNum)
                self.serialCloseFunc()
                return -3
        # self.dbgPtr("DOS??????MAC????????????\r\n")
        self.dbgPtr("[ OK ] MAC????????????\r\n")
        return 0


    '''
    # just can not get 3 cmd in one line!
    def dosWriteMacAddrFuncNew2(self,maclist):
        if None==maclist:
            self.dbgPtr("#?????? dosWriteMacAddrFunc ?????? None\r\n")
            return -1

        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -2

        nicNum=0
        #macStr=maclist[0]
        startTime=time.monotonic()

        cmd=''
        for macStr in maclist:
            nicNum=nicNum+1
            mac=macStr.replace(':','')
            if 1==nicNum:
                cmd=cmd+"eeupdate /nic=%d /MAC=%s "%(nicNum,mac)
            else :
                cmd=cmd+"| eeupdate /nic=%d /MAC=%s "%(nicNum,mac)

        self.dbgPtr("??????????????? %s\r\n"%cmd)


        beginTime=time.monotonic()

        #stage 1 write cmd and wait for 8086-xxxx

        nowTime=time.monotonic()
        endTime=nowTime+10
        stageSuccess=0

        #cmd=cmd+'\r\n'
        cmdArray=cmd.encode()
        #self.dbgPtr("%f???????????? %s"%(nowTime-startTime,cmd))
        self.ser.write(cmdArray)

        self.waitAndYield(0.1)
        self.ser.write('\r\n'.encode())
        foundinfo=0
        infostr=''


        updateMacDone=0
        updateCrcDone=0


        while(nowTime<=endTime):
            self.waitAndYield(0.1)
            data = self.ser.readline()
            nowTime=time.monotonic()
            rxstr = data.decode('utf-8','ignore')

            if 1==cm2003SerialDebug:
                rxlen=len(rxstr)
                if rxlen>0:
                    self.dbgPtr(("%f ????????????(%d)???"%(nowTime-startTime,rxlen))+rxstr+  "\r\n")

            str=rxstr

            if 0==foundinfo :
                for i in range (3):
                    ret=str.find('8086')
                    if ret >=16:
                        macStr=str[ret-16:]
                        ret=macStr.find('Connection')
                        if ret >=0:
                            str=macStr[ret:]
                            macStr=macStr[:ret]
                            infostr=infostr+("??????%d????????????:"%(i+1)+macStr+"\r\n")
                            if 2==i:
                                foundinfo=1
                                self.dbgPtr(("%f\r\n%s"%(nowTime-startTime,infostr)))


            ret= str.find("Updating MAC Address to")
            if ret>=4:
                ret=ret-4
                str2=str[ret:]
                ret= str2.find("Done.")
                if ret>=0:
                    ret=ret+5
                    str=str2[ret:]
                    info=str2[:ret]
                    self.dbgPtr(("%f %s"%(nowTime-startTime,info))+"\r\n")
                    updateMacDone=1

            if 1==updateMacDone:
                ret= str.find("Updating Checksum")
                if ret>=4:
                    ret=ret-4
                    str2=str[ret:]
                    ret= str2.find("Done.")
                    if ret>=0:
                        ret=ret+5
                        str=str2[ret:]
                        info=str2[:ret]
                        self.dbgPtr(("%f %s"%(nowTime-startTime,info))+"\r\n")
                        updateCrcDone=1
                        stageSuccess=1
                        break


        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????????%dMAC\r\n"%nicNum)
            self.serialCloseFunc()
            return -3

        return 0
    '''

    def dosWriteMacAddrFunc(self,maclist):
        if None==maclist:
            self.dbgPtr("#?????? dosWriteMacAddrFunc ?????? None\r\n")
            return -1

        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -2
        '''
        ret=self.serialCheckIfInDosNow()
        if(ret!=1):
            self.dbgPtr("#?????? ????????????DOS?????????????????????????????????\r\n")
            self.serialCloseFunc()
            return -3
        '''

        self.dosExecCmdFunc("cls")

        nicNum=1
        for macStr in maclist:
            mac=macStr.replace(':','')
            cmd="eeupdate /nic=%d /MAC=%s"%(nicNum,mac)
            #self.dosExecCmdFunc("cls")
            ret=self.dosExecCmdFunc(cmd)
            if 1!=ret:
                self.dbgPtr("#?????? ????????????:"+cmd+" ?????? ?????? %d ????????????\r\n"%ret)
                self.serialCloseFunc()
                return -(nicNum+3)
            nicNum=nicNum+1

        #you cannot get mac now....need reboot or reset the nic
        #self.dosCheckMacFunc()

        self.dbgPtr("MAC ?????????????????? ????????????\r\n")
        return  0

    def dosWriteBiosFunc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.serialCheckIfInDosNow()
        if(ret!=1):
            self.dbgPtr("#?????? ????????????DOS?????????????????????????????????\r\n")
            self.serialCloseFunc()
            return -2

        self.dosExecCmdFunc("cls")

        #Dont use b.bat, as it will display???
        # C:\>b.bat
        # C:\>afudos J1702010.rom /P /B /N
        # which will affect dosExecCmdFunc
        #

        cmd="afudos J1702010.rom /P /B /N \r\n"
        '''
        ret=self.dosExecCmdFunc(cmd)
        if 1!=ret:
            self.dbgPtr("#?????? ????????????:"+cmd+" ?????? ?????? %d ????????????\r\n"%ret)
            self.serialCloseFunc()
            return -3
        '''
        if 1==cm2003SerialDebug:
            self.dbgPtr("??????DOS??????:"+cmd+"\r\n")
        self.dbgPtr("\r\nBIOS????????????, ????????????(???2??????), ???????????????\r\n")

        cmdArray=cmd.encode()
        self.ser.write(cmdArray)

        success=0
        rxStr=''
        while(1):
            '''
            data = self.ser.readline()
            rxstr=data.decode('utf-8','ignore')
            self.dbgPtr("????????????:"+rxstr+  "\r\n")
            if rxstr.find("Verifying NVRAM Block ....... done") >=0:
                success=1
            if rxstr.find("C:\>") >=0:
                if 1==success:
                    break
            self.waitAndYield(0.1)
            '''
            if None != self.yieldPtr:
                self.yieldPtr()

            datac = self.ser.read(1)



            datac2=datac.decode('utf-8','ignore')

            #self.dbgPtr("[rx]:"+datac2+  "\r\n")

            rxStr=rxStr+datac2
            if (datac2== '\r') or (datac2== '\n') or (datac2== ')') or (rxStr.find('done')>=0):
                rxStr=rxStr+'\n'
                if 1==cm2003SerialDebug:
                    self.dbgPtr("????????????:"+rxStr+  "\r\n")
                if rxStr.find("Verifying NVRAM Block ....... done") >=0:
                    success=1
                    break

                self.waitAndYield(0.01)

                rxStr=''


        ret=self.serialCheckIfInDosNow()


        if 1==success:
            self.dbgPtr("[ OK ] BIOS????????????\r\n")
            ret=0
        else :
            self.dbgPtr("#?????? ?????? BIOS?????? ????????????\r\n")
            ret=-1
        self.serialCloseFunc()
        return ret


    def dosWriteEcFunc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.serialCheckIfInDosNow()
        if(ret!=1):
            self.dbgPtr("#?????? ????????????DOS?????????????????????????????????\r\n")
            self.serialCloseFunc()
            return -2

        self.dbgPtr("\r\nEC????????????, ????????????, ???????????????\r\n")
        self.dosExecCmdFunc("cls")

        #Dont use b.bat, as it will display???
        # C:\>b.bat
        # C:\>afudos J1702010.rom /P /B /N
        # which will affect dosExecCmdFunc
        #

        cmd="ITEFLASH.EXE /FLASH JZ1702EC.4T1"

        ret=self.dosExecCmdFunc(cmd)
        if 1!=ret:
            self.dbgPtr("#?????? ????????????:"+cmd+" ?????? ?????? %d ????????????\r\n"%ret)
            self.serialCloseFunc()
            return -3

        ret=self.serialCheckIfInDosNow()


        if 1==ret:
            self.dbgPtr("[ OK ] EC????????????\r\n")
            ret=0
        else :
            self.dbgPtr("#?????? ?????? EC?????? ????????????\r\n")
            ret=-1
        self.serialCloseFunc()
        return ret

    def dosWriteEcFuncNew(self):

        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1


        cmd="ITEFLASH.EXE /FLASH JZ1702EC.4T1"
        startTime=time.monotonic()

        #stage 1 write cmd and wait updatesize=10000
        nowTime=time.monotonic()

        cmdArray=cmd.encode()
        if 1==cm2003SerialDebug:
            self.dbgPtr("[%f] ???????????? %s\r\n"%(nowTime-startTime,cmd))

        self.ser.write(cmdArray)

        self.waitAndYield(0.1)
        self.ser.write('\r\n'.encode())
        foundinfo=0
        infostr=''



        self.dbgPtr("\r\nEC????????????, ????????????, ???????????????\r\n")
        '''

        endTime=nowTime+30
        stageSuccess=0

        while(nowTime<=endTime):
            self.waitAndYield(0.1)
            data = self.ser.readline()
            nowTime=time.monotonic()
            rxstr = data.decode('utf-8','ignore')

            if 1==cm2003SerialDebug:
                rxlen=len(rxstr)
                if rxlen>0:
                    self.dbgPtr(("%f ????????????(%d)???"%(nowTime-startTime,rxlen))+rxstr+  "\r\n")

            ret=rxstr.find("updatesize=10000")
            if ret>=0:
                if 1==cm2003SerialDebug:
                    self.dbgPtr(("[%f] ????????? updatesize=10000"%(nowTime-startTime))+"\r\n")
                stageSuccess=1
                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? ???????????????EC????????????\r\n")
            self.serialCloseFunc()
            return -3

        #stage 2 wait filesize=10000
        nowTime=time.monotonic()
        endTime=nowTime+30
        stageSuccess=0

        while(nowTime<=endTime):
            self.waitAndYield(0.1)
            data = self.ser.readline()
            nowTime=time.monotonic()
            rxstr = data.decode('utf-8','ignore')

            if 1==cm2003SerialDebug:
                rxlen=len(rxstr)
                if rxlen>0:
                    self.dbgPtr(("%f ????????????(%d)???"%(nowTime-startTime,rxlen))+rxstr+  "\r\n")

            ret=rxstr.find("filesize=10000")
            if ret>=0:
                self.dbgPtr(("[%f] ????????? filesize=10000 ???????????????"%(nowTime-startTime))+"\r\n")
                stageSuccess=1
                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? ???????????????EC????????????\r\n")
            self.serialCloseFunc()
            return -3
        '''
        #stage 3  wait BIOS
        nowTime=time.monotonic()
        endTime=nowTime+30
        stageSuccess=0

        while(nowTime<=endTime):
            self.waitAndYield(0.1)
            data = self.ser.readline()
            nowTime=time.monotonic()
            rxstr = data.decode('utf-8','ignore')

            if 1==cm2003SerialDebug:
                rxlen=len(rxstr)
                if rxlen>0:
                    self.dbgPtr(("%f ????????????(%d)???"%(nowTime-startTime,rxlen))+rxstr+  "\r\n")

            ret= rxstr.find("BIOS")
            if ret>=0:
                if 1==cm2003SerialDebug:
                    self.dbgPtr(("[%f] ????????? BIOS??????"%(nowTime-startTime))+"\r\n")
                stageSuccess=1
                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? ??????????????? BIOS?????? \r\n")
            self.serialCloseFunc()
            return -3

        #stage 4  wait C:\>
        nowTime=time.monotonic()
        endTime=nowTime+30
        stageSuccess=0

        while(nowTime<=endTime):
            self.waitAndYield(0.1)
            data = self.ser.readline()
            nowTime=time.monotonic()
            rxstr = data.decode('utf-8','ignore')

            if 1==cm2003SerialDebug:
                rxlen=len(rxstr)
                if rxlen>0:
                    self.dbgPtr(("%f ????????????(%d)???"%(nowTime-startTime,rxlen))+rxstr+  "\r\n")

            ret= rxstr.find("C:\>")
            if ret>=0:
                if 1==cm2003SerialDebug:
                    self.dbgPtr(("[%f] ????????? C:\> ????????????????????????DOS EC????????????"%(nowTime-startTime))+"\r\n")
                self.dbgPtr("[ OK ] EC????????????\r\n")
                stageSuccess=1
                break


        if 0==stageSuccess:
            self.dbgPtr("#?????? ??????????????? DOS??????  \r\n")
            self.serialCloseFunc()
            return -3


        return 0


    def dosCheckMacFunc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -2

        ret=self.serialCheckIfInDosNow()
        if(ret!=1):
            self.dbgPtr("#?????? ????????????DOS?????????????????????????????????\r\n")
            self.serialCloseFunc()
            return -3

        self.dosExecCmdFunc("cls")

        #ret=self.ser.write('\n'.encode())

        cmd="eeupdate /all  /mac_dump \r\n"
        if 1==cm2003SerialDebug:
            self.dbgPtr("???????????? %s"%cmd)

        ret=self.ser.write(cmd.encode())

        #self.ser.write(KEY_ENTER)
        data = self.ser.readline()
        rxstr=data.decode('utf-8','ignore')
        #self.dbgPtr("????????????: "+rxstr+  "\r\n")

        while(1):
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            #self.dbgPtr("????????????2???"+rxstr+  "\r\n")
            str=rxstr

            ret=str.find('1:  LAN MAC Address is')
            if ret >=0:
                macStr=str[ret:]
                ret=macStr.find('.')
                if ret >=0:
                    macStr=macStr[:ret]
                    #self.dbgPtr("????????????MAC:"+macStr+"\r\n")
                    self.dbgPtr("?????? "+macStr+"\r\n")

            ret=str.find('2:  LAN MAC Address is')
            if ret >=0:
                macStr=str[ret:]
                ret=macStr.find('.')
                if ret >=0:
                    macStr=macStr[:ret]
                    #self.dbgPtr("????????????MAC:"+macStr+"\r\n")
                    self.dbgPtr("?????? "+macStr+"\r\n")
            ret=str.find('3:  LAN MAC Address is')
            if ret >=0:
                macStr=str[ret:]
                ret=macStr.find('.')
                if ret >=0:
                    macStr=macStr[:ret]
                    #self.dbgPtr("????????????MAC:"+macStr+"\r\n")
                    self.dbgPtr("?????? "+macStr+"\r\n")


            if rxstr.find('C:\>') >=0 :
                if rxstr.find('eeupdate') <0:
                    break
            self.waitAndYield(0.1)

        '''
        self.dosExecCmdFunc("eeupdate /all /mac_dump")
        '''
        #self.dbgPtr("MAC?????????????????????????????????\r\n")
        self.dbgPtr("[ OK ] ??????MAC????????????\r\n")
        return 0

    def dosCheckFirmwareFunc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -2

        ret=self.serialCheckIfInDosNow()
        if(ret!=1):
            self.dbgPtr("#?????? ????????????DOS?????????????????????????????????\r\n")
            self.serialCloseFunc()
            return -3

        self.dosExecCmdFunc("cls")

        #ret=self.ser.write('\n'.encode())

        cmd="eeupdate /all \r\n"
        ret=self.ser.write(cmd.encode())

        #self.ser.write(KEY_ENTER)
        data = self.ser.readline()
        rxstr=data.decode('utf-8','ignore')
        #self.dbgPtr("????????????: "+rxstr+  "\r\n")

        while(1):
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            #self.dbgPtr("???????????????"+rxstr+  "\r\n")
            str=rxstr

            for i in range (3):
                ret=str.find('8086')
                if ret >=16:
                    macStr=str[ret-16:]
                    ret=macStr.find('Connection')
                    if ret >=0:
                        str=macStr[ret:]
                        macStr=macStr[:ret]
                        self.dbgPtr("????????????[ %d ] "%(i+1)+macStr+"\r\n")
                        if macStr.find('Backplane')>=0:
                            self.dbgPtr("????????????[ %d ] SERDES or HALF\r\n"%(i+1))
                        elif macStr.find('Fiber')>=0:
                            self.dbgPtr("????????????[ %d ] FIBER\r\n"%(i+1))
                        else :
                            self.dbgPtr("????????????[ %d ] ??????\r\n"%(i+1))

            if rxstr.find('C:\>') >=0 :
                if rxstr.find('eeupdate') <0:
                    break
            self.waitAndYield(0.2)


        #self.dbgPtr("???????????????????????????????????????\r\n")
        self.dbgPtr("[ OK ] ????????????????????????\r\n")
        return 0


    def linuxSetRtcFunc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.serialCheckIfInUEFIUDISK()
        if(ret!=1):
            self.dbgPtr("#??????1 ????????????LINUX?????????????????????LINUX??????\r\n")
            return -1


        nowtime=datetime.datetime.now()
        str=nowtime.strftime('%Y/%m/%d %H:%M:%S')
        cmdstr=("hwclock --set --date=\"%s\"\r\n"%str)

        if 1==cm2003SerialDebug:
            self.dbgPtr("???????????????"+cmdstr+  "\r\n")

        self.dbgPtr("LINUX??????????????????\r\n")

        cmdArray=cmdstr.encode()
        ret=self.ser.write(cmdArray)
        while(1):
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            #self.dbgPtr("???????????????"+rxstr+  "\r\n")
            self.dbgPtr(rxstr)

            if rxstr.find('#') >=0 :
                break

        ret=self.serialCheckIfInUEFIUDISK()
        if(ret!=1):
            self.dbgPtr("#??????2 ????????????LINUX?????????????????????LINUX??????\r\n")
            return -2

        cmdstr=("hwclock --hctosys\r\n")
        if 1==cm2003SerialDebug:
            self.dbgPtr("???????????????"+cmdstr+  "\r\n")

        cmdArray=cmdstr.encode()
        ret=self.ser.write(cmdArray)
        while(1):
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('#') >=0 :
                break

        ret=self.serialCheckIfInUEFIUDISK()
        if(ret!=1):
            self.dbgPtr("#??????2 ????????????LINUX?????????????????????LINUX??????\r\n")
            return -2

        #self.dbgPtr("???????????????????????????????????????\r\n")
        self.dbgPtr("[ OK ] LINUX??????????????????\r\n")
        self.serialCloseFunc()
        return ret


    def linuxInstallLinuxFunc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.serialCheckIfInUEFIUDISK()
        if(ret!=1):
            self.dbgPtr("#??????1 ????????????LINUX?????????????????????LINUX??????\r\n")
            return -1


        cmdstr=("/root/mnt-usb/usb-jobs/buildroot-install.sh \r\n")

        if 1==cm2003SerialDebug:
            self.dbgPtr("???????????????"+cmdstr+  "\r\n")

        self.dbgPtr("LINUX????????????, ???????????????\r\n")
        cmdArray=cmdstr.encode()
        ret=self.ser.write(cmdArray)
        while(1):
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")
            self.waitAndYield(0.01)
            if rxstr.find('/root/mnt-usb/usb-jobs/buildroot-install.sh FINISH!') >=0 :
                if 1==cm2003SerialDebug:
                    self.dbgPtr("???????????????LINUX????????????\r\n")
                break

        ret=self.serialCheckIfInUEFIUDISK()
        if(ret!=1):
            self.dbgPtr("#??????3 ????????????LINUX?????????????????????LINUX??????\r\n")
            return -2

        # self.dbgPtr("??????LINUX???????????????????????????\r\n")
        self.dbgPtr("[ OK ] LINUX????????????\r\n")
        self.serialCloseFunc()
        return ret


    def linuxDelSataContextFunc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.serialCheckIfInUEFIUDISK()
        if(ret!=1):
            self.dbgPtr("#??????1 ????????????LINUX?????????????????????LINUX??????\r\n")
            return -1


        cmdstr=("umount /dev/sda1 -f \r\n")
        if 1==cm2003SerialDebug:
            self.dbgPtr("???????????????"+cmdstr+  "\r\n")
        cmdArray=cmdstr.encode()
        ret=self.ser.write(cmdArray)
        #skip echo string
        self.ser.readline()

        data = self.ser.readline()
        while(1):
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")
            self.waitAndYield(0.01)
            if rxstr.find('#') >=0 :
                break

        ret=self.serialCheckIfInUEFIUDISK()
        if(ret!=1):
            self.dbgPtr("#??????2 ????????????LINUX?????????\r\n")
            return -2
        data = self.ser.readline()

        cmdstr=("dd if=/dev/zero of=/dev/sda bs=100M count=1 \r\n")

        if 1==cm2003SerialDebug:
            self.dbgPtr("???????????????"+cmdstr+  "\r\n")
        cmdArray=cmdstr.encode()
        ret=self.ser.write(cmdArray)

        #skip echo string
        self.ser.readline()


        while(1):
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")
            self.waitAndYield(0.01)
            if rxstr.find('#') >=0 :
                break

        ret=self.serialCheckIfInUEFIUDISK()
        if(ret!=1):
            self.dbgPtr("#??????3 ????????????LINUX?????????\r\n")
            return -2
        ret=0

        self.dbgPtr("??????SATA?????????????????????????????????\r\n")
        self.serialCloseFunc()
        return ret


    def linuxInstallMiniosFunc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.serialCheckIfInUEFIUDISK()
        if(ret!=1):
            self.dbgPtr("#??????1 ????????????LINUX?????????????????????LINUX??????\r\n")
            return -1

        cmd = "/root/mnt-usb/usb-jobs/minios-install.sh\n"
        self.ser.write(cmd.encode())
        self.ser.readline()
        time.sleep(1)
        self.dbgPtr("MINIOS????????????, ????????????, ???????????????\r\n")
        dd_keyword = [
            "DD-TIME",
            "records out",
            "real",
        ]

        self.comClear()
        while(1):
            self.waitAndYield(0.2)

            read_str = self.ser.readline().decode('utf-8','ignore')
            if (len(read_str) < 2):
                continue
            if any(word in read_str for word in bash_keyword):
                continue
            if (read_str.find("FINISH") >= 0):
                break
            if any(word in read_str for word in dd_keyword):
                self.dbgPtr(read_str)

        ret=self.serialCheckIfInUEFIUDISK()
        if(ret!=1):
            self.dbgPtr("#??????3 ????????????LINUX?????????????????????LINUX??????\r\n")
            return -2

        # self.dbgPtr("??????MINIOS???????????????????????????\r\n")
        self.dbgPtr("[ OK ] MINIOS????????????\r\n")
        self.serialCloseFunc()
        return ret


    def obsModeEnterFunc(self,type):
        self.obsExit=0
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1
        obsType=type
        if 1== obsType:
            self.dbgPtr("MINIOS????????????????????????\r\n")
        else :
            self.dbgPtr("????????????????????????\r\n")

        while(0==self.obsExit):
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 0==obsType:
                if len(rxstr)>0:
                    self.dbgPtr("???????????????"+rxstr)

            elif 1==obsType:
                ret=rxstr.find('eth1: rx pkt')
                if ret >=0:
                    printSrt=rxstr[ret:]
                    ret=printSrt.find('Mbps/s')
                    if ret >=0:
                        rxstr=printSrt[ret:]
                        printSrt=printSrt[:ret+1]
                        self.dbgPtr("???????????????"+printSrt+ '\r\n')

                ret=rxstr.find('eth2: rx pkt')
                if ret >=0:
                    printSrt=rxstr[ret:]
                    ret=printSrt.find('Mbps/s')
                    if ret >=0:
                        rxstr=printSrt[ret:]
                        printSrt=printSrt[:ret+1]
                        self.dbgPtr("???????????????"+printSrt+ '\r\n')

            #check linux time and network !
            elif 2==obsType:
                if len(rxstr)>0:
                    self.dbgPtr("???????????????"+rxstr)

                if (rxstr.find('TEST-TIME') >=0) :

                    #@   DATE=2019/01/14-16:34:56            TEST-TIME=130 s
                    #parse the time!
                    ret=rxstr.find('DATE=')
                    if ret>0:
                        timeStr=rxstr[ret+5:]
                        #self.dbgPtr("timeStr %s\r\n"%(timeStr))
                        ret=timeStr.find('-')
                        if ret >=0:
                            t1Str=timeStr[:ret]
                            #self.dbgPtr("t1Str %s\r\n"%(t1Str))
                            timeStr=timeStr[ret+1:]

                            ret=timeStr.find(' ')
                            if ret>0:
                                #self.dbgPtr("timeStr %s\r\n"%(timeStr))
                                timeStr=timeStr[:ret]
                                timeStr=timeStr.rstrip()
                                t1Str=t1Str+' '+timeStr
                                self.dbgPtr("???????????? %s\r\n"%(t1Str))
                                boardtime=datetime.datetime.strptime(t1Str,"%Y/%m/%d %H:%M:%S")
                                nowtime=datetime.datetime.now()
                                str=nowtime.strftime('%Y/%m/%d %H:%M:%S')
                                self.dbgPtr("???????????? %s\r\n"%(str))

                                if boardtime>=nowtime:
                                    diff=boardtime-nowtime
                                    boardLater=1
                                else:
                                    diff=nowtime-boardtime
                                    boardLater=0


                                if 1==boardLater:
                                    op=' >= '
                                else:
                                    op=' <  '

                                if diff.days>0:
                                    self.dbgPtr("[ !! ] ????????????-?????????!!!! ????????????%s???????????? %d ??? %d ???  ?????? %d ???\r\n"%(op,diff.days,diff.seconds,TIME_DIFF_THRESHOLD))
                                else:
                                    if diff.seconds>TIME_DIFF_THRESHOLD:
                                        self.dbgPtr("[ !! ] ????????????-?????????!!!! ????????????%s???????????? 0 ??? %d ???  ?????? %d ???\r\n"%(op,diff.seconds,TIME_DIFF_THRESHOLD))
                                    else:
                                        # self.dbgPtr(" ???????????? ????????????%s???????????? 0 ??? %d ???  ????????? %d ???\r\n"%(op,diff.seconds,TIME_DIFF_THRESHOLD))
                                        self.dbgPtr("[ OK ] ????????????-??????\r\n")

                #parse the time ends

            self.waitAndYield(0.05)

        #self.serialCloseFunc()
        pass


    def obsModeExitFunc(self):
        self.obsExit=1
        self.serialCloseFunc()
        return

    def obsModeCmdSend(self,cmdstr):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        cmdArray=cmdstr.encode()
        self.ser.write(cmdArray)

        return 0

    def obsKeyByteArraySendFunc(self,keyByteArray):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        self.ser.write(keyByteArray)

        return 0

    def miniosAutoLoginAndNetTest(self):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        self.ser.write('\r\n'.encode())
        while(1):
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("rx %d:"%(len(rxstr))+rxstr+"\r\n")
            if len(rxstr)<=3:
                continue
            if rxstr.find("miniOS login: ") <0:
                self.dbgPtr("#?????? ???????????? minios ??????????????????????????????\r\n")
                return -2
            else:
                break
        cmdstr="root\n"
        cmdArray=cmdstr.encode()
        self.ser.write(cmdArray)

        START_BOLD_MINIOS=bytearray(b'\x1B\x5B\x30\x3B\x31\x3B\x37\x6D\x0F')
        END_BOLD_MINIOS=bytearray(b'\x1B\x5B')

        START_BOLD_MINIOS_STR=START_BOLD_MINIOS.decode('utf-8','ignore')
        END_BOLD_MINIOS_STR=END_BOLD_MINIOS.decode('utf-8','ignore')

        while(1):
            self.waitAndYield(0.2)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            ret=rxstr.find(START_BOLD_MINIOS_STR)
            if ret >=0:
                tmpStr=rxstr[ret+9:]
                ret=tmpStr.find(END_BOLD_MINIOS_STR)
                if ret >=0:
                    strPart1=tmpStr[0:ret]
                    if 1==cm2003SerialDebug:
                        self.dbgPtr("????????????????????? %s\r\n"%strPart1)
                    if strPart1.find("Perform Aging Test") >=0:
                        break
            self.ser.write(KEY_DOWN_MINIOS)

        self.ser.write(KEY_ENTER_MINIOS)
        data = self.ser.readline()
        rxstr = data.decode('utf-8','ignore')
        if rxstr.find("Start Test") <0:
            self.dbgPtr("#?????? ???????????? Start Test ???????????? ???????????????\r\n")
            return -3

        while(1):
            self.ser.write(KEY_RIGHT_MINIOS)
            self.waitAndYield(0.2)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            ret=rxstr.find(START_BOLD_MINIOS_STR)
            if ret >=0:
                tmpStr=rxstr[ret+9:]
                ret=tmpStr.find(END_BOLD_MINIOS_STR)
                if ret >=0:
                    strPart1=tmpStr[0:ret]
                    if 1==cm2003SerialDebug:
                        self.dbgPtr("????????????????????? %s\r\n"%strPart1)
                    if strPart1.find("Start Test") >=0:
                        break

        self.ser.write(KEY_ENTER_MINIOS)
        self.dbgPtr("????????????????????????????????????????????????????????????\r\n")



        return 0

    def linuxViewNetTestResultFunc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1
        detectAutotest=0

        testpass=1

        for i in range(120):
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if len(rxstr)>0:
                self.dbgPtr("???????????????"+rxstr)
            self.waitAndYield(0.1)
            if rxstr.find('TEST-TIME') >=0 :
                self.dbgPtr("???????????????????????????????????????\r\n")
                detectAutotest=1
                break
        if 0==detectAutotest:
            self.dbgPtr("#?????? ????????????????????????????????????\r\n")
            return -2

        cmdstr=("/root/mnt-flash/flash-jobs/killall.sh \r\n")
        if 1==cm2003SerialDebug:
            self.dbgPtr("???????????????"+cmdstr+  "\r\n")

        cmdArray=cmdstr.encode()
        ret=self.ser.write(cmdArray)

        finalResult=''
        stage=0
        errStage=0
        errStr=''
        errLine=0
        lowSpeedStr=''
        lowSpeedLine=0
        speedPrint=0

        while(1):
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            self.dbgPtr("[????????????]???"+rxstr)
            self.waitAndYield(0.01)

            if rxstr.find('/root/mnt-flash/flash-jobs/killall.sh FINISH') >=0 :
                self.dbgPtr("??????????????????????????????\r\n")
                errStage=3

                if 6== speedPrint:
                    finalResult=finalResult+"  ?????????????????? 6???   ??????\r\n"
                else:
                    finalResult=finalResult+"# ?????????????????? %d???   ?????????\r\n"%speedPrint
                    testpass=0

                if 0==lowSpeedLine:
                    finalResult=finalResult+"  ??????????????????        ??????\r\n"
                else:
                    finalResult=finalResult+"# ??? %d ??????????????????  ?????????\r\n"%lowSpeedLine
                    finalResult=finalResult+lowSpeedStr
                    testpass=0

                if 1==testpass:
                    finalResult=finalResult+"  ???????????? ????????????\r\n"
                else:
                    finalResult=finalResult+"# ???????????? ?????????????????????#######???\r\n"

                self.dbgPtr("?????????????????????\r\n"+finalResult)

                break

            targetStr='CONNECT='
            ret=rxstr.find(targetStr)
            if ret>=0:
                str=rxstr[ret+len(targetStr):]
                str=str.lstrip()
                ret=str.find(' ')
                if ret>=0:
                    str=str[:ret]
                    connect=int(str)
                    if 12==connect:
                        finalResult=finalResult+"  Connect %d ??????\r\n"%connect
                    else:
                        finalResult=finalResult+"# Connect %d ?????????\r\n"%connect
                        testpass=0

            for j in range(2):
                if 0==j:
                    currentTarget="client"
                else:
                    currentTarget="server"

                for i in range(3):
                    num=i+1
                    targetStr='iperf3-%s-%d-tx.txt'%(currentTarget,num)
                    ret=rxstr.find(targetStr)
                    if ret>=0:
                        str=rxstr[ret+len(targetStr):]
                        targetStr='Bytes'
                        ret=str.find(targetStr)
                        if ret>=0:
                            str=str[ret+len(targetStr):]
                            str=str.lstrip()
                            ret=str.find(' ')
                            if ret>=0:
                                str=str[:ret]
                                speed=int(str)
                                if speed>600:
                                    finalResult=finalResult+"  [%s sender %d] %d Mbps >600 ??????\r\n"%(currentTarget,num,speed)
                                else:
                                    finalResult=finalResult+"# [%s sender %d] %d Mbps <600 ?????????\r\n"%(currentTarget,num,speed)
                                    testpass=0
                                speedPrint=speedPrint+1

                for i in range(3):
                    num=i+1
                    targetStr='iperf3-%s-%d-rx.txt'%(currentTarget,num)
                    ret=rxstr.find(targetStr)
                    if ret>=0:
                        str=rxstr[ret+len(targetStr):]
                        targetStr='Bytes'
                        ret=str.find(targetStr)
                        if ret>=0:
                            str=str[ret+len(targetStr):]
                            str=str.lstrip()
                            ret=str.find(' ')
                            if ret>=0:
                                str=str[:ret]
                                speed=int(str)
                                if speed>600:
                                    finalResult=finalResult+"  [%s receiver %d] %d Mbps >600 ??????\r\n"%(currentTarget,num,speed)
                                else:
                                    finalResult=finalResult+"# [%s receiver %d] %d Mbps <600 ?????????\r\n"%(currentTarget,num,speed)
                                    testpass=0
                                speedPrint=speedPrint+1






            if 2==errStage:
                if len(rxstr)>3:
                    lowSpeedStr=lowSpeedStr+rxstr+'\r\n'
                    lowSpeedLine=lowSpeedLine+1

            if rxstr.find('grep \"[0-5][0-9][0-9]')>=0:
                errStage=2
                if 0==errLine:
                    finalResult=finalResult+"  ???????????????        ??????\r\n"
                else:
                    finalResult=finalResult+"# ??? %d ???????????????  ?????????\r\n"%errLine
                    finalResult=finalResult+errStr
                if 1==cm2003SerialDebug:
                    self.dbgPtr("detect grep <599!\r\n")

            if 1==errStage:
                if len(rxstr)>3:
                    errStr=errStr+rxstr+'\r\n'
                    errLine=errLine+1

            if rxstr.find('grep \"error\"')>=0:
                errStage=1
                if 1==cm2003SerialDebug:
                    self.dbgPtr("detect grep error!\r\n")


        self.dbgPtr("???????????????????????????????????????????????????\r\n")
        self.dbgPtr("[ OK ] ??????????????????\r\n")

        if 1==testpass:
            return 0
        else:
            return -1

        return -1

    def waitAndYield(self,sec):
        nowTime=time.monotonic()
        nextStart=nowTime+sec
        while(nowTime<=nextStart):
            if(None!=self.yieldPtr):
                self.yieldPtr()
            nowTime=time.monotonic()
            if(None!=self.yieldPtr):
                self.yieldPtr()

        return


    def serialEnterBiosFromColdBoot(self):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        startTime=time.monotonic()
        nowTime=startTime
        waitTime=30
        endTime=nowTime+waitTime
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)

            ret=self.ser.write(KEY_DEL)
            if 1==cm2003SerialDebug:
                self.dbgPtr("?????? DEL ????????????BIOS \r\n")
            data = self.ser.readline()
            rxstr=data.decode('utf-8','ignore')

            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            if rxstr.find('F4: Save & Exit') >=0 :
                if 1==cm2003SerialDebug:
                    self.dbgPtr("\r\n?????????????????????BIOS \r\n")
                stageSuccess=1
                break

        if 0==stageSuccess:
            self.dbgPtr("#?????? %d ???????????????BIOS????????? ???1????????????\r\n"%waitTime)
            return -5

        return 0


    # Check for BIOS setup interface
    # to_setupBIOS, timeout to find setupBIOS keyword
    # Return True when found BIOS setup interface, False when not
    def serial_checkin_bios_setup (self, to_setupBIOS = 10):
        if (self.serialOpened != 1):
            self.dbgPtr("#?????? ???????????????\r\n")
            return False

        flag_setupBIOS = False          # True when setupBIOS_keyword found
        t_start = time.monotonic()
        while(time.monotonic() <= (t_start + to_setupBIOS)):
            data = self.ser.readline()
            if (len(data) < 1):
                self.ser.write(KEY_LEFT)
                self.waitAndYield(0.1)
                continue

            # print('\n\ncheckinBIOS data \"' + data.decode('utf-8', 'ignore') + '\"')
            if not any(word in data for word in setupBIOS_keyword):
                self.ser.write(KEY_LEFT)
                self.waitAndYield(0.1)
                continue

            flag_setupBIOS = True
            print('setupBIOS keyword found')
            break

        if not flag_setupBIOS:
            print('setupBIOS keyword not found!')
            return flag_setupBIOS

        return flag_setupBIOS


    # Try to find preBIOS keyword then send delete to enter BIOS
    # to_preBIOS, timeout to find preBIOS keyword
    # to_del, timeout to send delete
    # Return True when BIOS entered, False when not
    def serial_delete_enter_bios (self, to_preBIOS = 30, to_del = 1):
        if (self.serialOpened != 1):
            self.dbgPtr("#?????? ???????????????\r\n")
            return False

        flag_preBIOS = False            # True when preBIOS_keyword found
        t_start = time.monotonic()
        while(time.monotonic() <= (t_start + to_preBIOS)):
            data = self.ser.readline()
            if (len(data) < 1):
                continue

            # print('\n\npreBIOS data \"' + data.decode('utf-8', 'ignore') + '\"')
            if not any(word in data for word in preBIOS_keyword):
                continue

            flag_preBIOS = True
            print('preBIOS keyword found')
            break

        if not flag_preBIOS:
            print('preBIOS keyword not found!')
            return flag_preBIOS

        t_start = time.monotonic()
        while(time.monotonic() <= (t_start + to_del)):
            self.ser.write(KEY_DEL)
            self.waitAndYield(0.1)

        return self.serial_checkin_bios_setup()


    # Try to find preBIOS keyword or DOS keyword
    # to_preBIOS, timeout to find preBIOS keyword
    # to_del, timeout to send delete
    # Return (True, False) when BIOS entered
    # Return (False, True) when DOS keyword found
    def serial_delete_enter_bios_or_dos (self, to_preBIOS = 30, to_del = 1):
        if (self.serialOpened != 1):
            self.dbgPtr("#?????? ???????????????\r\n")
            return False

        flag_preBIOS = False            # True when preBIOS_keyword found
        flag_DOS = False
        t_start = time.monotonic()
        while(time.monotonic() <= (t_start + to_preBIOS)):
            data = self.ser.readline()
            if (len(data) < 1):
                continue

            # print('\n\npreBIOS or DOS data \"' + data.decode('utf-8', 'ignore') + '\"')
            if any(word in data for word in preBIOS_keyword):
                flag_preBIOS = True
                print('preBIOS keyword found')
                break
            elif any(word in data for word in DOS_keyword):
                flag_DOS = True
                print('DOS keyword found')
                break

        if not flag_preBIOS:
            print('preBIOS keyword not found!')
        if not flag_DOS:
            print('DOS keyword not found!')

        if flag_preBIOS:
            t_start = time.monotonic()
            while(time.monotonic() <= (t_start + to_del)):
                self.ser.write(KEY_DEL)
                self.waitAndYield(0.1)
            return self.serial_checkin_bios_setup(), flag_DOS

        return flag_preBIOS, flag_DOS


    # Try to assemble boot list from BIOS boot page
    # to_bootBIOS, timeout to find bootBIOS keyword
    # Return True when valid boot list found, False when not
    def serial_find_bios_boot_list (self, to_bootBIOS = 10):
        if (self.serialOpened != 1):
            self.dbgPtr("#?????? ???????????????\r\n")
            return False

        flag_bootBIOS = False           # True when bootBIOS_keyword found
        t_start = time.monotonic()
        while(time.monotonic() <= (t_start + to_bootBIOS)):
            data = self.ser.readline()
            if (len(data) < 1):
                self.ser.write(KEY_LEFT)
                self.waitAndYield(0.1)
                continue

            # print('\n\nbootBIOS data \"' + data.decode('utf-8', 'ignore') + '\"')
            if not any(word in data for word in bootBIOS_keyword):
                self.ser.write(KEY_LEFT)
                self.waitAndYield(0.1)
                continue

            flag_bootBIOS = True
            print('bootBIOS keyword found')
            break

        if not flag_bootBIOS:
            print('bootBIOS keyword not found!')
            return flag_bootBIOS

        self.serialScanForBootList(data.decode('utf-8', 'ignore'))
        if (len(self.bootlist) < 1):
            flag_bootBIOS = False
            print('bootBIOS empty list!')
            self.dbgPtr('#?????? BIOS???????????????')
            return flag_bootBIOS

        return flag_bootBIOS


    # Try to enter DOS
    # to_DOS, timeout to find DOS keyword
    # Return True when DOS entered, False when not
    def serial_enter_dos (self, to_DOS = 30):
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        flag_BIOS, flag_DOS = self.serial_delete_enter_bios_or_dos()

        if flag_DOS:
            print('\nTRY DOS')
            flag_DOS = False            # True when DOS_keyword found
            t_start = time.monotonic()
            while(time.monotonic() <= (t_start + to_DOS)):
                data = self.ser.readline()
                if (len(data) < 1):
                    self.ser.write(KEY_ENTER)
                    self.waitAndYield(0.1)
                    continue

                # print('DOS data \"' + data.decode('utf-8', 'ignore') + '\"')
                if not any(word in data for word in DOS_keyword):
                    self.ser.write(KEY_ENTER)
                    self.waitAndYield(0.1)
                    continue

                flag_DOS = True
                print('DOS found')
                break

            if not flag_DOS:
                print('DOS not found!')
                return flag_DOS

            return flag_DOS
        elif flag_BIOS:
            print('\n!!!!BIOS REBOOT!!!!')
            self.dbgPtr("#?????? ??????BIOS??????, ????????????????????????DOS\r\n")

            if not self.serial_find_bios_boot_list():
                print('ERR! find BIOS boot list failed!')
                return False

            bootStr=''
            for opt in self.bootlist:
                if any(word in opt for word in ['UEFI', 'SATA']):
                    continue
                bootStr = opt
                break
            if (len(bootStr) < 1):
                self.dbgPtr("#?????? ?????????U???DOS????????????"+"\r\n")
                return False

            newStr=bootStr[bootStr.find('['):(bootStr.find(']') + 1)]
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????" + newStr + "\r\n")

            if(self.serialSetFirstBoot(newStr) < 0):
                self.serialCloseFunc()
                return False

            print('\nTRY DOS')
            flag_DOS = False            # True when DOS_keyword found
            t_start = time.monotonic()
            while(time.monotonic() <= (t_start + to_DOS)):
                data = self.ser.readline()
                if (len(data) < 1):
                    self.ser.write(KEY_ENTER)
                    self.waitAndYield(0.1)
                    continue

                # print('DOS data \"' + data.decode('utf-8', 'ignore') + '\"')
                if not any(word in data for word in DOS_keyword):
                    self.ser.write(KEY_ENTER)
                    self.waitAndYield(0.1)
                    continue

                flag_DOS = True
                print('DOS found')
                break

            if not flag_DOS:
                print('DOS not found!')
                return flag_DOS

            return flag_DOS
        else:
            self.dbgPtr("#?????? ?????????BIOS???DOS"+"\r\n")
            return False


    def coldbootBootUC(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        if not self.serial_delete_enter_bios():
            print('ERR! delete enter BIOS failed! #1')
            return -1

        if not self.serial_find_bios_boot_list():
            print('ERR! find BIOS boot list failed!')
            return -1

        bootStr=''
        for opt in self.bootlist:
            if any(word in opt for word in ['UEFI', 'SATA']):
                continue
            bootStr = opt
            break
        if (len(bootStr) < 1):
            self.dbgPtr("#?????? ?????????U???DOS????????????"+"\r\n")
            return -10

        newStr=bootStr[bootStr.find('['):(bootStr.find(']') + 1)]
        if 1==cm2003SerialDebug:
            self.dbgPtr("???????????????" + newStr + "\r\n")

        ret=self.serialSetFirstBoot(newStr)
        if(ret<0):
            self.serialCloseFunc()
            return ret

        if self.serial_enter_dos():
            self.dbgPtr("[ OK ] DOS????????????\r\n")
            ret = 0
        else:
            ret = -1

        return ret


    def coldbootEnterBiosPrintBiosEc(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1
        if 1==cm2003SerialDebug:
            self.dbgPtr("????????????BIOS\r\n")

        ret=self.serialEnterBiosFromColdBoot()
        if ret<0 :
            self.serialCloseFunc()
            return ret

        # scan for our info
        strReturn=''
        while 1:
            if 1==cm2003SerialDebug:
                self.dbgPtr("?????????????????????????????? ?????????\r\n")
            ret=self.ser.write(KEY_RIGHT)
            data = self.ser.readline()
            rxstr=data.decode('utf-8','ignore')

            if len(rxstr)>0 :
                pass
                #self.dbgPtr("???????????????"+rxstr+  "\r\n")

            self.waitAndYield(0.01)

            ret=rxstr.find('BIOS Version')
            if  ret>=0 :
                newstr=rxstr[ret:]
                ret=newstr.find('|')
                strReturn=strReturn+ newstr[:ret]+"\r\n"

                #find  Build Date and Time
                newstr=newstr[ret+1:]
                ret=newstr.find('Build Date and Time')
                if  ret>=0 :
                    newstr=newstr[ret:]
                    ret=newstr.find('|')
                    strReturn=strReturn+ newstr[:ret]+"\r\n"

                #find  EC Version
                newstr=newstr[ret+1:]
                ret=newstr.find('EC Version')
                if  ret>=0 :
                    newstr=newstr[ret:]
                    ret=newstr.find('|')
                    strReturn=strReturn+ newstr[:ret]+"\r\n"
                break
        #need to delete every  [0m   [1m

        while(1):
            ret2=strReturn.find(setBoldStr)
            if ret2>=0:
                newStr2=strReturn[0:ret2]+strReturn[ret2+4:]
                strReturn=newStr2
            else:
                break

        while(1):
            ret2=strReturn.find(setUnboldStr)
            if ret2>=0:
                newStr2=strReturn[0:ret2]+strReturn[ret2+4:]
                strReturn=newStr2
            else:
                break


        #self.dbgPtr("???????????????\r\n")
        if 0==len(strReturn):
            self.serialCloseFunc()
            return -10

        self.dbgPtr("@ BIOS/EC???????????????\r\n")
        self.dbgPtr(strReturn)
        self.serialCloseFunc()
        return 0


    def coldbootBootUU(self,waitType):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1


        ret=self.serialEnterBiosFromColdBoot()
        if ret<0 :
            return ret

        self.serialFindBootPageFunc()

        bootStr=''

        for i in self.bootlist:
            ret=i.find('UEFI')
            if ret <0:
                continue

            ret=i.find('Built-in')
            if ret >=0:
                continue

            ret=i.find('SM651')
            if ret >=0:
                continue

            bootStr=i
            break

        if 0==len(bootStr):
            self.dbgPtr("#?????? ?????????U???UEFI????????????"+"\r\n")
            self.serialCloseFunc()
            return -2

        #self.dbgPtr("??????????????? "+bootStr +"\r\n")
        ret=bootStr.find('[')
        str2=bootStr[ret:]

        ret=str2.find(']')
        ret=ret+1
        newStr=str2[:ret]
        if 1==cm2003SerialDebug:
            self.dbgPtr("??????????????? "+newStr+"\r\n")

        #self.serialFindBootPageFunc()
        ret=self.serialSetFirstBoot(newStr)
        if(ret<0):
            self.serialCloseFunc()
            return ret
        '''
        self.serialScan(KEY_ENTER,"login:")
        '''
        ret=self.serialWaitBootUU(waitType)
        self.serialCloseFunc()

        return ret

    def coldbootEnterBiosPrintTime(self,skipEnterBios):
        self.serialOpenFunc()

        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1


        if 0==skipEnterBios:
            if 1==cm2003SerialDebug:
                self.dbgPtr("????????????BIOS\r\n")
            ret=self.serialEnterBiosFromColdBoot()
            if ret<0:
                self.serialCloseFunc()
                return -2

        mon=0
        year=0
        day=0
        hh=0
        mm=0
        ss=0
        timevalid=0

        # scan for our info
        strReturn=''
        while 1:
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????????????? ?????????\r\n")
            ret=self.ser.write(KEY_RIGHT)
            data = self.ser.readline()
            rxstr=data.decode('utf-8','ignore')

            if len(rxstr)>0 :
                pass
                #self.dbgPtr("???????????????"+rxstr+  "\r\n")

            self.waitAndYield(0.01)

            ret=rxstr.find('System Date')
            if  ret>=0 :
                newstr=rxstr[ret:]
                ret=newstr.find(']')
                strReturn=strReturn+ newstr[:ret+1]+"\r\n"

                #parse for month/day/year
                #System Date   [Mon 01/14/2019]
                #System Time   [16:01:09]

                mdy=newstr[:ret+1]
                ret2=mdy.find('[')
                if  ret2>=0 :
                    mdy=mdy[ret2+1:]

                    ret2=mdy.find(' ')
                    if  ret2>=0 :
                        mdy=mdy[ret2+1:]
                        mdy=mdy.rstrip()
                        mdy=mdy.rstrip(']')
                        #print(mdy)

                        ret2=re.split(r'/', mdy)
                        mon=int(ret2[0])
                        day=int(ret2[1])
                        year=int(ret2[2])
                        timevalid=1

                    #print(mdy,mon,day,year)


                #parse for month/day/year ends

                #find  System Time
                newstr=newstr[ret+1:]
                ret=newstr.find('System Time')
                if  ret>=0 :
                    newstr=newstr[ret:]
                    ret=newstr.find(']')
                    strReturn=strReturn+ newstr[:ret+1]+"\r\n"


                    #parse for hh:mm:sec
                    if 1==timevalid:
                        mdy=newstr[:ret+1]
                        ret2=mdy.find('[')
                        if  ret2>=0 :
                            mdy=mdy[ret2+1:]

                            mdy=mdy.rstrip()
                            mdy=mdy.rstrip(']')

                            ret=re.split(r':', mdy)
                            hh=int(ret[0])
                            mm=int(ret[1])
                            ss=int(ret[2])
                            timevalid=2
                break

        nowtime=datetime.datetime.now()

        #self.dbgPtr("???????????????\r\n")
        if 0==len(strReturn):
            self.serialCloseFunc()
            return -10

        self.dbgPtr("@ BIOS?????????\r\n")
        self.dbgPtr(strReturn)
        self.serialCloseFunc()

        str=nowtime.strftime('%Y/%m/%d %H:%M:%S')
        self.dbgPtr("????????????   "+str+"\r\n")

        ret=0

        boardLater=0
        if 2==timevalid:
            boardtime=datetime.datetime(year,mon,day,hh,mm,ss)
            if boardtime>=nowtime:
                diff=boardtime-nowtime
                boardLater=1
            else:
                diff=nowtime-boardtime
                boardLater=0


            if 1==boardLater:
                op=' >= '
            else:
                op=' <  '

            if diff.days>0:
                # self.dbgPtr("#????????? ????????????%s???????????? %d ??? %d ???  ?????? %d ???\r\n"%(op,diff.days,diff.seconds,TIME_DIFF_THRESHOLD))
                self.dbgPtr("[ !! ] ????????????-?????????!!!! ????????????%s???????????? %d ??? %d ???  ?????? %d ???\r\n"%(op,diff.days,diff.seconds,TIME_DIFF_THRESHOLD))
                ret=-11
            else:
                if diff.seconds>TIME_DIFF_THRESHOLD:
                    # self.dbgPtr("#????????? ????????????%s???????????? 0 ??? %d ???  ?????? %d ???\r\n"%(op,diff.seconds,TIME_DIFF_THRESHOLD))
                    self.dbgPtr("[ !! ] ????????????-?????????!!!! ????????????%s???????????? 0 ??? %d ???  ?????? %d ???\r\n"%(op,diff.seconds,TIME_DIFF_THRESHOLD))
                    ret=-110
                else:
                    # self.dbgPtr("   ?????? ????????????%s???????????? 0 ??? %d ???  ????????? %d ???\r\n"%(op,diff.seconds,TIME_DIFF_THRESHOLD))
                    self.dbgPtr("[ OK ] ????????????-??????\r\n")
                    ret=0
        return ret


    def serialBootLUFuncCheckModeA(self):
        ret=self.serialBootLUFunc(0xa)
        return ret

    def serialBootLUFuncCheckModeB(self):
        ret=self.serialBootLUFunc(0xb)
        return ret

    def serialLinuxScanNetTestFor40s(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        startTime=time.monotonic()
        nowTime=startTime
        endTime=nowTime+60
        stageSuccess=0

        while(nowTime<=endTime):
            nowTime=time.monotonic()
            self.waitAndYield(0.01)
            data = self.ser.readline()
            rxstr = data.decode('utf-8','ignore')
            if 1==cm2003SerialDebug:
                self.dbgPtr("???????????????"+rxstr+  "\r\n")

            ret=rxstr.find('TEST-TIME=')
            if (ret>=0) :
                self.dbgPtr(rxstr)
                str=rxstr[ret+len('TEST-TIME='):]
                ret=str.find(' ')
                if (ret>=0) :
                    str=str[:ret]
                    secNum=int(str)
                    if (secNum >=40):
                        stageSuccess=1
                        self.dbgPtr("[ OK ] LINUX?????????????????????40???\r\n")
                        break

        if 0==stageSuccess:
            self.dbgPtr("#?????? ????????????????????? TEST-TIME ?????????????????????????????????????????????????????????LINUX\r\n")
            self.serialCloseFunc()
            return -8

        return 0

    def coldbootBootLC(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        ret=self.serialEnterBiosFromColdBoot()
        if ret<0 :
            return ret

        self.serialFindBootPageFunc()

        bootStr=''

        for i in self.bootlist:
            ret=i.find('UEFI')
            if ret >=0:
                continue

            ret=i.find('SM651')
            if ret >=0:
                bootStr=i
                break

        if 0==len(bootStr):
            self.dbgPtr("#?????? ?????????????????????????????????"+"\r\n")
            return -10

        #self.dbgPtr("??????????????? "+bootStr +"\r\n")
        ret=bootStr.find('[')
        str2=bootStr[ret:]

        ret=str2.find(']')
        ret=ret+1
        newStr=str2[:ret]
        if 1==cm2003SerialDebug:
            self.dbgPtr("??????????????? "+newStr+"\r\n")

        #self.serialFindBootPageFunc()

        #self.serialSetFirstBoot(newStr)
        ret=self.serialSetFirstBoot(newStr)
        if(ret<0):
            self.serialCloseFunc()
            return ret

        '''
        ret=self.serialScan(KEY_ENTER,"miniOS login: ",40.0)

        if(0==ret):
            self.dbgPtr("?????????????????? ??????????????????(minios) ????????????\r\n")
        else :
            self.dbgPtr("#?????? ?????????????????? ??????????????????(minios) ????????????\r\n")
        '''

        ret=self.serialWaitBootLC()
        self.serialCloseFunc()
        return ret


    def  longTimeButton1Func(self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -1

        iperf3_result_ok = 1

        cmd = "/root/killall.sh\n"
        self.ser.write(cmd.encode())
        self.ser.readline()
        time.sleep(1)

        iperf3_average_replace = [
            ["/root/iperf3-log/iperf3-", ""],
            ["server", "A"],
            ["client", "B"],
            [".txt:", ""],
            ["rx", "RECV"],
            ["tx", "SEND"],
            ["Bytes", "B"],
            ["Mbits/sec", "Mb/s"],
        ]

        iperf3_average_keyword = [
            "0.00-",
            "Mbits/sec",
            "sender",
            "receiver",
        ]

        iperf3_stat_replace = [
            ["IPERF3_", ""],
            ["LE", "??????"],
        ]

        iperf3_stat_keyword = [
            "IPERF3_ERROR",
            "IPERF3_ALL",
        ]

        iperf3_average_str = "@ ????????????????????????:\r\n"
        iperf3_average_count = 0
        iperf3_stat_str = ""
        iperf3_stat_count = 0
        iperf3_stat_list = []
        read_count = 0
        while (1):
            self.waitAndYield(0.2)
            read_count += 1
            if (read_count > 200):
                break

            read_str = self.ser.readline().decode('utf-8','ignore')
            if (len(read_str) < 2):
                continue
            if any(word in read_str for word in bash_keyword):
                continue
            if (read_str.find("#") >= 0):
                break

            print(read_str)
            if any(word in read_str for word in iperf3_average_keyword):
                iperf3_average_str += read_str
                iperf3_average_count += 1
            elif any(word in read_str for word in iperf3_stat_keyword):
                iperf3_stat_str += read_str
                iperf3_stat_count += 1

        if (iperf3_average_count > 0):
            iperf3_average_str = re.sub(" +", " ", iperf3_average_str)
            iperf3_average_str = re.sub(r"\[.*\]", ":", iperf3_average_str)
            for part in iperf3_average_replace:
                iperf3_average_str = iperf3_average_str.replace(part[0], part[1])

            if (iperf3_average_count != 6):
                iperf3_result_ok = 0

            self.dbgPtr("%s" % iperf3_average_str)
        else :
            iperf3_result_ok = 0

        if (iperf3_stat_count > 0):
            for part in iperf3_stat_replace:
                iperf3_stat_str = iperf3_stat_str.replace(part[0], part[1])

            iperf3_stat_list = list(map(int, re.findall('\d+', iperf3_stat_str)))
            if ((iperf3_stat_list[0] > 0) or (iperf3_stat_list[3] > 0) or (iperf3_stat_list[5] > 0) or (iperf3_stat_list[7] > 0)):
                iperf3_result_ok = 0

            self.dbgPtr("%s" % iperf3_stat_str)

        if (iperf3_result_ok != 0):
            ret = "[ OK ] ????????????-??????"
            self.dbgPtr("%s\r\n" % ret)
        else :
            ret = "[ !! ] ????????????-?????????!!!!"
            self.dbgPtr("%s\r\n" % ret)
            self.longTimeButton2_job()


        self.serialCloseFunc()
        return ret

    def longTimeButton2_job (self):
        self.serialOpenFunc()
        if 1!=self.serialOpened:
            self.dbgPtr("#?????? ???????????????\r\n")
            return -2

        iperf3_record_list = []
        iperf3_result_ok = 1

    # MAC ADDRESS
        cmd = "grep \":\" /sys/class/net/enp*/address\n"
        self.ser.write(cmd.encode())
        self.ser.readline()

        mac_address_replace = [
            ["/sys/class/net/enp", "??????-"],
            ["s0/address:", "-MAC??????="],
            [":", ""],
            ["\r\n", ""],
        ]

        mac_address_str = "@ ??????MAC??????:\r\n"
        mac_address_count = 0
        mac_address_list = []
        read_count = 0
        while (1):
            self.waitAndYield(0.1)
            read_count += 1
            if (read_count > 20):
                break

            read_str = self.ser.readline().decode('utf-8','ignore')
            if (len(read_str) < 1):
                continue
            if any(word in read_str for word in bash_keyword):
                continue
            if (read_str.find("#") >= 0):
                break

            print(read_str)
            for part in mac_address_replace:
                read_str = read_str.replace(part[0], part[1])

            read_str = read_str.upper()
            mac_address_list.append(read_str.split("=", 1)[-1])
            mac_address_str += read_str + "\r\n"
            mac_address_count += 1

        iperf3_record_list.append(mac_address_str)
        print(mac_address_str)
        if (mac_address_count > 0):
            self.dbgPtr("%s" % mac_address_str)

        cmd = "IPERF3_LOG_PATH=/root/iperf3-log/*.txt\n"
        self.ser.write(cmd.encode())
        self.ser.readline()

    # IPERF3 AVERAGE
        cmd = "grep \"sender\|receiver\" $IPERF3_LOG_PATH | grep -v \" 0.00 Mbits/sec\"\n"
        self.ser.write(cmd.encode())
        self.ser.readline()
        time.sleep(1)

        iperf3_average_replace = [
            ["/root/iperf3-log/iperf3-", ""],
            ["server", "A"],
            ["client", "B"],
            [".txt:", ""],
            ["rx", "RECV"],
            ["tx", "SEND"],
            ["Bytes", "B"],
            ["Mbits/sec", "Mb/s"],
        ]

        iperf3_average_str = "@ ????????????????????????:\r\n"
        iperf3_average_count = 0
        read_count = 0
        while (1):
            self.waitAndYield(0.1)
            read_count += 1
            if (read_count > 20):
                break

            read_str = self.ser.readline().decode('utf-8','ignore')
            if (len(read_str) < 1):
                continue
            if any(word in read_str for word in bash_keyword):
                continue
            if (read_str.find("#") >= 0):
                break

            print(read_str)
            read_str = re.sub(" +", " ", read_str)
            read_str = re.sub(r"\[.*\]", ":", read_str)
            for part in iperf3_average_replace:
                read_str = read_str.replace(part[0], part[1])

            iperf3_average_str += read_str
            iperf3_average_count += 1

        if ((iperf3_average_count > 0) and (iperf3_average_count != 6)):
            iperf3_result_ok = 0
            iperf3_average_str += "[ !! ] ????????????-?????????!!!!\r\n"

        iperf3_record_list.append(iperf3_average_str)
        print(iperf3_average_str)
        if (iperf3_average_count > 0):
            self.dbgPtr("%s" % iperf3_average_str)


        else :
    # IPERF3 LAST
            cmd = "tail -n1 $IPERF3_LOG_PATH\n"
            self.ser.write(cmd.encode())
            self.ser.readline()
            time.sleep(1)

            iperf3_last_replace = [
                ["/root/iperf3-log/iperf3-", ""],
                ["server", "A"],
                ["client", "B"],
                [".txt", " "],
                ["Bytes", "B"],
                ["Mbits/sec", "Mb/s"],
                ["==> ", ""],
                ["  <==", ""],
                ["\r\n", ""],
            ]

            iperf3_last_str = "@ ??????????????????10?????????:\r\n"
            iperf3_last_count = 0
            read_count = 0
            while (1):
                read_count += 1
                if (read_count > 20):
                    break

                read_str = self.ser.readline().decode('utf-8','ignore')
                if (len(read_str) < 1):
                    continue
                if any(word in read_str for word in bash_keyword):
                    continue
                if (read_str.find("#") >= 0):
                    break

                print(read_str)
                read_str = re.sub(" +", " ", read_str)
                read_str = re.sub(r"\[.*\]", ":", read_str)
                for part in iperf3_last_replace:
                    read_str = read_str.replace(part[0], part[1])

                if (read_str.find("Mb/s") >= 0):
                    read_str += "\r\n"
                    iperf3_last_count += 1

                iperf3_last_str += read_str

            if ((iperf3_last_count > 0) and (iperf3_last_count != 6)):
                iperf3_result_ok = 0
                iperf3_last_str += "[ !! ] ????????????-?????????!!!!\r\n"

            iperf3_record_list.append(iperf3_last_str)
            print(iperf3_last_str)
            if (iperf3_last_count > 0):
                self.dbgPtr("%s" % iperf3_last_str)

        # IPERF3 TEST TIME
        if (iperf3_average_count > 0):
            iperf3_test_time_list = re.findall(r"\d+\.\d+-\d+\.\d+", iperf3_average_str)
        elif (iperf3_last_count > 0):
            iperf3_test_time_list = re.findall(r"\d+\.\d+-\d+\.\d+", iperf3_last_str)
        else :
            iperf3_result_ok = 0
            iperf3_record_list.append("!ERR ????????????????????????????????????????????????10?????????\r\n")
            self.dbgPtr("!ERR ????????????????????????????????????????????????10?????????\r\n")

        if iperf3_test_time_list:
            iperf3_test_time_str = "@ ??????????????????: "
            iperf3_test_time_str += iperf3_test_time_list[-1].split("-", 1)[-1] + " ???\r\n"
            iperf3_record_list.append(iperf3_test_time_str)
            print(iperf3_test_time_str)
            self.dbgPtr("%s" % iperf3_test_time_str)

        # IPERF3 STAT
        REGEX_ALL=" [[:digit:]]{1,3} Mbits/sec| [[:digit:]]{1,3}\.[[:digit:]]* Mbits/sec"
        REGEX_GE300=" [3-9][[:digit:]]{2} Mbits/sec| [3-9][[:digit:]]{2}\.[[:digit:]]* Mbits/sec"
        REGEX_LE300=" [1-2][[:digit:]]{2} Mbits/sec| [[:digit:]]{1,2} Mbits/sec| [1-2][[:digit:]]{2}\.[[:digit:]]* Mbits/sec| [[:digit:]]{1,2}\.[[:digit:]]* Mbits/sec"
        REGEX_LE200=" [1][[:digit:]]{2} Mbits/sec| [[:digit:]]{1,2} Mbits/sec| [1][[:digit:]]{2}\.[[:digit:]]* Mbits/sec| [[:digit:]]{1,2}\.[[:digit:]]* Mbits/sec"
        REGEX_LE100=" [[:digit:]]{1,2} Mbits/sec| [[:digit:]]{1,2}\.[[:digit:]]* Mbits/sec"
        GREP_CMD="grep -E"
        GREP_EXCLUDE="grep -vE \"sender|receiver\""

        iperf3_stat_cmd = [
            "IPERF3_ALL=$("+GREP_CMD+" \""+REGEX_ALL+"\" $IPERF3_LOG_PATH | "+GREP_EXCLUDE+" | wc -l)\n",
            "IPERF3_GE300=$("+GREP_CMD+" \""+REGEX_GE300+"\" $IPERF3_LOG_PATH | "+GREP_EXCLUDE+" | wc -l)\n",
            "IPERF3_LE300=$("+GREP_CMD+" \""+REGEX_LE300+"\" $IPERF3_LOG_PATH | "+GREP_EXCLUDE+" | wc -l)\n",
            "IPERF3_LE200=$("+GREP_CMD+" \""+REGEX_LE200+"\" $IPERF3_LOG_PATH | "+GREP_EXCLUDE+" | wc -l)\n",
            "IPERF3_LE100=$("+GREP_CMD+" \""+REGEX_LE100+"\" $IPERF3_LOG_PATH | "+GREP_EXCLUDE+" | wc -l)\n",
        ]

        for cmd in iperf3_stat_cmd:
            print(cmd)
            self.ser.write(cmd.encode())
            self.ser.readline()
            time.sleep(1)

        cmd = "echo \"ALL=$IPERF3_ALL GE300=$IPERF3_GE300 LE300=$IPERF3_LE300 LE200=$IPERF3_LE200 LE100=$IPERF3_LE100\"\n"
        self.ser.write(cmd.encode())
        self.ser.readline()

        iperf3_stat_string = "@ ????????????????????????:\r\n"
        iperf3_stat_count = 0
        read_count = 0
        while (1):
            self.waitAndYield(0.2)
            read_count += 1
            if (read_count > 200):
                break

            read_str = self.ser.readline().decode('utf-8','ignore')
            if (len(read_str) < 1):
                    continue
            if any(word in read_str for word in bash_keyword):
                continue
            if (read_str.find("#") >= 0):
                break

            iperf3_stat_string += re.sub(" +", " ", read_str)
            iperf3_stat_count += 1

        print(iperf3_stat_string)
        if (iperf3_stat_count > 0):
            iperf3_stat_list = list(map(int, re.findall('\d+', iperf3_stat_string)))
            iperf3_percent_list = [ "{:.04%}".format(num / iperf3_stat_list[0]) for num in iperf3_stat_list[2::2] ]
            print(iperf3_stat_list)
            print(iperf3_percent_list)

            iperf3_percent_str = "@ ????????????????????????: "
            iperf3_percent_str += "????????????: %d ???\r\n" % iperf3_stat_list[0]
            for idx, percent in enumerate(iperf3_percent_list) :
                idx_hold = idx
                idx = (idx * 2) + 1
                if (idx > 1):
                    iperf3_percent_str += "???????????? "
                else :
                    iperf3_percent_str += "???????????? "

                iperf3_percent_str += "%03d: %s, %d ???" % (iperf3_stat_list[idx], percent, iperf3_stat_list[idx + 1])
                if (idx_hold >= (len(iperf3_percent_list) - 3)):
                    if (iperf3_stat_list[idx + 1] != 0):
                        iperf3_result_ok = 0
                        iperf3_percent_str += ", ????????????-?????????!!!!"

                iperf3_percent_str += "\r\n"

            iperf3_record_list.append(iperf3_percent_str)
            print(iperf3_percent_str)
            self.dbgPtr("%s" % iperf3_percent_str)

        # IPERF3 ABNORMAL
        iperf3_abnormal_cmd = [
            "IPERF3_ERROR=$(grep \"error\" $IPERF3_LOG_PATH | wc -l)\n",
        ]

        for cmd in iperf3_abnormal_cmd:
            print(cmd)
            self.ser.write(cmd.encode())
            self.ser.readline()
            time.sleep(1)

        cmd = "echo \"ERROR=$IPERF3_ERROR\"\n"
        self.ser.write(cmd.encode())
        self.ser.readline()

        iperf3_abnormal_string = "@ ????????????????????????:\r\n"
        iperf3_abnormal_count = 0
        read_count = 0
        while (1):
            self.waitAndYield(0.1)
            read_count += 1
            if (read_count > 100):
                break

            read_str = self.ser.readline().decode('utf-8','ignore')
            if (len(read_str) < 1):
                    continue
            if any(word in read_str for word in bash_keyword):
                continue
            if (read_str.find("#") >= 0):
                break

            print(read_str)
            iperf3_abnormal_string += re.sub(" +", " ", read_str)
            if (int(read_str.split("=", 1)[-1]) > 0):
                iperf3_abnormal_count += 1

        iperf3_record_list.append(iperf3_abnormal_string)
        print(iperf3_abnormal_string)
        if (iperf3_abnormal_count > 0):
            iperf3_result_ok = 0
            self.dbgPtr("%s" % iperf3_abnormal_string)

        iperf3_result_str = "@ ??????????????????: "
        iperf3_record_title = "CM2003-MAC"
        if (mac_address_count > 0):
            iperf3_record_title += "-" + mac_address_list[0]

        iperf3_record_title += "-DATE-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        if (iperf3_result_ok != 0):
            ret = "[ OK ] ????????????-??????"
            iperf3_record_title += "-????????????-??????"
        else :
            ret = "[ !! ] ????????????-?????????!!!!"
            iperf3_record_title += "-????????????-?????????!!!!"

        iperf3_result_str += ret + "\r\n"
        iperf3_record_list.append(iperf3_result_str)
        self.dbgPtr("%s" % iperf3_result_str)

        iperf3_record_title += ".txt"
        iperf3_record_list.insert(0, iperf3_record_title + "\r\n")
        print(iperf3_record_title)

        iperf3_record_file = open(iperf3_record_title, "w")

        for line in iperf3_record_list:
            iperf3_record_file.write(line)

        iperf3_record_file.close()
        self.dbgPtr("@ ??????????????????:\r\n%s\r\n" % iperf3_record_title)

        self.serialCloseFunc()
        return ret

if __name__=='__main__':
    '''
    nowtime=datetime.datetime.now()
    str=nowtime.strftime('%Y/%m/%d %H:%M:%S')
    print(str)

    pathStr=os.path.split(os.path.realpath(__file__))[0]
    full_log_path_name=os.path.join(pathStr,"iperf-testlog-3000b.txt")

    file=open(full_log_path_name,'a')

    for i in range(3000):
        file.write("[  6]  %06d  sec  1.09 GBytes   123 Mbits/sec \n"%(i+100000))
    file.close()
    '''
    pass
