#!/usr/bin/python3
import requests
from telethon import TelegramClient, events, sync

# Remember to use your own values from my.telegram.org!
api_id = 
api_hash = ''
client = TelegramClient('alerts', api_id, api_hash)
pattern = '(?i)^(?!.*DOWN\/)(?!.*UP\/).*\/USDT.*'

def SendToDiscord(ticker,url):
    ticker = ticker.split("\n")[0]
    data = {"content": ticker}
    requests.post(url, json=data)

@client.on(events.NewMessage(chats='Hodloo Binance 10%',pattern=pattern))
async def binance10_event_handler(event):
    url = ""
    SendToDiscord(event.raw_text, url)

@client.on(events.NewMessage(chats='Hodloo Binance 5%',pattern=pattern))
async def binance5_event_handler(event):
    url = ""
    SendToDiscord(event.raw_text, url)

client.start()
client.get_dialogs()
client.run_until_disconnected()
