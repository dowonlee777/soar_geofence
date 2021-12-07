#!/usr/bin/env python3


from mavsdk import System
from mavsdk.action import ActionError
from mavsdk.offboard import OffboardError, PositionNedYaw, VelocityNedYaw, VelocityBodyYawspeed
from mavsdk.telemetry import FlightMode, TelemetryError
from soar_geofence.msg import telem, vxyz_yaw_cmd, mav_cmd
from collections import deque
import asyncio
import subprocess
import os
import signal
import rospy
import math
import threading
import enum
import geofence

HOME_DIRECTORY = os.environ['HOME']
TELEM_PUB_RATE = 10
SETPOINT_RATE = 2

class MAV_CMD(enum.Enum):
    MAV_NONE                  = -1
    MAV_ARM                   = 0
    MAV_ARM_AND_TAKEOFF       = 1
    MAV_LAND                  = 2
    MAV_NAV_WAYPOINT          = 3
    MAV_RTL                   = 4
    MAV_MOVE_TARGET_LOCAL_XYZ = 5
    MAV_PAUSE                 = 6
    MAV_CONTINUE              = 7 
    MAV_VELOCITY              = 8
    MAV_YAW                   = 9
    MAV_VELOCITY_YAW          = 10
    MAV_START_OFFBOARD        = 11

LAT = 42.99549724619581
LON = -78.79709535136203

class Telem():
    def __init__(self):
        # self.assetID 
        # self.swarmID
        self.lat = None
        self.lon = None
        self.epsLat = 1
        self.epsLon = 1
        self.altMSL = None
        self.altAGL = None
        self.epsAltMSL = None
        self.heading = None
        self.roll = None
        self.pitch = None
        self.yaw = None
        self.batteryRemain = None
        self.airSpeed = None
        self.groundSpeed = None
        self.epsSpeed = None
        # ??? climb (GPS)
        self.vx = None
        self.vy = None
        self.vz = None
        self.wifiQuality = None	# 0-100
        self.gpsFix = None
        self.numSats = None
        # TO ADD ?
        # self.climbRate
    
    def deg2rad(self, deg):
        return (deg * math.pi) / 180

class Uav():
    def __init__(self, looo):
        # from soar_rover uav_mavsdk.py Vehicle class
        self.vehicle = None
        self._event_loop = loop
        self._monitor_rate = 1 # param
        self.telem = Telem()
        self.tasks = {}
        self.userMavCmdProto = {#MAV_ARM_AND_TAKEOFF: self.mav_armAndTakeoff,
                        # MAV_LAND: self.mav_land,
                        # MAV_RTL: self.mav_rtl,
                        # MAV_PAUSE: self.mav_pause,
                        # MAV_CONTINUE: self.mav_continue,
                        # # MAV_VELOCITY: self.mav_velocity,
                        # MAV_YAW: self.mav_velocity_yaw,
                        # MAV_VELOCITY_YAW: self.mav_velocity_yaw,
                        # MAV_MOVE_TARGET_LOCAL_XYZ: self.mav_move_target_local_xyz,
                        # MAV_NAV_WAYPOINT: self.mav_wp,
                        # MAV_NONE: self.mav_none,
                        # MAV_ROI_SET: self.mav_param_roi_set,
                        # MAV_ROI_UNSET: self.mav_param_roi_unset,
                        # MAV_CONFIG_SPEEDS: self.mav_param_set_speeds}
                        # MAV_SET_AIRSPEED: self.mav_param_set_airspeed,
                        # MAV_SET_GROUNDSPEED: self.mav_param_set_groundspeed
                        # MAV_CONTINUE: self.mav_start_mission 
        }
        self.publishTelem = True

        self.setpoints = deque()
        self.setpoint = None
        self.offboard_starting = False
        # ---
        # UAV class
        self._telem_pub_rate = TELEM_PUB_RATE
        self.in_air = False
        self.flight_mode = FlightMode.UNKNOWN
        self.armed = False
        self.add_user_mav_cmds()

        self.run_geofence = False
        self.geofence = geofence.Fence([
            [42.99559635044619, -78.79735971011293, 20],
            [42.99531277502557, -78.79685522306578, 20],
            [42.99551134918702, -78.79665526993782, 20],
            [42.99579492459777, -78.79715975860931, 20]
        ])

    def add_user_mav_cmds(self):
        self.userMavCmdProto[MAV_CMD.MAV_ARM.value] = self.mav_arm
        self.userMavCmdProto[MAV_CMD.MAV_ARM_AND_TAKEOFF.value] = self.mav_arm_takeoff
        self.userMavCmdProto[MAV_CMD.MAV_LAND.value] = self.mav_land
        self.userMavCmdProto[MAV_CMD.MAV_MOVE_TARGET_LOCAL_XYZ.value] = self.mav_move_target_local_xyz
        self.userMavCmdProto[MAV_CMD.MAV_YAW.value] = self.mav_velocity_yaw
        self.userMavCmdProto[MAV_CMD.MAV_START_OFFBOARD.value] = self.start_offboard
        
        # self.userMavCmdProto[MAV_NAV_WAYPOINT] = self.mav_wp
        # self.userMavCmdProto[MAV_PAUSE] = self.mav_pause

    async def run(self):
        
        await self.connectSim()
        await self.set_params()

        print('Waiting for health checks...')
        await self.health()

        print('Creating telemetry tasks...')
        await self.create_telem_tasks()
        await asyncio.sleep(3)        

        await self.create_flight_mode_task()

        print('Setting up ROS...')
        await self.ros_setup()

        await self.clear_mission()

        await self.running()
    
#################################################################################################
#                                           ROS Functions                                       #
# ============================================================================================= #

    async def ros_setup(self):
        # Initialize some ROS stuff here
        rospy.init_node('uav', anonymous=False, disable_signals=True)		

        # Define the telemetry publisher
        self.pub_telem = rospy.Publisher("telem", telem, queue_size=10)
        # Start a thread for capturing GPS and publishing telem:
        
        self.isTelemRunning = True
        telemThread = threading.Thread(target=self.pubTelem, args=(TELEM_PUB_RATE,))
        telemThread.start()

		# Subscribe to the user_mav_commands topic
        # rospy.Subscriber("user_mav_commands", user_mav_commands, self.callback_user_mav_commands)

        rospy.Subscriber('mav_cmd', mav_cmd, self.callback_mav_cmd)

        # Subscribe to teleop commands -- vx/vy/vz/yaw
        rospy.Subscriber("vxyz_yaw_cmd", vxyz_yaw_cmd, self.callback_vxyz_yaw_cmd)
        


    async def running(self):
        print('Vehicle ready.')
        while not rospy.is_shutdown():
            # if 'flight_mode' in self.tasks:
            #     print(self.tasks['flight_mode'].done())
            await asyncio.sleep(self._monitor_rate)

    
    def pubTelem(self, rate):
        '''
        THIS IS A THREAD
        '''
        threadRate = rospy.Rate(rate)
        t_msg             = telem()
        while not rospy.is_shutdown():
            try:
                
                # t_msg.assetID     = self.assetID
                t_msg.lat		  = self.telem.lat
                t_msg.lon		  = self.telem.lon
                t_msg.altMSL	  = round(self.telem.altMSL, 2)
                t_msg.altAGL	  = round(self.telem.altAGL, 2)
                t_msg.heading	  = round(self.telem.heading, 1)
                t_msg.roll		  = self.telem.deg2rad(self.telem.roll)
                t_msg.pitch		  = self.telem.deg2rad(self.telem.pitch)	
                t_msg.yaw		  = self.telem.deg2rad(self.telem.yaw)
                t_msg.groundSpeed = round(self.telem.groundSpeed, 1)

                t_msg.epsLat      = round(self.telem.epsLat, 1)
                t_msg.epsLon      = round(self.telem.epsLon, 1)
                t_msg.epsAltMSL   = round(self.telem.epsAltMSL, 1)
                t_msg.epsSpeed    = -1			# FIXME
                # t_msg.wifiQuality = self.getWiFiQuality()			
                # t_msg.gpsFix      = self.telem.gpsFix
                # t_msg.numSats     = self.telem.numSats

                # if (self.telem.batteryRemain == None):
                #     t_msg.batteryRemain 	= -1.0
                # else:
                #     t_msg.batteryRemain 	= round(self.telem.batteryRemain, 2)							

                # t_msg.status			= self.status
                t_msg.airSpeed			= round(self.telem.airSpeed, 1)
                
                if self.telem.vx:
                    t_msg.vx				= round(self.telem.vx, 2)	# FIXME
                if self.telem.vy:
                    t_msg.vy				= round(self.telem.vy, 2)
                if self.telem.vz:
                    t_msg.vz				= round(self.telem.vz, 2)
                # self.pubConsole(self.assetID, MAV_SEVERITY_INFO, self.telem.vx, self.telem.vy, self.telem.vz)
                self.pub_telem.publish(t_msg)
            except Exception as e:
                print('Error publishing telemetry.', e)
            if not self.publishTelem:
                print("Telem Thread Closing.")
                break

            threadRate.sleep()

    def callback_mav_cmd(self, msg):
        try:
            self.tasks['currentMavCmd'] = self._event_loop.create_task(self.userMavCmdProto[msg.command](msg), name="currentMavCmd")
        except Exception as e:
            print(e)

    def callback_vxyz_yaw_cmd(self, msg):
        if self.flight_mode.name == FlightMode.OFFBOARD.name:
            # self.setpoints.append(msg)
            self.setpoint = msg
        elif not self.offboard_starting and self.armed and not (msg.vx + msg.vy + msg.vz == 0):
            self.offboard_starting = True
            self.tasks['currentMavCmd'] = self._event_loop.create_task(self.userMavCmdProto[MAV_CMD.MAV_START_OFFBOARD.value](), name='currentMavCmd')

    def monitor_geofence(self, rate):
        sleepRate = rospy.Rate(rate)
        while True:
            if not self.run_geofence:
                break
            if self.setpoint.vz > 0:
                if self.telem.altAGL < 2:
                    self.setpoint.vz = 0

            if self.setpoint.vz < 0:
                if self.telem.altAGL > 20:
                    self.setpoint.vz = 0
            

            sleepRate.sleep()

    # ============================================================================================= #
    #                                         END ROS Functions                                     #
    #################################################################################################

    async def connectSim(self, lat=None, lon=None, altMSL=None):
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

    async def mav_arm(self, msg):
        print('>> Arming...')
        try:
            await self.vehicle.action.arm()
        except ActionError as e:
            print(e)
        else:
            print('Armed.')
            self.armed = True

    async def mav_arm_takeoff(self, msg):
        # if self.args['mission'] and not self.hasMission:
        #     print('>> Reuploading Mission...')
        #     await self.build_mission()

        print('>> Arming...')
        try:
            await self.mav_arm(msg)
        except:
            pass
        else:
            target_alt = 5 # msg.param1
            await self.vehicle.action.set_takeoff_altitude(target_alt)
            self.tasks['monitor_takeoff'] = asyncio.create_task(self.monitor_takeoff(), name='monitor_takeoff')
            await self.vehicle.action.takeoff()
    
    async def mav_move_target_local_xyz(self, msg):
        return

    async def mav_velocity_yaw(self, msg):
        return

    async def mav_land(self, msg):
        print('>> Landing...')
        # if self.hasMission:
        #     await self.pause_mission()
        self.tasks['monitor_land'] = asyncio.create_task(self.monitor_land(), name="monitor_land")
        await self.vehicle.action.land()

    async def monitor_takeoff(self):
        targetAlt = await self.vehicle.action.get_takeoff_altitude()
        while(True):
            if self.telem.altAGL >= targetAlt:
                print('>> Takeoff Completed')
                return
            await asyncio.sleep(1)

    async def monitor_land(self):
        async for is_in_air in self.vehicle.telemetry.in_air():
            if not is_in_air == 1:
                print('>> Landing Completed.')
                # if self.hasMission:
                #     await self.clear_mission()
                return

    async def start_offboard(self):
        for i in range(0, 100):
            await self.vehicle.offboard.set_position_velocity_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0), VelocityNedYaw(0,0,0,0))
        try:
            await self.vehicle.offboard.start()
        except OffboardError as e:
            print(e)
            print('>> Disarming...')
            await self.vehicle.action.disarm()
        else:
            print('Waiting for offboard mode...')
            while self.flight_mode.name != FlightMode.OFFBOARD.name:
                await asyncio.sleep(1)
            
            await asyncio.sleep(1)
            print('Offboard Ready.')

            self.run_geofence = True
            geofenceThread = threading.Thread(target=self.monitor_geofence, args=(2,))
            geofenceThread.start()
            
            self.tasks['stream_setpoints'] = self._event_loop.create_task(self.stream_setpoints(SETPOINT_RATE), name='stream_setpoints')

    async def stream_setpoints(self, rate):

        async for sp in self.setpoint_stream(rate):
            try:
                await self.vehicle.offboard.set_velocity_body(VelocityBodyYawspeed(sp.vx, sp.vy, sp.vz, sp.yaw))
            except Exception as e:
                print(e)


    async def setpoint_stream(self, rate):
        while self.flight_mode.name == FlightMode.OFFBOARD.name:
            yield self.setpoint
            await asyncio.sleep(1/rate)


    #############################################################################################################
    # --------------------------------------   Vehicle Class Functions ---------------------------------------- #
    # ========================================================================================================= #

    async def health(self):
        async for health in self.vehicle.telemetry.health_all_ok():
            if health:
                return

    async def set_params(self):
        try:
            await self.vehicle.telemetry.set_rate_position(self._telem_pub_rate)
        except TelemetryError as e:
            print(e)

    async def create_telem_tasks(self):
        self.tasks['pos_task'] = asyncio.create_task(self.telemetry_position(), name="pos_task")
        self.tasks['heading_task'] = asyncio.create_task(self.telemetry_heading(), name="heading_task")
        self.tasks['rawGps_task'] = asyncio.create_task(self.telemetry_rawgps(), name="rawGps_task")
        self.tasks['euler_task'] = asyncio.create_task(self.telemetry_euler(), name="euler_task")
        self.tasks['fixedWing_task'] = asyncio.create_task(self.telemetry_fixedWing(), name="fixedWing_task")
        self.tasks['odom_task'] = asyncio.create_task(self.telemetry_odom(), name="odom_task")

    async def create_flight_mode_task(self):
        self.tasks['flight_mode'] = asyncio.create_task(self.flight_mode_change(), name="flight_mode")
    
    async def flight_mode_change(self):
        # print('Flight Mode:', await self.vehicle.telemetry.flight_mode().__anext__())
        async for mode in self.vehicle.telemetry.flight_mode():
            if mode != self.flight_mode:
                print('Flight Mode: %s' % mode)
                self.flight_mode = mode

    async def telemetry_position(self):
        async for position in self.vehicle.telemetry.position():
            self.telem.lat = float(position.latitude_deg)
            self.telem.lon = float(position.longitude_deg)
            self.telem.altAGL = position.relative_altitude_m
            self.telem.altMSL = position.absolute_altitude_m
            # print(float(position.latitude_deg), float(position.longitude_deg), position.relative_altitude_m, position.absolute_altitude_m)
    
    async def telemetry_heading(self):
        async for heading in self.vehicle.telemetry.heading():
            self.telem.heading = heading.heading_deg
            # print(self.telem.heading)
    
    async def telemetry_rawgps(self):
        async for gps in self.vehicle.telemetry.raw_gps():
            self.telem.epsAltMSL = gps.vertical_uncertainty_m
            self.telem.groundSpeed = gps.velocity_m_s
            # self.telem.epsSpeed = gps.velocity_uncertainty_m_s

    async def telemetry_euler(self):
        async for attitude in self.vehicle.telemetry.attitude_euler():
            self.telem.pitch = attitude.pitch_deg
            self.telem.roll = attitude.roll_deg
            self.telem.yaw = attitude.yaw_deg

    async def telemetry_odom(self):
        async for odom in self.vehicle.telemetry.odometry():
            self.telem.vx = odom.velocity_body.x_m_s
            self.telem.vy = odom.velocity_body.y_m_s
            self.telem.vz = odom.velocity_body.z_m_s
    
    async def telemetry_fixedWing(self):
        async for metric in self.vehicle.telemetry.fixedwing_metrics():
            self.telem.airSpeed = metric.airspeed_m_s

    async def clear_mission(self):
        print('Removing mission...')
        try:
            await self.vehicle.mission.clear_mission()
        except Exception as e:
            print('WTF:', e)
        else:
            self.hasMission = False
            print('Done.')
    
    async def cancel_tasks(self):
        for task in self.tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await asyncio.get_running_loop().shutdown_asyncgens()

    async def shutdown(self, sig):
        print(sig)
        self.publishTelem = False
        self.run_geofence = False

        print('Cancelling Asyncio Tasks...')
        tasks = [t for t in asyncio.all_tasks() if t.get_name() != 'shutdown' and t.get_name() != 'main']
        for task in tasks:
            print('\tCanceled:', task.get_name())
            task.cancel()
        # [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)

        await asyncio.get_running_loop().shutdown_asyncgens()
        self._event_loop.stop()


    # ========================================================================================================= #
    # -------------------------------------- END Vehicle Class Functions -------------------------------------  #
    #############################################################################################################


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    
    uav = Uav(loop)

    # https://www.roguelynn.com/words/asyncio-graceful-shutdowns/
    signals = (signal.SIGINT, signal.SIGTERM)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(uav.shutdown(s), name='shutdown'))

    try:
        loop.create_task(uav.run(), name="main")
        loop.run_forever()
    except rospy.ROSInterruptException:
        print("UAV node terminated")
    except KeyboardInterrupt:
        pass
    finally:
        print('Exiting.')
        loop.close()