#!/usr/bin/env python3

import rospy
import pygame
from soar_geofence.msg import vxyz_yaw_cmd
from soar_geofence.msg import mav_cmd
from uav import MAV_CMD
import math
import enum

''' 
XBox Controller Details:
	Buttons:
		 0 -- "A"
		 1 -- "B"
		 2 -- "X"
		 3 -- "Y"
		 4 -- Left Bumper
		 5 -- Right Bumper
		 6 -- tiny button left of the XBox logo
		 7 -- tiny button right of the XBox logo
		 8 -- XBox logo
		 9 -- Push down on the left stick
		10 -- Push down on the right stick
	Axes:
		 0 -- left stick, x axis. (left: -1. right: 1)
		 1 -- left stick, y axis. (up: -1, down: 1)
		 2 -- left trigger. (rest: -1, held: 1)
		 3 -- right stick, x axis. (left: -1. right: 1)
		 4 -- right stick, y axis. (up: -1, down: 1)
		 5 -- right trigger. (rest: -1, held: 1)
	Hat:
		 0 -- D Pad (+)

	Current Config:
		Left stick up/down (Axis 1) controls throttle.
		Right stick left/right (Axis 3) controls steering.
		D Pad (hat) up/down controls max throttle rate.
		
	Future Options:
		Allow user to use a button to toggle teleop mode on/off
'''

REFRESH_RATE = 10

class Axis(enum.Enum):
    YAW_AXIS        = 0
    THROTTLE_AXIS 	= 1				# 1 --> left stick, y axis.  4 --> right stick, y axis.
    STEERING_AXIS 	= 3				# 0 --> left stick, x axis.  3 --> right stick, x axis.
    PITCH_AXIS      = 4

MAX_THROTTLE	= 5	    # m/s
MAX_STEERING	= 3	    # m/s	
MAX_PITCH       = 2     # m/s
MAX_YAW         = 50    # deg/s

class UavJoystick():
    def __init__(self):
        rospy.init_node('joystick', anonymous=True)

        rospy.on_shutdown(self.shutdown)
        
        pygame.init()

        pygame.joystick.init()
        count = pygame.joystick.get_count()
        print("Number of joysticks: {}".format(count))
        
        self.connected = False
        if count > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print("Joystick {}".format(0))
				
            # Get the name from the OS for the controller/joystick
            name = self.joystick.get_name()
            print("Joystick name: {}".format(name) )
            
            # Usually axis run in pairs, up/down for one, and left/right for
            # the other.
            axes = self.joystick.get_numaxes()
            print("Number of axes: {}".format(axes) )
            
            buttons = self.joystick.get_numbuttons()
            print("Number of buttons: {}".format(buttons) )
            
            # Hat switch. All or nothing for direction, not like joysticks.
            # Value comes back in an array.
            hats = self.joystick.get_numhats()
            print("Number of hats: {}".format(hats) )

            self.connected = True
        
        self.rate = rospy.Rate(REFRESH_RATE)
        
        clock = pygame.time.Clock()
        rospy.sleep(0.5)

        if not self.connected:
            print('Could not connect')
            rospy.signal_shutdown("could not connect to joystick.")

        self.pub_mav_cmd = rospy.Publisher('mav_cmd', mav_cmd, queue_size=5)
        self.pub_vxyz_yaw = rospy.Publisher('vxyz_yaw_cmd', vxyz_yaw_cmd, queue_size=30)
        
        self.vel_cmd = vxyz_yaw_cmd()

        print('Joystick ready')
        while not rospy.is_shutdown():
            # Possible joystick actions: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
            # JOYBUTTONUP, JOYHATMOTION

            # print('ASDFASDFASDF >>>> ASDFASDF >>>> ASDFSDF >>>>>>>>>> aSDF ')
            # print(len(pygame.event.get()))

            for event in pygame.event.get(): # User did something.
                if event.type == pygame.JOYBUTTONDOWN:
                    # print("Joystick button pressed.", event.button)
                    self.publish_button_press(event.button)
                elif event.type == pygame.JOYBUTTONUP:
                    # print("Joystick button released.", event.button)
                    pass
                    
                elif event.type == pygame.JOYHATMOTION:
                    pass
                    # print("Hat motion.", event.value)
                    # print(event.joy)
                    # print(event.hat)
                    # value --> [x, y].  
                    # 			up: [0, 1]
                    # left: [-1, 0]			right: [1, 0]
                    # 		  down: [0, -1]
                    # print(event.value[0], event.value[1])

                    # self.joy_info.throttleRate += event.value[1]
                    # self.joy_info.throttleRate = max(0,   self.joy_info.throttleRate)
                    # self.joy_info.throttleRate = min(100, self.joy_info.throttleRate)
                    # # print(self.joy_info.throttleRate)
                    
                    # joy_msg = user_feedback()
                    # joy_msg.field_name = "throttleRate"
                    # joy_msg.values = [str(int(self.joy_info.throttleRate))]
                    # self.pub_joystick_feedback.publish(joy_msg)
                    
                    # NOTE:  When the GUI gets the updated throttle rate,
                    #        the GUI publishes to user_feedback.msg (with the new throttle_rate value).
                    #		 So, we do NOT want to re-publish this info here.	
                                        
                elif event.type == pygame.JOYAXISMOTION:
                    # print("Axis Motion", event)
                    # joy: joystick id of the event
                    # axis: axis id of the event
                    # value: new position of the axis, -1 (off) to 1 (fully depressed) with 0 the center	
                    '''
                    # 2 and 5 are triggers (left and right, resp.)
                    if event.axis in [2, 5]:
                        # print(event)
                        #print(event.axis)
                        print(event.value)
                    '''

                    
                    if event.axis == Axis.THROTTLE_AXIS.value:
                        if abs(event.value) > 0.1:
                            self.vel_cmd.vz = event.value * MAX_THROTTLE
                        else:
                            self.vel_cmd.vz = 0

                    elif event.axis == Axis.STEERING_AXIS.value:
                        if abs(event.value) > 0.1:
                            self.vel_cmd.vy = event.value * MAX_STEERING
                        else:
                            self.vel_cmd.vy = 0
                    
                    elif event.axis == Axis.PITCH_AXIS.value:
                        if abs(event.value) > 0.1:
                            self.vel_cmd.vx = -event.value * MAX_PITCH
                        else:
                            self.vel_cmd.vx = 0
                    
                    elif event.axis == Axis.YAW_AXIS.value:
                        if abs(event.value) > 0.1:
                            self.vel_cmd.yaw = event.value * MAX_YAW
                        else:
                            self.vel_cmd.yaw = 0

            self.pub_vxyz_yaw.publish(self.vel_cmd)
            
            # self.rate.sleep()
            clock.tick(REFRESH_RATE)

    def publish_button_press(self, button):
        if button == 8:
            cmd = mav_cmd()
            cmd.command = MAV_CMD.MAV_ARM.value
            # cmd.command = MAV_CMD.MAV_ARM_AND_TAKEOFF.value
            self.pub_mav_cmd.publish(cmd)


    def shutdown(self):
        rospy.loginfo("Shutting down the Joystick node...")

        try:
            pygame.quit()
        except Exception as e:
            print("Could not quit pygame.")
            print(e)
            
        rospy.sleep(1)

if __name__ == "__main__":
    # joysticks = {x: pygame.joystick.Joystick(x) for x in range[pygame.joystick.get_count()]}
    try:
        UavJoystick()
    except Exception as e:
        print(e)
