#!/usr/bin/env bash


if [ "$#" -gt 2 ]; then
	echo usage: launch_soar_geofence.sh --lat= --lon=
	exit 1
else
	for i in "$@"; do
		case $i in 
			--lat=*)
			LAT="${i#*=}" # regex sub remove "=" and anything before
			shift # past argument=value
			;;
			--lon=*)
			LON="${i#*=}"
			shift
			;;
			*)
			;;
		esac
	done
fi

if [ -n "$LAT" ] && [ -n "$LON" ]; then
	export PX4_HOME_LAT=$LAT
	export PX4_HOME_LON=$LON
else
	export PX4_HOME_LAT=42.9955301
	export PX4_HOME_LON=-78.7970664
fi

PROCESS="ros"
RESULT=`pgrep ${PROCESS}`

if [ "${RESULT:-null}" != null ]; then
	echo "ROS is already running."
	# echo -n "Do you want to kill ROS ([Y]/n)? "
	read -p "Do you want to kill ROS ([Y]/n)? " answer1
	answer1=${answer1:-y}
	# read answer1
	if echo "$answer1" | grep -iq "^y" ;then
		echo "Stopping ROS now..."

		# Stop all running nodes:
		rosnode kill --all
		
		# Stop roscore:
		pkill -x roscore
		pkill -x roslaunch
		pkill -x rosmaster		
		pkill -x rosout

		echo "DONE."
	else
		echo "Sorry, can't start mission control node.  Bye."
		exit
	fi

else
	echo "ROS is not running."
fi

# https://stackoverflow.com/questions/3512055/avoid-gnome-terminal-close-after-script-execution
START_ROS="roscore"
SCRIPT1="./sitl_run.sh iris gazebo SOAR_World"
SCRIPT2="rosrun soar_geofence uav.py"
SCRIPT3="rosrun soar_geofence joystick.py"

gnome-terminal --tab --title "ROS" -e "bash -ic \"export HISTFILE=${HOME}/.bash_history_junk1; $START_ROS; history -s $START_ROS; exec bash\"" 

sleep 3s

gnome-terminal --tab --title "PX4 SITL Gazebo" --working-directory=${HOME}/catkin_ws/src/soar_geofence -e "bash -ic \"export HISTFILE=${HOME}/.bash_history_junk1; $SCRIPT1; history -s $SCRIPT1; exec bash\"" 

gnome-terminal --tab --title "UAV Node" --working-directory=${HOME}/catkin_ws/src/soar_geofence -e "bash -ic \"export HISTFILE=${HOME}/.bash_history_junk2; $SCRIPT2; history -s $SCRIPT2; exec bash\""

gnome-terminal --tab --title "Joystick Node" --working-directory=${HOME}/catkin_ws/src/soar_geofence -e "bash -ic \"export HISTFILE=${HOME}/.bash_history_junk3; $SCRIPT3; history -s $SCRIPT3; exec bash\"" 

