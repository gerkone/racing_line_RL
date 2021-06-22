import numpy as np
import keras.backend as K
import tensorflow as tf

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Input, BatchNormalization, Activation, Add, Concatenate
from tensorflow.keras.initializers import RandomUniform
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import MSE

class Critic(object):
    """
    Critic network:
    stochastic funcion approximator for the Q value function C : SxA -> R
    (with S set of states, A set of actions)
    """
    def __init__(self, state_dims, action_dims, lr, batch_size, tau,
                fcl1_size, fcl2_size, noise_bound, lower_bound, upper_bound,
                stack_depth, img_height, img_width, encoder, save_dir):
        self.state_dims = state_dims
        self.action_dims = action_dims
        # learning rate
        self.lr = lr
        self.batch_size = batch_size
        # polyak averaging speed
        self.tau = tau
        self.fcl1_size = fcl1_size
        self.fcl2_size = fcl2_size

        self.stack_depth = stack_depth
        self.img_height = img_height
        self.img_width = img_width

        try:
            # load model if present
            self.model = tf.keras.models.load_model(save_dir + "/critic")
            self.target_model = tf.keras.models.load_model(save_dir +"/critic_target")
            print("Loaded saved critic models")
        except:
            self.model = self.build_network(encoder.model)
            #duplicate model for target
            self.target_model = self.build_network(encoder.model)
            self.target_model.set_weights(self.model.get_weights())
            self.model.summary()

        self.optimizer = Adam(self.lr)

        self.noise_bound = noise_bound
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def build_network(self, encoder_model):
        """
        Builds the model,
        non-sequential, state and action as inputs:
        two state fully connected layers and one action fully connected layer.
        Action introduced after the second state layer, as specified in the paper.
        Twin network to approximate two concurring approximators
        """
        # -- embedded encoder as submodel --
        encoder_input_layer = Input(shape = (self.stack_depth, self.img_height, self.img_width, 1), name = "Frame_in")
        encoder = encoder_model(encoder_input_layer)

        fcl1 = Dense(self.fcl1_size, name = "First_FCL")(encoder)
        fcl1 = Activation("relu", name = "ReLU_1")(fcl1)
        fcl2 = Dense(self.fcl2_size, name = "Second_FCL")(fcl1)
        fcl2 = Activation("relu", name = "ReLU_2")(fcl2)
        # -- action input --
        action_input_layer = Input(shape=(self.action_dims), name = "Action_in")

        #activation applied after batchnorm
        # fcl2 = Activation("linear")(fcl2)
        # Introduce action after the second layer
        action_layer =  Dense(self.fcl2_size, name = "Action_FCL")(action_input_layer)
        action_layer = Activation("relu")(action_layer)

        concat = Add(name = "Action_concat")([fcl2, action_layer])
        concat = Activation("relu")(concat)
        # Outputs single value for give state-action
        f3 = 0.003
        output = Dense(1, kernel_initializer=RandomUniform(-f3, f3), bias_initializer=RandomUniform(-f3, f3),
                kernel_regularizer=tf.keras.regularizers.l2(0.01))(concat)

        model = Model([encoder_input_layer, action_input_layer], output, name = "Critic")
        return model

    @tf.function
    def train(self, states, frames, actions, rewards, terminals, states_n, actor_target, gamma):
        """
        Update the weights with the Q targets. Graphed function for more
        efficient Tensor operations
        """
        with tf.GradientTape() as tape:
            # clipped noise for smooth policy update
            smoothing_noise = tf.random.uniform(actions.shape, -self.noise_bound, self.noise_bound)
            target_actions = tf.clip_by_value(actor_target(frames, training=True), self.lower_bound, self.upper_bound)
            q_n = self.target_model([frames, target_actions], training=True)

            q_target = rewards + gamma * q_n * (1 - terminals)
            q_value = self.model([frames, actions], training=True)

            # critic loss as sum of losses from both the q function estimators
            loss = MSE(q_target, q_value)

        gradient = tape.gradient(loss, self.model.trainable_variables)
        self.optimizer.apply_gradients(zip(gradient, self.model.trainable_variables))

    def update_target(self):
        """
        Update the target weights using tau as speed. The tracking function is
        defined as:
        target = tau * weights + (1 - tau) * target
        """
        # faster updates with graph mode
        self._transfer(self.model.variables, self.target_model.variables)

    @tf.function
    def _transfer(self, model_weights, target_weights):
        """
        Target update helper. Applies Polyak averaging on the target weights.
        """
        for (weight, target) in zip(model_weights, target_weights):
            #update the target values
            target.assign(weight * self.tau + target * (1 - self.tau))
