import sys
import re
import tkinter
from tkinter import ttk

from simulator.frontend import SelfHealingSimulation

# Default counts for each vehicle
VEHICLE_COUNTS = {
        "C17":      10,
        "B777":     10,
        "LMSR":     5,
        "train_US": 10,
        "truck_EU": 50,
        "truck_US": 50,
        "train_EU": 10,
    }
# Label text for each vehicle
VEHICLE_FANCY_NAMES = {
        "C17":      "C17 (Airplane)",
        "B777":     "B777 (Airplane)",
        "LMSR":     "LMSR (Ship)",
        "train_US": "US Train",
        "truck_US": "US Truck",
        "train_EU": "EU Train",
        "truck_EU": "EU Truck",
    }

class Data:
    def __init__(self):
        self.nodes = []
        self.vehicles = []

    def __str__(self):
        ret = "DATA\nVehicles\n"
        for v in self.vehicles:
            ret += str(v) + "\n"
        ret += "\nNodes\n"
        for n in self.nodes:
            ret += str(n) + "\n"
        return ret

    @staticmethod
    def from_sim(sim: SelfHealingSimulation):
        self = Data()
        for v in sim.vehicles.index:
            self.vehicles.append(self.Vehicle(v, sim.vehicles.at[v, "home"]))
        for n in sim.nodes.index:
            node = self.Node(n)
            for v in self.vehicles:
                for h in v.homes:
                    if h == n:
                        node.vehicles[v.model] = v.homes[h]
            self.nodes.append(node)
        return self

    def update_node(self, name: str, data: dict):
        for n in self.nodes:
            if n.name == name:
                n.vehicles = data
                return
        raise ValueError("Unknown node '%s'" % name)

    def add_disruption(self, name: str, disrupt: tuple[float, float]):
        for n in self.nodes:
            if n.name == name:
                n.disruption.append(disrupt)
                return
        raise ValueError("Unknown node '%s'" % name)

    def sync_vehicles(self):
        for v in self.vehicles:
            new = {}
            for n in self.nodes:
                for model in n.vehicles:
                    if model == v.model:
                        new[n.name] = n.vehicles[model]
            v.homes = new



    class Vehicle:
        def __init__(self, model: str, homes: dict):
            self.model = model
            self.homes = homes

        def __str__(self):
            return "%s @ %s" % (self.model, str(self.homes))

        def total(self) -> int:
            count = 0
            for h in homes:
                count += homes[h]
            return count

    class Node:
        def __init__(self, name):
            self.name = name
            self.vehicles = {}
            self.disruption = []

        def __str__(self):
            if len(self.disruption) == 0:
                disrupt = "-"
            else:
                disrupt = "(%f, %f)" % (self.disruption[0][0], self.disruption[0][1])
            return "%s > %s # %s" % (self.name, str(self.vehicles), disrupt)


class DataInputWindow:
    def __init__(self, sim: SelfHealingSimulation):
        self.data = Data.from_sim(sim)

    def run(self):
        # Setup window
        self.tk = tkinter.Tk()
        self.tk.title("SHS Demo")
        self.tk.grid()
        self.frame = tkinter.Frame(self.tk, padx=50, pady=20)
        self.frame.grid()
        # Setup titie
        self.title = tkinter.Label(self.frame, text="Vehicle Counts", font=("Helvetica", 18))
        self.title.grid(row=0, column=0)
        # Setup vehicle entry boxes
        i = 1
        self.nodes = []
        for n in self.data.nodes:
            if len(n.vehicles) == 0:
                continue
            form = NodeForm(n)
            form.display(self.frame, i)
            self.nodes.append(form)
            i += 1

        # Setup go button
        self.button = ttk.Button(self.frame, text="Run Simulation", command=self.submit)
        self.button.grid(row=i + 1, column=0)

        self.tk.mainloop()
        return self.data

    def get_vehicles(self):
        ret = {}
        for v in self.data.vehicles:
            ret[v.model] = v.homes
        return ret

    def submit(self):
        error = False
        for n in self.nodes:
            vehicles = n.parse_vehicles()
            disrupt = n.parse_disruption()
            if vehicles:
                self.data.update_node(n.data.name, vehicles)
            else:
                error = True
            if disrupt:
                self.data.add_disruption(n.data.name, disrupt)
        self.data.sync_vehicles()
        # If all data is valid, save it and close the window
        if not error:
            print(self.data)
            self.tk.destroy()
            self.tk.quit()


class NodeForm:
    def __init__(self, data: Data.Node):
        self.data = data

    def display(self, tk, i):
        self.frame = ttk.Frame(tk, padding=(0, 16))
        self.frame.grid(row=i, column=0)
        self.label = tkinter.Label(self.frame, text=self.data.name + " " + "-"*80, font="Helvetica 12 bold")
        self.label.grid(row=0, column=0, columnspan=3)
        # Node Vehicles
        i = 1
        self.entry = {}
        self.warnings = {}
        for v in self.data.vehicles:
            label = tkinter.Label(self.frame, text=v, width=12)
            label.grid(row=i, column=0, sticky=tkinter.W)
            # Entry box with default
            entry = tkinter.Entry(self.frame, width=20)
            entry.insert(0, self.data.vehicles[v])
            entry.grid(row=i, column=1)
            self.entry[v] = entry
            # Error message (blank by default)
            warning = tkinter.Label(self.frame, text="", width=20)
            warning.grid(row=i, column=2)
            self.warnings[v] = warning
            i += 1
        # Distruptions
        label = tkinter.Label(self.frame, text="Disruption", width=12)
        label.grid(row=i, column=0, sticky=tkinter.W)
        # Entry box start (empty)
        entry = tkinter.Entry(self.frame, width=20)
        entry.grid(row=i, column=1)
        self.disrupt_start = entry
        # Entry box end (empty)
        entry = tkinter.Entry(self.frame, width=20)
        entry.grid(row=i, column=2)
        self.disrupt_end = entry
        # Error message start
        warning = tkinter.Label(self.frame, text="", width=20)
        warning.grid(row=i + 1, column=1)
        self.start_warning = warning
        # Error message end
        warning = tkinter.Label(self.frame, text="", width=20)
        warning.grid(row=i + 1, column=2)
        self.end_warning = warning

    def parse_vehicles(self):
        error = False
        ret = {}
        for v in self.entry:
            self.warnings[v]["text"] = ""
            self.warnings[v]["bg"] = "#D9D9D9"
            try:
                val = int(self.entry[v].get())
                ret[v] = val
            except:
                self.warnings[v]["text"] = "Invalid number"
                self.warnings[v]["bg"] = "red"
                error = True
        if error:
            return None
        return ret

    def parse_disruption(self):
        error = False
        try:
            text = self.disrupt_start.get()
            if text == "":
                error = True
            else:
                start = float(text)
        except:
            self.start_warning["text"] = "Invalid number"
            self.start_warning["bg"] = "red"
            error = True
        try:
            text = self.disrupt_end.get()
            if text == "":
                error = True
            else:
                end = float(text)
        except:
            self.end_warning["text"] = "Invalid number"
            self.end_warning["bg"] = "red"
            error = True
        if error:
            return None
        return (start, end)
