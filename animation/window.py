import tkinter
from tkinter import ttk

from animation.data import *
from animation.canvas import MapCanvas, DYNAMIC_LEG_DISPLAY
from animation.panels import *
from animation.objects import *
import windows.style


# Main map window, contains all map elements
class WorldMap:
    time = 0.0
    end_time = 0.0
    paused = False
    speed = 1

    def __init__(self, xlsx, sim_log):
        self.xlsx = xlsx
        self.sim_log = sim_log
        self.canvas = MapCanvas()
        self.graphs = []
        self.nodes = []
        self.legs = []
        self.vehicles = []
        self.nodes = []
        for n in LocationsData.from_xlsx(xlsx):
            self.nodes.append(MapNode(n.name, n.lat, n.lon))
        routing = RoutingData.from_object(sim_log)
        if routing:
            self.legs = []
            for l in routing.get_legs():
                self.legs.append(MapLeg(l[0], l[1]))
            self.vehicles = []
            for v in routing.get_vehicles():
                self.vehicles.append(MapVehicle(v.vehicle_id, v.model, v.moves))
            self.end_time = routing.get_end_time()
        self.cargo_data = CargoData.from_object(sim_log)


    # Crop in map to show 1/4 of earth
    def crop(self, min_lat: int, min_lon: int):
        self.canvas.crop(min_lat, min_lon)

    # Set style by style name ('light', 'dark', or 'satellite')
    def style(self, style_name: str, icons: bool):
        self.canvas.set_style(style_name, icons)

    def add_vehicle_graph(self):
        graph = BarGraph(35, 80, 30, 20)
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

    def add_cargo_piechart(self, node, lat, lon):
        if not node in self.cargo_data.levels:
            return
        piechart = PieChart(node, self.cargo_data, lat, lon)
        piechart.layout({
                "title": "Cargo at " + node,
                "pies": {
                        "PAX": "Passengers",
                        "cargo": "Cargo",
                        "out": "Over Out",
                    },
                "colors": {
                        "PAX": self.canvas.style.vehicles["Ship"],
                        "cargo": self.canvas.style.vehicles["Train"],
                        "out": self.canvas.style.vehicles["Train"],
                    },
            })
        self.graphs.append(piechart)

    def add_cargo_charts(self):
        self.add_cargo_piechart("KFCS", 60, -100)
        self.add_cargo_piechart("KBGR", 70, -60)
        self.add_cargo_piechart("KGRK", 10, -100)
        self.add_cargo_piechart("LERT", 10, -15)
        self.add_cargo_piechart("ETAD", 70, -15)
        self.add_cargo_piechart("ETAR", 20, 30)
        self.add_cargo_piechart("KJAX", 10, -55)
        self.add_cargo_piechart("EPKK", 70, 30)
        self.add_cargo_piechart("EDWB", 70, 50)

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
    def run(self, speed: int = 1, verbose: bool = False):
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
        style = windows.style.get_style()
        self.tk.configure(bg=windows.style.BG_C1)
        self.tk.grid()
        # print("Displaying World, (0, 0) is", self.coord.calc_px(0, 0))

        # Create toolbar
        self.toolbar = ttk.Frame(self.tk, padding=(5*SCALE, 2*SCALE), style="OutBox.TFrame")
        self.toolbar.pack(fill=tkinter.X)
        # Clock
        self.clock = ttk.Label(self.toolbar, text="Time: 0.0", padding=(10*SCALE, 0), style="OutBox.TLabel", width=24)
        self.clock.pack(side="left")
        # Spacer
        ttk.Label(self.toolbar, style="OutBox.TLabel").pack(side="left", expand=True)
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
            ttk.Button(self.toolbar, text=b[0], style="Button.TButton", command=b[1]).pack(side="left", padx=15)
        # Spacer (wider to balance clock)
        ttk.Label(self.toolbar, style="OutBox.TLabel", width=9).pack(side="left", expand=True)
        # Quit button
        ttk.Button(self.toolbar, text="Quit", style="Button.TButton", command=self.tk.destroy).pack(side="left")


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
                node_count += 1
            except:
                pass
        if verbose:
            print("Nodes displayed (%d)" % node_count)
        if not DYNAMIC_LEG_DISPLAY:
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
        self.timebar = TimelineBar(self.end_time)
        self.timebar.display(self.canvas)
        for g in self.graphs:
            g.display(self.canvas)
        if verbose:
            print("Graphs displayed (%d)" % len(self.graphs))

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
        days = self.time
        hours = (days % 1) * 24
        minutes = (hours % 1) * 60
        self.clock["text"] = "Day %.0f %02.0f:%02.0f" % (days, hours, minutes)
        self.timebar.step(self.time)

        for v in self.vehicles:
            v.step(self.canvas, self.time)
        for g in self.graphs:
            g.step(self.time)

        self.time += 0.002 * self.speed
        if self.time > self.end_time:
            self.time = self.end_time
        elif self.time < 0:
            self.time = 0
        self.tk.after(10, self.step)


    def pause(self):
        self.paused = True

    def set_speed(self, speed: int):
        self.paused = False
        self.speed = speed

