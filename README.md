# racing_line_RL
Simple racerack environment for Reinforcement Learning tests.

The environment works in two modes:
* manual: The vehicle is driven directly by the user through a controller
* Automatic: The action are choosen by the agent

## Usage
First install the python requirements with
```
pip install -r requirements.txt
```
Then install the 3D visualizer dependencies: openGL and ZeroMQ. You can find cppzmq [here](https://github.com/zeromq/cppzmq).

Run the continuous agent with
```
python test.py
```

Or the manual mode with
```
python test.py manual
```

### Methods
#### **step(action) : tuple[3]**

  Returns the envionment observation given an action. The tuple represents an opservaion: it is made of the state to which we transitioned, the reward coming from the transition and wether the transition leads to a terminal state.

#### **reset() : state**

  Returns initial state of the environment and resets the world parameters.

#### **render() : nil**

  Visualizes the current state of the environment.

## Agent
### DDPG
The decision making is performed by a (deep) reinforcement learning agent. Considering the continuous nature of the environment and the possibility to train for an undefinedly long time we choose to use a modified version of Deep Deterministic Policy Gradient or DDPG.

Base DDPG is an model-free, off-policy algorithm that learns a Q-function and a policy in a **continuous** action space. It is inspired by Deep Q Learning, and can be seen as DQN on a continuous acion space.
It employs the use of off-policy data and the Bellman equation to learn the Q function which is in turn used to derive and learn the policy.

The DDPG algorith was originaly described [this paper](https://arxiv.org/pdf/1509.02971.pdf).

#### Main features of DDPG:
- Stochastic (deep) model estimation allows for continuous (infinite) action spaces.
- Use of a **noise process** (for example the _Ornstein–Uhlenbeck_ process) for action space exploration.
- Use of **experience replay** for a stable learning on previous experiences.
- Actor and critic structure
- Use of target models for both actor and critic networks (weight transfer with Polyak averaging).
- Use of the Bellman equation to describe the optimal q-value function for each pair <state, action>.

The changes made are based on the Twin Delayed DDPG or TD3 algorithm:
- (TODO) **Twin**: the critic learns to approximate two concurrent Q-functions. The Q-value used in the target optimization is the lesser of the two.
- **Delayed**: the critic is updated each step, while the actor is updated at a slower (delayed) rate.
- Uniform noise is introduced to the target action. This is done to prevent overfitting in the policy model.

The TD3 algorith was originaly described [this paper](https://arxiv.org/pdf/1802.09477.pdf).
