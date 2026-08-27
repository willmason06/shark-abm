import random
import numpy as np
import mesa
import matplotlib.pyplot as plt

# fish
# swim within range of others
# swim in same direction as others
# swim toward Centre 
# swim away from shark


# shark 
# swim towards closest Fish
# swim towards centre

# model 
# set number of fish and sharks
# set start postion
# set speeds
# set grid size



class Fish(mesa.Agent):
    def __init__(
        self,
        model,
        x,
        y,
        speed
    ):
        super().__init__(model)
        # self.model = model
        self.x = x
        self.y = y
        self.speed = speed

    def swim_towards_other_fish(self, fish_positions):
        fish_displacements = []
        fish_distances = []
        for fish_position in fish_positions:
            x, y = fish_position
            if x == self.x and y == self.y:
                continue

            dist = np.sqrt((x - self.x)**2 + (y - self.y)**2)
            xv = (x - self.x) / dist
            yv = (y - self.y) / dist
            
            fish_displacements.append((xv, yv))
            fish_distances.append(dist)
    
        closest_fish_idx = np.argmin(fish_distances)
        closest_fish_rel_vec = fish_displacements[closest_fish_idx]

        new_x = self.x + self.speed * closest_fish_rel_vec[0]
        new_y = self.y + self.speed * closest_fish_rel_vec[1]

        return new_x, new_y



    def step(self):
        fish_positions = self.model.get_fish_positions()
        new_x, new_y = self.swim_towards_other_fish(fish_positions)
        
        new_x = max(0, min(self.model.width - 1, new_x))
        new_y = max(0, min(self.model.height - 1, new_y))

        self.x = new_x
        self.y = new_y

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
        width=100,
        height=100,
        fish_speed=1,
        shark_speed=1,
    ):
        super().__init__()
        self.population = population
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

            fish = Fish(self, x, y, fish_speed)

            self.grid.place_agent(
                fish,
                (x, y),
            )

        self.fish_positions_history = []
        

    def get_fish_positions(self):
        fish_positions = []
        for fish in self.agents:
            fish_positions.append((fish.x, fish.y))
        return fish_positions


    def step(self):
        self.agents.shuffle_do("step")
        self.fish_positions_history.append(self.get_fish_positions())






model = Model()

for i in range(100):
    model.step()

fish_positions_history = model.fish_positions_history


# make animation for plotting graph
for i, fish_positions in enumerate(fish_positions_history):
    plt.clf()
    x = [pos[0] for pos in fish_positions]
    y = [pos[1] for pos in fish_positions]
    plt.scatter(x, y)
    plt.xlim(0, model.width)
    plt.ylim(0, model.height)
    plt.title(f"Step {i}")
    plt.pause(0.1)
