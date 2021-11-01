import requests
from py3cw.request import Py3CW
import config
from telethon import TelegramClient, events, sync

###
### Functions
###

def SendToDiscord(string,url):
    string = string.split("\n")[0]
    data = {"content": string}
    requests.post(url, json=data)

def send_buy_trigger_5(pair):
    pair = ("USDT_" + pair.replace("/USDT","")).split("\n")[0]
    error, deal = p3cw.request(
        entity = 'bots',
        action = 'start_new_deal',
        action_id = config.BOT_ID_5,
        payload={
            "pair": pair
        }
    )
    if not error:
        SendToDiscord(f"Started deal for pair {pair} 5% under the base",config.BINANCE_5_WEBHOOK)

def send_buy_trigger_10(pair):
    pair = ("USDT_" + pair.replace("/USDT","")).split("\n")[0]
    error, deal = p3cw.request(
        entity = 'bots',
        action = 'start_new_deal',
        action_id = config.BOT_ID_10,
        payload={
            "pair": pair
        }
    )
    if not error:
        SendToDiscord(f"Started deal for pair {pair} 10% under the base",config.BINANCE_10_WEBHOOK)

###
### Main script
###

# Connect to 3Commas
p3cw = Py3CW(
    key=config.TC_API_KEY,
    secret=config.TC_API_SECRET,
    request_options={
        'request_timeout': 30,
        'nr_of_retries': 1,
        'retry_status_codes': [502],
        'Forced-Mode': config.MODE
    }
)

# Initialize Telegram
client = TelegramClient('alerts', int(config.TELEGRAM_API_ID), config.TELEGRAM_API_HASH)

@client.on(events.NewMessage(chats='Hodloo Binance 10%',pattern=config.PATTERN))
async def binance10_event_handler(event):
    url = config.BINANCE_10_WEBHOOK
    SendToDiscord(event.raw_text, url)
    send_buy_trigger_10(event.raw_text)

@client.on(events.NewMessage(chats='Hodloo Binance 5%',pattern=config.PATTERN))
async def binance5_event_handler(event):
    url = config.BINANCE_5_WEBHOOK
    SendToDiscord(event.raw_text, url)
    send_buy_trigger_5(event.raw_text)

client.start()
client.get_dialogs()
client.run_until_disconnected()
