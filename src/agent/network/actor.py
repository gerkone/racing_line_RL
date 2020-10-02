import numpy as np
import math
from keras.initializations import normal, identity
from keras.models import model_from_json, Sequential, Model
from keras.engine.training import collect_trainable_weights
from keras.layers import Dense, Flatten, Input, merge, Lambda
from keras.optimizers import Adam
import tensorflow
import keras.backend as keras_backend

class Actor(object):
    def __init__(self, tensorflow_session, state_size, action_size, lr, batch_size, tau):
        self.session = tensorflow_session
        self.state_size = state_size
        self.action_size = action_size
        self.lr = lr
        self.batch_size = batch_size
        self.tau = tau
        keras_backend.set_session(tensorflow_session)
