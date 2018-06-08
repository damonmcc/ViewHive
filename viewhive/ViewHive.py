from viewhive.ViewHiveUtil import *

# Copy custom schedule to wittyPi folders and synch wittyPi
# bees = Schedule("Bees", "ScriptUTIL.wpi")
# bees.showEvents()

# mmal: mmal_vc_port_enable: failed to enable port vc.null_sink:in:0(OPQV): ENOSPC
# mmal: mmal_port_enable: failed to enable connected port (vc.null_sink:in:0(OPQV))0xd32660 (ENOSPC)
# #mmal: mmal_connection_enable: output port couldn't be enabled


print("ViewHive initializing...")
time.sleep(2)

# Test full system
print("Current Working Directory: {}".format(os.getcwd()))
display = Display(cam=True)
# print(display.nav.menuMain.struct)
# self.assertTrue(display.nav.menuMain.struct[5][2], "Config")
display.calibrate()
display.runNavigation()

# print('After startRooms, ViewHive is done')

