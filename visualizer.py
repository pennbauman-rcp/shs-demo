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
nodes = LocationsData.from_xlsx(args.input_xlsx, args.verbose)
routing = RoutingData.from_pickle(args.movement_log, args.verbose)
cargo = CargoData.from_pickle(args.movement_log, args.verbose)


print("Running animation ...")
world = WorldMap(nodes, routing, cargo)
world.crop(-5, -120)
world.style(args.style, args.icons)
world.add_cargo_piechart("KFCS", 60, -100)
world.add_cargo_piechart("KBGR", 70, -60)
world.add_cargo_piechart("KGRK", 10, -90)
world.add_cargo_piechart("LERT", 10, -15)
world.add_cargo_piechart("ETAD", 70, -15)
world.add_cargo_piechart("ETAR", 20, 30)
world.add_cargo_piechart("EPKK", 70, 30)
world.run(args.speed, args.verbose)
