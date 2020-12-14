import numpy as np
import tensorflow as tf

from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Dense, Input, BatchNormalization, Activation, Multiply
from tensorflow.keras.initializers import RandomUniform
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import CategoricalCrossentropy, SparseCategoricalCrossentropy

class Actor(object):
    def __init__(self, state_dims, action_dims, lr,
                    entropy_beta, fcl1_size, fcl2_size):

        self.state_dims = state_dims
        self.action_dims = action_dims
        # learning rate
        self.lr = lr
        # entropy coeff
        self.entropy_beta = entropy_beta

        self.fcl1_size = fcl1_size
        self.fcl2_size = fcl2_size

        self.model = self.build_network()

        self.optimizer = Adam(self.lr)

    def build_network(self):
        # -- input layer --
        input_layer = Input(shape = self.state_dims, name = "State_in")
        # -- first fully connected layer --
        fcl1 = Dense(self.fcl1_size, name = "First_FCL")(input_layer)
        fcl1 = Activation("relu", name = "ReLU_1")(fcl1)
        # -- second fully connected layer --
        fcl2 = Dense(self.fcl2_size, name = "Second_FCL")(fcl1)
        fcl2 = Activation("relu", name = "ReLU_2")(fcl2)
        # -- output layer, softmax activation --
        # output_layer = Dense(*self.action_dims, kernel_regularizer=tf.keras.regularizers.l2(0.01), name = "Action_out")(fcl2)
        output_layer = Dense(*self.action_dims, name = "Action_out")(fcl2)
        output_layer = Activation("softmax", name = "softmax_out")(output_layer)
        model = Model(input_layer, output_layer)
        return model

    def train(self, states, actions, advantages):
        """
        Update the weights with the new critic advantage
        """
        with tf.GradientTape() as tape:
            prediction = self.model(states, training=True)
            loss = self.compute_loss(actions, prediction, advantages)
        gradient = tape.gradient(loss, self.model.trainable_variables)
        self.optimizer.apply_gradients(zip(gradient, self.model.trainable_variables))

    def compute_loss(self, actions, prediction, advantages):
        """
        Get cumulate policy loss
        loss = -log(pi(s)) * A(s) - beta*entropy
        """
        # scce = SparseCategoricalCrossentropy(from_logits=True)
        cce = CategoricalCrossentropy(from_logits=True)
        # discrete actions
        actions = tf.cast(actions, tf.int32)
        policy_loss = cce(actions, prediction, sample_weight=tf.stop_gradient(advantages))
        entropy = cce(prediction, prediction)
        loss = policy_loss - self.entropy_beta * entropy
        return loss
