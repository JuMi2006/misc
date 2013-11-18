﻿#!/usr/bin/python

import serial
import time
import sys
import logging
from struct import *
logger = logging.getLogger('Roomba')



cmd_dict=dict(
    power_off = 133,            #change2passive
    spot = 134,                 #change2passive
    clean = 135,                #change2passive
    max = 136,                  #change2passive
    drive = 137,               #add 4 databytes
    stop = [137,0,0,0,0],
    forward = [137,0,100,128,0], #http://fantastickobe.blogspot.de/2008/03/lets-play-with-irobot-create-2.html
    backward = [137,255,156,128,0], #http://www.irobot.com/filelibrary/pdfs/hrd/create/Create%20Open%20Interface_v2.pdf
    spin_left = [137,0,0,255,255],
    spin_right = [137,0,0,0,1],
    motors = 138,               #add 1 databyte
    leds = 139,                 #add 3 databytes
    song = 140,                 #add 2n + 2 databytes
    play = 141,                 #add 1 databyte
    dock = 143,                 #change2passive
)


def main():
    try:
        tty = '/dev/rfcomm1'
        baudrate = 57600
        sci=roomba(tty,baudrate)    
    except:
        logger.error("Fehler: {0}".format(e))

class Roomba(object):
    _items = []
    
    def __init__(self,smarthome,tty,baudrate,cycle):
        self._cycle = cycle
        self._sh = smarthome
        self.tty = tty
        self.baudrate = baudrate
        self.ser = serial.Serial(tty, baudrate=baudrate, timeout=5)
        logger.debug("Connected to: {0} and {1} baud.".format(tty,baudrate))
        self._is_connected = 'False'
        #self.ser.open()
        #self.send(128)  #start
        #self.send(130)  #command
        #self.send(131)  #safe
        #self.send(132)  #full

        #self.send(135)
        #self.send([137,255,56,1,244])  #testfahrt
        #time.sleep(2)
        #self.send([137,0,0,0,0])
        #WORKS
        #self.ser.write(b"\x80") # 128: start command
        #self.ser.write(b"\x84") # 130: control command
        #self.ser.write(b"\x87") # 135: clean command
    
    def run(self):
        pass

    def connect(self):
        self.ser.open()
        self._is_connected = 'True'
        self.send(128)  #start
        self.send(130)  #command
    
    def disconnect(self):
        self.send(128)
        self.ser.close()
        self._is_connected = 'False'
    
    def parse_item(self, item):
        if 'roomba_cmd' in item.conf:
            cmd_string = item.conf['roomba_cmd']
            logger.debug("Roomba: {0} will send cmd \'{1}\'".format(item, cmd_string))
            self._items.append(item)
            return self.update_item
        elif 'roomba_get' in item.conf:
            sensor_string = item.conf['roomba_get']
            logger.debug("Roomba: {0} will get {1}".format(item, sensor_string))
            self._items.append(item)
            #self._sh.scheduler.add('Roomba', self.get_sensors, prio=5, cycle=self._cycle, offset=2)
        elif 'roomba_drive' in item.conf:
            drive_string = item.conf['roomba_drive']
            logger.debug("Roomba: {0} will drive {1}".format(item, drive_string))
            self._items.append(item)
            return self.update_item		
            
    def update_item(self, item, caller=None, source=None, dest=None):
        if caller != 'roomba':
            if item():
                if 'roomba_cmd' in item.conf:	
                    cmd_string = item.conf['roomba_cmd']
                    logger.debug("Roomba: item = true")
                    raw = self.string2cmd(cmd_string, item)
                    if cmd_string in cmd_dict:
                        self.send(raw)
                if 'roomba_drive' in item.conf:
                    drive_string = item.conf['roomba_drive']
                    logger.debug("Roomba: item = true")
                    self.drive(drive_string)
                else:
                    pass
    
    def string2cmd(self, cmd_string, item):
        if cmd_string in cmd_dict: 
            raw = cmd_dict[cmd_string]
            return raw
        else: 
            return
    
    def drive(self,cmd_string):
        print (len(cmd_string))
        full_raw_cmd = []
        for i in cmd_string:
            print (i)
            try:
                wait = float(i)
                print ("wait {0}".format(wait))
            except:
                full_raw_cmd.append(cmd_dict[i])
        print (full_raw_cmd)
            
        
    def send(self, raw):
        #Send a string of bytes to the robot
        if type(raw) is list:
            print ('a list')
            print ("Send {0}".format(raw))
            self.ser.write(bytearray(raw))
        else:
            print ('a single')
            print ("Send [{0}]".format(raw))
            self.ser.write(bytearray([raw]))

    def get_sensors(self):
        self.connect()
        self.send([142,0])
        answer = self.ser.read(26)
        answer = list(answer)
        print (answer)
        #create sensor_dict
        sensor_dict = {}
        sensor_dict = dict()
        
        #sensor_raw:
        _capacity = self.DecodeUnsignedShort(answer[25],answer[24]) #capacity
        sensor_dict['capacity']=_capacity
        
        _charge=self.DecodeUnsignedShort(answer[23],answer[22]) #charge
        sensor_dict['charge']=_charge
        
        _temperature = self.DecodeByte(answer[21]) #temperature
        sensor_dict['temperature']=_temperature
        
        _current=self.DecodeShort(answer[20],answer[19]) #current
        sensor_dict['current']=_current
        
        _voltage = self.DecodeUnsignedShort(answer[18],answer[17]) #voltage
        sensor_dict['voltage']=_voltage
        
        _charging_state = self.DecodeUnsignedByte(answer[16]) #charging state
        sensor_dict['charging_state']=_charging_state
        
        #_angle = self.Angle(answer[15], answer[14], 'degrees') #angle
        #sensor_dict['angle']=_angle
        
        _distance = self.DecodeShort(answer[13],answer[12]) #distance
        sensor_dict['distance']=_distance
        
        _buttons = list(self.Buttons(answer[11])) #Button
        sensor_dict['buttons_max']=_buttons[0]
        sensor_dict['buttons_clean']=_buttons[1]
        sensor_dict['buttons_spot']=_buttons[2]
        sensor_dict['buttons_power']=_buttons[3]
        
        _remote_opcode = self.DecodeUnsignedByte(answer[10]) #remote_opcode
        sensor_dict['remote_opcode']=_remote_opcode
        
        _dirt_detect_right = self.DecodeUnsignedByte(answer[9]) #dirt detect right
        sensor_dict['dirt_detect_right']=_dirt_detect_right
        
        _dirt_detect_left = self.DecodeUnsignedByte(answer[8]) #dirt detect left
        sensor_dict['dirt_detect_left']=_dirt_detect_left
        
        _motor_overcurrent = self.MotorOvercurrents(answer[7]) #motor overcurrent
        sensor_dict['motor_overcurrent_side_brush']=_motor_overcurrent[0]
        sensor_dict['motor_overcurrent_vacuum']=_motor_overcurrent[1]
        sensor_dict['motor_overcurrent_main_brush']=_motor_overcurrent[2]
        sensor_dict['motor_overcurrent_drive_right']=_motor_overcurrent[3]        
        sensor_dict['motor_overcurrent_drive_left']=_motor_overcurrent[3] 
        sensor_dict['motor_overcurrent_motor_overcurrent']=_motor_overcurrent[0]
        
        _virtual_wall = answer[6]
        sensor_dict['virtual_wall']=_virtual_wall
        
        _cliff_right = answer[5]
        sensor_dict['cliff_right']=_cliff_right
        
        _cliff_front_right = answer[4]
        sensor_dict['cliff_front_right']=_cliff_front_right
        
        _cliff_front_left = answer[3]
        sensor_dict['cliff_front_left']=_cliff_front_left
        
        _cliff_left = answer[2]
        sensor_dict['cliff_left']=_cliff_left
        
        _wall = answer[1]
        sensor_dict['wall']=_wall
        
        _bumps_wheeldrops = self.BumpsWheeldrops(answer[0])
        sensor_dict['bumps_wheeldrops_bump_right']=_bumps_wheeldrops[0]
        sensor_dict['bumps_wheeldrops_bump_left']=_bumps_wheeldrops[0]
        sensor_dict['bumps_wheeldrops_wheeldrop_right']=_bumps_wheeldrops[0]
        sensor_dict['bumps_wheeldrops_wheeldrop_left']=_bumps_wheeldrops[0]
        sensor_dict['bumps_wheeldrops_wheeldrop_caster']=_bumps_wheeldrops[0]
        
        for item in self._items:
            if 'roomba_get' in item.conf:
                sensor = item.conf['roomba_get']
                if sensor in sensor_dict:
                    value = sensor_dict[sensor]
                    item(value, 'Roomba', 'get_sensors')
        
        self.disconnect()
        
    def dec2hex(self,num):
        num = int(num)
        return (str('0x' + '%.2x' % num))

    def DecodeUnsignedShort(self, low, high):
        bytearr = bytearray([high,low])
        value = unpack('>H', bytearr)
        print (value[0])
        return (value[0])
        
    def DecodeByte(self,byte):
        bytearr = bytearray([byte])
        value = unpack('b', bytearr)
        print (value[0])
        return (value[0])
        
    def DecodeShort(self, low, high):
        bytearr = bytearray([high,low])
        value = unpack('>h', bytearr)
        print (value[0])
        return (value[0])
    
    def DecodeUnsignedByte(self, byte):
        bytearr = bytearray([byte])
        value = unpack('B', bytearr)
        print (value[0])
        return (value[0])
    
    def Angle(self, low, high, unit=None):
        #Angle in radians = (2 * difference) / 258
        #Angle in degrees = (360 * difference) / (258 * Pi).
        if unit not in (None, 'radians', 'degrees'):
            pass
        angle = self.DecodeShort(low, high)
        angle = int(angle[0])
        if unit == 'radians':
            angle = (2 * angle) / 258
            print ("{0} radians".format(angle))
            return angle
        if unit == 'degrees':
            angle /= math.pi
            print ("{0} degrees".format(angle))
            return angle
    
    def Buttons(self, byte):
        bytearr = bytearray([byte])
        byte = unpack('B', bytearr)
        byte = byte[0]
        return (byte & 1, byte & 2, byte & 3, byte & 4)
        #returns max,clean,spot,power
    
    def MotorOvercurrents(self, byte):
        bytearr = bytearray([byte])
        byte = unpack('B', bytearr)
        byte = byte[0]
        return (byte & 1, byte & 2, byte & 3, byte & 4, byte & 5)
        #returns side-brush,vacuum,main-brush,drive-right,drive-left
    
    def BumpsWheeldrops(self, byte):
        bytearr = bytearray([byte])
        byte = unpack('B', bytearr)
        byte = byte[0]
        return (byte & 1, byte & 2, byte & 3, byte & 4, byte & 5)
        #returns bump-right,bump-left,wheel-drop-right,wheel-drop-left,wheel-drop-caster

        
class roomba_cmd():
    pass

if __name__ == "__main__":
    sys.exit(main()) 
