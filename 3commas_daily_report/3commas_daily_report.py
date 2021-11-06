from py3cw.request import Py3CW
import config
from datetime import datetime, timedelta
import requests
import pandas as pd

def send_to_discord(string,url):
    data = {"content": string}
    requests.post(url, json=data)

print(f"{datetime.now().replace(microsecond=0)} - Connecting to 3Commas")
p3cw = Py3CW(
    key=config.TC_API_KEY,
    secret=config.TC_API_SECRET,
    request_options={
        'request_timeout': 30,
        'nr_of_retries': 1,
        'retry_status_codes': [502],
        'Forced-Mode': config.TC_MODE
    }
)

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
today = (datetime.now()).strftime('%Y-%m-%d')

list_of_dicts=[]
for account in config.TC_ACCOUNTS:   
    error1, balance = p3cw.request(
                entity = 'accounts',
                action = 'load_balances',
                action_id = account,
    )

    error2, historical_balance = p3cw.request(
                entity = 'accounts',
                action = 'balance_chart_data',
                action_id = account,
                payload={
                    "date_from":yesterday,
                    "date_to":today
                }
    )
    if not error1 or error2:
        amount_yesterday = float(historical_balance[0]["usd"]) # 0 = yesterday, 1 = today midnight, 2 = now
        amount_today = float(historical_balance[1]["usd"])
        gain_amount = amount_today - amount_yesterday 
        thisdict = {
        "Name": balance["name"],
        "Exchange": balance["exchange_name"],
        "USD": round(float(historical_balance[1]["usd"]),0),
        "Gain USD": round(gain_amount,0),
        "Gain %": round(100*(amount_today - amount_yesterday) / amount_yesterday,2)
        }
        list_of_dicts.append(thisdict)
    else:
        if error1:
            error = error1
            send_to_discord(f"Error fetching data from 3Commas\n```\n{error}\n```",config.DISCORD_NOTIFICATIONS)
            raise Exception(error)
        else:
            error = error2
            send_to_discord(f"Error fetching data from 3Commas\n```\n{error}\n```",config.DISCORD_NOTIFICATIONS)
            raise Exception(error)

        

df = pd.DataFrame(list_of_dicts, columns=['Name', 'Exchange','USD', 'Gain USD', 'Gain %']) 
send_to_discord(df.to_string(index=False),config.DISCORD_NOTIFICATIONS)
