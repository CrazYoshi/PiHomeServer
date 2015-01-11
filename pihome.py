#!/usr/bin/python
import sys
import RPi.GPIO as GPIO
import Adafruit_DHT
import sql
import os
import os.path
import config
import pyjsonrpc
import logging
from daemon import Daemon
from time import sleep
import threading

# Variables list
configFile = 'config.conf' 
ht = Adafruit_DHT.DHT22 
dbname = config.ConfigOptionMap(configFile,'DATABASE','dbname')
pin = config.ConfigSectionMapToInt(configFile,'PIN') 
bounce = config.ConfigSectionMapToInt(configFile,'BOUNCE_TIME')
wait = config.ConfigSectionMapToInt(configFile,'WAIT_TIME')
JSONserver = config.ConfigSectionMap(configFile,'JSONRPC')
logconf = config.ConfigSectionMap(configFile,'LOG')
authClient = config.ConfigOptionMap(configFile,'AUTHORIZED_CLIENT','ip')
client_wait = config.ConfigSectionMapToInt(configFile,'WAIT_FOR_CLIENT')


# Log
logger = logging.getLogger('pihome')
hdlr = logging.FileHandler(logconf['logfile'])
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
if logconf['level'] == 'INFO':
	logger.setLevel(logging.INFO)
elif logconf['level'] == 'WARNING':
	logger.setLevel(logging.WARNING)
elif logconf['level'] == 'ERROR':
	logger.setLevel(logging.ERROR)
else:
	logger.setLevel(logging.DEBUG)

# Functions
def setup():
	try:
		#setup DOOR pin
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(pin['door'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(pin['door'], GPIO.RISING, callback=door, bouncetime=bounce['door'])
		#setup PIR pin
		GPIO.setup(pin['pir'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(pin['pir'], GPIO.RISING, callback=pir, bouncetime=bounce['pir'])
		#setup LED pin
		GPIO.setup(pin['ledgreen'], GPIO.OUT)
		GPIO.setup(pin['ledred'], GPIO.OUT)
		# LED blink during startup	
		splash = threading.Thread(target = blinkLed, args = ('green',0.5,5))
		splash.daemon = True
		splash.start()
		splash.join(5) #Timeout 5 sec
	except Exception,e:
		logger.error('Exception in GPIO setup: %s',e)
		GPIO.cleanup()
		sys.exit(1)
	
def door(channel):
	if GPIO.input(pin['door']) == 1: #check if the door is really opened or is a fake
		if ping() == False: #if the server doesn't ping the client successfully, it will wait X sec and retry
			l = threading.Thread(target = wait_for_auth, args = ('door','PiHome has detected your home door has been opened'))
		else:
			l = threading.Thread(target = led, args = ('green',wait['led']))
		l.daemon = True
		l.start()

def pir(channel):
	if GPIO.input(pin['pir']) == 1: #double check if the sensor have really find someone
		if ping() == False: #if the server doesn't ping the client successfully, it will wait X sec and retry
			p = threading.Thread(target = wait_for_auth, args = ('pir','PiHome has detected some movements in your home'))
		else:
			p = threading.Thread(target = led, args = ('green',wait['led']))
		p.daemon = True
		p.start()				

def dht():
	while True:
		try:
			humidity, temperature = Adafruit_DHT.read_retry(ht, pin['dht']) # Try to grab a sensor reading.  Use the read_retry method which will retry up to 15 times to get a sensor reading (waiting 2 seconds between each retry).
			if humidity is not None and temperature is not None: # Note that sometimes you won't get a reading and the results will be null (because Linux can't guarantee the timing of calls to read the sensor). If this happens try again!
				sql.insertDHT(dbname,temperature,humidity) #print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity)
				#logger.info('DHT process going to sleep..')
				sleep(wait['dht'])
			else:
				logger.info('Failed to get reading. Try again!')
		except:
			logger.warning('DHT exit before time')

def dhtRead():
	try:
		logger.info('dhtRead request received')
		humidity, temperature = Adafruit_DHT.read_retry(ht, pin['dht'])
		if humidity is not None and temperature is not None:
			return temperature,humidity
		else:
			dhtRead()
	except:
		logger.error('Error during DHT read')

def led(color,time):
	if color == 'green':
		GPIO.output(pin['ledgreen'], True)
		GPIO.output(pin['ledred'], False)
	elif color == 'red':
		GPIO.output(pin['ledgreen'], False)
		GPIO.output(pin['ledred'], True)
	elif color == 'black':
		GPIO.output(pin['ledgreen'], False)
		GPIO.output(pin['ledred'], False)
	if time != 0:
		sleep(time)
		GPIO.output(pin['ledgreen'], False)
		GPIO.output(pin['ledred'], False)

def blinkLed(color,interval,times):
	i = 0
	while i<times*2:
		if i % 2 == 0:
			led(color,interval)
		else: 
			led('black',interval)
		i=i+1

def ping():
	response = os.system("ping -c 1 " + authClient)
	if response == 0:
		return True
	else:
		return False

def wait_for_auth(eventType,eventDescription):
	try:
		blinkLed('red',0.5,2)
		sleep(client_wait['wait'])
		color = 'black'
		if ping() == False:
			logger.info(eventDescription)
			sql.insertEvent(dbname,eventType,eventDescription)
			color = 'red'
        	else:
			color = 'green'
		led(color,wait['led']) 
	except Exception,e:
                logger.error('Exception in wait_for_auth: %s',e)

def selectEvents():	
	logger.info('selectEvents request received')
	return sql.selectEvents(dbname)

def selectDHTinfo():
	logger.info('selectDHTinfo request received')
	return sql.selectDHTinfo(dbname)

def selectEventNotification():
	logger.info('selectNotificationEvents request received')
	return sql.selectEventNotification(dbname)

def deleteEvent(eventIdList):
	logger.info('deleteEvent request received')
	for obj in eventIdList:
		sql.deleteEvent(dbname,obj)
	return sql.selectEvents(dbname)

# Threading HTTP-Server
class RequestHandler(pyjsonrpc.HttpRequestHandler): # Register public JSON-RPC methods
	methods = dict( 
        	dhtRead = dhtRead,
		selectEvents = selectEvents,
		selectDHTinfo = selectDHTinfo,
		selectEventNotification = selectEventNotification,
		ping = ping,
		deleteEvent = deleteEvent
	)

# Daemon class	
class piDaemon(Daemon):
	def run(self):
		if not os.path.isfile(dbname):
			logger.info('DB not found. Creating a new one..')
			sql.createDB(dbname)
		setup()
		http_server = pyjsonrpc.ThreadingHttpServer(	
			server_address = (JSONserver['server'], 8080),	
			RequestHandlerClass = RequestHandler)
		# Create a new Thread to read from DHT
		logger.info('Start DHT process')
		t= threading.Thread(target = dht)
		t.daemon = True
		t.start()
		logger.info('Start JSONRPCserver')
		http_server.serve_forever()
		
	def prestop(self):
		#http_server.shutdown()
		logger.info('Closing...')
		GPIO.cleanup()

# Main activity
if __name__ == "__main__":
	daemon = piDaemon('/tmp/pihome.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
				daemon.start()
		elif 'stop' == sys.argv[1]:
				daemon.stop()
		elif 'restart' == sys.argv[1]:
				daemon.restart()
		else:
				print "Unknown command"
				sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart" % sys.argv[0]
		sys.exit(2)
