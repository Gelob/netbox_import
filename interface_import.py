#!/usr/bin/python
import sys
import json
import requests
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
}

devices = ["DEVICE1", "DEVICE2"]

for device in devices:
    dlookup = "%s/dcim/devices/?name=%s" % (baseURI, device)
    r = requests.get(dlookup, headers=headers, verify=False)

    json = r.json()

    if json["count"] == 1:
        instance = json["results"][0]
        id = instance["id"]
    dev = driver(hostname=device, username="", password="")
    dev.open()
    interfaces = dev.get_interfaces()
    dev.close()
    data = {}
    iadd = "%s/dcim/interfaces/" % (baseURI)
    for key, value in interfaces.items():
        if key not in interface_bl:
            data["name"] = key
            data["device"] = id
            data["enabled"] = "true"
            #        print(data)
            r = requests.post(iadd, headers=headers, verify=False, data=data)
            if r.status_code != 201:
                print("error" + str(r.status_code))
            else:
                success = "added {} successfully on {}"
                print(success.format(data["name"], device))
        else:
            pass
