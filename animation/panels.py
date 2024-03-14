from operator import attrgetter
import tkinter
from tkinter import ttk
from tkinter import font

from animation.data import *
from animation.canvas import MapCanvas, ICON_SIZE


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


class BarGraph:
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

    def display(self, canvas: MapCanvas):
        self.canvas = canvas
        self.w_px, self.h_px = canvas.coord.calc_percent_px(self.width, self.height)
        self.x_px, self.y_px = canvas.coord.calc_percent_px(self.x, self.y)
        p1 = canvas.coord.calc_percent_px(self.x, self.y)
        p2 = canvas.coord.calc_percent_px(self.x + self.width, self.y + self.height)
        self.bg = canvas.canvas.create_rectangle(p1, p2, fill=canvas.style.bg, outline=canvas.style.text)
        self.title_item = canvas.canvas.create_text(self.x_px + (self.w_px/2), self.y_px + canvas.style.font_px, text=self.title, fill=canvas.style.text)

        self.x_frac = int(self.w_px / (len(self.bar_names)*3 + 1))
        self.y_floor = self.y_px + self.h_px - (2*canvas.style.font_px)
        self.bar_h = self.h_px - (4*canvas.style.font_px)
        # Create y index lines
        self.index_lines = []
        self.index_labels = []
        for i in range(3):
            y = self.y_floor - (self.bar_h*i / 2)
            p1 = (self.x_px + self.x_frac - int(canvas.style.font_px/2), y)
            p2 = (self.x_px + self.w_px - self.x_frac + int(canvas.style.font_px/2), y)
            line = canvas.canvas.create_line(p1, p2, fill=canvas.style.text, width=1)
            self.index_lines.append(line)
            text = "%.0f" % (self.max_height*i / 2)
            label = canvas.canvas.create_text(self.x_px + self.x_frac - canvas.style.font_px, y, text=text, fill=canvas.style.text, anchor=tkinter.E)
            self.index_labels.append(label)

        # Create bar labels
        self.bar_labels = []
        for i in range(len(self.bar_names)):
            label = canvas.canvas.create_text(self.x_px + (self.x_frac*(2 + 3*i)), self.y_floor + canvas.style.font_px, text=self.bar_names[i], fill=canvas.style.text)
            self.bar_labels.append(label)
        self._draw_bars(canvas)

    def _draw_bars(self):
        self.bars = []
        for bar, vals in self.data_source().items():
            bar_index = self.bar_names.index(bar)
            start = self.x_px + self.x_frac + (3*bar_index*self.x_frac)
            end = self.x_px + (3*self.x_frac*(bar_index + 1))
            layers = []
            sum_height = 0
            # Create layers of bars
            for i in range(len(vals)):
                if vals[i] == 0:
                    continue
                p1 = (start, self.y_floor - int(self.bar_h*sum_height / self.max_height))
                p2 = (end, self.y_floor - int(self.bar_h*(sum_height + vals[i]) / self.max_height))
                color = self.layer_colors[i]
                rect = self.canvas.canvas.create_rectangle(p1, p2, fill=color, outline=color)
                layers.append(rect)
                sum_height += vals[i]
            self.bars.append(layers)

    def step(self, time: float):
        for layers in self.bars:
            for l in layers:
                self.canvas.canvas.delete(l)
        self._draw_bars()


class PieChart:
    cached_time_index = -9
    cached_level_index = -9

    def __init__(self, node: str, cargo: CargoData, lat, lon):
        self.node = node
        self.levels = cargo.levels[node]
        self.maximums = dict(cargo.maximums[node])
        self.lat = lat
        self.lon = lon

    def layout(self, params: dict):
        self.title = params["title"]
        self.pie_names = params["pies"]
        self.colors = params["colors"]

    # Calculate index of move at give time
    def _index_at_time(self, time: float) -> int:
        if time < self.levels[0].time:
            return 0
        if time >= self.levels[-1].time:
            return len(self.levels) - 1
        if self.cached_time_index > 0:
            if time > self.levels[self.cached_time_index].time:
                if time < self.levels[self.cached_time_index + 1].time:
                    return self.cached_time_index
        i = 0
        while i < len(self.levels) - 1:
            if time == self.levels[i].time:
                break
            if time > self.levels[i].time and time < self.levels[i + 1].time:
                break
            i += 1
        return i

    def get_level_at(self, time):
        index = self._index_at_time(time)
        if index == self.cached_level_index:
            return self.cached_level
        level = self.levels[index]
        print("T%02.3f %s %s %s" % (time, self.node, str(level), str(self.maximums)))
        self.cached_level_index = index
        self.cached_level = level
        return level

    def draw_pies(self, level):
        self.canvas_pies = []
        i = 0
        for m in self.maximums:
            p1 = (self.pie_x0 + self.pie_r * (3 * i - 1), self.pie_y - self.pie_r)
            p2 = (self.pie_x0 + self.pie_r * (3 * i + 1), self.pie_y + self.pie_r)
            if level.levels[m] == 0:
                pass
            elif level.levels[m] == self.maximums[m]:
                self.canvas_pies.append(self.canvas.canvas.create_oval(p1, p2, fill=self.colors[m], outline=self.colors[m]))
            else:
                extent = 360 * level.levels[m] / self.maximums[m]
                self.canvas_pies.append(self.canvas.canvas.create_arc(p1, p2, start=0, extent=extent, fill=self.colors[m], outline=self.colors[m]))
            p = (self.pie_x0 + self.pie_r * 3 * i, self.pie_y)
            self.canvas_pies.append(self.canvas.canvas.create_text(p, text=int(level.levels[m]), fill=self.canvas.style.bg))
            i += 1

    def display(self, canvas: MapCanvas):
        self.canvas = canvas
        self.x_px, self.y_px = canvas.coord.calc_px(self.lat, self.lon)
        # Draw line to base
        self.canvas_line = canvas.canvas.create_line((self.x_px, self.y_px), canvas.get_named_px(self.node), fill=canvas.style.text, width=canvas.style.line_width)

        self.pie_r = 6*canvas.style.font_px
        self.w_px = self.pie_r * len(self.maximums) * 3
        self.h_px = self.pie_r * 3 + 3*canvas.style.font_px
        p1 = (self.x_px - self.w_px/2, self.y_px - self.h_px/2)
        p2 = (self.x_px + self.w_px/2, self.y_px + self.h_px/2)
        self.bg = canvas.canvas.create_rectangle(p1, p2, fill=canvas.style.bg, outline=canvas.style.text)
        self.title_item = canvas.canvas.create_text(self.x_px, self.y_px + canvas.style.font_px * 2 - self.h_px/2, text=self.title, fill=canvas.style.text)
        # Create pies
        self.pie_x0 = self.x_px + int(self.pie_r * 1.5 - self.w_px/2)
        self.pie_y = self.y_px + 2 * canvas.style.font_px + int(self.pie_r * 1.5 - self.h_px/2)
        self.pie_backs = []
        self.pie_labels = []
        i = 0
        for m in self.maximums:
            # Create chart backgrounds
            p1 = (self.pie_x0 + self.pie_r * (3 * i - 1) - canvas.coord.scale, self.pie_y - self.pie_r - canvas.coord.scale)
            p2 = (self.pie_x0 + self.pie_r * (3 * i + 1) + canvas.coord.scale, self.pie_y + self.pie_r + canvas.coord.scale)
            self.pie_backs.append(canvas.canvas.create_oval(p1, p2, fill=canvas.style.text, outline=canvas.style.text))
            # Create chart labels
            self.pie_labels.append(canvas.canvas.create_text(self.pie_x0 + self.pie_r * 3 * i, self.y_px + self.h_px/2 - canvas.style.font_px * 2, text=self.pie_names[m], fill=canvas.style.text))
            i += 1
        level = self.get_level_at(0)
        self.draw_pies(level)

    def step(self, time: float):
        level = self.get_level_at(time)
        for p in self.canvas_pies:
            self.canvas.canvas.delete(p)
        self.draw_pies(level)
