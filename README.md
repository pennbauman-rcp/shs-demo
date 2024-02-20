# Self Healing Simulation Demo
Visualizer and Runner for [Zanne's SHS code](https://github.com/suecoxdesigns/SimPy-Simulation/tree/lib)



## Setup
Tkinter must be installed with along with python. You can check if it available with the following command, an error means it is missing.

     python3 -c "import tkinter; print(tkinter)"

Fetch simulation code

    git submodule init
    git submodule update

Create python virtual environment

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt


## Usage
To run the visualizer and simulation use

    ./main.py

If you want to use existing simulation output, it can be provided with the `--mission-log` option. For example

    ./main.py --mission-log data/missionlog_transload_army.csv

Other option are available. To view help information run

    ./main.py --help
