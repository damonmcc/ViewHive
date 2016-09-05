from ViewHiveUtil import *
# Copy custom schedule to wittyPi folders and synch wittyPi
##bees = Schedule("Bees", "ScriptUTIL.wpi")
##bees.showEvents()

# Try launching a display
# *** Stopped using try statement to avoid Recorder init error:
##mmal: mmal_vc_port_enable: failed to enable port vc.null_sink:in:0(OPQV): ENOSPC
##mmal: mmal_port_enable: failed to enable connected port (vc.null_sink:in:0(OPQV))0xd32660 (ENOSPC)
##mmal: mmal_connection_enable: output port couldn't be enabled
##try:
##    display = Display(cam = True)
##    print('Display started')
##    display.welcome()
##    print('Welcome started')
##
##    display.update()
##    print('Display set!!!')
##except:
##    print('Display FAILED')
##    print('Unexpected error: %s'%sys.exc_info()[0])
##bees.showEvents()
##display.mode = 'VIEW'


display = Display(cam = True)
print('Display started')
display.welcome()
##print('Welcome started')

display.update()
print('Display set!!!')
display.clear()
display.update()

display.startRooms()

print('After startRooms, this')

