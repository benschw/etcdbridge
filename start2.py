#!/usr/bin/python

import json,os,sys,urllib,urllib2,time, etcd
import subprocess
import logging

if "DEBUG" in os.environ:
	logging.basicConfig(level=logging.DEBUG)


def registerService(e, serviceId, cid, address, hostName):

	e.set('svc/'+serviceId+'/name', hostName, 5)
	e.set('svc/'+serviceId+'/instances/'+cid, address, 5)


def stopRegistrar(e, serviceId, cid):
	logging.info("unregistering "+cid)

	e.set('svc/'+serviceId+'/signals/'+cid, "exit", 5)
	e.delete('svc/'+serviceId+'/instances/'+cid)


def hasExitSignal(e, serviceId, cid):
	try: 
		e.get('svc/'+serviceId+'/signals/'+cid)
		return True

	except Exception, e:
	    pass

	return False

def isHealthy(hc):
	code = subprocess.call(["/bin/bash", "-c", hc])
	return code == 0



def waitForServiceStart(hc, seconds):

	for i in range(0, seconds):
		logging.info("trying")
		if isHealthy(hc):
			return True

		time.sleep(1)
	return False

def initRegistration(etcd, serviceId, cid, address, hostName, replacing):
	registerService(etcd, serviceId, cid, address, hostName)

	if replacing is not None:
		logging.info("Replacing "+replacing)
		stopRegistrar(etcd, serviceId, replacing)

	return True

def keepRegistered(e, serviceId, cid, address, hostName, hc):
	while True:
		if not isHealthy(hc):
			return False

		if hasExitSignal(e, serviceId, cid):
		    return True

		registerService(e, serviceId, cid, address, hostName)

		time.sleep(3)



cid        = os.environ['CONTAINER_ID']
serviceId  = os.environ['SERVICE_ID']
address    = os.environ['APPLICATION_ADDRESS']
hc         = os.environ['HEALTH_CHECK']
etcdAdd    = os.environ['ETCD'].split(":")
etcdHost   = etcdAdd[0]
etcdPort   = etcdAdd[1]



replacing = None
if 'REPLACING' in os.environ:
	replacing = os.environ['REPLACING']


hostName = None
if 'HOST_NAME' in os.environ:
	hostName = os.environ['HOST_NAME']


e = etcd.Etcd(host=etcdHost, port=etcdPort)

seconds = 30
if waitForServiceStart(hc, seconds): 

	if initRegistration(e, serviceId, cid, address, hostName, replacing):
		logging.info(cid+" started")

		if keepRegistered(e, serviceId, cid, address, hostName, hc):
			logging.info("caught signal, exiting")
		else:
			logging.info(cid+" health check failed, exiting")

else:
	logging.info("service "+cid+ "didn't start for "+seconds+" seconds, giving up")


