#!/usr/bin/python3
#######################################################
# Python rsync Backup script
# Sebastian Kraft, 24.06.2013
# rework Klyucharov Dmitry
#######################################################
import os
import re
import subprocess
import sys
import time


class LogFile:
    def __init__(self, src: str, logDir: str):
        self.file = None
        self.write_logfile = (logDir != '' and logDir is not None and os.path.exists(logDir))
        if self.write_logfile:
            logFileName = os.path.join(logDir, os.path.basename(os.path.normpath(src)),
                                       time.strftime("%Y-%m-%dT%H:%M:%S") + '.log')
            self.file = open(logFileName, 'wb')
            self.print2log("\n-----------------------------------------------------------")
            self.print2log(f"\nLogging sync source {src}")
            self.print2log("-----------------------------------------------------------")
            self.print2log("\n")

    def print2log(self, s:str):
        sys.stdout.buffer.write(bytes(s, "utf-8"))
        sys.stdout.flush()
        # '\r' has no effect for file write
        if self.write_logfile and (s.find('\r') == -1):
            self.write_logfile.write(bytes(s, "utf-8"))

    def close(self):
        if self.file: self.file.close()


class Rsync_cmd:
    def __init__(self, srcs: list, dst: str, opt: str, logDir=None):
        if isinstance(srcs,str):
            srcs = tuple([srcs])
        self.srcs = srcs
        self.dst = dst
        self.opt = opt
        if logDir is None:
            logDir = ''
        if self.check_dirs(logDir) == 1:
            self.logDir = logDir
        else:
            self.logDir = ''
        self.logFile = LogFile(src=None, logDir=None)

    def run(self, srcs=None, dst=None, opt=None, log=False):
        if srcs is None:
            srcs = self.srcs
        if dst is None:
            dst = self.dst
        if opt is None:
            opt = self.opt
        if Rsync_cmd.check_dirs(srcs) != 1:
            print(
                f"\nERROR: Source directory\n>> {srcs} << \nis not exist or available!!If it's located on an external or "
                f'network drive check if it is correctly mounted in the expected place.\n\n')
            sys.exit(1)
        if Rsync_cmd.check_dirs(dst) != 1:
            print(
                f"\nERROR: Distination directory\n>> {dst} <<\nis not available! If it's located on an external or "
                f"network drive check if it is correctly mounted in the expected place.\n\n")
            sys.exit(1)
        opt += ' ' + self.__check_prev()
        for src in srcs:
            self.logFile = LogFile(src, self.logDir)
            # prepare destination name
            if src[-1]!=os.sep:
                dst = os.path.join(dst, os.path.basename(os.path.normpath(src)))
            dst = os.path.normpath(dst)
            if Rsync_cmd.check_dirs(dst) == 0:
                os.mkdir(dst)
            self.__exec_rsync(src)
        # @todo закрыть лог-файл
        self.logFile.close()
        sys.exit(0)

    def __check_prev(self) -> str:
        # check for previous backups
        if os.path.exists(self.dst):
            dirListing = os.listdir(self.dst)
            dirListing = [name for name in os.listdir(self.dst) if
                          os.path.isdir(os.path.join(self.dst, name))]
            # match directory names of type 2013-06-24T18:44:31
            rex = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8}$')
            dirListing = [x for x in dirListing if rex.match(x)]
            numOldBackups = len(dirListing)
            if numOldBackups > 0:
                # dirListing.sort(key=lambda s: os.path.getmtime(os.path.join(dst, s)))
                dirListing.sort()
                dirListing.reverse()
                previous_backup_link = os.path.join(dst, dirListing[0])
                self.logFile.print2log(
                    "Previous backup will be used as hard link reference: " + previous_backup_link + "\n")
                return '--link-dest="' + previous_backup_link + '" '
        return ''

    @staticmethod
    def check_dirs(dirs:(list,tuple,str)) -> int:
        """
        Проверка на существование директорий
        :param dirs: список директорий или одна директория
        :return: 0 - директории(й) не существует
        1- все директории существуют
        2- некоторые директории существуют
        """
        ret = 0
        if isinstance(dirs,str):
            dirs=tuple([dirs])
        for dir in dirs:
            if not os.path.exists(dir):
                if ret == 0:
                    ret = 0
                else:
                    ret = 2
            elif ret == 0:
                ret = 1
            else:
                ret = ret
        return ret

    @staticmethod
    def ask_ok(prompt, retries=4, complaint='Please type yes or no...'):
        while True:
            ok = input(prompt)
            if ok in ('y', 'Y', 'yes', 'Yes'):
                return True
            if ok in ('n', 'N', 'no', 'No'):
                return False
            print(complaint)

    def __exec_rsync(self, src):
        rsynccmd = f'rsync {self.opt} {src} {self.dst}'
        self.logFile.print2log(f"{rsynccmd}\n\n")
        rsyncproc = subprocess.Popen(rsynccmd,
                                     shell=True,
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     )
        # read rsync output and print to console
        while True:
            next_line = rsyncproc.stdout.readline().decode("utf-8")
            if not next_line:
                break
            self.logFile.print2log(f"{next_line}")

        # wait until process is really terminated
        exitcode = rsyncproc.wait()
        # check exit code
        if exitcode == 0:
            self.logFile.print2log("done \n\n")
        else:
            self.logFile.print2log("\nWARNING: looks like some error occured :( \n\n")


# ------------------------------------------------------
# Main program
if __name__ == '__main__':
    # FAIL!!!
    # srcs = (r'/home/dmitry/Projects/admin_scripts/test/src/src0','/home/dmitry/Projects/admin_scripts/test/src/src1','/home/dmitry/Projects/admin_scripts/test/src/src4')
    srcs = tuple([r'test/test_folder/src/'])
    dst = r'/home/dmitry/Projects/admin_scripts/test/dst'
    opt = '-aP'
    logDir = None
    # --------------------------------------
    for i in range(len(srcs)):
        print(os.path.abspath(srcs[i]))

    # rsyncCmd = Rsync_cmd(srcs=srcs, dst=dst, opt=opt)
    # rsyncCmd.run()
