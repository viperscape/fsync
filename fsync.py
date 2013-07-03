#python 3+

import os, platform
from os import walk
from os.path import getmtime
import shutil
import time

#cwd = os.path.dirname(os.path.realpath(__file__))+"\\" #this no go in EXE format

user = os.getlogin() #get logged in user

platform = platform.system() #get platform (windows, darwin(mac), linux)
mac = "Darwin"
win = "Windows"
lin = "Linux"

if lin in platform:
    platform = mac #to my knowledge this should be fine


#setup defaults
home = "/Users/"+user
if platform in mac: #i don't know why i can't compare directly, unicode issue?
    platform = mac #set this properly
    remote = "/Volumes/"+user+"/Backup" #preceding . makes it hide on hfs+ drive!
elif platform is win:
    remote = "U:/Backup"
else:
    print("unrecognizable OS")

hide = True
twowaysync = False
sched = True
schedtime = 900 #in seconds

lstuff = {}
rstuff = {}

excfilter = {"Music","Videos","Movies","Pictures","Downloads","AppData",
             "Hyper-V","My Data Sources","Microsoft User Data","Identity",
             "Library","Public"}
incfilter = {"Documents","Desktop"}
includeall = False

def checkConfig():
    global remote,home,excfilter,incfilter,includeall,twowaysnc,hide,sched,schedtime
    #change defaults if needed
    try:
        config = open("config.fsync","r")

        if config:
            print("config file found")

        for line in config:
            if '#' in line:
                continue

            sline = line.split()


            if any(x in sline for x in ['macshare','winshare']):
                remote = sline[1]
                remote = remote.replace('$user',user)
                print("found user command in remote path")
            if any(x in sline for x in ['macpath','winpath']):
                print (sline[1])
                home = sline[1]
                home = home.replace('$user',user)
                print("found user command in home path")
            """
            if platform is win:
                if 'winshare' in sline:
                    remote = sline[1]
                if 'winpath' in sline:
                    print (sline[1])
                    home = sline[1]
                    home = home.replace('$user',user)
                    print("found user command in path")
            """
            if 'hide' in sline:
                if 'false' in sline[1]:
                    hide = False
            if 'twoway' in line:
                if 'true' in sline[1]:
                    twowaysync = True
            if 'sched' in line:
                if 'false' in sline[1]:
                    sched = False
                else:
                    schedtime = int(sline[1])
            if 'filter' in line:
                sline = line.split(',')
                if ' ' in sline[0]:
                    sline = line.split(', ')
                del sline[0]
                sline[len(sline)-1] = sline[len(sline)-1].rstrip('\n')
                
            if 'incfilter' in line:
                incfilter = sline
                if '*' in sline:
                    includeall = True
                    print("including all")
            if 'excfilter' in line:
                excfilter = sline
    except:
        print('no config file, no biggie')


#check for root backup folder
def checkBackupRoot():
    global remote
    try:
        #always use . before final folder name, this ensures cross-compatibility
        #from multiusers on multiplatforms
        if (remote):
            if '.' not in remote[remote.rfind('/')+1:len(remote)]:
                remote = remote.replace(remote[remote.rfind('/')+1:len(remote)],'.'+remote[remote.rfind('/')+1:len(remote)])
            #else: print("remote is all set!")
        else: print("error, no remote destination set")

        print("using remote destination",remote) 
        if not os.path.isdir(remote): #double check
            print ("missing backup destination, creating")

            try:
                os.makedirs(remote)
                if hide:
                    if platform is win:
                        #subprocess.Popen(['nohup', 'attrib +h ', 'remote'])
                        os.system('C:\Windows\System32\attrib +h '+remote+' nohup') #hide folder if it's a ntfs drive!
            except:
                print("trouble making backup destination, come back later")
    except:
        print("error with root backup folder, nothing done")
        raise SystemExit



def getStuff(root):
    stuff = {}

    try:
        print("getting listing from",root)
        for subs, dirs, files in walk(root):
            for incfi in incfilter:
                if incfi in subs:
                    skip = False #reset skip
                    if not includeall:
                        for excfi in excfilter: #make sure we do not have nested media, skip it
                            if excfi in subs:
                                skip = True


                    if not skip:
                        folder = subs.replace(root,'')
                        stuff[folder] = files
    except:
        print("error connecting to",root)

    return stuff



def hasFolder(folder, rstuff):
    try:
        if folder in list(rstuff):
            return True
    except:
        return False
    


def needsFile(folder,files,rstuff):
    needfiles = []

    try:
        for f in list(files):
            if f in rstuff[folder]:
                ltime = int(getmtime(home+"/"+folder+"/"+f))
                rtime = int(getmtime(remote+"/"+folder+"/"+f))
                #print (f,":",ltime,"vs",rtime)
                if ltime != rtime:
                    needfiles.append(f)
            else:
                needfiles.append(f)
    except:
        print("error cannot check files in folder",folder)

    return needfiles



def checkStuff(lstuff,rstuff):
    print(list(lstuff),"\n",list(rstuff))
    print("checking sync")
    try:
        if len(list(lstuff))>0 and len(list(rstuff))>0:
            print (lstuff,"\n",rstuff)
    except:
        print("error, cannot seem to list files")
        #return

    #add all folders first
    try:
        print("checking folders")
        for lfolder in list(lstuff):
            print("checking folder",lfolder)
            if not hasFolder(lfolder,rstuff): #we should assume everything inside needs copying
                print ("needs folder",lfolder);

                #try and copy whole folder contents if entire folder is missing
                #try:
                #    shutil.copytree(home+"/"+lfolder, remote+"/"+lfolder, symlinks=True)
                #except IOError as e:
                #    print("error:",e,", folder contents not bulk-copied")
                
                #make a folder to copy to if it's still missing
                if not os.path.isdir(remote+"/"+lfolder): #double check
                    os.makedirs(remote+"/"+lfolder)
                    time.sleep(.1) #breathe a second
                    print ("created folder")
                else:
                    print ("major error in folders",lfolder)
                    continue #quit this iteration
    except:
        print("error cannot check folders")

    time.sleep(3)
    try:
        print("regrabbing more up to date remote listing")
        rstuff = getStuff(remote) #regrab remote listing, should be more up to date now
    except:
        print("error, cannot grab remote listing")
    
    #add all files now
    try:
        print("checking files")
        for lfolder in list(lstuff):
            files = needsFile(lfolder,lstuff[lfolder],rstuff)
            if (files):
                print ("need these files",files,"in this folder",lfolder)
                for f in files:
                    try:
                        
                        shutil.copy2(home+"/"+lfolder+"/"+f, remote+"/"+lfolder+"/"+"tmp.fsync")
                        print("copy file as temp")
                        if (os.path.isfile(remote+"/"+lfolder+"/"+f)):
                            print ("removing previous backup")
                            os.remove(remote+"/"+lfolder+"/"+f) #remove original, backuped file
                        os.rename(remote+"/"+lfolder+"/"+"tmp.fsync",remote+"/"+lfolder+"/"+f)
                        
                        print("file copied successfully",f)
                    except IOError as e:
                        print("error:",e,", file not copied ",f)
    except:
        print("error, cannot check files")

def main():
  global lstuff,rstuff
    
  while(1):
    checkConfig() #load our config if needed
    checkBackupRoot()

    lstuff = getStuff(home)
    rstuff = getStuff(remote)

    checkStuff(lstuff,rstuff)
    
    if twowaysync: #not working! FIXME
        print("performing reverse sync")
        checkStuff(rstuff,lstuff)

    if (sched):
        print("sleeping now",schedtime/60,"minutes/",schedtime,"seconds")
        time.sleep(schedtime)
    else: break



main() #kick off program
