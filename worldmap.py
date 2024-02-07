import re
import tkinter

from csvdata import *


MAP_FILE_FMT = "files/equirectangular_earth_map_%04dx%04d.png"
MAP_SCALES = [
    (7200, 3600),
    (3600, 1800),
    (1800,  900),
]
BASE_RADIUS = 3
VEHICLE_RADIUS = 5
LINE_WIDTH = 2
AIRPLANE_REGEX = re.compile("^(C17|B777)$")
SHIP_REGEX = re.compile("^(LMSR)$")
TRUCK_REGEX = re.compile("^([Tt]ruck_(US|EU))$")
TRAIN_REGEX = re.compile("^([Tt]rain_(US|EU))$")


# Main map window, contains all map elements
class WorldMap:
    bases = []
    legs = []
    vehicles = []
    tk = None
    canvas = None
    bg_img = None
    time = 0.0
    end_time = 0.0

    def __init__(self, bases: BasesData = None, routing: RoutingData = None):
        self.coord = WorldCoordinates()
        if bases:
            self.bases = []
            for b in bases:
                self.bases.append(MapBase(b.name, b.lat, b.lon))
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

    # Get pixel location of a base by name
    def get_base_px(self, name: str) -> tuple[int, int]:
        for b in self.bases:
            if name.split("_")[0] == b.name:
                b.unhide(self)
                return self.coord.calc_px(b.lat, b.lon)
        raise ValueError("Unknown base '%s'" % (name))

    # Run map display window
    def display(self):
        self.tk = tkinter.Tk()
        self.tk.title("SHS Demo")
        self.tk.configure(bg="black")
        self.coord.set_px(self.tk.winfo_screenwidth(), self.tk.winfo_screenheight())
        self.tk.minsize(self.coord.px_width, self.coord.px_height)
        # print("Displaying World, (0, 0) is", self.coord.calc_px(0, 0))

        # Setup canvas with background
        self.canvas = tkinter.Canvas(self.tk, bg="black", height=self.coord.px_height, width=self.coord.px_width, confine=False)
        img_width = self.coord.px_width * self.coord.zoom
        img_height = self.coord.px_height * self.coord.zoom
        bg_img_file = MAP_FILE_FMT % (img_width, img_height)
        self.bg_img = tkinter.PhotoImage(file=bg_img_file)
        self.canvas.create_image(self.coord.calc_world_offset_px(), image=self.bg_img, anchor=tkinter.NW)

        # Setup overlay items
        base_count = 0
        for b in self.bases:
            try:
                b.display(self)
                b.hide(self)
                base_count += 1
            except:
                pass
        print("Bases displayed (%d)" % base_count)
        for l in self.legs:
            l.display(self)
        print("Legs displayed (%d)" % len(self.legs))

        # Setup vehicles
        for v in self.vehicles:
            v.display(self)
        print("Vehicles displayed (%d)" % len(self.vehicles))

        self.clock = WorldClock()
        self.clock.display(self)

        # Run animation
        self.canvas.pack()
        self.tk.after(20, self.step)
        print("Running animation (T0 to T%f)" % (self.end_time))
        self.tk.mainloop()
        print("Ended animation T%f" % self.time)

    # Step animation
    def step(self):
        self.time += 0.05
        for v in self.vehicles:
            v.step(self)
        self.clock.step(self)
        if self.time < self.end_time:
            self.tk.after(10, self.step)



# Latitude/Longitude to Pixel converter class
class WorldCoordinates:
    min_lat = -90
    min_lon = -180
    max_lat = 90
    max_lon = 180
    zoom = 1
    px_width = None
    px_height = None

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


# Clock for the corner of the map
class WorldClock:
    def display(self, world: WorldMap):
        lat = world.coord.min_lat + (world.coord.max_lat - world.coord.min_lat)/36
        lon = world.coord.max_lon - (world.coord.max_lat - world.coord.min_lat)/24
        self.x, self.y = world.coord.calc_px(lat, lon)
        self.canvas_text = world.canvas.create_text(self.x, self.y, text="T%.3f" % 0.0)

    def step(self, world: WorldMap):
        world.canvas.delete(self.canvas_text)
        self.canvas_text = world.canvas.create_text(self.x, self.y, text="T%.3f" % world.time)



# Single base; with data and canvas object
class MapBase:
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
        p1 = (x - BASE_RADIUS, y - BASE_RADIUS)
        p2 = (x + BASE_RADIUS, y + BASE_RADIUS)
        self.canvas_dot = world.canvas.create_oval(p1, p2, fill="black", outline="black")

    def hide(self, world: WorldMap):
        world.canvas.itemconfig(self.canvas_dot, state="hidden")
    def unhide(self, world: WorldMap):
        world.canvas.itemconfig(self.canvas_dot, state="normal")


# Single travel leg; with start base, end base, and canvas object
class MapLeg:
    start_base = ""
    end_base = ""
    canvas_line = None

    def __init__(self, start_base: str, end_base: str):
        self.start_base = start_base
        self.end_base = end_base

    def display(self, world: WorldMap):
        p1 = world.get_base_px(self.start_base)
        p2 = world.get_base_px(self.end_base)
        self.canvas_line = world.canvas.create_line(p1, p2, fill="black", width=LINE_WIDTH)


# Single vehicle; with model, movement over time, and canvas object
class MapVehicle:
    vehicle_id = ""
    model = ""
    moves = []
    canvas_icon = None

    def __init__(self, vehicle_id: str, model: str, moves: list[tuple[float, str]]):
        self.vehicle_id = vehicle_id
        self.model = model
        self.moves = moves
        if AIRPLANE_REGEX.match(model):
            self.color = "orange"
        elif SHIP_REGEX.match(model):
            self.color = "red"
        elif TRUCK_REGEX.match(model):
            self.color = "green"
        elif TRAIN_REGEX.match(model):
            self.color = "purple"
        else:
            raise ValueError("Unknown model '%s'" % model)

    # Get vehicle location at a given time, return None if vehicle is out of use
    def get_location_at(self, time: float, world: WorldMap) -> tuple[int, int]:
        # Check if vehicle should be hidden
        if time < self.moves[0][0]:
            return None
        if time > self.moves[-1][0]:
            # Show ending vehicles forever
            if self.moves[-1][0] == world.end_time:
                return world.get_base_px(self.moves[-1][1])
            return None
        if time == self.moves[-1][0]:
            return world.get_base_px(self.moves[-1][1])
        # Fine current time with moves list
        i = 0
        while i < len(self.moves) - 1:
            if time == self.moves[i][0]:
                return world.get_base_px(self.moves[i][1])
            if time > self.moves[i][0] and time < self.moves[i + 1][0]:
                break
            i += 1
        p1 = world.get_base_px(self.moves[i][1])
        # Check if vehicle isn't moving
        if self.moves[i][0] == self.moves[i + 1][0]:
            return p1
        if self.moves[i][1] == self.moves[i + 1][1]:
            return p1
        p2 = world.get_base_px(self.moves[i + 1][1])
        # Calculate postion between start and end points
        ratio = (time - self.moves[i][0])/(self.moves[i + 1][0] - self.moves[i][0])
        x = int(p1[0] + (p2[0] - p1[0])*ratio)
        y = int(p1[1] + (p2[1] - p1[1])*ratio)
        # print("T%4.1f: %f (%f, %f)" %(time, ratio, self.moves[i][0], self.moves[i + 1][0]))
        return (x, y)


    # Show on canvas if vehicle exists at time 0
    def display(self, world: WorldMap):
        loc = self.get_location_at(0.0, world)
        if loc:
            (x, y) = loc
            p1 = (x - VEHICLE_RADIUS, y - VEHICLE_RADIUS)
            p2 = (x + VEHICLE_RADIUS, y + VEHICLE_RADIUS)
            self.canvas_icon = world.canvas.create_oval(p1, p2, fill=self.color, outline=self.color)

    # Update vehicle on canvas for current time
    def step(self, world: WorldMap):
        loc = self.get_location_at(world.time, world)
        if loc:
            (x, y) = loc
            p1 = (x - VEHICLE_RADIUS, y - VEHICLE_RADIUS)
            p2 = (x + VEHICLE_RADIUS, y + VEHICLE_RADIUS)
            world.canvas.delete(self.canvas_icon)
            self.canvas_icon = world.canvas.create_oval(p1, p2, fill=self.color, outline=self.color)
        else:
            world.canvas.delete(self.canvas_icon)
