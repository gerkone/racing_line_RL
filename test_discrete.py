import os

from src.agent_discrete.a3c import Agent

def main():
    agent = Agent("./tracks/track_4387235659010134370_ver1.npy", actor_lr = 1e-6, critic_lr = 4*1e-6, gamma = 0.99,
            render = True, beta = 0.01, batch_size = 8, fcl1_size = 128, fcl2_size = 128, fcl3_size = 64)
    agent.train(render = False)


if __name__ == "__main__":
    #tell tensorflow to train with GPU 0
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    main()
