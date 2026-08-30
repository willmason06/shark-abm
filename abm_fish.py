import random
import numpy as np
import mesa
import matplotlib.pyplot as plt

# FIH
# swim toward Centre 
# variable speeds depending on distance from shark



class Fish(mesa.Agent):
    def __init__(
        self,
        model
    ):
        super().__init__(model)

        heading_angle = self.random.uniform(0, 2 * np.pi)
        heading = np.array(np.cos(heading_angle), np.sin(heading_angle))

        self.velocity = heading * self.random.uniform(0.25 * self.model.fish_max_speed, 0.75* self.model.fish_max_speed)
        self.acceleration = np.array([0.0, 0.0])


    def separation(self):
        # separation: steer to avoid crowding local flockmates

        if len(self.nearby_fish) == 0:
            return np.array([0.0, 0.0])
        
        total_seperation_force = np.array([0.0, 0.0])

        for fish in self.nearby_fish:
            vector = np.array(fish.pos) - np.array(self.pos)
            dist = np.linalg.norm(vector)

            if dist <= self.model.separation_dist and dist > 0:
                direction_away = - vector / np.linalg.norm(vector)
                total_seperation_force += direction_away * (self.model.separation_dist - dist)

        return self.model.limit(total_seperation_force, self.model.fish_max_force)


    def alignment(self):
        # alignment: steer towards the average heading of local flockmates

        if len(self.nearby_fish) == 0:
            return np.array([0.0, 0.0])
        
        total_heading = np.array([0.0, 0.0])
        
        for fish in self.nearby_fish:
            fish_heading = fish.velocity / np.linalg.norm(fish.velocity)
            total_heading += fish_heading

        return self.get_force(total_heading)


    def cohesion(self):
        # cohesion: steer to move towards the average position (center of mass) of local flockmates

        if len(self.nearby_fish) == 0:
            return np.array([0.0, 0.0])
        
        total_position = np.array([0.0, 0.0])

        for fish in self.nearby_fish:
            total_position += np.array(fish.pos)

        average_position = (
                    total_position / len(self.nearby_fish)
        )
        vector_to_centre = average_position - self.pos

        return self.get_force(vector_to_centre)


    def boundary_force(self):

        force = np.array([0.0, 0.0])
        boundary_distance = self.model.fish_neighbourhood_radius

        x, y = self.pos

        if x < boundary_distance:
            force[0] += (boundary_distance - x)

        if x > self.model.width - boundary_distance:
            force[0] -= (x - (self.model.width - boundary_distance))

        if y < boundary_distance:
            force[1] += (boundary_distance - y)

        if y > self.model.height - boundary_distance:
            force[1] -= (y - (self.model.height - boundary_distance))

        return self.model.limit(force,self.model.fish_max_force)


    def get_force(self, velocity):
        # self.fish_max_speed change if shark uses function too

        direction = velocity / np.linalg.norm(velocity)
        velocity_max_speed = direction * self.model.fish_max_speed

        force = velocity_max_speed - self.velocity

        return self.model.limit(force, self.model.fish_max_force)



    def move_boid(self):

        separation_force = self.separation() * self.model.separation_weight
        alignment_force = self.alignment() * self.model.alignment_weight 
        cohesion_force = self.cohesion() * self.model.cohesion_weight

        boundary_force = self.boundary_force() * self.model.boundary_weight
    
        self.acceleration = separation_force + alignment_force + cohesion_force + boundary_force
        self.velocity += self.acceleration
        self.velocity = self.model.limit(self.velocity, self.model.fish_max_speed)
        self.new_pos = self.pos + self.velocity


    def run_from_shark(self):
        total_vector = np.array([0.0, 0.0])
        for shark in self.nearby_sharks:
            vector = shark.pos - self.pos
            dist = np.linalg.norm(vector)
            direction_away = vector / np.linalg.norm(vector)
            total_vector += direction_away * (self.model.separation_dist - dist)

        
        self.new_pos = self.pos


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
        
        self.model.grid.move_agent(
            self,
            self.new_pos
        )



class Shark(mesa.Agent):
    def __init__(
        self,
        model,
    ):
        super().__init__(model)

        heading_angle = self.random.uniform(0, 2 * np.pi)
        heading = (np.cos(heading_angle), np.sin(heading_angle))
        
        self.speed = self.model.shark_speed
        self.heading = np.array(heading, dtype=float)


    def move_towards_centre(self):
        centre_position = np.array([self.model.width / 2, self.model.height / 2])
        vector_to_centre = centre_position - self.pos

        self.heading = self.heading = self.model.clip_vector(self.heading, vector_to_centre, self.model.shark_max_turn)
        self.new_pos = self.pos + self.heading * self.speed
        

    def move_towards_closest_fish(self):
        total_vec = np.array([0.0,0.0])

        for fish in self.nearby_fish:
            vec = fish.pos - self.pos
            total_vec += vec
        closest_fish_vec = total_vec / np.linalg.norm(total_vec)

        self.heading = self.model.clip_vector(self.heading, closest_fish_vec, self.model.shark_max_turn)
        self.new_pos = self.pos + self.heading * self.speed
        


    def eat_fish(self):
        nearby_agents = self.model.grid.get_neighbors(
            self.pos,
            radius=self.model.shark_eating_distance,
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
        
        width=100,
        height=100,

        separation_weight=2,
        alignment_weight=1,
        cohesion_weight=0.3,
        boundary_weight=2,
        separation_dist=1,
        
        fish_population=100,
        fish_neighbourhood_radius=10,
        fish_max_speed=2,
        fish_max_force=0.4,

        shark_population=0,
        shark_neighbourhood_radius=20,
        shark_max_speed=1.5,
        shark_eating_distance=1,

    ):
    
        super().__init__()

        self.width = width
        self.height = height

        self.separation_weight = separation_weight
        self.alignment_weight = alignment_weight
        self.cohesion_weight = cohesion_weight
        self.boundary_weight = boundary_weight
        self.separation_dist = separation_dist

        self.fish_population = fish_population
        self.fish_neighbourhood_radius = fish_neighbourhood_radius
        self.fish_max_speed = fish_max_speed
        self.fish_max_force = fish_max_force

        self.shark_population = shark_population
        self.shark_neighbourhood_radius = shark_neighbourhood_radius
        self.shark_max_speed = shark_max_speed
        self.shark_eating_distance = shark_eating_distance

        self.grid = mesa.space.ContinuousSpace(
            x_max=width,
            y_max=height,
            torus=False, # wraps or not
        )

        for i in range(self.fish_population):
            x = self.random.randrange(width)
            y = self.random.randrange(height)

            fish = Fish(
                self, 
            )

            self.grid.place_agent(
                fish,
                (x, y),
            )

        for i in range(self.shark_population):
            x = self.random.randrange(width)
            y = self.random.randrange(height)

            shark = Shark(
                self, 
            )

            self.grid.place_agent(
                shark,
                (x, y),
            )

        self.fish_positions_history = []
        self.fish_velocity_history = []

        self.shark_positions_history = []
        self.shark_velocity_history = []


    def limit(self, vector, maximum):

        magnitude = np.linalg.norm(vector)

        if magnitude > maximum:
            return vector / magnitude * maximum

        return vector


    def step(self):
        self.agents.shuffle_do("step")

        fish_positions = []
        fish_velocities = []
        shark_positions = []
        shark_velocities = []

        for agent in self.agents:

            if isinstance(agent, Fish):
                fish_positions.append(tuple(agent.pos))
                fish_velocities.append(agent.velocity.copy())

            elif isinstance(agent, Shark):
                shark_positions.append(tuple(agent.pos))
                shark_velocities.append(agent.velocity.copy())

        self.fish_positions_history.append(fish_positions)
        self.fish_velocity_history.append(fish_velocities)
        self.shark_positions_history.append(shark_positions)
        self.shark_velocity_history.append(shark_velocities)





model = Model()
for i in range(100):
    model.step()

fish_positions_history = model.fish_positions_history
fish_velocity_history = model.fish_velocity_history

shark_positions_history = model.shark_positions_history
shark_velocity_history = model.shark_velocity_history






for i, fish_positions in enumerate(fish_positions_history):
    plt.clf()

    fish_x = [pos[0] for pos in fish_positions]
    fish_y = [pos[1] for pos in fish_positions]
    fish_dx = [heading[0] for heading in fish_velocity_history[i]]
    fish_dy = [heading[1] for heading in fish_velocity_history[i]]

    shark_x = [pos[0] for pos in shark_positions_history[i]]
    shark_y = [pos[1] for pos in shark_positions_history[i]]
    shark_dx = [heading[0] for heading in shark_velocity_history[i]]
    shark_dy = [heading[1] for heading in shark_velocity_history[i]]

    plt.scatter(
        fish_x,
        fish_y,
        s=30
    )

    plt.quiver(
        fish_x, 
        fish_y, 
        fish_dx, 
        fish_dy, 
        color='blue', 
        angles="xy",
        scale_units="xy",
        scale=0.3
    )
    
    plt.quiver(
        shark_x, 
        shark_y, 
        shark_dx, 
        shark_dy, 
        color='red', 
        scale=20
    )



    plt.xlim(0, model.width)
    plt.ylim(0, model.height)
    plt.title(f"Step {i}")
    plt.pause(0.03)

