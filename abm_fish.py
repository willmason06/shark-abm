import random
import numpy as np
import mesa
import matplotlib.pyplot as plt

# fish

# swim toward Centre 
# swim away from shark
# variable speeds depending on distance from shark

# separation: steer to avoid crowding local flockmates
# alignment: steer towards the average heading of local flockmates
# cohesion: steer to move towards the average position (center of mass) of local flockmates

# shark 
# swim towards closest Fish
# swim towards centre

# custom pngs for fish and shark
# fix the x and y to use mesa
# add a direction

# get the vecvtor it wants to go in

# make np arrays


class Fish(mesa.Agent):
    def __init__(
        self,
        model,
        heading,
        speed
    ):
        super().__init__(model)
        self.speed = speed
        self.heading = np.array(heading, dtype=float)


    def normalise_vector(self, vector):
        vector = np.array(vector, dtype=float)
        magnitude = np.linalg.norm(vector)
        if magnitude == 0:
            return np.array([0.0, 0.0])
        return vector / magnitude


    def dist_between(self, pos):
        pos = np.array(pos, dtype=float)
        self_pos = np.array(self.pos, dtype=float)
        vector = pos - self_pos
        distance = np.linalg.norm(vector)
        return distance, vector


    def separation(self):
        if len(self.nearby_fish) == 0:
            return np.array([0.0, 0.0])
        
        separation_dist=1
        total_vector = np.array([0.0, 0.0])
        for fish in self.nearby_fish:
            dist, vector = self.dist_between(fish.pos)
            if dist <= separation_dist and dist > 0:
                direction_away = -self.normalise_vector(vector)
                total_vector += direction_away * (separation_dist - dist)

        return self.normalise_vector(total_vector)


    def alignment(self):
        if len(self.nearby_fish) == 0:
            return np.array([0.0, 0.0])
        
        total_heading = np.array([0.0, 0.0])
        
        for fish in self.nearby_fish:
            total_heading += fish.heading
        average_heading = total_heading / len(self.nearby_fish)

        return self.normalise_vector(average_heading)



    def cohesion(self):
        if len(self.nearby_fish) == 0:
            return np.array([0.0, 0.0])
        total_position = np.array([0.0, 0.0])

        for fish in self.nearby_fish:
            total_position += np.array(fish.pos)

        average_position = (
                    total_position / len(self.nearby_fish)
        )
        vector_to_centre = self.dist_between(average_position)[1]

        return self.normalise_vector(vector_to_centre)


    def move(self):

        separation_vector = self.separation()
        alignment_vector = self.alignment()
        cohesion_vector = self.cohesion()
    
        vector = 3*separation_vector + 2*alignment_vector + 1*cohesion_vector
        normalised_vector = self.normalise_vector(vector)



        heading_angle = np.arctan2(normalised_vector[1], normalised_vector[0])

        self.heading = normalised_vector

        
        new_position = self.pos + normalised_vector * self.speed

        return new_position



    def step(self):
        self.nearby_fish = self.model.grid.get_neighbors(
            self.pos,
            radius=self.model.neighbourhood_radius,
            include_center=False
        )
        new_x, new_y = self.move()
        
        # new_x = max(0, min(self.model.width - 1, new_x))
        # new_y = max(0, min(self.model.height - 1, new_y))

        self.model.grid.move_agent(
            self,
            (new_x, new_y)
        )












'''
class Shark:
    def __init__(self):


    def step(self):

'''





class Model(mesa.Model):
    def __init__(
        self,
        population=100,
        neighbourhood_radius=10,
        width=100,
        height=100,
        fish_speed=1,
        shark_speed=1,
    ):
        super().__init__()
        self.population = population
        self.neighbourhood_radius = neighbourhood_radius
        self.width = width
        self.height = height
        self.fish_speed = fish_speed
        self.shark_speed = shark_speed

        self.grid = mesa.space.ContinuousSpace(
            x_max=width,
            y_max=height,
            torus=True, # wraps or not
        )

        for i in range(population):
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            heading_angle = self.random.uniform(0, 2 * np.pi)
            heading = (np.cos(heading_angle), np.sin(heading_angle))

            fish = Fish(
                self, 
                heading,
                fish_speed

            )

            self.grid.place_agent(
                fish,
                (x, y),
            )

        self.fish_positions_history = []
        self.fish_directions_history = []
        

    def get_fish_positions(self):
        fish_positions = []
        for fish in self.agents:
            fish_positions.append((fish.pos[0], fish.pos[1]))
        return fish_positions


    def step(self):
        self.agents.shuffle_do("step")
        self.fish_positions_history.append(self.get_fish_positions())











model = Model(        
    population=100,
    width=100,
    height=100,
    fish_speed=1,
    shark_speed=1,
)

for i in range(100):
    model.step()

fish_positions_history = model.fish_positions_history

for i, fish_positions in enumerate(fish_positions_history):
    plt.clf()
    x = [pos[0] for pos in fish_positions]
    y = [pos[1] for pos in fish_positions]
    plt.scatter(x, y)
    plt.xlim(0, model.width)
    plt.ylim(0, model.height)
    plt.title(f"Step {i}")
    plt.pause(0.1)
