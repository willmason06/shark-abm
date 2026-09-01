from abm_fish import Fish, Shark, Model
from flask import Flask, request, jsonify
from flask_cors import CORS

import numpy as np


model = Model(shark_mouse_input=True)

app = Flask(__name__)
CORS(app)  # allow requests from Live Server's origin (different port than Flask's)


@app.route("/abm_fish_server", methods=["POST"])
def send_to_javascript():

    data = request.json

    mouse_x = data["mouseX"]
    mouse_y = data["mouseY"]

    for agent in model.agents:
        if isinstance(agent, Shark):
            agent.move_towards_mouse(mouse_x, mouse_y)

    model.step()

    fish_positions = []
    fish_velocities = []
    shark_positions = []
    shark_velocities = []

    for agent in model.agents:

        if isinstance(agent, Fish):
            fish_positions.append(np.asarray(agent.pos).tolist())
            fish_velocities.append(agent.velocity.tolist())

        elif isinstance(agent, Shark):
            shark_positions.append(np.asarray(agent.pos).tolist())
            shark_velocities.append(agent.velocity.tolist())

    return jsonify({
        "fish_positions": fish_positions,
        "fish_velocities": fish_velocities,
        "shark_positions": shark_positions,
        "shark_velocities": shark_velocities
    })


if __name__ == "__main__":
    app.run(debug=True)