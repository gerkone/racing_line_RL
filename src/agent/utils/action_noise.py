import numpy as np

"""
Python implementation of Ornstein-Uhlenbeck process for random noise generation
"""
class OUActionNoise(object):
    def __init__(self, mu, sigma = 0.15, theta = 0.2, dt = 1e-2, x0 = None):
        self.theta = theta
        self.mu = mu
        self.sigma = sigma
        self.dt = dt
        self.x0 = x0
        self.reset()

    def reset(self):
        if self.x0 is None:
            self.x_p = np.zeros_like(self.mu)
        else:
            self.x_p = self.x0

    def __call__(self):
        x = self.x_p + self.theta * (self.mu - self.x_p) * self.dt + self.sigma * np.sqrt(self.dt) * np.random.normal(size=self.mu.shape)
        self.x_p = x
        return x
