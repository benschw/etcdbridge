#!/usr/bin/python

import json,os,sys,urllib,urllib2,time
import subprocess
import logging

if "DEBUG" in os.environ:
	logging.basicConfig(level=logging.DEBUG)


def registerService(etcd, serviceId, cid, address, hostName):
	opener = urllib2.build_opener(urllib2.HTTPHandler)
	# headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "application/json"}

	nameData = urllib.urlencode({'value': hostName, 'ttl': 5})
	nameReq = urllib2.Request('http://'+etcd+'/v2/keys/svc/'+serviceId+'/name', nameData)
	nameReq.get_method = lambda: 'PUT'
	opener.open(nameReq)

	addyData = urllib.urlencode({'value': address, 'ttl': 5})
	addyReq = urllib2.Request('http://'+etcd+'/v2/keys/svc/'+serviceId+'/instances/'+cid, addyData)
	addyReq.get_method = lambda: 'PUT'
	opener.open(addyReq)

def stopRegistrar(etcd, serviceId, cid):
	logging.info("unregistering "+cid)

	opener = urllib2.build_opener(urllib2.HTTPHandler)

	sigData = urllib.urlencode({'value': 'exit', 'ttl': 45})
	sigReq = urllib2.Request('http://'+etcd+'/v2/keys/svc/'+serviceId+'/signals/'+cid, sigData)
	sigReq.get_method = lambda: 'PUT'
	opener.open(sigReq)

	delReq = urllib2.Request('http://'+etcd+'/v2/keys/svc/'+serviceId+'/instances/'+cid)
	delReq.get_method = lambda: 'DELETE'
	opener.open(delReq)

def hasExitSignal(etcd, serviceId, cid):
	try: 

		sigResp = urllib2.urlopen('http://'+etcd+'/v2/keys/svc/'+serviceId+'/signals/'+cid)

		if sigResp.code == 200:
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

def keepRegistered(etcd, serviceId, cid, address, hostName, hc):
	while True:
		if not isHealthy(hc):
			return False

		if hasExitSignal(etcd, serviceId, cid):
		    return True

		registerService(etcd, serviceId, cid, address, hostName)

		time.sleep(3)



cid        = os.environ['CONTAINER_ID']
serviceId  = os.environ['SERVICE_ID']
address    = os.environ['APPLICATION_ADDRESS']
hc         = os.environ['HEALTH_CHECK']
etcd       = os.environ['ETCD']

replacing = None
if 'REPLACING' in os.environ:
	replacing = os.environ['REPLACING']


hostName = None
if 'HOST_NAME' in os.environ:
	hostName = os.environ['HOST_NAME']


seconds = 30
if waitForServiceStart(hc, seconds): 

	if initRegistration(etcd, serviceId, cid, address, hostName, replacing):
		logging.info(cid+" started")

		if keepRegistered(etcd, serviceId, cid, address, hostName, hc):
			logging.info("caught signal, exiting")
		else:
			logging.info(cid+" health check failed, exiting")

else:
	logging.info("service "+cid+ "didn't start for "+seconds+" seconds, giving up")


