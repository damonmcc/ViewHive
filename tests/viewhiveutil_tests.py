from nose.tools import *
from viewhive.ViewHiveUtil import *


def test_schedule():
    bees = Schedule("Bees", "ScriptUTIL.wpi")
    assert_equal(bees.name, "Bees")
    assert_equal(bees.file.name, "ScriptUTIL.wpi")
    
def test_schedule_read():
    old = Schedule("Old", "ScriptUTIL.wpi")
    assert_equal(old.events[0]['start'], 200)
    old.showEvents()

def test_display():
    display = Display()
    display.welcome()

def test_events():
    bees = Schedule("Bees", "ScriptUTIL.wpi")
    
    display = Display(schedule = bees)
    display.eventsBar()
    display.update()
    time.sleep(0.3)

def test_tabs():
    bees = Schedule("Bees", "ScriptUTIL.wpi")
    
    display = Display(schedule = bees)
    display.eventsBar()
    display.mode = 'VIEW'
    display.tabs()
    display.update()
    time.sleep(0.3)
    
    display.clear()
    display.mode = 'ADD'
    display.tabs()
    display.update()
    time.sleep(0.3)

    display.clear()
    display.mode = 'DEL'
    display.tabs()
    display.update()
    time.sleep(0.3)

def test_rooms():
    bees = Schedule("Bees", "ScriptUTIL.wpi")

    display = Display(schedule = bees)
    display.mode = 'BLAH'   # enter a random mode
    display.tabs()
    display.roomMain()      # show main room
    display.update()
    time.sleep(1)
    
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
    time.sleep(1)

    display.clear()
    display.mode = 'DEL'
    display.tabs()
    display.update()
    time.sleep(1)
    
    display.clear()
    display.mode = 'TIME'
    display.tabs()
    display.update()
    time.sleep(1)
    display.clear()
    display.mode = 'MEH'
    display.tabs()
    display.update()
    time.sleep(2)

def test_UI():
    bees = Schedule("Bees", "ScriptUTIL.wpi")
    display = Display(schedule = bees, cam = True   )
    display.mode = 'VIEW'
    display.clear()
    display.tabs()
    display.eventsBar()
    display.update()
    time.sleep(2)
    display.startRooms()


def test_recording():
    bees = Schedule("Bees", "ScriptUTIL.wpi")
    display = Display(schedule = bees, cam = True   )
    display.mode = 'VIEW'
    display.clear()
    display.tabs()
    display.eventsBar()
    display.update()
    time.sleep(2)
    
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
