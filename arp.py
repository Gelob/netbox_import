#!/opt/rh/rh-python35/root/usr/bin/python3.5
import sys
import json
import requests
import re
import ipaddress
from requests.packages.urllib3.exceptions import InsecurePlatformWarning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3.exceptions import SNIMissingWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
requests.packages.urllib3.disable_warnings(SNIMissingWarning)
from napalm import get_network_driver

driver = get_network_driver('eos')

#generate API token at https://netbox.mydomain.com/user/api-tokens
token = ''
baseURI = "https://netbox.mydomain.com/api"

headers = {'Accept':'application/json','Authorization': 'Token ' + token}

devices = ["DEVICE1", "DEVICE2"]

def interface_lookup(interface,device):
     ilookup = "%s/dcim/interfaces/?name=%s&device=%s" % (baseURI, interface, device)
     r = requests.get(ilookup, headers=headers, verify=False)
     json = r.json()
     if json["count"] == 1:
       instance = json["results"][0]
       return instance["id"]
     elif json["count"] == 0:
       return False
     else:
       raise Exception('The mentioned interface does not exist on this device or returned more than 1 result')

def ipaddress_lookup(ip):
     ilookup = "%s/ipam/ip-addresses/?q=%s/" % (baseURI, ip)
     r = requests.get(ilookup, headers=headers, verify=False)
     json = r.json()
     if json["count"] == 1:
       instance = json["results"][0]
       return instance["id"]
     elif json["count"] == 0:
       return False
     else:
       raise Exception('The mentioned ip address does not exist or returned more than 1 result')

def vm_macaddress_lookup(mac):
     mlookup = "%s/virtualization/interfaces/?mac_address=%s" % (baseURI, mac)
     r = requests.get(mlookup, headers=headers, verify=False)
     json = r.json()
     if json["count"] == 1:
       instance = json["results"][0]
       return instance["virtual_machine"]["id"]
     elif json["count"] == 0:
       return False
     else:
       raise Exception('The mentioned mac address does not exist  or returned more than 1 result')

def devices_macaddress_lookup(mac):
     mlookup = "%s/dcim/devices/?mac_address=%s" % (baseURI, mac)
     r = requests.get(mlookup, headers=headers, verify=False)
     json = r.json()
     if json["count"] == 1:
       instance = json["results"][0]
       return instance["id"]
     elif json["count"] == 0:
       return False
     else:
       raise Exception('The mentioned mac address does not exist  or returned more than 1 result')

def ipaddress_add(address,interface_id,vrf_id,status):
    ipadd = "%s/ipam/ip-addresses/" % (baseURI)
    data = {}
    data['address'] = address
    data['interface'] = interface_id
    data['vrf'] = vrf_id
    data['status'] = status
    r = requests.post(ipadd, headers=headers, verify=False, data=data)
    json = r.json()
    if r.status_code != 201:
      return False
      raise Exception('Failed to add ip address')
    else:
      return json["id"]

def device_lookup(device):
    dlookup = "%s/dcim/devices/?name=%s" % (baseURI, device)
    r = requests.get(dlookup, headers=headers, verify=False)
    json = r.json()
    if json["count"] == 1:
      instance = json["results"][0]
      return instance["id"]
    else:
      raise Exception('The mentioned device does not exist or returned more than 1 result')

def device_lookup_by_id(id):
    dlookup = "%s/dcim/devices/?id__in=%s" % (baseURI, id)
    r = requests.get(dlookup, headers=headers, verify=False)
    json = r.json()
    if json["count"] == 1:
      instance = json["results"][0]
      return instance["name"]
    elif json["count"] == 0:
       return False
    else:
       raise Exception('The mentioned mac address does not exist  or returned more than 1 result')

def vm_lookup(id):
    vlookup = "%s/virtualization/virtual-machines/%s/" % (baseURI, id)
    r = requests.get(vlookup, headers=headers, verify=False)
    json = r.json()
    if json["count"] == 1:
      instance = json["results"][0]
      return instance["name"]
    else:
      raise Exception('The mentioned device does not exist or returned more than 1 result')

# Loop through all the above devices
for device in devices:
   try:
     print("Trying to lookup %s" % (device))
     device_id = device_lookup(device); # lookup the device id
   except Exception as e:
    print(e)
    print(device)
   dev = driver(hostname=device, username='',
             password='')
   dev.open()
   arpt = dev.get_arp_table() # query the device for its ip addresses
   dev.close()
   data = {}
   data2 = {}
# Loop through all of the ip addresses returned
   for key in arpt:
     try:
       if ipaddress_lookup(key['ip']):
         pass
       elif vm_macaddress_lookup(key['mac']):
         vm = vm_lookup(vm_macaddress_lookup(key['mac']))
         mac_url = 'http://macvendors.co/api/%s' % (key['mac'])
         r = requests.get(mac_url)
         json = r.json()
         fail = "Couldn't find {} ({}) in netbox, but found {} ({}) on {}"
         print(fail.format(key['ip'],key['interface'],key['mac'], json['result']['company'], vm))
       elif devices_macaddress_lookup(key['mac']):
         device = device_lookup_by_id(devices_macaddress_lookup(key['mac']))
         mac_url = 'http://macvendors.co/api/%s' % (key['mac'])
         r = requests.get(mac_url)
         json = r.json()
         fail = "Couldn't find {} ({}) in netbox, but found {} ({}) on {}"
         print(fail.format(key['ip'],key['interface'],key['mac'], json['result']['company'], device))
       else:
         mac_url = 'http://macvendors.co/api/%s' % (key['mac'])
         r = requests.get(mac_url)
         json = r.json()
         fail = "Couldn't find {} ({}) or {} ({}) in netbox"
         print(fail.format(key['ip'],key['interface'],key['mac'], json['result']['company']))
     except KeyboardInterrupt:
        break
     except:
        fail = "{} returned more than 1 result in Netbox, ignoring."
        print(fail.format(key['ip']))
