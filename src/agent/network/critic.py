import numpy as np
import keras.backend as K
import tensorflow as tf

from keras.models import Model
from keras.layers import Dense, Input, BatchNormalization, Activation, multiply, concatenate, Flatten
from keras.initializers import RandomUniform
from keras.optimizers import Adam

"""
Critic network:
stochastic funcion approssimator for the Q value function C : SxA -> R
(with S set of states, A set of actions)
"""
class Critic(object):
    def __init__(self, tensorflow_session, state_dims, action_dims, lr, batch_size, tau,
                fcl1_size, fcl2_size, middle_layer1_size, middle_layer2_size):
        self.session = tensorflow_session
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

        #generate gradient function
        self.action_gradients = self._generate_gradients()

    def build_network(self):
        """
        Builds the model (non-sequential, state and action as inputs).
        """
        #input layers
        state_input_layer = Input(shape = self.state_dims)
        action_input_layer = Input(shape = self.action_dims)
        #hidden fully connected layers
        f1 = 1. / np.sqrt(self.fcl1_size)
        fc_layer_state = Dense(self.fcl1_size, activation="relu",
                    kernel_initializer = RandomUniform(-f1, f1),
                    bias_initializer = RandomUniform(-f1, f1))(state_input_layer)
        fc_layer_action = Dense(self.fcl2_size, activation="linear")(action_input_layer)

        f2 = 1. / np.sqrt(self.fcl2_size)
        hidden = Dense(self.fcl2_size, activation="linear",
                    kernel_initializer = RandomUniform(-f2, f2),
                    bias_initializer = RandomUniform(-f2, f2))(fc_layer_state)
        #merge the action hidden layer with the first layer
        hidden = Flatten()(hidden)
        merged = concatenate([hidden, fc_layer_action])

        #output layer, single real number as output (q)
        output_layer = Dense(1, activation="linear")(merged)
        #realize the C(s,a) = q function
        model = Model([state_input_layer, action_input_layer], output_layer)
        #config optimizer and loss
        model.compile(Adam(self.lr), "mse")

        return model, state_input_layer, action_input_layer

    def train(self, states, actions, q_target):
        """
        Update the weights with the Q targets
        """
        #use the compiled model training to fit the weights
        return self.model.train_on_batch([states, actions], q_target)

    def update_target(self):
        """
        Update the target weights using tau as speed. The tracking function is
        defined as:
        target = tau * weights + (1 - tau) * target
        """
        weights = self.model.get_weights()
        targets = self.target_model.get_weights()
        targets = [self.tau * weight + (1 - self.tau) * target for weight, target in zip(weights, targets)]
        #update the target values
        self.target_model.set_weights(targets)

    def _generate_gradients(self):
        action_gradients = K.gradients(self.model.output, [self.action_input])
        return K.function([self.state_input, self.action_input], action_gradients)

    def get_gradients(self, states, actions):
        """
        Return the model action gradients
        """
        return np.array(self.action_gradients([states, actions]))
