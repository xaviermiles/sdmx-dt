import os
import shutil

DATA_DIR = os.path.join("tests", "test_data")
# Ensure previous data is cleared
try:
    shutil.rmtree(DATA_DIR)
except FileNotFoundError:
    pass
os.makedirs(DATA_DIR)
