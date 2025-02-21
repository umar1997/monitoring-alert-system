import os
import json 
import time

#############################################################################################
#                                 GENERAL
#############################################################################################

def load_configurations(cwd):
    try:
        config_path = os.path.join(cwd, 'config.json')
        with open(config_path, 'r') as json_file:
            config = json.load(json_file)
        print(f"Current Working Directory: {cwd} (^_^)")
    except Exception as e:
        print(f"Custom Exception: - (load_configurations) {e}")
        config = {}
    return config


def calculate_time(start_time):
    end_time = time.time()
    elapsed_time = end_time - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"*********Elapsed Time: {int(hours)} Hours, {int(minutes)} Minutes, {int(seconds)} Seconds*********")
