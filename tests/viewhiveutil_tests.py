from nose.tools import *
from viewhive.ViewHiveUtil import *


def test_schedule():
    bees = Schedule("Bees", "HVScriptUTIL.wpi")
    assert_equal(bees.name, "Bees")
    assert_equal(bees.file.name, "HVScriptUTIL.wpi")
    assert_equal(bees.events, [])
    
def test_schedule_read():
    old = Schedule("Old", "HVScriptUTIL.wpi")
    old.WpiToEvents()
    assert_equal(old.events[0]['start'], 200)
    old.showEvents()

def test_display():
    display = Display()
    display.welcome()

def test_events():
    bees = Schedule("Bees", "HVScriptUTIL.wpi")
    bees.WpiToEvents()
    display = Display()
    display.eventsBar(bees.events)
    display.update()
    time.sleep(1)

def test_tabs():
    display = Display()
    bees = Schedule("Bees", "HVScriptUTIL.wpi")
    bees.WpiToEvents()
    display.eventsBar(bees.events)
    display.mode = 0
    display.tabs()
    display.update()
    time.sleep(0.5)
    
    display.clear()
    display.mode = 1
    display.tabs()
    display.update()
    time.sleep(0.5)

    display.clear()
    display.mode = 2
    display.tabs()
    display.update()
    time.sleep(1)

def test_rooms():
    display = Display()
    display.mode = 6
    display.tabs()
    display.roomMain()
    display.update()
    time.sleep(2)
    
    bees = Schedule("Bees", "HVScriptUTIL.wpi")
    bees.WpiToEvents()
    display.clear()
    display.mode = 0
    display.tabs()
    display.eventsBar(bees.events)
    display.roomView(bees.events)
    display.update()
    time.sleep(2)

    display.clear()
    display.mode = 1
    display.tabs()
    display.roomAdd(bees)
    display.update()
    
    


##
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