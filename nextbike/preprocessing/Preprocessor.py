import os

from .. import io


class Preprocessor:

    cleaned = None

    def __init__(self):
        self.datapath = io.get_data_path()
        self.raw = io.read_file(path=os.path.join(self.datapath, 'raw/bremen.csv'))

    def clean_dataset(self):

        print('Cleaning data set...')

        # Drop unnecessary columns.
        self.raw.drop(columns=['Unnamed: 0'], inplace=True)

        # Filter exclusively for data points inside boundaries of Bremen.
        self.raw = self.raw[(self.raw['p_lat'] < 53.228967) &
                          (self.raw['p_lat'] > 53.011037) &
                          (self.raw['p_lng'] < 8.990582) &
                          (self.raw['p_lng'] > 8.481593)]
        print('Filtered for city of Bremen.')

        # Drop duplicates with key datetime and bike number
        self.raw = self.raw[self.raw.duplicated(subset=['datetime', 'b_number'], keep='first') == False]
        print('Duplicates of subset [datetime, bike number] dropped.')

        # Reset index to be improve its interpretability
        self.raw = self.raw.reset_index().drop(columns=['index'])
        print('Index reset.')

        # Rearange order of columns in a more intuitive order.
        self.raw = self.raw[['datetime', 'b_number', 'b_bike_type', 'p_spot', 'p_place_type',
                         'trip', 'p_uid', 'p_bikes', 'p_name',
                         'p_number', 'p_bike', 'p_lat', 'p_lng']]
        print('Order of columns rearranged.')

        # Save cleaned data set as csv in data/preprocessed.
        io.save_df(self.raw, 'bremen_cleaned')
        print('Cleaned data set saved in data/preprocessed as bremen_cleaned.csv.')
        print('Cleaning data sucessfully finished.')


    def get_cleaned(self):
        self.cleaned = io.read_file(path=os.path.join(self.datapath, 'processed/bremen_cleaned.csv'))

    def create_trips(self):
        # TODO: Janik
        pass