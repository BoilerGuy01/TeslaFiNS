#!/usr/bin/env python
try:
    import polyinterface,logging
except ImportError:
    import pgc_interface as polyinterface
import sys
from urllib.request import urlopen
import xml.etree.ElementTree as ET
import time
import json
import requests

LOGGER = polyinterface.LOGGER
LOGGER.setLevel(logging.WARNING)
LOGGER.setLevel(logging.INFO)
LOGGER.setLevel(logging.DEBUG)
_PARM_API_KEY_NAME = "API_KEY"
BASE_URL = "https://www.teslafi.com/feed.php?token="

def pollTeslaFi(self):
        LOGGER.info('polling TeslaFi')
        try:
          url = '{0}{1}'.format(BASE_URL, self.API_KEY)
          LOGGER.debug('shortPoll - going to check TeslaFi API @ {}'.format(url))
          r = requests.get(url)
          LOGGER.debug('r     = {}'.format(r.json()))
          rJSON = r.json()
          LOGGER.debug('rJSON = {}'.format(rJSON))

          # get car data
          carState = rJSON['carState']
          odometer = rJSON['odometer']
          est_battery_range = rJSON['est_battery_range']
          usable_battery_level = rJSON['usable_battery_level']
          charge_limit_soc = rJSON['charge_limit_soc']
          ideal_battery_range = rJSON['ideal_battery_range']
          locked = rJSON['locked']

          LOGGER.debug('carState = {}'.format(carState))
          LOGGER.debug('odometer = {}'.format(odometer))
          LOGGER.debug('est_battery_range = {}'.format(est_battery_range))
          LOGGER.debug('usable_battery_level = {}'.format(usable_battery_level))
          LOGGER.debug('charge_limit_soc = {}'.format(charge_limit_soc))
          LOGGER.debug('ideal_battery_range= {}'.format(ideal_battery_range))
          LOGGER.debug('locked = {}'.format(locked))

          # set node values
          if carState == 'Sleeping':
            LOGGER.debug('Setting car to asleep (0)')
            self.setDriver('GV1', 0)
          elif carState == 'Idling':
            LOGGER.debug('Setting car to idling (1)')
            self.setDriver('GV1', 1)
          else:
            LOGGER.debug('Setting car to driving (2)')
            self.setDriver('GV1', 2)
          if usable_battery_level is not None:
            self.setDriver('GV2', usable_battery_level)
          if est_battery_range is not None:
            self.setDriver('GV3', est_battery_range)
          if charge_limit_soc is not None:
            self.setDriver('GV4', charge_limit_soc)
          if ideal_battery_range is not None:
            self.setDriver('GV5', ideal_battery_range)
          if locked is not None:
            self.setDriver('GV7', locked)
          if odometer is not None:
            LOGGER.debug('Odometer before rounding = {}'.format(odometer))
            odometer = round(float(odometer), 2)
            LOGGER.debug('Odometer after  rounding = {}'.format(odometer))
            self.setDriver('GV6', odometer)
          LOGGER.debug('Done setting drivers')
        except Exception as err:
          LOGGER.debug('Exception occurred doing URL request {}'.format(err))
          LOGGER.error('Excption: {0}'.format(err), exc_info=True)
        return

class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'TeslaFi Controller'
        self.poly.onConfig(self.process_config)
        LOGGER.debug('Done with __init__')

    def start(self):
        # This grabs the server.json data and checks profile_version is up to date
        serverdata = self.poly.get_server_data()
        LOGGER.info('Started TeslaFi NodeServer {}'.format(serverdata['version']))
        self.heartbeat(0)
        self.check_params()
        self.discover()
        self.poly.add_custom_config_docs("")
        # self.poly.installprofile()

    def shortPoll(self):
        pollTeslaFi(self)
        LOGGER.debug('shortPoll - done checking TeslaFi API')

    def longPoll(self):
        LOGGER.debug('longPoll')
        self.heartbeat()

    def query(self,command=None):
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        return
          
    def delete(self):
        LOGGER.info('Oh God I\'m being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        LOGGER.info("process_config: Enter config={}".format(config));
        LOGGER.info("process_config: Exit");

    def heartbeat(self,init=False):
        LOGGER.debug('heartbeat: init={}'.format(init))
        if init is not False:
            self.hb = init
        LOGGER.debug('heartbeat: hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def check_params(self):
        default_api_key = "ABCDEFG"
        self.removeNoticesAll()

        if 'DebugLevel' in self.polyConfig['customParams']:
            LOGGER.debug('DebugLevel found in customParams')
            self.DebugLevel = self.polyConfig['customParams']['DebugLevel']
            LOGGER.debug('check_params: DebugLevel is: {}'.format(self.DebugLevel))
            if self.DebugLevel == '':
                LOGGER.debug('check_params: DebugLevel is empty')
                self.DebugLevel = int(logging.INFO)
                LOGGER.debug('check_params: DebugLevel is defined in customParams, but is blank - please update it.  Using {}'.format(self.DebugLevel))
                self.addNotice('Set \'DebugLevel\' and then restart')
                st = False
        else:
            LOGGER.debug('check_params: DebugLevel does not exist self.polyCconfig: {}'.format(self.polyConfig))
            self.DebugLevel = int(logging.INFO)
            LOGGER.debug('check_params: DebugLevel not defined in customParams, setting to {}'.format(self.DebugLevel))
            st = False

        # convert string to int
        self.DebugLevel = int(self.DebugLevel)

        # Set the debug level based on parameter
        LOGGER.setLevel(self.DebugLevel)
        LOGGER.warning('Setting debug level to {}'.format(self.DebugLevel))
        self.setDriver('GV0', self.DebugLevel)
        LOGGER.warning('Done setting debug level to {}'.format(self.DebugLevel))

        if 'API_KEY' in self.polyConfig['customParams']:
            LOGGER.debug('API_KEY found in customParams')
            self.API_KEY = self.polyConfig['customParams']['API_KEY']
            LOGGER.debug('check_params: API_KEY is: {}'.format(self.API_KEY))
            if self.API_KEY == '' or self.API_KEY == default_api_key:
                LOGGER.debug('check_params: API_KEY is empty')
                self.API_KEY = default_api_key
                LOGGER.debug('check_params: API_KEY is defined in customParams, but is blank - please update it.  Using {}'.format(self.API_KEY))
                self.addNotice('Set \'API_KEY\' and then restart')
                st = False
        else:
            LOGGER.debug('check_params: API_KEY does not exist self.polyCconfig: {}'.format(self.polyConfig))
            self.API_KEY = default_api_key
            LOGGER.debug('check_params: API_KEY not defined in customParams, please update it.  Using {}'.format(self.API_KEY))
            self.addNotice('Set \'API_KEY\' and then restart')
            st = False

        LOGGER.debug('Done checking: self.API_KEY = {}'.format(self.API_KEY))

        # Make sure they are in the params
        self.addCustomParam({'DebugLevel': self.DebugLevel, 'API_KEY': self.API_KEY})

    def remove_notice_test(self,command):
        LOGGER.info('remove_notice_test: notices={}'.format(self.poly.config['notices']))
        # Remove all existing notices
        self.removeNotice('test')

    def remove_notices_all(self,command):
        LOGGER.info('remove_notices_all: notices={}'.format(self.poly.config['notices']))
        # Remove all existing notices
        self.removeNoticesAll()

    def update_profile(self,command):
        LOGGER.info('update_profile:')
        st = self.poly.installprofile()
        return st

    def set_debug_level(self,command):
        self.DebugLevel = int(command['value'])
        LOGGER.warning("New debug level: {}".format(self.DebugLevel))
        self.setDriver('GV0', self.DebugLevel)
        LOGGER.setLevel(self.DebugLevel)

        # Make sure they are in the params
        self.addCustomParam({'DebugLevel': self.DebugLevel, 'API_KEY': self.API_KEY})

    def send_teslafi_command(self, commandStr):
       LOGGER.debug('commandStr = {}'.format(commandStr))
       try:
         url = '{0}{1}&command={2}'.format(BASE_URL, self.API_KEY, commandStr)
         LOGGER.debug('Sending command to TeslaFi API @ {}'.format(url))
         r = requests.get(url)
         LOGGER.debug('r = {}'.format(r))
       except Exception as err:
         LOGGER.error('Flash Exception: {0}'.format(err), exc_info=True)

    def wake(self, command=None):
       LOGGER.debug("Wake command received");
       LOGGER.debug('command = {}'.format(command))
       self.send_teslafi_command("wake_up")

    def honk(self, command=None):
       LOGGER.debug("Honk command received");
       LOGGER.debug('command = {}'.format(command))
       self.send_teslafi_command("honk")

    def flash(self, command=None):
       LOGGER.debug("Flash command received");
       LOGGER.debug('command = {}'.format(command))
       self.send_teslafi_command("flash_lights")

    def lock(self, command=None):
       LOGGER.debug("Lock command received");
       LOGGER.debug('command = {}'.format(command))
       self.send_teslafi_command("door_lock")
       self.setDriver('GV7', 1)

    def set_charge_level(self, command=None):
       LOGGER.debug('command = {}'.format(command))
       chargeLimit = command['value']
       LOGGER.debug('chargeLimit = {}'.format(chargeLimit))
       commandStr = 'set_charge_limit&charge_limit_soc={0}'.format(chargeLimit)
       self.send_teslafi_command(commandStr)
       self.setDriver('GV4', chargeLimit)

    def setOn(self, command):
       self.setDriver('ST', 1)

    def setOff(self, command):
       self.setDriver('ST', 0)

    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile,
        'REMOVE_NOTICES_ALL': remove_notices_all,
        'REMOVE_NOTICE_TEST': remove_notice_test,
        'SET_DEBUG_LEVEL': set_debug_level,
        'WAKE': wake,
        'HONK': honk,
        'FLASH': flash,
        'SET_CHARGE_LEVEL': set_charge_level,
        'LOCK': lock,
    }
    drivers = [{'driver': 'ST',  'value': 0, 'uom': 2},
               {'driver': 'GV0', 'value': 0, 'uom': 25},
               {'driver': 'GV1', 'value': 0, 'uom': 25},
               {'driver': 'GV2', 'value': 0, 'uom': 51},
               {'driver': 'GV3', 'value': 0, 'uom': 116},
               {'driver': 'GV4', 'value': 0, 'uom': 51},
               {'driver': 'GV5', 'value': 0, 'uom': 116},
               {'driver': 'GV6', 'value': 0, 'uom': 116},
               {'driver': 'GV7', 'value': 0, 'uom': 25},
    ]

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('TeslaFiNS')
        """
        Instantiates the Interface to Polyglot.
        The name doesn't really matter unless you are starting it from the
        command line then you need a line Template=N
        where N is the slot number.
        """
        polyglot.start()
        """
        Starts MQTT and connects to Polyglot.
        """
        control = Controller(polyglot)
        """
        Creates the Controller Node and passes in the Interface
        """
        control.runForever()
        """
        Sits around and does nothing forever, keeping your program running.
        """
    except (KeyboardInterrupt, SystemExit):
        LOGGER.warning("Received interrupt or exit...")
        """
        Catch SIGTERM or Control-C and exit cleanly.
        """
        polyglot.stop()
    except Exception as err:
        LOGGER.error('Excption: {0}'.format(err), exc_info=True)
    sys.exit(0)
