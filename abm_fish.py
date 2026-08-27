import random
import mesa
import matplotlib.pyplot as plt

# fish
# swim toward Centre 
# swim in same direction as others
# swim within range of others
# swim away from shark


# shark 
# swim towards closest Fish
# swim towards centre

# model 
# set number of fish and sharks
# set start postion
# set speeds
# set grid size
# assign ids

class Fish:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y


    def step(self):



class Shark:
    def __init__(self):


    def step(self):




class Model:
    def __init__(self):

    def step(self):



model = Model()
results = []

for i in range(100):
    model.step()
    results.append(model.results)


