import csv
import re


MOVE_REGEX = re.compile("leaving from [ a-zA-Z]+; (driv|sail|mov|fly)ing to [ a-zA-Z]+")
ARRIVE_REGEX = re.compile("arriving at [ a-zA-Z]+")


class BasesData:
    def __init__(self):
        self.bases = []

    def __str__(self):
        fin = ""
        for b in self.bases:
            fin += str(b) + "\n"
        return fin[:-1]

    # Make iterable
    def __iter__(self):
        self.iter = self.bases.__iter__()
        return self.iter
    def __next__(self):
        return self.iter.__next__()

    @staticmethod
    def from_csv(filename: str):
        self = BasesData()
        with open(filename, newline='') as csvfile:
            csvreader = csv.reader(csvfile, dialect='excel')
            row_i = 1
            for row in csvreader:
                # Check header row
                if row_i == 1:
                    row_i += 1
                    if row[1] != "base name":
                        print(row)
                        raise ValueError("BasesData: CSV Header Invalid")
                    continue
                self.bases.append(self.Base.from_csv(row))
                row_i += 1
        return self

    class Base:
        name = ""
        lat = -365
        lon = -365

        def __str__(self):
            return "%s (%02.2f, %02.2f)" % (self.name, self.lat, self.lon)

        @staticmethod
        def from_csv(row: list[str]):
            self = BasesData.Base()
            self.name = row[1]
            self.lat = float(row[2])
            self.lon = float(row[3])
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
    def from_csv(filename: str):
        self = RoutingData()
        with open(filename, newline='') as csvfile:
            csvreader = csv.reader(csvfile, dialect='excel')
            row_i = 1
            for row in csvreader:
                # Check header row
                if row_i == 1:
                    row_i += 1
                    if row[1] != "vehicle id":
                        print(row)
                        raise ValueError("RoutingData: CSV Header Invalid")
                    continue
                self.event_log.append(self.RoutingEvent.from_csv(row))
                row_i += 1
        return self

    def get_legs(self) -> list[tuple[str, str]]:
        ret = []
        for e in self.event_log:
            if MOVE_REGEX.match(e.event):
                start = e.event.split(";")[0][13:]
                i = 0
                spaces = 0
                for c in e.event.split(";")[1]:
                    if c == " ":
                        spaces += 1
                    i += 1
                    if spaces == 3:
                        break
                end = e.event.split(";")[1][i:]
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
