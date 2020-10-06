# racing_line_RL
Racing line estimation using deep reinforcement learning.

## Model
The model interface is similar to OpenAI gym:

### State space
The state space is an abstraction of the set of measurements from an array of sensors. Useful "sensor" are:
| Name  | Range | Description |
| --- | --- | --- |
| angle | [-π,+π] | Angle between the car axis and the track axis |
| distance | [-width, +width] | Distance of the car and the middle of the track (width is the track width) |
| position | [] | Distance from the car and multiple points of the track |
| speed | [-max_speed, max_speed] | Three dimensional vector for speed |
| inclination | [-max_incl,+max_incl] | Vertical inclination of the vehicle |

### Action space
| Name  | Range | Description |
| --- | --- | --- |
| steering | [-1,+1] | Steering percentage |
| brake | [-1,0] | Breaking percentage |
| accelerator | [0,+1] | Accelerator percentage |
| inclination | [-1, +1] | Vertical inclination (request) |

The brake and accelerator actions can be combined to reduce action space, and avoid breaking while accelerating.

### Reward
TODO

### Methods
- **step(action) : tuple[3]**
  
  Returns the envionment observation given an action. The tuple represents an opservaion: it is made of the state to which we transitioned, the reward coming from the transition and wether the transition leads to a terminal state.

- **reset() : state**
  
  Returns initial state of the environment and resets the world parameters.
 
- **render() : nil**
  
  Visualizes the current state of the environment.

### Fields
TODO

## Resources
### AI
- RL for track following [article](https://medium.com/@sdeleers/autonomous-car-with-reinforcement-learning-part-2-track-following-4ffbf7aa33d1).
- Keras for TORCS simulation [article](https://yanpanlau.github.io/2016/10/11/Torcs-Keras.html).
- Racing line optimization using MDPs with a simple 2d spatial state space.
  - Optimization of ideal racing line, Werkstuk-Beltman [paper](https://science.vu.nl/en/Images/werkstuk-beltman_tcm296-91313.pdf).
### OpenGL
- OpenGL tutorial [repo](https://github.com/opengl-tutorials/ogl) and [website](http://www.opengl-tutorial.org).
