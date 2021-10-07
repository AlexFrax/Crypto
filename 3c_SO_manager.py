import requests
import os
import json
import sys
from py3cw.request import Py3CW

###
### Variables. Do edit.
###

# 3Commas API info
# BOTS_READ permissions are mandatory
# BOTS_WRITE permissions are only needed if you want to adjust the take profit value
API_Key = ''
API_Secret = ''
account_id = ''

# Discord webhook for notifications
DiscordWebhook = ''

# Adjust TP, too?
adjust_TP = True # Can be True or False

# Adjust TP percentages when SO is completed
TPSO5 = 3 # Safety order 5
TPSO6 = 7 # Safety order 6
TPSO7 = 10 # Safety order 7

# Trailing settings
trailing_enabled = False
trailing_deviation = 0

###
### Functions. Do not edit.
###

def SendToDiscord(string,url):
    data = {"content": string}
    requests.post(url, json=data)

def AdjustTP(deal_id,tp):
    error, data = p3cw.request(
        entity='deals',
        action='update_deal',
        action_id=str(deal_id),
        payload = {
            "take_profit": tp,
            "deal_id": str(deal_id),
            "trailing_enabled": trailing_enabled,
            "trailing_deviation": trailing_deviation
        }
    )

def check_deal_id(deal_id,file_path):
    with open(file_path, 'r') as f:
        datafile = f.readlines()
    for line in datafile:
        if deal_id in line:
            f.close()
            return True
    f.close()
    return False

def store_deal_id(deal_id,file_path):
    with open(file_path, mode='a') as f:
        f.write(deal_id + '\n')
        f.close()

###
### Main script. Do not edit.
###
p3cw = Py3CW(
    key=API_Key,
    secret=API_Secret,
    request_options={
        'request_timeout': 10,
        'nr_of_retries': 1,
        'retry_status_codes': [502]
    }
)
    
error, deals = p3cw.request(
    entity='deals',
    action='',
    payload = {
        "scope": "active",
        "account_id": account_id
    }
)

# Create id storage file if it does not exist
dir_path = os.path.dirname(os.path.realpath(__file__))
file_name = 'deal_ids.txt'
file_path = os.path.join(dir_path, file_name)
if not os.path.exists(file_path):
    open(file_path, 'a').close()

DiscordText = ""
for deal in deals:
    if deal["status"] == "bought":
        deal_id = deal["id"]
        deal_name = deal["bot_name"]
        deal_current_so = deal["completed_safety_orders_count"]

        if int(deal_current_so) >= 4:
            if check_deal_id(str(deal_id),file_path) == False:
                DiscordText = DiscordText + str(deal_id) + ', ' + str(deal_name) + ', ' + str(deal_current_so) + '\n'
                store_deal_id(str(deal_id),file_path)
            if adjust_TP == True:
                if deal_current_so == 5:
                    AdjustTP(deal_id,TPSO5)
                if deal_current_so == 6:
                    AdjustTP(deal_id,TPSO6)
                if deal_current_so == 7:
                    AdjustTP(deal_id, TPSO7)

if DiscordText != "":
    SendToDiscord(DiscordText,DiscordWebhook)
