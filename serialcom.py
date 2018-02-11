from server import app, Access, get_day_timestamp, Employee, Event
import datetime
import serial
import os
import threading
from time import sleep
import coloredlogs
import logging


##############
## Logger
#########
# Create a logger object.
logger = logging.getLogger('SERIAL')
coloredlogs.install(level='DEBUG', logger=logger)

##############
## End Logger
#########

##############
## Events
#########

def save_event(badge_hexcode, authorized):
    fullname = "Unknown"
    try:
        employee = Employee.objects(badges__code_hex=badge_hexcode)[0]
        fullname = employee.last_name + ' ' + employee.first_name
    except :
        pass
    event = Event(
        badge_owner=fullname,
        badge_hexcode=badge_hexcode,
        authorized=authorized
    )
    event.save()
    return event

##############
## End Events
#########

##############
## Access Controle
#########

def isAuthorized(bagde_hexcode):
    now = datetime.datetime.now()
    t = get_day_timestamp(now)
    result = Access.objects(
        start_time__lte=t, end_time__gte=t, badges=bagde_hexcode)
    if result.count() >= 1:
        return True

    return False


def authorize(bagde_hexcode):
    logger.debug("Cheking Auth for badge: '%s'" % bagde_hexcode)
    is_authorized = isAuthorized(bagde_hexcode)
    if is_authorized:
        logger.info('badge %s authorized' % bagde_hexcode)
        serial_com.write('y'.encode())
    else:
        logger.error('badge %s not authorized' % bagde_hexcode)
        serial_com.write('n'.encode())
    
    event = save_event(bagde_hexcode, is_authorized)

##############
## End Access Controle
#########


##############
## Serial Communication
#########
serial_com = None


def serial_connect():
    global serial_com
    while(True):
        logger.debug("serial while")
        try:
            if(serial_com == None):
                logger.debug("Attempting serial connect")
                serial_com = serial.Serial('COM9', 9600)

            read_serial()
        except:
            logger.error("serial connect error")
            if(not(serial_com == None)):
                serial_com.close()
                serial_com = None
            sleep(1)
            # serial_connect()


def read_serial():
    while True:
        logger.info("Reading serial")
        serial_line = serial_com.readline()
        logger.info("Got serial: '%s'" % serial_line)
        s = serial_line.decode('ascii').strip()
        decode_serial(s)


options = {
    'Auth': authorize,
    'nAuth': authorize
}


def decode_serial(line):
    logger.debug("decoding serial: '%s'" % line)
    array = line.split(':')
    if array[0] in options:
        options[array[0]](array[1])
    else:
        logger.warning("Unknown Serial CMD")


serial_connect()
# t1 = threading.Thread(target=serial_connect, args=())
# t1.start()
# read_serial()
##############
## End Serial Communication
#########
