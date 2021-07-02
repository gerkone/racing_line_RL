import os, sys
import numpy as np
import cv2
import yaml
import collections
import matplotlib.pyplot as plt
import argparse

from src.simulation.environment import TrackEnvironment, manual
from src.agent.ddpg import Agent

N_EPISODES = 1000000
CHECKPOINT = 100


def main(headless, trackpath = "./tracks/track_4387235659010134370_ver1.npy"):
    hyperparams = {}
    vision = False
    render = not headless or vision
    with open("src/agent/hyperparams.yaml", 'r') as stream:
        try:
            hyperparams = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
        #get simulation environment
    #track_4387235659010134370_ver1
    env = TrackEnvironment(trackpath, render = render, vision = vision, width = 1.0)
    if render:
        visualizer_pid = env.setup_comms()
    state_dims = [env.n_states]
    action_dims = [env.n_actions]
    action_boundaries = [-1,1]
    #create agent with environment parameters
    agent = Agent(state_dims = state_dims, action_dims = action_dims,
            action_boundaries = action_boundaries, hyperparams = hyperparams)
    np.random.seed(0)

    scores = []
    #training loop: call remember on predicted states and train the models
    try:
        for i in range(N_EPISODES):
            #get initial state
            state = env.reset()
            terminal = False
            score = 0
            avg_loss = 0
            #proceed until reaching an exit state
            while not terminal:
                #predict new action
                action = agent.get_action(state, i)
                #perform the transition according to the predicted action
                state_new, reward, terminal = env.step(action)

                agent.remember(state, state_new, action, reward, terminal)
                #adjust the weights according to the new transaction
                avg_loss += agent.learn(i)
                #iterate to the next state
                state = state_new
                score += reward
            scores.append(score)
            print("Iteration {:d} --> Score {:.2f}. Running average {:.2f}. Avg actor loss {:.2f}".format( i, score, np.mean(scores), avg_loss))
            if i > 0 and i % 20 == 0:
                agent.save_models()
                print("Models saved")
        plt.plot(scores)
        plt.xlabel("Episode")
        plt.ylabel("Cumulate reward")
        plt.show()
    except Exception as e:
        import traceback
        traceback.print_exc()
        if render:
            from subprocess import Popen
            Popen(["kill", "-9", str(visualizer_pid)])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="racing line RL.")
    parser.add_argument("--trackpath", help="Path to the track file.", default="./tracks/track_4387235659010134370_ver1.npy", type=str)
    parser.add_argument("--manual", help="Set manual mode.", default = False, action="store_true")
    parser.add_argument("--headless", help="Run without rendering.", default=False, action="store_true")
    args = parser.parse_args()
    if(args.manual == True):
        while True:
            print("Starting in manual mode...\n\n")
            manual("../tracks/track_4387235659010134370.npy")
    else:
        #tell tensorflow to train with GPU 0
        os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        print("Starting in autonomous mode...\n\n")
        main(args.headless, args.trackpath)
