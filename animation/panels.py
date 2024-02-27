import tkinter
from tkinter import ttk
from tkinter import font

from animation.canvas import MapCanvas
from animation.objects import ICON_SIZE


# Clock for the corner of the map
class WorldClock:
    def display(self, world: MapCanvas):
        x, y = world.coord.calc_percent_px(99, 98)
        self.canvas_text = world.canvas.create_text(x, y, fill=world.style.text, text="T%.3f" % 0.0, anchor=tkinter.SE)

    def step(self, world: MapCanvas, time: float):
        world.canvas.itemconfig(self.canvas_text, text="T%.3f" % time)



# On map key for vehicle types
class VehicleKey:
    def display(self, world: MapCanvas):
        vehicles = ["Airplane", "Ship", "Train", "Truck"]
        self.icon_images = [None] * 4
        self.canvas_icons = [None] * 4
        self.canvas_texts = [None] * 4
        for i in range(0, 4):
            if world.style.icons:
                x, y = world.coord.calc_percent_px(1 + 0.5*ICON_SIZE, 92 - 4*ICON_SIZE + (2 + ICON_SIZE)*i)
                self.icon_images[i] = tkinter.PhotoImage(file=world.style.get_icon_file(vehicles[i]))
                self.canvas_icons[i] = world.canvas.create_image(x, y, image=self.icon_images[i])
                self.canvas_texts[i] = world.canvas.create_text(x + world.style.vehicle_radius * (2 + 2*ICON_SIZE), y, fill=world.style.text, text=vehicles[i], anchor=tkinter.W)
            else:
                x, y = world.coord.calc_percent_px(1, 92 + 2*i)
                p1 = (x - world.style.vehicle_radius, y - world.style.vehicle_radius)
                p2 = (x + world.style.vehicle_radius, y + world.style.vehicle_radius)
                color = world.style.vehicles[vehicles[i]]
                self.canvas_icons[i] = world.canvas.create_oval(p1, p2, fill=color, outline=color)
                self.canvas_texts[i] = world.canvas.create_text(x + world.style.vehicle_radius * 3, y, fill=world.style.text, text=vehicles[i], anchor=tkinter.W)


class MapGraph:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.width = w
        self.height = h

    def layout(self, params: dict):
        self.title = params["title"]
        self.bar_names = params["bars"]
        self.layer_colors = params["colors"]
        self.max_height = params["max"]

    def data_source(self, func):
        self.data_source = func

    def display(self, world: MapCanvas):
        self.w_px, self.h_px = world.coord.calc_percent_px(self.width, self.height)
        self.x_px, self.y_px = world.coord.calc_percent_px(self.x, self.y)
        p1 = world.coord.calc_percent_px(self.x, self.y)
        p2 = world.coord.calc_percent_px(self.x + self.width, self.y + self.height)
        self.bg = world.canvas.create_rectangle(p1, p2, fill=world.style.bg, outline=world.style.text)
        self.title_item = world.canvas.create_text(self.x_px + (self.w_px/2), self.y_px + world.style.font_px, text=self.title, fill=world.style.text)


        # Create bars
        x_frac = int(self.w_px / (len(self.bar_names)*3 + 1))
        y_floor = self.y_px + self.h_px - (2*world.style.font_px)
        bar_h = self.h_px - (4*world.style.font_px)
        y_ceiling = self.y_px + (2*world.style.font_px)
        # Create y index lines
        self.index_lines = []
        self.index_labels = []
        for i in range(3):
            y = y_floor - (bar_h*i / 2)
            p1 = (self.x_px + x_frac - int(world.style.font_px/2), y)
            p2 = (self.x_px + self.w_px - x_frac + int(world.style.font_px/2), y)
            line = world.canvas.create_line(p1, p2, fill=world.style.text, width=1)
            self.index_lines.append(line)
            text = "%.0f" % (self.max_height*i / 2)
            label = world.canvas.create_text(self.x_px + x_frac - world.style.font_px, y, text=text, fill=world.style.text, anchor=tkinter.E)
            self.index_labels.append(label)

        # Create bar labels
        self.bar_labels = []
        for i in range(len(self.bar_names)):
            label = world.canvas.create_text(self.x_px + (x_frac*(2 + 3*i)), y_floor + (world.style.font_px), text=self.bar_names[i], fill=world.style.text)
            self.bar_labels.append(label)
        self.bars = []
        # Create bars
        for bar, vals in self.data_source().items():
            bar_index = self.bar_names.index(bar)
            start = self.x_px + x_frac + (3*bar_index*x_frac)
            end = self.x_px + (3*x_frac*(bar_index + 1))
            layers = []
            sum_height = 0
            # Create layers of bars
            for i in range(len(vals)):
                if vals[i] == 0:
                    continue
                p1 = (start, y_floor - int(bar_h*sum_height / self.max_height))
                p2 = (end, y_floor - int(bar_h*(sum_height + vals[i]) / self.max_height))
                color = self.layer_colors[i]
                rect = world.canvas.create_rectangle(p1, p2, fill=color, outline=color)
                layers.append(rect)
                sum_height += vals[i]
            self.bars.append(layers)

    def step(self, world: MapCanvas):
        for layers in self.bars:
            for l in layers:
                world.canvas.delete(l)
        self.display(world)
