import random
import matplotlib.pyplot as plt


# -----------------------------
# AGENT
# -----------------------------

class Agent:
    def __init__(self, agent_id, x, y):
        self.id = agent_id
        self.x = x
        self.y = y

        # Possible states:
        # "healthy"
        # "infected"
        # "recovered"

        self.state = "healthy"

        # How long the agent has been infected
        self.infection_time = 0

    def move(self, grid_size):
        """Move randomly around the grid."""

        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])

        self.x += dx
        self.y += dy

        # Keep agent inside the grid
        self.x = max(0, min(grid_size - 1, self.x))
        self.y = max(0, min(grid_size - 1, self.y))


# -----------------------------
# MODEL
# -----------------------------

class Simulation:
    def __init__(
        self,
        population=100,
        grid_size=20,
        infection_chance=0.2,
        recovery_time=10,
    ):

        self.population = population
        self.grid_size = grid_size
        self.infection_chance = infection_chance
        self.recovery_time = recovery_time

        self.agents = []

        self.healthy_history = []
        self.infected_history = []
        self.recovered_history = []

        # Create agents
        for i in range(population):

            x = random.randint(0, grid_size - 1)
            y = random.randint(0, grid_size - 1)

            agent = Agent(i, x, y)

            self.agents.append(agent)

        # Infect one random agent at the start
        random.choice(self.agents).state = "infected"

    def step(self):

        # -----------------------------
        # MOVE AGENTS
        # -----------------------------

        for agent in self.agents:
            agent.move(self.grid_size)

        # -----------------------------
        # SPREAD INFECTION
        # -----------------------------

        infected_agents = [
            agent
            for agent in self.agents
            if agent.state == "infected"
        ]

        for infected in infected_agents:

            for other in self.agents:

                if other.state == "healthy":

                    # Check if agents are in the same position
                    if (
                        infected.x == other.x
                        and infected.y == other.y
                    ):

                        # Chance of infection
                        if random.random() < self.infection_chance:

                            other.state = "infected"

        # -----------------------------
        # RECOVERY
        # -----------------------------

        for agent in self.agents:

            if agent.state == "infected":

                agent.infection_time += 1

                if agent.infection_time >= self.recovery_time:

                    agent.state = "recovered"

        # -----------------------------
        # RECORD DATA
        # -----------------------------

        healthy = sum(
            agent.state == "healthy"
            for agent in self.agents
        )

        infected = sum(
            agent.state == "infected"
            for agent in self.agents
        )

        recovered = sum(
            agent.state == "recovered"
            for agent in self.agents
        )

        self.healthy_history.append(healthy)
        self.infected_history.append(infected)
        self.recovered_history.append(recovered)

    def run(self, steps=100):

        for step in range(steps):

            self.step()

            print(
                f"Step {step + 1}: "
                f"Healthy = {self.healthy_history[-1]}, "
                f"Infected = {self.infected_history[-1]}, "
                f"Recovered = {self.recovered_history[-1]}"
            )


# -----------------------------
# RUN SIMULATION
# -----------------------------

model = Simulation(
    population=100,
    grid_size=20,
    infection_chance=0.2,
    recovery_time=10,
)

model.run(steps=100)


# -----------------------------
# PLOT RESULTS
# -----------------------------

plt.plot(model.healthy_history, label="Healthy")
plt.plot(model.infected_history, label="Infected")
plt.plot(model.recovered_history, label="Recovered")

plt.xlabel("Simulation Step")
plt.ylabel("Number of Agents")

plt.title("Agent-Based Disease Simulation")

plt.legend()

plt.show()