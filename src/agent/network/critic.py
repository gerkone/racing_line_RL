from keras.layers import Dense, Input, merge
from keras.models import Model
from keras.optimizers import Adam
import keras.backend as keras_backend
import tensorflow

class Critic(object):
    def __init__(self, tensorflow_session, state_size, action_size, lr, batch_size, tau):
        self.session = tensorflow_session
        self.state_size = state_size
        self.action_size = action_size
        self.lr = lr
        self.batch_size = batch_size
        self.tau = tau
        keras_backend.set_session(tensorflow_session)
