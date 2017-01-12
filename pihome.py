#!/usr/bin/python
import sys
from daemon import Daemon
from time import sleep
import threading
import urllib2
import logging
import sql
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import json
with open('settings.json', 'r') as settings_file:
    config = json.load(settings_file)

# Initialization functions
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%y-%m-%d %H:%M',
                    filename='pihome.log')
logger = logging.getLogger('pihome.py')
sql.init()

def setHistory():
	while True:
		logger.debug('Calling setHistory')
		try:
			data = urllib2.urlopen(config['HTTPServer']['ArduinoUrl']).read()
			sql.setHistory(data)
			logger.debug('setHistory thread going to sleep')
			sleep(config['History']['SleepTime'])
		except urllib2.URLError, e:
			logger.error('Error in HTTP request: %r',e)
		except socket.timeout, e:
			logger.error('Request timeout: %r',e)

#This class will handles any incoming request from the browser 
class httpHandler(BaseHTTPRequestHandler):
	#Handler for the GET requests
	def do_GET(self):
		logger.debug('Path received: %s', self.path)
		resposne = None
		if self.path == '/':
			response = urllib2.urlopen(config['HTTPServer']['ArduinoUrl']).read()
		if self.path.endswith('history'):
			response = json.dumps(sql.getHistory())

		if response is not None:
			logger.debug('Sending reponse..')
			self.send_response(200)
			self.send_header('Content-type','application/json')
			self.end_headers()
			# Send the html message
			self.wfile.write(response)
		return

# Daemon class	
class piDaemon(Daemon):
	def run(self):
		# Create a new Thread to read from Arduino
		logger.debug('Starting history thread')
		t = threading.Thread(target = setHistory)
		t.daemon = True
		t.start()

		#Create a web server and define the handler to manage the incoming request
		PORT_NUMBER = config['HTTPServer']['Port']
		server = HTTPServer(('', PORT_NUMBER), httpHandler)
		logger.info('Starting httpserver on port %s' , PORT_NUMBER)
		server.serve_forever()
		
	def prestop(self):
		logger.info('Closing httpserver')

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
