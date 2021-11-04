# soar_geofence

## IE 485/582 Project

This course project is motivated by SOAR, an outdoor facility for drone research. It is a netted enclsoure allowing for both autonomous and manual flight. Although the netting prevents drones from escaping the facility, it would be ideal to prevent a drone from ever hitting the net resulting in getting stuck or a crash to the floor. The open source drone autopilots such as PX4 and ArduPilot have geofence functionality but seems to only implement failsafes (hold, return to home) once a breach occurs. We aim to implement geofence logic that identifies if a drone's thrust and trajectory will exceed the encolsure. The drone will be redirected along the boundary of the geofence, based on the angle of its approach. In testing of our logic, we will control a simulated drone with an Xbox controller. This is representative of a real use case in SOAR, and would allow for inexperienced pilots and even guests at the facility to fly safely.

Similarly, we will also implement a low altitude boundary to ensure a drone does not crash in the middle of a flight (This must be switched off when a land command is given).



### Simulation World

The soar_rover project has the facility visualized in Cesium, but does not have a gazebo world. For our project, we will build a gazebo world of the facility to conduct our simulation.

Links that might help:

- https://github.com/optimatorlab/SOAR
- https://docs.px4.io/master/en/simulation/gazebo_worlds.html
- http://gazebosim.org/tutorials?tut=build_world


### PX4-MAVSDK

Our simulated drone will be running PX4 SITL in gazebo, thus we will use MAVSDK to connect and send commands.

- https://docs.px4.io/master/en/simulation/gazebo.html

### Joystick Control

The drone will be controlled via an Xbox controller, using the `pygame` library. Similar to the actual radio controller, the left stick will control the throttle and yaw, the right stick will control pitch and roll. The signals will need to be mapped accordingly.

- https://github.com/optimatorlab/m3c_wg/blob/master/catkin_ws_gcs/m3c_wg/scripts/m3c_wg_joystick.py

### Geofence/Avoidance

