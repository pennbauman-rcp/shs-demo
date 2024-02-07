#!/bin/python3
import argparse
import tkinter

from worldmap import WorldMap
from csvdata import *

# Parse command line arguments
parser = argparse.ArgumentParser(prog='SHS Demo')
parser.add_argument("-n", "--nodes", default="data/opennav_airports.csv", help="CSV file containing location node definitions")
parser.add_argument("-l", "--mission-log", help="CSV file containing mission events")
args = parser.parse_args()

nodes = LocationsData.from_csv(args.nodes)
if args.mission_log:
    routing = RoutingData.from_csv(args.mission_log)
else:
    routing = None

world = WorldMap(nodes, routing)
world.crop(0, -120)
world.display()
