# obsolete functions


def clip_vector(self, current_vector, target_vector, max_turn):
    heading_angle_current = np.arctan2(current_vector[1], current_vector[0])
    heading_angle_target = np.arctan2(target_vector[1], target_vector[0])

    heading_angle_diff = (heading_angle_target - heading_angle_current + np.pi) % (2 * np.pi) - np.pi
    heading_angle_diff = np.clip(heading_angle_diff, -max_turn, max_turn)

    heading_angle_new = heading_angle_current + heading_angle_diff
    
    return np.array([np.cos(heading_angle_new), np.sin(heading_angle_new)])