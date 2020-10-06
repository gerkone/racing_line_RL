import numpy as np
import keras.backend as K
import tensorflow as tf

from keras.models import Model
from keras.layers import Dense, Input, BatchNormalization, Activation, Lambda
from keras.initializers import RandomUniform

"""
Actor network:
stochastic funcion approssimator for the deterministic policy map u : S -> A
(with S set of states, A set of actions)
"""
class Actor(object):
    def __init__(self, tensorflow_session, state_dims, action_dims, lr, batch_size, tau, fcl1_size, fcl2_size, upper_bound):
        self.session = tensorflow_session
        self.state_dims = state_dims
        self.action_dims = action_dims
        self.lr = lr
        self.batch_size = batch_size
        self.tau = tau
        self.fcl1_size = fcl1_size
        self.fcl2_size = fcl2_size
        self.upper_bound = upper_bound

        self.model = self.build_network()
        #duplicate model for target
        self.target_model = self.build_network()

        #instantiate optimizer with gradients and weights
        self.optimizer = self._generate_Optimizer()

        # self.session.run(tf.initialize_all_variables())


    def build_network(self):
        """
        Builds the model. Consists of two fully connected layers.
        """
        # input layer
        input_layer = Input(shape = self.state_dims)
        #first fully connected layer
        f1 = 1. / np.sqrt(self.fcl1_size)
        fcl1 = Dense(self.fcl1_size, activation="relu", kernel_initializer = RandomUniform(-f1, f1),
                        bias_initializer = RandomUniform(-f1, f1))(input_layer)
        fcl1 = BatchNormalization()(fcl1)
        #second fully connected layer
        f2 = 1. / np.sqrt(self.fcl1_size)
        fcl2 = Dense(self.fcl2_size, activation="relu", kernel_initializer = RandomUniform(-f2, f2),
                        bias_initializer = RandomUniform(-f2, f2))(fcl1)
        fcl2 = BatchNormalization()(fcl2)
        #output layer
        f3 = 0.003
        output_layer = Dense(*self.action_dims, activation="tanh", kernel_initializer = RandomUniform(-f3, f3),
                        bias_initializer = RandomUniform(-f3, f3))(fcl2)
        #scale the output
        output_layer = Lambda(lambda i : i * self.upper_bound)(output_layer)
        model = Model(input_layer, output_layer)
        return model

    def train(self, states, action_gradients):
        """
        Update the weights with the new gradients
        """
        self.optimizer([states, action_gradients])

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

    def _generate_Optimizer(self):
        #generate gradients
        action_gradients = K.placeholder(shape=(None, *self.action_dims))
        unnormalized_actor_gradients = tf.gradients(self.model.output, self.model.trainable_weights, -action_gradients)
        actor_gradients = zip(unnormalized_actor_gradients, self.model.trainable_weights)
        return K.function(inputs = [self.model.input, action_gradients],
                    outputs=[K.constant(1)], updates = [tf.optimizers.Adam(self.lr).apply_gradients(actor_gradients)])
