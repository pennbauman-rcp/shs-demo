import tkinter
from tkinter import ttk

from data.parse import *
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
        if self.tk.winfo_screenheight() == 1080:
            SCALE = 1
        elif self.tk.winfo_screenheight() == 2160:
            SCALE = 2
        else:
            raise ValueError("Unknown screen resolution %dx%d" % (self.tk.winfo_screenheight(), self.tk.winfo_screenwidth()))
        self.tk.title("SHS Demo")
        self.tk.configure(bg="black")
        self.tk.grid()
        # print("Displaying World, (0, 0) is", self.coord.calc_px(0, 0))

        # Create toolbar
        self.toolbar = ttk.Frame(self.tk, padding=(5*SCALE, 2*SCALE))
        self.toolbar.pack(fill=tkinter.X)
        # Clock
        self.clock = ttk.Label(self.toolbar, text="Time: 0.0", padding=(10*SCALE, 0), width=12)
        self.clock.pack(side="left")
        # Spacer
        ttk.Label(self.toolbar).pack(side="left", expand=True)
        # Centeral buttons
        buttons = [
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
        for b in buttons:
            ttk.Button(self.toolbar, text=b[0], command=b[1]).pack(side="left", padx=5)
        # Spacer (wider to balance clock)
        ttk.Label(self.toolbar, width=6).pack(side="left", expand=True)
        # Quit button
        ttk.Button(self.toolbar, text="Quit", command=self.tk.destroy).pack(side="left")


        # Setup canvas
        self.map_frame = ttk.Frame(self.tk, padding=0, borderwidth=0)
        self.map_frame.pack(fill=tkinter.BOTH)
        # Size map
        canvas_w = self.tk.winfo_screenwidth() - 2
        canvas_h = self.tk.winfo_screenheight() - 100*SCALE - 14
        self.canvas.set_px(canvas_w, canvas_h)
        # Add bases
        for n in self.nodes:
            self.canvas.add_named_loc(n.name, n.lat, n.lon)
        self.canvas.display(self.map_frame, verbose)

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
        self.clock["text"] = "Time: %.3f" % self.time

        for v in self.vehicles:
            v.step(self.canvas, self.time)
        for g in self.graphs:
            g.step(self.canvas)

        if self.time <= self.end_time:
            self.tk.after(10, self.step)
        else:
            if self.verbose:
                print("Finished animation (T%.3f)" % self.time)
        self.time += 0.002 * self.speed

    def pause(self):
        self.paused = True

    def set_speed(self, speed: int):
        self.paused = False
        self.speed = speed

