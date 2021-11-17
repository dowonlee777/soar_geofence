#!/usr/bin/env python3

from mavsdk import System
from mavsdk.action import ActionError
from mavsdk.telemetry import FlightMode
import asyncio
import subprocess
import os

HOME_DIRECTORY = os.environ['HOME']

LAT = 42.99549724619581
LON = -78.79709535136203

class Uav():
    def __init__(self):
        self.vehicle = None
        self.flight_mode = FlightMode(9)
        self.tasks = {}

    async def run(self):
        print('Connecting to sitl')
        await self.connectSim(LAT, LON, 170)
        await self.create_flight_mode_task()
        self.tasks['telem'] = asyncio.create_task(self.telemetry_position())

        while self.flight_mode.value != 3:
            print(type(self.flight_mode))
            # print('Waiting for Flight Mode: HOLD... | Current: %s' % self.flight_mode)
            await asyncio.sleep(1)

        await self.mav_arm_takeoff(self)

        while(True):
            await asyncio.sleep(1)
    
    async def mav_arm_takeoff(self, msg):
        print('>> Arming...')
        try:
            await self.vehicle.action.arm()
        except ActionError as e:
            print(e)
        else:
            print('>> Taking off...')
            await self.vehicle.action.set_takeoff_altitude(10)
            await self.vehicle.action.takeoff()


    async def connectSim(self, lat, lon, altMSL):
        try:
            # self.open_sitl(lat, lon, altMSL)
            # self.sitl_proc = await asyncio.create_subprocess_shell(
            #     'HEADLESS=1 make px4_sitl gazebo',
            #     cwd='%s/PX4-Autopilot' % HOME_DIRECTORY,
            # )
            self.vehicle = System()
            print("Waiting for drone to connect...")
            await self.vehicle.connect(system_address="udp://:14540")
            async for state in self.vehicle.core.connection_state():
                if state.is_connected:
                    print("Connected to sitl.")
                    break
        except:
            print("Could not connect to sitl vehicle.")
            exit()
    
    def open_sitl(self, lat, lon, altMSL):
        lat_var = 'export PX4_HOME_LAT=%f' % lat
        lon_var = 'export PX4_HOME_LON=%f' % lon
        alt_var = 'export PX4_HOME_ALT=%f' % altMSL
        self.sitl_proc = subprocess.Popen(
                ['xterm', '-e', '%s;%s;%s;make px4_sitl gazebo' % (lat_var, lon_var, alt_var)],
                cwd='%s/PX4-Autopilot' % HOME_DIRECTORY,
            )

    async def telemetry_position(self):
        async for position in self.vehicle.telemetry.position():
            print(float(position.latitude_deg), float(position.longitude_deg), position.relative_altitude_m, position.absolute_altitude_m)

    async def create_flight_mode_task(self):
        self.tasks['flight_mode'] = asyncio.create_task(self.flight_mode_change())
    
    async def flight_mode_change(self):
        # print('Flight Mode:', await self.vehicle.telemetry.flight_mode().__anext__())
        async for mode in self.vehicle.telemetry.flight_mode():
            if mode != self.flight_mode:
                print('Flight Mode: %s' % mode)
                self.flight_mode = mode

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    uav = Uav()
    try:
        loop.run_until_complete(uav.run())
    except KeyboardInterrupt:
        pass
    finally:
        loop.stop()
        loop.close()