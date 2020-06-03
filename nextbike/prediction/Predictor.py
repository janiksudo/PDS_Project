from .. import io
import os
import geopandas as gpd

class Predictor:

    def __init__(self, data_path):
        self._datapath = data_path
        self._raw = io.read_file(path=os.path.join(self._datapath, 'raw/bremen.csv'), datetime_cols=['datetime'])
        self._raw_new = io.read_file(path=os.path.join(self._datapath, 'raw/new_data.csv'), datetime_cols=['datetime'])
        self.plz_df = gpd.read_file(self._datapath + '/external/plz_bremen.geojson')


    def train(self):

        # Do the magic

        return

    def transform(self):

        # Do the magic

        return


    def predict(self):

        # Do the magic

        return
