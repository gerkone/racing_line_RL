import logging

import numpy as np
import tensorflow as tf

from utils.replay_buffer import ReplayBuffer
from utils.action_noise import OUActionNoise
from network.actor import Actor
from network.critic import Critic

"""

"""
class Agent(object):
    def __init__(self, state_dims, action_dims, action_boundaries,
                actor_lr = 1e-5, critic_lr = 1e-3, batch_size = 64, gamma = 0.99,
                buf_size = 10000, tau = 1e-3, fcl1_size = 256, fcl2_size = 256):
        self.n_actions = action_dims[0]
        self.n_states = state_dims[0]
        self.batch_size = batch_size
        self._memory = ReplayBuffer(buf_size, state_dims, action_dims)
        self._noise = OUActionNoise(mu=np.zeros(action_dims))
        self.gamma = gamma
        self.lower_bound = action_boundaries[0]
        self.upper_bound = action_boundaries[1]

        logging.getLogger("tensorflow").setLevel(logging.FATAL)

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
        states = tf.convert_to_tensor(states)
        actions = tf.convert_to_tensor(actions)
        rewards = tf.convert_to_tensor(rewards)
        rewards = tf.cast(rewards, dtype=tf.float32)
        states_n = tf.convert_to_tensor(states_n)
        self.train_critic(states, actions, rewards, terminal, states_n)
        self.train_actor(states)
        #update the target models
        self.critic.update_target()
        self.actor.update_target()

    def train_critic(self, states, actions, rewards, terminal, states_n):
        """
        Use updated Q targets to train the critic network
        """
        self.critic.train(states, actions, rewards, terminal, states_n, self.actor.target_model, self.gamma)

    def train_actor(self, states):
        """
        Use calculated policy gradients to train the actor network
        """
        self.actor.train(states, self.critic.model)

    def remember(self, state, state_new, action, reward, terminal):
        """
        replay buffer interfate to the outsize
        """
        self._memory.remember(state, state_new, action, reward, terminal)
