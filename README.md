# Final Project

- This repo is where you will store **all** of your documents for the course project.
- Please see [PROPOSAL.md](PROPOSAL.md) for a template for your **proposal**.

## Getting Started

mavsdk-Python `v0.20.0` and PX4-Autopilot SITL is required. See installations below.

### MAVSDK
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

Make sure `sitl.sh` is executable
```
cd soar_geofence/code/soar_geofence/scripts
chmod +x ./sitl.sh
```

### Catkin Workspace

Assumes you have a catkin workspace at `~/catkin_ws`.

Create our package once:
```
cd ~/catkin_ws/src
catkin_create_pkg soar_geofence
```
Copy and paste our `soar_geofence/code/soar_geofence` directory into the `~/catkin_ws/src` directory

```
cp -R ~/Projects/soar_geofence/code/geofence ~/catkin_ws/src
```
Build/make project:
```
cd ~/catkin_ws
catkin_make
```

### To Run

Have a joystick controller (Xbox 360) connected via USB.

Then run:

```
cd ~/catkin_ws/src/soar_geofence
./launch_soar_geofence.sh
```

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
