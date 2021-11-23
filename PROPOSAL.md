 
# SOAR Geofence Gazebo

Team Members:
- Dowon Lee, dowonlee@buffalo.edu
- Dylan Czubak, dylanczu@buffalo.edu

--- 

## Project Objective

This course project is motivated by SOAR, an outdoor facility for drone research. It is a netted enclsoure allowing for both autonomous and manual flight. Although the netting prevents drones from escaping the facility, it would be ideal to prevent a drone from ever hitting the net resulting in getting stuck or a crash to the floor. The open source drone autopilots such as PX4 and ArduPilot have geofence functionality but seems to only implement failsafes (hold, return to home) once a breach occurs. We aim to implement geofence logic that identifies if a drone's thrust and trajectory will exceed the encolsure. The drone will be redirected along the boundary of the geofence, based on the angle of its approach. In testing of our logic, we will control a simulated drone with an Xbox controller. This is representative of a real use case in SOAR, and would allow for inexperienced pilots and even guests at the facility to fly safely.

Similarly, we will also implement a low altitude boundary to ensure a drone does not crash in the middle of a flight (This must be switched off when a land command is given).

We will leverage ROS to share information between the SITL, joystick controller and geofence monitor nodes. The planned framework is roughly scripted in the flowchart below.

![Framework](images/soar_geofence_framework.png)


## Contributions
- Proactive geofence logic


## Project Plan

First we'll build the Gazebo world of SOAR. Then we will get the PX4 SITL to run in the world, with GPS data enabled. We'll use PX4 and MAVSDK documentation to implement the SITL and use basic ROS messages/services to communicate between the nodes. 


## Milestones/Schedule Checklist
{What are the tasks that you need to complete?  Who is going to do them?  When will they be completed?}
- [x] Complete this proposal document.  *Due Nov. 2*
- [x] Research into suspected future problems or topics not covered in class 
- [ ] Custom SOAR Gazebo Model, DC
  - [ ] Create Main Poles x13
    - [ ] Correct Color, Location, & Size
  - [ ] Lights x2
    - [ ] Using light id: 1 as the origin of the model, with everything built off this dimension wise
  - [ ] Generate materials folder for asphault ground 
  - [ ] Find suitable replacement for enclosement mesh/ wire 
  - [ ] If it makes sense also add the three grass mounds
- [ ] Setting up Gazebo Sim and PX4 SITL
    - [x] Installation of PX4-Autopilot and mavsdk-Python. See README.md
    - [ ] Write separate shell script from PX4's `sitl_run.sh` (tailored to our needs) to launch Gazebo and PX4 SITL.
- [ ] `Uav.py` node
    - [ ] Connect to running PX4 SITL
    - [ ] Takeoff, land
    - [ ] Create `telemetry` thread and publish to `telem` topic
    - [ ] Implement Offboard Mode
        - [ ] Implement offboard functions in response to `joystick.py` node.
        - [ ] Implement overriding of offboard functions in response to `geofence_monitor.py` node.
- [ ] `joystick.py` node
    - [ ] Borrow code from `optimatorlab/m3c_wg`
    - [ ] Refine mappings if necessary and publish to `mav_cmd` topic
- [ ] `geofence_monitor.py` node
    - [ ] Identify if the drone flight and given `mav_cmd` will cause it to exceed the geofence
    - [ ] Send the overriding `mav_cmds` if necessary to make drone slide across geofence, or prevent altitude (rise/sink)

- [ ] Create progress report.  *Due Nov. 20*
- [ ] Necessary changes found due to errors arised during progress update 
- [ ] Create final presentation.  *Due Dec. 4*
- [ ] Provide system documentation (README.md).  *Due Dec. 14*


## Measures of Success
{How will you know you succeeded?  If you were to receive partial credit, what should we look for?}

- [ ] Gazebo World of SOAR is relatively accurate
- [ ] SITL drone flies given joystick commands
- [ ] SITL drone stops near geofence
- [ ] SITL drone moves along geofence based on angle of approach
