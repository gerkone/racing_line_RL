from ddpg import Agent
import gym
from gym import wrappers
import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf

N_EPISODES = 5000

def main():
    #get simulation environment
    env = gym.make("Pendulum-v0")
    state_dims = [len(env.observation_space.low)]
    action_dims = [len(env.action_space.low)]
    #create agent with environment parameters
    agent = Agent(state_dims = state_dims, action_dims = action_dims,
                actor_lr = 1e-3, critic_lr = 1e-3, batch_size = 32, gamma = 0.99,
                buf_size = 10000, tau = 1e-2, fcl1_size = 8, fcl2_size = 8)
    np.random.seed(0)
    scores = []
    #training loop: call remember on predicted states and train the models
    for i in range(N_EPISODES):
        #get initial state
        state = env.reset()
        terminal = False
        score = 0
        #proceed until reaching an exit state
        while not terminal:
            #predict new action
            action = agent.get_action(state)
            #perform the transition according to the predicted action
            state_new, reward, terminal, info = env.step(action)
            #store the transaction in the memory
            agent.remember(state, state_new, action, reward, terminal)
            #adjust the weights according to the new transaction
            agent.learn()
            #iterate to the next state
            state = state_new
            score += reward
            env.render()
        scores.append(score)
        print("Iteration {:d} --> score {:.2f}. Running average {:.2f}".format( i, score, np.mean(scores)))




if __name__ == "__main__":
    #tell tensorflow to train with GPU 0
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    main()
