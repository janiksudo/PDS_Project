import os
import datetime
import pandas as pd
from tqdm import tqdm

from .. import io


class Preprocessor:

    _cleaned = None
    _trips = []

    def __init__(self, data_path):
        self._datapath = data_path
        self._raw = io.read_file(path=os.path.join(self._datapath, 'raw/bremen.csv'))

    def clean_dataset(self):

        print('Cleaning data set...')

        # Drop unnecessary columns.
        self._raw.drop(columns=['Unnamed: 0'], inplace=True)

        # Filter exclusively for data points inside boundaries of Bremen.
        self._raw = self._raw[(self._raw['p_lat'] < 53.228967) &
                              (self._raw['p_lat'] > 53.011037) &
                              (self._raw['p_lng'] < 8.990582) &
                              (self._raw['p_lng'] > 8.481593)]
        print('Filtered for city of Bremen.')

        # Drop duplicates with key datetime and bike number
        self._raw = self._raw[self._raw.duplicated(subset=['datetime', 'b_number'], keep='first') == False]
        print('Duplicates of subset [datetime, bike number] dropped.')

        # Reset index to be improve its interpretability
        self._raw = self._raw.reset_index().drop(columns=['index'])
        print('Index reset.')

        # Rearange order of columns in a more intuitive order.
        self._raw = self._raw[['datetime', 'b_number', 'b_bike_type', 'p_spot', 'p_place_type',
                         'trip', 'p_uid', 'p_bikes', 'p_name',
                         'p_number', 'p_bike', 'p_lat', 'p_lng']]
        print('Order of columns rearranged.')

        # Drop null values
        self._raw.dropna(inplace=True)
        print('Null values dropped.')

        # Save cleaned data set as csv in data/preprocessed.
        io.save_df(self._raw, 'bremen_cleaned')
        print('Cleaned data set saved in data/processed as bremen_cleaned.csv.')
        print('Cleaning data sucessfully finished.')

    def _get_cleaned(self):
        return io.read_file(path=os.path.join(self._datapath, 'processed/bremen_cleaned.csv'))

    def _write_trip(self, ping, buffer):
        trip = {'bike': ping['b_number'],
                'bike_type': ping['b_bike_type'],
                'start_time': buffer['datetime'],
                'end_time': ping['datetime'],
                'duration_sec': (ping['datetime'] - buffer['datetime']).total_seconds(),
                'start_lng': buffer['p_lng'],
                'start_lat': buffer['p_lat'],
                'end_lng': ping['p_lng'],
                'end_lat': ping['p_lat'],
                'start_place': buffer['p_number'],
                'end_place': ping['p_number']
                }

        self._trips.append(trip)

    def create_trips(self):

        print('Creating Trips from cleaned bike pings...')

        self._cleaned = self._get_cleaned()
        ordered = self._cleaned.sort_values(['b_number', 'datetime'], axis=0)

        buffer = None

        for index, ping in tqdm(ordered.iterrows(), total=len(ordered), desc='Finished rows:'):

            bike = ping['b_number']
            trip = ping['trip']
            time = ping['datetime']
            lat = ping['p_lat']
            lng = ping['p_lng']

            if buffer is not None:

                buffer_bike = buffer['b_number']
                if bike != buffer_bike:
                    # if records of the next bike start, overwrite buffer and continue
                    buffer = ping
                    continue

                buffer_trip = buffer['trip']
                buffer_time = buffer['datetime']
                buffer_lat = buffer['p_lat']
                buffer_lng = buffer['p_lng']

                if trip == 'first' and buffer_trip == 'last':
                    # check for midnight trip
                    if buffer_time.time() != datetime.time(23, 59) and time.time() != datetime.time(0, 0):

                        # this was not just a checkout/checkin ping
                        # now check if the bike has moved
                        moved = (lat != buffer_lat) | (lng != buffer_lng)
                        if moved:
                            self._write_trip(ping, buffer)
                            buffer = None
                            # TODO: roundtrips over midnight to a station vs. that station going offline?

                elif trip == 'end' and buffer_trip == 'start':
                    # write trip, discard buffer and continue
                    self._write_trip(ping, buffer)
                    buffer = None

                buffer = ping

            else:
                if trip == 'last' or trip == 'start':
                    # only write buffer and start a potential trip with last and start trip attribute
                    buffer = ping

        self._trips = pd.DataFrame.from_records(self._trips)

        # Save trips data set as csv in data/preprocessed.
        io.save_df(self._trips, 'trips')
        print('Trips data set saved in data/processed as trips.csv.')
        print('Creating trips from data completed successfully.')
