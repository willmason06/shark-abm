import random
import numpy as np
import mesa
import matplotlib.pyplot as plt

# claude version with all wanted changes

# FIH
# swim toward Centre
# should i be limiting forces at each stage and then also the final one
# eg limiting at seperation alignment and cohesion then alkso on the final force?

# use self.alive = True / False instead of removing agents
# shark swims around centre rather than directly to it
# chang plotting to animation
# remove limit func


class Fish(mesa.Agent):
    def __init__(
        self,
        model
    ):
        super().__init__(model)

        heading_angle = self.random.uniform(0, 2 * np.pi)
        heading = np.array([np.cos(heading_angle), np.sin(heading_angle)])

        self.velocity = heading * self.random.uniform(0.25 * self.model.fish_max_speed, 0.75 * self.model.fish_max_speed)
        self.force = np.array([0.0, 0.0])

        self.nearby_fish = []
        self.nearby_sharks = []
        self.topo_neighbours = []


    def get_topological_neighbours(self):
        # restrict perception to a forward field of view, then keep only
        # the closest N of the visible fish (like real schooling fish
        # respond to a roughly fixed number of nearest neighbours, not
        # everyone within a fixed radius)

        if not self.nearby_fish:
            return []

        speed = np.linalg.norm(self.velocity)
        heading = self.velocity / speed if speed > 0 else np.array([1.0, 0.0])
        fov_half = self.model.fish_fov / 2

        visible = []
        for fish in self.nearby_fish:
            to_other = np.array(fish.pos) - np.array(self.pos)
            dist = np.linalg.norm(to_other)

            if dist == 0:
                visible.append((0.0, fish))
                continue

            cos_angle = np.clip(np.dot(heading, to_other / dist), -1.0, 1.0)
            angle_deg = np.degrees(np.arccos(cos_angle))

            if angle_deg <= fov_half:
                visible.append((dist, fish))

        visible.sort(key=lambda pair: pair[0])
        return [fish for _, fish in visible[:self.model.fish_topological_neighbours]]


    def local_polarization(self):
        # 0 = neighbourhood heading in random directions (disordered)
        # 1 = neighbourhood all heading the same way (perfectly aligned)

        group = self.topo_neighbours + [self]
        total = np.array([0.0, 0.0])
        count = 0

        for fish in group:
            speed = np.linalg.norm(fish.velocity)
            if speed == 0:
                continue
            total += fish.velocity / speed
            count += 1

        if count == 0:
            return 0.0

        return np.linalg.norm(total) / count


    def separation(self):
        # separation: steer to avoid crowding local flockmates
        # kept omnidirectional (not FOV filtered) - collision avoidance
        # should react even to flockmates approaching from behind

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
        # alignment: steer towards the average heading of visible,
        # topologically-nearest flockmates, weighting closer ones more

        if not self.topo_neighbours:
            return np.array([0.0, 0.0])

        total_heading = np.array([0.0, 0.0])
        total_weight = 0.0

        for fish in self.topo_neighbours:
            magnitude = np.linalg.norm(fish.velocity)

            if magnitude == 0:
                continue

            dist = np.linalg.norm(np.array(fish.pos) - np.array(self.pos))
            weight = 1.0 / (dist + 0.1)

            total_heading += (fish.velocity / magnitude) * weight
            total_weight += weight

        if total_weight == 0:
            return np.array([0.0, 0.0])

        return self.model.get_force(self, total_heading)


    def cohesion(self):
        # cohesion: steer to move towards the (distance-weighted) centre
        # of mass of visible, topologically-nearest flockmates

        if not self.topo_neighbours:
            return np.array([0.0, 0.0])

        total_position = np.array([0.0, 0.0])
        total_weight = 0.0

        for fish in self.topo_neighbours:
            dist = np.linalg.norm(np.array(fish.pos) - np.array(self.pos))
            weight = 1.0 / (dist + 0.1)

            total_position += np.array(fish.pos) * weight
            total_weight += weight

        if total_weight == 0:
            return np.array([0.0, 0.0])

        average_position = total_position / total_weight
        vector_to_centre = average_position - self.pos

        return self.model.get_force(self, vector_to_centre)


    def move_boid(self):
        separation_force = self.separation() * self.model.separation_weight
        alignment_force = self.alignment() * self.model.alignment_weight
        cohesion_force = self.cohesion() * self.model.cohesion_weight

        return separation_force + alignment_force + cohesion_force


    def flee_force(self):
        total_vector = np.array([0.0, 0.0])

        for shark in self.nearby_sharks:
            vector = np.array(shark.pos) - np.array(self.pos)
            dist = np.linalg.norm(vector)

            if dist == 0:
                continue

            direction_away = vector / dist
            total_vector += direction_away * (self.model.separation_dist - dist)

        return self.model.get_force(self, total_vector)


    def step(self):
        if self.pos is None:
            return

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

        self.topo_neighbours = self.get_topological_neighbours()

        school_force = self.move_boid()

        if self.nearby_sharks:
            # blend schooling and fleeing based on how close the nearest
            # threat is, instead of hard-switching between the two
            closest_dist = min(
                np.linalg.norm(np.array(shark.pos) - np.array(self.pos))
                for shark in self.nearby_sharks
            )
            threat = np.clip(1 - closest_dist / self.model.fish_neighbourhood_radius, 0.0, 1.0)

            flee = self.flee_force()
            self.force += school_force * (1 - threat) + flee

            speed_cap = self.model.fish_max_speed  # burst speed while fleeing

        else:
            self.force += school_force

            # cruise slower when well-aligned/cohesive with the school,
            # speed up when the local group is disordered (e.g. just
            # after a separation event)
            polarization = self.local_polarization()
            speed_cap = self.model.fish_min_speed + polarization * (
                self.model.fish_max_speed - self.model.fish_min_speed
            )

        self.force += self.model.boundary_force(self) * self.model.boundary_weight
        self.force += self.model.noise(self.model.fish_noise_strength)

        desired_velocity = self.velocity + self.force
        desired_velocity = self.model.limit_turn(
            self.velocity, desired_velocity, self.model.fish_max_turn_rate
        )

        self.velocity = self.model.limit(desired_velocity, speed_cap)
        self.new_pos = self.pos + self.velocity

        self.model.grid.move_agent(
            self,
            self.model.apply_boundary(self.new_pos)
        )

        self.force = np.array([0.0, 0.0])



class Shark(mesa.Agent):
    def __init__(
        self,
        model
    ):
        super().__init__(model)

        heading_angle = self.random.uniform(0, 2 * np.pi)
        heading = np.array([np.cos(heading_angle), np.sin(heading_angle)])

        self.velocity = heading * self.random.uniform(0.25 * self.model.shark_max_speed, 0.75 * self.model.shark_max_speed)
        self.force = np.array([0.0, 0.0])


    def move_towards_centre(self):
        centre_position = np.array([self.model.width / 2, self.model.height / 2])
        vector_to_centre = centre_position - self.pos

        self.force += self.model.get_force(self, vector_to_centre)


    def move_towards_fish(self):

        vectors = []
        distances = []

        for fish in self.nearby_fish:
            vec = np.array(fish.pos) - np.array(self.pos)
            vectors.append(vec)
            distances.append(np.linalg.norm(vec))

        index = np.argmin(distances)
        closest_fish_vec = vectors[index]

        self.force += self.model.get_force(self, closest_fish_vec)


    def eat_fish(self):
        nearby_agents = self.model.grid.get_neighbors(
            self.pos,
            radius=self.model.shark_eating_distance,
            include_center=False
        )

        for agent in nearby_agents:
            if isinstance(agent, Fish):
                self.model.grid.remove_agent(agent)
                agent.remove()


    def step(self):

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
            self.move_towards_fish()

        else:
            self.move_towards_centre()

        self.force += self.model.boundary_force(self) * self.model.boundary_weight

        desired_velocity = self.velocity + self.force
        desired_velocity = self.model.limit_turn(
            self.velocity, desired_velocity, self.model.shark_max_turn_rate
        )

        self.velocity = self.model.limit(desired_velocity, self.model.shark_max_speed)
        self.new_pos = self.pos + self.velocity

        self.model.grid.move_agent(
            self,
            self.model.apply_boundary(self.new_pos)
        )

        self.force = np.array([0.0, 0.0])
        self.eat_fish()



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
        fish_max_speed=1,
        fish_max_force=0.4,
        fish_fov=270,                       # degrees, forward field of view
        fish_topological_neighbours=7,      # nearest-N used for alignment/cohesion
        fish_max_turn_rate=np.radians(15),  # max heading change per step
        fish_noise_strength=0.02,           # small random force each step
        fish_min_speed_fraction=0.4,        # cruising speed as a fraction of max

        shark_population=1,
        shark_neighbourhood_radius=10,
        shark_max_speed=1.5,
        shark_max_force=0.4,
        shark_max_turn_rate=np.radians(10),
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
        self.fish_fov = fish_fov
        self.fish_topological_neighbours = fish_topological_neighbours
        self.fish_max_turn_rate = fish_max_turn_rate
        self.fish_noise_strength = fish_noise_strength
        self.fish_min_speed = fish_min_speed_fraction * fish_max_speed

        self.shark_population = shark_population
        self.shark_neighbourhood_radius = shark_neighbourhood_radius
        self.shark_max_speed = shark_max_speed
        self.shark_max_force = shark_max_force
        self.shark_max_turn_rate = shark_max_turn_rate
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


    def boundary_force(self, agent):

        force = np.array([0.0, 0.0])
        x, y = agent.pos

        if isinstance(agent, Fish):
            boundary_distance = self.fish_neighbourhood_radius
            max_force = self.fish_max_force

        elif isinstance(agent, Shark):
            boundary_distance = self.shark_neighbourhood_radius
            max_force = self.shark_max_force


        if x < boundary_distance:
            force[0] += (boundary_distance - x)

        if x > self.width - boundary_distance:
            force[0] -= (x - (self.width - boundary_distance))

        if y < boundary_distance:
            force[1] += (boundary_distance - y)

        if y > self.height - boundary_distance:
            force[1] -= (y - (self.height - boundary_distance))

        return self.limit(force, max_force)


    def limit(self, vector, maximum):

        magnitude = np.linalg.norm(vector)

        if magnitude == 0:
            return np.array([0.0, 0.0])

        if magnitude > maximum:
            return vector / magnitude * maximum

        return vector


    def limit_turn(self, old_velocity, new_velocity, max_turn_rad):
        # clamp the change in heading between old_velocity and
        # new_velocity to max_turn_rad, preserving new_velocity's speed

        old_speed = np.linalg.norm(old_velocity)
        new_speed = np.linalg.norm(new_velocity)

        if old_speed == 0 or new_speed == 0:
            return new_velocity

        old_dir = old_velocity / old_speed
        new_dir = new_velocity / new_speed

        cos_angle = np.clip(np.dot(old_dir, new_dir), -1.0, 1.0)
        angle = np.arccos(cos_angle)

        if angle <= max_turn_rad:
            return new_velocity

        # rotate old_dir towards new_dir by at most max_turn_rad
        cross = old_dir[0] * new_dir[1] - old_dir[1] * new_dir[0]
        turn_sign = 1.0 if cross >= 0 else -1.0
        rotate_angle = turn_sign * max_turn_rad

        cos_r = np.cos(rotate_angle)
        sin_r = np.sin(rotate_angle)
        rotated_dir = np.array([
            old_dir[0] * cos_r - old_dir[1] * sin_r,
            old_dir[0] * sin_r + old_dir[1] * cos_r
        ])

        return rotated_dir * new_speed


    def noise(self, magnitude):
        if magnitude <= 0:
            return np.array([0.0, 0.0])

        return np.random.normal(0, magnitude, 2)


    def get_force(self, agent, velocity):

        if isinstance(agent, Fish):
            max_speed = self.fish_max_speed
            max_force = self.fish_max_force

        elif isinstance(agent, Shark):
            max_speed = self.shark_max_speed
            max_force = self.shark_max_force

        magnitude = np.linalg.norm(velocity)

        if magnitude == 0:
            return np.array([0.0, 0.0])

        direction = velocity / magnitude
        velocity_max_speed = direction * max_speed

        force = velocity_max_speed - agent.velocity

        return self.limit(force, max_force)

    def apply_boundary(self, pos):
        # ContinuousSpace treats x == width / y == height as out of bounds
        # (it checks x >= x_max), so clip just inside the edge, not onto it
        eps = 1e-6

        x, y = pos
        x = np.clip(x, 0, self.width - eps)
        y = np.clip(y, 0, self.height - eps)

        return np.array([x, y])

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
for i in range(500):
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
        color='blue',
        s=30
    )

    plt.scatter(
        shark_x,
        shark_y,
        color='red',
        s=30,
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
        angles="xy",
        scale_units="xy",
        scale=0.3
    )

    plt.xlim(0, model.width)
    plt.ylim(0, model.height)
    plt.title(f"Step {i}")
    plt.pause(0.03)
