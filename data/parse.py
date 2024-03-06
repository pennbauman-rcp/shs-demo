import sys
import csv
import re
import pandas as pd


MOVE_REGEX = re.compile("[Ll]eaving from [-_ a-zA-Z]+, (driv|sail|mov|fly|go)ing to [-_ a-zA-Z]+")
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
    def from_csv(filename: str, verbose: bool = False):
        if verbose:
            print("Reading locations from CSV (%s)" % filename)
        self = LocationsData()
        with open(filename, newline='') as csvfile:
            csvreader = csv.reader(csvfile, dialect='excel')
            row_i = 1
            for row in csvreader:
                # Check header row
                if row_i == 1:
                    row_i += 1
                    if row[0] != "ICAO":
                        print("ERROR: Invalid CSV header for locations")
                        print(row)
                        sys.exit(1)
                    continue
                self.nodes.append(self.Node.from_csv(row))
                row_i += 1
        return self

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
    def from_csv(filename: str, verbose: bool = False):
        if verbose:
            print("Reading mission log from CSV (%s)" % filename)
        self = RoutingData()
        with open(filename, newline='') as csvfile:
            csvreader = csv.reader(csvfile, dialect='excel')
            row_i = 1
            for row in csvreader:
                # Check header row
                if row_i == 1:
                    row_i += 1
                    if row[1] != "vehicle id":
                        print("ERROR: Invalid CSV header for mission log")
                        print(row)
                        sys.exit(1)
                    continue
                self.event_log.append(self.RoutingEvent.from_csv(row))
                row_i += 1
        return self

    def get_legs(self) -> list[tuple[str, str]]:
        ret = []
        for e in self.event_log:
            if MOVE_REGEX.match(e.event):
                start = e.event.split(",")[0][13:]
                i = 0
                spaces = 0
                for c in e.event.split(",")[1]:
                    if c == " ":
                        spaces += 1
                    i += 1
                    if spaces == 3:
                        break
                end = e.event.split(",")[1][i:]
                ret.append((start, end))
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
        def from_csv(row: list[str]):
            self = RoutingData.RoutingEvent()
            self.vehicle_id = row[1]
            self.vehicle_model = row[2]
            self.event = row[3]
            self.time = float(row[4])
            self.location = row[5]
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
