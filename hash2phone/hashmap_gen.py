#!/usr/bin/env python2

# web: https://hexway.io
# Twitter: https://twitter.com/_hexway


#yeah, this is just PoC

from __future__ import print_function
import sys
import hashlib
import psycopg2

if len(sys.argv)!=2:
	print("\nUsage:\t",sys.argv[0],"<4-digit phone prefix>")
	print("\nEx.:Calculate hashmap for range +12130000000 -- +12139999999:")
  print(sys.argv[0],"1213")
	print("\n\n");
	sys.exit()


prefix = sys.argv[1]
num=int(prefix+"0000000")
stop_num=num+10000000

connection = psycopg2.connect(user="lookup",
                              password="h3xwayp4ssw0rd", #you can change it if you want
                              host="127.0.0.1",
                              port="5432",
                              database="phones")
cursor = connection.cursor()

postgres_insert_query = """ INSERT INTO map (hash, phone) VALUES (%s, %s)"""


while num < stop_num :

    if num % 100000 is 0:
        print(100-(stop_num-num)/100000,"% complete")
        connection.commit()
    strnum = str(num)
    m = hashlib.sha256()
    m.update(strnum)
    hash= m.digest().encode("hex")[0:6]

    record_to_insert = ("\\x"+hash, strnum)
    cursor.execute(postgres_insert_query, record_to_insert)



    num +=1
connection.commit()
print("last num:\t", strnum)
print("done!")

