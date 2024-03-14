#!/bin/env python3
import os
import argparse
import tempfile
from multiprocessing import Process, Queue

from windows.data import *
from windows.controller import ApplicationController


# TMP_DIR = tempfile.gettempdir()
TMP_DIR = "/tmp/shs-demo"
INPUT_FILE = "files/simulation_input_planes.xlsx"


parser = argparse.ArgumentParser(prog='SHS GUI Demo')
parser.add_argument("-x", "--input-xlsx", default=INPUT_FILE, help="XLSX file containing simulation input definitions")
parser.add_argument("-d", "--directory", default=TMP_DIR, help="Directory containing user simulations")
args = parser.parse_args()


ApplicationController(args.input_xlsx, args.directory).run()
