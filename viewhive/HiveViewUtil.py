from sortedcontainers import SortedDict

class Schedule(object):

    def __init__(self, source):
        self.source = source            # Source file
        self.file = open(source)
        self.content = self.file.read() # Intermediary data for read/write
        self.file.close()
        self.events = []                # List of schedule events
        
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
            print("From %04d to %04d" % (event['start'], event['end']))
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
            print("Event %d: %04d to %04d" % (i, event['start'], event['end']))
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

        ##  While reading commands
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
                    tempEvent['end'] = tempEvent['start']+tempEvent['length']
                    self.events.append(tempEvent)
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
                  'length' : 0000,
                  'end' : 0000}
        while True:
            try:
                newEvent['start'] = int(input("Enter start time (0000)> "))
                newEvent['length'] = int(input("Enter rec. length (0000)> "))
                newEvent['end'] = newEvent['start'] + newEvent['length']
                assert (newEvent['start'] < 2400) or (newEvent['length'] < 2400), "Entered a start%d/length%d greater than 2400!"% (newEvent['start'], newEvent['start'])
                assert newEvent['length'] != 0, "Entered 0000 for length!"
                break
            except ValueError:
                print("Not a valid time! Quit?"),
                if(self.confirmed()): return
            except AssertionError as strerror:
                print("%s Try again!"% strerror),
        
        
        # Confirm before saving
        print("End time: %04d\nSave this event?" % newEvent['end']),
        if(self.confirmed()):  # Pressed ENTER
            self.events.append(newEvent)
            self.events = SortedDict(self.events)
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
                 'length' : 0000,
                 'end' : 0000}
        return blankEvent

    #   Ask user to confirm a task and return result
    def confirmed(self):
        if(input("Confirm with ENTER? >")==''):
            return True
        else:
            print("CANCELED")
            return False
        
    # def sync():
        # sync object with schedule file
        # truncate
        # write header comments
        # write BEGIN and END
        # wrie events in wpi format
        self.file = open(source, '-a')
        self.file.write(self.content)
        print("File appended")
        self.file.close()
        


schedule_cur = Schedule("HVScriptUTIL.wpi")
schedule_cur.showContent()
schedule_cur.WpiToEvents()
schedule_cur.EventsToWpi()

while True:
    schedule_cur.addEvent()
    schedule_cur.EventsToWpi()
    schedule_cur.clearAllEvents()
    schedule_cur.addEvent()
    schedule_cur.showContent()

