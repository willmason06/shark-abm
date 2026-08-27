import random
import mesa
import matplotlib.pyplot as plt


# =========================================
# AGENT
# =========================================

class Person(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)

        # Possible states:
        # healthy
        # infected
        # recovered
        self.state = "healthy"

        # How long the person has been infected
        self.infection_time = 0

    def step(self):
        # ---------------------------------
        # MOVE RANDOMLY
        # ---------------------------------

        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False,
        )

        new_position = self.random.choice(possible_steps)

        self.model.grid.move_agent(
            self,
            new_position,
        )

        # ---------------------------------
        # SPREAD INFECTION
        # ---------------------------------

        cellmates = self.model.grid.get_cell_list_contents(
            [self.pos]
        )

        if self.state == "infected":

            for other in cellmates:

                if other.state == "healthy":

                    if (
                        self.random.random()
                        < self.model.infection_chance
                    ):

                        other.state = "infected"

        # ---------------------------------
        # RECOVERY
        # ---------------------------------

        if self.state == "infected":

            self.infection_time += 1

            if (
                self.infection_time
                >= self.model.recovery_time
            ):

                self.state = "recovered"


# =========================================
# MODEL
# =========================================

class DiseaseModel(mesa.Model):
    def __init__(
        self,
        population=100,
        width=20,
        height=20,
        infection_chance=0.2,
        recovery_time=10,
    ):
        super().__init__()

        self.population = population
        self.infection_chance = infection_chance
        self.recovery_time = recovery_time

        # Create the grid
        self.grid = mesa.space.MultiGrid(
            width,
            height,
            torus=True,
        )

        # Create agents
        for _ in range(population):

            person = Person(self)

            x = self.random.randrange(width)
            y = self.random.randrange(height)

            self.grid.place_agent(
                person,
                (x, y),
            )

        # Infect one random agent
        patient_zero = self.random.choice(
            list(self.agents)
        )

        patient_zero.state = "infected"

        # Store data for graphing
        self.healthy_history = []
        self.infected_history = []
        self.recovered_history = []

    def step(self):
        # Make every agent perform its step
        self.agents.shuffle_do("step")

        # Count each state
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

        # Save results
        self.healthy_history.append(healthy)
        self.infected_history.append(infected)
        self.recovered_history.append(recovered)


# =========================================
# RUN SIMULATION
# =========================================

model = DiseaseModel(
    population=100,
    width=20,
    height=20,
    infection_chance=0.2,
    recovery_time=10,
)

steps = 100

for step in range(steps):

    model.step()

    print(
        f"Step {step + 1}: "
        f"Healthy = {model.healthy_history[-1]}, "
        f"Infected = {model.infected_history[-1]}, "
        f"Recovered = {model.recovered_history[-1]}"
    )


# =========================================
# PLOT RESULTS
# =========================================

plt.plot(
    model.healthy_history,
    label="Healthy",
)

plt.plot(
    model.infected_history,
    label="Infected",
)

plt.plot(
    model.recovered_history,
    label="Recovered",
)

plt.xlabel("Simulation Step")
plt.ylabel("Number of Agents")
plt.title("Mesa Agent-Based Disease Simulation")

plt.legend()

plt.show()