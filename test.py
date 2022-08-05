'''
#!/usr/bin/evn python
# -*- coding:utf-8 -*-

import wx
import shutil
import os
from io import StringIO
import io
import six
import numpy


def GetMondrianData():
    fp = open("C:\\FileDriveLetter\\tlzyz\\zgzl-iar8.4\\jslogo.png", 'rb')
    fcontent = fp.read()

    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\x00\x00 \x08\x06\x00\
\x00\x00szz\xf4\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\x00\x00qID\
ATX\x85\xed\xd6;\n\x800\x10E\xd1{\xc5\x8d\xb9r\x97\x16\x0b\xad$\x8a\x82:\x16\
o\xda\x84pB2\x1f\x81Fa\x8c\x9c\x08\x04Z{\xcf\xa72\xbcv\xfa\xc5\x08 \x80r\x80\
\xfc\xa2\x0e\x1c\xe4\xba\xfaX\x1d\xd0\xde]S\x07\x02\xd8>\xe1wa-`\x9fQ\xe9\
\x86\x01\x04\x10\x00\\(Dk\x1b-\x04\xdc\x1d\x07\x14\x98;\x0bS\x7f\x7f\xf9\x13\
\x04\x10@\xf9X\xbe\x00\xc9 \x14K\xc1<={\x00\x00\x00\x00IEND\xaeB`\x82'

def GetMondrianBitmap():
    return wx.Bitmap(GetMondrianImage())

def GetMondrianImage():
    stream = numpy.genfromtxt(io.StringIO(GetMondrianData()))
    # stream = StringIO(GetMondrianData())
    # stream = numpy.genfromtxt(io.BytesIO(GetMondrianData().encode()))
    # stream = six.StringIO(GetMondrianData())
    return wx.Image(stream)

def GetMondrianIcon():
    icon = wx.Icon()
    icon.CopyFromBitmap(GetMondrianBitmap())
    return icon


class Create_Frame(wx.Frame):
    def __init__(self, parent, ID, title):
        wx.Frame.__init__(self, parent, ID, title, size=(380, 250),
                          style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
        panel = wx.Panel(self, -1)


        fp = open("C:\\FileDriveLetter\\tlzyz\\zgzl-iar8.4\\jslogo.png", 'rb')
        fcontent = fp.read()
        print(fcontent)
        print(str(fcontent))


        if
        ic = wx.Icon("C:\\FileDriveLetter\\tlzyz\\zgzl-iar8.4\\jslogo.png")

        # self.SetIcon(GetMondrianIcon())

        self.SetIcon(ic)

        self.list0 = ["中国", "美国", "俄罗斯", "日本", "韩国", "英国", "澳大利亚"]
        rb = wx.RadioBox(
            panel, -1, "北京奥运", wx.DefaultPosition, wx.DefaultSize,
            self.list0, 1, wx.RA_SPECIFY_COLS | wx.NO_BORDER)
        rb.SetToolTip(wx.ToolTip("北京加油!"))
        rb.Bind(wx.EVT_RADIOBOX, self.Print, rb)

    def Print(self, event):
        ID = event.GetInt()
        print(self.list0[ID])


if __name__ == '__main__':
    app = wx.App()
    frame = Create_Frame(None, -1, "北京奥运")
    frame.Show(True)
    app.MainLoop()
'''
# !/usr/bin/python
# -*- coding: UTF-8 -*-
import images.py

class AppnameFrame(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, 'Appname', size=(600, 400))

        self.SetIcon(images.AppIcon.GetIcon())

if __name__ == '__main__':
    app = wx.App()
    frame = Create_Frame(None, -1, "北京奥运")
    frame.Show(True)
    app.MainLoop()
