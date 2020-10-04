import numpy as np
import math
from keras.models import model_from_json, Sequential, Model
from keras.layers import Dense, Input, BatchNormalization, Activation
from keras.initializers import RandomUniform
from keras.optimizers import Adam
import tensorflow.compat.v1 as tf
from tensorflow.python.keras import backend as keras_backend

"""
Actor network:
stochastic funcion approssimator for the deterministic policy map u : S -> A
(with S set of states, A set of actions)
"""
class Actor(object):
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

        self.model, self.model_weights, self.model_input = self.build_network()
        #duplicate model for target
        self.target_model, _, _ = self.build_network()

        #generate gradients
        self.action_gradients = tf.compat.v1.placeholder(tf.float32, [None, *self.action_dims])
        self.unnormalized_gradients = tf.gradients(self.model.output, self.model_weights, -self.action_gradients)
        #normalize gradients by batch size
        self.actor_gradients = list(map(lambda x: tf.div(x, self.batch_size),self.unnormalized_gradients))
        #instantiate optimizer with gradients and weights
        self.optimizer = tf.train.AdamOptimizer(self.lr).apply_gradients(zip(self.actor_gradients, self.model_weights))

        self.session.run(tf.initialize_all_variables())


    def build_network(self):
        """
        Builds the model. Consists of two fully connected layers.
        """
        model = Sequential()
        #input layer
        input_layer = Input(shape = self.state_dims)
        model.add(input_layer)

        f1 = 1. / np.sqrt(self.fcl1_size)
        #first fully connected layer
        model.add(Dense(self.fcl1_size, kernel_initializer = RandomUniform(-f1, f1),
                    bias_initializer = RandomUniform(-f1, f1)))
        model.add(BatchNormalization())
        model.add(Activation("relu"))

        f2 = 1. / np.sqrt(self.fcl2_size)
        #second fully connected layer
        model.add(Dense(self.fcl2_size, kernel_initializer = RandomUniform(-f2, f2),
                    bias_initializer = RandomUniform(-f2, f2)))
        model.add(BatchNormalization())
        model.add(Activation("relu"))

        #output layer
        model.add(Dense(*self.action_dims))
        model.add(Activation("sigmoid"))

        return model, model.trainable_weights, input_layer

    def train(self, states, action_gradients):
        """
        Update the weights with the new gradients
        """
        self.session.run(self.optimizer, feed_dict={
        self.model_input: states,
        self.action_gradients: action_gradients
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
