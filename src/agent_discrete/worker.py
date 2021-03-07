import numpy as np

from threading import Thread, Lock

from src.agent_discrete.network.actor import Actor
from src.agent_discrete.network.critic import Critic
from src.agent_discrete.utils.buffer import ReplayBuffer

CUR_EPISODE = 0
RUNNING_AVG = 0
REWARDS = np.ones(50)

class WorkerAgent(Thread):
    def __init__(self, env, state_dims, action_dims, actor_lr, critic_lr,
                    entropy_beta, global_actor, global_critic, fcl1_size = 32,
                    fcl2_size = 32, fcl3_size = 16, episodes = 10000,
                    batch_size = 16, gamma = 0.99,render = True):
        Thread.__init__(self)
        self.lock = Lock()

        # training environment
        self.env = env
        self.render = render

        self.gamma = gamma

        self.state_dims = state_dims
        self.action_dims = action_dims

        self.episodes = episodes
        self.batch_size = batch_size

        # global networks
        self.global_actor = global_actor
        self.global_critic = global_critic

        #worker internal networks
        self.actor = Actor(self.state_dims, self.action_dims,
                            actor_lr, entropy_beta, fcl1_size, fcl2_size)
        self.critic = Critic(self.state_dims, critic_lr,
                            fcl1_size, fcl2_size, fcl3_size)

        # clone global networks
        self.actor.model.set_weights(self.global_actor.model.get_weights())
        self.critic.model.set_weights(self.global_critic.model.get_weights())

        self.buffer = ReplayBuffer(batch_size, state_dims, action_dims)


    def get_td_target(self, rewards, n_value, done):
        td_target = np.zeros_like(rewards)
        cumulative = 0
        if not done:
            cumulative = n_value
        for k in reversed(range(0, len(rewards))):
            cumulative = self.gamma * cumulative + rewards[k]
            td_target[k] = cumulative
        return td_target


    def advatnage(self, td_targets, values):
        return td_targets - values

    def running_mean(x, N):
        sum = numpy.cumsum(numpy.insert(x, 0, 0))
        return (sum[N:] - sum[:-N]) / float(N)

    def train(self):
        global CUR_EPISODE
        global RUNNING_AVG
        global REWARDS

        while self.episodes >= CUR_EPISODE:
            episode_reward, done = 0, False

            state = self.env.reset()

            while not done:
                probs = self.actor.model.predict(np.reshape(state, [1, *self.state_dims]))
                # get action according to prediction
                action = np.random.choice(*self.action_dims, p = probs[0])

                next_state, reward, done = self.env.step(action)

                state = np.reshape(state, [1, *self.state_dims])
                action = np.reshape(action, [1, 1])
                next_state = np.reshape(next_state, [1, *self.state_dims])
                reward = np.reshape(reward, [1, 1])

                self.buffer.remember(state, action, reward)

                if self.buffer.isReady() or done:
                    states, actions, rewards = self.buffer.sample()

                    n_value = self.critic.model.predict(next_state)
                    td_target = self.get_td_target(rewards, n_value, done)
                    advantages = td_target - self.critic.model.predict(states)
                    with self.lock:
                        # lock global networks for changes
                        self.global_actor.train(states, actions, advantages)
                        self.global_critic.train(states, td_target)

                        self.actor.model.set_weights(self.global_actor.model.get_weights())
                        self.critic.model.set_weights(self.global_critic.model.get_weights())

                    self.buffer.clear()
                episode_reward += reward[0][0]
                state = next_state[0]
                if(self.render):
                    self.env.render()

            CUR_EPISODE += 1
            REWARDS[CUR_EPISODE % len(REWARDS)] = episode_reward
            RUNNING_AVG = sum(REWARDS) / min(CUR_EPISODE, len(REWARDS))
            print('EP{} EpisodeReward={:.2f} AVG={:.2f}'.format(CUR_EPISODE, episode_reward, RUNNING_AVG))

    def run(self):
        self.train()
