#!/usr/bin/python
import ConfigParser
def ConfigSectionMap(file,section):
	config = ConfigParser.ConfigParser()
	config.read(file)
	r = {}
    	options = config.options(section)
    	for option in options:
        	try:
            		r[option] = config.get(section, option)
        	except:
            		print("exception on %s!" % option)
            		r[option] = None
    	return r

def ConfigSectionMapToInt(file,section):
        config = ConfigParser.ConfigParser()
        config.read(file)
        r = {}
        options = config.options(section)
        for option in options:
                try:
                        r[option] = config.getint(section, option)
                except:
                        print("exception on %s!" % option)
                        r[option] = None
        return r

def ConfigOptionMap(file,section,option):
	config = ConfigParser.ConfigParser()
        config.read(file)
	try:
		r = config.get(section,option)
	except:
		print("exception on %s!" % option)
		r = None
	return r
