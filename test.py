# manage.py
import time
import mysql.connector
import logging
from __removal import removal
logging.getLogger('engineio').setLevel(logging.ERROR)

def process_groups_removal():
    removal(
        False, #socketio,
        "achcoopcom", #row['target_domain'], 
        "site_url", #row['site_url'],
        "id", #row['id'], 
        "user_id", #row['user_id'], 
        "email@gmail.com", #row['email'], 
        "Michael", #row['firstname'], 
        "ab", #row['lastname'], 
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        ""
    )

process_groups_removal()