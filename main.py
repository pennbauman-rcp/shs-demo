#!/bin/python3
import argparse
import tkinter

from worldmap import WorldMap
from csvdata import *

# Parse command line arguments
parser = argparse.ArgumentParser(prog='SHS Demo')
parser.add_argument("-b", "--bases", default="data/opennav_airports.csv", help="CSV file containing base definitions")
parser.add_argument("-e", "--event-log", help="CSV file containing events")
args = parser.parse_args()

bases = BasesData.from_csv(args.bases)
if args.event_log:
    routing = RoutingData.from_csv(args.event_log)
else:
    routing = None

world = WorldMap(bases, routing)
world.crop(0, -120)
world.display()
