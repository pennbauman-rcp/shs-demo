import tkinter as tk
from tkinter import ttk

from windows.data import SimGUIInputs
import windows.style

class InputWindow:
    submitted = False

    def __init__(self, data, name, cmd_queue):
        if not type(data) is SimGUIInputs:
            raise ValueError("InputWindow requires SimGUIInputs")
        self.data = data
        self.name = name
        self.cmd_queue = cmd_queue

    def display(self):
        self.tk = tk.Tk()
        style = windows.style.get_style()
        self.tk.title("Simulation Inputs")
        self.tk.configure(bg=windows.style.BG_C1)

        # Setup titie
        self.title = ttk.Label(self.tk, text="SIMULATION INPUTS", style="WinTitle.TLabel", anchor=tk.CENTER)
        self.title.pack(padx=20, pady=10, fill=tk.X)
        self.frame = ttk.Frame(self.tk, padding=20, style="OutBox.TFrame")
        self.frame.pack(expand=True, fill=tk.X)
        self.frame_left = ttk.Frame(self.frame, padding=20, style="OutBox.TFrame")
        self.frame_left.pack(side=tk.LEFT, expand=True, fill=tk.Y)
        self.frame_right = ttk.Frame(self.frame, padding=20, style="OutBox.TFrame")
        self.frame_right.pack(side=tk.LEFT, expand=True, fill=tk.Y)

        self.nodes = []
        nodelist = []
        for d in self.data.nodes:
            nodelist.append(d)
        nodelist.sort()
        for n in nodelist:
            self.nodes.append(InputNode(self.data.nodes[n]))
        i = 0
        while i < int(len(nodelist)/2) + len(nodelist) % 2:
            self.nodes[i].display(self.frame_left)
            ttk.Frame(self.frame_left, height=20, style="OutBox.TFrame").pack()
            i += 1
        while i < len(nodelist):
            self.nodes[i].display(self.frame_right)
            ttk.Frame(self.frame_right, height=20, style="OutBox.TFrame").pack()
            i += 1

        # for n in self.nodes:
            # n.display(self.frame)
            # ttk.Frame(self.frame, height=20, style="OutBox.TFrame").pack()

        self.bottom = ttk.Frame(self.tk, padding=20, style="OutBox.TFrame")
        self.bottom.pack(fill=tk.X)
        ttk.Label(self.bottom, text="Save as:", style="OutBox.TLabel").pack(side=tk.LEFT)
        self.name_entry = ttk.Entry(self.bottom, width=18, style="Text.TEntry")
        self.name_entry.insert(0, self.name)
        self.name_entry.pack(side=tk.LEFT)
        ttk.Frame(self.bottom, style="OutBox.TFrame").pack(expand=True, side=tk.LEFT)
        ttk.Button(self.bottom, text="SAVE", style="BigButton.TButton", command=self.submit).pack(side=tk.LEFT)
        ttk.Frame(self.tk, height=20, style="OutBox.TFrame").pack()

        self.tk.mainloop()

    def submit(self):
        success = True
        for n in self.nodes:
            success = success and n.submit()
            self.data.nodes[n.data.icao] = n.data
        if success:
            self.cmd_queue.put(("new_sim", self.name_entry.get(), self.data))
            self.tk.quit()
            self.tk.destroy()




class InputNode:
    def __init__(self, data):
        if not type(data) is SimGUIInputs.Node:
            raise ValueError("InputNode requires SimGUIInputs.Node")
        self.data = data

    def display(self, frame):
        self.box = ttk.Frame(frame, style="Box.TFrame", padding=15)
        self.box.pack(fill=tk.X)
        # Header row
        self.row1 = ttk.Frame(self.box, style="InBox.TFrame", width=40)
        self.row1.pack(fill=tk.X)
        # Title
        title = self.data.icao + " - " + self.data.name
        self.title = ttk.Label(self.row1, text=title, style="SubTitle.TLabel", width=30)
        self.title.pack(side=tk.LEFT)
        ttk.Frame(self.row1, style="InBox.TFrame").pack(side=tk.LEFT, expand=True)
        # Enable/disable buttom
        self.enable_button = ttk.Button(self.row1, text="Disable", style="Button.TButton", command=self.toggle_disabled)
        self.enable_button.pack(side=tk.LEFT, fill=tk.Y)
        # Vehicle and distruption rows
        self._detail_rows()

    def _detail_rows(self):
        # Vehicle row
        self.row2 = ttk.Frame(self.box, style="InBox.TFrame", padding=5)
        self.row2.pack(fill=tk.X)
        self.vehicles = {}
        for v in self.data.vehicles:
            ttk.Label(self.row2, text=v, style="InBox.TLabel").pack(side=tk.LEFT)
            entry = ttk.Entry(self.row2, width=4, style="Num.TEntry")
            entry.insert(0, self.data.vehicles[v])
            entry.pack(side=tk.LEFT)
            self.vehicles[v] = entry
        # Disruptions
        self.disruptions = []
        self.row3 = ttk.Frame(self.box, style="InBox.TFrame")
        self.row3.pack(fill=tk.X)
        for d in self.data.disruptions:
            self.add_disruption()
            entries = self.disruptions[-1]
            entries[0].insert(0, d[0])
            entries[1].insert(0, d[1])
        self.row4 = ttk.Frame(self.box, style="InBox.TFrame", padding=5)
        self.row4.pack(fill=tk.X)
        ttk.Button(self.row4, text="Add Disruption", style="Button.TButton", command=self.add_disruption).pack(side=tk.LEFT, fill=tk.Y)

    def toggle_disabled(self):
        if self.data.disabled:
            self.data.disabled = False
            self.title.configure(style="SubTitle.TLabel")
            self.enable_button.configure(text="Disable")
            self._detail_rows()
        else:
            self.data.disabled = True
            self.title.configure(style="SubTitleOff.TLabel")
            self.enable_button.configure(text="Enable")
            for v in self.vehicles:
                try:
                    self.data.vehicles[v] = int(self.vehicles[v].get())
                except:
                    pass
            self.data.disruptions = []
            for d in self.disruptions:
                try:
                    start = float(d[0].get())
                    end = float(d[1].get())
                    self.data.disruptions.append((start, end))
                except:
                    pass
            self.row2.pack_forget()
            self.row3.pack_forget()
            self.row4.pack_forget()

    def add_disruption(self):
        frame = ttk.Frame(self.row3, style="InBox.TFrame", padding=5)
        frame.pack(fill=tk.X)
        ttk.Label(frame, text="Disruption start:", style="InBox.TLabel").pack(side=tk.LEFT)
        start = ttk.Entry(frame, width=4, style="Num.TEntry")
        start.pack(side=tk.LEFT)
        ttk.Label(frame, text="end:", style="InBox.TLabel").pack(side=tk.LEFT)
        end = ttk.Entry(frame, width=4, style="Num.TEntry")
        end.pack(side=tk.LEFT)
        ttk.Label(frame, text="days", style="InBox.TLabel").pack(side=tk.LEFT)
        self.disruptions.append((start, end))

    def submit(self):
        ret = True
        for v in self.vehicles:
            try:
                self.data.vehicles[v] = int(self.vehicles[v].get())
                self.vehicles[v].configure(style="Num.TEntry")
            except:
                self.vehicles[v].configure(style="NumError.TEntry")
                ret = False
        self.data.disruptions = []
        for d in self.disruptions:
            this = True
            try:
                start = float(d[0].get())
                d[0].configure(style="Num.TEntry")
            except:
                d[0].configure(style="NumError.TEntry")
                ret = False
                this = False
            try:
                end = float(d[1].get())
                d[1].configure(style="Num.TEntry")
            except:
                d[1].configure(style="NumError.TEntry")
                ret = False
                this = False
            if this:
                self.data.disruptions.append((start, end))
        return ret

