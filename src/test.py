import os, sys

from simulation.environment import TrackEnvironment, manual
from agent.ddpg import Agent

N_EPISODES = 1000
CHECKPOINT = 100

def main():
    #TODO args to load model
    #get simulation environment
    env = TrackEnvironment("../tracks/track_4387235659010134370.npy", render = True, width = 1.5)
    state_dims = [env.n_states]
    action_dims = [env.n_actions]
    action_boundaries = [-1,1]
    #create agent with environment parameters
    agent = Agent(state_dims = state_dims, action_dims = action_dims,
                action_boundaries = action_boundaries, actor_lr = 1e-6,
                critic_lr = 4*1e-6, batch_size = 128, gamma = 0.99, rand_steps = 2,
                buf_size = int(1e4), tau = 0.001, fcl1_size = 256, fcl2_size = 256)
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
            action = agent.get_action(state, i)
            #perform the transition according to the predicted action
            state_new, reward, terminal = env.step(action)
            #store the transaction in the memory
            agent.remember(state, state_new, action, reward, terminal)
            #adjust the weights according to the new transaction
            agent.learn(i)
            #iterate to the next state
            state = state_new
            score += reward
            env.render()
        scores.append(score)
        print("Iteration {:d} --> score {:.2f}. Running average {:.2f}".format( i, score, np.mean(scores)))
        # if i % CHECKPOINT:
        #     agent.save()

    plt.plot(scores)
    plt.xlabel("Episode")
    plt.ylabel("Cumulate reward")
    plt.show()



if __name__ == "__main__":

    if("manual" in sys.argv):
        while True:
            print("starting in manual mode...\n\n")
            manual("../tracks/track_4387235659010134370.npy")
    else:
        #tell tensorflow to train with GPU 0
        os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        print("starting in autonomous mode...\n\n")
        main()
