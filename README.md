# Behaviors and FSM Project

#### Pippin Fleet, Austin Woolf, Pepper Wang

In this project, we were tasked to create a finite state machine with various behaviors for our Neato robot, using ROS2 and Python.

## Finite State Machine

![Diagram showing the FSM's states and the triggers for transitioning between them.](/media/fsm_diagram.png)

We decided to make wall following the default behavior for the Neato. Certain conditions can cause state changes:

- If the bump sensor is triggered at any time, the Neato will stop completely. This takes precedence over any other state.
- If the front-facing portion of the LiDAR scan detects anything too close, collision avoidance will be triggered.
- The Neato will start in the wall following state. If it detects a potential "person" (see [Person Following](#person-following) for more details), person following will be triggered.
- If, during person following, the Neato stops detecting a person, it will go back to wall following.

## Behaviors

- [Emergency Stop](#emergency-stop)
- [Collision Avoidance](#collision-avoidance)
- [Wall Following](#wall-following)
- [Person Following](#person-following)

### Emergency Stop

The primary method to avoid obstacles is “Collision Avoidance” using the Neato’s LiDAR. However, if something is missed and the Neato bumps something, its bump sensor will immediately detect it, causing it to stop doing any other activity.

The simulated Neato doing an emergency stop can be seen at the end of the person following video.

### Collision Avoidance

We used the Neato's LiDAR to detect if anything is too close to it (the threshold we chose was 0.2 meters). If there is anything too close in the Neato's forward-facing 90° "field of view", it will turn left until it no longer detects the obstacle.

[Video of simulated Neato avoiding collision with wall](https://olincollege-my.sharepoint.com/:v:/g/personal/pwang_olin_edu/IQDofBbstbdsSJZMlvClnOwNAfKvC09fnIUuASjeqLVgT7w?e=dMSqgC&nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJTdHJlYW1XZWJBcHAiLCJyZWZlcnJhbFZpZXciOiJTaGFyZURpYWxvZy1MaW5rIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXcifX0%3D)

### Wall Following

Our wall following algorithm runs each frame and is as follows:

- We split the forward-facing 180° of the Neato's field of view into 2 halves: the right and the left. Each of these is received as a list of numbers, each representing a distance in meters.

![Diagram of Neato facing an angled wall, with lines showing LiDAR scan.](/media/neato_at_wall.png)

- For both the right and the left, we take reciprocals of each distance and then sum them all. This gives us a number, "closeness", that is smaller if the overall distances on that side are farther away, and larger if the distances on that side are closer.

$$\mathrm{closeness} = \sum^d \frac{1}{d} $$

- We assume that the wall is on the side that has higher closeness.
- We compare that side's closeness value to an "ideal closeness" value, which is a constant, to get the error.
- We store the error from the previous frame and use it and the current error to determine the current rate of change of error with respect to time.
- We scale both the error and its rate of change by constants and add the results together to get the angular velocity.
- We set the linear velocity to half of the Neato’s linear velocity and clamp the angular velocity to not exceed half of its maximum angular velocity. This way the Neato’s maximum wheel velocity cannot be exceeded.

#### Result:

The Neato smoothly moves around the world, moving towards the closest wall that’s in front of it while keeping a safe distance from it. It can move around 90° corners without needing to go into collision avoidance mode. It doesn’t oscillate closer and further from the wall as it would if the rate of change of error didn’t affect angular velocity.

[Video of simulated Neato during wall following](https://olincollege-my.sharepoint.com/:v:/g/personal/pwang_olin_edu/IQCw82-khCmUT5X8Nl9OMrTEAbDxxazYetnbQDZEsN6KrrI?e=zle0Wg&nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJTdHJlYW1XZWJBcHAiLCJyZWZlcnJhbFZpZXciOiJTaGFyZURpYWxvZy1MaW5rIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXcifX0%3D)

### Person Following

Our person following algorithm runs each frame and is as follows:

- We go through all 360° of the Neato’s LiDAR scan, and for every pair of adjacent points, we compare the points’ distances from the Neato. If they are far apart (the difference is over one meter), we assume it might be a person and add the closer point and its angle to a list.

![Diagram of Neato facing a wall with an object in front of it.](/media/neato_find_person.png)

- If this list has at least 1 point, the person-following state is triggered.
- We select the closest “potential person” point as the point to follow. From the scan data, we have its angle (with respect to the Neato’s heading) and its distance from the Neato.
- Our goal is to move in a smooth arc to reach the person so the Neato doesn’t waste time turning towards a target that could move.
- We use the angle and distance to calculate the length of the arc from the Neato to the point using this formula:

$$ \mathrm{Arc\ length} = \frac{d \cdot \theta}{\sin(\frac{\theta}{2})} $$

- where d is the distance in meters and is the angle in radians. We convert the angle, which is stored as indices in a list, from degrees to radians.

![Diagram of calculation of arc from Neato to object.](/media/neato_arc.png)

- After this arc length is calculated, we can calculate the amount of time the Neato will take to travel along that arc. Using this, we determine an angular velocity to use.
- During person following, LiDAR collision avoidance is disabled, to allow the Neato to run into the object it’s following; this will trigger the bump sensor causing the Neato to stop.

#### Result:

The Neato smoothly drives towards the nearest freestanding object until it hits it and stops. If the object moves before the Neato reaches it, the Neato will continue to follow it as if it was always there. If the object moves far enough away to no longer be the closest freestanding object, the Neato will change its target.

[Video of simulated Neato during person following](https://olincollege-my.sharepoint.com/:v:/g/personal/pwang_olin_edu/IQABtrCjnAMERaUsXZ-jbKi3AWRO2GUK3Fda_L2WpvCxLsM?e=bqtFKd&nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJTdHJlYW1XZWJBcHAiLCJyZWZlcnJhbFZpZXciOiJTaGFyZURpYWxvZy1MaW5rIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXcifX0%3D)

## Contributions

The majority of this project was done by our whole team together, with smaller parts being done individually or in pairs.

Together:

- Implementation of drive in square (which didn’t end up being included in the FSM), collision avoidance, and emergency stop
- The FSM structure
- Algorithm development for person following and wall following
- Testing, debugging, and documentation

Austin:

- Implementation and improvement on wall following

Pepper & Pippin:

- Implementation of person following

## Interacting with the project

Steps for running the code for this project:

- Set up SSH and install ROS and the Neato packages by following steps 2-4 on [this page](https://comprobo26.github.io/How%20to/setup_your_environment).
- Clone the project repository by running the following command while in the `ros2_ws/src` directory:

`git clone git@github.com:olincollege/CompRobo-FSM-Yeeto-your-Neato.git`

- Do the following steps in the `ros2_ws` directory:
- Build and source the project by running the following command:

`colcon build --symlink-install && source ~/ros2_ws/install/setup.bash`

- Finally, run the project by running the following command:

`ros2 run ros_behaviors_fsm finite_state_controller`

- It can be run either on a physical Neato or in simulation:
  - [Physical Neato instructions](https://comprobo26.github.io/How%20to/use_the_neatos)
  - [Simulation instructions](https://comprobo26.github.io/How%20to/use_the_simulator)

## Limitations

- If there is a large jump in LiDAR distance data the Neato will go to it even if it isn’t a person or a freestanding object.
- While the Neato is “Person Following” “Collision Avoidance” isn't active, therefore it can hit stuff in its path and will have to “Emergency Stop”.
- Once the Neato’s bump sensor is triggered it stops forever, there is no way of getting out of “Emergency Stop”.
- The “Collision Avoidance” algorithm always turns to the left, there is no way for it to turn to the right even if that would make more sense in the context of “Person Following” or “Wall Following”.
- Once the Neato has found the “person” it will bump into it triggering “Emergency Stop” and ending the program completely.

## Takeaways

Some of the things we learned:

- The basics of ROS2: how to subscribe and publish to the Neato's topics and write architecture around ROS2's interfaces
- Using our code with both physical Neatos and the Gazebo simulation
- Effectively collaborating with Git
- Writing closed loop control algorithms
- Using the VSCode Live Share extension
