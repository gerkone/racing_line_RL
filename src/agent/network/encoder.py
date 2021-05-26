import numpy as np
import tensorflow as tf

from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Dense, Conv2D, Input, Flatten, BatchNormalization, Activation, Multiply
from tensorflow.keras.initializers import RandomUniform
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import MSE

class Encoder(object):
    def __init__(self, stack_depth, img_height, img_width):
        self.stack_depth = stack_depth
        self.img_height = img_height
        self.img_width = img_width

        self.model = self.build_network()
        self.model.summary()

    def build_network(self):
        input_layer = Input(shape = (self.stack_depth, self.img_height, self.img_width, 1))
        conv_1 = Conv2D(4, (3,3), padding ="same", activation = "relu", name="conv_1",
            kernel_initializer="glorot_uniform", bias_initializer="zeros")(input_layer)
        conv_1 = Conv2D(4, (3,3), strides = 2, padding="same", activation="relu",name="conv_1_2",
            kernel_initializer="glorot_uniform", bias_initializer="zeros")(conv_1)

        conv_2 = Conv2D(8, (3,3), padding="same", activation="relu", name="conv_2",
            kernel_initializer="glorot_uniform", bias_initializer="zeros")(conv_1)
        conv_2 = Conv2D(8, (3,3), strides = 2, padding="same", activation="relu", name="conv_2_2",
            kernel_initializer="glorot_uniform", bias_initializer="zeros")(conv_2)

        conv_3 = Conv2D(8, (3,3), padding="same", activation="relu", name="conv_3",
            kernel_initializer="glorot_uniform", bias_initializer="zeros")(conv_2)
        conv_3 = Conv2D(8, (3,3), strides = 2, padding="same", activation="relu", name="conv_3_2",
            kernel_initializer="glorot_uniform", bias_initializer="zeros")(conv_3)

        conv_4 = Conv2D(16, (2,2), padding="same", activation="relu", name="conv_4",
            kernel_initializer="glorot_uniform", bias_initializer="zeros")(conv_3)
        conv_4 = Conv2D(16, (2,2), strides = 2, padding="same", activation="relu", name="conv_4_2",
            kernel_initializer="glorot_uniform", bias_initializer="zeros")(conv_4)

        conv_5 = Conv2D(16, (2,2), padding="same", activation="relu", name="conv_5",
            kernel_initializer="glorot_uniform", bias_initializer="zeros")(conv_4)
        conv_5 = Conv2D(16, (2,2), strides = 2, padding="same", activation="relu", name="conv_5_2",
            kernel_initializer="glorot_uniform", bias_initializer="zeros")(conv_5)

        output_layer = Flatten()(conv_5)

        model = Model(input_layer, output_layer)
        return model
