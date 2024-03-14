import os
import pickle
from operator import itemgetter
import pandas as pd
from simulator.frontend import SelfHealingSimulation



class SimGUIInputs:
    def __init__(self):
        self.nodes = {}

    def __str__(self):
        ret = "Nodes: "
        vehicles = {}
        disruptions = []
        for n in self.nodes:
            if not self.nodes[n].disabled:
                ret += self.nodes[n].icao + ", "
                for v in self.nodes[n].vehicles:
                    if v in vehicles:
                        vehicles[v] += self.nodes[n].vehicles[v]
                    else:
                        vehicles[v] = self.nodes[n].vehicles[v]
                for d in self.nodes[n].disruptions:
                    disruptions.append((d[0], n))
        ret = ret[0: -2] + "\nVehicles: "
        for v in vehicles:
            ret += v + " " + str(vehicles[v]) + ", "
        if len(disruptions) > 0:
            ret = ret[0: -2] + "\nDisruptions: "
            disruptions.sort(key=itemgetter(0))
            for d in disruptions:
                ret += d[1] + ", "
        return ret[0: -2]


    @staticmethod
    def from_xlsx(file: str):
        xls = pd.ExcelFile(file)
        nodes_raw = pd.read_excel(xls, "Army_nodes")
        nodes_raw.set_index("ICAO", inplace=True)

        ret = SimGUIInputs()
        for idx, row in nodes_raw.iterrows():
            ret.nodes[idx] = SimGUIInputs.Node(idx, row["name"])

        vehicles_raw = pd.read_excel(xls, "Vehicles")
        vehicles_raw.set_index("model", inplace=True)

        for idx, row in vehicles_raw.iterrows():
            for h in row["home"].split(","):
                home = h.split(":")
                ret.nodes[home[0]].vehicles[idx] = int(home[1])
        return ret

    def print(self):
        for n in self.nodes:
            print(self.nodes[n])

    class Node:
        def __init__(self, icao, name):
            self.icao = icao
            self.name = name
            self.vehicles = {}
            self.disruptions = []
            self.disabled = False

        def __str__(self):
            if self.disabled:
                state = "DISABLED"
            else:
                state = "enabled"
            return "%s %s v: %s d: %s %s" % (
                    self.icao,
                    self.name,
                    str(self.vehicles),
                    str(self.disruptions),
                    state
                )

class UserSim:
    def __init__(self, name, xlsx):
        self.name = name
        self.xlsx = xlsx
        self.input = None
        self.output = None

    @staticmethod
    def from_pickle(file: str):
        with open(file, "rb") as f:
            return pickle.load(f)

    def to_pickle(self, path: str):
        with open(os.path.join(path, self.name + ".pkl"), "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def from_xlsx(file: str):
        ret = SimInput()
        ret.xlsx = file
        ret.input = SimGUIInputs.from_xlsx(file)
        return ret


    def run(self):
        sim = SelfHealingSimulation(self.xlsx)
        vehicles = {}
        for n in self.input.nodes:
            node = self.input.nodes[n]
            for v in node.vehicles:
                if v in vehicles:
                    vehicles[v][n] = node.vehicles[v]
                else:
                    vehicles[v] = {}
                    vehicles[v][n] = node.vehicles[v]
            if node.disabled:
                sim.add_disruption(n, 0, 10000)
            else:
                for d in node.disruptions:
                    sim.add_disruption(n, d[0], d[1])
        sim.set_vehicle_counts(vehicles)
        sim.run()
        self.output = sim.cargo_log
