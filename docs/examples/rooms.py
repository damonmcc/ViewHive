#!/usr/bin/env python
import curses
screen = curses.initscr()
curses.curs_set(0)
screen.keypad(1)


def main(screen):

    screen.addstr("This\n\n")
    while True:
        event = screen.getch()
        if event == ord("q"): break
##    curses.echo()

curses.wrapper(main)
curses.wrapper(main)
