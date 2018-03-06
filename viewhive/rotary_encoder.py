

class decoder:
    """Class to decode mechanical rotary encoder pulses."""

    def __init__(self, pi, gpioA, gpioB, gpioC, callbackR, callbackS):
        """
      Instantiate the class with the pi and gpios connected to
      rotary encoder contacts A and B.  The common contact
      should be connected to ground.  The callback is
      called when the rotary encoder is turned.  It takes
      one parameter which is +1 for clockwise and -1 for
      counterclockwise.
      """

        import pigpio
        self.pi = pi
        self.gpioA = gpioA
        self.gpioB = gpioB
        self.gpioC = gpioC
        self.callbackR = callbackR
        self.callbackS = callbackS
        self.place = 0
        self.bounce = 0

        self.levA = 0
        self.levB = 0

        self.lastGpio = None
        self.lastState = None

        self.pi.set_mode(gpioA, pigpio.INPUT)
        self.pi.set_mode(gpioB, pigpio.INPUT)
        self.pi.set_mode(gpioC, pigpio.INPUT)

        self.pi.set_pull_up_down(gpioA, pigpio.PUD_UP)
        self.pi.set_pull_up_down(gpioB, pigpio.PUD_UP)
        self.pi.set_pull_up_down(gpioC, pigpio.PUD_UP)

        # Debounce switch pin, time in microseconds
        self.pi.set_glitch_filter(gpioC, 2000)

        # Rotation callback will be callbackR (_push)
        self.cbA = self.pi.callback(gpioA, pigpio.EITHER_EDGE, self._pulse)
        self.cbB = self.pi.callback(gpioB, pigpio.EITHER_EDGE, self._pulse)
        # Switch callback will be callbackS (_pulse)
        self.cbC = self.pi.callback(gpioC, pigpio.FALLING_EDGE, self._push)

    def _pulse(self, gpio, level, tick):

        """
      Decode the rotary encoder pulse.

                   +---------+         +---------+      0
                   |         |         |         |
         A         |         |         |         |
                   |         |         |         |
         +---------+         +---------+         +----- 1

             +---------+         +---------+            0
             |         |         |         |
         B   |         |         |         |
             |         |         |         |
         ----+         +---------+         +---------+  1
      """
        if gpio == self.gpioA:
            self.levA = level
        else:
            self.levB = level

        if gpio != self.lastGpio:  # debounce
            self.lastGpio = gpio

            if gpio == self.gpioA and level == 1:
                if self.levB == 1:
                    self.callbackR(1)
            elif gpio == self.gpioB and level == 1:
                if self.levA == 1:
                    self.callbackR(-1)

    def _push(self, gpio, state, tick):
        """
        Decode the rotary encoder button press.
        """
        if state == 0:  # pressed
            print("Pressed!")
            print("{:2d}->{} at {}".format(gpio, state, tick))
            self.callbackS(1)
            # self.state ==
        else:
            print("NoT Pressed?!!")
            self.callbackS(0)

    def cancel(self):

        """
      Cancel the rotary encoder decoder.
      """
        self.cbA.cancel()
        self.cbB.cancel()
        self.cbC.cancel()


if __name__ == "__main__":
    import time
    import pigpio

    pos = 0
    state = 0

    def callbackR(way):
        global pos
        pos += way
        print("pos={}".format(pos))

    def callbackS(val):
        global state
        state = val
        print("state={}".format(state))


    pi = pigpio.pi()

    decoder = decoder(pi, 16, 20, 26, callbackR, callbackS)

    time.sleep(30)

    decoder.cancel()

    pi.stop()
