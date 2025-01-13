import asyncio
import json
import logging

from bleak import BleakClient

from pyboneco.auth import BonecoAuth
from pyboneco.client import BonecoClient
from pyboneco.enums import AuthState, ModeStatus, OperationMode

logging.basicConfig(level=logging.INFO)


async def device_control(boneco_client):
    while True:
        print("\nDevice Control Menu:")
        print("1. Turn On")
        print("2. Turn Off")
        print("3. Set Fan Speed (0-32)")
        print("4. Show Status")
        print("5. Exit")
        
        choice = input("Enter your choice (1-5): ")
        
        try:
            state = await boneco_client.get_state()
            
            if choice == "1":
                state._fan_mode = 0
                state.is_enabled = True
                await boneco_client.set_state(state)
                print("Device turned ON")
                
            elif choice == "2":
                state._fan_mode = 0
                state.is_enabled = False
                await boneco_client.set_state(state)
                print("Device turned OFF")
                
            elif choice == "3":
                try:
                    speed = int(input("Enter fan speed (0-32): "))
                    if 0 <= speed <= 32:
                        state._fan_mode = 0
                        if speed == 0:
                            # Turn device off if speed is 0
                            state.is_enabled = False
                            state.fan_level = 0
                            await boneco_client.set_state(state)
                            print("Device turned OFF")
                        else:
                            # Turn on and set speed for values 1-32
                            state.is_enabled = True
                            state.fan_level = speed
                            await boneco_client.set_state(state)
                            print(f"Device turned ON and fan speed set to {speed}")
                    else:
                        print("Invalid speed. Must be between 0-32")
                except ValueError:
                    print("Invalid input. Please enter a number")
                    
            elif choice == "4":
                info = await boneco_client.get_device_info()
                print(f"\nCurrent Status:")
                print(f"Power: {'ON' if state.is_enabled else 'OFF'}")
                print(f"Fan Speed: {state.fan_level}")
                print(f"Temperature: {info.temperature}°C")
                print(f"Humidity: {info.humidity}%")
                
            elif choice == "5":
                print("Exiting device control")
                break
                
        except Exception as e:
            print(f"Error: {e}")

async def actions(auth: BonecoAuth):
    bleak_client = BleakClient(address_or_ble_device=auth.device)
    boneco_client = BonecoClient(bleak_client, auth)
    try:
        await boneco_client.connect()
        name = await boneco_client.get_device_name()
        print(f"Connected to: {name}")
        
        await device_control(boneco_client)
        
    finally:
        await boneco_client.disconnect()


def auth_state_callback(auth: BonecoAuth) -> None:
    print(
        f"Got new auth state: current={auth.current_state}, level={auth.current_auth_level}"
    )
    if auth.current_state == AuthState.CONFIRM_WAITING:
        print("Press button on device to confirm pairing")


async def find_device(address: str):
    scanned = await BonecoClient.find_boneco_devices()
    chosen = next((x for x in scanned.keys() if x.address == address), None)
    return chosen, scanned[chosen]


async def pair():
    scanned = await BonecoClient.find_boneco_devices()
    devices = list(scanned.keys())
    devices_text = "\n".join(
        [
            f"{n}) {value} (Pairing active = {scanned[value].pairing_active})"
            for n, value in enumerate(devices, start=1)
        ]
    )
    print(f"Scan results: \n{devices_text}\n")
    number = input(f"Choose device to pair [1-{len(scanned)}]: ")
    device = devices[int(number) - 1]
    advertisement = scanned[device]
    pairing_active = advertisement.pairing_active
    print(
        f'Chosen device "{device.name}" with address "{device.address}". Pairing active = {pairing_active}'
    )
    while not pairing_active:
        print("Put the device in pairing mode and press Enter")
        input()
        device, advertisement = await find_device(device.address)
        pairing_active = device and advertisement.pairing_active

    auth_data = BonecoAuth(device)
    auth_data.set_auth_state_callback(auth_state_callback)

    await actions(auth_data)


async def connect():
    print("Enter device json data")
    data = json.loads(input())
    device, advertisement = await find_device(data["address"])
    auth_data = BonecoAuth(device, data["key"])
    await actions(auth_data)


async def menu():
    choice = input("Choose between (1) pairing new device and (2) connecting existing device: ")
    if choice == "2":
        await connect()
    else:
        await pair()

if __name__ == "__main__":
    asyncio.run(menu())
