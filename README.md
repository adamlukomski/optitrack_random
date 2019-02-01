# Working with OptiTrack Motion Capture in ROS

This is a copy of: https://barelywalking.com/?p=440

This is one of the older things I did, but did not have enough time to make it into a post. So: the aim is to get a working stream of data from OptiTrack system into ROS Kinetic. A small catch: get individual points.

Ok, first of all - the access to the OptiTrack was courtesy of Poznan University of Technology, kudos to them.

First, let us check what is available: 

```
Motive 1.8.0 Final 64-bit
Prime 17W 15111,15107,15112,15110,15117,15121,14908,15105,15122,15106
Hardware Key

Toolbox:

Camera Calibration
Point Cloud
Rigid Bodies
Single Camera Tracking
VRPN Streaming
Trackd Streaming
NatNet Streaming
M Camera
M Subsystem
M Application UI
Marker History
Marker Trajectories
Camera Calibration
Volume Accuracy Tool
Synchronization

IP: 192.168.1.241
Multicast: 239.255.42.99
```

# VRPN test

My first option is to use VRPN to connect to it, so let me try building a Slackware VRPN package - the necessary set of modifications:

vrpn is being compiled with -DVRPN_GPL_SERVER=on

I added FindVRPN.cmake to vrpn_client_ros directory cmake/

I added in CMakeLists.txt a line with:
```
list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake)
```
and made the package.

So now to dummy test the vrpn:
edit the config file:
```
mcedit /usr/etc/vrpn.cfg
```
uncomment line vrpn_Tracker_NULL:
```
vrpn_Tracker_NULL Tracker0 2 2.0
```

launch the server:
First console:
```
vrpn_server
```
Second console:
```
vrpn_print_devices Tracker0@127.0.0.1
```
If everything is alright - let us proceed with ROS client.

# VRPN and ROS

Compile vrpn_client_ros: (I keep my ROS in /opt/ros/kinetic)
(you can be in home directory if you want, doesn't matter)
```
source /opt/ros/kinetic/setup.bash
mkdir vrpn_test
cd vrpn_test
mkdir src
catkin_make
cd src
git clone https://github.com/ros-drivers/vrpn_client_ros
cd ..
catkin_make_isolated -DCMAKE_INSTALL_PREFIX=/opt/ros/kinetic -DLIB_SUFFIX="64" -DCMAKE_BUILD_TYPE=Release --install
```

Now an important announcement:
<strong> VRPN streams only rigid bodies </strong>
Not cool, right? But we will fix it waaaaay later on, in Python. Right now, let us start it:

Motive:

Create a Rigid Body from a set of points.
Make sure there are no white spaces in the filename: e.g. RigidBody1.

VRPN in advanced options:
```
Broadcast VRPN Data: true
```

Now check if the tracker responds:
```
vrpn_print_devices RigidBody1@192.168.1.241
```
aaaand start ROS package vrpn_client_ros:

First console:
```
source /opt/ros/kinetic/setup.bash
roslaunch vrpn_client_ros sample.launch server:=192.168.1.241
```
Second console:
```
source /opt/ros/kinetic/setup.bash
rostopic echo /vrpn_client_node/RigidBody1/pose
```
a happy stream should be visible.

(PLACEHOLDER FOR EXPLANATION - you don't need it, but I do:
```
roslaunch vrpn_client_ros sample.launch server:=192.168.1.148
roslaunch mavros px4.launch fcu_url:="udp://:14550@192.168.4.1:14555" gcs_url:="udp://@192.168.4.2:14556
rosrun topic_tools relay /vrpn_client_node/(tracker name)/pose /mavros/mocap/pose rosrun topic_tools relay /vrpn_client_node/(tracker name)/pose /mavros/mocap/pose
```
ok, done, in case I forget it or lose it again)

Back to our usual program - what else can we do?

<h4>Maybe... MOCAP?</h4>

The setup for this one is as generic as humanly possible:
```
source /opt/ros/kinetic/setup.bash
mkdir mocap
cd mocap
mkdir src
catkin_make
cd src
git clone https://github.com/ros-drivers/mocap_optitrack
cd ..
```
Yeah, no surprises there. Now launch it:
#1 console
```
roslaunch mocap_optitrack mocap.launch
```
aaaand:
#2 console
```
rostopic list
rostopic echo /Robot_1/pose
```

What's the result?

```
header: 
  seq: 3438
  stamp: 
    secs: 1519816203
    nsecs: 344498680
  frame_id: "world"
pose: 
  position: 
    x: -1.3609367609
    y: -1.55265676975
    z: 0.809030890465
  orientation: 
    x: -0.0133089488372
    y: 0.00888985395432
    z: 0.605775594711
    w: -0.795474588871
```

No deal. Also, a note - the configuration file is static and written by hand:
```
/opt/ros/kinetic/share/mocap_optitrack/config/mocap.yaml
```
after only pointing him to a right multicast, it started working BUT only for rigid bodies - there is no individual marker info.

Any other bright ideas?

# python-optirx

Ok, so again, do the installation procedure for the package:
```
https://github.com/crigroup/optitrack
```
I did it by hand, so you know the drill:
```
catkin_make_isolated -D...
```
standard to /opt/ros/kinetic.
I got a couple of errors at the very start:
missing launch/ in share/optitrack/, ok, I did a copy from src
missing config/ - the same, make a copy
missing scripts/ - the same.

That's not a good start. Ok, now a quick sketch to get the basic data:
```
import optirx as rx

dsock = rx.mkdatasock(ip_address='0.0.0.0',multicast_address='239.255.42.99', port=1511)
version = (2, 7, 0, 0)  # NatNet version to use
while True:
    data = dsock.recv(rx.MAX_PACKETSIZE)
    packet = rx.unpack(data, version=version)
    if type(packet) is rx.SenderData:
        version = packet.natnet_version
    print packet 
```
And the result:
```
FrameOfData(frameno=846853, sets={'RigidBody1': [(-1.4107482433319092, 0.809095025062561, 1.4977911710739136), ...  tracked_models_changed=False)
```
Those three dots in the middle are from me - originally it exceeded the line limit in KWrite.

Sometimes the short version is also enough, I needed the multicast options, but just in case:
```
import optirx as rx

dsock = rx.mkdatasock()
version = (2, 9, 0, 0)  # NatNet version to use
while True:
    data = dsock.recv(rx.MAX_PACKETSIZE)
    packet = rx.unpack(data, version=version)
    if type(packet) is rx.SenderData:
        version = packet.natnet_version
    print( packet )
```




Now, if you would like to store a single packet for later:
```
import pickle

f = open('store.pckl', 'wb')
pickle.dump(packet, f)
f.close()
```
and to restore it:
```
f = open('store.pckl', 'rb')
packet = pickle.load(f)
f.close()
```

... and in case you don't have OptiTrack on hand and no pennies to buy one (like me):
store.pckl


And that's it - the individual points are there, so we're finished.
