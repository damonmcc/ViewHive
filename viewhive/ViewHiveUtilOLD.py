import errno
import os
import shutil
import subprocess
import time
from datetime import datetime as dt

from RPi import GPIO
import Adafruit_GPIO.SPI as SPI
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import picamera


def now():
    # Return current time and date as a string
    return dt.now().strftime("%Y-%m-%d_%H.%M.%S")


def nowt():
    # Return current time as a formatted string
    return dt.now().strftime("%H:%M")


def nowdt():
    # Return current date and time for display
    return dt.now().strftime("%Y/%m/%d, %H:%M")


def nowdts():
    # Return current date and time with seconds for display
    return dt.now().strftime("%Y/%m/%d, %H:%M:%S")


def nowti():
    # Return current time as an int
    return int(dt.now().strftime("%H%M"))


def dateFormat(y, m, d, time):
    # Return current time and date for command line script
    # Add date input support
    # Date format: YYYYMMDD?
    print("Date %r %r %r" % (y, m, d))
    ys = str(y)
    ms = str(m)
    ds = str(d)
    if len(time) < 3:
        hours = "00"
        minutes = time[:]
    elif len(time) == 3:
        hours = time[:1]
        minutes = time[2:]
    else:
        hours = time[:2]
        minutes = time[2:]
    print("From %r... Hours %r , Mins: %r" % (time, hours, minutes))
    return dt.now().strftime(ys + "-" + ms + "-" + ds + " " + hours + ":" + minutes + ":00")


def waitforUSB(drivename):
    print("Looking for USB named %s..." % drivename)
    path = '/media/pi/' + drivename + '/'
    while os.path.exists(path) == False:
        print("Waiting for %s USB..." % drivename)
        time.sleep(3)
    print("%s detected at %s !" % (drivename, path))
    print("USB contains:")
    p = subprocess.Popen("ls", shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         cwd=path)
    p_status = p.wait()
    for line in iter(p.stdout.readline, b''):
        print(line),


def silentremove(filename):
    try:
        os.remove(filename)
        print("*** Deleted: ", filename)
    except OSError as e:
        if e.errno != errno.ENOENT:  # no such file or directory
            raise  # re-raise exception if a different error occured


class Recorder(object):
    def __init__(self):
        print('.. Recorder init.. ', end='')
        self.camera = picamera.PiCamera()
        print('.. ', end='')
        # self.camera.rotation = 180
        # self.camera.resolution = (1920, 1080)
        # self.camera.framerate = 30
        self.camera.resolution = (1296, 730)
        self.camera.framerate = 49
        self.camera.annotate_background = picamera.Color('grey')
        self.camera.annotate_foreground = picamera.Color('purple')
        print('.')
        self.timestamp = now()
        self.timeElaps = 0
        self.recRes = 0.01  # resolution of elapsed time counter (seconds)
        #####
        #
        # 3600 seconds per hour
        self.recPeriod = 10  # Seconds to record

        self.usbname = 'VIEWHIVE'
        self.dstroot = '/media/pi/' + self.usbname + '/'
        self.coderoot = '/home/pi/ViewHive/viewhive/ViewHive'
        self.srcfile = ''
        self.srcroot = ''
        self.convCommand = ''
        #####        
        print('*** Recorder born %s***\n' % self.timestamp)
        os.system("sudo gpio -g mode 5 out")
        os.system("sudo gpio -g mode 6 out")
        os.system("sudo gpio -g write 5 0")
        os.system("sudo gpio -g write 6 0")
        # self.camera.led = False

    def start(self):
        # Wait for USB drive named VIEWHIVE
        waitforUSB(self.usbname)
        # Name files with current timestamp
        self.timestamp = now()
        self.startTime = time.time()
        self.srcfile = '%s.h264' % self.timestamp
        self.srcroot = '/home/pi/Videos/%s' % self.srcfile
        self.convCommand = 'MP4Box -add {0}.h264 {1}.mp4'.format(self.timestamp, self.timestamp)

        print("*** Recording started at %s ..." % self.timestamp)
        self.camera.start_recording(self.srcroot, format='h264')
        self.camera.led = True
        os.system("gpio -g write 5 1")
        os.system("gpio -g write 6 1")
        self.camera.start_preview(alpha=120)
        self.camera.annotate_text = "%s | START" % nowdts()

    def refresh(self):
        self.timeElaps = time.time() - self.startTime
        self.camera.annotate_text = "%s | %.3f" % (nowdts(), self.timeElaps)
        os.system("gpio -g write 5 1")
        os.system("gpio -g write 6 1")

    def stop(self):
        self.camera.annotate_text = "%s | %.2f END" % (nowdts(), self.timeElaps)
        self.camera.wait_recording(1)
        self.camera.stop_recording()
        # Wait for USB drive named VIEWHIVE
        waitforUSB(self.usbname)
        try:
            shutil.copy(self.srcroot, self.dstroot)
        except Exception as inst:
            print("*SAVE error: %s" % inst)
        else:
            silentremove(self.srcroot)

        ##        NO MORE CONVERTING TO MP4
        ##        print(self.convCommand)
        ##        conv = subprocess.Popen(self.convCommand, shell=True,
        ##                            cwd=self.dstroot)
        ##        conv_status = conv.wait()
        ##        if conv_status==0:
        ##            print ("*** Conversion complete ***")
        ##        else:
        ##            print ("**! Conversion FAILED !**")
        ##        silentremove("{0}{1}.h264".format(self.dstroot,self.timestamp))
        print("%s contains:" % self.dstroot)
        p = subprocess.Popen("ls", shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             cwd=self.dstroot)
        p_status = p.wait()
        for line in iter(p.stdout.readline, b''):
            print(line),
        self.camera.stop_preview()
        self.timeElaps = 0
        self.camera.led = False

        os.system("gpio -g write 5 0")
        os.system("gpio -g write 6 0")
        print("Recording stopped at %s ..." % now())

    def record(self):
        ### OLD standalone recording behavior
        ### NOT USED
        # Wait for USB drive named VIEWHIVE
        waitforUSB(self.usbname)

        # Name files with current timestamp
        self.timestamp = now()
        self.srcfile = '%s.h264' % self.timestamp
        self.srcroot = '/home/pi/Videos/%s' % self.srcfile
        self.convCommand = 'MP4Box -add {0}.h264 {1}.mp4'.format(self.timestamp, self.timestamp)

        print("Recording started at %s ..." % self.timestamp)
        self.camera.start_recording(self.srcroot, format='h264')
        self.camera.led = True
        for i in range(self.recPeriod * int((1 / self.recRes))):
            timeElapS = "%.2f" % round(float(i + 1) * self.recRes, 3)
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
        if conv_status == 0:
            print("*** Conversion complete ***")
        else:
            print("**! Conversion FAILED !**")
        self.camera.led = False

        silentremove(self.srcroot)
        silentremove("{0}{1}.h264".format(self.dstroot, self.timestamp))
        print("{0} contains:".format(self.dstroot))
        p = subprocess.Popen("ls", shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             cwd=self.dstroot)
        p_status = p.wait()
        for line in iter(p.stdout.readline, b''):
            print(line),
        self.camera.stop_preview()
        time.sleep(1)
        self.camera.close()
        #
        #


def code1440(time):
    # Convert a 2400 time to 1440 time
    if len(time) == 4:
        t_raw = (int(time[0]) * 600) + (int(time[1]) * 60) + (int(time[2]) * 10) + int(time[3])
    elif len(time) == 3:
        t_raw = (int(time[0]) * 60) + (int(time[1]) * 10) + int(time[2])
    elif len(time) == 2:
        t_raw = (int(time[0]) * 10) + int(time[1])
    else:
        t_raw = int(time[0])
    return t_raw


def code2400():
    # Convert a 1440 time to 2400
    if len(time) >= 2:
        m = int(time) % 60
        h = (int(time) - m) / 60
        t_raw = (h * 100) + m
        print('TRaw = %r' % (t_raw))
    else:
        t_raw = int(time[0])

    return t_raw



class Schedule(object):
    def __init__(self, name, source):
        self.name = name
        self.source = source  # Source file
        self.file = open(source)
        self.content = self.file.read()  # Intermediary data for read/write
        self.file.close()
        self.events = []  # List of schedule events
        self.version = 1.7
        self.WpiToEvents()

    #   Display Schedule source file data
    def showSource(self):
        self.file = open(self.source)
        print("\nSource " + self.source + " content:", )
        print(self.file.read())
        self.file.close()

    #   Display cuurent Schedule content
    def showContent(self):
        print("\nSchedule's current content:")
        print(self.content)

    #   Display list of user-defined events
    def showEvents(self):
        print("All events:")
        for event in self.events:
            s = event['start']
            e = code2400(str(code1440(str(event['start'])) + code1440(str(event['length']))))
            print("From %04d to %04d" % (s, e))
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
        # converts the event list to wpi format and stores in self.content
        self.content = ''
        time = now()
        header = '''# HiveView generated schedule v%r , %r
# Should turn on 30 minutes before sunrise and sunset everyday
#	%r
#
# Recording length in comments''' % (self.version, time, self.events)
        wpiCommands = [""]
        i = 0
        curTime = 0
        mornBuff = 0

        def code(time, **k_parems):
            # Convert a 2400 style time to a __:__ morning format or wittyPi's H__ M__ format
            # Parameters are state="ON", begin="ON"
            h = ''
            m = ''

            timeS = str(time)
            print(": " + "timeS: " + timeS + " curTime: " + str(curTime))
            if (time >= 100):  # Has an hour component
                if (time >= 1000):  # more than 10 hours
                    if ('state' in k_parems and k_parems['state'] == 'ON'):  # For an ON command
                        if (timeS[2] != '0' or timeS[3] != '0'):  # there are minutes
                            h = 'H%s%s' % (timeS[0], timeS[1])
                            m = '%s%s' % (timeS[2], timeS[3])
                            m = 'M%s' % (int(m) - 1)  # subtract 1 minute for OFF state
                        else:  # m goes from 00 to 59
                            h = '%s%s' % (timeS[0], timeS[1])
                            h = 'H%d' % (int(h) - 1)
                            m = 'M59'
                        code = h + ' ' + m
                    else:
                        if ('begin' in k_parems and k_parems[
                            'begin'] == 'ON'):  # begining of the day
                            h = '%s%s' % (timeS[0], timeS[1])
                            m = '%s%s' % (timeS[2], timeS[3])
                            code = h + ':' + m
                        else:
                            h = 'H%s%s' % (timeS[0], timeS[1])
                            m = 'M%s%s' % (timeS[2], timeS[3])
                            code = h + ' ' + m

                else:  # less than 10 hours, more than 1 hour
                    if ('state' in k_parems and k_parems['state'] == 'ON'):  # For an ON command
                        if (timeS[1] != '0' or timeS[2] != '0'):  # there are minutes
                            h = 'H%s' % timeS[0]
                            m = '%s%s' % (timeS[1], timeS[2])
                            m = 'M%s' % (int(m) - 1)  # subtract 1 minute for OFF state
                        else:
                            h = 'H%d' % (int(timeS[0]) - 1)
                            m = 'M59'
                        code = h + ' ' + m
                    else:
                        if ('begin' in k_parems and k_parems['begin'] == 'ON'):  # begining of the day
                            h = '0%s' % timeS[0]
                            m = '%s%s' % (timeS[1], timeS[2])
                            code = h + ':' + m
                        else:
                            h = 'H%s' % timeS[0]
                            m = 'M%s%s' % (timeS[1], timeS[2])
                            code = h + ' ' + m

            else:  # Only has a minute component
                if ('state' in k_parems and k_parems['state'] == 'ON'):  # For an ON command
                    code = 'M%s' % (time - 1)  # subtract 1 minute for OFF state
                else:
                    if ('begin' in k_parems and k_parems['begin'] == 'ON'):  # begining of the day
                        code = '00:%s' % time
                    else:
                        code = 'M%s' % time
            return code

        if (len(self.events) == 0):  # No events
            wpiCommands.append('BEGIN 2016-11-19 00:00:00')
            wpiCommands.append('END	2025-07-31 23:59:59')
            wpiCommands.append('ON H23 M59')
            wpiCommands.append('OFF M1')
            #   Combine all command strings into contents
            self.content = '\n'.join(wpiCommands)
            self.content = header + self.content
            self.showContent()

        else:
            for event in self.events:  # For each event in the list...
                print("Event %d: %04d to %04d" % (i, event['start'], (event['start'] + event['length'])))

                if (len(self.events) > 1 and i == 0):  # First event
                    print("First event ..."),
                    if (event['start'] > 0):  # If starting after midnight, add morning buffer
                        print("Adding morning buffer ..."),
                        startRAW = event['start']
                        mornBuff = startRAW
                        start = code(startRAW, begin='ON')
                        wpiCommands.append('BEGIN 2016-11-19 ' + start + ':00')
                        wpiCommands.append('END	2025-07-31 23:59:59')
                        ##                    wpiCommands.append('ON\t%s\tWAIT'% code(event['start'],state="ON"))
                        ##                    wpiCommands.append('OFF\tM1')
                        curTime = mornBuff
                    else:
                        wpiCommands.append('BEGIN 2016-11-19 00:00:00')
                        wpiCommands.append('END	2025-07-31 23:59:59')

                    gap = self.events[i + 1]['start'] - (curTime)
                    if (gap % 100 >= 60):
                        print("gap is: %s" % gap)
                        gap -= 40
                        print("after modulo, gap is: %s" % gap)
                    wpiCommands.append('ON\t%s\tWAIT\t#%s' % (code(gap, state="ON"), code(event['length'])))
                    wpiCommands.append('OFF\tM1')
                    curTime = self.events[i + 1]['start']

                elif (i == len(self.events) - 1):  # Last or only event
                    print("Last (or only?) event ..."),
                    if (i == 0):  # Only event
                        print("Adding morning buffer for ONLY event..."),
                        startRAW = event['start']
                        start = code(startRAW, begin='ON')
                        wpiCommands.append('BEGIN 2016-11-19 ' + start + ':00')
                        wpiCommands.append('END	2025-07-31 23:59:59')
                        wpiCommands.append('ON\t%s\tWAIT\t#%s' % (code(2400, state="ON"), code(event['length'])))
                        wpiCommands.append('OFF\tM1')
                    else:
                        # stretch until next BEGIN
                        # Sbtract times correctly in regards to the 2400 format
                        last = 2400 + mornBuff
                        last -= curTime
                        if (last % 100 >= 60):
                            print("last was: %s" % last)
                            last -= 40  # for the minutes?
                            print("after modulo, last is: %s" % last)
                        wpiCommands.append('ON\t%s\tWAIT\t#%s' % (code(last, state="ON"), code(event['length'])))
                        wpiCommands.append('OFF\tM1')
                        print(curTime, " + ", last, " should be 2400 + ", mornBuff, "!")
                else:  # All other events
                    print("Average event ..."),
                    gapA = self.events[i + 1]['start'] - (curTime)
                    if (gapA % 100 >= 60):
                        print("gap is: %s" % gapA)
                        gapA -= 40
                        print("after modulo, gap is: %s" % gapA)
                    wpiCommands.append('ON\t%s\tWAIT\t#%s' % (code(gapA, state="ON"), code(event['length'])))
                    wpiCommands.append('OFF\tM1')
                    curTime = self.events[i + 1]['start']
                i += 1

            # Combine all command strings into contents
            self.content = '\n'.join(wpiCommands)
            self.content = header + self.content
            self.showContent()

    # Convert Witty Pi schedule text to an events list
    def WpiToEvents(self):
        wpiLines = self.content.split('\n')
        tempEvent = self.clearEvent()
        i = 0
        curLength = 0

        # converts the wpi time codes to 0000 formatted time int
        def time(code, event):
            code0000 = 0000
            if (' ' not in code):  # if the command has 1 number
                if (code[0] == 'H'):
                    hours = int(code[1:len(code)]) * 100
                    code0000 += hours
                if (code[0] == 'M'):
                    if (event == True):
                        mins = int(code[1:len(code)])
                    else:
                        mins = int(code[1:len(code)]) + 1
                        if (mins > 59): mins = 100
                    code0000 += mins
            elif (' ' in curCommand[1]):  # Hour and minute present
                splitCode = code.split(' ')
                hours = int(splitCode[0][1:len(splitCode[0])]) * 100
                if (event == True):
                    mins = int(splitCode[1][1:len(splitCode[1])])
                else:
                    mins = int(splitCode[1][1:len(splitCode[1])]) + 1
                    if (mins > 59): mins = 100
                code0000 += hours
                code0000 += mins
            return code0000

        ##  While reading header
        while len(wpiLines[i]) < 1 or wpiLines[i][0] == '#':
            print(i, " ", wpiLines[i])
            i += 1
        print(i, " ", wpiLines[i])  # BEGIN
        bSplit = wpiLines[i].split(' ')
        bTime = dt.strptime(bSplit[len(bSplit) - 1], "%H:%M:%S")

        if (bTime.hour or bTime.minute != 0):
            print("Beginning has a non-zero time %r:%r!!!" % (bTime.hour, bTime.minute))

        i += 1
        print(i, " ", wpiLines[i])  # END
        i += 1
        curTime = 0

        ##  While reading WPI command lines
        while i < len(wpiLines):
            curCommand = wpiLines[i].split('\t')
            print(i, " ", curCommand),
            curType = curCommand[0]
            ##            print("%s command Length: %d"% (curType, curLength))
            if (curType == 'ON'):
                #   If theres a recording length comment
                if ('#' in curCommand[len(curCommand) - 1]):
                    if (curTime == 0):  # First event...
                        # Overide blank/0000 start time
                        tempEvent['start'] = (int(bTime.hour) * 100) + int(bTime.minute)
                        curTime = tempEvent['start']

                    curTime += time(curCommand[1], False)
                    if (curTime % 100 >= 60):
                        print("curTime (soon to be 'start') is: %s" % curTime)
                        curTime += 40
                        print("after modulo, curTime is: %s" % curTime)
                    comment = curCommand[len(curCommand) - 1].split('#')

                    tempEvent['length'] = time(comment[1], True)
                    print("Length is %d" % tempEvent['length']),
                    ##                    tempEvent['end'] = tempEvent['start']+time(comment[1])-1
                    self.events.append(tempEvent)
                    self.showEvents()
                    tempEvent = self.clearEvent()
                    i += 1
                # Otherwise this is a gap without recording length
                #   Since utilizing BEGIN time, this may never be reached
                else:
                    curTime += time(curCommand[1], False)
                    tempEvent = self.clearEvent()
                    print("ON Gap ending at %d, not recording" % curTime)
                    i += 1

            elif (curType == 'OFF'):
                tempEvent['start'] = curTime
                i += 1
            else:
                print("NON-command on this line ", curCommand)
                i += 1

    #
    #   Ask for and append a new event entry (start/end times)
    def addEvent(self, s, l):
        print("Adding an event ... "),
        # Create an empty new event and sorted events list
        newEvent = {'start': 0000,
                    'length': 0000}
        added = False
        sortedEv = []
        while True:
            try:
                newEvent['start'] = s
                newEvent['length'] = l

                assert (newEvent['start'] < 2400) or (
                newEvent['length'] < 2400), "Entered a start%d/length%d greater than 2400!" % (
                newEvent['start'], newEvent['start'])
                assert newEvent['length'] != 0, "Entered 0000 for length!"
                break

            except ValueError:
                print("Not a valid time! Quit?"),
                if (curses.wrapper(getConfirm)): return
            except AssertionError as strerror:
                print("%s Try again!" % strerror),

        # Create a NEW event list sorted by start time
        print("NEW event is .. at %d from %d" % (newEvent['start'], newEvent['length']))
        if (len(self.events) == 0):
            self.events.append(newEvent)
        elif (newEvent['start'] > self.events[len(self.events) - 1]['start']):
            # new event will be the last
            self.events.append(newEvent)
        else:
            for ev in self.events:
                if (ev['start'] < newEvent['start']):  # New event is after this one
                    print("Added Old ev at %d" % (ev['start']))
                    sortedEv.append(ev)
                else:  # New event is before this one
                    # time.sleep(3)
                    # BUT has already been added
                    if (added == True):
                        sortedEv.append(ev)
                        print("Added Old event at %d" % (ev['start']))
                    else:
                        sortedEv.append(newEvent)
                        sortedEv.append(ev)
                        added = True
                        print("Added New event and ev at %d" % (ev['start']))
            if (len(sortedEv) != len(self.events) + 1):
                print("Adding error")
                print("sortedEv len %d, events len %d" % (len(sortedEv), len(self.events)))

            print("sortedEv len %d, events len %d" % (len(sortedEv), len(self.events)))
            self.events = list(sortedEv)
            print("sortedEv len %d, events len %d" % (len(sortedEv), len(self.events)))

        print("New event added! There are %d events:" % len(self.events))
        self.showEvents()

    #
    #   Empty the schedule's event list
    def clearAllEvents(self):
        print("/n/nClearing events..."),
        newEvent = {'start': 0000,
                    'length': 0000}
        self.events.clear()
        print("Events cleared! There are %d events:" % len(self.events))

    #   Return a blank event item
    def clearEvent(self):
        blankEvent = {'start': 0000,
                      'length': 0000}
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
        os.chdir('/')
        cpCom1 = 'sudo cp -v ' + self.source + ' /home/wittyPi/schedules/HVScriptIMPORT.wpi'
        cpCom2 = 'sudo cp -v ' + self.source + ' /home/wittyPi/schedule.wpi'
        os.system(cpCom1)
        os.system(cpCom2)

        print("Schedule files copied ...")
        time.sleep(1)

        # Set wittyPi apparent time
        # rtc_to_system() to overwrite system time
        syncCom1 = "sudo /home/wittyPi/init.sh"
        ##        os.system(syncCom1)
        print("Setting wittyPi apparent time ...")
        print(subprocess.check_output(["bash", "-c",
                                       ". /home/wittyPi/utilities.sh; system_to_rtc"],
                                      universal_newlines=True))

        # Set wittyPi schedule with its runScript.sh
        print(subprocess.check_output(["sudo", "/home/wittyPi/runScript.sh"],
                                      universal_newlines=True))
        print("Ran wittyPi system_to_rtc utility and runScript.sh ...")

    def systemToRTC(self):
        # Set wittyPi RTC time
        print("Setting wittyPi RTC time ...")
        print(subprocess.check_output(["bash", "-c",
                                       ". /home/wittyPi/utilities.sh; system_to_rtc"],
                                      universal_newlines=True))

    def RTCToSystem(self):
        # Set system time
        print("Setting wittyPi RTC time ...")
        print(subprocess.check_output(["bash", "-c",
                                       ". /home/wittyPi/utilities.sh; rtc_to_system"],
                                      universal_newlines=True))




##  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def nav(screen):
    screen.addstr(8, 8, "Surfin >")
    start = 15000
    # 10000 tics ~= 6.5 seconds?
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
            screen.addstr(10, 1, "* nav error: %s" % inst)
            # if called during cooldown, exit loop so OLED can countdown
            tic -= 1
        else:
            screen.addstr(4, 1, "Got nav event %s" % event)
            tic = start
            if event == '0':
                return 0
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

            elif event == 'KEY_F1':  # 100+ button
                return 'F1'
            elif event == 'KEY_F2':  # 200+ button
                return 'F2'
            elif event == '0':
                return 0
            elif event == '1':
                return 1
            else:
                screen.addstr(5, 1, "TRY AGAIN (not %s) >" % event)

        screen.clear()
    screen.addstr(5, 1, "OUT\n\n")


# if called during cooldown, exit loop so OLED can countdown
def navDecay(screen):
    screen.addstr(8, 8, "Dyin >")
    screen.keypad(1)
    # halfdelay blocks for getch call for x tenths of a second
    screen.nodelay(1)
    while True:
        try:
            event = screen.getkey()
        except Exception as inst:
            screen.addstr(10, 1, "* nav error: %s" % inst)
            break
        ##            print("*** nav error: %s"%inst)
        ##            return 'e'
        ##            return 'decay'
        ##            action = False
        else:
            screen.addstr(4, 1, "Got nav event %s" % event)
            if event == '0':
                return 0
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

            elif event == 'KEY_F1':  # 100+ button
                return 'F1'
            elif event == 'KEY_F2':  # 200+ button
                return 'F2'
            elif event == '0':
                return 0
            elif event == '1':
                return 1
            else:
                screen.addstr(5, 1, "TRY AGAIN (not %s) >" % event)

        screen.clear()
    screen.addstr(5, 1, "OUT\n\n")


#   Get user confirmation
def getConfirm(screen):
    screen.addstr(3, 8, "Confirm by pressing ENTER >")
    screen.nodelay(0)
    screen.keypad(1)
    curses.echo()
    try:
        event = screen.getkey()
    except Exception as inst:
        screen.addstr(11, 1, "* conf error: %s" % inst)
    else:
        screen.addstr(5, 1, "Got confirm event %s" % event)
        if event == '\n':
            screen.addstr(5, 20, "CONFIRMED")
            return True
        else:
            return False


# Get user-input time string
def getTime(screen):
    screen.addstr(3, 8, "Enter a 2400 time, press ENTER >")
    screen.nodelay(0)
    curses.echo()
    try:
        time = screen.getstr()
    except Exception as inst:
        screen.addstr(11, 1, "*TIME error: %s" % inst)
    else:
        if (len(time) < 1):
            time = 0
            print("Blank time entered!")
        elif (len(time) > 4):
            time = time[-4:]
            print("Long entered!")
        return int(time)


def getDate(screen):
    screen.addstr(3, 8, "Enter YYYYMMDD, press ENTER >")
    screen.nodelay(0)
    curses.echo()
    try:
        date = screen.getstr()
    except Exception as inst:
        screen.addstr(11, 1, "*DATE error: %s" % inst)
    else:
        if (date == ''): time = 0
        if (len(date) > 8): time = time[-8:]
        return int(date)


class Display(object):
    def __init__(self, **k_parems):
        print('Display instance starting... at %s' % now())
        time.sleep(1)
        RST = 24
        DC = 23
        SPI_PORT = 0
        SPI_DEVICE = 0
        self.disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, dc=DC,
                                                    spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))
        self.width = self.disp.width
        self.height = self.disp.height
        self.font = ImageFont.truetype("GameCube.ttf", 7)
        print('..schedule..')
        if 'schedule' in k_parems:
            # If the assigned schedule is listed...
            self.schedule = k_parems['schedule']
        else:
            self.schedule = Schedule("Import", "/home/wittyPi/schedules/HVScriptIMPORT.wpi")
        # self.schedule.sync()
        print('...')
        self.mode = -1
        self.fresh = True
        self.manual = False

        self.start = 25
        # length of decay countdowm
        self.decay = self.start
        # initialize decay countdown


        print('....')
        self.disp.begin()
        self.image = Image.new('1', (self.width, self.height))

        print('..cam..')
        if 'cam' in k_parems and k_parems['cam'] == True:
            # If the assigned camera is listed...
            try:
                recorder = Recorder()
            except Exception as inst:
                # screen.addstr(11, 1,"*CAM error: %s"% inst)
                # NameError: name 'screen' is not found
                print("CAM error: %s!!" % inst)
                time.sleep(3)
                self.mode = 'ERR'
            else:
                self.cam = recorder
                print('...cam created..')
        else:
            self.recorder = []
            print('...blank cam created..')

        self.draw = ImageDraw.Draw(self.image)
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

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
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

    def welcome(self):
        # Load default font.
        font = ImageFont.truetype("electroharmonix.ttf", 12)
        self.draw.text((2, 2), 'Hello', font=self.font, fill=255)
        self.draw.text((2, 15), 'ViewHive v%s' % self.schedule.version,
                       font=self.font, fill=255)
        self.update()
        time.sleep(3)
        ## Call schedule sync function

    ##        self.schedule.sync()
    ## Don't call now, old system time will overwrite correct RTC
    ## Recording will not start

    def shutdown(self):
        print("*** Shutting down ***")
        self.mode = 'KILL'
        self.tabs()
        self.showRoom(self.mode, 0)
        self.update()

        self.cam.camera.close()

        self.tabs()
        self.showRoom(self.mode, 0)
        self.update()
        os.system("sudo gpio mode 7 out")
        # 'gpio mode 7 out' for wittypi intead of 'sudo shutdown -h now'

    def startRooms(self):
        ### Main interaction code

        recRes = 0.01
        ##        self.cam.start()
        self.eventsBar()
        self.update()
        while self.decay > 0 or self.cam.camera.recording == True:

            if (self.mode == 'TIME'):
                com = curses.wrapper(navDecay)

            else:
                com = curses.wrapper(nav)
            if (self.fresh == True):
                i = 0  # If this view is fresh, reset item index

            # Interpret navigation commands
            if (com == 'CH'):
                self.mode = 'ADD'
                self.fresh = True
                self.decay = self.start
            elif (com == 'CH-'):
                if (self.mode == 'VIEW'):
                    self.mode = 'TIME'
                elif (self.mode == 'ADD'):
                    self.mode = 'VIEW'
                elif (self.mode == 'DEL'):
                    self.mode = 'ADD'
                elif (self.mode == 'TIME'):
                    self.mode = 'DEL'
                self.fresh = True
                self.decay = self.start
            elif (com == 'CH+'):
                if (self.mode == 'VIEW'):
                    self.mode = 'ADD'
                elif (self.mode == 'ADD'):
                    self.mode = 'DEL'
                elif (self.mode == 'DEL'):
                    self.mode = 'TIME'
                elif (self.mode == 'TIME'):
                    self.mode = 'VIEW'
                self.fresh = True


            elif (com == 'ENT'):
                if (self.mode == 'TIME' or self.mode == 'ADD'): i = -1
                self.fresh = False

            elif (com == 'P'):
                if (self.mode == 'ADD'): i = -1
                if (self.mode == 'TIME'): i = -2
                self.decay = self.start
                self.fresh = False

            elif (com == 0 and self.mode == 'DEL'):
                self.fresh = False
                i = -1
            elif (com == 1 and self.mode == 'ADD'):
                self.fresh = False
                i = -1

            # Interpret Left and Right commands
            elif (com == 'R'):
                if (i == len(self.schedule.events) - 1):
                    pass
                else:
                    i += 1
                    self.fresh = False
            elif (com == 'L'):
                if (i == 0):
                    pass
                else:
                    i -= 1
                    self.fresh = False

            # Interpret a DECAY command due to idling
            elif (com == 'DECAY' or self.mode == 'TIME'):
                if (hasattr(self, 'cam') == False):
                    self.mode = 'ERR'
                    self.shutdown()
                else:
                    if (self.cam.camera.recording == True and self.decay <= 0):
                        # Recording but idle
                        i = -3
                    else:
                        self.mode = 'TIME'
                        self.decay -= recRes * 2
                        ### End of navigation code

            if (self.fresh == True):
                i = 0  # If this view is fresh, reset item index
            if hasattr(self, 'cam'):
                if self.cam.camera.recording == True:
                    self.cam.refresh()
            self.tabs()
            self.showRoom(self.mode, i)
            self.eventsBar()
            self.update()
        # End of while loop
        # Decay is complete and not recording, SHUTDOWN

        ## Call schedule sync function
        self.schedule.sync()
        self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
        self.draw.text((self.width / 2 - 30, self.height / 2), 'SYNCHED', font=self.font, fill=1)
        self.shutdown()

    def showRoom(self, mode, i):
        if (mode == 'VIEW'):
            self.roomView(i)
        elif (mode == 'ADD'):
            self.roomAdd(i)
        elif (mode == 'DEL'):
            self.roomDelete(i)
        elif (mode == 'TIME'):
            self.roomTime(i)
        else:
            self.roomMain()

    def roomMain(self):
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
        if (self.mode == 'KILL'):
            self.draw.text((5, self.height / 2), 'SHUTTING DOWN', font=self.font, fill=1)
        elif (self.mode == 'ERR'):
            self.draw.text((5, self.height / 2), 'CAMERA ERROR', font=self.font, fill=1)
        else:
            self.draw.text((1, self.height / 2), 'MAIN main', font=self.font, fill=1)

    def roomView(self, i):
        i = i
        if (len(self.schedule.events) == 0):
            curString = 'No events scheduled'
        else:

            cur = self.schedule.events[i]
            curString = '#%d - %d' % (i + 1, cur['start']) + ' for ' + '%d.' % cur['length']
            if (len(self.schedule.events) > 1 and i < len(self.schedule.events) - 1):
                self.draw.text((self.width - 10, self.height / 2), '...',
                               font=self.font, fill=1)
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
        self.draw.text((3, self.height / 2), '%s' % curString,
                       font=self.font, fill=1)

    ##        self.eventsBar()

    def roomDelete(self, i):
        i = i
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
        if i == -1:
            self.draw.text((2, self.height / 2), "Delete all events?",
                           font=self.font, fill=1)

            self.update()
            answer = curses.wrapper(getConfirm)

            self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
            if answer == True:
                ## Call schedule delete function
                self.schedule.clearAllEvents()
                self.draw.text((self.width / 2 - 30, self.height / 2), "DELETED!",
                               font=self.font, fill=1)
                self.update()
                time.sleep(2)
                ## Call schedule sync function
                self.schedule.sync()
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((self.width / 2 - 30, self.height / 2), 'SYNCHED', font=self.font, fill=1)
                self.fresh = True
            else:
                self.draw.text((self.width / 2 - 28, self.height / 2), "Canceled",
                               font=self.font, fill=1)
            self.update()
            time.sleep(1)
            self.fresh = True
        elif i == 0:
            self.draw.text((2, self.height / 2), "Press 0 >",
                           font=self.font, fill=1)
            self.fresh = True

    def roomTime(self, i):
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
        # i = i
        try:
            if (self.liveNow() == True):
                # If an event is scheduled for now...
                self.decay = self.start
                self.draw.rectangle((0, 0, self.width - 50, 10), outline=0, fill=0)
                if (self.cam.camera.recording == False):
                    self.cam.start()  # Start recording scheduled event
                else:  # Already started a scheduled event
                    self.draw.text((1, 1), "RECording..",
                                   font=self.font, fill=1)
            elif (self.liveNow() == False and self.cam.camera.recording == True):
                # If recording outside of schedule
                if (self.manual == True):  # Middle of a manual recording
                    pass
                else:  # End of a scheduled event
                    self.draw.rectangle((0, 0, self.width / 3, 5), outline=0, fill=0)
                    self.draw.text((1, 1), "SAVing..",
                                   font=self.font, fill=1)
                    self.update()
                    self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                    self.draw.text((2, self.height / 2), "USB 'VIEWHIVE' req.",
                                   font=self.font, fill=1)
                    self.cam.stop()
                    self.decay = self.start

            else:
                pass
        except AttributeError:
            self.draw.text((1, 1), "no CAMERA, ERR",
                           font=self.font, fill=1)
            self.update()

        if (i == -1):  # Setting system/RTC time
            self.draw.text((5, self.height / 2), "Set the time?",
                           font=self.font, fill=1)
            self.update()

            # Confirm
            answer = curses.wrapper(getConfirm)
            self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
            if answer == True:
                self.draw.text((self.width / 2 - 38, self.height / 2), 'SETTING TIME', font=self.font, fill=1)
                self.update()
                time.sleep(2)
                self.fresh = False

                # Get current date
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((3, self.height / 2), 'Give date YYYY >',
                               font=self.font, fill=1)
                self.update()
                y = curses.wrapper(getDate)
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((3, self.height / 2), 'Give date MM >',
                               font=self.font, fill=1)
                self.update()
                m = curses.wrapper(getDate)
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((3, self.height / 2), 'Give date DD >',
                               font=self.font, fill=1)
                self.update()
                d = curses.wrapper(getDate)

                # Get current time
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((3, self.height / 2), 'Give cur. time (2400) >',
                               font=self.font, fill=1)
                self.update()
                newTime = curses.wrapper(getTime)

                # Now confirm this entries
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((1, self.height / 2), "Set %r / %r / %r %d ?" % (m, d, y, newTime),
                               font=self.font, fill=1)
                self.update()

                conf = curses.wrapper(getConfirm)
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                if conf == True:
                    ## Set system/RTC time
                    timeCom = 'sudo date %r%r%r%r' % (
                    str(m).zfill(2), str(d).zfill(2), str(newTime).zfill(4), str(y).zfill(4))
                    print(timeCom)
                    os.system(timeCom)
                    self.schedule.systemToRTC()
                    self.draw.text((35, self.height / 2), 'RTC SET', font=self.font, fill=1)
                    self.update()
                    time.sleep(2)

                    # Clear image buffer by drawing a black filled box.
                    self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                    self.draw.text((1, self.height / 2), 'Time is now %r' % nowt(),
                                   font=self.font, fill=1)
                    self.update()
                    time.sleep(2)
                    self.fresh = True
                else:
                    self.draw.text((self.width / 2 - 28, self.height / 2), "Canceled SET",
                                   font=self.font, fill=1)
                    self.fresh = True
            else:
                self.draw.text((self.width / 2 - 28, self.height / 2), "Canceled CLOCK",
                               font=self.font, fill=1)

            self.fresh = True

        if (i == -2):  # Manually start/stop a recording
            if (self.cam.camera.recording == False):
                self.draw.text((2, self.height / 2), "Record NOW??",
                               font=self.font, fill=1)
            else:
                self.draw.text((2, self.height / 2), "STOP NOW??",
                               font=self.font, fill=1)
            self.update()
            answer = curses.wrapper(getConfirm)

            self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
            if answer == True and self.cam.camera.recording == False:
                self.cam.start()
                self.manual = True
                self.draw.text((2, self.height / 2), "Recording...",
                               font=self.font, fill=1)
                self.update()
                i = 0
            elif answer == True and self.cam.camera.recording == True:
                self.draw.text((2, self.height / 2), "Stopping...",
                               font=self.font, fill=1)
                self.update()
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((2, self.height / 2), "USB 'VIEWHIVE' req.",
                               font=self.font, fill=1)
                self.cam.stop()
                self.maual = False
                i = 0
            else:
                self.draw.text((self.width / 2 - 28, self.height / 2), "Canceled",
                               font=self.font, fill=1)
            self.update()
            time.sleep(2)
            self.fresh = True

        if (i == -3):  # Sleeping during a recording
            self.draw.text((self.width / 2 - 28, self.height / 2), "SLEEPING",
                           font=self.font, fill=1)
            self.update()
            self.fresh = True
        else:  # Show current time in tabs and decay coutdown
            if hasattr(self, 'cam'):
                if self.cam.camera.recording == True:
                    self.draw.text((self.width / 2 - 50, self.height / 2), 'Sleeping after REC',
                                   font=self.font, fill=1)
                else:
                    self.draw.text((self.width / 2 - 50, self.height / 2),
                                   'Shutdown in  %.2f' % round(float(self.decay), 3),
                                   font=self.font, fill=1)
            else:
                self.draw.text((self.width / 2 - 50, self.height / 2),
                               'Shutdown in  %.2f' % round(float(self.decay), 3),
                               font=self.font, fill=1)
            self.fresh = True

    def roomAdd(self, i):
        # Add an event

        i = i
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
        if i == -1:
            self.draw.text((2, self.height / 2), "Add an event?",
                           font=self.font, fill=1)
            self.update()

            answer = curses.wrapper(getConfirm)
            self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
            if answer == True:
                self.draw.text((self.width / 2 - 30, self.height / 2), 'ADDING', font=self.font, fill=1)
                self.update()
                time.sleep(2)
                self.fresh = False
                # Get start and length times for new event
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((1, self.height / 2), 'Enter start time 0000 >',
                               font=self.font, fill=1)

                self.update()
                start = curses.wrapper(getTime)  # Start time from 0000 to 24000
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((1, self.height / 2), 'Enter rec. length 0000 >',
                               font=self.font, fill=1)
                self.update()
                length = curses.wrapper(getTime)  # Length of event

                # Check for invalid entries
                if (length == 0):
                    self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                    self.draw.text((self.width / 2 - 38, self.height / 2), "entered LEN. of 0",
                                   font=self.font, fill=1)
                    self.update()
                    time.sleep(2)
                else:
                    # Now confirm these entries
                    self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                    self.draw.text((2, self.height / 2), "At %d  for  %d?" % (start, length),
                                   font=self.font, fill=1)
                    self.update()

                    conf = curses.wrapper(getConfirm)
                    self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                    if conf == True:
                        ## Call schedule add function
                        self.schedule.addEvent(start, length)
                        self.draw.text((1, self.height / 2), 'ADDED...', font=self.font, fill=1)
                        ## Call schedule sync function
                        self.schedule.sync()
                        self.draw.text((58, self.height / 2), 'SYNCHED', font=self.font, fill=1)
                        self.fresh = True
                    else:
                        self.draw.text((self.width / 2 - 38, self.height / 2), "Canceled SAVE",
                                       font=self.font, fill=1)
            else:
                self.draw.text((self.width / 2 - 28, self.height / 2), "Canceled ADD",
                               font=self.font, fill=1)

        elif i == 0:
            self.draw.text((2, self.height / 2), "Press 1 >",
                           font=self.font, fill=1)
            self.fresh = True

    def liveNow(self):
        # Function to check if an event is scheduled for right now
        for ev in self.schedule.events:
            start = code1440(str(ev['start']))
            length = code1440(str(ev['length']))
            now = code1440(str(nowti()))

            s = self.width * (start / 1440)
            e = (self.width * ((start + length) / 1440))
            if (now >= start and now < start + length):
                print('%r >= %r and <%r' % (now, start, start + length))
                return True
        else:
            return False

    def eventsBar(self):
        j = 1440  # 1440 minutes in a day
        # Clear bar buffer by drawing a black filled box.
        self.draw.rectangle((0, 28, self.width, self.height), outline=0, fill=0)

        while (j > 0):
            x = ((self.width) * (float(j) / float(1440)))
            if (j % 720 == 0):
                self.draw.line(((x, 27), (x, self.height)), fill=1)
            elif (j % 180 == 0):
                self.draw.line(((x, 29), (x, self.height)), fill=1)
            elif (j % 60 == 0):
                self.draw.line(((x, 31), (x, self.height)), fill=1)
            j -= 60
        ##        self.draw.line(((self.width/2,26) , (self.width/2,self.height)), fill=1)
        for ev in self.schedule.events:
            start = code1440(str(ev['start']))
            length = code1440(str(ev['length']))
            end = start + length

            s = (self.width * (float(start) / float(1440)))
            # g = float(720)/float(1440)
            e = (self.width * (float(end) / float(1440)))
            ##self.draw.line(((self.width/2,26) , (self.width/2,self.height)), fill=1)

            # print("%r,%r, %r ~ %r, %r"%(start,length,end, s,e))
            # Draw a triangle.
            padding = 2
            shape_w = 4
            bottom = self.height - padding
            top = bottom - shape_w / 3
            self.draw.polygon([(s - shape_w / 2, top), (s, bottom),
                               (s + shape_w / 2, top)], outline=255, fill=0)

            # self.draw.line(((s,27) , (s,self.height)), fill=1)
            # self.draw.chord((s,30, e,self.height), -180,0, outline=1, fill=0)
            # self.draw.line(((f, 20) , (f,32)), fill=1)

            # self.draw.line(((10,self.width), (20, self.height)), fill=1)

    def tabs(self):
        length = 40
        off = 6
        buf = 8
        h = 10
        # Clear tab buffer by drawing a black filled box.
        self.draw.rectangle((0, 0, self.width, h), outline=0, fill=0)
        if (self.mode == 'VIEW'):
            self.draw.polygon([(buf, 0), (buf + length, 0), (buf + length - off / 2, h), (buf + off / 2, h)],
                              outline=0, fill=1)
            self.draw.text((10 + off / 2, 0), 'VIEW', font=self.font, fill=0)

            self.draw.polygon([(buf + length, 0), (buf + (length * 2) - off, 0), (buf + (length * 2) + off / 2, h),
                               (buf + length - 5, h)],
                              outline=255, fill=0)
            self.draw.text((buf + length + 5, 0), 'ADD', font=self.font, fill=255)

            self.draw.polygon(
                [(buf + (length * 2 - off), 0), (buf + length * 3 - off, 0), (buf + length * 3 - off - off / 2, h),
                 (buf + length * 2 - off / 2, h)],
                outline=255, fill=0)
            self.draw.text((buf + length * 2 + 5, 0), 'DEL', font=self.font, fill=255)

        elif (self.mode == 'ADD'):
            self.draw.polygon([(buf, 0), (buf + length, 0), (buf + length - off / 2, h), (buf + off / 2, h)],
                              outline=1, fill=0)
            self.draw.text((10 + off / 2, 0), 'VIEW', font=self.font, fill=1)

            self.draw.polygon([(buf + length, 0), (buf + (length * 2) - off, 0), (buf + (length * 2) + off / 2, h),
                               (buf + length - off / 2, h)],
                              outline=0, fill=1)
            self.draw.text((buf + length + 5, 0), 'ADD', font=self.font, fill=0)

            self.draw.polygon(
                [(buf + (length * 2 - +off), 0), (buf + length * 3 - off, 0), (buf + length * 3 - off - off / 2, h),
                 (buf + length * 2 - off / 2, h)],
                outline=1, fill=0)
            if (self.fresh == False):
                self.draw.text((self.width - 37, 1), "%s" % nowt(), font=self.font, fill=1)
            else:
                self.draw.text((buf + length * 2 + 5, 0), 'DEL', font=self.font, fill=1)

        elif (self.mode == 'DEL'):
            self.draw.polygon([(buf, 0), (buf + length, 0), (buf + length - off / 2, h), (buf + off / 2, h)],
                              outline=1, fill=0)
            self.draw.text((10 + off / 2, 0), 'VIEW', font=self.font, fill=1)

            self.draw.polygon([(buf + length, 0), (buf + (length * 2) - off, 0), (buf + (length * 2) + off / 2, h),
                               (buf + length - off / 2, h)],
                              outline=1, fill=0)
            self.draw.text((buf + length + 5, 0), 'ADD', font=self.font, fill=1)

            self.draw.polygon(
                [(buf + (length * 2 - off), 0), (buf + length * 3 - off, 0), (buf + length * 3 - off - off / 2, h),
                 (buf + length * 2 - off / 2, h)],
                outline=0, fill=1)
            self.draw.text((buf + length * 2 + 5, 0), 'DEL', font=self.font, fill=0)

        elif (self.mode == 'TIME'):
            self.draw.polygon([(buf, 0), (self.width - buf, 0), (self.width - buf - off / 2, h), (buf + off / 2, h)],
                              outline=1, fill=0)
            self.draw.text((self.width - 105, 1), "%s" % nowdt(), font=self.font, fill=1)
        else:
            self.draw.polygon([(buf, 0), (self.width - buf, 0), (self.width - buf - off / 2, h), (buf + off / 2, h)],
                              outline=0, fill=1)
            self.draw.text((self.width / 2 - 25, 0), 'VIEWHIVE', font=self.font, fill=0)

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




    def startRooms(self):
        # Main interaction code

        recRes = 0.01
        # self.cam.start()
        self.eventsBar()
        self.update()
        while self.decay > 0 or self.cam.camera.recording == True:

            if self.mode == 'TIME':
                com = curses.wrapper(navDecay)

            else:
                com = curses.wrapper(nav)
            if self.fresh:
                i = 0  # If this view is fresh, reset item index

            # Interpret navigation commands
            if com == 'CH':
                self.mode = 'ADD'
                self.fresh = True
                self.decay = self.start
            elif com == 'CH-':
                if self.mode == 'VIEW':
                    self.mode = 'TIME'
                elif self.mode == 'ADD':
                    self.mode = 'VIEW'
                elif self.mode == 'DEL':
                    self.mode = 'ADD'
                elif self.mode == 'TIME':
                    self.mode = 'DEL'
                self.fresh = True
                self.decay = self.start
            elif com == 'CH+':
                if self.mode == 'VIEW':
                    self.mode = 'ADD'
                elif self.mode == 'ADD':
                    self.mode = 'DEL'
                elif self.mode == 'DEL':
                    self.mode = 'TIME'
                elif self.mode == 'TIME':
                    self.mode = 'VIEW'
                self.fresh = True

            elif com == 'ENT':
                if self.mode == 'TIME' or self.mode == 'ADD': i = -1
                self.fresh = False

            elif com == 'P':
                if self.mode == 'ADD': i = -1
                if self.mode == 'TIME': i = -2
                self.decay = self.start
                self.fresh = False

            elif com == 0 and self.mode == 'DEL':
                self.fresh = False
                i = -1
            elif com == 1 and self.mode == 'ADD':
                self.fresh = False
                i = -1

            # Interpret Left and Right commands
            elif com == 'R':
                if i == len(self.schedule.events) - 1:
                    pass
                else:
                    i += 1
                    self.fresh = False
            elif com == 'L':
                if i == 0:
                    pass
                else:
                    i -= 1
                    self.fresh = False

            # Interpret a DECAY command due to idling
            elif com == 'DECAY' or self.mode == 'TIME':
                if not hasattr(self, 'cam'):
                    self.mode = 'ERR'
                    self.shutdown()
                else:
                    if self.cam.camera.recording == True and self.decay <= 0:
                        # Recording but idle
                        i = -3
                    else:
                        self.mode = 'TIME'
                        self.decay -= recRes * 2
                        # End of navigation code

            if self.fresh:
                i = 0  # If this view is fresh, reset item index
            if hasattr(self, 'cam'):
                if self.cam.camera.recording:
                    self.cam.refresh()
            self.tabs()
            self.showRoom(self.mode, i)
            self.eventsBar()
            self.update()
        # End of while loop
        # Decay is complete and not recording, SHUTDOWN

        # Call schedule sync function
        self.schedule.sync()
        self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
        self.draw.text((self.width / 2 - 30, self.height / 2), 'SYNCHED', font=self.font, fill=1)
        self.shutdown()

    def showRoom(self, mode, i):
        if mode == 'VIEW':
            self.roomView(i)
        elif mode == 'ADD':
            self.roomAdd(i)
        elif mode == 'DEL':
            self.roomDelete(i)
        elif mode == 'TIME':
            self.roomTime(i)
        else:
            self.roomMain()

    def roomMain(self):
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
        if self.mode == 'KILL':
            self.draw.text((5, self.height / 2), 'SHUTTING DOWN', font=self.font, fill=1)
        elif self.mode == 'ERR':
            self.draw.text((5, self.height / 2), 'CAMERA ERROR', font=self.font, fill=1)
        else:
            self.draw.text((1, self.height / 2), 'MAIN main', font=self.font, fill=1)

    def roomView(self, i):
        i = i
        if len(self.schedule.events) == 0:
            curString = 'No events scheduled'
        else:

            cur = self.schedule.events[i]
            curString = '#%d - %d' % (i + 1, cur['start']) + ' for ' + '%d.' % cur['length']
            if len(self.schedule.events) > 1 and i < len(self.schedule.events) - 1:
                self.draw.text((self.width - 10, self.height / 2), '...',
                               font=self.font, fill=1)
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
        self.draw.text((3, self.height / 2), '%s' % curString,
                       font=self.font, fill=1)

        self.eventsBar()

    def roomDelete(self, i):
        i = i
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
        if i == -1:
            self.draw.text((2, self.height / 2), "Delete all events?",
                           font=self.font, fill=1)

            self.update()
            answer = curses.wrapper(getConfirm)

            self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
            if answer:
                # Call schedule delete function
                self.schedule.clearAllEvents()
                self.draw.text((self.width / 2 - 30, self.height / 2), "DELETED!",
                               font=self.font, fill=1)
                self.update()
                time.sleep(2)
                # Call schedule sync function
                self.schedule.sync()
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((self.width / 2 - 30, self.height / 2), 'SYNCHED', font=self.font, fill=1)
                self.fresh = True
            else:
                self.draw.text((self.width / 2 - 28, self.height / 2), "Canceled",
                               font=self.font, fill=1)
            self.update()
            time.sleep(1)
            self.fresh = True
        elif i == 0:
            self.draw.text((2, self.height / 2), "Press 0 >",
                           font=self.font, fill=1)
            self.fresh = True

    def roomTime(self, i):
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
        # i = i
        try:
            if self.liveNow():
                # If an event is scheduled for now...
                self.decay = self.start
                self.draw.rectangle((0, 0, self.width - 50, 10), outline=0, fill=0)
                if not self.cam.camera.recording:
                    self.cam.start()  # Start recording scheduled event
                else:  # Already started a scheduled event
                    self.draw.text((1, 1), "RECording..",
                                   font=self.font, fill=1)
            elif self.liveNow() is False and self.cam.camera.recording is True:
                # If recording outside of schedule
                if self.manual:  # Middle of a manual recording
                    pass
                else:  # End of a scheduled event
                    self.draw.rectangle((0, 0, self.width / 3, 5), outline=0, fill=0)
                    self.draw.text((1, 1), "SAVing..",
                                   font=self.font, fill=1)
                    self.update()
                    self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                    self.draw.text((2, self.height / 2), "USB 'VIEWHIVE' req.",
                                   font=self.font, fill=1)
                    self.cam.stop()
                    self.decay = self.start

            else:
                pass
        except AttributeError:
            self.draw.text((1, 1), "no CAMERA, ERR",
                           font=self.font, fill=1)
            self.update()

        if i == -1:  # Setting system/RTC time
            self.draw.text((5, self.height / 2), "Set the time?",
                           font=self.font, fill=1)
            self.update()

            # Confirm
            answer = curses.wrapper(getConfirm)
            self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
            if answer:
                self.draw.text((self.width / 2 - 38, self.height / 2), 'SETTING TIME', font=self.font, fill=1)
                self.update()
                time.sleep(2)
                self.fresh = False

                # Get current date
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((3, self.height / 2), 'Give date YYYY >',
                               font=self.font, fill=1)
                self.update()
                y = curses.wrapper(getDate)
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((3, self.height / 2), 'Give date MM >',
                               font=self.font, fill=1)
                self.update()
                m = curses.wrapper(getDate)
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((3, self.height / 2), 'Give date DD >',
                               font=self.font, fill=1)
                self.update()
                d = curses.wrapper(getDate)

                # Get current time
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((3, self.height / 2), 'Give cur. time (2400) >',
                               font=self.font, fill=1)
                self.update()
                newTime = curses.wrapper(getTime)

                # Now confirm this entries
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((1, self.height / 2), "Set %r / %r / %r %d ?" % (m, d, y, newTime),
                               font=self.font, fill=1)
                self.update()

                conf = curses.wrapper(getConfirm)
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                if conf == True:
                    ## Set system/RTC time
                    timeCom = 'sudo date %r%r%r%r' % (
                        str(m).zfill(2), str(d).zfill(2), str(newTime).zfill(4), str(y).zfill(4))
                    print(timeCom)
                    os.system(timeCom)
                    self.schedule.systemToRTC()
                    self.draw.text((35, self.height / 2), 'RTC SET', font=self.font, fill=1)
                    self.update()
                    time.sleep(2)

                    # Clear image buffer by drawing a black filled box.
                    self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                    self.draw.text((1, self.height / 2), 'Time is now %r' % nowt(),
                                   font=self.font, fill=1)
                    self.update()
                    time.sleep(2)
                    self.fresh = True
                else:
                    self.draw.text((self.width / 2 - 28, self.height / 2), "Canceled SET",
                                   font=self.font, fill=1)
                    self.fresh = True
            else:
                self.draw.text((self.width / 2 - 28, self.height / 2), "Canceled CLOCK",
                               font=self.font, fill=1)

            self.fresh = True

        if i == -2:  # Manually start/stop a recording
            if not self.cam.camera.recording:
                self.draw.text((2, self.height / 2), "Record NOW??",
                               font=self.font, fill=1)
            else:
                self.draw.text((2, self.height / 2), "STOP NOW??",
                               font=self.font, fill=1)
            self.update()
            answer = curses.wrapper(getConfirm)

            self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
            if answer == True and self.cam.camera.recording == False:
                self.cam.start()
                self.manual = True
                self.draw.text((2, self.height / 2), "Recording...",
                               font=self.font, fill=1)
                self.update()
                i = 0
            elif answer == True and self.cam.camera.recording == True:
                self.draw.text((2, self.height / 2), "Stopping...",
                               font=self.font, fill=1)
                self.update()
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((2, self.height / 2), "USB 'VIEWHIVE' req.",
                               font=self.font, fill=1)
                self.cam.stop()
                self.manual = False
                i = 0
            else:
                self.draw.text((self.width / 2 - 28, self.height / 2), "Canceled",
                               font=self.font, fill=1)
            self.update()
            time.sleep(2)
            self.fresh = True

        if i == -3:  # Sleeping during a recording
            self.draw.text((self.width / 2 - 28, self.height / 2), "SLEEPING",
                           font=self.font, fill=1)
            self.update()
            self.fresh = True
        else:  # Show current time in tabs and decay coutdown
            if hasattr(self, 'cam'):
                if self.cam.camera.recording:
                    self.draw.text((self.width / 2 - 50, self.height / 2), 'Sleeping after REC',
                                   font=self.font, fill=1)
                else:
                    self.draw.text((self.width / 2 - 50, self.height / 2),
                                   'Shutdown in  %.2f' % round(float(self.decay), 3),
                                   font=self.font, fill=1)
            else:
                self.draw.text((self.width / 2 - 50, self.height / 2),
                               'Shutdown in  %.2f' % round(float(self.decay), 3),
                               font=self.font, fill=1)
            self.fresh = True

    def roomAdd(self, i):
        # Add an event

        i = i
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
        if i == -1:
            self.draw.text((2, self.height / 2), "Add an event?",
                           font=self.font, fill=1)
            self.update()

            answer = curses.wrapper(getConfirm)
            self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
            if answer:
                self.draw.text((self.width / 2 - 30, self.height / 2), 'ADDING', font=self.font, fill=1)
                self.update()
                time.sleep(2)
                self.fresh = False
                # Get start and length times for new event
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((1, self.height / 2), 'Enter start time 0000 >',
                               font=self.font, fill=1)

                self.update()
                start = curses.wrapper(getTime)  # Start time from 0000 to 24000
                self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                self.draw.text((1, self.height / 2), 'Enter rec. length 0000 >',
                               font=self.font, fill=1)
                self.update()
                length = curses.wrapper(getTime)  # Length of event

                # Check for invalid entries
                if length == 0:
                    self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                    self.draw.text((self.width / 2 - 38, self.height / 2), "entered LEN. of 0",
                                   font=self.font, fill=1)
                    self.update()
                    time.sleep(2)
                else:
                    # Now confirm these entries
                    self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                    self.draw.text((2, self.height / 2), "At %d  for  %d?" % (start, length),
                                   font=self.font, fill=1)
                    self.update()

                    conf = curses.wrapper(getConfirm)
                    self.draw.rectangle((0, 12, self.width, 24), outline=0, fill=0)
                    if conf:
                        # Call schedule add function
                        self.schedule.addEvent(start, length)
                        self.draw.text((1, self.height / 2), 'ADDED...', font=self.font, fill=1)
                        # Call schedule sync function
                        self.schedule.sync()
                        self.draw.text((58, self.height / 2), 'SYNCHED', font=self.font, fill=1)
                        self.fresh = True
                    else:
                        self.draw.text((self.width / 2 - 38, self.height / 2), "Canceled SAVE",
                                       font=self.font, fill=1)
            else:
                self.draw.text((self.width / 2 - 28, self.height / 2), "Canceled ADD",
                               font=self.font, fill=1)

        elif i == 0:
            self.draw.text((2, self.height / 2), "Press 1 >",
                           font=self.font, fill=1)
            self.fresh = True
