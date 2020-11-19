import numpy as np

class ReplayBuffer(object):
    def __init__(self, batch_size, input_shape, output_shape):
        self.batch_size = batch_size
        self.input_shape= input_shape
        self.output_shape = output_shape
        self._buf_ctr = 0

        self.state_buf = np.zeros((self.batch_size, *input_shape))
        self.action_buf = np.zeros((self.batch_size, *output_shape))
        self.reward_buf = np.zeros((self.batch_size, 1))

    def remember(self, state, action, reward):
        i = self._buf_ctr % self.batch_size
        self.state_buf[i] = state
        self.action_buf[i] = action
        self.reward_buf[i] = reward
        self._buf_ctr+=1;

    def sample(self):
        i_max = min(self.batch_size, self._buf_ctr)
        batch = np.random.choice(i_max, self.batch_size)

        states = self.state_buf[batch]
        actions = self.action_buf[batch]
        rewards = self.reward_buf[batch]

        return (states, actions, rewards)

    def isReady(self):
        return(self._buf_ctr > self.batch_size)

    def clear(self):
        self._buf_ctr = 0

        self.state_buf = np.zeros((self.batch_size, *self.input_shape))
        self.action_buf = np.zeros((self.batch_size, *self.output_shape))
        self.reward_buf = np.zeros((self.batch_size, 1))
