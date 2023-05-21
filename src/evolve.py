# Genetic Algorithm for Intrinsic Analog Hardware Evolution
# FOR USE WITH LATTICE iCE40 FPGAs ONLY
#
# This code can be used to evolve an analog oscillator
#
# Author: Derek Whitley


from Microcontroller import Microcontroller
from CircuitPopulation import CircuitPopulation
from Circuit import Circuit
from Config import Config
from Logger import Logger
from configparser import ConfigParser
from subprocess import run
from datetime import datetime
import shutil
from pathlib import Path
import os

CONFIG_PATH = "data/config.ini"

def copy_file(src, dest):
    '''
    Simple creates the dest and copies the file
    '''
    os.makedirs(os.path.dirname(dest), exist_ok = True)
    shutil.copy(src, dest)

def copy_tree(src, dest):
    '''
    Creates the dest and copies the whole tree
    '''
    os.makedirs(os.path.dirname(dest), exist_ok = True)
    shutil.copytree(src, dest)

# TODO: Store the live data files in some sort of constant

config_parser = ConfigParser()
config_parser.read(CONFIG_PATH)
config = Config(config_parser)

explanation = input("Explain this experiment: ")

logger = Logger(config, explanation)
mcu = Microcontroller(config, logger)

live_data_prefix = 'workspace'
live_datas = ['alllivedata.log', 'bestlivedata.log', 'maplivedata.log', 'poplivedata.log', 'violinlivedata.log', 'waveformlivedata.log']

num_runs = config.get_num_runs()
run_folders = []
runs_dir = config.get_runs_dir()
if num_runs > 1:
    # Select folders to store the runs into
    now = datetime.now()
    time_string = now.strftime("%d-%m-%Y %H:%M:%S")
    logger.log_info(1, "Will output " + str(num_runs) + " runs to these folders:")
    for run in range(0, num_runs):
        folder = runs_dir.joinpath(time_string + " NUM" + str(run))
        run_folders.append(folder)
        logger.log_event(1, str(folder))

for run in range(0, num_runs):
    logger.log_info(1, "Starting run #" + str(run + 1))

    population = CircuitPopulation(mcu, config, logger)

    population.populate()
    population.evolve()

    if num_runs > 1:
        # Finished a run, need to store the results, inform the user, and continue
        logger.log_info(1, "Completed run #" + str(run + 1))
        # Included: config.ini, the experiment_asc folder, best.asc, and live datas 
        # (alllivedata, bestlivedata, maplivedata, poplivedata, violinlivedata, waveformlivedata)
        folder = run_folders[run]
        copy_file(CONFIG_PATH, str(folder.joinpath('config.ini')))
        copy_file(config.get_best_file(), str(folder.joinpath('best.asc')))

        copy_tree(config.get_asc_directory(), str(folder.joinpath('experiment_asc')))

        for data_path in live_datas:
            path = Path(live_data_prefix).joinpath(data_path)
            new_path = folder.joinpath(data_path)
            copy_file(str(path), str(new_path))

        # Clear log files for the next run
        logger.clear_logs()


logger.log_event(0, "Evolution has completed successfully")
if num_runs > 1:
    logger.log_event(0, "Runs are in these folders:")
    for folder in run_folders:
        logger.log_event(0, folder)



# SECTION Clean up resources


# We don't use this anymore; hardware_blink is never touched
'''if config.get_simulation_mode() == "FULLY_INTRINSIC":
    # Upload a sample bitstream to the FPGA.
    run([
        "iceprog",
        "-d",
        "i:0x0403:0x6010:0",
        "data/hardware_blink.bin"
    ])'''
