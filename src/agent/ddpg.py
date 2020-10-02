import numpy as np
import tensorflow as tf

from utils.replay_buffer import ReplayBuffer
from utils.action_noise import OUActionNoise
from network.actor import Actor
from network.critic import Critic

"""

"""
class DDPG(object):
    def __init__(self, state_size, action_size, actor_lr = 1e-5,
                critic_lr = 1e-3, batch_size = 64, gamma = 0.99,
                buf_size = 1e4, tau = 1e-3):

        self.batch_size = batch_size
        self.memory = ReplayBuffer(buf_size, [state_size], action_size)
        self.gamma = gamma

        #generate tensorflow session
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        session = tf.Session(config=config)

        self.actor = Actor(tensorflow_session = session, state_size = state_size,
                            action_size = action_size, lr = actor_lr,
                            batch_size = batch_size, tau = tau)
        self.critic = Critic(tensorflow_session = session, state_size = state_size,
                            action_size = action_size, lr = critic_lr,
                            batch_size = batch_size, tau = tau)

    def get_action(self, state):
        """
        Return the best action in the passed state,
        according to the model in training
        """
        return self.actor.model.predict(state)

    def train(self):
        """
        Wait to fill the buffer up to the batch size, then train the
        network from the replay buffer.
        """
        if self.memory.isReady(self.batch_size):
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
        states, actions, rewards, terminal, states_n = self.memory.sample()
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
        self.critic.train(states, gradients)

    def get_q_targets(self, states_n, terminal, rewards):
        """
        Calculate the Q target values with the Bellman equation:
        Q = r + gamma * q_n
        with r current reward, gamma discount factor and q_n future q values.
        """
        actions_n = self.actor.model.predict(states_n)
        q_values_n = self.critic.target_model.predict(states_n, actions_n)
        q_targets = []

        for (reward, q_value_n, this_done) in zip(rewards, q_values_n, terminal):
            q_target = reward
            if(!this_done):
                q_target += self.gamma * q_value_n
            q_targets.append(q_target)

        return q_target

    def get_action_gradients(self, states):
        """
        Calculate the predicted deterministic policy gradients.
        """
        actions = self.actor.model.predict(states)
        self.critic.get_gradients(states, actions)
