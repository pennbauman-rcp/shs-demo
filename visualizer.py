#!/bin/env python3
import argparse

from animation.data import *
from animation.window import WorldMap


# Parse command line arguments
parser = argparse.ArgumentParser(prog='SHS Animation')
parser.add_argument("-x", "--input-xlsx", default="files/simulation_input_planes.xlsx", help="XLSX file containing simulation input definitions")
parser.add_argument("-l", "--movement-log", default="files/movement_log_planes.pkl", help="Pickle file containing mission events")
parser.add_argument("-v", "--verbose", action="store_true", help="Print detailed information")
parser.add_argument("-s", "--speed", type=int, default=1, help="Animation speed, a integer between 1 and 20 ")
parser.add_argument("--style", choices=["light", "dark", "satellite"], help="Animation style and color scheme")
parser.add_argument("--icons", action="store_true", help="Use icons in place of dots of vehicles")
args = parser.parse_args()


print("Loading animation data ...")
with open(args.movement_log, "rb") as f:
    log = pickle.load(f)
world = WorldMap(args.input_xlsx, log)


world.crop(-5, -120)
world.style(args.style, args.icons)
# world.add_vehicle_graph()
world.add_cargo_charts()


print("Running animation ...")
world.run(args.speed, args.verbose)
