import tkinter
from tkinter import ttk

from csvdata import *
from animation.canvas import MapCanvas
from animation.panels import *
from animation.objects import *


# Main map window, contains all map elements
class WorldMap:
    time = 0.0
    end_time = 0.0
    paused = False
    speed = 1

    def __init__(self, nodes: LocationsData = None, routing: RoutingData = None):
        self.canvas = MapCanvas()
        self.graphs = []
        self.nodes = []
        self.legs = []
        self.vehicles = []
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
        self.canvas.crop(min_lat, min_lon)

    # Set style by style name ('light', 'dark', or 'satellite')
    def style(self, style_name: str, icons: bool):
        self.canvas.set_style(style_name, icons)

    def add_graph(self):
        graph = MapGraph(35, 80, 30, 20)
        graph.layout({
                "title": "Vehicle Utilization",
                "bars": ["Loading", "Moving", "Done"],
                "colors": [
                        self.canvas.style.vehicles["Airplane"],
                        self.canvas.style.vehicles["Ship"],
                        self.canvas.style.vehicles["Train"],
                        self.canvas.style.vehicles["Truck"],
                    ],
                "max": len(self.vehicles),
            })
        graph.data_source(self.get_vehicle_usage)
        self.graphs.append(graph)

    def get_vehicle_usage(self) -> dict[str, list[int]]:
        vehicle_index = {"Airplane": 0, "Ship": 1, "Train": 2, "Truck": 3}
        usage = {
                "Loading": [0]*4,
                "Moving": [0]*4,
                "Done": [0]*4,
            }
        for v in self.vehicles:
            usage[v.get_usage_at(self.time)][vehicle_index[v.kind]] += 1
        return usage


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
        self.canvas.coord.set_px(self.tk.winfo_screenwidth(), self.tk.winfo_screenheight())
        # self.tk.minsize(self.coord.px_width, self.coord.px_height)
        # self.canvas.style.set_px(self)
        # print("Displaying World, (0, 0) is", self.coord.calc_px(0, 0))

        # Create toolbar
        self.toolbar = ttk.Frame(self.tk, padding=0)
        self.toolbar.grid()
        self.toolbar.grid(column=0, row=0)
        buttons = [
                ("Quit", self.tk.destroy),
                ("Rewind x16", lambda: self.set_speed(-16)),
                ("Rewind x8", lambda: self.set_speed(-8)),
                ("Rewind x4", lambda: self.set_speed(-4)),
                ("Rewind x2", lambda: self.set_speed(-2)),
                ("Rewind", lambda: self.set_speed(-1)),
                ("Pause", self.pause),
                ("Play", lambda: self.set_speed(1)),
                ("Speed x2", lambda: self.set_speed(2)),
                ("Speed x4", lambda: self.set_speed(4)),
                ("Speed x8", lambda: self.set_speed(8)),
                ("Speed x16", lambda: self.set_speed(16)),
            ]
        col = 0
        for b in buttons:
            ttk.Button(self.toolbar, text=b[0], command=b[1]).grid(column=col, row=0)
            col += 1

        # Setup canvas with background
        self.canvas.set_nodes(self.nodes)
        self.canvas.display(self.tk, verbose)

        # Setup overlay items
        node_count = 0
        for n in self.nodes:
            try:
                n.display(self.canvas)
                if len(self.legs) > 0:
                    n.hide(self.canvas)
                node_count += 1
            except:
                pass
        if verbose:
            print("Nodes displayed (%d)" % node_count)
        for l in self.legs:
            l.display(self.canvas)
        if verbose:
            print("Legs displayed (%d)" % len(self.legs))

        # Setup vehicles
        for v in self.vehicles:
            v.display(self.canvas)
        if verbose:
            print("Vehicles displayed (%d)" % len(self.vehicles))

        # Add map decorations
        self.clock = WorldClock()
        self.clock.display(self.canvas)
        self.key = VehicleKey()
        self.key.display(self.canvas)
        for g in self.graphs:
            g.display(self.canvas)

        # Print vehicle counts
        tmp = self.get_vehicle_usage()
        for i in range(4):
            count = 0
            for col in tmp:
                count += tmp[col][i]
            print(">", ["airplanes:", "ships:", "trains:", "trucks:"][i], count)

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
            v.step(self.canvas, self.time)
        self.clock.step(self.canvas, self.time)
        for g in self.graphs:
            g.step(self.canvas)

        if self.time <= self.end_time:
            self.tk.after(10, self.step)
        else:
            if self.verbose:
                print("Finished animation (T%.3f)" % self.time)
        self.time += 0.05 * self.speed

    def pause(self):
        self.paused = True

    def set_speed(self, speed: int):
        self.paused = False
        self.speed = speed

