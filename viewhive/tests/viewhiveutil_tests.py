import unittest
from viewhive.ViewHiveUtilOLD import *
import viewhive.WittyPi


class TestWittyPiMethods(unittest.TestCase):
    def test_code1440(self):
        self.assertEqual(code1440(130), 90)

    def test_code2400(self):
        self.assertEqual(code2400(130), 210)

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()


def test_schedule():
    bees = viewhive.WittyPi.Schedule("Bees", "ScriptUTIL.wpi")
    # assertEqual(bees.name, "Bees")
    # assert_equal(bees.file.name, "ScriptUTIL.wpi")
    
def test_schedule_read():
    old = viewhive.WittyPi.Schedule("Old", "ScriptUTIL.wpi")
    # assert_equal(old.events[0]['start'], 200)
    old.showEvents()

def test_display():
    display = Display()
    display.welcome()

def test_events():
    bees = viewhive.WittyPi.Schedule("Bees", "ScriptUTIL.wpi")
    
    display = Display(schedule = bees)
    display.eventsBar()
    display.update()
    viewhive.WittyPi.time.sleep(0.3)

def test_tabs():
    bees = viewhive.WittyPi.Schedule("Bees", "ScriptUTIL.wpi")
    
    display = Display(schedule = bees)
    display.eventsBar()
    display.mode = 'VIEW'
    display.tabs()
    display.update()
    viewhive.WittyPi.time.sleep(0.3)
    
    display.clear()
    display.mode = 'ADD'
    display.tabs()
    display.update()
    viewhive.WittyPi.time.sleep(0.3)

    display.clear()
    display.mode = 'DEL'
    display.tabs()
    display.update()
    viewhive.WittyPi.time.sleep(0.3)

def test_rooms():
    bees = viewhive.WittyPi.Schedule("Bees", "ScriptUTIL.wpi")

    display = Display(schedule = bees)
    display.mode = 'BLAH'   # enter a random mode
    display.tabs()
    display.roomMain()      # show main room
    display.update()
    viewhive.WittyPi.time.sleep(1)
    
    display.mode = 'VIEW'
    display.clear()
    display.tabs()
    display.eventsBar()
    display.update()
    viewhive.WittyPi.time.sleep(2)

    display.clear()
    display.mode = 'ADD'
    display.tabs()
    display.update()
    viewhive.WittyPi.time.sleep(1)

    display.clear()
    display.mode = 'DEL'
    display.tabs()
    display.update()
    viewhive.WittyPi.time.sleep(1)
    
    display.clear()
    display.mode = 'TIME'
    display.tabs()
    display.update()
    viewhive.WittyPi.time.sleep(1)
    display.clear()
    display.mode = 'MEH'
    display.tabs()
    display.update()
    viewhive.WittyPi.time.sleep(2)

def test_UI():
    bees = viewhive.WittyPi.Schedule("Bees", "ScriptUTIL.wpi")
    display = Display(schedule = bees, cam = True   )
    display.mode = 'VIEW'
    display.clear()
    display.tabs()
    display.eventsBar()
    display.update()
    viewhive.WittyPi.time.sleep(2)
    display.startRooms()


def test_recording():
    bees = viewhive.WittyPi.Schedule("Bees", "ScriptUTIL.wpi")
    display = Display(schedule = bees, cam = True   )
    display.mode = 'VIEW'
    display.clear()
    display.tabs()
    display.eventsBar()
    display.update()
    viewhive.WittyPi.time.sleep(2)
    
    display.cam.start()
    while(display.cam.timeElaps < 10):
        display.cam.refresh()
    display.cam.stop()
    
    
##def test_map():
##    start = Room("Start", "You can go west and down a hole.")
##    west = Room("Trees", "There are trees here, you can go east.")
##    down = Room("Dungeon", "It's dark down here, you can go up")
##
##    start.add_paths({'west': west, 'down': down})
##    west.add_paths({'east': start})
##    down.add_paths({'up': start})
##
##    assert_equal(start.go('west'), west)
##    assert_equal(start.go('west').go('east'), start)
##    assert_equal(start.go('down').go('up'), start)


def setup():
    print("SETUP!")

def teardown():
    print("TEAR DOWN!")

def test_basic():
    print("I RAN!")
