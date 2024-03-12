#!/bin/env python3
import argparse

from animation.window import WorldMap
from animation.data import *
from data.inputform import DataInputWindow
from simulator.frontend import SelfHealingSimulation


TMP_FILE="/tmp/shs_demo_mission_log"
INPUT_FILE = "files/simulation_input_planes.xlsx"


# Parse command line arguments
parser = argparse.ArgumentParser(prog='SHS Demo')
parser.add_argument("-x", "--input-xlsx", default=INPUT_FILE, help="XLSX file containing simulation input definitions")
parser.add_argument("-l", "--movement-log", help="Pickle file containing mission events")
parser.add_argument("-v", "--verbose", action="store_true", help="Print detailed information")
parser.add_argument("-s", "--speed", type=int, default=1, help="Animation speed, a integer between 1 and 20 ")
parser.add_argument("--style", choices=["light", "dark", "satellite"], help="Animation style and color scheme")
parser.add_argument("--icons", action="store_true", help="Use icons in place of dots of vehicles")
args = parser.parse_args()


nodes = LocationsData.from_xlsx(args.input_xlsx, args.verbose)
if args.movement_log:
    routing = RoutingData.from_pickle(args.movement_log, args.verbose)
else:
    print("Loading simulation data ...")
    sim = SelfHealingSimulation(INPUT_FILE)
    dataform = DataInputWindow(sim)
    dataform.run()

    sim.set_vehicle_counts(dataform.get_vehicles())
    print("Running simulation ...")
    sim.run()
    sim.save_to_files(TMP_FILE)

    routing = RoutingData.from_pickle(TMP_FILE + ".pkl", args.verbose)


print("Running animation ...")
world = WorldMap(nodes, routing)
world.crop(-5, -120)
world.style(args.style, args.icons)
world.add_graph()
world.run(args.speed, args.verbose)
