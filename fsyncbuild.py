import sys
from cx_Freeze import setup, Executable

import os
#print (os.getcwd())
cwd = os.path.dirname(os.path.realpath(__file__))+"\\"

exenoshow = Executable(
    script="fsync.py",
    base="Win32GUI",
    targetName="fsync.exe"
    )
exeshow = Executable(
    script="fsync.py",
    targetName="fsync-console.exe"
    )

setup(
    name = "fsync",
    version = "1.0",
    description = "File Sync Tool",
    executables = [exenoshow,exeshow])
