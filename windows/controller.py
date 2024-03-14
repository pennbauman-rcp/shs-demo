import os
from multiprocessing import Process, Queue

from animation.data import *
from animation.window import WorldMap
from windows.data import SimGUIInputs
from windows.manager import ManagerWindow
from windows.input import InputWindow



def run_manager(xlsx, directory, cmd_queue, in_queue):
    win = ManagerWindow(xlsx, directory, cmd_queue, in_queue)
    win.display()

def edit_sim(name, data, cmd_queue):
    win = InputWindow(data, name, cmd_queue)
    (name, data) = win.display()
    cmd_queue.put(("new_sim", name, data))

def display_sim(data):
    nodes = LocationsData.from_xlsx(data.xlsx)
    routing = RoutingData.from_object(data.output)
    cargo = CargoData.from_object(data.output)

    world = WorldMap(nodes, routing, cargo)
    world.crop(-5, -120)
    world.style("satellite", False)
    world.run()



class ApplicationController:
    def __init__(self, xlsx, directory):
        self.xlsx = xlsx
        os.makedirs(directory, exist_ok=True)
        self.directory = directory
        self.cmd_queue = Queue()
        self.manager_queue = Queue()
        self.procs = []

    def run(self):
        self.manager_proc = Process(
                target=run_manager,
                args=(self.xlsx, self.directory, self.cmd_queue, self.manager_queue)
            )
        self.manager_proc.start()
        while True:
            cmd = self.cmd_queue.get()
            if cmd[0] == "quit":
                break
            elif cmd[0] == "edit_sim":
                if cmd[2]:
                    data = cmd[2]
                else:
                    data = SimGUIInputs.from_xlsx(self.xlsx)
                proc = Process(
                        target = edit_sim,
                        args = (cmd[1], data, self.cmd_queue)
                    )
                proc.start()
                self.procs.append(proc)
            elif cmd[0] == "display_sim":
                proc = Process(target=display_sim, args=(cmd[1],))
                proc.start()
                self.procs.append(proc)
            elif cmd[0] == "new_sim":
                self.manager_queue.put(cmd)
            else:
                raise ValueError("Unknown cmd in queue", cmd)
        for p in self.procs:
            p.join()

