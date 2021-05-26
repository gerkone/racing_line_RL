import os, sys
import numpy as np
import cv2
import yaml
import collections
import matplotlib.pyplot as plt

from src.simulation.environment import TrackEnvironment, manual
from src.agent.ddpg import Agent

N_EPISODES = 1000000
CHECKPOINT = 100

def preprocess(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # plt.imshow(image)
    # plt.show()
    image = image.flatten()
    return image


def main():
    hyperparams = {}
    vision = True
    render = True or vision
    with open("src/agent/hyperparams.yaml", 'r') as stream:
        try:
            hyperparams = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
        #get simulation environment
    env = TrackEnvironment("./tracks/track_4387235659010134370_ver1.npy", render = render, vision = vision, width = 1.0,
            img_width = hyperparams["img_width"], img_height = hyperparams["img_height"])
    if render:
        visualizer_pid = env.setup_comms()
    state_dims = [env.n_states]
    action_dims = [env.n_actions]
    action_boundaries = [-1,1]
    #create agent with environment parameters
    agent = Agent(state_dims = state_dims, action_dims = action_dims,
            action_boundaries = action_boundaries, hyperparams = hyperparams)
    np.random.seed(0)

    frame_stack = collections.deque(maxlen=hyperparams["stack_depth"])
    scores = []
    #training loop: call remember on predicted states and train the models
    try:
        for i in range(N_EPISODES):
            #get initial state
            state = env.reset()
            terminal = False
            score = 0

            frame_stack.clear()
            frame_stack.append(state["image"])
            frame_stack.append(state["image"])
            frame_stack.append(state["image"])
            state["image"] = frame_stack

            #proceed until reaching an exit state
            while not terminal:
                #predict new action
                action = agent.get_action(state, i)
                #perform the transition according to the predicted action
                state_new, reward, terminal = env.step(action)
                frame_stack.append(state_new["image"])
                state_new["image"] = frame_stack

                #store the transaction in the memory
                agent.remember(state, state_new, action, reward, terminal)
                #adjust the weights according to the new transaction
                agent.learn(i)
                #iterate to the next state
                state = state_new
                score += reward
            scores.append(score)
            print("Iteration {:d} --> score {:.2f}. Running average {:.2f}".format( i, score, np.mean(scores)))
            if i > 0 and i % 5 == 0:
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
    if("manual" in sys.argv):
        while True:
            print("starting in manual mode...\n\n")
            manual("../tracks/track_4387235659010134370.npy")
    elif("keyboard" in sys.argv):
        while True:
            print("starting in manual mode...\n\n")
            manual("../tracks/track_4387235659010134370.npy", joystick = False)
    else:
        #tell tensorflow to train with GPU 0
        os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        print("starting in autonomous mode...\n\n")
        main()
