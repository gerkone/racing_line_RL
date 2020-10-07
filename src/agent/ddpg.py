import numpy as np
import tensorflow.compat.v1 as tf

from utils.replay_buffer import ReplayBuffer
from utils.action_noise import OUActionNoise
from network.actor import Actor
from network.critic import Critic

"""

"""
class Agent(object):
    def __init__(self, state_dims, action_dims, action_boundaries,
                actor_lr = 1e-5, critic_lr = 1e-3, batch_size = 64, gamma = 0.99,
                buf_size = 10000, tau = 1e-3, fcl1_size = 300, fcl2_size = 400):
        tf.disable_v2_behavior()
        self.n_actions = action_dims[0]
        self.n_states = state_dims[0]
        self.batch_size = batch_size
        self._memory = ReplayBuffer(buf_size, state_dims, action_dims)
        self._noise = OUActionNoise(mu=np.zeros(action_dims))
        self.gamma = gamma
        self.lower_bound = action_boundaries[0]
        self.upper_bound = action_boundaries[1]

        #generate tensorflow session
        session = tf.Session()

        self.actor = Actor(state_dims = state_dims, action_dims = action_dims,
                            lr = actor_lr, batch_size = batch_size, tau = tau,
                            upper_bound = self.upper_bound,
                            fcl1_size = fcl1_size, fcl2_size = fcl2_size)
        self.critic = Critic(state_dims = state_dims, action_dims = action_dims,
                            lr = critic_lr, batch_size = batch_size, tau = tau,
                            fcl1_size = fcl1_size, fcl2_size = fcl2_size,
                            middle_layer1_size = 16, middle_layer2_size = 32)

    def get_action(self, state):
        """
        Return the best action in the passed state, according to the model
        in training. Noise added for exploration
        """
        noise = self._noise()
        state = state.reshape(self.n_states, 1).T
        action = self.actor.model.predict(state)[0]
        action_p = action + noise
        #clip the resulting action with the bounds
        action_p = np.clip(action_p, self.lower_bound, self.upper_bound)
        return action_p

    def learn(self):
        """
        Fill the buffer up to the batch size, then train both networks with
        experience from the replay buffer.
        """
        if self._memory.isReady(self.batch_size):
            self.train_helper()

    """
    Train helper methods
    train_helper
    train_critic
    train_actor
    get_q_targets  Q values to train the critic
    get_gradients  policy gradients to train the actor
    """

    def train_helper(self):
        states, actions, rewards, terminal, states_n = self._memory.sample(self.batch_size)
        self.train_critic(states, actions, rewards, terminal, states_n)
        self.train_actor(states)
        #update the target models
        self.critic.update_target()
        self.actor.update_target()

    def train_critic(self, states, actions, rewards, terminal, states_n):
        """
        Use updated Q targets to train the critic network
        """
        q_targets = self.get_q_targets(states_n, terminal, rewards)
        self.critic.train(states, actions, q_targets)

    def train_actor(self, states):
        """
        Use calculated policy gradients to train the actor network
        """
        gradients = self.get_action_gradients(states)
        self.actor.train(states, gradients)

    def get_q_targets(self, states_n, terminal, rewards):
        """
        Calculate the Q target values with the Bellman equation:
        Q = r + gamma * q_n
        with r current reward, gamma discount factor and q_n future q values.
        """
        actions_n = self.actor.model.predict(states_n)
        q_values_n = self.critic.target_model.predict([states_n, actions_n])
        q_targets = []

        for (reward, q_value_n, this_done) in zip(rewards, q_values_n, terminal):
            if(this_done):
                q_target = reward
            else:
                q_target = reward + self.gamma * q_value_n
            q_targets.append(q_target.item())
        return np.array(q_targets)

    def get_action_gradients(self, states):
        """
        Calculate the predicted deterministic policy gradients.
        """
        actions = self.actor.model.predict(states)
        return self.critic.get_gradients(states, actions).reshape(self.batch_size, self.n_actions)

    def remember(self, state, state_new, action, reward, terminal):
        """
        replay buffer interfate to the outsize
        """
        self._memory.remember(state, state_new, action, reward, terminal)
