# Behaviors and FSM Project

#### Pippin Fleet, Austin Woolf, Pepper Wang

In this project, we were tasked to create a finite state machine with various behaviors for our Neato robot, using ROS and Python.

## Behaviors:

- [Emergency Stop](#emergency-stop)
- [Collision Avoidance](#collision-avoidance)
- [Wall Following](#wall-following)
- [Person Following](#person-following)

### Emergency Stop

meow meow meow meow meow

### Collision Avoidance

We used the Neato's LiDAR to detect if anything is too close to it (the threshold we chose was 0.2 meters). If there is anything too close in the Neato's forward-facing 90° "field of view", it will turn left until it no longer detects the obstacle.

### Wall Following

Our wall following algorithm:

![Diagram of Neato facing an angled wall, with lines showing LiDAR scan.](/media/neato_at_wall.png)

- We split the Neato's forward-facing field of view into 2 halves: the right and the left. Each of these is received as a list of numbers, each representing a distance in meters.
- For both the right and the left, we take squared reciprocals of each distance and then sum them all. This gives us a number, "closeness", that is smaller if the overall distances on that side are farther away, and larger if the distances on that side are closer.
- We assume that the wall is on the side that has higher closeness.
- We compare that side's closeness value to an "ideal closeness" value, which is a constant, to get the error.
- We set angular velocity scaling on that error.

Result:

![GIF of simulated Neato approaching wall and turning to be parallel with it, then curving away from it.](/media/wallfollowingsim.gif)

### Person Following

jklsdfjlskjlsdgjlksdf

## Finite State Machine

![Diagram showing the FSM's states and the triggers for transitioning between them.](/media/fsm_diagram.png)

We decided to make wall following the default behavior for the Neato. Certain conditions can cause state changes:

- If the bump sensor is triggered at any time, the Neato will stop completely. This takes precedence over any other state.
- If the front-facing portion of the LiDAR scan detects anything too close, collision avoidance will be triggered.
- The Neato will start in the wall following state. If it detects a potential "person" (see [Person Following](#person-following) for more details), person following will be triggered.
- If, during person following, the Neato stops detecting a person, it will go back to wall following.
