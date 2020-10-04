from keras.layers import Dense, Input, add, BatchNormalization
from keras import Model
from keras.optimizers import Adam
from keras.losses import mean_squared_error as mse
from tensorflow.python.keras import backend as keras_backend
from keras.initializers import RandomUniform
import tensorflow.compat.v1 as tf
import numpy as np


"""
Critic network:
stochastic funcion approssimator for the Q value function C : SxA -> R
(with S set of states, A set of actions)
"""
class Critic(object):
    def __init__(self, tensorflow_session, state_dims, action_dims, lr, batch_size, tau, fcl1_size, fcl2_size):
        self.session = tensorflow_session
        self.state_dims = state_dims
        self.action_dims = action_dims
        self.lr = lr
        self.batch_size = batch_size
        self.tau = tau
        self.fcl1_size = fcl1_size
        self.fcl2_size = fcl2_size

        tf.disable_v2_behavior()

        keras_backend.set_session(tensorflow_session)

        self.q_target = tf.placeholder(tf.float32, shape=[None,1], name='targets')

        self.model, self.state_input, self.action_input, self.loss = self.build_network()
        #duplicate model for target
        self.target_model, _, _, _ = self.build_network()

        #generate gradients
        self.action_gradients = tf.gradients(self.model.output, self.action_input)

        self.optimizer = tf.train.AdamOptimizer(self.lr).minimize(self.loss)

        self.session.run(tf.initialize_all_variables())

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
        merged = add([hidden, fc_layer_action])

        #output layer, single real number as output (q)
        output_layer = Dense(1, activation="linear")(merged)
        #realize the C(s,a) = q function
        model = Model([state_input_layer, action_input_layer], output_layer)

        loss = mse(self.q_target, output_layer)
        return model, state_input_layer, action_input_layer, loss

    @tf.function
    def optimize(self):
        self.optimizer()

    def train(self, states, actions, q_target):
        """
        Update the weights with the Q targets
        """
        # self.state_input = states,
        # self.action_input = actions,
        # self.q_target = q_target
        self.session.run(self.optimizer, feed_dict={
            self.state_input: states,
            self.action_input: actions,
            self.q_target: q_target
        })

    def update_target(self):
        """
        Update the target weights using tau as speed. The tracking function is
        defined as:
        target = tau * weights + (1 - tau) * target
        """
        weights = self.model.get_weights()
        targets = self.target_model.get_weights()
        targets = [self.tau * weight + (1 - self.tau) * target for weight,target in zip(weights, targets)]
        #update the target values
        self.target_model.set_weights(targets)

    def get_gradients(self, states, actions):
        """
        Return the model action gradients
        """
        return self.session.run(self.action_gradients, feed_dict={
            self.state_inputs: states,
            self.action_input: actions
        })
