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

The brake and accelerator actions can be combined to reduce action space, and avoid breaking while accelerating.

### Reward
TODO

### Methods
#### **step(action) : tuple[3]**

  Returns the envionment observation given an action. The tuple represents an opservaion: it is made of the state to which we transitioned, the reward coming from the transition and wether the transition leads to a terminal state.

#### **reset() : state**

  Returns initial state of the environment and resets the world parameters.

#### **render() : nil**

  Visualizes the current state of the environment.

### Fields
TODO

## IA Agent
### DDPG
The decision making is performed by a (deep) reinforcement learning agent. Considering the continuous nature of the environment and the possibility to train for an undefinedly long time we choose to use a modified version of Deep Deterministic Policy Gradient or DDPG.
DDPG is an model-free, off-policy algorithm that learns a Q-function and a policy in a **continuous** action space. It is inspired by Deep Q Learning, and can be seen as DQN on a continuous acion space.
It employs the use of off-policy data and the Bellman equation to learn the Q function which is in turn used to derive and learn the policy.

The DDPG algorith was originaly described [this paper](https://arxiv.org/pdf/1509.02971.pdf).

#### Main features:
- Stochastic (deep) model estimation allows for continuous (infinite) action spaces.
- Use of a **noise process** (for example the _Ornstein–Uhlenbeck_ process) for action space exploration.
- Use of **experience replay** for a stable learning on previous experiences.
- Actor and critic structure
- Use of target models for both actor and critic networks (weight transfer with Polyak averaging).
- Use of the Bellman equation to describe the optimal q-value function for each pair <state, action>.

The changes made are inspired to the Twin Delayed DDPG or TD3 algorithm:
- **Twin**: the critic learns to approximate two concurrent Q-functions. The Q-value used in the target optimization is the lesser of the two.
- **Delayed**: the critic is updated each step, while the actor is updated at a slower (delayed) rate.
- Uniform noise is introduced to the target action. This is done to prevent overfitting in the policy model.

The TD3 algorith was originaly described [this paper](https://arxiv.org/pdf/1802.09477.pdf).

### Network structure
#### Critic:
![Critic](/img/networks/critic.png)
#### Actor:
![Actor](/img/networks/actor.png)
## Resources
### AI
- RL for track following [article](https://medium.com/@sdeleers/autonomous-car-with-reinforcement-learning-part-2-track-following-4ffbf7aa33d1).
- Keras for TORCS simulation [article](https://yanpanlau.github.io/2016/10/11/Torcs-Keras.html).
- Racing line optimization using MDPs with a simple 2d spatial state space.
  - Optimization of ideal racing line, Werkstuk-Beltman [paper](https://science.vu.nl/en/Images/werkstuk-beltman_tcm296-91313.pdf).
### OpenGL
- OpenGL tutorial [repo](https://github.com/opengl-tutorials/ogl) and [website](http://www.opengl-tutorial.org).
