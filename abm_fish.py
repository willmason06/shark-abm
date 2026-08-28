import random
import numpy as np
import mesa
import matplotlib.pyplot as plt

# FIH
# swim toward Centre 
# swim away from shark
# variable speeds depending on distance from shark

# when shark near centre swim randomly 





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


    def separation(self):
        if len(self.nearby_fish) == 0:
            return np.array([0.0, 0.0])
        
        total_vector = np.array([0.0, 0.0])
        for fish in self.nearby_fish:
            dist, vector = self.model.dist_between(self.pos, fish.pos)
            if dist <= self.model.separation_dist and dist > 0:
                direction_away = -self.model.normalise_vector(vector)
                total_vector += direction_away * (self.model.separation_dist - dist)

        return self.model.normalise_vector(total_vector)


    def alignment(self):
        if len(self.nearby_fish) == 0:
            return np.array([0.0, 0.0])
        
        total_heading = np.array([0.0, 0.0])
        
        for fish in self.nearby_fish:
            total_heading += fish.heading
        average_heading = total_heading / len(self.nearby_fish)

        return self.model.normalise_vector(average_heading)


    def cohesion(self):
        if len(self.nearby_fish) == 0:
            return np.array([0.0, 0.0])
        total_position = np.array([0.0, 0.0])

        for fish in self.nearby_fish:
            total_position += np.array(fish.pos)

        average_position = (
                    total_position / len(self.nearby_fish)
        )
        vector_to_centre = self.model.dist_between(self.pos, average_position)[1]

        return self.model.normalise_vector(vector_to_centre)


    def move_boid(self):

        separation_vector = self.separation() # separation: steer to avoid crowding local flockmates
        alignment_vector = self.alignment() # alignment: steer towards the average heading of local flockmates
        cohesion_vector = self.cohesion() # cohesion: steer to move towards the average position (center of mass) of local flockmates
    
        combined_vector = 3*separation_vector + 2*alignment_vector + 1*cohesion_vector

        self.heading = self.heading = self.model.clip_vector(self.heading, combined_vector, self.model.fish_max_turn)
        self.new_pos = self.pos + self.heading * self.speed


    def run_from_shark(self):
        total_vector = np.array([0.0, 0.0])
        for shark in self.nearby_sharks:
            dist, vector = self.model.dist_between(self.pos, shark.pos)
            direction_away = self.model.normalise_vector(vector)
            total_vector += direction_away * (self.model.separation_dist - dist)

        self.heading = self.model.normalise_vector(total_vector)
        self.new_pos = self.pos + self.heading * self.speed


    def step(self):
        nearby_agents = self.model.grid.get_neighbors(
            self.pos,
            radius=self.model.fish_neighbourhood_radius,
            include_center=False
        )
        self.nearby_fish = [
            agent for agent in nearby_agents
            if isinstance(agent, Fish)
        ]

        self.nearby_sharks = [
            agent for agent in nearby_agents
            if isinstance(agent, Shark)
        ]
        if self.nearby_sharks:
            self.run_from_shark()
        else:
            self.move_boid()
        
        # new_x = max(0, min(self.model.width - 1, new_x))
        # new_y = max(0, min(self.model.height - 1, new_y))

        self.model.grid.move_agent(
            self,
            self.new_pos
        )



class Shark(mesa.Agent):
    def __init__(
        self,
        model,
        heading,
        speed
    ):
        super().__init__(model)
        self.speed = speed
        self.heading = np.array(heading, dtype=float)

    def find_closest_fish_group(self):
        total_vec = np.array([0.0,0.0])

        for fish in self.nearby_fish:
            dist, vec = self.model.dist_between(self.pos, fish.pos)
            total_vec += vec
        return self.model.normalise_vector(total_vec)

    def move_towards_centre(self):
        centre_position = np.array([self.model.width / 2, self.model.height / 2])
        vector_to_centre = self.model.dist_between(self.pos, centre_position)[1]

        self.heading = self.heading = self.model.clip_vector(self.heading, vector_to_centre, self.model.shark_max_turn)
        self.new_pos = self.pos + self.heading * self.speed
        

    def move_towards_closest_fish(self):
        closest_fish_vec = self.find_closest_fish_group()
        self.heading = self.model.clip_vector(self.heading, closest_fish_vec, self.model.shark_max_turn)
        self.new_pos = self.pos + self.heading * self.speed
        


    def eat_fish(self):
        nearby_agents = self.model.grid.get_neighbors(
            self.pos,
            radius=self.model.eating_distance,
            include_center=False
        )

        for agent in nearby_agents:
            if isinstance(agent, Fish):
                agent.remove()

    def step(self):
        self.eat_fish()

        nearby_agents = self.model.grid.get_neighbors(
            self.pos,
            radius=self.model.shark_neighbourhood_radius,
            include_center=False
        )
        self.nearby_fish = [
            agent for agent in nearby_agents
            if isinstance(agent, Fish)
        ]

        if self.nearby_fish:
            self.move_towards_closest_fish()
        else:
            self.move_towards_centre()

        self.model.grid.move_agent(
            self,
            self.new_pos
        )



class Model(mesa.Model):
    def __init__(
        self,
        fish_population=100,
        shark_population=1,
        fish_neighbourhood_radius=10,
        shark_neighbourhood_radius=20,
        width=100,
        height=100,
        fish_speed=1,
        shark_speed=1.5,
        separation_dist=1,
        fish_max_turn=np.pi/12,
        shark_max_turn=np.pi/6,
        eating_distance=1
    ):
        
        super().__init__()
        self.fish_population = fish_population
        self.shark_population = shark_population
        self.fish_neighbourhood_radius = fish_neighbourhood_radius
        self.shark_neighbourhood_radius = shark_neighbourhood_radius
        self.width = width
        self.height = height
        self.fish_speed = fish_speed
        self.shark_speed = shark_speed
        self.separation_dist = separation_dist
        self.fish_max_turn = fish_max_turn
        self.shark_max_turn = shark_max_turn
        self.eating_distance = eating_distance

        self.grid = mesa.space.ContinuousSpace(
            x_max=width,
            y_max=height,
            torus=True, # wraps or not
        )

        for i in range(self.fish_population):
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

        for i in range(self.shark_population):
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            heading_angle = self.random.uniform(0, 2 * np.pi)
            heading = (np.cos(heading_angle), np.sin(heading_angle))

            shark = Shark(
                self, 
                heading,
                shark_speed
            )

            self.grid.place_agent(
                shark,
                (x, y),
            )

        self.fish_positions_history = []
        self.fish_directions_history = []

        self.shark_positions_history = []
        self.shark_directions_history = []


    def normalise_vector(self, vector):
        vector = np.array(vector, dtype=float)
        magnitude = np.linalg.norm(vector)
        if magnitude == 0:
            return np.array([0.0, 0.0])
        return vector / magnitude


    def dist_between(self, pos1, pos2):
        pos1 = np.array(pos1, dtype=float)
        pos2 = np.array(pos2, dtype=float)
        vector = pos2 - pos1
        distance = np.linalg.norm(vector)
        return distance, vector


    def clip_vector(self, current_vector, target_vector, max_turn):
        heading_angle_current = np.arctan2(current_vector[1], current_vector[0])
        heading_angle_target = np.arctan2(target_vector[1], target_vector[0])

        heading_angle_diff = (heading_angle_target - heading_angle_current + np.pi) % (2 * np.pi) - np.pi
        heading_angle_diff = np.clip(heading_angle_diff, -max_turn, max_turn)

        heading_angle_new = heading_angle_current + heading_angle_diff
        
        return np.array([np.cos(heading_angle_new), np.sin(heading_angle_new)])


    def get_fish_positions(self):
        fish_positions = []
        for agent in self.agents:
            if isinstance(agent, Fish):
                fish_positions.append((agent.pos[0], agent.pos[1]))
        return fish_positions


    def get_shark_positions(self):
        shark_positions = []
        for agent in self.agents:
            if isinstance(agent, Shark):
                shark_positions.append((agent.pos[0], agent.pos[1]))
        return shark_positions


    def step(self):
        self.agents.shuffle_do("step")

        self.fish_positions_history.append(self.get_fish_positions())
        self.fish_directions_history.append([agent.heading for agent in self.agents if isinstance(agent, Fish)])

        self.shark_positions_history.append(self.get_shark_positions())
        self.shark_directions_history.append([agent.heading for agent in self.agents if isinstance(agent, Shark)])



model = Model()
for i in range(500):
    model.step()

fish_positions_history = model.fish_positions_history
fish_directions_history = model.fish_directions_history

shark_positions_history = model.shark_positions_history
shark_directions_history = model.shark_directions_history

for i, fish_positions in enumerate(fish_positions_history):
    plt.clf()

    fish_x = [pos[0] for pos in fish_positions]
    fish_y = [pos[1] for pos in fish_positions]
    fish_dx = [heading[0] for heading in fish_directions_history[i]]
    fish_dy = [heading[1] for heading in fish_directions_history[i]]

    shark_x = [pos[0] for pos in shark_positions_history[i]]
    shark_y = [pos[1] for pos in shark_positions_history[i]]
    shark_dx = [heading[0] for heading in shark_directions_history[i]]
    shark_dy = [heading[1] for heading in shark_directions_history[i]]

    plt.quiver(fish_x, fish_y, fish_dx, fish_dy, color='blue', scale=20)
    plt.quiver(shark_x, shark_y, shark_dx, shark_dy, color='red', scale=20)
    plt.xlim(0, model.width)
    plt.ylim(0, model.height)
    plt.title(f"Step {i}")
    plt.pause(0.03)
