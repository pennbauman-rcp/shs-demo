#!/bin/python3
import tkinter

from worldmap import WorldMap
from csvdata import *

bases = BasesData.from_csv("data/bases.csv")
# print(bases)
routing = RoutingData.from_csv("data/routes_log.csv")
# print(routing)

world = WorldMap(bases, routing)
world.crop(0, -90)
world.display()
