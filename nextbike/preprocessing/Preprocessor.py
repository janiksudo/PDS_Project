import os

from .. import io


class Preprocessor:

    cleaned = None

    def __init__(self):
        self.datapath = io.get_data_path()
        self.raw = io.read_file(path=os.path.join(self.datapath, 'raw/bremen.csv'))

    def clean_dataset(self):
        # TODO: Tim
        pass

    def get_cleaned(self):
        self.cleaned = io.read_file(path=os.path.join(self.datapath, 'processed/bremen_cleaned.csv'))

    def create_trips(self):
        # TODO: Janik
        pass
