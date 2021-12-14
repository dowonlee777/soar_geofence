# SOAR Geofence Gazebo

Project Name: `soar_geofence`

Team Members:
- Dowon Lee, dowonlee@buffalo.edu
- Dylan Czubak, dylanczu@buffalo.edu

## Project Description

Our project provides the means to fly a drone in the SOAR facility manually, using a joystick (PlayStation or Xbox controller) with minimal risk of crashing into the netted enclosure as well as the ground. To develop this we leveraged the PX4 autopilot's SITL (Software-in-the-Loop) and their Gazebo simulation. 

The framework below is different from what was proposed as we began to understand how to implement this project. It consists of three major components, the PX4 SITL in Gazebo, and the ROS nodes `UAV` and `Joystick`. 

![](images/soar_geofence_framework2.png)

While we use PX4's SITL in a Gazebo simulation, we created and use our own world, which is modeled after the SOAR facility. Details on how we built the world will be covered in the next section.

The SITL is waiting to be connected to, which our Python ROS node, `UAV` will do through `MAVSDK`. The `Joystisck` node connects to an available controller and publishes the signals at a rate of `2 hz` from the sticks to the `vyxyz_yaw_cmd` topic, which represents velocities in the x,y,z directions and yaw speed in m/s. The commands for starting `Offboard` Mode, taking off and landing are done through button signals published to a separate topic: `mav_cmd`.

The `Monitor Geofence` block takes in the most recent velocities and yaw message in addition to the telemetry (lat, lon), and runs the geofence logic before sending the command to the STIL, at a rate of `5 hz`. The specifics in the geofence logic are outlined in a separate section.

### Gazebo World

First, we created a Gazebo world of the SOAR facility. The dimensions of the pole placements can be seen in the image below, courtesy of SOAR's GitHub page: https://github.com/optimatorlab/SOAR

![](images/SOAR_dims_1.png)

By default, the Gazebo simulator does not have a sense of an ellipsoidal earth and uses Cartesian coordinates (x,y,z). However, we can specify the latitude, longitude and MSL altitude at the origin of the Gazebo world, using the `<spherical_coordinates>` tag in the world file. We defined this origin as pole number `10`, in the diagram. The latitude, longitude and altitude of each pole is once again provided by SOAR's GitHub page. While we have now specified to Gazebo the geo-location of the origin, we could not place the poles by specifying their latitude and longitude. Thus, we needed to convert the change in latitdue and longitude of each pole from the origin, to `x` and `y` lengths in meters. Rather than using an estimation calculated using the radius of the Earth, we simply estimated the difference of latitude and longitude for a 1 meter offset in the `y` and `x` directions, respectively, in the Gazebo world. In order to do this, we leverage the telemetry reported by the PX4 SITL, which we are publishing to a ROS topic, named `telem`. By moving the drone 1 meter in both directions, we captured the latitude and longitude values reported by the SITL and calculated a constant conversion. This resulted in the rough estimates: 

|   |           Change per `1m` |
| -------   |  -------   |
| latitude |`0.0000088`  |
| longitude | `0.0000122`|

We used these constants to calculate the (x,y) positions of each pole.

![](images/soar_gazebo.png)

### Geofence Logic

Our default geofence is defined by 4 coordinates that define an inner rectangle of SOAR, as seen in the dimension diagram from earlier. From these coordinates we define the fences. We assume the adjacent coordinates in the list given share an edge, or "fence". The default geofence is defined by a JSON file located in `/soar_geofence/code/soar_geofence/geofences/`. A custom geofence using the default format can be saved here and loaded when running the `uav.py` script. 

The following is the JSON contents of the default geofence:

```
{
    "geofence": {
        "poly": [[42.99559635044619, -78.79735971011293, 181.28],
            [42.99531277502557, -78.79685522306578, 180.59],
            [42.99551134918702, -78.79665526993782, 180.9],
            [42.99579492459777, -78.79715975860931, 181.44]],
        "ceilingMetersAGL": 22,
        "minAGL": 2,
        "closeToFenceDist": 4,
        "takeOverDist": 2,
        "cornerDist": 2
    }
}
```

| JSON Geofence Attribute | Value  		 |
| --------------------    | ---------------- |
| `poly`			  |    List of coordinates: [ [lat, lon, alt], [lat, lon, alt] ... ]|
| `ceilingMetersAGL`     | Maximum altitude above ground, in meters 		  |
| `minAGL` 				 | Minimum altitude above ground, in meters        |
| `closeToFenceDist`     | The distance to fence at which the uav begins to slow down (if flying into fence) |
| `takeOverDist`         | The distance to fence at which the uav is redirected (if flying into fence)|
| `cornerDist` 			  | The distance between two adjacent fences to be considered in the corner, at which the uav stops (if flying into fence) |

We will reference this figure to describe our logic:

![](images/geofence_diagram_2.png)

The first step is to be able to calculate perpendicular distances to the fences/edges. This can be done by using the `veroviz` Python package. Using the function `closestPointLoc2Path`, we can find the closest (lat, lon) coordinate along a path, in our case a fence, to the drone's location. We then find the distance from the drone to this coordinate, using a geodesic distance function, from the `geopy` package. We find the distances to each fence and reference the fence with the minimium distance, when redirecting the drone. The coordinate and distance is shown in figure below as the red dot and dashed line to the drone.

If the distance calculated is `<= closeToFenceDist`, we then proceed to determine whether the drone is headed into the fence. We do this by using the drone's heading and velocities `vx` and `vy`. The resulting value is the velocity heading (in degrees), from North. Because the velocity heading is referenced from North, we can determine if this angle is not within the safe angles of the fence. The safe angles for each fence are pre-calculated, from the heading required to travel from one vertex to the other, of a fence. In the figure, the `127` degrees is the heading required to travel along that fence. The safe angles are therefore between `(127, 307)` degrees. Any value below 127 or above 307, would be directed into the fence. 

One the velocity heading is deemed to be directed into the fence and the distance to fence is `<= takeOverDist`, the next step is to calculate the velocities necesssary to slide along the fence.

In the figure, the velocity heading is 70 degrees. Because 70 is closer to 127 than 307, the resulting velocity heading will be 127 instead of 307. And so, the drone travels to the right. In order to calculate the unit vectors `vx` and `vy` that results in this heading, we need to know the angle `a` in the figure. We can calculate this angle using the drone's body heading (50 degrees) and the goal velocity heading. Because the drone's heading is facing 50 degrees from North, the angle now from its heading to 127 (goal velocity heading) is 77 (`127-50`) In this case, the angle `a` is simply this heading, 77. We can then calculate both the `vx` and `vy` necessary for the drone to travel at the angle `a`, from its current heading. **Note**: we assumed a unit vector, where the magnitude is 1. 

Depending on which quadrant the angle falls, here is how `vx` and `vy` are calculated.

| `a` | vx 	| vy |
| --------------  | ---- | ---- |
| <= 90		  | cos(a) | sin(a) |
| <= 180		| - cos(180-a) | sin(180-a) |
| <= 270 		| - cos(270-a) | - sin(270-a) |
| <= 360 		| cos(360-a) | - sin(360-a) |

We multiply the unit vectors by the magnitude of the original velocities given by the joystick user.

The drone will keep sliding if the user keeps sending the drone in the direction of the fence, until it has reached a corner. The distance to two adjacent fences at which a corner is identified is specified by `cornerDist`. If the two distances are `<= cornerDist` and the user is sending the drone into either fence, `vx` and `vy` are set to 0.


For minimum and maximum altitudes, we define a threshold from `ceilingMetersDist` and `minAGL`, in which the drone is slowed by half its speed. When it reaches the next threshold, the `vz` is set to 0. If drift occurs while the user is not giving velocity inputs and it goes past the limits, we give a small adjustment so that it does not keep drifting past the boundary.

---

## Contributions

We have implemented an interesting geofence environment where the drones do not simply hold, land or RTL when a breach occurs, but instead remap incoming velocities that will breach a fence to slide along this fence.

With some tuning, we hope this will allow guests at SOAR to fly a drone safely and provide the groundwork to add improvements to the system.

## Installation Instructions

We assume you are running Ubuntu 20.04 and have `ROS Noetic`, `catkin` and `Gazebo-11` installed in your system.

List of Prerequisite Software:
- Python 3.6+
- Python MAVSDK
- PX4-Autopilot / SITL
- Python veroviz

### MAVSDK

We use the MAVSDK-Python API to interface with the MAVLink enabled PX4 drone, specifically version `0.20.0`. Note that Python 3.6+ is required.

```
pip3 install mavsdk==0.20.0
```

### PX4-Autopilot

- https://docs.px4.io/master/en/simulation/gazebo.html
- https://docs.px4.io/master/en/dev_setup/dev_env_linux_ubuntu.html#gazebo-jmavsim-and-nuttx-pixhawk-targets

Clone the repo in your HOME directory.
```
cd ~
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
```
Run the following, this may take some time.
```
bash ./PX4-Autopilot/Tools/setup/ubuntu.sh
```

### soar_geofence

Clone our repo in your `Projects` directory:
```
cd ~/Projects
git clone https://github.com/dowonlee777/soar_geofence.git
```


### Catkin Workspace

This assumes you have a catkin workspace at `~/catkin_ws/`.

Create our package:
```
cd ~/catkin_ws/src
catkin_create_pkg soar_geofence
```
Copy and paste `~/Projects/soar_geofence/code/soar_geofence/` directory into the `~/catkin_ws/src` directory

```
cp -R ~/Projects/soar_geofence/code/geofence ~/catkin_ws/src
```
Build/make project:
```
cd ~/catkin_ws
catkin_make
```

---

## Running the Code

First, have a joystick controller (Xbox One, Playstation 4, or Playstation 5) connected via USB or Bluetooth.

Navigate to the catkin package `soar_geofence`:

```
cd ~/catkin_ws/src/soar_geofence
```
You can then use the `launch_soar_geofence.sh`. This will spawn multiple necessary processes in separate terminal tabs.
```
./launch_soar_geofence.sh --x=<meters> --y=<meters>
```
- You may specify the `x` and `y` coordinate in the Gazebo world frame, where the drone will spawn
- The default is (20, 0)
- Note that the origin (0,0) is right on a pole.

The spawned tabs consist of the following processes:

- `roscore`
- `sitl_run.sh`
- `uav.py`
- `joystick.py`

If you need to cancel one process, you may CTRL-C the process and rerun that process in the same terminal. (No need to rerun `launch_soar_geofence.sh`)

### 1. `sitl_run.sh`

This script launches the SITL and Gazebo. 

Usage:
```
./sitl_run.sh iris gazebo SOAR_World --x=<meters> --y=<meters>
```

If you wanted to load a separate Gazebo world, you may create a valid Gazebo `.world` file and save it to `~/catkin_ws/src/soar_geofence/worlds/`. Then specify it instead of `SOAR_World` in the command above. However, be sure to define the `<spherical_coordinates>` tag in your world file.

### 2. `uav.py`

This script launches the UAV node to connect to the SITL and send MAVSDK commands. 

Usage:
```
rosrun soar_geofence uav.py --geofence <geofence filename>
```

The `--geofence` flag is optional, by default we use the `default.json` geofence, located in `~/catkin_ws/src/soar_geofence/geofences/`. 

If you had a JSON file, `myGeofence.json`, you may save it to the geofences directory and use the command:
```
rosrun soar_geofence uav.py --geofence myGeofence
```

### 3. `joystick.py`

This script immediately tries to connect to an available joystick controller. If none is found this script will terminate.

Usage:
```
rosrun soar_geofence joystick.py
```
---

## Measures of Success
<TABLE>
<TR>
	<TH>Measures of Success</TH>
	<TH>Status</TH>
</TR>
<TR>
	<TD>Gazebo World of SOAR is relatively accurate.</TD>
	<TD>100%</TD>
</TR>
<TR>
	<TD>SITL drone flies given joystick commands.</TD>
	<TD>100%</TD>
</TR>
<TR>
	<TD>SITL drone moves along geofence based on angle of approach.</TD>
	<TD>100%</TD>
</TR>
<TR>
	<TD>SITL drone stops at the corners of geofence.</TD>
	<TD>100%</TD>
</TR>
<TR>
	<TD>SITL drone cannot ever escape geofence.</TD>
	<TD>99.9% (Recent tests are successful, but you never know)</TD>
</TR>
<TR>
	<TD>SITL drone returns or is able to re-enter geofence if escaped.</TD>
	<TD>90%. (It is possible to manually re-enter, but no autonomous commands yet)</TD>
</TR>
</TABLE>

---

## What did you learn from this project?
*For example, what concepts from class do you now have a solid understanding of?  What new techniques did you learn?*
*Also, what challenges did you face, and how did you overcome these?  Be specific.*

*Challenges:*
- Incorporating a life like 'cage' or 'fence' into the Gazebo world and attached to the poles. Two options were investigated. The first being boxes dragged into walls that would be close to 100% transparent. The second was using smaller boxes that would import a material similar in looks to a fence and only display on one side of the box. Making the rest of the box transparent. A purely transparent box was not implemented as it would potentially interfere with our GeoFence, where we would not know at times if the drone was stopped due to out algorithim or the trasparent box. The second option presented a challenge with mirroring a fence material into a box in order to replicate it over the entire outer perimeter. This took a back seat until the GeoFence logic was near completation. 
- Understanding exactly which geometry parameters that were needed to be taken into account in order to take control of the drone upon coming close to a wall or corner.  The logic behind finding distance and angle to the nearest fence and corner pole. Defining the acceptable degree of motion while taking into account the velocity heading of the drone and walls angle in relation to due North. Upon knowing the drone's angle of attack on the nearest wall, only allowing velocity application in the axis that won't move the drone closer to the fence. Once the drone was clear from the fence re-allowing velocity cotrol on that axis. 

---

## Future Work

- Improve upon Gazebo default 'follow' drone camera angle. Currently does not support velocity heading direction or altitiude changes.  
- Exclusion GeoFence for interior ojbects most notably the lightpoles and for anything in the future that may be added to the interior of the SOAR Facility. 
- We could use more precise slowing down of the drone when approaching a geofence so that it can get as close to the geofence as possible, but never outside.
---

## References/Resources

*What resources did you use to help finish this project?*
- Include links to Websites.  Explain what this Website enabled you to accomplish.

- Getting accustomed to editing make a custom Gazebo world
	- http://gazebosim.org/tutorials?tut=model_editor
	- https://learn.turtlebot.com/2015/02/03/6/
- VeroViz: Vehcile Routing Visualization
	- https://veroviz.org/
- PyGame: Python Module for connecting a Microsfot or Sony controller with minimal customizations
	- https://www.pygame.org/news
- PX4 Github Page: Drone Usage in a Gazebo Enviroment and Controlling it  
	- https://github.com/PX4/PX4-Autopilot 

- Python MAVSDK:
	- https://mavsdk.mavlink.io/main/en/python/

--------------------------------------------------------------------------------------------------------------------------------------------------------

## Organizing your Repository
For consistency, please use the directory structure described below, where `projectname` should be replaced with the actual catkin_ws name of your project.
	
```
PROPOSAL.md
README.md
Images/	
code/projectname/	
	scripts/
	msg/
	srv/
	CMakeLists.txt
	package.xml
```		

- A sample README file [may be found here](README_template.md)
- `Images/` is a directory (folder) for storing the graphics for your README.
- `code/projectname/` is a directory for your ROS code.  Replace `projectname` with the name of your catkin package.
	- Within this directory you should have `CMakeLists.txt`, `package.xml`, a `scripts/` directory, most likely a `msg/` directory, and possibly a `srv/` directory (if your project uses services).  
- See `06_Followbot` for an example of the directory structure.


---

## Project Grading

Grades for the final project will be based on the following percentages and content:

- Proposal (15%)
- Progress Report (10%)
- Final Documentation and Code (50%)
	- Did you address issues from the presentation feedback?
	- How did you do on the "measures of success"?
	- Can the instructor successfully install the prereqs?
	- Can the instructor successfully run the code?  (I highly recommend that you find someone to test this for you)
	- Does the code do what it's supposed to?
- Project Demonstration (25%)
	- Did you prepare/rehearse for this presentation?
	- Is the README neatly formatted?
	- Is the README (nearly) complete?
	- Was the code submitted/organized properly?  Are filenames correct?  Code in the proper directories/subdirectories?
	- Are the installation instructions complete?
	- Are the instructions for running the code complete?
	- Were you able to answer technical questions about your project?
	- How well were you able to demonstrate the actual implementation?
