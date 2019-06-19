"""
    arduino.py
    ==========

    Base model for communicating with Arduino devices. In principle, Arduino's can be programmed in very different
    ways, and therefore the flow of information may be very different. This model is thought to interface with
    an Arduino which is in control of two DC motors and which is able to read values from some devices, such as a
    DHT22, and a DS18B20. It relies on PyVisa with pyvisa-py as backend in order to establish the communication with the
    device.
"""
from time import sleep

import pyvisa
from pynta.util.log import get_logger
# TODO: Make more flexible which backend will be used for PyVisa
from pynta.model.exceptions import OutOfRange

rm = pyvisa.ResourceManager('@py')
logger = get_logger(name=__name__)


class Arduino:
    def __init__(self, port=None):
        """

        :param port: Serial port where the Arduino is connected, can be none and in order to look for devices
        automatically
        """
        logger.info(f'Starting Arduino class on port {port}')
        self.rsc = None
        self.port = port
        if port:
            if not port.startswith('ASRL'):
                port = 'ASRL' + port
            self.port = port
            self.rsc = rm.open_resource(self.port, baud_rate=19200)
            sleep(5)
            self.rsc.read_termination = '\r\n'
            self.rsc.timeout = 2500

    def set_speed(self, motor: int, direction: int, speed: int) -> None:
        """ Sets the speed and direction of movement of a motor. It is designed to work with two connected motors
        through a quadrupole half-H driver(SN754410).

        Parameters
        ----------
        motor : int
            Either 1 or 2, which motor to control. It can be extended to control more motors provided that the
            Arduino has enough digital channels available.
        direction : int
            Direction of the movement. Either 0 or 1.
        speed : int
            Speed in 8-bit format (i.e. values between 0 and 255 are accepted)

        Raises
        ------
        OutOfRange
            In case any of the values is outside the allowed range of options.

        """
        logger.info(f'Setting motor {motor} to direction {direction} at speed {speed}')
        if motor not in (1, 2):
            raise OutOfRange('Motor must be either 1 or 2')
        if not 0 <= speed <= 255:
            raise OutOfRange('Speed must be between 0 and 255')
        if direction not in (0, 1):
            raise OutOfRange('Direction must be either 0 or 1')

        command = f'{motor}{direction}{speed:0>3}'
        logger.debug(command)
        logger.info(self.rsc.query(command))

    def read_temperature(self, channel):
        """ Reads the temperature from connected sensors

        Parameters
        ----------
        channel : int
            In principle the Arduino can have more than one temperature sensor connected to it. Specifying the
            channel allows the user to know which temperature is being read.

        Returns
        -------
        temperature : float
            The temperature in degree C.

        """
        command = f'temp{channel}'
        logger.debug(command)
        return self.rsc.query(command)

    def close(self):
        self.set_speed(1, 0, 0)
        self.set_speed(2, 0, 0)
        self.rsc.close()

    @staticmethod
    def list_devices():
        return rm.list_resources()

    def __del__(self):
        self.close()

if __name__ == '__main__':
    import logging

    logger = get_logger()  # 'pynta.model.experiment.nano_cet.saver'
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    inst = Arduino('COM3')
    print(inst.read_temperature(0))
    inst.set_speed(1, 0, 155)
    sleep(1)
    inst.set_speed(1, 1, 155)
    sleep(1)
    inst.set_speed(1, 0, 0)
    inst.close()
    inst.list_devices()