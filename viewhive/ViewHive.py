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
    display.eventsBar()
    display.tabs()
    display.update()
    print('Display set!!!')
except:
    print('Display FAILED')
    print('Unexpected error: %s'%sys.exc_info()[0])



display.mode = 'VIEW'
display.clear()
display.tabs()
display.eventsBar()
display.update()


r = Process(target=recorder.record(), args=())
r.start()
print('After recording started, this')

r.join()

