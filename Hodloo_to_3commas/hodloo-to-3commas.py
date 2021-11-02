import websockets
import json
import asyncio
import requests
import re
import decimal
import config
from datetime import datetime
from py3cw.request import Py3CW
import traceback

def test_leveraged_token(exchange_str,pair,asset):
	if exchange_str == 'Kucoin':
		is_leveraged_token = bool(re.search('3L', asset)) or bool(re.search('3S', asset))
	if exchange_str == 'Binance':
		is_leveraged_token = bool(re.search('UP/', pair)) or bool(re.search('DOWN/', pair))
	return is_leveraged_token

def send_to_discord(string,url):
    data = {"content": string}
    requests.post(url, json=data)

def send_buy_trigger(quote,asset,exchange_str,discord_message,bot_id):
    if exchange_str in ['Binance','Kucoin']:
        pair = quote + "_" + asset
        error, deal = p3cw.request(
            entity = 'bots',
            action = 'start_new_deal',
            action_id = bot_id,
            payload={
                "pair": pair
            }
        )
        if not error and notification_alerts == True:
            send_to_discord(discord_message,config.DISCORD_NOTIFICATIONS)
    
    

def on_message(ws, message):
    messages = json.loads(message)
    now = datetime.now().replace(microsecond=0)

    # {"basePrice":0.0000011026,"belowBasePct":5,"marketInfo":{"price":0.000001047177966101695,"priceDate":1632045240,"ticker":"Kucoin:KAI-BTC"},"period":60,"type":"base-break"}
    # {"marketInfo":{"price":0.0000010517610169491524,"priceDate":1631879160,"ticker":"Kucoin:KAI-BTC"},"period":60,"strength":1.17,"type":"panic","velocity":-3.43}
    if messages['type'] in ['base-break','panic']:
        exchange_str,pair = messages["marketInfo"]["ticker"].split(':')
        pair = pair.replace('-','/')
        asset,quote = pair.split('/')

        is_leveraged_token = test_leveraged_token(exchange_str, pair, asset)

        if is_leveraged_token == True and config.TC_EXCLUDE_LEVERAGED_TOKENS == True:
            print(f"Leveraged tokens not desired but {pair} is one. Skipping...")
        else:
            if pair in config.TC_DENYLIST:
                print(f"{pair} is on the denylist. Skipping...")
            else:
                alert_price = decimal.Decimal(str(messages["marketInfo"]["price"]))
                tv_url = "https://www.tradingview.com/chart/?symbol=" + exchange_str + ":" + pair.replace('/','')
                hodloo_url = (config.HODLOO_URI).replace('wss:','https:').replace('/ws','/#/')
                hodloo_url = hodloo_url + exchange_str + ":" + pair.replace('/','-')

                if messages['type'] == 'base-break':
                    base_price = decimal.Decimal(str(messages["basePrice"]))
                    
                    if messages["belowBasePct"] == 5 and bot_id_5 == True:
                        print(f"Processing {pair} for Exchange {exchange_str} at {now}")
                        discord_message = f'\n[ {now} | {exchange_str} | Base Break 5%]\n\nSymbol: *{pair}*\nAlert Price: {alert_price} - Base Price: {base_price}\n[TradingView]({tv_url}) - [Hodloo]({hodloo_url})'
                        send_buy_trigger(quote,asset,exchange_str,discord_message,config.BOT_ID_5)
                    if messages["belowBasePct"] == 10 and bot_id_10 == True:
                        print(f"Processing {pair} for Exchange {exchange_str} at {now}")
                        discord_message = f'\n[ {now} | {exchange_str} | Base Break 10%]\n\nSymbol: *{pair}*\nAlert Price: {alert_price} - Base Price: {base_price}\n[TradingView]({tv_url}) - [Hodloo]({hodloo_url})'
                        send_buy_trigger(quote,asset,exchange_str,discord_message,config.BOT_ID_10)

                if messages['type'] == 'panic' and bot_id_panic == True:
                    print(f"Processing {pair} for Exchange {exchange_str} at {now}")
                    strength = messages["strength"]
                    velocity = messages["velocity"]
                    discord_message = f'\n[ {now} | {exchange_str} | Panic Trade ]\n\nSymbol: *{pair}*\nAlert Price: {alert_price}\nVelocity: {velocity}\nStrength: {strength}\n[TradingView]({tv_url}) - [Hodloo]({hodloo_url})'
                    send_buy_trigger(quote,asset,exchange_str,discord_message,config.BOT_ID_PANIC)
            



async def consumer_handler(websocket) -> None:
	async for message in websocket:
		on_message(websocket,message)

async def consume(uri) -> None:
	async with websockets.connect(uri) as websocket:
		await consumer_handler(websocket)

if __name__ == "__main__":
    try:
        notification_alerts = bool(re.search('^https:\/\/discord\.com\/api\/webhooks', config.DISCORD_NOTIFICATIONS))
        error_alerts = bool(re.search('^https:\/\/discord\.com\/api\/webhooks', config.DISCORD_ERRORS))
        bot_id_5 = bool(config.BOT_ID_5)
        bot_id_10 = bool(config.BOT_ID_10)
        bot_id_panic = bool(config.BOT_ID_PANIC)

        if error_alerts == False:
            raise Exception("Variable DISCORD_ERRORS must be filled")

        print('Connecting to 3Commas')
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

        print("Waiting for events")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(consume(config.HODLOO_URI))
        loop.run_forever()
    except:
        send_to_discord(f"Unexpected error: {traceback.format_exc()}",config.DISCORD_ERRORS)
