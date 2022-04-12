import os

DATA_DIR = os.path.join("tests", "test_data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
