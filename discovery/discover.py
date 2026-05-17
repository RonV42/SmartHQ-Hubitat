import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from gehomesdk import (
    GeWebsocketClient,
    EVENT_APPLIANCE_STATE_CHANGE,
    EVENT_GOT_APPLIANCE_LIST,
    EVENT_CONNECTED,
    EVENT_APPLIANCE_INITIAL_UPDATE,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')

with open('config.json') as f:
    creds = json.load(f)

async def on_appliance_list(items):
    print(f"\nFound {len(items)} appliance(s):")
    for item in items:
        print(f"\n  Appliance ID: {item.get('applianceId')}")
        print(f"  Type: {item.get('type')}")
        print(f"  Brand: {item.get('brand')}")
        print(f"  Nickname: {item.get('nickname')}")
        print(f"  Online: {item.get('online')}")

async def on_initial_update(appliance):
    print(f"\n{'='*60}")
    print(f"ERD DUMP for {appliance.mac_addr}")
    print(f"{'='*60}")
    for erd_code in sorted(appliance.known_properties, key=str):
        try:
            value = appliance.get_erd_value(erd_code)
            print(f"  {erd_code}: {value}")
        except Exception:
            pass
    print(f"\nInteract with your appliance to capture state changes...")
    print(f"(open door, turn on light, set timer, start preheat)")
    print(f"Press Ctrl+C when done\n")

async def on_state_change(args):
    if not isinstance(args, list) or len(args) < 2:
        return
    appliance, changes = args[0], args[1]
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{ts}] STATE CHANGE on {appliance.mac_addr}:")
    for erd_code, value in changes.items():
        print(f"  {erd_code}: {value}")

async def on_connected(*args):
    print("\nConnected to SmartHQ - waiting for appliance list...")

async def main():
    session = aiohttp.ClientSession()
    client = GeWebsocketClient(creds['username'], creds['password'], creds['region'])

    async def handle_state_change(args):
        await on_state_change(args)

    async def handle_initial_update(appliance):
        await on_initial_update(appliance)

    async def handle_connected(*args):
        await on_connected()

    client.add_event_handler(EVENT_APPLIANCE_STATE_CHANGE, handle_state_change)
    client.add_event_handler(EVENT_GOT_APPLIANCE_LIST, on_appliance_list)
    client.add_event_handler(EVENT_CONNECTED, handle_connected)
    client.add_event_handler(EVENT_APPLIANCE_INITIAL_UPDATE, handle_initial_update)

    await client.async_get_credentials_and_run(session)

asyncio.run(main())
