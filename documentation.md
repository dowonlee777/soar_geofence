# Documentation

## PX4 SITL Setup

We used the PX4-Autopilot SITL in Gazebo for this project, but we needed to modify a couple startup files for our use case and preferences. We moved the following startup scripts into our working directory and made edits to them.

1. `~/PX4-Autopilot/Tools/sitl_run.sh` moved to `~/catkin_ws/src/soar_geofence`
2. `~/PX4-Autopilot/build/px4_sitl_default/etc/init.d-posix/rcS` moved to `~/catkin_ws/src/soar_geofence/px4/etc`


### sitl_run.sh

### rcS

The PX4 SITL tries to load an existing parameter file saved in the `eeprom/` directory of the working directory (by default, `~/PX4-Autopilot/build/px4_sitl_default/tmp/rootfs`). If unable to find the parameter file, it creates one and saves it in the `eeprom/` directory. The default parameter files are unique to each drone model.

We need to edit one or more parameters (examples in the `Issues` section) for convenience. The editing of the parameters are "permanent", in that it saves it to the parameter file in `eeprom/`. We only know how to set parameters manually in the terminal, where the `px4` sitl is running:

```
param set <PARAM_NAME> <value>
```

Rather than having the user run this in the terminal and overwrite the default parameters, or edit the `rcS` script in the `PX4-Autopilot` project, we will modify the parameter file ourselves, save it to `~/catkin_ws/src/soar_geofence/px4/params/parameters_10016`, and have PX4 load this file.

We copied the `rcS` script into our directory:
```
cd ~/PX4-Autopilot/build/px4_sitl_default/etc/init.d-posix
cp rcS ~/catkin_ws/src/soar_geofence/px4/etc
```

Then we edited line `58` to be:
```
set PARAM_FILE ${soar_geo_path}/px4/params/parameters_"$REQUESTED_AUTOSTART"
```

Note: the `${soar_geo_path}` was exported in our `sitl_run.sh` script.


## Issues

### RC Failsafe:

Because we are not using an RC or running QGC to enable a virtual joystick, we need to disable the RC failsafe, otherwise we cannot takeoff Since we are flying SITL here, this should be safe.

See:
- https://githubmemory.com/repo/PX4/PX4-Autopilot/issues/18389
- https://github.com/PX4/PX4-Autopilot/pull/18160

We can do this by setting `COM_RCL_EXCEPT` to `4` in the terminal where PX4 SITL is running. But as documented in the `PX4 SITL Setup` Section, we made the parameter file to be set with this parameter value.
