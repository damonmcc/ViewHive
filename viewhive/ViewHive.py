from ViewHiveUtil import *


# Copy custom schedule to wittyPi folders and synch wittyPi
##bees = Schedule("Bees", "ScriptUTIL.wpi")
##bees.showEvents()

# Try launching a display
try:
    display = Display(cam = True)
    print('Display started')
    display.welcome()
    print('Welcome started')

    display.update()
    print('Display set!!!')
except:
    print('Display FAILED')
    print('Unexpected error: %s'%sys.exc_info()[0])

##bees.showEvents()
##display.mode = 'VIEW'

display.clear()
display.update()
time.sleep(2)

display.startRooms()

print('After startRooms, this')

