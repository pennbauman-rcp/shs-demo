#!/bin/env python3
import argparse

from animation.data import *
from animation.window import WorldMap


# Parse command line arguments
parser = argparse.ArgumentParser(prog='SHS Animation')
parser.add_argument("-x", "--input-xlsx", default="files/simulation_input_transload.xlsx", help="XLSX file containing simulation input definitions")
parser.add_argument("-l", "--movement-log", default="files/movement_log_transload.pkl", help="Pickle file containing mission events")
parser.add_argument("-v", "--verbose", action="store_true", help="Print detailed information")
parser.add_argument("-s", "--speed", type=int, default=1, help="Animation speed, a integer between 1 and 20 ")
parser.add_argument("--style", choices=["light", "dark", "satellite"], help="Animation style and color scheme")
parser.add_argument("--icons", action="store_true", help="Use icons in place of dots of vehicles")
args = parser.parse_args()


print("Loading animation data ...")
nodes = LocationsData.from_xlsx(args.input_xlsx, args.verbose)
routing = RoutingData.from_pickle(args.movement_log, args.verbose)


print("Running animation ...")
world = WorldMap(nodes, routing)
world.crop(-5, -120)
world.style(args.style, args.icons)
world.add_graph()
world.run(args.speed, args.verbose)
