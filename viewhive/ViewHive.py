from ViewHiveUtil import *


# First initiate camera object
recorder = Recorder()

# Copy custom schedule to wittyPi folders and synch wittyPi
bees = Schedule("Bees", "ScriptUTIL.wpi")
bees.sync()
bees.showEvents()

# Try launching a display
try:
    display = Display(bees)
    print('Display started')
    display.welcome()
    print('Welcome started')

    display.clear()
    display.tabs()
    display.eventsBar()
    display.update()
    print('Display set!!!')
except:
    print('Display FAILED')
    print('Unexpected error: %s'%sys.exc_info()[0])


##display.mode = 'VIEW'
display.mode = 'VIEW'

display.clear()
display.tabs()
display.eventsBar()
display.update()
time.sleep(2)

display.clear()
display.mode = 'ADD'
display.tabs()
display.update()

display.startRooms()

##recorder.record()
print('After recording started, this')

