import numpy as np
import keras.backend as K
import tensorflow as tf

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Input, BatchNormalization, Activation, Concatenate, Flatten
from tensorflow.keras.initializers import RandomUniform
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import MSE

"""
Critic network:
stochastic funcion approssimator for the Q value function C : SxA -> R
(with S set of states, A set of actions)
"""
class Critic(object):
    def __init__(self, state_dims, action_dims, lr, batch_size, tau,
                fcl1_size, fcl2_size, middle_layer1_size, middle_layer2_size):
        self.state_dims = state_dims
        self.action_dims = action_dims
        self.lr = lr
        self.batch_size = batch_size
        self.tau = tau
        self.fcl1_size = fcl1_size
        self.fcl2_size = fcl2_size
        self.middle_layer1_size = middle_layer1_size
        self.middle_layer2_size = middle_layer2_size

        self.model, self.state_input, self.action_input = self.build_network()
        #duplicate model for target
        self.target_model, _, _ = self.build_network()
        self.target_model.set_weights(self.model.get_weights())

        #generate gradient function
        self.optimizer = Adam(self.lr)

    def build_network(self):
        """
        Builds the model (non-sequential, state and action as inputs).
        """
        # -- state input --
        state_input_layer = Input(shape=(self.state_dims))
        state_middle_layer = Dense(self.middle_layer1_size, activation="relu")(state_input_layer)
        state_middle_layer = Dense(self.middle_layer2_size, activation="linear")(state_middle_layer)

        # -- action input --
        action_input_layer = Input(shape=(self.action_dims))
        action_middle_layer = Dense(self.middle_layer2_size, activation="relu")(action_input_layer)

        # Introduce action in the second layer
        state_middle_layer = Flatten()(state_middle_layer)
        concat = Concatenate()([state_middle_layer, action_middle_layer])
        # -- hidden fully connected layers --
        f1 = 1. / np.sqrt(self.fcl1_size)
        fcl1 = Dense(self.fcl1_size, kernel_initializer = RandomUniform(-f1, f1),
                    bias_initializer = RandomUniform(-f1, f1))(concat)
        fcl1 = BatchNormalization()(fcl1)
        #activation applied after batchnorm
        fcl1 = Activation("relu")(fcl1)
        f2 = 1. / np.sqrt(self.fcl1_size)
        fcl2 = Dense(self.fcl2_size, kernel_initializer = RandomUniform(-f2, f2),
                    bias_initializer = RandomUniform(-f2, f2))(fcl1)
        fcl2 = BatchNormalization()(fcl2)
        #activation applied after batchnorm
        fcl2 = Activation("linear")(fcl2)
        # Outputs single value for give state-action
        output = Dense(1)(fcl2)

        model = Model([state_input_layer, action_input_layer], output)
        model.summary()
        return model, state_input_layer, action_input_layer

    @tf.function
    def train(self, states, actions, rewards, states_n, actor_target, gamma):
        """
        Update the weights with the Q targets
        """
        with tf.GradientTape() as tape:
            target_actions = actor_target(states_n, training=True)
            q_n = self.target_model([states_n, target_actions], training=True)
            q_target = rewards + gamma * q_n
            q_value = self.model([states, actions], training=True)
            loss = MSE(q_target, q_value)

        gradient = tape.gradient(loss, self.model.trainable_variables)
        self.optimizer.apply_gradients(zip(gradient, self.model.trainable_variables))

    def update_target(self):
        """
        Update the target weights using tau as speed. The tracking function is
        defined as:
        target = tau * weights + (1 - tau) * target
        """
        i = 0
        weights = []
        targets = self.target_model.get_weights()
        for weight in self.model.get_weights():
            weights.append(weight * self.tau + targets[i] * (1 - self.tau))
            i+=1
        #update the target values
        self.target_model.set_weights(weights)
