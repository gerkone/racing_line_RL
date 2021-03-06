import logging
from datetime import datetime

import numpy as np
import tensorflow as tf

from src.agent_vision.utils.replay_buffer import ReplayBuffer
from src.agent_vision.utils.action_noise import OUActionNoise
from src.agent_vision.network.actor import Actor
from src.agent_vision.network.critic import Critic
from src.agent_vision.network.encoder import Encoder

save_dir = "../agent/trained_models"

class Agent(object):
    """
    DDPG agent
    """
    def __init__(self, state_dims, action_dims, action_boundaries, hyperparams):

        # physical_devices = tf.config.list_physical_devices('GPU')
        # tf.config.experimental.set_memory_growth(physical_devices[0], True)

        actor_lr = hyperparams["actor_lr"]
        critic_lr = hyperparams["critic_lr"]
        batch_size = hyperparams["batch_size"]
        gamma = hyperparams["gamma"]
        rand_steps = hyperparams["rand_steps"]
        buf_size = int(hyperparams["buf_size"])
        tau = hyperparams["tau"]
        fcl1_size = hyperparams["fcl1_size"]
        fcl2_size = hyperparams["fcl2_size"]

        img_height = hyperparams["img_height"]
        img_width = hyperparams["img_width"]
        stack_depth = hyperparams["stack_depth"]

        # action size
        self.n_states = state_dims[0]
        # state size
        self.n_actions = action_dims[0]
        self.batch_size = batch_size

        self.img_height = img_height
        self.img_width = img_width
        self.stack_depth = stack_depth

        frame_shape = (self.stack_depth, self.img_height, self.img_width, 1)

        # experience replay buffer
        self._memory = ReplayBuffer(buf_size, input_shape = state_dims, frame_shape = frame_shape, output_shape = action_dims)
        # noise generator
        self._noise = OUActionNoise(mu=np.zeros(action_dims))
        # Bellman discount factor
        self.gamma = gamma
        # environmental action boundaries
        self.lower_bound = action_boundaries[0]
        self.upper_bound = action_boundaries[1]


        # number of episodes for random action exploration
        self.rand_steps = rand_steps - 1

        self.actor_update_delay = hyperparams["actor_update_delay"]

        # turn off most logging
        logging.getLogger("tensorflow").setLevel(logging.FATAL)

        # encoder support
        self.encoder = Encoder(stack_depth = stack_depth, img_height = img_height, img_width = img_width)

        # actor class
        self.actor = Actor(state_dims = state_dims, action_dims = action_dims, lr = actor_lr, batch_size = batch_size,
            tau = tau, upper_bound = self.upper_bound, img_width = img_width, img_height = img_height, stack_depth = stack_depth,
            fcl1_size = fcl1_size, fcl2_size = fcl2_size, save_dir = save_dir, encoder = self.encoder)
        # critic class
        self.critic = Critic(state_dims = state_dims, action_dims = action_dims, lr = critic_lr, batch_size = batch_size, tau = tau,
            img_width= img_width, img_height = img_height, stack_depth = stack_depth, lower_bound = self.lower_bound, upper_bound = self.upper_bound,
            noise_bound = self.upper_bound / 10, fcl1_size = fcl1_size, fcl2_size = fcl2_size, save_dir = save_dir, encoder = self.encoder)


    def save_models(self):
        self.actor.model.save(save_dir + "/actor")
        self.actor.target_model.save(save_dir + "/actor_target")

        self.critic.model.save(save_dir + "/critic")
        self.critic.target_model.save(save_dir + "/critic_target")

    def get_action(self, state, step):
        """
        Return the best action in the passed state, according to the model
        in training. Noise added for exploration
        """
        #take only random actions for the first episode
        if(step > self.rand_steps):
            noise = self._noise()
            frames = np.asarray(state["image"])
            frames = tf.expand_dims(frames, axis = 0)

            state = state.copy()
            state = state["sensors"]
            state = tf.expand_dims(state, axis = 0)
            action = self.actor.model.predict(frames)
            action_p = action + noise
            action_p = action_p[0]
        else:
            #explore the action space quickly
            action_p = np.random.uniform(self.lower_bound, self.upper_bound, self.n_actions)
        #clip the resulting action with the bounds
        action_p = np.clip(action_p, self.lower_bound, self.upper_bound)
        return action_p


    def learn(self, step):
        """
        Fill the buffer up to the batch size, then train both networks with
        experience from the replay buffer.
        """
        if self._memory.isReady(self.batch_size):
            self.train_helper(step)

    """
    Train helper methods
    train_helper
    train_critic
    train_actor
    get_q_targets  Q values to train the critic
    get_gradients  policy gradients to train the actor
    """

    def train_helper(self, step):
        # get experience batch
        states, frames, actions, rewards, terminal, states_n = self._memory.sample(self.batch_size)

        states = tf.convert_to_tensor(states)
        frames = tf.convert_to_tensor(frames)
        actions = tf.convert_to_tensor(actions)
        rewards = tf.convert_to_tensor(rewards)
        rewards = tf.cast(rewards, dtype=tf.float32)
        states_n = tf.convert_to_tensor(states_n)

        # train the critic before the actor
        self.train_critic(states, frames, actions, rewards, terminal, states_n)
        # delayed actor (policy) update
        actor_loss = 0
        if (step + 1) % self.actor_update_delay == 0:
            actor_loss = self.train_actor(states, frames)

        #update the target models
        self.critic.update_target()
        # delayed actor (policy) update
        if (step + 1) % self.actor_update_delay == 0:
            self.actor.update_target()
        return actor_loss

    def train_critic(self, states, frames, actions, rewards, terminal, states_n):
        """
        Use updated Q targets to train the critic network
        """
        # TODO cleaner code, ugly passing of actor target model
        self.critic.train(states, frames, actions, rewards, terminal, states_n, self.actor.target_model, self.gamma)

    def train_actor(self, states, frames):
        """
        Train the actor network with the critic evaluation
        """
        # TODO cleaner code, ugly passing of critic model
        loss = self.actor.train(states, frames, self.critic.model)
        return loss

    def remember(self, state, state_new, action, reward, terminal):
        """
        replay buffer interfate to the outsize
        """
        self._memory.remember(state, state_new, action, reward, terminal)

    def save(self):
        ext = ".h5"
        self.actor.model.save(self.path_actor + ext)
        self.critic.model.save(self.path_critic + ext)
        self.actor.target_model.save(self.path_actor + "_target" + ext)
        self.critic.target_model.save(self.path_critic + "_target" + ext)

    def load(self):
        ext = ".h5"
        self.actor.model.model = tf.keras.models.load_model(self.path_actor + ext)
        self.critic.model.save = tf.keras.models.load_model(self.path_critic + ext)
        self.actor.target_model = tf.keras.models.load_model(self.path_actor + "_target" + ext)
        self.critic.target_model = tf.keras.models.load_model(self.path_critic + "_target" + ext)
