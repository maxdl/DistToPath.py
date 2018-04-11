#!/usr/bin/env python3

import wx
from disttopath import frame


class App(wx.App):

    def OnInit(self):
        self.main = frame.Frame(None)
        self.main.Show(True)
        self.SetTopWindow(self.main)
        return True


def main():
    app = wx.App()
    app.MainLoop()

if __name__ == '__main__':
    main()