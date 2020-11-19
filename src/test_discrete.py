from agent_discrete.a3c import Agent
import os

def main():
    agent = Agent("../tracks/track_4387235659010134370.npy")
    agent.train(render = True)


if __name__ == "__main__":
    #tell tensorflow to train with GPU 0
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    main()
