# Pre-calculated phone numbers hash map

## Installation

**Tested on: Ubuntu 18.04**

Install dependencies

```
sudo apt update
sudo apt install postgresql apache2 apache2-utils php php-pgsql libapache2-mod-php libpq5 postgresql postgresql-client postgresql-client-common postgresql-contrib python python-pip python-pip postgresql-server-dev-all
sudo pip install psycopg2
```

Prepare database

```
sudo -u postgres psql < db_init.sql
```

Place lookup script into webserver directory:

```
cp map_hash_num.php /var/www/html/
```


Fill database with hashes for phone numbers range with your favourite prefix (e.g. +12130000000 -> +12139999999)

```
python ./hashmap_gen.py 1213
```

## Usage

Now you can get mobile phones by 3 bytes of SHA256(phone_number) this way:

```
http://127.0.0.1/map_hash_num.php?hash=112233
```

![ph_candidates](img/hash_api.png)
