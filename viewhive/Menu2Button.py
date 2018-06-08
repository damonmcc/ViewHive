#!/usr/bin/python
#
# ViewHive menu systems: menu, menuTime, menuView
#
import pigpio
import logging
LOG_FORMAT = "%(Levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename="/home/pi/pywork/ViewHive/vh.log",
                    level=logging.DEBUG,
                    format=LOG_FORMAT)
logger = logging.getLogger()
import time
from viewhive.rotary_encoder import *

ViewHiveMenu = [
    [0, "Welcome", 1],
    [1, "View", 200],
    [1, "Add", 300],
    [1, "Clear", 400],
    [1, "Videos", 700],
    [1, "Record", 500],
    [1, "Config", 600],
    [1, "shutdown", 100],

    # View menus
    [200, "Day", "exec_day_view"], # TODO Say no schedule if empty

    # Event Add menus
    [300, "Confirm add?", 301],
    [301, "Adding", "exec_add_conf"],

    # Event Clear menus
    [400, "Confirm CLR?", 401],
    [401, "Clearing", "exec_del_events"],

    # Videos menus
    [700, "Copy to USB", 710],
    [700, "View saved", 720],
    [700, "Delete", 730],
    [710, "Copying->", "exec_copy"],
    [720, "Saved:", "exec_storage"],
    [730, "Confirm DEL?", 731],
    [731, "Deleting", "exec_del_storage"],

    # Record menus
    [500, "Start Now?", 510],
    [500, "Stop?", 511],

    [510, "Recording..", "exec_rec_now"],
    [511, "Saving..", "exec_stop_now"],

    # Config menus TODO Review options
    [600, "Time", 610],
    [600, "WIFI", 620],
    [600, "IP", 630],
    [600, "Cam", 640],
    #   Time
    [610, "Show", "exec_time_show"],
    [610, "Set", 611],
    [611, "Confirm Time Sst?", 612],
    [612, "Setting!", "exec_time_set"],
    #   WIFI
    [620, "Show", 621],
    [620, "OFF", 622],
    [620, "ON", 624],
    [621, "Wifi:", "exec_wifi_show"],
    [622, "WIFI OFF?", 623],
    [623, "wifi down ..", "exec_wifi_down"],
    [624, "WIFI ON?", 625],
    [625, "wifi up ..", "exec_wifi_up"],
    #   IP
    [630, "IP :", "exec_ip_show"],
    # Cam
    [640, "Preview", "exec_cam_prev"],

    # Shutdown menus
    [100, "SHUTDOWN?", 110],
    [100, "Soft STOP?", 120],
    [110, "shutdown", "shutdown"],
    [120, "soft stop", "softstop"]
]

TimeMenu = [
    [0, "null", 1],
    [1, "0", "0"],
    [1, "1", "1"],
    [1, "2", "2"],
    [1, "3", "3"],
    [1, "4", "4"],
    [1, "5", "5"],
    [1, "6", "6"],
    [1, "7", "7"],
    [1, "8", "8"],
    [1, "9", "9"]
]

# Menu Access
# self._menu[pos][1]


class menu:
    """
    Menu System typically for 2 line LCD and 2 button navigation.
    structure is list of menu items with the following format :
    [reference to parent entry identifier,
    menu entry display title,
    positive integer identifier if entry goes to submenu OR
    string with action to be returned when entry is selected]
    """

    def __init__(self, structure, ExitLabel="EXIT"):

        # Initialize internal variables
        self._menu = []
        i = 0
        r = {0: 0}

        # Copy menu adding indexes
        for item in structure:
            if isinstance(item[2], int): r[item[2]] = i
            self._menu.append([i, r[item[0]], item[1], item[2]])
            i += 1
        self.key = 1
        self.level = 1

        # Build internal dictionary representing menu structure
        self.struct = {}
        for item in self._menu:
            # if item[0] != 0:
            if item[1] not in self.struct: self.struct[item[1]] = []
            self.struct[item[1]].append(item[0])

        # Add EXIT entry for each level
        for key in self.struct:
            index = len(self._menu)
            self._menu.append([index, key, ExitLabel, -1])
            self.struct[key].append(index)
        # Add EXIT entry for each level
        # TODO prevent exit from top menu
        # print("struct:")
        # for key in self.struct:
        #     index = len(self._menu)
        #     print(self.struct[key])
        #     if self._menu[key][1] == 0:
        #         print("!!!SKIPING EXIT FOR!!!"+self._menu[key][2])
        #         continue    # No EXIT for first and Welcome levels
        #     self._menu.append([index, key, ExitLabel, -1])
        #     self.struct[key].append(index)
        #     print(self.struct[key])
        # Start at config
        # print(self._menu)
        self.key = 7

    def display(self, pos=None):
        """
        Displays the current menu entry as :
        1st line : parent entry
        2nd line : current selected item
        """
        if pos is None: pos = self.key
        self.key = pos
        parent = self._menu[pos][1]
        print(str(self.level) + ":" + self._menu[parent][2])
        print(self._menu[pos][2])

    def displayCurrent(self, pos=None):
        """
        Returns the current selected item string
        """
        if pos is None: pos = self.key
        self.key = pos
        # The string menuMain.key[2] is the current selection title
        return self._menu[pos][2]

    def action(self, pos=None):
        """
        Returns action associated with current selected menu item
        None if selected item refers to submenu
        """
        if pos is None: pos = self.key
        self.key = pos
        if isinstance(self._menu[pos][3], str): return self._menu[pos][3]
        return None

    def next(self, pos=None):
        """
        Advances selection to next menu item in same level.
        Rotates to first item when at end of menu level.
        """
        if pos is None: pos = self.key
        self.key = pos
        level = self.struct[self._menu[pos][1]]
        i = level.index(pos)
        i = i + 1
        if i >= len(level): i = 0
        self.key = level[i]

    def back(self, pos=None):
        """
        Decrements selection to prev. menu item in same level.
        Rotates to last item when at beginning of menu level.
        """
        if pos is None: pos = self.key
        self.key = pos
        level = self.struct[self._menu[pos][1]]
        i = level.index(pos)
        i = i - 1
        if i < 0: i = len(level) - 1
        self.key = level[i]

    def select(self, pos=None):
        """
        Advances to sub menu or parent menu then returns False, OR
        Returns True if selected menu has to be actioned.
        Returns -1 if selected item is EXIT from first level, i.e. quit the menu
        """
        if pos is None: pos = self.key
        self.key = pos
        print("SelectPos is " + str(pos))
        if isinstance(self._menu[pos][3], str): return True
        if self._menu[pos][3] > 0:
            print("key was" + str(self._menu[pos][0])+", is "+str(self.struct[self._menu[pos][0]][0]))
            self.key = self.struct[self._menu[pos][0]][0]
            self.level += 1
            return False
        if self._menu[pos][3] == -1:
            self.key = self._menu[pos][1]
            self.level -= 1
            if self.key == 0: return -1
            return False

    def up(self, pos=None):
        """
        Goes up one level and returns True
        Returns False if already on top/first level
        Can typically be used after actioning a selection to return to previous menu item
        """
        if pos is None: pos = self.key
        self.key = pos
        if self.level == 1: return False
        self.key = self._menu[pos][1]
        self.level -= 1
        return True


class menuTime:
    """
    Menu System for constructing a time string from 0000 - 2359
    by choosing each digit, one at a time.
    Structure is a list of menu items with the following format:
    [digit of current choice,
    numerical value string,
    1 to go to submenu with digits OR numerical value string]
    """
    def __init__(self, structure, ExitLabel="BACK"):

        # Initialize internal variables
        self._menu = []
        i = 0
        r = {0: 0}
        self.time = ""

        for item in structure:
            if isinstance(item[2], int): r[item[2]] = i
            self._menu.append([i, r[item[0]], item[1], item[2]])
            i += 1
        self.key = 1
        self.level = 1

        # Build internal dictionary representing menu structure
        self.struct = {}
        for item in self._menu:
            if item[0] != 0:
                if item[1] not in self.struct: self.struct[item[1]] = []
                self.struct[item[1]].append(item[0])

        # Add BACK entry to delete entries and exit
        for key in self.struct:
            index = len(self._menu)
            self._menu.append([index, key, ExitLabel, -2])
            self.struct[key].append(index)

        # Add Done entry to choose a short time
        for key in self.struct:
            index = len(self._menu)
            self._menu.append([index, key, "Done", -1])
            self.struct[key].append(index)

    def display(self, pos=None):
        """
        Displays the current menu entry as :
        1st line : parent entry
        2nd line : current selected item
        """
        if pos is None: pos = self.key
        self.key = pos
        parent = self._menu[pos][1]
        print(str(self.level) + ":" + self._menu[parent][2])
        print("time:" + self.time + " sel:" + self._menu[pos][2])

    def displayCurrent(self, pos=None):
        """
        Returns the current selected item string
        """
        if pos is None: pos = self.key
        self.key = pos
        # The string menuMain.key[2] is the current selection title
        return self._menu[pos][2]

    def displayTime(self, pos=None):
        """
        Returns the current time string
        """
        if pos is None: pos = self.key
        self.key = pos
        # The string menuMain.key[2] is the current selection title
        # return self._menu[pos][2]
        while len(self.time) < 4:
            self.time = "0" + self.time
        return str(self.time)

    def action(self, pos=None):
        """
        Returns action associated with current selected menu item
        None if selected item refers to submenu (short time choice)
        """
        if pos is None: pos = self.key
        self.key = pos
        if isinstance(self._menu[pos][3], str): return self._menu[pos][3]
        if self._menu[pos][3] == -2: return self._menu[pos][3]
        return None

    def next(self, pos=None):
        """
        Advances selection to next menu item in same level.
        Rotates to first item when at end of menu level.
        """
        if pos is None: pos = self.key
        self.key = pos
        level = self.struct[self._menu[pos][1]]
        i = level.index(pos)
        i = i + 1
        if i >= len(level): i = 0
        self.key = level[i]

    def back(self, pos=None):
        """
        Decrements selection to prev. menu item in same level.
        Rotates to last item when at beginning of menu level.
        """
        if pos is None: pos = self.key
        self.key = pos
        level = self.struct[self._menu[pos][1]]
        i = level.index(pos)
        i = i - 1
        if i < 0: i = len(level) - 1
        self.key = level[i]

    def select(self, pos=None):
        """
        Advances to sub menu or parent menu then returns False, OR
        Returns True if selected menu has to be actioned, updating actionString.
            and adds digit to time string.
        Returns -1 if selected item is BACK from first level, i.e. abort entry
        If selected item is DONE value -1 from any level, return time string
        If selected item is BACK value -2, shorten time string or go back
        """
        if pos is None: pos = self.key
        self.key = pos
        time.sleep(0.001)
        if isinstance(self._menu[pos][3], str):
            print("Added time now "+self.time)
            self.time += self._menu[pos][3]     # Add selection int to time
            # Keep 4 leftmost digits
            self.time = self.time[4:] if len(self.time) > 4 else self.time
            return True
        if self._menu[pos][3] > 0:      # Top "null" level
            self.key = self.struct[self._menu[pos][0]][0]
            self.level += 1
            return False
        if self._menu[pos][3] == -1:     # Return a short time
            self.key = self._menu[pos][1]
            self.level -= 1
            if self.key == 0: return -1
            return False
        if self._menu[pos][3] == -2:    # Delete last int added to time
            if len(self.time) > 0:
                # Keep n-1 leftmost digits
                if len(self.time) > 1: self.time = self.time[-(len(self.time)-1):]
                else: self.time = ""
                print("digit deleted!")
                return True
            else:
                self.key = self._menu[pos][1]
                self.level -= 1
                if self.key == 0: return -2
                return False

    def up(self, pos=None):
        """
        Goes up one level and returns True
        Returns False if already on top/first level
        to signify a time choice cancelling
        Can typically be used after actioning a selection to return to previous menu item
        """
        if pos is None: pos = self.key
        self.key = pos
        if len(self.time) == 0:
            # print("Time is blank!!!!")
            return False
        if self.level == 1: return False
        self.key = self._menu[pos][1]
        self.level -= 1
        return True


class menuView:
    """
    Menu System for viewing daily recording events OR recorded video files.
    structure is a list of menu items with the following format:
    [digit of current choice,
    start time, end time] OR
    []
    """

    def __init__(self, structure, ExitLabel="BACK", **k_parems):

        # Initialize internal variables
        self._menu = []
        i = 0
        r = {0: 0}
        self.time = "0"
        self._menu.append([0, r[0], "S0", "L0"])
        r[1] = 0
        i += 1

        if 'files' in k_parems:
            # If viewing video files...
            for cur in structure:
                print("menuView file " + str(i) + ": " + str(cur))
                self._menu.append([i, r[0], str(cur), -1])
                # if isinstance(item[2], int): r[item[2]] = i
                # self._menu.append([i, r[item[0]], item[1], item[2]])
                i += 1
            self.key = 1
            self.level = 1
        else:
            # Viewing event schedule
            for cur in structure:
                print("menuView structure" + str(i) + ": " + str(cur))
                print("start:" + str(cur['start']))
                self._menu.append([i, r[0], str(cur['start']), str(cur['length'])])
                # if isinstance(item[2], int): r[item[2]] = i
                # self._menu.append([i, r[item[0]], item[1], item[2]])
                i += 1
            self.key = 1
            self.level = 1

        # Build internal dictionary representing menu structure
        self.struct = {}
        for item in self._menu:
            print("_menu: " + str(item))
            if item[0] != 0:
                if item[1] not in self.struct: self.struct[item[1]] = []
                self.struct[item[1]].append(item[0])

        # Add EXIT entry for each level
        for key in self.struct:
            print("self.struct: " + str(key))
            index = len(self._menu)
            self._menu.append([index, key, ExitLabel, -1])
            self.struct[key].append(index)

    def display(self, pos=None):
        """
        Displays the current menu entry as :
        1st line : parent entry
        2nd line : current selected item
        """
        if pos is None: pos = self.key
        self.key = pos
        parent = self._menu[pos][1]
        print(str(self.level) + ":" + self._menu[parent][2])
        # The string menuMain.key[2] is the current event's start
        # menuMain.key[3] is the current event's length
        print("start:" + str(self._menu[pos][2]) + " length:" + str(self._menu[pos][3]))

    def displayCurrent(self, pos=None):
        """
        Returns the current start time as a string
        """
        if pos is None: pos = self.key
        self.key = pos
        if len(self._menu) == 1: return "Empty"
        # The string menuMain.key[2] is the current event's start
        # menuMain.key[3] is the current event's length
        if self._menu[pos][3] == -1:
            # If current choice is BACK or a video file:
            if self._menu[pos][2] == "BACK":
                return str(self._menu[pos][2])
            else:
                fileName = self._menu[pos][2]
                return str(fileName)
        return str(self._menu[pos][2])+" for "+str(self._menu[pos][3])

    def displayTime(self, pos=None):
        """
        Returns the current time string
        """
        if pos is None: pos = self.key
        self.key = pos
        # The string menuMain.key[2] is the current selection title
        # return self._menu[pos][2]
        while len(self.time) < 4:
            self.time = "0" + self.time
        return str(self.time)

    def action(self, pos=None):
        """
        Returns action associated with current selected menu item
        None if selected item refers to submenu
        """
        if pos is None: pos = self.key
        self.key = pos
        if isinstance(self._menu[pos][3], str): return self._menu[pos][3]
        return None

    def next(self, pos=None):
        """
        Advances selection to next menu item in same level.
        Rotates to first item when at end of menu level.
        """
        if pos is None: pos = self.key
        self.key = pos
        level = self.struct[self._menu[pos][1]]
        i = level.index(pos)
        i = i + 1
        if i >= len(level): i = 0
        self.key = level[i]

    def back(self, pos=None):
        """
        Decrements selection to prev. menu item in same level.
        Rotates to last item when at beginning of menu level.
        """
        if pos is None: pos = self.key
        self.key = pos
        level = self.struct[self._menu[pos][1]]
        i = level.index(pos)
        i = i - 1
        if i < 0: i = len(level) - 1
        self.key = level[i]

    def select(self, pos=None):
        """
        Advances to sub menu or parent menu then returns False, OR
        Returns True if selected menu has to be actioned.
        Returns -1 if selected item is EXIT from first level, i.e. quit the menu
        """
        if pos is None: pos = self.key
        self.key = pos
        if isinstance(self._menu[pos][3], str):
            self.time += self._menu[pos][3]     # Add selection int to time
            # Keep 4 leftmost digits
            self.time = self.time[4:] if len(self.time) > 4 else self.time
            return True
        if self._menu[pos][3] > 0:
            self.key = self.struct[self._menu[pos][0]][0]
            self.level += 1
            return False
        if self._menu[pos][3] == -1:
            self.key = self._menu[pos][1]
            self.level -= 1
            if self.key == 0: return -1
            return False

    def up(self, pos=None):
        """
        Goes up one level and returns True
        Returns False if already on top/first level
        to signify a time choice cancelling
        Can typically be used after actioning a selection to return to previous menu item
        """
        if pos is None: pos = self.key
        self.key = pos
        if self.level == 1: return False
        self.key = self._menu[pos][1]
        self.level -= 1
        return True

MyMenu = [
    [0, "Menu Top", 1],
    [1, "Pompe", 2],
    [2, "Auto", "exec pompe auto"],
    [2, "ON", "exec pompe on"],
    [2, "OFF", "exec pompe OFF"],
    [1, "Lampe", 3],
    [3, "ON", "exec Lampe ON"],
    [3, "OFF", "exec Lampe OFF"],
    [1, "Config", 4],
    [4, "IP", 5],
    [5, "SET", "exec IP Set"],
    [4, "WIFI", 6],
    [6, "Check", "exec wifi check"],
    [6, "Show", "exec wifi show"]
]

MyMenu2 = [
    [0, "Menu Top", 1],

    [1, "Pompe", 2],
    [1, "Lampe", 3],
    [1, "Config", 4],

    [2, "Auto", "exec pompe auto"],
    [2, "ON", "exec pompe on"],
    [2, "OFF", "exec pompe OFF"],

    [3, "ON", "exec Lampe ON"],
    [3, "OFF", "exec Lampe OFF"],

    [4, "IP", 5],
    [4, "WIFI", 6],

    [5, "SET", "exec IP Set"],

    [6, "Check", "exec wifi check"],
    [6, "Show", "exec wifi show"]
]

TimeMenu2 = [
    [0, "null", 10],
    [10, "0", 100],
    [10, "1", 1],
    [10, "2", 2],
    [10, "3", 3],
    [10, "4", 4],
    [10, "5", 5],
    [10, "6", 6],
    [10, "7", 7],
    [10, "8", 8],
    [10, "9", 9],

    [100, "0", "0"],
    [1, "1", "1"],
    [2, "2", "2"],
    [3, "3", "3"],
    [4, "4", "4"],
    [5, "5", "5"],
    [6, "6", "6"],
    [7, "7", "7"],
    [8, "8", "8"],
    [9, "9", "9"]
]


def isInt(v):
    v = str(v).strip()
    return v == '0' or (v if v.find('..') > -1 else v.lstrip('-+').rstrip('0').rstrip('.')).isdigit()


def getch():
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def knob_initTest():
    """
    Teat initiating the knob with rotary switch and
    a push button
    """
    def callbackR(way):
        dec.place += way
        print("pos={}".format(dec.place))

    def callbackS(val):
        dec.state = val
        print("state={}".format(dec.state))

    knobpi = pigpio.pi()
    dec = decoder(knobpi, 16, 20, 26, callbackR, callbackS)

if __name__ == "__main__":

    # import os
    # m = menu(ViewHiveMenu)
    m = menuTime(TimeMenu)
    action = ""

    while True:
        # os.system("clear")
        m.display()
        # print(action)
        c = getch()
        if c == "x": break
        if c == "n": m.next()  # Simulate NEXT button
        if c == "s":  # Simulate SELECT button
            s = m.select()
            if s:
                if s == -1: break
                action = m.action()
                m.up()
