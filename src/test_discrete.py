from agent_discrete.a3c import Agent

def main():
    agent = Agent("../tracks/track_4387235659010134370.npy")
    agent.train()


if __name__ == "__main__":
    main()
