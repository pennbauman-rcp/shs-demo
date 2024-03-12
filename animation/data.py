import sys
import csv
import pickle
import re
import pandas as pd


DIRECTION_SIGN_KEY = {
    "N":  1, "n":  1,
    "S": -1, "s": -1,
    "E":  1, "e":  1,
    "W": -1, "w": -1,
}


# Convert degrees minutes seconds notation to float degrees
def dms2float(dms: str) -> float:
    state = 0
    flip = 0
    degrees = 0
    minutes = 0
    seconds = 0

    # Parse direction letter (eg N,S,E,W)
    current = dms.strip()
    if current[0].isalpha():
        flip = DIRECTION_SIGN_KEY[current[0]]
        current = current[1:]
    elif current[-1].isalpha():
        flip = DIRECTION_SIGN_KEY[current[-1]]
        current = current[:-1]
    elif current[0] == "-":
        flip = -1
        current = current[1:]
    else:
        flip = 1
    # Parse each section in order
    i = 0
    while len(current) > 0:
        # Degrees
        if state == 0:
            if i == len(current):
                degrees = float(current)
                break
            elif current[i] in "°*":
                degrees = float(current[:i])
                current = current[i + 1:].strip()
                state = 1
                i = 0
                continue
        # Minutes
        elif state == 1:
            if i == len(current):
                minutes = float(current)
                break
            elif current[i] in "′'":
                minutes = float(current[:i])
                current = current[i + 1:].strip()
                state = 2
                i = 0
                continue
        # Seconds
        elif state == 2:
            if i == len(current):
                seconds = float(current)
                break
            elif current[i] in "″\"":
                seconds = float(current[:i])
                current = current[i + 1:].strip()
                state = 2
                i = 0
                continue
        # Check for invalid characters
        if not (current[i].isdigit() or current[i] == "."):
            raise ValueError("ERROR: Invalid degree minute second value '%s'" % (dms))
        i += 1
    return flip * (degrees + (minutes / 60) + (seconds / 3600))

def parse_coord(coord: str) -> tuple[float, float]:
    if "/" in coord:
        c = "/"
    else:
        c = ","
    return (dms2float(coord.split(c)[0]), dms2float(coord.split(c)[1]))




class LocationsData:
    def __init__(self):
        self.nodes = []

    def __str__(self):
        fin = ""
        for b in self.nodes:
            fin += str(b) + "\n"
        return fin[:-1]

    # Make iterable
    def __iter__(self):
        self.iter = self.nodes.__iter__()
        return self.iter
    def __next__(self):
        return self.iter.__next__()

    @staticmethod
    def from_xlsx(filename: str, verbose: bool = False):
        if verbose:
            print("Reading locations from XLSX (%s)" % filename)
        self = LocationsData()
        data = pd.read_excel(filename, "Army_nodes")
        for name in data.index:
            new = self.Node()
            new.name = data.at[name, "ICAO"]
            new.lat = data.at[name, "lat"]
            new.lon = data.at[name, "LNG_180"]
            self.nodes.append(new)
        return self

    class Node:
        name = ""
        lat = -365
        lon = -365

        def __str__(self):
            return "%s (%02.2f, %02.2f)" % (self.name, self.lat, self.lon)

        @staticmethod
        def from_csv(row: list[str]):
            self = LocationsData.Node()
            self.name = row[0]
            self.lat = dms2float(row[1])
            self.lon = dms2float(row[2])
            return self




class RoutingData:
    def __init__(self):
        self.event_log = []

    def __str__(self):
        fin = ""
        for e in self.event_log:
            fin += str(e) + "\n"
        return fin[:-1]

    # Make iterable
    def __iter__(self):
        self.iter = self.event_log.__iter__()
        return self.iter
    def __next__(self):
        return self.iter.__next__()

    @staticmethod
    def from_pickle(filename: str, verbose: bool = False):
        if verbose:
            print("Reading mission log from CSV (%s)" % filename)
        self = RoutingData()
        with open(filename, "rb") as f:
            data = pickle.load(f)
        for d in data:
            if not d["Vehicle_name"]:
                continue
            self.event_log.append(self.RoutingEvent.from_dict(d))
        return self

    def get_legs(self) -> list[tuple[str, str]]:
        ret = []
        vehicles = {}
        for e in self.event_log:
            if e.event == "taking off":
                if e.vehicle_id in vehicles:
                    raise ValueError("Vehicle leaing again without arriving '%s'" % e.vehicle_id)
                vehicles[e.vehicle_id] = e.location
            elif e.event == "arriving":
                if not e.vehicle_id in vehicles:
                    if e.time == 0.0:
                        continue
                    print(e)
                    raise ValueError("Vehicle arriving without leaving '%s'" % e.vehicle_id)
                ret.append((vehicles[e.vehicle_id], e.location))
                vehicles.pop(e.vehicle_id)
            elif e.event == "loading cargo":
                continue
            else:
                raise ValueError("Unknown event '%s'" % e.event)
        return ret

    def get_vehicles(self) -> list:
        ret = []
        for e in self.event_log:
            # print("Move for %s at %f" % (v.vehicle_id, e.time))
            done = False
            for v in ret:
                if v.vehicle_id == e.vehicle_id:
                    v.insert_move(e.time, e.location)
                    done = True
                    break
            if not done:
                v = self.RoutingVehicle(e.vehicle_id, e.vehicle_model)
                v.insert_move(e.time, e.location)
                ret.append(v)
        return ret

    def get_end_time(self) -> float:
        ret = 0.0
        for e in self.event_log:
            if e.time > ret:
                ret = e.time
        return ret


    class RoutingEvent:
        vehicle_id = ""
        vehicle_model = ""
        event = ""
        time: -1.0
        location = ""

        def __str__(self):
            return "T%04.1f: %s @ %s (%s)" % (self.time, self.vehicle_id, self.location, self.event)

        @staticmethod
        def from_dict(data: dict):
            self = RoutingData.RoutingEvent()
            self.vehicle_id = data["Vehicle_name"]
            self.vehicle_model = self.vehicle_id.split(" ")[0]
            self.event = data["event"]
            self.time = data["time"]
            self.location = data["location"]
            return self


    class RoutingVehicle:
        vehicle_id = ""
        model = ""
        moves = []

        def __init__(self, vehicle_id: str, model: str):
            self.vehicle_id = vehicle_id
            self.model = model
            self.moves = []

        def __str__(self):
            return "%s (%s) with %d moves" % (self.vehicle_id, self.model, len(self.moves))

        def insert_move(self, time: float, location: str):
            i = 0
            for m in self.moves:
                if m[0] >= time:
                    break
                i += 1
            self.moves.insert(i, (time, location))




class CargoData:
    def __init__(self):
        self.init = {}
        self.levels = {}

    @staticmethod
    def from_pickle(file: str):
        with open("movement_log.pkl", "rb") as f:
            data = pickle.load(f)
        # log = CargoData.EventLog()
        events = {}

        for d in data:
            if d["Cargo"] == "empty":
                continue
            if d["event"] == "taking off" or d["event"] == "arriving":
                # log.add_event(d)
                event = CargoData.Event(d)
                if event.location in events:
                    events[event.location].append(event)
                else:
                    events[event.location] = [event]

        ret = CargoData()
        # Get starting levels for nodes
        ret.init = {}
        for node in events:
            current = {"PAX": 0, "cargo": 0}
            minimum = {"PAX": 0, "cargo": 0}
            for e in events[node]:
                if e.move_type == "arriving":
                    current[e.cargo_type] += e.quantity
                elif e.move_type == "taking off":
                    current[e.cargo_type] -= e.quantity
                else:
                    raise ValueError("Unknown move type '%s'" % (e.move_type))
                if current[e.cargo_type] < minimum[e.cargo_type]:
                    minimum[e.cargo_type] = current[e.cargo_type]
            ret.init[node] = {}
            for t in minimum:
                ret.init[node][t] = -1 * minimum[t]
        # Calculate levels over time
        ret.levels = {}
        for node in events:
            ret.levels[node] = []
            current = ret.init[node]
            for e in events[node]:
                if e.move_type == "arriving":
                    current[e.cargo_type] += e.quantity
                elif e.move_type == "taking off":
                    current[e.cargo_type] -= e.quantity
                else:
                    raise ValueError("Unknown move type '%s'" % (e.move_type))
                ret.levels[node].append(CargoData.CargoLevels(e.time, current))
        return ret

    class CargoLevels:
        def __init__(self, time, levels):
            self.time = time
            self.levels = levels["PAX"]

    class Event:
        def __init__(self, log):
            self.time = log["time"]
            self.location = log["location"].split("_")[0]
            self.move_type = log["event"]
            self.cargo_type = log["Cargo"][0]["c_type"]
            self.quantity = log["Cargo"][0]["cargo_moved"]

        def __str__(self):
            return "%02.3f %s %s [%s %s]" % (self.time, self.location, self.move_type, self.cargo_type, self.quantity)
