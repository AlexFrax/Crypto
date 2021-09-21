import requests
from telethon import TelegramClient, events, sync

###
### Variables
###
api_id = 
api_hash = ''
binance_10_webhook = ''
binance_5_webhook = ''

# Only include USDT pairs but exclude anything with "DOWN/" or "UP/" in the name aka Binance Leveraged Tokens.
# Valid pair examples: ADA/USDT, LINK/USDT and so on
# Non-valid pairs: ADADOWN/USDT, ADA/BUSD, LINK/ETH, LINK/BTC and so on
pattern = '(?i)^(?!.*DOWN\/)(?!.*UP\/).*\/USDT.*'

###
### Main script
###
client = TelegramClient('alerts', api_id, api_hash)

def SendToDiscord(ticker,url):
    ticker = ticker.split("\n")[0]
    data = {"content": ticker}
    requests.post(url, json=data)

@client.on(events.NewMessage(chats='Hodloo Binance 10%',pattern=pattern))
async def binance10_event_handler(event):
    url = binance_10_webhook
    SendToDiscord(event.raw_text, url)

@client.on(events.NewMessage(chats='Hodloo Binance 5%',pattern=pattern))
async def binance5_event_handler(event):
    url = binance_5_webhook
    SendToDiscord(event.raw_text, url)

client.start()
client.get_dialogs()
client.run_until_disconnected()
