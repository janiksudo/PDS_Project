from .. import io
import os
import geopandas as gpd


class Predictor:

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

        self.trips_duration = self._processed

        for col in ['start_time']:
            self.trips_duration['month'] = pd.DatetimeIndex(
                self.trips_duration['start_time']).month
            self.trips_duration['booking_date'] = self.trips_duration.start_time.dt.date
            self.trips_duration['weekdays'] = pd.DatetimeIndex(
                self.trips_duration['start_time']).weekday

        self.trips_duration['duration_min'] = self.trips_duration['duration_sec']/60
        # Feature Creation
        # Train Model
        # Dump Model

        return

    def train_direction(self):

        # Do the magic

        return

    def train_demand(self):

        # Do the magic

        return

    def predict_duration(self):

        # Do the magic

        return

    def predict_direction(self):

        # Do the magic

        return

    def predict_demand(self):

        # Do the magic

        return
