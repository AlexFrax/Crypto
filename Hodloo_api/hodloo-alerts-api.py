import websockets
import json
import traceback
import re
import asyncio
import decimal
import config
import requests
from datetime import datetime
import sys


def send_to_discord(string,url):
    data = {"content": string}
    requests.post(url, json=data)

def test_leveraged_token(exchange_str,pair,asset):
	is_leveraged_token = False
	if exchange_str == 'Kucoin':
		is_leveraged_token = bool(re.search('3L', asset)) or bool(re.search('3S', asset))
	if exchange_str == 'Binance':
		is_leveraged_token = bool(re.search('UP/', pair)) or bool(re.search('DOWN/', pair))
	return is_leveraged_token

def on_message(ws, message):
	messages = json.loads(message)

	# {"basePrice":0.0000011026,"belowBasePct":5,"marketInfo":{"price":0.000001047177966101695,"priceDate":1632045240,"ticker":"Kucoin:KAI-BTC"},"period":60,"type":"base-break"}
	# {"marketInfo":{"price":0.0000010517610169491524,"priceDate":1631879160,"ticker":"Kucoin:KAI-BTC"},"period":60,"strength":1.17,"type":"panic","velocity":-3.43}
	if messages['type'] in ['base-break','panic']:
		exchange_str,pair = messages["marketInfo"]["ticker"].split(':')
		if exchange_str in config.HODLOO_EXCHANGES:
			pair = pair.replace('-','/')
			asset,quote = pair.split('/')
			if quote in config.HODLOO_QUOTES:
				if test_leveraged_token(exchange_str, pair, asset) == False:
					alert_price = decimal.Decimal(str(messages["marketInfo"]["price"]))
					tv_url = "https://www.tradingview.com/chart/?symbol=" + exchange_str + ":" + pair.replace('/','')
					hodloo_url = (config.HODLOO_URI).replace('wss:','https:').replace('/ws','/#/')
					hodloo_url = hodloo_url + exchange_str + ":" + pair.replace('/','-')

					if messages['type'] == 'base-break':
						base_price = decimal.Decimal(str(messages["basePrice"]))
						discord_message = f'\n[ {datetime.now().replace(microsecond=0)} | {exchange_str} | Base Break ]\n\nSymbol: *{pair}*\nAlert Price: {alert_price} - Base Price: {base_price}\n[TradingView]({tv_url}) - [Hodloo]({hodloo_url})'
						
						if messages["belowBasePct"] == 5 and percent_5_alerts == True:
							print(f"{datetime.now().replace(microsecond=0)} - Processing {pair} for Exchange {exchange_str}")
							send_to_discord(discord_message,config.DISCORD_WEBHOOK_5)
						if messages["belowBasePct"] == 10 and percent_10_alerts == True:
							print(f"{datetime.now().replace(microsecond=0)} - Processing {pair} for Exchange {exchange_str}")
							send_to_discord(discord_message,config.DISCORD_WEBHOOK_10)
					
					if messages['type'] == 'panic' and panic_alerts == True:
						print(f"{datetime.now().replace(microsecond=0)} - Processing {pair} for Exchange {exchange_str}")
						strength = messages["strength"]
						velocity = messages["velocity"]
						discord_message = f'\n[ {datetime.now().replace(microsecond=0)} | {exchange_str} | Panic Alert ]\n\nSymbol: *{pair}*\nAlert Price: {alert_price}\nVelocity: {velocity}\nStrength: {strength}\n[TradingView]({tv_url}) - [Hodloo]({hodloo_url})'
						send_to_discord(discord_message,config.DISCORD_PANIC)
				else:
					print(f"{datetime.now().replace(microsecond=0)} - {pair} is a leveraged token. Skipping it.")
			else:
				print(f"{datetime.now().replace(microsecond=0)} - Quote is {quote} hence skipping pair {pair}")


async def consumer_handler(websocket) -> None:
	async for message in websocket:
		on_message(websocket,message)

async def consume(uri) -> None:
	async with websockets.connect(uri) as websocket:
		await consumer_handler(websocket)

def await_events():
	print(f"{datetime.now().replace(microsecond=0)} - Waiting for events")
	loop = asyncio.get_event_loop()
	loop.run_until_complete(consume(config.HODLOO_URI))
	loop.run_forever()

if __name__ == "__main__":
	try:
		percent_5_alerts = bool(re.search('^https:\/\/(discord|discordapp)\.com\/api\/webhooks', config.DISCORD_WEBHOOK_5))
		percent_10_alerts = bool(re.search('^https:\/\/(discord|discordapp)\.com\/api\/webhooks', config.DISCORD_WEBHOOK_10))
		panic_alerts = bool(re.search('^https:\/\/(discord|discordapp)\.com\/api\/webhooks', config.DISCORD_PANIC))
		error_alerts = bool(re.search('^https:\/\/(discord|discordapp)\.com\/api\/webhooks', config.DISCORD_ERRORS))

		if error_alerts == False:
			raise Exception("Variable DISCORD_ERRORS must be filled")
		
		await_events()
    
	except KeyboardInterrupt:
		print(f"{datetime.now().replace(microsecond=0)} - Exiting as requested by user")

	except websockets.ConnectionClosedError:
		print(f"{datetime.now().replace(microsecond=0)} - Connection to websockets server lost. Reconnecting...")
		await_events()

	except TimeoutError:
		print(f"{datetime.now().replace(microsecond=0)} - Got a timeout. Reconnecting...")
		await_events()
		
	except:
		send_to_discord(f"{datetime.now().replace(microsecond=0)} - Unexpected error:\n```\n{traceback.format_exc()}\n```\nReconnecting...",config.DISCORD_ERRORS)
		await_events()

	finally:
		print(f"{datetime.now().replace(microsecond=0)} - Exiting...")
