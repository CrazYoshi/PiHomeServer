#!/usr/bin/python
import sys 
import sqlite3 as lite 
import os.path
import logging
import time
import urllib2
import json
with open('settings.json', 'r') as settings_file:
    config = json.load(settings_file)

DBNAME = config['Database']['Path']
logger = logging.getLogger('sql.py')

def init():
	if not os.path.isfile(DBNAME):
		logger.warning('Database does NOT exists. Creating a new one..')
		createDatabase()
	else:
		logger.debug('Database %s found', DBNAME)

def getHistory():
	logger.debug('Getting history from database')
	con = lite.connect(DBNAME)
	cur = con.cursor()
	cur.execute('SELECT Timestamp,Sensor FROM History ORDER BY Timestamp DESC LIMIT 24')
	rows = cur.fetchall()
	logger.debug('Retrieved %s rows',len(rows))
	con.close()
	return rows

def setHistory(data):
	try:
		logger.debug('Inserting new row inside database %s: %s', DBNAME, data)
		con = lite.connect(DBNAME)
		cur = con.cursor()
		cur.execute('INSERT INTO History(Timestamp,Sensor) VALUES (?,?)',(time.strftime("%Y-%m-%d %H:%M:%S.000",time.localtime()),data))
		con.commit()
	except Exception,e:
		logger.error('Exception in INSERT History: %s',e)
	finally:
		con.close()

def createDatabase():
	logger.debug('CreateDatabase called..')
	con = lite.connect(DBNAME)
	cur = con.cursor()
	cur.execute('''CREATE TABLE History(Id INTEGER PRIMARY KEY AUTOINCREMENT, Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, Sensor TEXT NOT NULL)''')
	con.commit()
	con.close()
	logger.info('Database created')
