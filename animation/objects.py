import re
import tkinter
from tkinter import ttk
from tkinter import font

from animation.canvas import MapCanvas, ICON_SIZE


AIRPLANE_REGEX = re.compile("^(plane|C17|B777)$")
SHIP_REGEX = re.compile("^(ship|LMSR)$")
TRUCK_REGEX = re.compile("^(truck|[Tt]ruck_(US|EU))$")
TRAIN_REGEX = re.compile("^(train|[Tt]rain_(US|EU))$")


# Single location node; with data and canvas object
class MapNode:
    name = ""
    lat = 0
    lon = 0
    canvas_dot = None

    def __init__(self, name: str, lat: float, lon: float):
        self.name = name
        self.lat = lat
        self.lon = lon

    def display(self, world: MapCanvas):
        (x, y) = world.coord.calc_px(self.lat, self.lon)
        p1 = (x - world.style.node_radius, y - world.style.node_radius)
        p2 = (x + world.style.node_radius, y + world.style.node_radius)
        self.canvas_dot = world.canvas.create_oval(p1, p2, fill=world.style.text, outline=world.style.text)

    def hide(self, world: MapCanvas):
        world.canvas.itemconfig(self.canvas_dot, state="hidden")
    def unhide(self, world: MapCanvas):
        world.canvas.itemconfig(self.canvas_dot, state="normal")


# Single travel leg; with start node, end node, and canvas object
class MapLeg:
    start_node = ""
    end_node = ""
    canvas_line = None

    def __init__(self, start_node: str, end_node: str):
        self.start_node = start_node
        self.end_node = end_node

    def display(self, canvas: MapCanvas):
        p1 = canvas.get_named_px(self.start_node)
        p2 = canvas.get_named_px(self.end_node)
        self.canvas_line = canvas.canvas.create_line(p1, p2, fill=canvas.style.text, width=canvas.style.line_width)


# Single vehicle; with model, movement over time, and canvas object
class MapVehicle:
    vehicle_id = ""
    model = ""
    moves = [] # (time: float, loc: str)
    icon_img = None
    canvas_icon = None
    cached_time_index = -9
    cached_px_index = -9
    cached_usage_index = -9
    current_loc = None

    def __init__(self, vehicle_id: str, model: str, moves: list[tuple[float, str]]):
        self.vehicle_id = vehicle_id
        self.model = model
        self.moves = moves
        if AIRPLANE_REGEX.match(model):
            self.kind = "Airplane"
        elif SHIP_REGEX.match(model):
            self.kind = "Ship"
        elif TRUCK_REGEX.match(model):
            self.kind = "Truck"
        elif TRAIN_REGEX.match(model):
            self.kind = "Train"
        else:
            raise ValueError("Unknown model '%s'" % model)

    # Calculate index of move at give time
    def _index_at_time(self, time: float) -> int:
        if time < self.moves[0][0]:
            return -1
        if time >= self.moves[-1][0]:
            return len(self.moves) - 1
        if self.cached_time_index > 0:
            if time > self.moves[self.cached_time_index][0]:
                if time < self.moves[self.cached_time_index + 1][0]:
                    return self.cached_time_index
        i = 0
        while i < len(self.moves) - 1:
            if time == self.moves[i][0]:
                break
            if time > self.moves[i][0] and time < self.moves[i + 1][0]:
                break
            i += 1
        return i

    # Get vehicle location at a given time, return None if vehicle is out of use
    def get_location_at(self, time: float, world: MapCanvas) -> tuple[int, int]:
        index = self._index_at_time(time)
        if index == self.cached_px_index:
            return self.cached_px
        # Check if vehicle is before or after its moves
        if index == -1:
            ret = world.get_named_px(self.moves[0][1])
            self.cached_px_index = index
            self.cached_px = ret
            return ret
        if index == len(self.moves) - 1:
            ret = world.get_named_px(self.moves[-1][1])
            self.cached_px_index = index
            self.cached_px = ret
            return ret
        # Check if vehicle isn't moving
        p1 = world.get_named_px(self.moves[index][1])
        if self.moves[index][1] == self.moves[index + 1][1]:
            self.cached_px_index = index
            self.cached_px = p1
            return p1
        self.cached_px_index = -2
        p2 = world.get_named_px(self.moves[index + 1][1])
        # Calculate postion between start and end points
        ratio = (time - self.moves[index][0])/(self.moves[index + 1][0] - self.moves[index][0])
        x = int(p1[0] + (p2[0] - p1[0])*ratio)
        y = int(p1[1] + (p2[1] - p1[1])*ratio)
        # print("T%4.1f: %f (%f, %f)" %(time, ratio, self.moves[i][0], self.moves[i + 1][0]))
        return (x, y)

    # Get what a vehicle is doing at a given time
    def get_usage_at(self, time: float) -> str:
        index = self._index_at_time(time)
        # Check if vehicle hasn't moved
        if index == self.cached_usage_index:
            return self.cached_usage
        if index == -1:
            self.cached_usage_index = index
            self.cached_usage = "Loading"
            return "Loading"
        # Check if vehicle is finished
        if index == len(self.moves) - 1:
            self.cached_usage_index = index
            self.cached_usage = "Done"
            return "Done"
        # Check if vehicle isn't moving (loading)
        if self.moves[index][1] == self.moves[index + 1][1]:
            self.cached_usage_index = index
            self.cached_usage = "Loading"
            return "Loading"
        # Vehicle must be moving
        self.cached_usage_index = index
        self.cached_usage = "Moving"
        return "Moving"

    def draw_img(self, loc):
        self.canvas_icon = self.canvas.canvas.create_image(loc, image=self.icon_img)

    def draw_dot(self, loc):
        (x, y) = loc
        p1 = (x - self.canvas.style.vehicle_radius, y - self.canvas.style.vehicle_radius)
        p2 = (x + self.canvas.style.vehicle_radius, y + self.canvas.style.vehicle_radius)
        color = self.canvas.style.vehicles[self.kind]
        self.canvas_icon = self.canvas.canvas.create_oval(p1, p2, fill=color, outline=color)


    # Show on canvas if vehicle exists at time 0
    def display(self, canvas: MapCanvas):
        self.canvas = canvas
        if self.canvas.style.icons:
            if not self.icon_img:
                self.icon_img = tkinter.PhotoImage(file=self.canvas.style.get_icon_file(self.kind))
            self.draw = self.draw_img
        else:
            self.draw = self.draw_dot

        loc = self.get_location_at(0, canvas)
        self.current_loc = loc
        if loc:
            self.draw(loc)

    # Update vehicle on canvas for current time
    def step(self, world: MapCanvas, time: float):
        loc = self.get_location_at(time, world)
        if loc == self.current_loc:
            return
        self.current_loc = loc
        self.canvas.canvas.delete(self.canvas_icon)
        if loc:
            self.draw(loc)
