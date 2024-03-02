#!/bin/env python3
import argparse
import tkinter

from animation.window import WorldMap
from data.csvparse import *
from data.inputform import DataInputWindow
from simulator.wrapper import Simulation

TMP_FILE="/tmp/shs_demo_mission_log.csv"


# Parse command line arguments
parser = argparse.ArgumentParser(prog='SHS Demo')
parser.add_argument("-n", "--nodes", default="files/airports_icao.csv", help="CSV file containing location node definitions")
parser.add_argument("-l", "--mission-log", help="CSV file containing mission events")
parser.add_argument("-v", "--verbose", action="store_true", help="Print detailed information")
parser.add_argument("-s", "--speed", type=int, default=1, help="Animation speed, a integer between 1 and 20 ")
parser.add_argument("--style", choices=["light", "dark", "satellite"], help="Animation style and color scheme")
parser.add_argument("--icons", action="store_true", help="Use icons in place of dots of vehicles")
args = parser.parse_args()


nodes = LocationsData.from_csv(args.nodes, args.verbose)
if args.mission_log:
    routing = RoutingData.from_csv(args.mission_log, args.verbose)
else:
    print("Loading simulation data ...")
    sim = Simulation.from_xlsx("files/simulation_input.xlsx")
    dataform = DataInputWindow(sim)
    dataform.run()

    sim.set_vehicle_counts(dataform.get_vehicles())
    print("Running simulation ...")
    sim.run()
    sim.save_to_csv(TMP_FILE)

    routing = RoutingData.from_csv(TMP_FILE, args.verbose)


print("Running animation ...")
world = WorldMap(nodes, routing)
world.crop(-5, -120)
world.style(args.style, args.icons)
world.add_graph()
world.run(args.speed, args.verbose)
