from sortedcontainers import SortedDict
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import time
import threading
import curses
import Adafruit_SSD1306
import Adafruit_GPIO.SPI as SPI 

#def recordNow():
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
    # Convert a 1400 time to 2400
    pass


screen = curses.initscr()
curses.echo()
curses.curs_set(0)
screen.keypad(1)
def room(screen):
    screen.addstr("Thisssss\n\n")
    while True:
        event = screen.getch()
        if event == ord("q"): break
    screen.addstr(5, 1,"OUT\n\n")
    

class Schedule(object):

    def __init__(self, name, source):
        self.name = name
        self.source = source            # Source file
        self.file = open(source)
        self.content = self.file.read() # Intermediary data for read/write
        self.file.close()
        self.events = []                # List of schedule events
        self.ED = SortedDict(self.events)
        
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
        print("\nSorted:")
        for event in self.ED:
            print("From %s to %s" % (event[0], (event[0]+event[1])))
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
        wpiCommands = ["#"]
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
            
        #   Combine all command stings into contents
        self.content = '\n'.join(wpiCommands)
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
    def addEvent(self):
        print("Adding an event ... "),
        # Create an empty new event
        newEvent = {'start' : 0000,
                  'length' : 0000}
        while True:
            try:
                newEvent['start'] = int(input("Enter start time (0000)> "))
                newEvent['length'] = int(input("Enter rec. length (0000)> "))
##                newEvent['end'] = newEvent['start'] + newEvent['length']
                assert (newEvent['start'] < 2400) or (newEvent['length'] < 2400), "Entered a start%d/length%d greater than 2400!"% (newEvent['start'], newEvent['start'])
                assert newEvent['length'] != 0, "Entered 0000 for length!"
                break
            except ValueError:
                print("Not a valid time! Quit?"),
                if(self.confirmed()): return
            except AssertionError as strerror:
                print("%s Try again!"% strerror),
        
        
        # Confirm before saving
        print("End time: %04d\nSave this event?" % (newEvent['start']+newEvent['length'])),
        if(self.confirmed()):  # Pressed ENTER
            self.events.append(newEvent)
            self.ED = SortedDict(self.events)
            print("New event added! There are %d events:" % len(self.events))
            self.showEvents()
        else:   # Pressed anything else
            print("Canceled save with %s aka %r button!" % (save, save))
            self.showEvents()

    #
    #   Empty the schedule's event list
    def clearAllEvents(self):
        print("Clearing events..."),
        if(self.confirmed()):
            self.events = []
            print("Events cleared! There are %d events:" % len(self.events))
    
    #   Clear an event object's time attributes to 0000
    def clearEvent(self):
        blankEvent = {'start' : 0000,
                 'length' : 0000}
        return blankEvent


   

    #   Ask user to confirm a task and return result
    def confirmed(self):
        if(input("Confirm with ENTER? >")==''):
            return True
        else:
            print("CANCELED")
            return False

    def sync():
        # sync object with schedule file
        # truncate
        # write header comments
        # write BEGIN and END
        # wrie events in wpi format
        self.file = open(source, '-a')
        self.file.write(self.content)
        print("File appended")
        self.file.close()





class Display(object):
    def __init__(self):
        RST = 24
        DC = 23
        SPI_PORT = 0
        SPI_DEVICE = 0
        self.disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))
        self.width = self.disp.width
        self.height = self.disp.height
        self.font = ImageFont.truetype("GameCube.ttf", 7)       
        
        self.mode = -1
        self.disp.begin()
        self.image = Image.new('1', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)


    #   Get user-input time string
    def getTime(self):
        event = 28
        curses.wrapper(room)
        curses.wrapper(room)

        return str(event)


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

    def eventsBar(self, events):
        i=0     #   1440 minutes in a day
        while(i<=1440):
            x = (128*(i/1400))
            if(i%720 == 0):
                self.draw.line(((x,26) , (x,self.height)), fill=1)
            elif(i%180 == 0):
                self.draw.line(((x,28), (x,self.height)), fill=1)            
            elif(i%60 == 0):
                self.draw.line(((x,30) , (x,self.height)), fill=1)
            else:
                self.draw.line(((x,31), (x,self.height)), fill=1)
            i+=30
        for ev in events:
            start = code1440(str(ev['start']))
            length = code1440(str(ev['length']))
            
            s = 128*(start/1440)
            e = (128*((start+length)/1440))
            self.draw.chord((s,28 , e,self.height), -180,0, outline=1, fill=1)
##            self.draw.line(((s, 20) , (s,32)), fill=1)
            

    def tabs(self):
        length = 40
        off = 6
        buf = 8
        h = 10
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
            t = self.getTime()
            self.draw.text((self.width/2-25, 0), "%s" % t,  font=self.font, fill=1)

        else:
            self.draw.polygon([(buf,0), (self.width-buf,0), (self.width-buf-off/2,h) , (buf+off/2,h)],
                              outline=0, fill=1)
            self.draw.text((self.width/2-25, 0), 'VIEWHIVE',  font=self.font, fill=0)


    def roomMain(self):
        #
        self.draw.text((1,self.height/2), 'MAIN main', font=self.font, fill=1)
    
    def roomView(self, events):
        # Generate scrolling event time display
        # Check if this is a recording time
        # Decay if idle
        velocity = -0.5
        startpos = self.width-10
        pos = startpos
        i = 0
        evString = ''
        font = self.font = ImageFont.truetype("GameCube.ttf", 7)
        for ev in events:
            evString = evString+'%d'%(ev['start'])+'for'+'%d/ '%ev['length']
        maxwidth, unused = self.draw.textsize(evString, font=font)
##        AC = self.AwaitCommand()
##        AC.start()
        
        while (self.mode == 0): # Until view mode changes
            # Clear image buffer by drawing a black filled box.
            self.draw.rectangle((0,12,self.width,24), outline=0, fill=0)
            # Enumerate characters and draw them offset vertically based on a sine wave.
            x = pos
            for i, c in enumerate(evString):
                # Stop drawing if off the right side of screen.
                if x > self.width:
                    break
                # Calculate width but skip drawing if off the left side of screen.
                if x < -10:
                    char_width, char_height = self.draw.textsize(c, font=font)
                    x += char_width
                    continue
                # Calculate offset from screen size.
                y = self.height/2
                # Draw text.
                self.draw.text((x, y), c, font=self.font, fill=1)
                # Increment x position based on chacacter width.
                char_width, char_height = self.draw.textsize(c, font=font)
                x += char_width
            # Draw the image buffer.
            self.disp.image(self.image)
            self.disp.display()
            # Move position for next frame.
            pos += velocity
            # Start over if text has scrolled completely off left side of screen.
            if pos < -maxwidth:
                pos = startpos
            # Pause briefly before drawing next frame.
            time.sleep(0.1)

            
    

    def roomAdd(self, schedule):
        #
        self.draw.text((1, self.height/2), 'ADDING', font=self.font, fill=1)


    
                


##        while event != ord('q'):
##        scr = curses.initscr()    
##        scr.clear()
##        scr.border(0)
##        curses.echo()
##        #curses.curs_set(0)
##        scr.keypad(1)
##            
##        scr.addstr(5, 1, "Ask")
##        scr.addstr(5, 1, "AAsk")
##        event = scr.getkey()
##
##        scr.clear()
##        scr.addstr(5, 1, "Quit")
##        event = 0
##        while event != ord('4'):
##            scr.addstr("Enter current time >")
##            scr.addstr("!")
##            scr.refresh()
##            event = scr.getch()
##            
##            if event == ord('q'):
##                curses.endwin()
##                scr.addstr(5, 1, "Quit")
##                break
##            elif event == curses.KEY_DOWN:
##                break
##            elif event == ord('5'):
##                scr.clear()
##                scr.addstr(4, 1, "Pressed 5")                
##                curses.endwin()
##                
##            scr.addstr("<")
##            scr.refresh()
##        curses.nocbreak()
##        scr.keypad(False)
##        curses.echo()
##        curses.endwin()

  
##
##    def roomDel():
##        #

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

