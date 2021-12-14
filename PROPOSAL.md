 
# SOAR Geofence Gazebo

Team Members:
- Dowon Lee, dowonlee@buffalo.edu
- Dylan Czubak, dylanczu@buffalo.edu

--- 

## Project Objective

This course project is motivated by SOAR, an outdoor facility for drone research. It is a netted enclsoure allowing for both autonomous and manual flight. One of the many interests of this facility is to provide a system for safe manual flight of drones so that even visitors, who have never flown a drone, can do so with minimal risk of crashing. Although the netting prevents drones from escaping the facility, if a drone hits the netting it will likely get stuck and it becomes difficult (potentially expensive) to retrieve. A geofence is a solution to this problem, and although drone autopilots, such as PX4 and ArduPilot, can be given geofences, they seem to simply implement failsafes (hold, return to launch) once a breach occurs. Our project implements a slightly more proactive and interesting geofence logic.

Based on the angle of approach, the drone will be redirected along the boundary of the geofence. In testing of our logic, we will control a simulated PX4 drone with a joystick (PS4/Xbox).

Similarly, we will also implement altitude boundaries to ensure a drone does not crash in the middle of a flight or surpass the maximum altitude.

We will leverage ROS to share information between the SITL, joystick controller and geofence monitor nodes. The planned framework is roughly scripted in the flowchart below.

![Framework](images/soar_geofence_framework.png)


## Contributions
- Gazebo World of SOAR
- Proactive geofence logic


## Project Plan

First we'll build the Gazebo world of SOAR. Then we will get the PX4 SITL to run in the world, with GPS data enabled. We'll use PX4 and MAVSDK documentation to implement the SITL and use basic ROS messages/services to communicate between the nodes. 


## Milestones/Schedule Checklist
{What are the tasks that you need to complete?  Who is going to do them?  When will they be completed?}
- [x] Complete this proposal document.  *Due Nov. 2*
- [x] Research into suspected future problems or topics not covered in class 
- [x] Custom SOAR Gazebo Model
  - [x] Create Main Poles x13
    - [x] Correct Color, Location, & Size
  - [x] Lights x2
    - [x] Using Pole #10: 1 as the origin of the model, with everything built off this dimension wise 
  - [ ] Find suitable replacement for enclosement mesh/ wire 
- [x] Setting up Gazebo Sim and PX4 SITL
    - [x] Installation of PX4-Autopilot and mavsdk-Python. See README.md
    - [x] Write separate shell script from PX4's `sitl_run.sh` (tailored to our needs) to launch Gazebo and PX4 SITL.
- [ ] `Uav.py` node
    - [x] Connect to running PX4 SITL
    - [x] Takeoff, land
    - [ ] Create `telemetry` thread and publish to `telem` topic
    - [ ] Implement Offboard Mode
        - [ ] Implement offboard functions in response to `joystick.py` node.
        - [ ] Implement overriding of offboard functions in response to `geofence_monitor.py` node.
- [x] `joystick.py` node
    - [x] Borrow code from `optimatorlab/m3c_wg`
    - [x] Refine mappings if necessary and publish to `mav_cmd` topic
    - [x] Check Bluetooth Connections 
- [ ] `geofence_monitor.py` node
    - [ ] Identify if the drone flight and given `mav_cmd` will cause it to exceed the geofence
    - [ ] Send the overriding `mav_cmds` if necessary to make drone slide across geofence, or prevent altitude (rise/sink)

- [x] Create progress report.  *Due Nov. 20*
- [x] Necessary changes found due to errors arised during progress update 
- [x] Create final presentation.  *Due Dec. 15*
- [x] Provide system documentation (README.md).  *Due Dec. 15*


------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Measures of Success
{How will you know you succeeded?  If you were to receive partial credit, what should we look for?}
- Working Custom Gazebo Model
- Ability to launch PX4 drone in model and move around freely 
- Demonstrate our geofence code from a multitude of different entrances 

- [x] Gazebo World of SOAR is relatively accurate
- [x] SITL drone flies given joystick commands
- [ ] SITL drone stops near geofence
- [ ] SITL drone moves along geofence based on angle of approach
