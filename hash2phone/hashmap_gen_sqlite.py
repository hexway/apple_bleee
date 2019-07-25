#!/usr/bin/env python3
#
# Generating 3 first-bytes sha256 of
# phones number given a specific range
# and storing into an sqlite3 DB
# 
# -- gelim

from hashlib import sha256
import sqlite3
import sys


db_file = 'phones.db'
sql_drop = 'DROP TABLE IF EXISTS map'
sql_create = 'CREATE TABLE map (id integer primary key, hash text, phone integer)' # saving up to 20% with integer for phones
sql_insert = 'INSERT INTO map (hash, phone) VALUES (?, ?)'


if len(sys.argv) != 2:
    progname = sys.argv[0]
    print('''Usage: %s dbinit
will initialize the sqlite3 phone hash database (can takes some time)

%s phonemask
Example: %s 336XXXXXXXX
for generating hashes for numbers starting from 33600000000 up to 33699999999

You can as well use space or hyphen char as you wish, like:
- 336 XX XX XX XX (French mobile number)
- 1 408-XXX-XXXX (would be a landline Cupertino area)
''' % (progname, progname, progname))
    exit(0)

conn = sqlite3.connect(db_file)
c = conn.cursor()

if sys.argv[1] == 'test':
    c.execute("SELECT phone FROM map WHERE hash='56d5a1'")
    phones = c.fetchall()
    for p in phones: print(str(p[0]))
    exit(0)
    
if sys.argv[1] == 'dbinit':
    c.execute(sql_drop)
    c.execute(sql_create)
    conn.commit()
    conn.close()
    exit(0)

phonemask = sys.argv[1]
phonemask = phonemask.replace(' ', '').replace('-', '')
phone_start = int(phonemask.replace('X', '0'))
phone_stop = int(phonemask.replace('X', '9'))
percentile = (phone_stop - phone_start + 1) / 100

phones_temp = list()

for num in range(phone_start, phone_stop + 1):
    hashp = sha256(str(num).encode('latin1')).hexdigest()[:6]
    phones_temp.append((hashp, num))

    if num % percentile == 0:
        print("\r%d%% completed" % int(100 - (phone_stop-num)/percentile), end="")
        c.executemany(sql_insert, phones_temp)
        phones_temp = list()
conn.commit()
conn.close()
print()
