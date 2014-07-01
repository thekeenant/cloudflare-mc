#!/usr/bin/env python

import json
import urllib
import time
import random
import socket
import struct

# # # # # # # # #
# Configuration #
# # # # # # # # #

# Account Info: https://www.cloudflare.com/my-account
API      = ''
EMAIL    = 'someone@example.com'

# Subdomain of the website to load balance
RECORD   = 'lb' # where you want the load balancer

# Your Cloudflare Domain
DOMAIN   = 'domain.com'

# Load balance IPs, will ping these and add all live results.
HOSTS    = [
            ['127.0.0.1', 'A'],
            ['127.0.0.2', 'A']
           ]
PORT     = 25565

# TTL and interval to ping server health
TTL      = 1
INTERVAL = 60
 
# # # # # 
# Code! #
# # # # #

RECS = []

def unpack_varint(s):
    d = 0
    for i in range(5):
        b = ord(s.recv(1))
        d |= (b & 0x7F) << 7*i
        if not b & 0x80:
            break
    return d
 
def pack_varint(d):
    o = ""
    while True:
        b = d & 0x7F
        d >>= 7
        o += struct.pack("B", b | (0x80 if d > 0 else 0))
        if d == 0:
            break
    return o
 
def pack_data(d):
    return pack_varint(len(d)) + d
 
def pack_port(i):
    return struct.pack('>H', i)
 
def get_info(host='localhost', port=25565):
 
    # Connect
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
 
    # Send handshake + status request
    s.send(pack_data("\x00\x00" + pack_data(host.encode('utf8')) + pack_port(port) + "\x01"))
    s.send(pack_data("\x00"))
 
    # Read response
    unpack_varint(s)     # Packet length
    unpack_varint(s)     # Packet ID
    l = unpack_varint(s) # String length
 
    d = ""
    while len(d) < l:
        d += s.recv(1024)
 
    # Close our socket
    s.close()
 
    # Load json and return
    return json.loads(d.decode('utf8'))

def call_api(params):
    go = urllib.urlopen("https://www.cloudflare.com/api_json.html", params)
    return go.read()
    
def get_recs():
    print "\nGetting data from CloudFlare"
    rec = json.loads(call_api(urllib.urlencode({'a': 'rec_load_all', 'tkn': API, 'email': EMAIL, 'z': DOMAIN})))
    if rec['result'] == "success":
        return rec['response']['recs']['objs']
    else:
        return False
        
def del_rec(rec_id, host):
    result = json.loads(call_api(urllib.urlencode({'a': 'rec_delete', 'tkn': API, 'email': EMAIL, 'z': DOMAIN, 'id': rec_id})))
    if result['result'] == 'success':
        print 'Removing:' +host
    else:
        print 'Remove Failed: '+host+'. '+result['msg']
        
def add_rec(rec):
    result_add = json.loads(call_api(urllib.urlencode({'a': 'rec_new', 'tkn': API, 'email': EMAIL, 'z': DOMAIN, 'name': RECORD, 'content': rec[0], 'type': rec[1], 'ttl': 1})))
    if result_add['result'] == 'success':
        result_edit = json.loads(call_api(urllib.urlencode({'a': 'rec_edit', 'tkn': API, 'email': EMAIL, 'z': DOMAIN, 'name': RECORD, 'content': rec[0], 'type': rec[1], 'ttl': 1, 'id': result_add['response']['rec']['obj']['rec_id'], 'service_mode': 0})))
        if result_edit['result'] == 'success':
            print 'Adding: '+rec[0]
            return True
        else:
            del_rec(result_add['response']['rec']['obj']['rec_id'], rec) #faild to orange cloud
            print "Add Failed: "+rec[0]+". "+result_edit['msg']
            return False
    
    print 'Add Failed: '+rec[0]+'. '+result_add['msg']
    return False

def healthcheck(host):
    try:
        result = get_info(host[0], PORT)
        if get_rec_id(RECORD, host[0]) == False: #needs to be added
            add_rec(host)
        else:
            print host[0]+': Passed'
    except: #we were not able to do what was needed
        rec_id = get_rec_id(RECORD, host[0]) #get the id of the record
        if rec_id != False:
            del_rec(rec_id, host[0])
        else:
            print host[0]+': Still dead'
            
def get_rec_id(name, host):
    for y in RECS:
        if y['display_name'] == name and y['content'] == host and (y['type'] == "A" or y['type'] == "AAAA"):
            return y['rec_id']
    return False

if __name__=="__main__":
    while True:
        RECS, start_time = get_recs(), time.time()
        random.shuffle(HOSTS)
        
        for host in HOSTS:
            healthcheck(host)
        
        if INTERVAL >= 0:
            lapse = int(time.time() - start_time)
            print "DONE: sleeping for "+str(INTERVAL-lapse)+" seconds"
            time.sleep(INTERVAL-lapse) #sleep for some set time seconds
        else:
            exit()

