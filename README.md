# soar_geofence

## IE 485/582 Project

This course project is motivated by SOAR, an outdoor facility for drone research. It is a netted enclsoure allowing for both autonomous and manual flight. Although the netting prevents drones from escaping the facility, it would be ideal to prevent a drone from ever hitting the net resulting in getting stuck or a crash to the floor. The open source drone autopilots such as PX4 and ArduPilot have geofence functionality but seems to only implement failsafes (hold, return to home) once a breach occurs. We aim to implement geofence logic that identifies if a drone's thrust and trajectory will exceed the encolsure. The drone will be redirected along the boundary of the geofence, based on the angle of its approach. In testing of our logic, we will control a simulated drone with an Xbox controller. This is representative of a real use case in SOAR, and would allow for inexperienced pilots and even guests at the facility to fly safely.

Similarly, we will also implement a low altitude boundary to ensure a drone does not crash in the middle of a flight (This must be switched off when a land command is given).

We will leverage ROS to share information between the SITL, joystick controller and geofence monitor nodes. The planned framework is roughly scripted in the flowchart below.

![Framework](images/soar_geofence_gazebo_ros_diagram.png)

## PX4-MAVSDK

Our simulated drone will be running PX4 SITL in gazebo, thus we will use MAVSDK to connect and send commands.

- https://docs.px4.io/master/en/simulation/gazebo.html

Here is roughly what I did for installations to get started.

### MAVSDK
```
pip3 install mavsdk
```

### PX4-Autopilot
https://docs.px4.io/master/en/dev_setup/dev_env_linux_ubuntu.html#gazebo-jmavsim-and-nuttx-pixhawk-targets

Clone the repo in your HOME directory.
```
cd ~
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
```
```
bash ./PX4-Autopilot/Tools/setup/ubuntu.sh
```
I also had to run the following, which I then placed in `.bashrc`
```
source /usr/share/gazebo/setup.bash
```
#### To Run in Terminal

Navigate to `PX4-Autopilot`
```
cd ~/PX4-Autopilot
```
You can run the SITL (quadrotor) in gazebo with
```
make px4_sitl gazebo
```

## Simulation World

The soar_rover project has the facility visualized in Cesium, but does not have a gazebo world. For our project, we will build a gazebo world of the facility to conduct our simulation.

Links that might help:

- https://github.com/optimatorlab/SOAR
- https://docs.px4.io/master/en/simulation/gazebo_worlds.html
- https://docs.px4.io/master/en/simulation/gazebo.html
- http://gazebosim.org/tutorials?tut=build_world

The default PX4-Autopilot SITL launches gazebo in the `empty.world` but is not WGS84 enabled. In our world file we will need a `spherical_coordinates` tag, e.g.:
```
<spherical_coordinates>
    <surface_model>EARTH_WGS84</surface_model>
    <latitude_deg>42.99549724619581</latitude_deg>
    <longitude_deg>-78.79709535136203</longitude_deg>
    <elevation>170</elevation>
</spherical_coordinates>
```

Note: The launched gazebo environment doesn't allow us to zoom well, to do this edit the `sitl_run.sh` script to look like this:
```
# Disable follow mode
if [[ "$PX4_NO_FOLLOW_MODE" != "1" ]]; then
    follow_mode=""
else
    follow_mode="--gui-client-plugin libgazebo_user_camera_plugin.so"
fi
```
## Joystick Control

The drone will be controlled via an Xbox controller, using the `pygame` library. Similar to the actual radio controller, the left stick will control the throttle and yaw, the right stick will control pitch and roll. The signals will need to be mapped accordingly.

- https://github.com/optimatorlab/m3c_wg/blob/master/catkin_ws_gcs/m3c_wg/scripts/m3c_wg_joystick.py

## Geofence/Avoidance

