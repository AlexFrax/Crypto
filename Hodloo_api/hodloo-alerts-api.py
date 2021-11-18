import websockets
import json
import traceback
import re
import asyncio
import decimal
import config
import requests
from datetime import datetime


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

def test_volume24(volume_hodloo,volume_threshold):
	if volume_threshold == '':
		# Volume filter not desired -> proceeed
		return True
	else:
		if bool(re.search('^\d+(\.\d+)$',volume_threshold)) == True:
			if volume_hodloo < float(volume_threshold):
				# Volume filter is set and volume below threshold -> stop
				return False
			else:
				# Volmue filter is set and volume above threshold -> proceed
				return True
		else:
			raise Exception("Variable HODLOO_MIN_VOLUME not set correctly. Please read the variable documentation.")

def on_message(ws, message):
	messages = json.loads(message)

	# {"basePrice":0.0000014002,"belowBasePct":0,"marketInfo":{"pctRelBase":-4.04,"price":0.0000013597,"priceDate":1637223011,"symbol":"manbtc","ticker":"Huobi:MAN-BTC","volume24":5.74040067182},"period":60,"type":"base-break"}
	# {"marketInfo":{"price":0.002621,"priceDate":1637222839,"symbol":"BSVBTC","ticker":"HitBTC:BSV-BTC","volume24":28.209960342},"period":60,"strength":7.7,"type":"panic","velocity":-2.27}
	if messages['type'] in ['base-break','panic']:
		exchange_str,pair = messages["marketInfo"]["ticker"].split(':')
		if exchange_str in config.HODLOO_EXCHANGES:
			pair = pair.replace('-','/')
			asset,quote = pair.split('/')
			volume24 = messages["marketInfo"]["volume24"]
			if test_volume24(volume24,config.HODLOO_MIN_VOLUME) == True:
				if quote in config.HODLOO_QUOTES:
					if test_leveraged_token(exchange_str, pair, asset) == False:
						alert_price = decimal.Decimal(str(messages["marketInfo"]["price"]))
						tv_url = "https://www.tradingview.com/chart/?symbol=" + exchange_str + ":" + pair.replace('/','')
						hodloo_url = (config.HODLOO_URI).replace('wss:','https:').replace('/ws','/#/')
						hodloo_url = hodloo_url + exchange_str + ":" + pair.replace('/','-')

						if messages['type'] == 'base-break':
							base_price = decimal.Decimal(str(messages["basePrice"]))
							discord_message = f'\n[ {datetime.now().replace(microsecond=0)} | {exchange_str} | Base Break ]\n\nSymbol: *{pair}*\nAlert Price: {alert_price} - Base Price: {base_price} - Volume: {volume24}\n[TradingView]({tv_url}) - [Hodloo]({hodloo_url})'
							
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
							discord_message = f'\n[ {datetime.now().replace(microsecond=0)} | {exchange_str} | Panic Alert ]\n\nSymbol: *{pair}*\nAlert Price: {alert_price}\nVolume: {volume24}\nVelocity: {velocity}\nStrength: {strength}\n[TradingView]({tv_url}) - [Hodloo]({hodloo_url})'
							send_to_discord(discord_message,config.DISCORD_PANIC)
					else:
						print(f"{datetime.now().replace(microsecond=0)} - {pair} is a leveraged token. Skipping it.")
				else:
					print(f"{datetime.now().replace(microsecond=0)} - Quote is {quote} hence skipping pair {pair}")
			else:
					print(f"{datetime.now().replace(microsecond=0)} - Volume is below threshold hence skipping pair {pair}")


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
