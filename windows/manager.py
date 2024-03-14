import os
from multiprocessing import Process, Queue
import tkinter as tk
from tkinter import ttk

# from data.inputform import DataInputWindow
from simulator.frontend import SelfHealingSimulation

import windows.style
from windows.data import *



class ManagerWindow:
    def __init__(self, xlsx: str, working_dir: str, cmd_queue: Queue, update_queue: Queue):
        self.xlsx = xlsx
        self.dir = working_dir
        self.cmd_queue = cmd_queue
        self.update_queue = update_queue
        self.simulations = []
        self.sim_procs = []
        self.spinners = []
        self.i = 0

        os.makedirs(self.dir, exist_ok=True)
        for f in os.scandir(self.dir):
            if f.name.endswith(".pkl"):
                self.simulations.append(SimEntry(UserSim.from_pickle(f.path), self))

    def new_sim(self):
        self.cmd_queue.put(("edit_sim", "Sim %03d" % (len(self.simulations) + 1), None))

    def display(self):
        self.tk = tk.Tk()
        self.tk.title("Simulation Controller")
        self.tk.geometry("2000x1600")
        style = windows.style.get_style()
        self.tk.configure(bg=windows.style.BG_C1)

        # Setup titie
        self.title = ttk.Label(self.tk, text="SELF HEALING SIMULATION", style="WinTitle.TLabel", anchor=tk.CENTER)
        self.title.pack(padx=20, pady=10, fill=tk.X)
        self.frame = ttk.Frame(self.tk, padding=20, style="OutBox.TFrame")
        self.frame.pack(fill=tk.X)

        for s in self.simulations:
            s.display(self.frame)

        ttk.Frame(self.tk, height=20, style="OutBox.TFrame").pack(expand=True)
        ttk.Button(self.tk, text="NEW SIM", style="BigButton.TButton", command=self.new_sim).pack()
        ttk.Frame(self.tk, height=20, style="OutBox.TFrame").pack()

        self.tk.after(10, self.step)
        self.tk.mainloop()
        for p in self.sim_procs:
            p.terminate()
        self.cmd_queue.put(("quit",))

    def step(self):
        self.tk.after(10, self.step)
        self.i += 1
        while not self.update_queue.empty():
            cmd = self.update_queue.get()
            if cmd[0] == "new_sim":
                sim = UserSim(cmd[1], self.xlsx)
                sim.input = cmd[2]
                sim.to_pickle(self.dir)
                gui = SimEntry(sim, self)
                gui.display(self.frame)
                self.simulations.append(gui)
            elif cmd[0] == "update_sim":
                for s in self.simulations:
                    if s.data.name == cmd[1]:
                        s.data.output = cmd[2]
                        s.finish_sim()
                        break
            else:
                raise ValueError("Unknown cmd in queue", cmd)
        if self.i % 20 == 0:
            for s in self.spinners:
                s.step(int(self.i/20))



class SimEntry:
    def __init__(self, data, parent):
        if not type(data) is UserSim:
            raise ValueError("SimEntry requires UserSim")
        self.data = data
        self.parent = parent

    def display(self, frame):
        self.box = ttk.Frame(frame, style="Box.TFrame", padding=15)
        self.box.pack(fill=tk.X)
        ttk.Frame(frame, height=20, style="OutBox.TFrame").pack()
        # Title
        self.title = ttk.Label(self.box, text=self.data.name, style="SubTitle.TLabel", width=40)
        self.title.pack(fill=tk.X)
        # Description
        self.desc = ttk.Label(self.box, text=self.data.input, style="InBox.TLabel")
        self.desc.pack(fill=tk.X)
        # Buttons
        self.button_row = ttk.Frame(self.box, style="InBox.TFrame")
        self.button_row.pack(fill=tk.X)
        # Delete
        self.delete = ttk.Button(self.button_row, text="Delete", style="Button.TButton", command=self.delete)
        self.delete.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Frame(self.button_row, width=20, style="InBox.TFrame").pack(side=tk.LEFT)
        # Copy
        self.copy = ttk.Button(self.button_row, text="Make Copy", style="Button.TButton", command=self.copy)
        self.copy.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Frame(self.button_row, width=20, style="InBox.TFrame").pack(side=tk.LEFT, expand=True)
        # Run or display
        if self.data.output:
            self.sim_button = ttk.Button(self.button_row, text="Display", style="Button.TButton", command=self.display_sim)
        else:
            self.sim_button = ttk.Button(self.button_row, text="Run Sim", style="Button.TButton", command=self.run_sim)
        self.sim_button.pack(side=tk.LEFT, fill=tk.Y)

    def copy(self):
        self.parent.cmd_queue.put(("edit_sim", self.data.name + " COPY", self.data.input))

    def delete(self):
        self.box.pack_forget()

    def run_sim(self):
        proc = Process(target=run_user_sim, args=(self.data, self.parent.update_queue))
        proc.start()
        self.parent.sim_procs.append(proc)
        self.sim_button.pack_forget()
        self.sim_button = self.Spinner(self.button_row)
        self.parent.spinners.append(self.sim_button)

    def display_sim(self):
        self.parent.cmd_queue.put(("display_sim", self.data))

    def finish_sim(self):
        self.sim_button.pack_forget()
        self.parent.spinners.remove(self.sim_button)
        self.sim_button = ttk.Button(self.button_row, text="Display", style="Button.TButton", command=self.display_sim)
        self.sim_button.pack(side=tk.LEFT, fill=tk.Y)
        self.data.to_pickle(self.parent.dir)

    class Spinner:
        def __init__(self, frame):
            self.frame = frame
            self.dots = []
            for i in range(8):
                label = ttk.Label(frame, text="■", style="InBox.TLabel")
                label.pack(side=tk.LEFT, fill=tk.Y)
                self.dots.insert(0, label)

        def step(self, n):
            for i in range(8):
                if (n + i) % 8 == 0 or (n + i + 1) % 8 == 0:
                    self.dots[i].configure(style="BrightInBox.TLabel")
                else:
                    self.dots[i].configure(style="InBox.TLabel")

        def pack_forget(self):
            for d in self.dots:
                d.pack_forget()


def run_user_sim(sim, queue):
    sim.run()
    queue.put(("update_sim", sim.name, sim.output))
