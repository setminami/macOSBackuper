# -*- coding: utf-8 -*-
# this made for python3
from datetime import datetime
import os
import subprocess as sp


class Backups:
    """https://www.evernote.com/l/AB1_bTLV7XBO274WUjNM4bLGf0n2ykxIZqo"""
    DEBUG = True
    cmd = "/usr/local/bin/rsync"
    afpUrl = "afp://setminami@WDCloud._afpovertcp._tcp.local/"
    option = "avz --delete"

    def do(self, folders, dest):
        if not os.path.exists(dest):
            mkdirCmd = "mkdir %s" % (dest)
            pathName = os.path.basename(dest)
            mntCmd = "mount_afp -k " +\
                     "%s/%s /Volumes/%s" % (self.afpUrl, pathName, pathName)
        for x in folders:
            bkupcmd = "%s -%s %s %s" % (self.cmd, self.option, x, dest)
            print("Start %s @ %s" % (bkupcmd,
                  datetime.now().strftime("%Y-%m-%dT%H:%M:%S")), end='')
            if not os.path.exists(x):
                mkdirCmd = "mkdir %s" % (x)
                pathName = os.path.basename(x)
                mntCmd = "mount_afp -k " +\
                         "afp://setminami@WDCloud._afpovertcp._tcp" +\
                         ".local/%s /Volumes/%s" % (pathName, pathName)
                sp.check_call(mkdirCmd, shell=True)
                sp.check_call(mntCmd, shell=True)
                pass
            if sp.check_call(bkupcmd, shell=True) != 0:
                print("Couldn't backup @ %s" % x)
            else:
                print(" ... done")
            pass
        print("EndTime is %s" % datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))

    @staticmethod
    def DebugPrint(str):
        if Backups.DEBUG:
            print(str)
        else:
            pass


if __name__ == "__main__":
    ins = Backups()
    ins.do(["/Volumes/ExBackups/Timemachine/SetMBA.sparsebundle"], "/Volumes/WD\ Scorpion\ Blue/SetMBA_Backup/")
