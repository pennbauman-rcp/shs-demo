import sys
import re
import tkinter
from tkinter import ttk

from csvdata import *


MAP_FILE_FMT = "files/equirectangular_earth_map_%04dx%04d.png"
MAP_SCALES = [
    # px_width, px_width, node_radius, line_width, vehicle_radius
    (7200, 3600, 12, 8, 20),
    (3600, 1800,  6, 4, 10),
    (1800,  900,  3, 2,  5),
]
NODE_COLOR = "black"
AIRPLANE_REGEX = re.compile("^(plane|C17|B777)$")
SHIP_REGEX = re.compile("^(ship|LMSR)$")
TRUCK_REGEX = re.compile("^(truck|[Tt]ruck_(US|EU))$")
TRAIN_REGEX = re.compile("^(train|[Tt]rain_(US|EU))$")


# Main map window, contains all map elements
class WorldMap:
    nodes = []
    legs = []
    vehicles = []
    tk = None
    canvas = None
    bg_img = None
    time = 0.0
    end_time = 0.0
    paused = False
    speed = 1

    def __init__(self, nodes: LocationsData = None, routing: RoutingData = None):
        self.coord = WorldCoordinates()
        if nodes:
            self.nodes = []
            for n in nodes:
                self.nodes.append(MapNode(n.name, n.lat, n.lon))
        if routing:
            self.legs = []
            for l in routing.get_legs():
                self.legs.append(MapLeg(l[0], l[1]))
            self.vehicles = []
            for v in routing.get_vehicles():
                self.vehicles.append(MapVehicle(v.vehicle_id, v.model, v.moves))
            self.end_time = routing.get_end_time()

    # Crop in map to show 1/4 of earth
    def crop(self, min_lat: int, min_lon: int):
        self.coord = WorldCoordinates(min_lat, min_lon, 2)
        # print("Cropping world to", self.coord)

    # Get pixel location of a node by name
    def get_node_px(self, name: str) -> tuple[int, int]:
        for n in self.nodes:
            if name.split("_")[0] == n.name:
                n.unhide(self)
                return self.coord.calc_px(n.lat, n.lon)
        raise ValueError("Unknown node '%s'" % (name))

    # Run map display window
    def run(self, speed: int, verbose: bool = False):
        self.verbose = verbose
        if speed > 20:
            if speed > 100:
                print("ERROR: High speed '%s'" % speed)
                sys.exit(1)
            print("WARNING: High speed '%s'" % speed)
        self.speed = speed

        self.tk = tkinter.Tk()
        self.tk.title("SHS Demo")
        self.tk.configure(bg="black")
        self.tk.grid()
        self.coord.set_px(self.tk.winfo_screenwidth(), self.tk.winfo_screenheight())
        self.tk.minsize(self.coord.px_width, self.coord.px_height)
        # print("Displaying World, (0, 0) is", self.coord.calc_px(0, 0))

        # Create toolbar
        self.toolbar = ttk.Frame(self.tk, padding=0)
        self.toolbar.grid()
        self.toolbar.grid(column=0, row=0)
        ttk.Button(self.toolbar, text="Quit", command=self.tk.destroy).grid(column=0, row=0)
        ttk.Button(self.toolbar, text="Pause", command=self.pause).grid(column=1, row=0)
        ttk.Button(self.toolbar, text="1x Speed", command=lambda: self.set_speed(1)).grid(column=2, row=0)
        ttk.Button(self.toolbar, text="2x Speed", command=lambda: self.set_speed(2)).grid(column=3, row=0)
        ttk.Button(self.toolbar, text="4x Speed", command=lambda: self.set_speed(4)).grid(column=4, row=0)
        ttk.Button(self.toolbar, text="8x Speed", command=lambda: self.set_speed(8)).grid(column=5, row=0)
        ttk.Button(self.toolbar, text="16x Speed", command=lambda: self.set_speed(16)).grid(column=6, row=0)


        # Setup canvas with background
        self.canvas = tkinter.Canvas(self.tk, bg="black", height=self.coord.px_height, width=self.coord.px_width, confine=False)
        self.canvas.grid(column=0, row=1)
        img_width = self.coord.px_width * self.coord.zoom
        img_height = self.coord.px_height * self.coord.zoom
        bg_img_file = MAP_FILE_FMT % (img_width, img_height)
        self.bg_img = tkinter.PhotoImage(file=bg_img_file)
        self.canvas.create_image(self.coord.calc_world_offset_px(), image=self.bg_img, anchor=tkinter.NW)
        if verbose:
            center_lat = self.coord.min_lat + (self.coord.max_lat - self.coord.min_lat)/2
            center_lon = self.coord.min_lon + (self.coord.max_lon - self.coord.min_lon)/2
            print("Cropping map to center on (%d, %d)" % (center_lat, center_lon))

        # Setup overlay items
        node_count = 0
        for n in self.nodes:
            try:
                n.display(self)
                if len(self.legs) > 0:
                    n.hide(self)
                node_count += 1
            except:
                pass
        if verbose:
            print("Nodes displayed (%d)" % node_count)
        for l in self.legs:
            l.display(self)
        if verbose:
            print("Legs displayed (%d)" % len(self.legs))

        # Setup vehicles
        for v in self.vehicles:
            v.display(self)
        if verbose:
            print("Vehicles displayed (%d)" % len(self.vehicles))

        # Add map decorations
        self.clock = WorldClock()
        self.clock.display(self)
        self.key = VehicleKey()
        self.key.display(self)

        # Run animation
        self.tk.after(0, self.step)
        if verbose:
            print("Running animation (T0 to T%.3f)" % (self.end_time))
        self.tk.mainloop()
        if self.verbose:
            if self.time < self.end_time:
                print("Ended animation (T%.3f)" % self.time)

    # Step animation
    def step(self):
        if self.paused:
            self.tk.after(10, self.step)
            return
        for v in self.vehicles:
            v.step(self)
        self.clock.step(self)

        self.time += 0.05 * self.speed
        if self.time <= self.end_time:
            self.tk.after(10, self.step)
        else:
            if self.verbose:
                print("Finished animation (T%.3f)" % self.time)

    def pause(self):
        self.paused = True

    def set_speed(self, speed: int):
        self.paused = False
        self.speed = speed


# Latitude/Longitude to Pixel converter class
class WorldCoordinates:
    min_lat = -90
    min_lon = -180
    max_lat = 90
    max_lon = 180
    zoom = 1
    px_width = None
    px_height = None
    node_radius = 3
    vehicle_radius = 5
    line_width = 2

    def __init__(self, min_lat: int = -90, min_lon: int = -180, zoom: int = 1):
        if min_lat < self.min_lat:
            raise ValueError("Latitude cannot go below %d" % (self.min_lat))
        if min_lon < self.min_lon:
            raise ValueError("Longitude cannot go below %d" % (self.min_lon))
        max_lat = min_lat + (180/zoom)
        max_lon = min_lon + (360/zoom)
        if max_lat > self.max_lat:
            raise ValueError("Latitude cannot go above %d" % (self.max_lat))
        if max_lon > self.max_lon:
            raise ValueError("Longitude cannot go above %d" % (self.max_lon))
        self.min_lat = min_lat
        self.min_lon = min_lon
        self.max_lat = max_lat
        self.max_lon = max_lon
        self.zoom = zoom

    def __str__(self):
        if not (self.px_width and self.px_height):
            return "Coord[(%d, %d) (%d, %d)]" % (self.min_lat, self.min_lon, self.max_lat, self.max_lon)
        else:
            return "Coord[(%d, %d) (%d, %d) %dx%d]" % (self.min_lat, self.min_lon, self.max_lat, self.max_lon, self.px_width, self.px_height)

    def set_px(self, max_width: int, max_height: int):
        for scale in MAP_SCALES:
            if (scale[0] < max_width) and (scale[1] < max_height):
                self.px_width = scale[0]
                self.px_height = scale[1]
                self.node_radius = scale[2]
                self.line_width = scale[3]
                self.vehicle_radius = scale[4]
                return
        raise ValueError("Unsupported screen resolution %dx%d" % (max_width, max_height))

    # Calculate pixel coordinates from latitude/longitude
    def calc_px(self, lat: float, lon: float) -> tuple[int, int]:
        if not (self.px_width and self.px_height):
            raise ValueError("Pixels must be set before they can be calculated")
        if lat < self.min_lat:
            raise ValueError("Latitude below mimumum")
        if lon < self.min_lon:
            raise ValueError("Longitude below mimumum")
        if lat > self.max_lat:
            raise ValueError("Latitude above maximum")
        if lon > self.max_lon:
            raise ValueError("Longitude above maximum")
        x = (lon - self.min_lon) * self.px_width / (self.max_lon - self.min_lon)
        y = (lat - self.min_lat) * self.px_height / (self.max_lat - self.min_lat)
        y = self.px_height - y
        return (int(x), int(y))

    # Calculate overset for world map background
    def calc_world_offset_px(self) -> tuple[int, int]:
        if not (self.px_width and self.px_height):
            raise ValueError("Pixels must be set before they can be calculated")
        x = (-180 - self.min_lon) * self.px_width / (self.max_lon - self.min_lon)
        y = (90 - self.min_lat) * self.px_height / (self.max_lat - self.min_lat)
        y = self.px_height - y
        return (x, y)

    def calc_percent_px(self, lat_percent: float, lon_percent: float) -> tuple[int, int]:
        if not (self.px_width and self.px_height):
            raise ValueError("Pixels must be set before they can be calculated")
        x = (self.px_width * lat_percent) / 100
        y = (self.px_height * lon_percent) / 100
        return (int(x), int(y))


# Clock for the corner of the map
class WorldClock:
    def display(self, world: WorldMap):
        x, y = world.coord.calc_percent_px(99, 98)
        self.canvas_text = world.canvas.create_text(x, y, fill=NODE_COLOR, text="T%.3f" % 0.0, anchor=tkinter.SE)

    def step(self, world: WorldMap):
        world.canvas.itemconfig(self.canvas_text, text="T%.3f" % world.time)


class VehicleKind:
    def __init__(self, model: str):
        if AIRPLANE_REGEX.match(model):
            self.name = "Airplane"
            self.color = "orange"
        elif SHIP_REGEX.match(model):
            self.name = "Ship"
            self.color = "red"
        elif TRUCK_REGEX.match(model):
            self.name = "Truck"
            self.color = "green"
        elif TRAIN_REGEX.match(model):
            self.name = "Train"
            self.color = "purple"
        else:
            raise ValueError("Unknown model '%s'" % model)

# On map key for vehicle types
class VehicleKey:
    def display(self, world: WorldMap):
        vehicles = [VehicleKind("truck"), VehicleKind("train"), VehicleKind("ship"), VehicleKind("plane")]
        self.canvas_dots = [None] * 4
        self.canvas_texts = [None] * 4
        for i in range(0, 4):
            x, y = world.coord.calc_percent_px(1, 98 - 2*i)
            p1 = (x - world.coord.vehicle_radius, y - world.coord.vehicle_radius)
            p2 = (x + world.coord.vehicle_radius, y + world.coord.vehicle_radius)
            self.canvas_dots[i] = world.canvas.create_oval(p1, p2, fill=vehicles[i].color, outline=vehicles[i].color)
            self.canvas_texts[i] = world.canvas.create_text(x + world.coord.vehicle_radius * 3, y, fill=NODE_COLOR, text=vehicles[i].name, anchor=tkinter.W)



# Single location node; with data and canvas object
class MapNode:
    name = ""
    lat = 0
    lon = 0
    canvas_dot = None

    def __init__(self, name: str, lat: int, lon: int):
        self.name = name
        self.lat = lat
        self.lon = lon

    def display(self, world: WorldMap):
        (x, y) = world.coord.calc_px(self.lat, self.lon)
        p1 = (x - world.coord.node_radius, y - world.coord.node_radius)
        p2 = (x + world.coord.node_radius, y + world.coord.node_radius)
        self.canvas_dot = world.canvas.create_oval(p1, p2, fill=NODE_COLOR, outline=NODE_COLOR)

    def hide(self, world: WorldMap):
        world.canvas.itemconfig(self.canvas_dot, state="hidden")
    def unhide(self, world: WorldMap):
        world.canvas.itemconfig(self.canvas_dot, state="normal")


# Single travel leg; with start node, end node, and canvas object
class MapLeg:
    start_node = ""
    end_node = ""
    canvas_line = None

    def __init__(self, start_node: str, end_node: str):
        self.start_node = start_node
        self.end_node = end_node

    def display(self, world: WorldMap):
        p1 = world.get_node_px(self.start_node)
        p2 = world.get_node_px(self.end_node)
        self.canvas_line = world.canvas.create_line(p1, p2, fill=NODE_COLOR, width=world.coord.line_width)


# Single vehicle; with model, movement over time, and canvas object
class MapVehicle:
    vehicle_id = ""
    model = ""
    moves = [] # (time: float, loc: str)
    canvas_icon = None

    def __init__(self, vehicle_id: str, model: str, moves: list[tuple[float, str]]):
        self.vehicle_id = vehicle_id
        self.model = model
        self.moves = moves
        self.kind = VehicleKind(model)

    # Calculate index of move at give time
    def _index_at_time(self, time: float) -> int:
        if time < self.moves[0][0]:
            return -1
        if time >= self.moves[-1][0]:
            return len(self.moves) - 1
        i = 0
        while i < len(self.moves) - 1:
            if time == self.moves[i][0]:
                break
            if time > self.moves[i][0] and time < self.moves[i + 1][0]:
                break
            i += 1
        return i

    # Get vehicle location at a given time, return None if vehicle is out of use
    def get_location_at(self, time: float, world: WorldMap) -> tuple[int, int]:
        index = self._index_at_time(time)
        # Check if vehicle is before or after its moves
        if index == -1:
            return world.get_node_px(self.moves[0][1])
        if index == len(self.moves) - 1:
            return world.get_node_px(self.moves[-1][1])
        # Check if vehicle isn't moving
        p1 = world.get_node_px(self.moves[index][1])
        if self.moves[index][0] == self.moves[index + 1][0]:
            return p1
        if self.moves[index][1] == self.moves[index + 1][1]:
            return p1
        p2 = world.get_node_px(self.moves[index + 1][1])
        # Calculate postion between start and end points
        ratio = (time - self.moves[index][0])/(self.moves[index + 1][0] - self.moves[index][0])
        x = int(p1[0] + (p2[0] - p1[0])*ratio)
        y = int(p1[1] + (p2[1] - p1[1])*ratio)
        # print("T%4.1f: %f (%f, %f)" %(time, ratio, self.moves[i][0], self.moves[i + 1][0]))
        return (x, y)


    # Show on canvas if vehicle exists at time 0
    def display(self, world: WorldMap):
        loc = self.get_location_at(0.0, world)
        if loc:
            (x, y) = loc
            p1 = (x - world.coord.vehicle_radius, y - world.coord.vehicle_radius)
            p2 = (x + world.coord.vehicle_radius, y + world.coord.vehicle_radius)
            self.canvas_icon = world.canvas.create_oval(p1, p2, fill=self.kind.color, outline=self.kind.color)

    # Update vehicle on canvas for current time
    def step(self, world: WorldMap):
        loc = self.get_location_at(world.time, world)
        if loc:
            (x, y) = loc
            p1 = (x - world.coord.vehicle_radius, y - world.coord.vehicle_radius)
            p2 = (x + world.coord.vehicle_radius, y + world.coord.vehicle_radius)
            world.canvas.delete(self.canvas_icon)
            self.canvas_icon = world.canvas.create_oval(p1, p2, fill=self.kind.color, outline=self.kind.color)
        else:
            world.canvas.delete(self.canvas_icon)
