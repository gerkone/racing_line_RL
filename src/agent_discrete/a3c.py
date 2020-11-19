from agent_discrete.network.actor import Actor
from agent_discrete.network.critic import Critic
from agent_discrete.worker import WorkerAgent
from simulation.environment import TrackEnvironment

from multiprocessing import cpu_count
import gym

class Agent(object):
    def __init__(self, trackpath, actor_lr = 1e-6, critic_lr = 4*1e-6, gamma = 0.99,
            beta = 0.03, batch_size = 5, fcl1_size = 128, fcl2_size = 64, fcl3_size = 32):

        env = TrackEnvironment(trackpath, render = False, width = 1.5, discrete = True)
        self.trackpath = trackpath

        self.state_dims = [env.n_states]
        self.action_dims = [env.n_actions]

        self.actor_lr = actor_lr
        self.critic_lr = critic_lr
        self.gamma = gamma
        self.entropy_beta = beta

        self.batch_size = batch_size

        self.fcl1_size = fcl1_size
        self.fcl2_size = fcl2_size
        self.fcl3_size = fcl3_size

        self.global_actor = Actor(self.state_dims, self.action_dims,
                                self.actor_lr, self.entropy_beta, self.fcl1_size, self.fcl2_size)
        self.global_critic = Critic(self.state_dims, self.critic_lr,
                                self.fcl1_size, self.fcl2_size, self.fcl3_size)

        self.num_workers = cpu_count()

    def train(self, max_episodes = 1000, render = True):
        workers = []

        for i in range(self.num_workers - 1):
            # new env each worker, NO RENDERING
            env = TrackEnvironment(self.trackpath, render = False, width = 1.5, discrete = True)
            #env = gym.make("CartPole-v1")
            workers.append(WorkerAgent(env, self.state_dims, self.action_dims, render = False,
                    actor_lr = self.actor_lr, critic_lr = self.critic_lr, entropy_beta = self.entropy_beta,
                    fcl1_size = self.fcl1_size,fcl2_size = self.fcl2_size, fcl3_size =  self.fcl3_size,
                    global_actor = self.global_actor, global_critic = self.global_critic,
                    episodes = max_episodes, batch_size = self.batch_size, gamma = self.gamma))

        # leave rendering for one worker, test purpose
        env = TrackEnvironment(self.trackpath, render = render, width = 1.5, discrete = True)
        # env = gym.make("CartPole-v1")
        workers.append(WorkerAgent(env, self.state_dims, self.action_dims, render = render,
                actor_lr = self.actor_lr, critic_lr = self.critic_lr, entropy_beta = self.entropy_beta,
                fcl1_size = self.fcl1_size,fcl2_size = self.fcl2_size, fcl3_size =  self.fcl3_size,
                global_actor = self.global_actor, global_critic = self.global_critic,
                episodes = max_episodes, batch_size = self.batch_size, gamma = self.gamma))

        for worker in workers:
            worker.start()

        for worker in workers:
            worker.join()

        self.global_actor.model.save("../trained_models/actor1.h5")
        self.global_critic.model.save("../trained_models/critic1.h5")
