import unittest
from viewhive.ViewHiveUtil import *


class ViewHiveTests(unittest.TestCase):

    def test_code1440(self):
        # Test converting to 1440-time
        # e.g. 1:30 to 90 minutes
        print('code1440...')
        self.assertEqual(code1440(130), 90)
        print('code1440 ran')
        time.sleep(2)

    def test_code2400(self):
        # Test converting to 2400-time
        # e.g. 190 to 3:10
        print('code2400...')
        self.assertEqual(code2400(130), 210)
        self.assertEqual(code2400(190), 310)
        self.assertEqual(code2400(1400), 2320)
        self.assertEqual(code2400(70), 110)
        self.assertEqual(code2400(50), 50)
        print('code2400 ran')
        time.sleep(2)

    def test_spotlight(self):
        # Cycle IR spotlights on GPIO pins
        # and check pin value
        print('\nspotlight')
        print('GPIO 21 is at {}'.format(spotlight_check(21)))
        time.sleep(2)
        spotlight_on(21)
        self.assertTrue(spotlight_check(21))
        print('GPIO 21 is at {}'.format(spotlight_check(21)))
        time.sleep(2)
        spotlight_off(21)
        self.assertTrue(not spotlight_check(21))
        print('GPIO 21 is at {}'.format(spotlight_check(21)))

    def test_nav(self):
        # Start a Navigation object until Shutdown is selected
        # and check for specific menu actions
        print('test_nav...')
        print("Current Working Directory: {}".format(os.getcwd()))
        nav = Navigation()
        # Should be the 3rd item's title
        self.assertIs(nav.menuMain._menu[2][2], "Add")
        nav.testRun()
        print('test_nav ran!')

    def test_menuTime(self):
        # Create a menuTime object and confirm structure
        print("test_menuTime...")
        mt = menuTime(TimeMenu)
        nav = Navigation(menu=mt)
        # Should be the 4th item's title
        self.assertIs(nav.menuMain._menu[3][2], "2")
        print('test_menuTime ran!')

    def test_schedule(self):
        # Test schedule import and creation
        print("Script file path: {}".format(os.path.dirname(os.path.realpath("ScriptUTIL.wpi"))))
        print("Current Working Directory: {}".format(os.getcwd()))
        testSchedule = Schedule("test", "viewhive/tests/ScriptUTIL.wpi")
        self.assertEqual(testSchedule.events[0]['start'], 722)
        # testSchedule.showEvents()
        self.assertEqual(testSchedule.name, "test")
        self.assertEqual(testSchedule.file.name, "viewhive/tests/ScriptUTIL.wpi")
        testSchedule.sync()
        os.chdir('/')
        print("Current Working Directory: {}".format(os.getcwd()))
        self.assertTrue(os.path.isfile("/home/pi/wittyPi/schedule.wpi"))

    def test_recording(self):
        print("test_recording...")
        viewhiveRec = Recorder()
        self.assertTrue(viewhiveRec.camera.framerate == 49)
        viewhiveRec.start()
        time.sleep(10)
        viewhiveRec.stop()

    def test_screenCal(self):
        # Run a calibration image on the screen
        print("test_screenCal...")
        print("Current Working Directory: {}".format(os.getcwd()))
        display = Display(cam=True)
        print(display.nav.menuMain.struct[1])
        # self.assertTrue(display.nav.menuMain.struct, "Day")
        display.calibrate()

    def test_menuTimeChoice(self):
        # Choose a time with the display
        print("test_menuTimeChoice...")
        display = Display(cam=True)
        print(display.nav.menuMain.struct[1])
        # self.assertTrue(display.nav.menuMain.struct, "Day")
        display.calibrate()
        self.assertIs(display.nav.menuMain._menu[2][2], "Add")
        print(display.chooseTime())

    def test_menuFULL(self):
        # Test full system
        print("test_menuFULL...")
        print("Current Working Directory: {}".format(os.getcwd()))
        display = Display(cam=True)
        # print(display.nav.menuMain.struct)
        # self.assertTrue(display.nav.menuMain.struct[5][2], "Config")
        display.calibrate()
        display.runNavigation()


if __name__ == '__main__':
    unittest.main()
