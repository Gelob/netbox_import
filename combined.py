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

driver = get_network_driver("junos")

# generate API token at https://netbox.mydomain.com/user/api-tokens
token = ""
baseURI = "https://netbox.mydomain.com/api"

headers = {"Accept": "application/json", "Authorization": "Token " + token}

interface_bl = {
    "ut-0/0/0",
    "pfh-0/0/0",
    "pfe-0/0/0",
    "pd-0/0/0",
    "ip-0/0/0",
    "lt-0/0/0",
    "lc-0/0/0",
    "ud-0/0/0",
    "vt-0/0/0",
    "mt-0/0/0",
    "pe-0/0/0",
    "lsi",
    "em0",
    "lo0",
    "pime",
    "esi",
    ".local.",
    "pimd",
    "tap",
    "gre",
    "demux0",
    "ipip",
    "pip0",
    "irb",
    "dsc",
    "mtun",
    "vtep",
    "em1",
    "cbp0",
    "jsrv",
    "pp0",
    "bme0",
}

devices = ["DEVICE1"]


def interface_lookup(interface, device):
    ilookup = "%s/dcim/interfaces/?name=%s&device=%s" % (baseURI, interface, device)
    r = requests.get(ilookup, headers=headers, verify=False)
    json = r.json()
    if json["count"] == 1:
        instance = json["results"][0]
        return instance["id"]
    elif json["count"] == 0:
        return False
    else:
        raise Exception(
            "The mentioned interface does not exist on this device or returned more than 1 result"
        )


def interface_add(interface, device_id, enable):
    iadd = "%s/dcim/interfaces/" % (baseURI)
    data = {}
    data["name"] = interface
    data["device"] = device_id
    data["enabled"] = enable
    r = requests.post(iadd, headers=headers, verify=False, data=data)
    json = r.json()
    if r.status_code != 201:
        raise Exception("Failed to add interface")
    else:
        return json["id"]


def ipaddress_lookup(ip, device):
    ilookup = "%s/ipam/ip-addresses/?q=%s&device=%s" % (baseURI, ip, device)
    r = requests.get(ilookup, headers=headers, verify=False)
    json = r.json()
    if json["count"] == 1:
        instance = json["results"][0]
        return instance["id"]
    elif json["count"] == 0:
        return False
    else:
        raise Exception(
            "The mentioned ip address does not exist on this device or returned more than 1 result"
        )


def ipaddress_add(address, interface_id, vrf_id, status):
    ipadd = "%s/ipam/ip-addresses/" % (baseURI)
    data = {}
    data["address"] = address
    data["interface"] = interface_id
    data["vrf"] = vrf_id
    data["status"] = status
    r = requests.post(ipadd, headers=headers, verify=False, data=data)
    json = r.json()
    if r.status_code != 201:
        return False
        raise Exception("Failed to add ip address")
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
        raise Exception(
            "The mentioned device does not exist or returned more than 1 result"
        )


# Loop through all the above devices
for device in devices:
    try:
        device_id = device_lookup(device)
        # lookup the device id
    except Exception as e:
        print(e)
        print(device)
    dev = driver(hostname=device, username="", password="")
    dev.open()
    interfaces = dev.get_interfaces_ip()  # query the device for its ip addresses
    dev.close()
    data = {}
    data2 = {}
    # Loop through all of the ip addresses returned
    for key, value in interfaces.items():
        # Check if the interface is in the above blacklist
        if re.sub("\.[0-9]+", "", key) not in interface_bl:
            data["status"] = 1
            # Strip out juniper units
            data["name"] = re.sub("\\.\d\\b", "", key)
            # Loop through the returned ip address/CIDR sets
            for key, value in value["ipv4"].items():
                # Merge the IP and CIDR block together
                data["address"] = str(key) + "/" + str(value["prefix_length"])
                addr = ipaddress.IPv4Address(key)
                # Check if IP address is private and set VRF accordingly
                if addr.is_private:
                    #            if addr in ipaddress.ip_network('10.0.0.0/29'):
                    #              data['vrf'] = 3 #vrf-3
                    #            else:
                    data["vrf"] = 2  # vrf-2
                else:
                    data["vrf"] = 1  # vrf-1
                interface = data["name"]
                # Check if interface exists and if not add it
                # Add IP address # TODO Check if in use or assigned to something else
                if interface_lookup(interface, device):
                    data["interface"] = interface_lookup(interface, device)
                    if not ipaddress_lookup(data["address"], device):
                        if not ipaddress_add(
                            data["address"],
                            data["interface"],
                            data["vrf"],
                            data["status"],
                        ):
                            fail = "failed to add: {} to {} on {}"
                            print(fail.format(data["address"], interface, device))
                    else:
                        fail = "FAILED: {} already exists in netbox"
                        print(fail.format(data["address"]))
                else:
                    data["interface"] = interface_add(interface, device_id, "true")
                    if not ipaddress_add(
                        data["address"], data["interface"], data["vrf"], data["status"]
                    ):
                        fail = "failed to add: {} to {} on {}"
                        print(fail.format(data["address"], interface, device))
