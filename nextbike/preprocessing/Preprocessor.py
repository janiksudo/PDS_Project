from .. import io
import datetime
import geopandas as gpd
import numpy as np
import os
import pandas as pd
import requests
from tqdm import tqdm
from nextbike.io import get_data_path


class Preprocessor:

    _cleaned = None
    _trips = []
    _filename = ''

    def __init__(self, filename, refresh=False):
        self._refresh = refresh
        self._filename = filename
        self._prettyfilename = filename.replace('.csv', '')
        self._datapath = get_data_path()
        self._raw = io.read_file(path=os.path.join(
            self._datapath, 'raw/' + filename), datetime_cols=['datetime'])
        self.plz_df = gpd.read_file(
            self._datapath + '/external/plz_bremen.geojson')

    def _intermediateexists(self, step):
        try:
            if step == 'weather':
                path = os.path.join(self._datapath, 'external',
                                    self._prettyfilename+'_' + step + '.gz')
            elif step == 'final':
                path = os.path.join(self._datapath, 'processed',
                                    self._filename)
            else:
                path = os.path.join(self._datapath, 'processed',
                                    self._prettyfilename+'_' + step + '.csv')
            if os.path.isfile(path):
                return True
        except FileNotFoundError:
            return False

    def clean_dataset(self):

        if self._intermediateexists('cleaned') and not self._refresh:
            print('An intermediate cleaned Dataset exists. Skipping...')
            print('If you want to force re-run of preprocessing and transformation, provide the -r/--refresh option.\n')
            return

        print('Cleaning data set...')

        # Drop unnecessary columns.
        self._raw.drop(columns=['Unnamed: 0'], inplace=True)

        # Filter exclusively for data points inside boundaries of Bremen.
        self._raw = self._raw[(self._raw['p_lat'] < 53.228967) &
                              (self._raw['p_lat'] > 53.011037) &
                              (self._raw['p_lng'] < 8.990582) &
                              (self._raw['p_lng'] > 8.481593)]

        # Create geopandas data frames from data frames
        print('Filtering for city of Bremen. This can take some time depending on the computational power of your '
              'device.')
        self._raw = gpd.GeoDataFrame(self._raw, geometry=gpd.points_from_xy(self._raw.p_lng.copy(),
                                                                            self._raw.p_lat.copy()))
        self._raw.crs = "EPSG:4326"

        self._raw = gpd.sjoin(
            self._raw, self.plz_df[['geometry', 'plz']], how='left', op='within')

        # Drop null values which include all data points outside of Bremens boundaries
        self._raw = self._raw.drop(columns=['index_right']).dropna()

        print('Filtered for city of Bremen.')

        # Drop duplicates with key datetime and bike number
        self._raw = self._raw[self._raw.duplicated(
            subset=['datetime', 'b_number'], keep='first') == False]
        print('Duplicates of subset [datetime, bike number] dropped.')

        # Reset index to be improve its interpretability
        self._raw = self._raw.reset_index().drop(columns=['index'])
        print('Index reset.')

        # Rearange order of columns in a more intuitive order.
        self._raw = self._raw[['datetime', 'b_number', 'b_bike_type', 'p_spot', 'p_place_type',
                               'trip', 'p_uid', 'p_bikes', 'p_name',
                               'p_number', 'p_bike', 'p_lat', 'p_lng', 'plz']]
        print('Order of columns rearranged.')

        # Drop null values
        self._raw.dropna(inplace=True)
        print('Null values dropped.')

        # Sort data by timestamp
        self._raw['datetime'] = pd.to_datetime(
            self._raw['datetime'])  # parse timestamp to datetime
        self._raw = self._raw.sort_values('datetime')

        # Save cleaned data set as csv in data/preprocessed.
        print('Saving intermediate DataFrame in data/processed as {}_cleaned.csv.'.format(self._prettyfilename))
        io.save_df(self._raw, self._prettyfilename+'_cleaned')
        print('Cleaning data sucessfully finished.\n\n')

    def _get_cleaned(self):
        return io.read_file(path=os.path.join(self._datapath, 'processed/{}_cleaned.csv'.format(self._prettyfilename)),
                            datetime_cols=['datetime'])

    def _write_trip(self, ping, buffer):
        trip = {'bike': ping['b_number'],
                'bike_type': ping['b_bike_type'],
                'identification': ping['p_uid'],
                'start_time': buffer['datetime'],
                'end_time': ping['datetime'],
                'weekend': (0 if (buffer['datetime'].weekday() < 5) else 1),
                'duration_sec': (ping['datetime'] - buffer['datetime']).total_seconds(),
                'start_lng': buffer['p_lng'],
                'start_lat': buffer['p_lat'],
                'end_lng': ping['p_lng'],
                'end_lat': ping['p_lat'],
                'start_place': buffer['p_number'],
                'end_place': ping['p_number'],
                'start_plz': buffer['plz'],
                'end_plz': ping['plz']
                }

        self._trips.append(trip)

    def create_trips(self):

        if self._intermediateexists('trips') and not self._refresh:
            print('An intermediate Trips Dataset exists. Skipping...')
            print('If you want to force re-run of preprocessing and transformation, provide the -r/--refresh option.\n')
            return

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
        print('created', len(self._trips), 'trips.')

        # Drop all trips with duration over 24h
        self._trips = self._trips[self._trips['duration_sec'] < (24*60*60)]
        print('Droped all trips with duration over 24h.')

        # Drop round trips - trips with no differences in both start/end lng and start/end lat that are not station-bound
        print('removing round trips that are obviously not real...')
        self._trips = self._trips[~((self._trips['start_lng'] == self._trips['end_lng']) &
                                    (self._trips['start_lat'] == self._trips['end_lat']) &
                                    (self._trips['start_place'] == 0) & (self._trips['end_place'] == 0))]

        print(len(self._trips), 'trips remaining...')

        # Drop remaining round trips that are shorter (or =) 7 minutes
        print('removing sub-7 round trips...')
        self._trips = self._trips[~((self._trips['start_lng'] == self._trips['end_lng']) & (
            self._trips['start_lat'] == self._trips['end_lat']) & (self._trips['duration_sec'] <= 420))]

        print(len(self._trips), 'trips remaining...')

        # drop round trips on days that deviate more than 3 std variations away from the median (more robust than the mean)
        print('removing trips on days that deviate 3 std away from the median of trips per day...')
        tripsperday = self._trips[(self._trips['start_lng'] == self._trips['end_lng']) & (
            self._trips['start_lat'] == self._trips['end_lat'])].resample('D', on='start_time').agg({'bike': 'count'}).reset_index()
        cutoff = tripsperday.std().values[0] * 3
        tripsmean = tripsperday.median().values[0]
        dropdays = tripsperday[tripsperday['bike'] > tripsmean +
                               cutoff]['start_time'].dt.strftime('%Y-%m-%d')
        self._trips = self._trips[~((self._trips['start_time'].dt.strftime('%Y-%m-%d').isin(dropdays)) & (
            self._trips['start_lng'] == self._trips['end_lng']) & (self._trips['start_lat'] == self._trips['end_lat']))]
        print(len(self._trips), 'trips remaining...')

        # drop trips that duplicate perfectly over start_time and end_time and when this happens > 10
        print('removing trips that duplicate perfectly on start and end time...')
        duplicates = self._trips.duplicated(
            subset=['start_time', 'end_time'], keep=False)
        n_duplicates = self._trips[duplicates].groupby(['start_time', 'end_time']).agg(
            {'bike': 'count'}).reset_index().rename({'bike': 'count'}, axis=1)
        drop_starttimes = n_duplicates[n_duplicates['count']
                                       < 10]['start_time']
        self._trips = self._trips[~(
            self._trips['start_time'].isin(drop_starttimes))]

        print(len(self._trips), 'trips remaining.')

        # finally fill na values with zeros
        self._trips.fillna(0, inplace=True)

        # Save trips data set as csv in data/preprocessed.
        print('Saving intermediate DataFrame in data/processed as {}_trips.csv.'.format(self._prettyfilename))
        io.save_df(self._trips, self._prettyfilename+'_trips')
        print('Creating trips from data completed successfully.\n\n')

    def _get_trips(self):
        return io.read_file(path=os.path.join(self._datapath, 'processed/{}_trips.csv'.format(self._prettyfilename)),
                            datetime_cols=['start_time', 'end_time'])

    def _saveDwdData(self, url, path, f_name):

        # print('Download ' + f_name + ' from ' + url + ' and save to ' + path)

        file = requests.get(url)
        open(path + f_name, 'wb').write(file.content)
        file.close()

    def _getDwdData(self, url, path, f_name):

        self._saveDwdData(url, path, f_name)

        df = pd.read_csv(path + f_name, sep=';')
        # print('Created data frame of ' + f_name)

        os.remove(path + f_name)
        # print('Zip file removed: ' + path + f_name)

        return df

    def _filterForYears(self, df):

        df.rename(columns={"MESS_DATUM": "timestamp"}, inplace=True)

        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(str))

        df.set_index('timestamp', inplace=True)

        df = df[df.index.year >= 2018]

        return df

    def prepWeather(self):

        if self._intermediateexists('weather') and not self._refresh:
            print('Weather data was already fetched for this dataset. Skipping...')
            print('If you want to force re-run of preprocessing and transformation, provide the -r/--refresh option.\n')
            return

        print('Fetching and processing weather data from DWD...')

        path = os.path.join(self._datapath, 'external/')

        urls = {
            'air_temp': 'https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/air_temperature/historical/10minutenwerte_TU_00691_20100101_20191231_hist.zip',
            'air_temp_extr': 'https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_temperature/historical/10minutenwerte_extrema_temp_00691_20100101_20191231_hist.zip',
            'wind': 'https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/wind/historical/10minutenwerte_wind_00691_20100101_20191231_hist.zip',
            'wind_extr': 'https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/historical/10minutenwerte_extrema_wind_00691_20100101_20191231_hist.zip',
            'precipitation': 'https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/precipitation/historical/10minutenwerte_nieder_00691_20100101_20191231_hist.zip'
        }

        air_temp = self._getDwdData(urls['air_temp'], path, 'air_temp.zip')

        air_temp_extr = self._getDwdData(
            urls['air_temp_extr'], path, 'air_temp_extr.zip')

        wind = self._getDwdData(urls['wind'], path, 'wind.zip')

        wind_extr = self._getDwdData(urls['wind_extr'], path, 'wind_extr.zip')

        precipitation = self._getDwdData(
            urls['precipitation'], path, 'precipitation.zip')

        print('Cleaning air_temp...')

        air_temp = self._filterForYears(air_temp)

        # Drop unnecessary columns
        air_temp.drop(columns={'STATIONS_ID', '  QN',
                               'PP_10', 'eor'}, inplace=True)

        # Assign interpretable column names
        air_temp.rename(columns={"TT_10": "temp_2m", "TM5_10": "temp_5cm",
                                 "RF_10": "humidity_2m", "TD_10": "dew_point_2m"}, inplace=True)
        air_temp.drop(columns={'temp_5cm'}, inplace=True)

        air_temp.replace(-999, float('NaN'), inplace=True)
        air_temp.dropna(inplace=True)

        print('Cleaning air_temp_extr...')

        air_temp_extr = self._filterForYears(air_temp_extr)

        # Drop unnecessary columns
        air_temp_extr.drop(
            columns=['STATIONS_ID', '  QN', 'eor'], inplace=True)

        # Assign interpretable column names

        air_temp_extr.rename(columns={'TX_10': 'max_at_2m', 'TX5_10': 'max_at_5cm',
                                      'TN_10': 'min_at_2m', 'TN5_10': 'min_at_5cm'}, inplace=True)
        air_temp_extr.drop(columns={'min_at_2m', 'min_at_5cm'}, inplace=True)
        air_temp_extr.drop(columns={'max_at_5cm'}, inplace=True)

        air_temp_extr.replace(-999, float('NaN'), inplace=True)
        air_temp_extr.dropna(inplace=True)

        print('Cleaning wind...')

        wind = self._filterForYears(wind)

        # Drop unnecessary columns
        wind.drop(columns={'STATIONS_ID', '  QN', 'eor'}, inplace=True)

        # Assign interpretable column names
        wind.rename(columns={'FF_10': 'mean_speed_h/s',
                             'DD_10': 'direction_degree'}, inplace=True)

        wind.replace(-999, float('NaN'), inplace=True)
        wind.dropna(inplace=True)

        print('Cleaning wind_extr...')

        wind_extr = self._filterForYears(wind_extr)

        # Drop unnecessary columns
        wind_extr.drop(columns={'STATIONS_ID', '  QN', 'eor'}, inplace=True)

        # Assign interpretable column names
        wind_extr.rename(columns={'FX_10': 'max_m/s', 'FNX_10': 'min_mean_m/s',
                                  'FMX_10': 'max_mean_m/s', 'DX_10': 'direction_degree'}, inplace=True)

        wind_extr.replace(-999, float('NaN'), inplace=True)
        wind_extr.dropna(inplace=True)

        print('Cleaning precipitation...')

        precipitation = self._filterForYears(precipitation)

        # Drop unnecessary columns
        precipitation.drop(
            columns={'STATIONS_ID', '  QN', 'eor', 'RWS_IND_10'}, inplace=True)

        # Assign interpretable column names
        precipitation.rename(
            columns={'RWS_DAU_10': 'min', 'RWS_10': 'mm'}, inplace=True)

        precipitation.replace(-999, float('NaN'), inplace=True)
        precipitation.dropna(inplace=True)

        print('Merging all weather data...')

        all_weather = pd.merge(air_temp, air_temp_extr, on='timestamp')

        all_weather = pd.merge(all_weather, wind, on='timestamp')

        all_weather = pd.merge(all_weather, wind_extr, on='timestamp')

        all_weather = pd.merge(all_weather, precipitation, on='timestamp')

        all_weather.to_csv(path + self._prettyfilename +
                           '_weather.gz', compression='gzip')

        print('Getting and cleaning of weather data successful!')
        print('Weather Data saved as ' + path +
              '{}_weather.gz'.format(self._prettyfilename))
        print('\nTo import the data use the following command:')
        print("pd.read_csv(path + 'external/{}_weather.gz', index_col='timestamp')".format(self._prettyfilename))

    def _get_weather(self):
        return pd.read_csv(os.path.join(self._datapath, 'external/{}_weather.gz'.format(self._prettyfilename)))

    def mergeWeatherTrips(self, trips, weather):

        if self._intermediateexists('final') and not self._refresh:
            print('A processed version of the dataset {} exists. Skipping...'.format(
                self._filename))
            print('If you want to force re-run of preprocessing and transformation, provide the -r/--refresh option.\n')
            return

        weather['timestamp'] = pd.to_datetime(weather['timestamp'])

        # Floor start time to next 10 minutes so we can merge it with weather data

        trips['sTime_floored'] = pd.to_datetime(
            trips['start_time']).dt.floor('10T')
        trips['sTime_floored'] = pd.to_datetime(trips['sTime_floored'])
        data = trips.merge(right=weather, left_on='sTime_floored',
                           right_on='timestamp', how='left')
        data.drop(columns=['sTime_floored'], inplace=True)
        print("Trip and weather data merged")
        print("Clean data...")
        data.drop(columns=["bike_type", "mm", "timestamp"], inplace=True)
        data.dropna(inplace=True)

        # save to /data/processed
        io.save_df(data, self._filename)
        print('Done with preprocessing and transformation!')

    def run(self):
        self.clean_dataset()
        self.create_trips()
        self.prepWeather()
        trips = self._get_trips()
        weather = self._get_weather()
        self.mergeWeatherTrips(trips, weather)
