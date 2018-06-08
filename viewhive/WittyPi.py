import os
from datetime import datetime as dt
# from pythonwifi.iwlibs import Wireless
import time
import errno
import subprocess
import socket
from viewhive.Menu2Button import *

# Absolute path of wittyPi source code
wittyPi_Dir = '/home/pi/wittyPi/'


def now() -> str:
    # Return current time and date as a string
    return dt.now().strftime("%Y-%m-%d_%H.%M.%S")


def nowd() -> str:
    # Return current date as a string
    return dt.now().strftime("%Y-%m-%d")


def nowt():
    # Return current time as a string
    return dt.now().strftime("%H:%M")


def nowti():
    # Return current time as an int
    return int(dt.now().strftime("%H%M"))


def nowdts():
    # Return current date and time with seconds for display
    return dt.now().strftime("%d/%m/%Y, %H:%M:%S")


def nowdtsShort():
    # Return current date and time with seconds for display
    return dt.now().strftime("%d/%m/%y,  %H:%M:%S")


def code1440(time: int) -> int:
    # Convert a 2400 time to 1440 time
    time_int = time
    time_string = str(time)
    if len(time_string) == 4:  # time has 4 digits
        t_raw = (int(time_string[0]) * 600) + (int(time_string[1]) * 60) + (int(time_string[2]) * 10) + int(
            time_string[3])
    elif len(time_string) == 3:  # time has 3 digits
        t_raw = (int(time_string[0]) * 60) + (int(time_string[1]) * 10) + int(time_string[2])
    elif len(time_string) == 2:  # time has 2 digits
        t_raw = (int(time_string[0]) * 10) + int(time_string[1])
    else:  # time has only 1 digit
        t_raw = int(time_string[0])
    return t_raw


def code2400(time: int) -> int:
    # Convert a 1440 time to 2400
    time_int = time
    time_string = str(time)
    if len(time_string) >= 2:  # time has at least 3 digits
        m = time_int % 60  # minutes will be the remainder after removing hours
        h = (time_int - m) / 60  # without minutes, time only consists of hours
        t_raw = (h * 100) + m  # shifting hours 2 digits and adding minutes
        # print('TRaw = %r'% (tRaw))
    else:
        t_raw = int(time_string[0])

    return t_raw


def spotlight_on(gpio):
    irpi = pigpio.pi()
    gpioA = gpio
    irpi.set_mode(gpioA, pigpio.OUTPUT)
    irpi.write(gpioA, 1)
    irpi.stop()


def spotlight_off(gpio):
    irpi = pigpio.pi()
    gpioA = gpio
    irpi.set_mode(gpioA, pigpio.OUTPUT)
    irpi.write(gpioA, 0)
    irpi.stop()


def spotlight_check(gpio):
    irpi = pigpio.pi()
    gpioA = gpio
    irpi.set_mode(gpioA, pigpio.OUTPUT)
    level = irpi.read(gpioA)
    irpi.stop()
    return level


def waitforUSB(drivename):
    print("Looking for USB named %s..." % drivename)
    path = drivename
    attempts = 0
    while attempts < 10:
        if not os.path.exists(path):
            print("Waiting for %s USB at %s..." % (drivename, path))
            time.sleep(3)
        attempts += 1
    print("%s detected at %s !" % (drivename, path))
    # print("USB contains:")
    # p = subprocess.Popen("ls", shell=True,
    #                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    #                      cwd=path)
    # p_status = p.wait()
    # for line in iter(p.stdout.readline, b''):
    #     print(line),
    return path


def silentremove(filename):
    try:
        os.remove(filename)
        print("*** Deleted: ", filename)
    except OSError as e:
        if e.errno != errno.ENOENT:  # no such file or directory
            raise  # re-raise exception if a different error occured


def show_time():
    # Return current time as a string
    return dt.now().strftime("%H:%M:%S")


def sync_time():
    # Sync system and RTC times with WittyPi script
    # If RTC is good, writes to system
    # If RTC is old OR internet detected, writes to RTC
    print("Syncing RTC/system times ...")
    print("Curent Working Directory: {}".format(os.getcwd()))
    # time.sleep(2)
    oldDir = os.getcwd()
    os.chdir(wittyPi_Dir)
    print(subprocess.check_output(["bash", "-c",
                                   ". /home/pi/wittyPi/syncTime.sh"],
                                  universal_newlines=True))
    os.chdir(oldDir)


def set_system_time(MMDD, time, year):
    # Set system/RTC time
    # sudo date nnddhhmmyyyy
    # e.g.sudo date 120622432007.55 for December 6, 2007, 22:43:55
    timeCom = 'sudo date %r%r%r' % (
        str(MMDD).zfill(4), str(time).zfill(4), str(year).zfill(4))
    print(timeCom)
    os.system(timeCom)
    systemToRTC()


def systemToRTC():
    # Set wittyPi RTC time
    print("Setting wittyPi RTC time ...")
    print(subprocess.check_output(["bash", "-c",
                                   ". /home/pi/wittyPi/utilities.sh; system_to_rtc"],
                                  universal_newlines=True))


def RTCToSystem():
    # Set system time
    print("Setting wittyPi RTC time ...")
    print(subprocess.check_output(["bash", "-c",
                                   ". /homepi/wittyPi/utilities.sh; rtc_to_system"],
                                  universal_newlines=True))


def show_wifi():
    # wifi = Wireless('wlan0')
    # return wifi.getEssid()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(("8.8.8.8", 80))
    wifi = socket.gethostname()
    sock.close()
    return wifi


def wifi_down():
    # Turn off wifi
    print('Turning WIFI off...')
    os.system("sudo ifdown wlan0")
    print('WIFI OFF')


def wifi_up():
    # Turn on wifi
    print('Turning WIFI on...')
    os.system("sudo ifup wlan0")
    print('WIFI ON')


def show_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except:
        return 'no IP addr!'


class Schedule(object):
    def __init__(self, name, source):
        print("Schedule init...")
        self.name = name
        self.source = source  # Source file
        try:
            self.file = open(source)
        except:
            print("No {}, using default")
        self.content = self.file.read()  # Intermediary data for read/write
        self.file.close()
        self.events = []  # List of schedule events
        self.version = 3.0
        print("Schedule V {} created from {}:".format(self.version, self.source))
        self.WpiToEvents()
        print("Schedule init complete.")

    #   Display Schedule source file data
    def showSource(self):
        self.file = open(self.source)
        print("\nSource " + self.source + " content:", )
        print(self.file.read())
        self.file.close()

    #   Display current Schedule content
    def showContent(self):
        print("\nSchedule's current content:")
        print(self.content)

    #   Display list of user-defined events
    def showEvents(self):
        print("All events:")
        for event in self.events:
            start = event['start']
            end = code2400(code1440(event['start']) + code1440(event['length']))
            print("From %04d to %04d" % (start, end))
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
# Perhaps turn on 30 minutes before sunrise and sunset everyday
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
            if time >= 100:  # Has an hour component
                if time >= 1000:  # more than 10 hours
                    if 'state' in k_parems and k_parems['state'] == 'ON':  # For an ON command
                        if timeS[2] != '0' or timeS[3] != '0':  # there are minutes
                            h = 'H%s%s' % (timeS[0], timeS[1])
                            m = '%s%s' % (timeS[2], timeS[3])
                            m = 'M%s' % (int(m) - 1)  # subtract 1 minute for OFF state
                        else:  # menuMain goes from 00 to 59
                            h = '%s%s' % (timeS[0], timeS[1])
                            h = 'H%d' % (int(h) - 1)
                            m = 'M59'
                        code = h + ' ' + m
                    else:
                        if 'begin' in k_parems and k_parems['begin'] == 'ON':  # beginning of the day
                            h = '%s%s' % (timeS[0], timeS[1])
                            m = '%s%s' % (timeS[2], timeS[3])
                            code = h + ':' + m
                        else:
                            h = 'H%s%s' % (timeS[0], timeS[1])
                            m = 'M%s%s' % (timeS[2], timeS[3])
                            code = h + ' ' + m

                else:  # less than 10 hours, more than 1 hour
                    if 'state' in k_parems and k_parems['state'] == 'ON':  # For an ON command
                        if timeS[1] != '0' or timeS[2] != '0':  # there are minutes
                            h = 'H%s' % timeS[0]
                            m = '%s%s' % (timeS[1], timeS[2])
                            m = 'M%s' % (int(m) - 1)  # subtract 1 minute for OFF state
                        else:
                            h = 'H%d' % (int(timeS[0]) - 1)
                            m = 'M59'
                        code = h + ' ' + m
                    else:
                        if 'begin' in k_parems and k_parems['begin'] == 'ON':  # begining of the day
                            h = '0%s' % timeS[0]
                            m = '%s%s' % (timeS[1], timeS[2])
                            code = h + ':' + m
                        else:
                            h = 'H%s' % timeS[0]
                            m = 'M%s%s' % (timeS[1], timeS[2])
                            code = h + ' ' + m

            else:  # Only has a minute component
                if 'state' in k_parems and k_parems['state'] == 'ON':  # For an ON command
                    code = 'M%s' % (time - 1)  # subtract 1 minute for OFF state
                else:
                    if 'begin' in k_parems and k_parems['begin'] == 'ON':  # begining of the day
                        code = '00:%s' % time
                    else:
                        code = 'M%s' % time
            return code

        if len(self.events) == 0:  # No events
            wpiCommands.append('BEGIN 2017-6-02 00:00:00')
            wpiCommands.append('END	2025-07-31 23:59:59')
            wpiCommands.append('ON H23 M59')
            wpiCommands.append('OFF M1')
            #  Combine all command strings into contents
            self.content = '\n'.join(wpiCommands)
            self.content = header + self.content

        else:
            for event in self.events:  # For each event in the list...
                print("Event %d: %04d to %04d" % (i, event['start'], (event['start'] + event['length'])))

                if len(self.events) > 1 and i == 0:  # First event
                    print("First event ..."),
                    if event['start'] > 0:  # If starting after midnight, add morning buffer
                        print("Adding morning buffer ..."),
                        startRAW = event['start']
                        mornBuff = startRAW
                        start = code(startRAW, begin='ON')
                        wpiCommands.append('BEGIN ' + nowd() + ' ' + start + ':00')
                        wpiCommands.append('END	2025-07-31 23:59:59')
                        # wpiCommands.append('ON\t%s\tWAIT'% code(event['start'],state="ON"))
                        # wpiCommands.append('OFF\tM1')
                        curTime = mornBuff
                    else:
                        wpiCommands.append('BEGIN 2016-11-19 00:00:00')
                        wpiCommands.append('END	2025-07-31 23:59:59')

                    gap = self.events[i + 1]['start'] - curTime
                    if gap % 100 >= 60:
                        print("gap is: %s" % gap)
                        gap -= 40
                        print("after modulo, gap is: %s" % gap)
                    wpiCommands.append('ON\t%s\tWAIT\t#%s' % (code(gap, state="ON"), code(event['length'])))
                    wpiCommands.append('OFF\tM1')
                    curTime = self.events[i + 1]['start']

                elif i == len(self.events) - 1:  # Last or only event
                    print("Last (or only?) event ..."),
                    if i == 0:  # Only event
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
                        if last % 100 >= 60:
                            print("last was: %s" % last)
                            last -= 40  # for the minutes?
                            print("after modulo, last is: %s" % last)
                        wpiCommands.append('ON\t%s\tWAIT\t#%s' % (code(last, state="ON"), code(event['length'])))
                        wpiCommands.append('OFF\tM1')
                        print(curTime, " + ", last, " should be 2400 + ", mornBuff, "!")
                else:  # All other events
                    print("Average event ..."),
                    gapA = self.events[i + 1]['start'] - curTime
                    if gapA % 100 >= 60 or gapA + (self.events[i]['start'] % 100) >= 60:
                        # (eg. 1350 start to 1405 gives gap of 55 instead of 15
                        print("gap is over 60 or crosses an hour mark")
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

    # Convert Witty Pi schedule text to an events list
    def WpiToEvents(self):
        wpiLines = self.content.split('\n')
        tempEvent = self.clearEvent()
        i = 0
        curLength = 0

        # converts the wpi time codes to 0000 formatted time int
        def time(code, event):
            code0000 = 0000
            if ' ' not in code:  # if the command has 1 number
                if code[0] == 'H':
                    hours = int(code[1:len(code)]) * 100
                    code0000 += hours
                if code[0] == 'M':
                    if event:
                        mins = int(code[1:len(code)])
                    else:
                        mins = int(code[1:len(code)]) + 1
                        if mins > 59: mins = 100
                    code0000 += mins
            elif ' ' in curCommand[1]:  # Hour and minute present
                splitCode = code.split(' ')
                hours = int(splitCode[0][1:len(splitCode[0])]) * 100
                if event:
                    mins = int(splitCode[1][1:len(splitCode[1])])
                else:
                    mins = int(splitCode[1][1:len(splitCode[1])]) + 1
                    if mins > 59: mins = 100
                code0000 += hours
                code0000 += mins
            return code0000

        #  While reading header
        while len(wpiLines[i]) < 1 or wpiLines[i][0] == '#':
            print(i, " ", wpiLines[i])
            i += 1
        print(i, " ", wpiLines[i])  # BEGIN
        bSplit = wpiLines[i].split(' ')
        bTime = dt.strptime(bSplit[len(bSplit) - 1], "%H:%M:%S")

        if bTime.hour or bTime.minute != 0:
            print("Beginning has a non-zero time %r:%r!!!" % (bTime.hour, bTime.minute))

        i += 1
        print(i, " ", wpiLines[i])  # END
        i += 1
        curTime = 0

        # While reading WPI command lines
        while i < len(wpiLines):
            curCommand = wpiLines[i].split('\t')
            print(i, " ", curCommand),
            curType = curCommand[0]
            # print("%s command Length: %d"% (curType, curLength))
            if curType == 'ON':
                #   If there's a recording length comment
                if '#' in curCommand[len(curCommand) - 1]:
                    if curTime == 0:  # First event...
                        # Override blank/0000 start time
                        tempEvent['start'] = (int(bTime.hour) * 100) + int(bTime.minute)
                        curTime = tempEvent['start']

                    curTime += time(curCommand[1], False)
                    if curTime % 100 >= 60:
                        print("curTime (soon to be 'start') is: %s" % curTime)
                        curTime += 40
                        print("after modulo, curTime is: %s" % curTime)
                    comment = curCommand[len(curCommand) - 1].split('#')

                    tempEvent['length'] = time(comment[1], True)
                    print("Length is %d" % tempEvent['length']),
                    # tempEvent['end'] = tempEvent['start']+time(comment[1])-1
                    self.events.append(tempEvent)
                    self.showEvents()
                    tempEvent = self.clearEvent()
                    i += 1
                # Otherwise this is a gap without recording length
                # Since utilizing BEGIN time, this may never be reached
                else:
                    curTime += time(curCommand[1], False)
                    tempEvent = self.clearEvent()
                    print("ON Gap ending at %d, not recording" % curTime)
                    i += 1

            elif curType == 'OFF':
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
                newEvent['start'] = int(s)
                newEvent['length'] = int(l)
                # If length given is 60 minutes, change to 100 for 1 hour
                if newEvent['length'] == 60: newEvent['length'] = 100
                assert (newEvent['start'] < 2400) or (
                    newEvent['length'] < 2400), "Entered a start%d/length%d greater than 2400!" % (
                    newEvent['start'], newEvent['start'])
                assert newEvent['length'] != 0, "Entered 0000 for length!"
                break

            except ValueError:
                print("Not a valid time! Quit?"),
                if self.confirmed():
                    return
            except AssertionError as strerror:
                print("%s Try again!" % strerror),
                break

        # Create a NEW event list sorted by start time
        print("NEW event is .. at %d from %d" % (newEvent['start'], newEvent['length']))
        if len(self.events) == 0:
            self.events.append(newEvent)
        elif newEvent['start'] > self.events[len(self.events) - 1]['start']:
            # new event will be the last
            self.events.append(newEvent)
        else:
            for ev in self.events:
                if ev['start'] < newEvent['start']:  # New event is after this one
                    print("Added Old ev at %d" % (ev['start']))
                    sortedEv.append(ev)
                else:  # New event is before this one
                    # time.sleep(3)
                    # BUT has already been added
                    if added:
                        sortedEv.append(ev)
                        print("Added Old event at %d" % (ev['start']))
                    else:
                        sortedEv.append(newEvent)
                        sortedEv.append(ev)
                        added = True
                        print("Added New event and ev at %d" % (ev['start']))
            if len(sortedEv) != len(self.events) + 1:
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
        # write events in wpi format
        self.EventsToWpi()
        self.file = open(self.source, 'w')
        self.file.write(self.content)
        print("Schedule source written ...")
        self.file.close()
        workingDir = os.getcwd()
        print("Curent Working Directory: {}".format(workingDir))
        os.chdir('/')

        # Copy local schedule file to wittyPi directories
        # cpCom1 = 'sudo cp -v ' + self.source + ' /home/pi/wittyPi/schedules/VHScriptIMPORT.wpi'
        cpCom2 = 'sudo cp -v ' + self.source + ' /home/pi/wittyPi/schedule.wpi'
        # os.system(cpCom1)
        os.system(cpCom2)
        print("Schedule files copied ...")

        # Set wittyPi apparent time
        # rtc_to_system() to overwrite system time
        # syncCom1 = "sudo /home/pi/wittyPi/init.sh"
        # os.system(syncCom1)
        # print("Setting wittyPi apparent time ...")
        # os.system('bash -c . /home/pi/wittyPi/utilities.sh; system_to_rtc')

        systemToRTC()
        # Set wittyPi schedule with its runScript.sh
        # os.system('sudo /home/pi/wittyPi/utilities.sh system_to_rtc')
        os.system('sudo /home/pi/wittyPi/runScript.sh')
        # print(subprocess.check_output(["sudo", "/home/wittyPi/runScript.sh"],
        #                               universal_newlines=True))
        print("Ran system_to_rtc and runScript.sh ...")

    def confirmed(self):
        pass
