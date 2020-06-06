from .. import io

from sklearn.ensemble import RandomForestRegressor
import os
import pandas as pd
import geopandas as gpd


class Model:
    def __init__(self, data_path):
        self._datapath = data_path
        try:
            self._processed = io.read_file(path=os.path.join(
                self._datapath, 'processed/dataset.csv'), datetime_cols=['start_time', 'end_time'])
        except FileNotFoundError:
            print(
                'The dataset "dataset.csv" does not exist - please run preprocssing first.')

        try:
            self._processed_new = io.read_file(path=os.path.join(
                self._datapath, 'raw/new_dataset.csv'), datetime_cols=['start_time', 'end_time'])
        except FileNotFoundError:
            print(
                'The dataset "new_dataset.csv" does not exist - please run preprocssing first.')

        self.plz_df = gpd.read_file(
            self._datapath + '/external/plz_bremen.geojson')

    def train_duration(self):

        trips_duration = self._processed

        trips_duration['duration_min'] = trips_duration['duration_sec']/60

        X = trips_duration[['start_plz','start_place', 'max_mean_m/s']]
        y = trips_duration['duration_min']
        
        rf = RandomForestRegressor(criterion='mse', n_estimators=512, max_depth=2)
        rf.fit(X, y)

        io.save_model(rf, "model_duration")
        return

    def train_direction(self):

        # Do the magic

        return

    def train_demand(self):

        # Do the magic

        return

    def predict_duration(self):

        model = io.read_model("model_duration")
        model.score

        return

    def predict_direction(self):

        # Do the magic

        return

    def predict_demand(self):

        # Do the magic

        return
