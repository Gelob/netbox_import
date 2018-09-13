# netbox-import
Random quick and dirty scripts to help import data into netbox

This is a set of scripts that utilize [napalm](https://github.com/napalm-automation/napalm) to query network devices, gather data, and import it into netbox.

## Notes
I intended to clean these up but never got around to it. I take no responsbility if something goes wrong when you run them.

## Configuration
You need to change the driver manually to match your device type, such as junos, eos, ios. You can find a list of NAPALM driver names [here](https://napalm.readthedocs.io/en/latest/support/index.html).

You need to set the username and password for the devices manually in the script.

The script assumes there is a device created in Netbox already with the same exact name you supplied in the list of devices. You will need to be able to resolve those names, hardcode them in your hosts file if they don't already resolve.

If you use VRFs look at line 116 in combined.py, set the VRF you want properly or add more logic if needed. Remove that section if needed

## Bugs
In interfaces_import.py Juniper vlans get imported as just "vlan" and not vlan.247, etc. This works as expected in combined.py but not in interfaces_import.py

## Requirements
* Python3.5+
* napalm (pip3 install napalm)

### interface_import.py
This script queries your network device(s) using the napalm command _get_interfaces_. It strips out useless interfaces on Juniper devices and then imports the remaining ones into Netbox using the API. It has been tested on JunOS and EOS devices, but should work with any device that works with napalm.

### ipaddress_import.py
This script queries your network device(s) using the napalm command _get_interfaces_ip_. It strips out useless interfaces on Juniper devices, removes the unit designation from them and then imports the remaining ones into Netbox using the API. It detects if an IP address is private or not and selects the appliance VRF using hardcoded IDs. It has been tested on JunOS and EOS devices, but should work with any device that works with napalm.

### combined.py
This script combines the two above scripts into one and uses functions which gives us some better error handling.

## TODO
* Better error handling
* ~~Combine both scripts~~
* Detect device type