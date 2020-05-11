from .utils import get_data_path
import pandas as pd
import os
import pickle


def read_file(path=os.path.join(get_data_path(), "input/<My_data>.csv")):
    try:
        try:
            df = pd.read_csv(path, parse_dates=['datetime', 'start_time', 'end_time'], infer_datetime_format=True, cache_dates=True)
        except ValueError:
            df = pd.read_csv(path, parse_dates=['datetime'], infer_datetime_format=True, cache_dates=True)
        return df
    except FileNotFoundError:
        print("Data file not found. Path was " + path)


def read_model():
    path = os.path.join(get_data_path(), "output/model.pkl")
    with open(path, "rb") as f:
        model = pickle.load(f)
    return model
