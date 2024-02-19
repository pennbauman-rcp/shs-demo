import sys
import re
import tkinter
from tkinter import ttk

# Default counts for each vehicle
VEHICLE_COUNTS = {
        "C17":      12,
        "B777":     10,
        "LMSR":     4,
        "train_US": 20,
        "truck_EU": 70,
        "truck_US": 70,
        "train_EU": 10,
    }
# Label text for each vehicle
VEHICLE_FANCY_NAMES = {
        "C17":      "C17 (Airplane)",
        "B777":     "B777 (Airplane)",
        "LMSR":     "LMSR (Ship)",
        "train_US": "US Train",
        "truck_US": "US Truck",
        "train_EU": "EU Train",
        "truck_EU": "EU Truck",
    }


class DataInputWindow:
    def __init__(self):
        pass

    def run(self):
        # Setup window
        self.tk = tkinter.Tk()
        self.tk.title("SHS Demo")
        self.frame = tkinter.Frame(self.tk, padx=50, pady=20)
        self.frame.pack()
        # Setup titie
        self.title = tkinter.Label(self.frame, text="Vehicle Counts", font=("Helvetica", 18))
        self.title.pack()
        # Setup vehicle entry boxes
        self.vehicles = []
        for model, n in VEHICLE_COUNTS.items():
            form = VehicleCountForm(model)
            form.display(self.frame)
            self.vehicles.append(form)
        # Setup go button
        self.button = ttk.Button(self.frame, text="Run Simulation", command=self.read_in)
        self.button.pack()

        self.tk.mainloop()
        return self.data

    def read_in(self):
        error = False
        data = {}
        for v in self.vehicles:
            if v.read_int() < 0:
                error = True
            else:
                data[v.model] = v.read_int()
        # If all data is valid, save it and close the window
        if not error:
            self.data = data
            self.tk.destroy()
            self.tk.quit()


class VehicleCountForm:
    def __init__(self, model: str):
        self.model = model
        self.input = str(VEHICLE_COUNTS[model])

    def display(self, tk):
        self.label = tkinter.Label(tk, text=VEHICLE_FANCY_NAMES[self.model])
        self.label.pack()
        # Entry box with default
        self.entry = tkinter.Entry(tk)
        self.entry.insert(0, VEHICLE_COUNTS[self.model])
        self.entry.pack()
        # Error message (blank by default)
        self.warning = tkinter.Label(tk, text="")
        self.warning.pack()

    def read_int(self):
        self.warning["text"] = ""
        self.warning["bg"] = "#D9D9D9"
        try:
            return int(self.entry.get())
        except:
            self.warning["text"] = "Invalid number"
            self.warning["bg"] = "red"
            return -1

