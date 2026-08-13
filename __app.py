import os, re, importlib, time, string, random, sys
import json  # Import json for proper JSON serialization
from celery import Celery
from flask import Flask, request, Response, jsonify, send_from_directory, abort
from celery.events import EventReceiver
from kombu import Connection
import redis
import mysql.connector
from datetime import datetime
from kombu.utils.json import loads
from sites.spokeocom import spokeocom

def get_website_name(filename):
    replacements = {
        r"(comus|comeu|com)$": ".com",
        r"(neteu|netus|net)$": ".net",
        r"(orgeu|orgus|org)$": ".org",
        r"(gov)$": ".gov",
        r"(io)$": ".io",
        r"(info)$": ".info",
        r"(ai)$": ".ai",
        r"(us)$": ".us",
        r"(run)$": ".run",
        r"(pro)$": ".pro",
        r"(co)$": ".co"
    }
    for pattern, replacement in replacements.items():
        if re.search(pattern, filename):
            return re.sub(pattern, replacement, filename)
    return filename


if __name__ == "__main__":
    # dataRow = { 
    #     "Verification Email": "webremovals@privacypros.com", 
    #     "User Email": "bkobe@american.edu", 
    #     "Title": "Ms.", 
    #     "Name": "Bryce Kobe", 
    #     "Age": 29, 
    #     "Birth Day": "14", 
    #     "Birth Month": "12", 
    #     "Birth Year": 1995, 
    #     "Address": "f4330 Old Virginia street, Roanoke, Virginia 24019", 
    #     "Area Code": 540, 
    #     "Phone Number": "5405105709", 
    #     "Street": "4330 Old Virginia street", 
    #     "Apartment": "", 
    #     "City": "Haslett", 
    #     "State": "Michigan", 
    #     "Zipcode": 24019, 
    #     "County": "Haslett County", 
    #     "Advertising Id": "", 
    #     "Job Title": "", 
    #     "Business Name": "", 
    #     "LinkedIn Profile": "", 
    #     "Status": "" 
    # }

    dataRow = { 
        "Verification Email": "webremovals@privacypros.com", 
        "User Email": "daliaj019@gmail.com", 
        "Title": "Ms.", 
        "Name": "Erika Chin",
        "Age": 29, 
        "Birth Day": "", 
        "Birth Month": "", 
        "Birth Year": "1995", 
        "Address": "f4330 Old Virginia street, Roanoke, Virginia 24019", 
        "Area Code": 540, 
        "Phone Number": "5405105709", 
        "Street": "4330 Old Virginia street", 
        "Apartment": "", 
        "City": "Roanoke", 
        "State": "Virginia", 
        "Zipcode": 24019, 
        "County": "Roanoke County", 
        "Advertising Id": "", 
        "Job Title": "", 
        "Business Name": "", 
        "LinkedIn Profile": "", 
        "Status": "" 
    }
    
    screenshot_save_path = spokeocom(dataRow, "website", dataRow["User Email"], run_mode="non-headless")
    print(screenshot_save_path)

    # now = datetime.datetime.now()
    # current_date = now.strftime("%Y-%m-%d")
    # base_dir = os.getcwd()

    # screentShotDir = os.path.join(base_dir, "ScreenShot", current_date)
    # screenshot_save_path = screentShotDir + "\usaofficialcom_" + "Aaaaa" + ".png"
    # do_email_verification("American City Business Journals", screenshot_save_path)

    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # for filename in os.listdir(current_dir):
    #     if filename.endswith(".py") and filename not in ["app.py", "__init__.py"]:
    #         module_name = filename[:-3]
    #         website_name = get_website_name(module_name)
    #         print(website_name)