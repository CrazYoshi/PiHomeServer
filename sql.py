#!/usr/bin/python

import sqlite3 as lite
import sys
import time

def createDB(dbname):
	con = lite.connect(dbname)
	cur = con.cursor()
	cur.execute('''CREATE TABLE events(id INTEGER PRIMARY KEY AUTOINCREMENT, eventType TEXT,
                       eventDescription TEXT NULL, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, isNotified INTEGER DEFAULT '0' NULL)''')
	cur.execute('CREATE TABLE dht (id INTEGER PRIMARY KEY AUTOINCREMENT, temperature NUMERIC, humidity NUMERIC, ts TIMESTAMP)')
	con.commit()
	con.close()

def insertEvent(dbname,eventType,eventDescription):
	con = lite.connect(dbname)
	cur = con.cursor()
	cur.execute("INSERT INTO events (eventType,eventDescription,ts) VALUES (?,?,?)",(eventType,eventDescription,time.strftime("%Y-%m-%d %H:%M:%S.000",time.localtime())))
	con.commit()
	con.close()

def deleteEvent(dbname,eventId):
	con = lite.connect(dbname)
	cur = con.cursor()
	cur.execute("DELETE FROM events WHERE id=?",(eventId,))
	con.commit()
	con.close()

def insertDHT(dbname,temperature,humidity): 
	con = lite.connect(dbname)
	cur = con.cursor()
        cur.execute("INSERT INTO dht (temperature,humidity,ts) VALUES (?,?,?)",(temperature,humidity, time.strftime("%Y-%m-%d %H:%M:%S.000",time.localtime())))
	con.commit()
        con.close()

def selectEvents(dbname):
	con = lite.connect(dbname)
	cur = con.cursor()
	cur.execute("SELECT id,eventType,eventDescription,ts FROM events ORDER BY ts DESC LIMIT 15")
	rows = cur.fetchall()
	con.close()
	return rows

def selectDHTinfo(dbname):
	con = lite.connect(dbname)
	cur = con.cursor()
   	cur.execute("SELECT id,temperature,humidity,ts FROM dht ORDER BY ts DESC LIMIT 12")
   	rows = cur.fetchall()
   	con.close()
	return rows

def selectEventNotification(dbname):
	con = lite.connect(dbname)
        cur = con.cursor()
        cur.execute("SELECT id,eventType,eventDescription,ts FROM events WHERE isNotified = 0")
        rows = cur.fetchall()
	cur.execute("UPDATE events SET isNotified = 1 WHERE isNotified = 0")
        con.close()
        return rows
