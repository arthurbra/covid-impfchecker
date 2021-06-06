import json
import os
from time import sleep
import webbrowser
import requests
import tqdm 
import http.client, urllib
import atexit

# Einstellungen
POSTAL_CODE = 30521
CITY = "Hannover"
PUSHOVER_TOKEN = "<TOKEN>"
PUSHOVER_USER = "<USER>"
BIRTHDAY = '419896800000'

###########################

headers = {
    'authority': 'www.impfportal-niedersachsen.de',
    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    'accept': 'application/json, text/plain, */*',
    'authorization': '',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://www.impfportal-niedersachsen.de/portal/',
    'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7,la;q=0.6',
}

params = (
    ('stiko', ''),
    ('count', '1'),
    ('birthdate', BIRTHDAY),
)


def send_push_msg(msg, url=None):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
      urllib.parse.urlencode({
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER,
        "message": msg,
        "priority": 1,
        "url": url
      }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()


def exit_handler():
    send_push_msg("Impfchecker beendet!")

atexit.register(exit_handler)


send_push_msg("Impfchecker läuft!")

def check_free_appointment():
    response = requests.get(f'https://www.impfportal-niedersachsen.de/portal/rest/appointments/findVaccinationCenterListFree/{POSTAL_CODE}', headers=headers, params=params)
    if response.status_code != 200:
        print("Error: " + str(response.status_code))
        return None
    result = json.loads(response.text)
    if result["succeeded"] is not True:
        print("Error: " + str(result))
        return None
    for r in result["resultList"]:     
        if not r["outOfStock"] and CITY in r["city"]:
            return r
    return None

bar = tqdm.tqdm(desc="Trying...")
while True:
    r = check_free_appointment()
    if r is not None:
        # check again to avoid false positives
        sleep(1)
        r = check_free_appointment()
        if r is not None:
            print("Success: " + str(r["vaccineName"]))
            send_push_msg("Impftermin verfügbar: " + str(r["vaccineName"]), url="https://www.impfportal-niedersachsen.de/portal/#/appointment/public")
            sleep(5*60)
        else:
            print("False positive: " + str(r))
    sleep(1)    
    bar.update()

