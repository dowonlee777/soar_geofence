#!/usr/bin/env python3

import sys
import rospy
import pygame

from robocar.msg import user_feedback
from robocar.msg import joystick_feedback
from robocar.msg import ts_cmd


refreshRate 	= 10.0	# Hz	

''' 
XBox Controller Details:
	Buttons:
		 0 -- "A"
		 1 -- "B"
		 2 -- "X"
		 3 -- "Y"
		 4 -- Left Button
		 5 -- Right Button
		 6 -- tiny button left of the XBox logo
		 7 -- tiny button right of the XBox logo
		 8 -- XBox logo
		 9 -- Push down on the left stick
		10 -- Push down on the right stick
	Axes:
		 0 -- left stick, x axis.
		 1 -- left stick, y axis.
		 2 -- left trigger.
		 3 -- right stick, x axis.
		 4 -- right stick, y axis.
		 5 -- right trigger.
	Hat:
		 0 -- D Pad (+)

	Current Config:
		Left stick up/down (Axis 1) controls throttle.
		Right stick left/right (Axis 3) controls steering.
		D Pad (hat) up/down controls max throttle rate.
		
	Future Options:
		Allow user to use a button to toggle teleop mode on/off
'''
		
THROTTLE_AXIS 	= 1				# 1 --> left stick, y axis.  4 --> right stick, y axis.
STEERING_AXIS 	= 3				# 0 --> left stick, x axis.  3 --> right stick, x axis.

MAX_THROTTLE	= 100			# --> Throttle goes from -100 to 100
MAX_STEERING	=  90			# --> Steering goes from -90 to 90

class make_joystick():
	def __init__(self, init_throttleRate):
		# Set self.joy_info
		self.throttleRate 	= init_throttleRate
		self.throttle		= 0
		self.steering		= 0
	
	 
class runJoystick():
	def __init__(self):

		# Should be 1 command line argument:
		if (len(sys.argv) == 2):
			INIT_THROTTLE_RATE = float(sys.argv[1])			# In range [0, 100]
		else:
			print("Wrong number of command line arguments passed.  Bye.")
			exit()

		# Initialize some ROS stuff here
		rospy.init_node('joystick', anonymous=True)		
		
		# Set the shutdown function
		rospy.on_shutdown(self.shutdown)		

		# How often should we send messages?
		self.rate = rospy.Rate(refreshRate)	
		
		# Define the publisher to send throttle/steering values to the RPi
		# (and to the GUI).
		# NOTE: The GUI publishes to 'ts_cmd_gui' using the same 'ts_cmd' msg type.
		# 		That only happens when user presses directional buttons on GUI.
		# (same message type, different topics)
		self.pub_ts_cmd = rospy.Publisher('ts_cmd_joystick', ts_cmd, queue_size=1)
		
		# Define the publisher to send custom joystick feedback to the RPi
		# In particular, we'll send:
		#	joystickStatus 	--> False if we can't connect to the joystick.
		#	throttleRate	--> Allow the user to change the throttle rate threshold via joystick.
		# NOTE:  This topic does NOT send steering/throttle values.  That's done in user_feedback.
		self.pub_joystick_feedback = rospy.Publisher('joystick_feedback', joystick_feedback, queue_size=1)
		
		# Try to connect to the joystick
		couldConnect = False
		try:			
			pygame.init()
			
			# Initialize the joysticks
			pygame.joystick.init()
						
			# Used to manage how fast the screen updates
			clock = pygame.time.Clock()
			
			# Get count of joysticks
			joystick_count = pygame.joystick.get_count()
			print("Number of joysticks: {}".format(joystick_count))
			
			if (joystick_count > 0):
				joystick = pygame.joystick.Joystick(0)
				joystick.init()
			
				print("Joystick {}".format(0))
				
				# Get the name from the OS for the controller/joystick
				name = joystick.get_name()
				print("Joystick name: {}".format(name) )
				
				# Usually axis run in pairs, up/down for one, and left/right for
				# the other.
				axes = joystick.get_numaxes()
				print("Number of axes: {}".format(axes) )
				
				buttons = joystick.get_numbuttons()
				print("Number of buttons: {}".format(buttons) )
				
				# Hat switch. All or nothing for direction, not like joysticks.
				# Value comes back in an array.
				hats = joystick.get_numhats()
				print("Number of hats: {}".format(hats) )

				couldConnect = True
					
		except:
			print("Error with pygame.init():")
			e = sys.exc_info()[1]
			print(e)
			raise

		rospy.sleep(0.5)					

		# Publish message to joystick_feedback topic
		joy_msg = user_feedback()
		joy_msg.field_name = "joystickStatus"
		joy_msg.values = [str(couldConnect)]
		self.pub_joystick_feedback.publish(joy_msg)
		
		rospy.sleep(0.5)					
			
		if (not couldConnect):
			print("Could not connect to joystick.")
			# self.shutdown()
			rospy.signal_shutdown("could not connect to joystick.")			
		
		
		# Initialize our data structure:
		self.joy_info = make_joystick(INIT_THROTTLE_RATE)
		
		# Subscribe to the user_feedback topic to get info from the GUI.
		# We're only listening for changes to teleopStatus and throttleRate
		rospy.Subscriber("user_feedback", user_feedback, self.user_feedback_callback)



		# Keep this node alive.
		print("Joystick Node Running...")
		while not rospy.is_shutdown():	

			# EVENT PROCESSING STEP
			for event in pygame.event.get(): # User did something
				# print(event)

				pubAxis = False

				
				'''
				if event.type == pygame.QUIT: # If user clicked close
					done=True # Flag that we are done so we exit this loop
				'''
				
				# Possible joystick actions: JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
				if event.type == pygame.JOYBUTTONDOWN:
					print("Joystick button pressed.")

				elif event.type == pygame.JOYBUTTONUP:
					print("Joystick button released.")

				elif event.type == pygame.JOYHATMOTION:
					# print("Hat motion.")
					# print(event.joy)
					# print(event.hat)
					# value --> [x, y].  
					# 			up: [0, 1]
					# left: [-1, 0]			right: [1, 0]
					# 		  down: [0, -1]
					# print(event.value[0], event.value[1])

					self.joy_info.throttleRate += event.value[1]
					self.joy_info.throttleRate = max(0,   self.joy_info.throttleRate)
					self.joy_info.throttleRate = min(100, self.joy_info.throttleRate)
					# print(self.joy_info.throttleRate)
					
					joy_msg = user_feedback()
					joy_msg.field_name = "throttleRate"
					joy_msg.values = [str(int(self.joy_info.throttleRate))]
					self.pub_joystick_feedback.publish(joy_msg)
					
					# NOTE:  When the GUI gets the updated throttle rate,
					#        the GUI publishes to user_feedback.msg (with the new throttle_rate value).
					#		 So, we do NOT want to re-publish this info here.	
										
				elif event.type == pygame.JOYAXISMOTION:
					# print("Axis Motion")
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
					if (event.axis == THROTTLE_AXIS):
						# up is -1, down is 1
						self.joy_info.throttle = -1 * event.value * MAX_THROTTLE
						self.joy_info.throttle = max(-1 * MAX_THROTTLE, self.joy_info.throttle)
						self.joy_info.throttle = min(+1 * MAX_THROTTLE, self.joy_info.throttle)
						self.joy_info.throttle = round(self.joy_info.throttle, 2)
						# self.joy_info.steering remains unchanged
						# print("throttle: %f, steering: %f" % (self.joy_info.throttle, self.joy_info.steering))
						pubAxis = True
					elif (event.axis == STEERING_AXIS):
						# left is -1, right is 1
						self.joy_info.steering = event.value * MAX_STEERING
						self.joy_info.steering = max(-1 * MAX_STEERING, self.joy_info.steering)
						self.joy_info.steering = min( 1 * MAX_STEERING, self.joy_info.steering)
						self.joy_info.steering = round(self.joy_info.steering, 2)
						# self.joy_info.throttle remains unchanged
						# print("throttle: %f, steering: %f" % (self.joy_info.throttle, self.joy_info.steering))
						pubAxis = True

					if (pubAxis):
						# Publish message to ts_cmd_joystick topic
						ts_cmd_msg = ts_cmd()
						ts_cmd_msg.throttle = self.joy_info.throttle
						ts_cmd_msg.steering = self.joy_info.steering
						self.pub_ts_cmd.publish(ts_cmd_msg)

						# print(ts_cmd_msg)
						
					'''		
					elif event.axis in [4]:
						# Right stick, up (-1) / down (1)
						print(event.axis, event.value)
					'''
					
					'''	
					elif event.axis in [3]:
						# Right stick, left (-1) / right (1)
						print(event.axis, event.value)
					'''	

					

			# self.rate.sleep()			
			clock.tick(refreshRate)
			

	def user_feedback_callback(self, msg):
		if (msg.field_name == 'teleopStatus'):
			if (msg.values[0] == 'False'):
				print("User turned teleop off.")
				rospy.signal_shutdown("User turned teleop off.")	
		if (msg.field_name == 'throttle_rate'):
			self.joy_info.throttleRate = float(msg.values[0])
			

	def shutdown(self):
		rospy.loginfo("Shutting down the Joystick node...")

		try:
			pygame.quit()
		except:
			print("Could not quit pygame.")
			e = sys.exc_info()[1]
			print(e)
			
		rospy.sleep(1)
		

if __name__ == '__main__':
	try:
		runJoystick()
	except rospy.ROSInterruptException:
		rospy.loginfo("Joystick node terminated.")	



