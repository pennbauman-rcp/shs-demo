#!/bin/python3
import argparse
import tkinter

from worldmap import WorldMap
from csvdata import *

# Parse command line arguments
parser = argparse.ArgumentParser(prog='SHS Demo')
parser.add_argument("-n", "--nodes", default="data/airports_icao.csv", help="CSV file containing location node definitions")
parser.add_argument("-l", "--mission-log", help="CSV file containing mission events")
parser.add_argument("-v", "--verbose", action="store_true", help="Print detailed information")
parser.add_argument("-s", "--speed", type=int, default=1, help="Animation speed, a integer between 1 and 20 ")

args = parser.parse_args()

nodes = LocationsData.from_csv(args.nodes, args.verbose)
if args.mission_log:
    routing = RoutingData.from_csv(args.mission_log, args.verbose)
else:
    routing = None

world = WorldMap(nodes, routing)
world.crop(0, -120)
world.run(args.speed, args.verbose)
