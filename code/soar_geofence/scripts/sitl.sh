#!/bin/bash

# This script will launch PX4 SITL and Gazebo
if ["$#" -lt 3]; then
    echo usage: sitl.sh model simulation_program
    exit 1
fi

set -e

model="$1"
program="$2"
world="$3"
sitl_bin="/${HOME}/PX4-Autopilot/build/px4_sitl_default/bin/px4"
src_path="/${HOME}/PX4-Autopilot"
build_path="/${HOME}/PX4-Autopilot/build/px4_sitl_default"
ros_args=""
verbose=""

model_name=$model

export PX4_HOME_LAT=42.99549724619581
export PX4_HOME_LON=-78.79709535136203
export PX4_HOME_ALT=150

echo SITL ARGS
echo sitl_bin: $sitl_bin
echo program: $program
echo model: $model
echo world: $world
echo src_path: $src_path
echo build_path: $build_path

rootfs="$build_path/tmp/rootfs" # this is the working directory
mkdir -p "$rootfs"

# To disable user input
if [[ -n "$NO_PXH" ]]; then
	no_pxh=-d
else
	no_pxh=""
fi

# init.d-posix/rcS startup script needs this variable
export PX4_SIM_MODEL=${model}
SIM_PID=0

# Set the plugin path so Gazebo finds our model and sim
source "$src_path/Tools/setup_gazebo.bash" "${src_path}" "${build_path}"

world="empty"
world_path="${src_path}/Tools/sitl_gazebo/worlds/${world}.world"

gzserver $verbose $world_path $ros_args &
SIM_PID=$!
# Check all paths in ${GAZEBO_MODEL_PATH} for specified model
IFS_bak=$IFS
IFS=":"
for possible_model_path in ${GAZEBO_MODEL_PATH}; do
    if [ -z $possible_model_path ]; then
        continue
    fi
    # trim \r from path
    possible_model_path=$(echo $possible_model_path | tr -d '\r')
    if test -f "${possible_model_path}/${model}/${model}.sdf" ; then
        modelpath=$possible_model_path
        break
    fi
done

gzserver $verbose $world_path $ros_args &
SIM_PID=$!

IFS=$IFS_bak

if [ -z $modelpath ]; then
    echo "Model ${model} not found in model path: ${GAZEBO_MODEL_PATH}"
    exit 1
else
    echo "Using: ${modelpath}/${model}/${model}.sdf"
fi

while gz model --verbose --spawn-file="${modelpath}/${model}/${model_name}.sdf" --model-name=${model} -x 5.00 -y 0.98 -z 0.83 2>&1 | grep -q "An instance of Gazebo is not running."; do
    echo "gzserver not ready yet, trying again!"
    sleep 1
done

if [[ -n "$HEADLESS" ]]; then
    echo "not running gazebo gui"
else
    # gzserver needs to be running to avoid a race. Since the launch
    # is putting it into the background we need to avoid it by backing off
    sleep 3
    nice -n 20 gzclient --verbose $follow_mode &
    GUI_PID=$!
fi

pushd "$rootfs" >/dev/null

# Do not exit on failure now from here on because we want the complete cleanup
set +e

sitl_command="\"${sitl_bin}\" $no_pxh -s ${build_path}/etc/init.d-posix/rcS -w ${build_path} -t \"${src_path}\"/test_data"
echo SITL COMMAND: $sitl_command

eval $sitl_command

popd >/dev/null

kill -9 $SIM_PID
if [[ ! -n "$HEADLESS" ]]; then
    kill -9 $GUI_PID
fi
