import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from gehomesdk import (
    GeWebsocketClient,
    EVENT_APPLIANCE_STATE_CHANGE,
    EVENT_GOT_APPLIANCE_LIST,
    EVENT_CONNECTED,
    EVENT_DISCONNECTED,
    EVENT_APPLIANCE_INITIAL_UPDATE,
    ErdCode,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
_LOGGER = logging.getLogger(__name__)

with open('/opt/smarthq-bridge/config.json') as f:
    creds = json.load(f)

# Hubitat Maker API config
HUBITAT_IP = creds['hubitat_ip']
MAKER_API_APP = creds['maker_api_app']
ACCESS_TOKEN = creds['access_token']
DEVICE_CONTROL_PANEL = creds['device_control_panel']
DEVICE_UPPER_OVEN = creds['device_upper_oven']
DEVICE_LOWER_OVEN = creds['device_lower_oven']

BASE_URL = f"http://{HUBITAT_IP}/apps/api/{MAKER_API_APP}/devices"

def make_url(device_id, attribute, value):
    return f"{BASE_URL}/{device_id}/setAttribute/{attribute},{value}?access_token={ACCESS_TOKEN}"

async def push_attribute(session, device_id, attribute, value):
    url = make_url(device_id, attribute, str(value))
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                _LOGGER.debug(f"Set device {device_id} {attribute}={value}")
            else:
                _LOGGER.warning(f"Failed to set {attribute} on device {device_id}: HTTP {resp.status}")
    except Exception as e:
        _LOGGER.error(f"Error pushing to Hubitat: {e}")

async def push_control_panel(session, changes):
    mapping = {
        ErdCode.USER_INTERFACE_LOCKED: "interfaceLocked",
        ErdCode.SABBATH_MODE: "sabbathMode",
        ErdCode.SOUND_LEVEL: "soundLevel",
        ErdCode.END_TONE: "endTone",
        ErdCode.CONVECTION_CONVERSION: "convectionConversion",
        ErdCode.HOUR_12_SHUTOFF_ENABLED: "twelveHourShutoff",
        ErdCode.CLOCK_FORMAT: "clockFormat",
        ErdCode.WIFI_MODULE_SW_VERSION: "wifiVersion",
        ErdCode.MODEL_NUMBER: "modelNumber",
        ErdCode.SERIAL_NUMBER: "serialNumber",
        ErdCode.BRAND: "brand",
    }
    for erd, attr in mapping.items():
        if erd in changes:
            value = changes[erd]
            # Clean up enum representations
            if hasattr(value, 'name'):
                value = value.name
            await push_attribute(session, DEVICE_CONTROL_PANEL, attr, value)

async def push_upper_oven(session, changes):
    # Current state
    if ErdCode.UPPER_OVEN_CURRENT_STATE in changes:
        val = changes[ErdCode.UPPER_OVEN_CURRENT_STATE]
        await push_attribute(session, DEVICE_UPPER_OVEN, "ovenState",
                           val.name if hasattr(val, 'name') else val)

    # Cook mode
    if ErdCode.UPPER_OVEN_COOK_MODE in changes:
        val = changes[ErdCode.UPPER_OVEN_COOK_MODE]
        cook_mode = val.cook_mode.oven_state.name if val.cook_mode else "NO_MODE"
        await push_attribute(session, DEVICE_UPPER_OVEN, "cookMode", cook_mode)
        await push_attribute(session, DEVICE_UPPER_OVEN, "setTemperature", val.temperature)

    # Temperatures
    if ErdCode.UPPER_OVEN_DISPLAY_TEMPERATURE in changes:
        temp = changes[ErdCode.UPPER_OVEN_DISPLAY_TEMPERATURE]
        await push_attribute(session, DEVICE_UPPER_OVEN, "actualTemperature", temp)
        await push_attribute(session, DEVICE_UPPER_OVEN, "temperature", temp)

    # Cook time remaining
    if ErdCode.UPPER_OVEN_COOK_TIME_REMAINING in changes:
        val = changes[ErdCode.UPPER_OVEN_COOK_TIME_REMAINING]
        seconds = int(val.total_seconds()) if isinstance(val, timedelta) else 0
        await push_attribute(session, DEVICE_UPPER_OVEN, "cookTimeRemaining", seconds)

    # Kitchen timer
    if ErdCode.UPPER_OVEN_KITCHEN_TIMER in changes:
        val = changes[ErdCode.UPPER_OVEN_KITCHEN_TIMER]
        seconds = int(val.total_seconds()) if isinstance(val, timedelta) else 0
        await push_attribute(session, DEVICE_UPPER_OVEN, "kitchenTimer", seconds)

    # Delay time
    if ErdCode.UPPER_OVEN_DELAY_TIME_REMAINING in changes:
        val = changes[ErdCode.UPPER_OVEN_DELAY_TIME_REMAINING]
        seconds = int(val.total_seconds()) if isinstance(val, timedelta) else 0
        await push_attribute(session, DEVICE_UPPER_OVEN, "delayTimeRemaining", seconds)

    # Probe
    if ErdCode.UPPER_OVEN_PROBE_PRESENT in changes:
        await push_attribute(session, DEVICE_UPPER_OVEN, "probePresent",
                           changes[ErdCode.UPPER_OVEN_PROBE_PRESENT])
    if ErdCode.UPPER_OVEN_PROBE_DISPLAY_TEMP in changes:
        await push_attribute(session, DEVICE_UPPER_OVEN, "probeTemperature",
                           changes[ErdCode.UPPER_OVEN_PROBE_DISPLAY_TEMP])

    # Light
    if ErdCode.UPPER_OVEN_LIGHT in changes:
        val = changes[ErdCode.UPPER_OVEN_LIGHT]
        await push_attribute(session, DEVICE_UPPER_OVEN, "lightLevel",
                           val.name if hasattr(val, 'name') else val)

    # Remote enabled
    if ErdCode.UPPER_OVEN_REMOTE_ENABLED in changes:
        await push_attribute(session, DEVICE_UPPER_OVEN, "remoteEnabled",
                           changes[ErdCode.UPPER_OVEN_REMOTE_ENABLED])

async def push_lower_oven(session, changes):
    # Current state
    if ErdCode.LOWER_OVEN_CURRENT_STATE in changes:
        val = changes[ErdCode.LOWER_OVEN_CURRENT_STATE]
        await push_attribute(session, DEVICE_LOWER_OVEN, "ovenState",
                           val.name if hasattr(val, 'name') else val)

    # Cook mode
    if ErdCode.LOWER_OVEN_COOK_MODE in changes:
        val = changes[ErdCode.LOWER_OVEN_COOK_MODE]
        cook_mode = val.cook_mode.oven_state.name if val.cook_mode else "NO_MODE"
        await push_attribute(session, DEVICE_LOWER_OVEN, "cookMode", cook_mode)
        await push_attribute(session, DEVICE_LOWER_OVEN, "setTemperature", val.temperature)

    # Temperatures
    if ErdCode.LOWER_OVEN_DISPLAY_TEMPERATURE in changes:
        temp = changes[ErdCode.LOWER_OVEN_DISPLAY_TEMPERATURE]
        await push_attribute(session, DEVICE_LOWER_OVEN, "actualTemperature", temp)
        await push_attribute(session, DEVICE_LOWER_OVEN, "temperature", temp)

    # Cook time remaining
    if ErdCode.LOWER_OVEN_COOK_TIME_REMAINING in changes:
        val = changes[ErdCode.LOWER_OVEN_COOK_TIME_REMAINING]
        seconds = int(val.total_seconds()) if isinstance(val, timedelta) else 0
        await push_attribute(session, DEVICE_LOWER_OVEN, "cookTimeRemaining", seconds)

    # Delay time
    if ErdCode.LOWER_OVEN_DELAY_TIME_REMAINING in changes:
        val = changes[ErdCode.LOWER_OVEN_DELAY_TIME_REMAINING]
        seconds = int(val.total_seconds()) if isinstance(val, timedelta) else 0
        await push_attribute(session, DEVICE_LOWER_OVEN, "delayTimeRemaining", seconds)

    # Light
    if ErdCode.LOWER_OVEN_LIGHT in changes:
        val = changes[ErdCode.LOWER_OVEN_LIGHT]
        await push_attribute(session, DEVICE_LOWER_OVEN, "lightLevel",
                           val.name if hasattr(val, 'name') else val)

    # Remote enabled
    if ErdCode.LOWER_OVEN_REMOTE_ENABLED in changes:
        await push_attribute(session, DEVICE_LOWER_OVEN, "remoteEnabled",
                           changes[ErdCode.LOWER_OVEN_REMOTE_ENABLED])

async def on_state_change(session, args):
    if not isinstance(args, list) or len(args) < 2:
        return
    appliance, changes = args[0], args[1]
    _LOGGER.info(f"State change on {appliance.mac_addr}: {len(changes)} ERD(s) changed")
    await push_control_panel(session, changes)
    await push_upper_oven(session, changes)
    await push_lower_oven(session, changes)

async def on_initial_update(session, appliance):
    _LOGGER.info(f"Initial update for {appliance.mac_addr}")
    # Build a dict from known properties
    changes = {}
    for erd_code in appliance.known_properties:
        try:
            changes[erd_code] = appliance.get_erd_value(erd_code)
        except Exception:
            pass
    await on_state_change(session, [appliance, changes])


async def on_connected(session, *args):
    _LOGGER.info("Connected to SmartHQ")
    await push_attribute(session, DEVICE_CONTROL_PANEL, "online", "true")

async def on_disconnected(session, *args):
    _LOGGER.warning("Disconnected from SmartHQ")
    await push_attribute(session, DEVICE_CONTROL_PANEL, "online", "false")

async def main():
    session = aiohttp.ClientSession()
    client = GeWebsocketClient(creds['username'], creds['password'], creds['region'])

    async def handle_state_change(args):
        await on_state_change(session, args)

    async def handle_initial_update(appliance):
        await on_initial_update(session, appliance)

    async def handle_connected(*args):
        await on_connected(session)

    async def handle_disconnected(*args):
        await on_disconnected(session)

    client.add_event_handler(EVENT_APPLIANCE_STATE_CHANGE, handle_state_change)
    client.add_event_handler(EVENT_APPLIANCE_INITIAL_UPDATE, handle_initial_update)
    client.add_event_handler(EVENT_CONNECTED, handle_connected)
    client.add_event_handler(EVENT_DISCONNECTED, handle_disconnected)

    await client.async_get_credentials_and_run(session)

asyncio.run(main())
