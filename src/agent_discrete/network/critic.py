import numpy as np
import keras.backend as K
import tensorflow as tf

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Input, BatchNormalization, Activation, Add, Concatenate
from tensorflow.keras.initializers import RandomUniform
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import MSE

class Critic(object):
    def __init__(self, state_dims, lr,
                fcl1_size, fcl2_size, fcl3_size):
        self.state_dims = state_dims
        # learning rate
        self.lr = lr

        self.fcl1_size = fcl1_size
        self.fcl2_size = fcl2_size
        self.fcl3_size = fcl3_size

        self.model = self.build_network()
        #generate gradient function
        self.optimizer = Adam(self.lr)

    def build_network(self):
        # -- input layer --
        input_layer = Input(shape=(self.state_dims), name = "State_in")
        # -- first fully connected layer --
        fcl1 = Dense(self.fcl1_size, name = "First_FCL")(input_layer)
        fcl1 = Activation("relu", name = "ReLU_1")(fcl1)
        # -- second fully connected layer --
        fcl2 = Dense(self.fcl2_size, name = "Second_FCL")(fcl1)
        fcl2 = Activation("relu", name = "ReLU_2")(fcl2)
        # -- third fully connected layer --
        fcl3 = Dense(self.fcl3_size, name = "Third_FCL")(fcl2)
        fcl3 = Activation("relu", name = "ReLU_3")(fcl3)
        # -- output layer
        output = Dense(1, kernel_regularizer=tf.keras.regularizers.l2(0.01))(fcl3)

        model = Model(input_layer, output)
        return model

    def train(self, states, q_value):
        with tf.GradientTape() as tape:
            q_value = self.model(states, training = True)
            loss = self.compute_loss(q_value, tf.stop_gradient(q_value))
        gradient = tape.gradient(loss, self.model.trainable_variables)
        self.optimizer.apply_gradients(zip(gradient, self.model.trainable_variables))

    def compute_loss(self, predicted_actions, q_value):
        return MSE(predicted_actions, q_value)
