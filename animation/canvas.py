import tkinter
from tkinter import font


MAP_SCALES = [
    # px_width, px_width, scale
    (7200, 3600, 4),
    (3600, 1800, 2),
    (1800,  900, 1),
]
ICON_SIZE = 1 # 1 or 2


class MapCanvas:
    def __init__(self):
        self.style = None
        self.coord = WorldCoordinates()
        self.named = {}

    # Set style by style name ('light', 'dark', or 'satellite')
    def set_style(self, style_name: str, icons: bool):
        self.style = WorldStyle(style_name, icons)

    # Crop in map to show 1/4 of earth
    def crop(self, min_lat: int, min_lon: int):
        self.coord = WorldCoordinates(min_lat, min_lon, 2)
        # print("Cropping world to", self.coord)

    # Add a named location that other can reference later
    def add_named_loc(self, name: str, lat: float, lon: float):
        if "_" in name:
            # Everything after a '_' is stripped by the getter (see below)
            raise ValueError("'_' not allowed in named locations")
        try:
            self.named[name] = self.coord.calc_px(lat, lon)
        except:
            self.named[name] = None

    # Get pixel location of a name location
    def get_named_px(self, name: str) -> tuple[int, int]:
        name = name.split("_")[0]
        if name in self.named:
            return self.named[name]
        raise ValueError("Unknown node '%s'" % (name))

    def display(self, parent, verbose: bool = False):
        if not self.style:
            self.style = WorldStyle
        self.style.set_px(self)
        # Setup canvas with background
        self.canvas = tkinter.Canvas(parent, bg="black", height=self.coord.px_height, width=self.coord.px_width, confine=False)
        self.canvas.grid(column=0, row=0)
        img_width = self.coord.px_width * self.coord.zoom
        img_height = self.coord.px_height * self.coord.zoom
        self.bg_img = tkinter.PhotoImage(master=self.canvas, file=self.style.get_map_file(img_width, img_height))
        self.canvas.create_image(self.coord.calc_world_offset_px(), image=self.bg_img, anchor=tkinter.NW)

        if verbose:
            center_lat = self.coord.min_lat + (self.coord.max_lat - self.coord.min_lat)/2
            center_lon = self.coord.min_lon + (self.coord.max_lon - self.coord.min_lon)/2
            print("Cropping map to center on (%d, %d)" % (center_lat, center_lon))



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
                self.scale = scale[2]
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

    def calc_percent_px(self, x_percent: float, y_percent: float) -> tuple[int, int]:
        if not (self.px_width and self.px_height):
            raise ValueError("Pixels must be set before they can be calculated")
        x = (self.px_width * x_percent) / 100
        y = (self.px_height * y_percent) / 100
        return (int(x), int(y))


class WorldStyle:
    def __init__(self, map_style: str, icons: bool = False):
        if map_style:
            self.map = map_style
        else:
            self.map = "light"
        self.icons = icons
        # Determine colors
        if self.map == "light":
            self.text = "#000000"
            self.bg = "#D9D9D9"
            self.vehicles = {
                    "Airplane": "#ffa500",
                    "Ship":     "#ff0000",
                    "Train":    "#800080",
                    "Truck":    "#008000",
                }
        else:
            self.text = "#eeeeee"
            self.bg = "#040404"
            self.vehicles = {
                    "Airplane": "#ff5252",
                    "Ship":     "#40c4ff",
                    "Train":    "#b2ff59",
                    "Truck":    "#7c4dff",
                }

    def set_px(self, world: MapCanvas):
        # Determine map item scales
        self.node_radius = world.coord.scale * 3
        self.vehicle_radius = world.coord.scale * 5
        if self.map == "light":
            self.line_width = world.coord.scale * 2
        else:
            self.line_width = world.coord.scale
        self.font_px = font.nametofont('TkTextFont').actual()["size"]*world.coord.scale

    def get_map_file(self, w: int, h: int) -> str:
        if self.map == "light":
            return "files/maps/equirectangular_earth_map_light_%04dx%04d.png" % (w, h)
        elif self.map == "dark":
            return "files/maps/equirectangular_earth_map_dark_%04dx%04d.png" % (w, h)
        elif self.map == "satellite":
            return "files/maps/equirectangular_earth_satellite_%04dx%04d.png" % (w, h)

    def get_icon_file(self, vehicle: str) -> str:
        if not (self.node_radius and self.vehicle_radius and self.line_width):
            raise ValueError("Pixels values must be set get icon files")
        color = self.vehicles[vehicle].replace("#", "")
        size = self.vehicle_radius * 4 * ICON_SIZE
        return "files/icons/%s_%s_%dx%d.png" % (vehicle.lower(), color, size, size)



