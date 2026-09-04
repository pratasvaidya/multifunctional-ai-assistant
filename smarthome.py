import asyncio
from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager
import config

async def _toggle_switch(action: str):
    # Establish HTTP client session using the correct method for v0.4.x
    http_client = await MerossHttpClient.async_from_user_password(
        email=config.MEROSS_EMAIL,
        password=config.MEROSS_PASSWORD,
        api_base_url="https://iot.meross.com",
    )
    
    manager = MerossManager(http_client=http_client)
    await manager.async_init()
    await manager.async_device_discovery()

    # Locate the specific switch by name
    devices = manager.find_devices(device_name="Bedroom light")
    if len(devices) == 0:
        manager.close()
        await http_client.async_logout()
        return "Bedroom light not found on account."

    target_device = devices[0]
    await target_device.async_update()

    if action.lower() == "on":
        await target_device.async_turn_on()
        result = "Turned on the bedroom light."
    elif action.lower() == "off":
        await target_device.async_turn_off()
        result = "Turned off the bedroom light."
    else:
        result = f"Unknown action '{action}'."

    # Clean up session
    manager.close()
    await http_client.async_logout()
    return result

def control_bedroom_light(action: str) -> str:
    try:
        return asyncio.run(_toggle_switch(action))
    except Exception as e:
        print(f"Meross Error: {e}")
        return f"Failed to control bedroom light: {e}"
