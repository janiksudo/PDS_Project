from .utils import *
import pandas as pd
import os
import pickle


def read_file(path=os.path.join(get_data_path(), "input/<My_data>.csv"), datetime_cols=['datetime']):
    df = pd.read_csv(path, parse_dates=datetime_cols,
                     infer_datetime_format=True, cache_dates=True)
    return df


def read_model(name):
    path = os.path.join(get_model_path(), "" + name + ".pkl")
    with open(path, "rb") as f:
        model = pickle.load(f)
    return model
