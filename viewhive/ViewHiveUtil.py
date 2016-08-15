from sortedcontainers import SortedDict
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from picamera import PiCamera, Color
import time
from datetime import datetime as dt
from multiprocessing import Process
import subprocess
import sys
import shutil
import os, errno
import curses
import Adafruit_SSD1306
import Adafruit_GPIO.SPI as SPI 


def now():
    # Return current time and date as a string
    return dt.now().strftime("%Y-%m-%d_%H.%M.%S")
def nowt():
    # Return current time as a formatted string
    return dt.now().strftime("%H:%M")
def nowti():
    # Return current time as an int
    return (dt.now().strftime("%H%M"))
def waitforUSB(drivename):
    print("Looking for USB drive named %s..."% drivename)
    path = '/media/pi/'+drivename+'/'
    while os.path.exists(path) == False:
          print("Waiting for %s USB..." % drivename)
          wait(3)
    print("%s detected at %s !"% (drivename, path))
def silentremove(filename):
    try:
        os.remove(filename)
        print ("*** Deleted: ", filename)
    except OSError as e:
        if e.errno != errno.ENOENT: # no such file or directory
            raise # re-raise exception if a different error occured


class Recorder(object):

    def __init__(self):
        self.camera = PiCamera()
        self.camera.rotation = 180
        self.camera.resolution = (1920, 1080)
        self.camera.framerate = 30
        #camera.resolution = (1296, 730)
        #camera.framerate = 49
        self.camera.annotate_background = Color('grey')
        self.camera.annotate_foreground = Color('purple')
        time.sleep(5)
        self.timestamp = now()
        self.recRes = 0.01 # resolution of elapsed time counter (seconds)
        #####
        #
        # 3600 seconds per hour
        self.recPeriod = 10 # Seconds to record

        self.usbname = 'VIEWHIVE'
        self.dstroot = '/media/pi/'+self.usbname+'/'
        self.coderoot = '/home/pi/ViewHive/viewhive/ViewHive'
        self.srcfile = ''
        self.srcroot = ''
        self.convCommand = ''
        #####        
        self.camera.start_preview(alpha=100)
        print('*** Active on %s***\n' % self.timestamp)


    def record(self):
        # Wait for USB drive named VIEWHIVE
        waitforUSB(self.usbname)

        # Name files with current timestamp
        self.timestamp = now()
        self.srcfile = '%s.h264' % self.timestamp
        self.srcroot = '/home/pi/Videos/%s' % self.srcfile
        self.convCommand = 'MP4Box -add {0}.h264 {1}.mp4'.format(self.timestamp,self.timestamp)

        print("Recording started at %s ..."% self.timestamp)
        self.camera.start_recording(self.srcroot, format='h264')
        self.camera.led = True
        for i in range(self.recPeriod*int((1/self.recRes))):
            timeElapS = "%.2f" % round(float(i+1)*self.recRes, 3)
            self.camera.annotate_text = "{0}, Elapsed: {1}".format(now(), timeElapS)
            time.sleep(self.recRes)
        self.camera.annotate_text = "{0}, DONE".format(now())
        self.camera.wait_recording(1)
        self.camera.stop_recording()
        shutil.copy(self.srcroot, self.dstroot)
        print(self.convCommand)
        conv = subprocess.Popen(self.convCommand, shell=True,
                            cwd=self.dstroot)
        conv_status = conv.wait()
        if conv_status==0:
            print ("*** Conversion complete ***")
        else:
            print ("**! Conversion FAILED !**")
        self.camera.led = False

        silentremove(self.srcroot)
        silentremove("{0}{1}.h264".format(self.dstroot,self.timestamp))
        print("{0} contains:".format(self.dstroot))
        p = subprocess.Popen("ls", shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             cwd=self.dstroot)
        p_status = p.wait()
        for line in iter(p.stdout.readline, b''):
            print (line),
        self.camera.stop_preview()
        self.camera.led = True
        time.sleep(2)
        self.camera.close()
        #
        #




def code1440(time):
    # Convert a 2400 time to 1440 time
    if(len(time) == 4):
        tRaw = (int(time[0])*600+int(time[1])*60)+int(time[2])+int(time[3])
    elif(len(time) == 3):
        tRaw = (int(time[0])*60)+int(time[1])+int(time[2])
    elif(len(time) == 2):
        tRaw = int(time[0])+int(time[1])
    else:
        tRaw = int(time[0])
    return tRaw
def code2400(time):
    # Convert a 1440 time to 2400
    if(len(time) == 4):
        tRaw = (int(time[0])*600+int(time[1])*60)+int(time[2])+int(time[3])
    elif(len(time) == 3):
        tRaw = (int(time[0])*60)+int(time[1])+int(time[2])
    elif(len(time) == 2):
        tRaw = int(time[0])+int(time[1])
    else:
        tRaw = int(time[0])
    return tRaw

    

class Schedule(object):

    def __init__(self, name, source):
        self.name = name
        self.source = source            # Source file
        self.file = open(source)
        self.content = self.file.read() # Intermediary data for read/write
        self.file.close()
        self.events = []                # List of schedule events

        self.WpiToEvents()
        
    #   Display Schedule source file data
    def showSource(self):
        self.file = open(self.source)
        print("Source content:",)
        print(self.file.read())
        self.file.close()

    #   Display cuurent Schedule content
    def showContent(self):
        print("Schedule's current content:")
        print(self.content)

    #   Display list of user-defined events
    def showEvents(self):
        print("All events:")
        for event in self.events:
            print("From %04d to %04d" % (event['start'], (event['start']+event['length'])))
        print("\n")

    #   Convert an events list to Witty Pi schedule text
    def EventsToWpi(self):
            # rules:
            #   Minimize OFF periods (1M only) to right before a recording
            #   Maximize ON WAIT periods since unit will decay to shutdown
            #   Recording length stored in comment in ON line
            #   ON line w/o a comment is a wait period
            #   Start and end days with a wait period
            #   All elements seperated by tabs
            # ON    H1 M59  WAIT
            # OFF   M1
            # ON    H22  WAIT    #H1
        # converts the event list to wpi format and store in self.content
        self.content = ''
        header ='''# HiveView generated schedule v1.1
# Turn on 30 minutes before sunrise and sunset everyday
#	05:52, 20:36 (05:22, 20:06) for VA on 7/11/2016
#
# Recording length in comments

BEGIN	2015-08-01 00:00:00
END	2025-07-31 23:59:59'''
        wpiCommands = [""]
        i = 0
        curTime = 0
        def code(time, **k_parems):
            h = ''
            m = ''
            
            timeS = str(time)
            print(": "+"timeS: "+timeS+" curTime: "+str(curTime))
            if(time>=100): # Has an hour component
                if(time>=1000): # more than 10 hours
                    h = 'H%s%s'% (timeS[0], timeS[1])
                    if('state' in k_parems and k_parems['state'] == 'ON'): # For an ON command
                        if(timeS[2] != '0' or timeS[3] != '0'): # there are minutes
                            h = 'H%s'% timeS[0:1]
                            m = 'M%d'% (int(timeS[2:3])-1) # subtract 1 minute for OFF state
                        else: # m goes from 00 to 59
                            h = 'H%d'% (int(timeS[0:2]) - 1)
                            m = 'M59'
                    else:
                        h = 'H%s'% timeS[0:1]
                        m = 'M%s%s'% (timeS[2], timeS[3])
                    code = h+' '+m
                    
                else:   # less than 10 hours
                    if('state' in k_parems and k_parems['state'] == 'ON'): # For an ON command
                        if(timeS[1] != '0' or timeS[2] != '0'): # there are minutes                            
                            h = 'H%s'% timeS[0]
                            m = 'M%d'% (int(timeS[1:2])-1) # subtract 1 minute for OFF state
                        else:                           
                            h = 'H%d'% (int(timeS[0]) - 1)
                            m = 'M59' 
                    else:
                        h = 'H%s'% timeS[0]
                        m = 'M%s%s'% (timeS[1], timeS[2])
                    code = h+' '+m
            else:   # Only has a minute component
                code = 'M%s'% time
            return code
            

        
        for event in self.events:   # For each event in the list...
            print("Event %d: %04d to %04d" % (i, event['start'], (event['start']+event['length'])))
            if(i==0 and len(self.events)>1):   # First event
                print("First event ..."),
                if(event['start']>0):   # If starting after midnight, add morning buffer
                    print("Adding morning buffer ..."),
                    wpiCommands.append('ON\t%s\tWAIT'% code(event['start'],state="ON"))
                    wpiCommands.append('OFF\tM1')
                    curTime+= event['start']
                #   Actual first event
                wpiCommands.append('ON\t%s\tWAIT\t#%s'% (code(self.events[i+1]['start']-(curTime), state="ON"),code(event['length'])))
                wpiCommands.append('OFF\tM1')
                curTime = self.events[i+1]['start']
                
            elif(i==len(self.events)-1): # Last or only event
                print("Last (only?) event ..."),
                if(i==0):
                    print("Adding morning buffer for ONLY event..."),
                    wpiCommands.append('ON\t%s\tWAIT'% code(event['start'],state="ON"))
                    wpiCommands.append('OFF\tM1')
                sleep = 2400 - curTime  # stretch until midnight
                wpiCommands.append('ON\t%s\tWAIT\t#%s' %(code(sleep, state="ON"),code(event['length'])))
                print(curTime," + ",sleep," should be 2400!")
                                            
            else:       # All other events
                print("Average event ..."),
                wpiCommands.append('ON\t%s\tWAIT\t#%s' %(code(self.events[i+1]['start']-(curTime), state="ON"),code(event['length'])))
                wpiCommands.append('OFF\tM1')
                curTime = self.events[i+1]['start']
            i+= 1
            
        #   Combine all command strings into contents
        self.content = '\n'.join(wpiCommands)
        self.content = header+self.content
        self.showContent()
        
    #   Convert Witty Pi schedule text to an events list
    def WpiToEvents(self):
        wpiLines = self.content.split('\n')
        tempEvent = self.clearEvent()
        i = 0
        curLength = 0

        # converts the wpi time codes to 0000 formatted time int
        def time(code):
            code0000 = 0000
            if(' ' not in code): # if the command has 1 number
                if(code[0] == 'H'):
                    hours = int(code[1:len(code)])*100
                    code0000+= hours
                if(code[0] == 'M'):
                    mins = int(code[1:len(code)])
                    if(mins > 59): mins = 100
                    code0000+= mins
            elif(' ' in curCommand[1]):   # Hour and minute present
                splitCode = code.split(' ')
                hours = int(splitCode[0][1:len(splitCode[0])])*100
                mins = int(splitCode[1][1:len(splitCode[1])])+1
                if(mins > 59): mins = 100
                code0000+= hours
                code0000+= mins
            return code0000

        ##  While reading header
        while len(wpiLines[i]) < 1 or wpiLines[i][0] == '#':
            print(i," ", wpiLines[i])
            i += 1
        print(i," ", wpiLines[i])  # BEGIN
        i+=1
        print(i," ", wpiLines[i])  # END
        i+=1
        curTime = 0

        ##  While reading WPI command lines
        while i < len(wpiLines):
            curCommand = wpiLines[i].split('\t')
            print(i," ", curCommand),
            curType = curCommand[0]
##            print("%s command Length: %d"% (curType, curLength))
            if(curType == 'ON'):
                #   If theres a recording length comment
                if('#' in curCommand[len(curCommand)-1]):
                    curTime+= time(curCommand[1])
                    comment = curCommand[len(curCommand)-1].split('#')
                    
                    tempEvent['length'] = time(comment[1])-1
##                    print("Length is %d"%tempEvent['length']),
##                    tempEvent['end'] = tempEvent['start']+time(comment[1])-1
                    self.events.append(tempEvent)
                    self.ED = SortedDict(self.events)
                    self.showEvents()
                    tempEvent = self.clearEvent()
                    i+=1
                #   Otherwise this is a gap without recording length
                else:
                    curTime+= time(curCommand[1])
                    tempEvent = self.clearEvent()
                    print("ON Gap ending at %d, not recording"% curTime)
                    i+=1
                    
            elif(curType == 'OFF'):
                tempEvent['start'] = curTime
                i+=1
            else:
                print("NON-command on this line ", curCommand)
                i+=1





    #
    #   Ask for and append a new event entry (start/end times)
    def addEvent(self, s, l):
        print("Adding an event ... "),
        # Create an empty new event and sorted events list
        newEvent = {'start' : 0000,
                  'length' : 0000}        
        sortedEv = []
        
        while True:
            try:
                newEvent['start'] = s
                newEvent['length'] = l

                assert (newEvent['start'] < 2400) or (newEvent['length'] < 2400), "Entered a start%d/length%d greater than 2400!"% (newEvent['start'], newEvent['start'])
                assert newEvent['length'] != 0, "Entered 0000 for length!"
                break
            
            except ValueError:
                print("Not a valid time! Quit?"),
                if(self.confirmed()): return
            except AssertionError as strerror:
                print("%s Try again!"% strerror),

        # Create an event list sorted by start time        added = False
        if(len(self.events) == 0): self.events.append(newEvent)
        elif(newEvent['start'] > self.events[len(self.events)-1]['start']):
            # new event will be the last
            self.events.append(newEvent)
        else:
            for ev in self.events:
                if (ev['start'] < newEvent['start']): # New event is after this one
                    print("Added ev at %d"%(ev['start']))
                    sortevEv.append(ev)
                else:   # New event is before this one
                    time.sleep(3)
                    sortedEv.append(newEvent)
                    sortedEv.append(ev)
                    print("Added newEvent and ev at %d"%(ev['start']))
            if(len(sortedEv) != len(self.events)+1):
                print("Adding error")
                print("sortedEv len %d, events len %d" % (len(sortedEv), len(self.events)))
                golf
            print("sortedEv len %d, events len %d" % (len(sortedEv), len(self.events)))
            self.events = list(sortedEv)
            print("sortedEv len %d, events len %d" % (len(sortedEv), len(self.events)))

        
        print("New event added! There are %d events:" % len(self.events))
        self.showEvents()

    #
    #   Empty the schedule's event list
    def clearAllEvents(self):
        print("Clearing events..."),
        newEvent = {'start' : 0000,
                  'length' : 0000}
        self.events.clear()
        self.ED = SortedDict(self.events)
        print("Events cleared! There are %d events:" % len(self.events))
    
    #   Return a blank event item
    def clearEvent(self):
        blankEvent = {'start' : 0000,
                 'length' : 0000}
        return blankEvent


    def sync(self):
        # sync object with schedule file
        # truncate
        # write header comments
        # write BEGIN and END
        # wrie events in wpi format
        self.EventsToWpi()
        self.file = open(self.source, 'w')
        self.file.write(self.content)
        print("Schedule source overwritten ...")
        self.file.close()
        
        # Copy local schedule file to wittyPi directories
        cpCom1 = 'sudo cp -v ./'+self.source+' /home/wittyPi/schedules/HVScriptIMPORT.wpi'
        cpCom2 = 'sudo cp -v ./'+self.source+' /home/wittyPi/schedule.wpi'
        os.system(cpCom1)
        os.system(cpCom2)
        print("Schedule files copied ...")
        
        # Set wittyPi schedule with its runScript.sh
        print(subprocess.check_output(["sudo", "/home/wittyPi/runScript.sh"],
                                  universal_newlines = True))
        print("Ran wittyPi runScript.sh ...")








##  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def nav(screen):
    screen.addstr(8,8,"Surfin >")
    start = 30000
    # 10000 tics ~= 6.5 seconds
    tic = start
    screen.keypad(1)
    # halfdelay blocks for getch call for x tenths of a second
    screen.nodelay(1)
    while True:
        screen.addstr(9, 8, str(tic))
        if tic == 0: return 'DECAY'
        try:
            event = screen.getkey()
        except Exception as inst:            
            screen.addstr(10, 1,"* nav error: %s"% inst)
            # if called during cooldown, exit loop so OLED can countdown
            tic -= 1
##            print("*** nav error: %s"%inst)
##            return 'e'
##            return 'decay'
##            action = False
        else:
            screen.addstr(4, 1,"Got nav event %s"%event)
            tic = start
            if event == '0': return 0
            elif event == ord("2"):
                return chr(event)
            elif event == 'KEY_HOME':
                return 'CH'
            elif event == 'KEY_PPAGE':
                return 'CH-'
            elif event == 'KEY_NPAGE':
                return 'CH+'
            elif event == 'KEY_F(3)':
                return 'L'
            elif event == 'KEY_F(4)':
                return 'R'
            elif event == 'KEY_END':
                return 'P'
            elif event == 'KEY_UP':
                return 'U'
            elif event == 'KEY_DOWN':
                return 'D'
            elif event == 'KEY_ENTER':
                return 'ENT'
            
            elif event == 'KEY_F1':     # 100+ button
                return 'F1'
            elif event == 'KEY_F2':     # 200+ button
                return 'F2'
            elif event == '0': return 0
            elif event == '1': return 1
            else:
                screen.addstr(5, 1,"TRY AGAIN (not %s) >"%event)
        
        screen.clear()
    screen.addstr(5, 1,"OUT\n\n")

# if called during cooldown, exit loop so OLED can countdown
def navDecay(screen):
    screen.addstr(8,8,"Dyin >")
    screen.keypad(1)
    # halfdelay blocks for getch call for x tenths of a second
    screen.nodelay(1)
    while True:
        try:
            event = screen.getkey()
        except Exception as inst:            
            screen.addstr(10, 1,"* nav error: %s"% inst)
            break
##            print("*** nav error: %s"%inst)
##            return 'e'
##            return 'decay'
##            action = False
        else:
            screen.addstr(4, 1,"Got nav event %s"%event)
            if event == '0': return 0
            elif event == ord("2"):
                return chr(event)
            elif event == 'KEY_HOME':
                return 'CH'
            elif event == 'KEY_PPAGE':
                return 'CH-'
            elif event == 'KEY_NPAGE':
                return 'CH+'
            elif event == 'KEY_F(3)':
                return 'L'
            elif event == 'KEY_F(4)':
                return 'R'
            elif event == 'KEY_END':
                return 'P'
            elif event == 'KEY_UP':
                return 'U'
            elif event == 'KEY_DOWN':
                return 'D'
            elif event == '\n':
                return 'ENT'
            
            elif event == 'KEY_F1':     # 100+ button
                return 'F1'
            elif event == 'KEY_F2':     # 200+ button
                return 'F2'
            elif event == '0': return 0
            elif event == '1': return 1
            else:
                screen.addstr(5, 1,"TRY AGAIN (not %s) >"%event)

        screen.clear()
    screen.addstr(5, 1,"OUT\n\n")

#   Get user confirmation
def getConfirm(screen):
    screen.addstr(3,8,"Confirm by pressing ENTER >")
    screen.nodelay(0)
    screen.keypad(1)
    curses.echo()
    try:
        event = screen.getkey()
    except Exception as inst:            
        screen.addstr(11, 1,"* conf error: %s"% inst)
    else:
        screen.addstr(5, 1,"Got confirm event %s"% event)
        if event == '\n':
            screen.addstr(5, 20,"CONFIRMED")
            return True
        else: return False
        

#   Get user-input time string
def getTime(screen):
    screen.addstr(3,8,"Enter a time and press ENTER >")
    screen.nodelay(0)
    curses.echo()
    time = screen.getstr()
    return int(time)


class Display(object):
    def __init__(self, sch):
        print('Display instance starting...')
        RST = 24
        DC = 23
        SPI_PORT = 0
        SPI_DEVICE = 0
        self.disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))
        self.width = self.disp.width
        self.height = self.disp.height
        self.font = ImageFont.truetype("GameCube.ttf", 7)
        if sch == 0:
            self.schedule = []
        else:
            self.schedule = sch
##            self.events = sch.events

        
        print('...')
        self.mode = -1
        self.fresh = True
        self.start = 30
        # length of decay countdowm
        self.decay = self.start
        # initialize decay countdown

        
        print('....')
        self.disp.begin()
        self.image = Image.new('1', (self.width, self.height))
        
        print('.....')
        self.draw = ImageDraw.Draw(self.image)
        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)

##        
##        self.screen = curses.initscr()
##        curses.echo()
##        curses.curs_set(0)
##        self.screen.keypad(1)
##
##    class AwaitCommand(threading.Thread):
##        def run(self):
##            print("Awaiting command")
##            c = input()
##            if(c == '1'):
##                print(c)
##                self.mode = 1

    def update(self):
        self.disp.clear()
        self.disp.image(self.image)
        self.disp.display()

    def clear(self):
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)



    def welcome(self):
        # Load default font.
        font = ImageFont.truetype("electroharmonix.ttf", 12)
        self.draw.text((2, 2),    'Hello',  font=self.font, fill=255)
        self.draw.text((2, 15), 'ViewHive v0.6!', font=self.font, fill=255)
        self.update()
        time.sleep(3)



    def startRooms(self):
##        self.clear()
##        self.mode = 'TIME'
##        self.tabs()
##        self.update()
        recRes = 0.01
        while self.decay>0:
            if(self.mode == 'TIME'): 
                com = curses.wrapper(navDecay)
            else: com = curses.wrapper(nav)
            if(self.fresh == True):
                i = 0   # If this view is fresh, reset item index
          
            # Interpret navigation commands
            if(com == 'CH'):
                self.mode = 'ADD'
                self.fresh = True
                self.decay = self.start
            elif(com == 'CH-'):
                if(self.mode == 'VIEW'): self.mode = 'TIME'
                elif(self.mode == 'ADD'): self.mode = 'VIEW'
                elif(self.mode == 'DEL'): self.mode = 'ADD'
                elif(self.mode == 'TIME'): self.mode = 'DEL'
                self.fresh = True
                self.decay = self.start
            elif(com == 'CH+'):
                if(self.mode == 'VIEW'): self.mode = 'ADD'
                elif(self.mode == 'ADD'): self.mode = 'DEL'
                elif(self.mode == 'DEL'): self.mode = 'TIME'
                elif(self.mode == 'TIME'): self.mode = 'VIEW'
                self.fresh = True
                self.decay = self.start

            
            elif(com == 'P' or com == 'ENT'):
                 if(self.mode == 'TIME' or self.mode == 'ADD'): i = -1
                 self.fresh = False
                 
            elif (com == 0 and self.mode == 'DEL'): i = -1
            elif (com == 1 and self.mode == 'ADD'): i = -1
            
            # Interpret Left and Right commands
            elif(com == 'R'):
                if(i==len(self.schedule.events)-1): pass
                else:
                    i += 1
                    self.fresh = False
            elif(com == 'L'):
                if(i==0): pass
                else:
                    i -= 1 
                    self.fresh = False
                    
            # Interpret a DECAY command due to idling
            elif(com == 'DECAY'):
                self.mode = 'TIME'
            
##            if(self.decay < self.start/2):  # When decay is almost complete, show countdown
##                self.mode = 'TIME'
##                # Clear image buffer by drawing a black filled box.
##                self.draw.rectangle((0,12,self.width,24), outline=0, fill=0)
##                self.draw.text((self.width/2-25,self.height/2), '%.2f' % round(float(self.decay),3),
##                        font=self.font, fill=1)

            
            if(self.fresh == True):
                i = 0   # If this view is fresh, reset item index
            self.tabs()
            self.showRoom(self.mode, i)
            self.eventsBar()
##            self.draw.text((120,self.height/2), '%s' % i,
##                        font=self.font, fill=1)
            
            self.update()
            self.decay -= recRes*2
            time.sleep(recRes/2)
        # Decay is complete, SHUTDOWN
        self.mode = 'KILL'
        self.tabs()
        self.update()

    def showRoom(self, mode, i):
        if(mode == 'VIEW'): self.roomView(i)
        if(mode == 'ADD'): self.roomAdd(i)
        if(mode == 'DEL'): self.roomDelete(i)
        if(mode == 'TIME'): self.roomTime(i)







            

    def roomMain(self):
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0,12,self.width,24), outline=0, fill=0)
        self.draw.text((1,self.height/2), 'MAIN main', font=self.font, fill=1)

    
    def roomView(self, i):
        i = i
        if(len(self.schedule.events)==0):
            curString = 'No events scheduled'
        else:
            
            cur = self.schedule.events[i]
            curString = '%d) %d'%(i+1, cur['start'])+' for '+'%d.'%cur['length']
            if(len(self.schedule.events)>1 and i<len(self.schedule.events)-1):
                self.draw.text((self.width-10,self.height/2), '...',
                            font=self.font, fill=1)
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0,12,self.width,24), outline=0, fill=0)
        self.draw.text((3 ,self.height/2), '%s' % curString,
                        font=self.font, fill=1)
##        self.eventsBar()

    def roomDelete(self, i):
        i = i
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0,12,self.width,24), outline=0, fill=0)
        if i == -1:
            self.draw.text((2, self.height/2), "Delete all events?",
                           font=self.font, fill=1)
            
            self.update()
            answer = curses.wrapper(getConfirm)
            
            self.draw.rectangle((0,12,self.width,24), outline=0, fill=0)
            if answer == True :
                ## Call schedule delete function
                self.schedule.clearAllEvents()
                self.draw.text((self.width/2-30, self.height/2), "DELETED!",
                           font=self.font, fill=1)
            else:
                self.draw.text((self.width/2-28, self.height/2), "Canceled",
                           font=self.font, fill=1)
            self.update()
            time.sleep(2)
            self.fresh = True
        elif i == 0:
            self.draw.text((2, self.height/2), "Press 0",
                           font=self.font, fill=1)
            self.fresh = True
                
        
    def roomTime(self, i):
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0,12,self.width,24), outline=0, fill=0)
        i = i
        if(i == -1):    # Setting system/RTC time
            self.draw.text((3 ,self.height/2), 'Give cur. time:',
                       font=self.font, fill=1)
            
            time = curses.wrapper(getTime)
            # Clear image buffer by drawing a black filled box.
            self.draw.rectangle((0,12,self.width,24), outline=0, fill=0)
            self.draw.text((3 ,self.height/2), '%d' % time,
                       font=self.font, fill=1)
            self.fresh = True
        else:   # Show current time in tabs and decay coutdown
            time = nowt()
            self.draw.text((self.width/2-50,self.height/2), 'Shutdown in  %.2f' % round(float(self.decay),3),
                        font=self.font, fill=1)
            self.fresh = True 
        
        

    def roomAdd(self, i):
        # Add an event

        i = i
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0,12,self.width,24), outline=0, fill=0)
        if i == -1:
            self.draw.text((2, self.height/2), "Add an event?",
                           font=self.font, fill=1)
            self.update()
            
            answer = curses.wrapper(getConfirm)
            self.draw.rectangle((0,12,self.width,24), outline=0, fill=0)
            if answer == True :
                self.draw.text((1, self.height/2), 'ADDING', font=self.font, fill=1)
                self.update()
                time.sleep(2)
                # Get start and length times for new event
                self.draw.rectangle((0,12,self.width,24), outline=0, fill=0)
                self.draw.text((1, self.height/2), 'Enter start time 0000 >',
                               font=self.font, fill=1)
                self.update()
                start = curses.wrapper(getTime)     # Start time from 0000 to 24000
                self.draw.rectangle((0,12,self.width,24), outline=0, fill=0)
                self.draw.text((1, self.height/2), 'Enter rec. length 0000 >',
                               font=self.font, fill=1)
                self.update()
                length = curses.wrapper(getTime)    # Length of event

                # Now confirm these entries
                self.draw.rectangle((0,12,self.width,24), outline=0, fill=0)
                self.draw.text((2, self.height/2), "At %d for %d?"% (start,length),
                           font=self.font, fill=1)
                self.update()
                
                conf = curses.wrapper(getConfirm)
                self.draw.rectangle((0,12,self.width,24), outline=0, fill=0)
                if conf == True :
                    ## Call schedule add function
                    self.schedule.addEvent(start, length)
                    self.draw.text((1, self.height/2), 'Event ADDED...', font=self.font, fill=1)
                    ## Call schedule synch function
##                    self.draw.text((1, self.height/2), 'Events SYNCHED', font=self.font, fill=1)
                else:
                    self.draw.text((self.width/2-28, self.height/2), "Canceled SAVE",
                               font=self.font, fill=1)
            else:
                self.draw.text((self.width/2-28, self.height/2), "Canceled ADD",
                           font=self.font, fill=1)
            
        elif i == 0:
            self.draw.text((2, self.height/2), "Press 1",
                           font=self.font, fill=1)
            self.fresh = True

    




                

    def eventsBar(self):
        i=0     #   1440 minutes in a day
        # Clear bar buffer by drawing a black filled box.
        self.draw.rectangle((0,28,self.width,self.height), outline=0, fill=0)
        while(i<=1440):
            x = ((self.width-3)*(i/1440))
            if(i%720 == 0):
                self.draw.line(((x,26) , (x,self.height)), fill=1)
            elif(i%180 == 0):
                self.draw.line(((x,28), (x,self.height)), fill=1)            
            elif(i%60 == 0):
                self.draw.line(((x,30) , (x,self.height)), fill=1)
            else:
                ##self.draw.line(((x,31), (x,self.height)), fill=1)
                pass
            i+=30
        for ev in self.schedule.events:
            start = code1440(str(ev['start']))
            length = code1440(str(ev['length']))
            
            s = self.width*(start/1440)
            e = (self.width*((start+length)/1440))
            self.draw.chord((s,30, e,self.height), -180,0, outline=1, fill=0)
##            self.draw.line(((s, 20) , (s,32)), fill=1)

    def tabs(self):
        length = 40
        off = 6
        buf = 8
        h = 10
        # Clear tab buffer by drawing a black filled box.
        self.draw.rectangle((0,0,self.width,h), outline=0, fill=0)
        if(self.mode == 'VIEW'):
            self.draw.polygon([(buf,0), (buf+length,0), (buf+length-off/2,h) , (buf+off/2,h)],
                              outline=0, fill=1)
            self.draw.text((10+off/2, 0), 'VIEW',  font=self.font, fill=0)

            self.draw.polygon([(buf+length,0), (buf+(length*2)-off,0), (buf+(length*2)+off/2,h) , (buf+length-5,h)],
                              outline=255, fill=0)
            self.draw.text((buf+length+5, 0), 'ADD',  font=self.font, fill=255)
        
            self.draw.polygon([(buf+(length*2-off),0), (buf+length*3-off,0), (buf+length*3-off-off/2,h) , (buf+length*2-off/2,h)],
                              outline=255, fill=0)
            self.draw.text((buf+length*2+5, 0), 'DEL',  font=self.font, fill=255)

        elif(self.mode == 'ADD'):
            self.draw.polygon([(buf,0), (buf+length,0), (buf+length-off/2,h) , (buf+off/2,h)],
                              outline=1, fill=0)
            self.draw.text((10+off/2, 0), 'VIEW',  font=self.font, fill=1)

            self.draw.polygon([(buf+length,0), (buf+(length*2)-off,0), (buf+(length*2)+off/2,h) , (buf+length-off/2,h)],
                              outline=0, fill=1)
            self.draw.text((buf+length+5, 0), 'ADD',  font=self.font, fill=0)
        
            self.draw.polygon([(buf+(length*2-+off),0), (buf+length*3-off,0), (buf+length*3-off-off/2,h) , (buf+length*2-off/2,h)],
                              outline=1, fill=0)
            self.draw.text((buf+length*2+5, 0), 'DEL',  font=self.font, fill=1)

        elif(self.mode == 'DEL'):
            self.draw.polygon([(buf,0), (buf+length,0), (buf+length-off/2,h) , (buf+off/2,h)],
                              outline=1, fill=0)
            self.draw.text((10+off/2, 0), 'VIEW',  font=self.font, fill=1)

            self.draw.polygon([(buf+length,0), (buf+(length*2)-off,0), (buf+(length*2)+off/2,h) , (buf+length-off/2,h)],
                              outline=1, fill=0)
            self.draw.text((buf+length+5, 0), 'ADD',  font=self.font, fill=1)
        
            self.draw.polygon([(buf+(length*2-off),0), (buf+length*3-off,0), (buf+length*3-off-off/2,h) , (buf+length*2-off/2,h)],
                              outline=0, fill=1)
            self.draw.text((buf+length*2+5, 0), 'DEL',  font=self.font, fill=0)

        elif(self.mode == 'TIME'):
            self.draw.polygon([(buf,0), (self.width-buf,0), (self.width-buf-off/2,h) , (buf+off/2,h)],
                              outline=1, fill=0)
            self.draw.text((self.width-45, 1), "%s" % nowt(),  font=self.font, fill=1)
        else:
            self.draw.polygon([(buf,0), (self.width-buf,0), (self.width-buf-off/2,h) , (buf+off/2,h)],
                              outline=0, fill=1)
            self.draw.text((self.width/2-25, 0), 'VIEWHIVE',  font=self.font, fill=0)

##
##
##schedule_cur = Schedule("HVScriptUTIL.wpi")
##schedule_cur.showContent()
##schedule_cur.WpiToEvents()
##schedule_cur.EventsToWpi()
##
##while True:
##    schedule_cur.addEvent()
##    schedule_cur.EventsToWpi()
##    schedule_cur.clearAllEvents()
##    schedule_cur.addEvent()
##    schedule_cur.showContent()

