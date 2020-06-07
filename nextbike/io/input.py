from .utils import *
import pandas as pd
import os
import pickle


def read_file(path=os.path.join(get_data_path(), "input/<My_data>.csv"), datetime_cols=['datetime']):
    try:
        df = pd.read_csv(path, parse_dates=datetime_cols, infer_datetime_format=True, cache_dates=True)
        return df
    except FileNotFoundError:
        print("Data file not found. Path was " + path)


def read_model(name):
    path = os.path.join(get_model_path(), "" + name + ".pkl")
    with open(path, "rb") as f:
        model = pickle.load(f)
    return model
