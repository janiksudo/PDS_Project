from .. import io
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import os
import pandas as pd
import geopandas as gpd
from math import sin, cos, sqrt, atan2, radians
from nextbike.io import get_data_path
from tqdm import tqdm


class Model:

    _export_attributes = [
        'bike',
        'identification',
        'start_time',
        'end_time',
        'weekend',
        'duration_sec',
        'start_lng',
        'start_lat',
        'end_lng',
        'end_lat',
        'start_place',
        'end_place',
        'start_plz',
        'end_plz'
    ]

    def __init__(self, filename):
        self._datapath = get_data_path()
        self._filename = filename

    def train_duration(self):

        try:
            trips_duration = io.read_file(path=os.path.join(
                self._datapath, 'processed', self._filename), datetime_cols=['start_time', 'end_time'])
        except FileNotFoundError:
            print(
                'The dataset data/processed/{} does not exist - please run preprocessing first.'.format(self._filename))
            return

        print('Generating features...')

        trips_duration['duration_min'] = trips_duration['duration_sec']/60

        X = trips_duration[['start_plz', 'start_place', 'max_mean_m/s']]
        y = trips_duration['duration_min']

        rf = RandomForestRegressor(
            criterion='mse', n_estimators=512, max_depth=2)

        print('Training model...')
        rf.fit(X, y)

        io.save_model(rf, "model_duration")

        print('Model saved.')

    def train_direction_uni(self):

        try:
            trips_direction = io.read_file(path=os.path.join(
                self._datapath, 'processed', self._filename), datetime_cols=['start_time', 'end_time'])
        except FileNotFoundError:
            print(
                'The dataset data/processed/{} does not exist - please run preprocessing first.'.format(self._filename))
            return

        print('Working on Direction -> University...')

        trips_direction["start_time"] = pd.to_datetime(
            trips_direction["start_time"])

        # Lists of target variables
        to_uni = []
        to_uni_bool = []

        # Lists of features
        hour = []

        # Iterrate through df and add features to feature lists
        for index, row in tqdm(trips_direction.iterrows(), total=len(trips_direction), desc='Calculating distances:'):

            dist_to_uni = self.distanceToUni(
                row['start_lng'], row['start_lat'], row['end_lng'], row['end_lat'])

            # Save datetime information
            hour.append(row['start_time'].hour)

            # Save distances to corresponding list
            to_uni.append(dist_to_uni)

            if dist_to_uni < 0:
                to_uni_bool.append(0)
            else:
                to_uni_bool.append(1)

        # Add columns to df
        trips_direction['to_uni'] = to_uni
        trips_direction['to_uni_bool'] = to_uni_bool
        trips_direction['hour'] = hour

        # Initialize independent and target variables
        X_uni = trips_direction[['start_lng', 'start_lat',
                                 'humidity_2m', 'dew_point_2m', 'max_mean_m/s', 'hour']]
        y_uni = trips_direction['to_uni_bool']

        print('Training model...')

        # Train RandomForestClassifier with optimzed hyperparameters through grid search (see notebook #8)
        rf_uni = RandomForestClassifier(
            criterion='entropy', class_weight='balanced_subsample', n_estimators=256, max_depth=7)
        rf_uni.fit(X_uni, y_uni)

        # Save model
        io.save_model(rf_uni, "model_direction_uni")
        print('Model saved.')

    def train_direction_main_station(self):

        try:
            trips_direction = io.read_file(path=os.path.join(
                self._datapath, 'processed', self._filename), datetime_cols=['start_time', 'end_time'])
        except FileNotFoundError:
            print(
                'The dataset data/processed/{} does not exist - please run preprocessing first.'.format(self._filename))
            return

        print('Working on Direction -> Main Station...')

        trips_direction["start_time"] = pd.to_datetime(
            trips_direction["start_time"])

        # Lists of target variables
        to_main_station = []
        to_main_station_bool = []

        # Lists of features
        hour = []

        # Iterrate through df and add features to feature lists
        for index, row in tqdm(trips_direction.iterrows(), total=len(trips_direction), desc='Calculating distances:'):

            dist_to_main_station = self.distanceToMainStation(
                row['start_lng'], row['start_lat'], row['end_lng'], row['end_lat'])

            # Save datetime information
            hour.append(row['start_time'].hour)

            # Save distances to corresponding list
            to_main_station.append(dist_to_main_station)

            if dist_to_main_station < 0:
                to_main_station_bool.append(0)
            else:
                to_main_station_bool.append(1)

        # Add columns to df
        trips_direction['to_main_station'] = to_main_station
        trips_direction['to_main_station_bool'] = to_main_station_bool
        trips_direction['hour'] = hour

        # Initialize independent and target variables
        X_main_station = trips_direction[[
            'start_lng', 'start_plz', 'humidity_2m', 'dew_point_2m', 'max_m/s', 'hour']]
        y_main_station = trips_direction['to_main_station_bool']

        print('Training model...')

        # Train RandomForestClassifier with optimzed hyperparameters through grid search (see notebook #8)
        rf_main_station = RandomForestClassifier(
            criterion='entropy', class_weight='balanced_subsample', n_estimators=256, max_depth=7)
        rf_main_station.fit(X_main_station, y_main_station)

        # Save model
        io.save_model(rf_main_station, 'model_direction_main_station')
        print('Model saved.')

    # data by timespan 24H, 1H, 4H, 12H
    def _setDataset(self, dataset, temp_resol, columnnamegroupby, functions_dic):
        return dataset.resample(
            temp_resol, on=columnnamegroupby).agg(functions_dic)

    def train_demand(self, resolution):

        try:
            trips_demand = io.read_file(path=os.path.join(
                self._datapath, 'processed', self._filename), datetime_cols=['start_time', 'end_time'])
        except FileNotFoundError:
            print(
                'The dataset data/processed/{} does not exist - please run preprocessing first.'.format(self._filename))
            return

        print('Generating features...')

        for col in ['start_time']:
            trips_demand['month'] = pd.DatetimeIndex(
                trips_demand['start_time']).month
            trips_demand['booking_date'] = trips_demand.start_time.dt.date
            trips_demand['weekdays'] = pd.DatetimeIndex(
                trips_demand['start_time']).weekday
            trips_demand['hour'] = trips_demand['start_time'].dt.hour

        features = ['month', "hour", 'temp_2m', "min"]

        trips_demand['number_bookings'] = 1

        trips_demand = self._setDataset(trips_demand, resolution, "start_time", {
                                        "number_bookings": "count", "month": "mean",  "hour": "mean", "temp_2m": "mean", "min": "mean"})
        trips_demand.dropna(axis=0, inplace=True)

        X = trips_demand[features]
        y = trips_demand['number_bookings']

        switch = {
            '1H': 5,
            '6H': 3,
            '12H': 2,
            '24H': 1
        }

        poly_features = PolynomialFeatures(
            degree=switch.get(resolution), include_bias=False)
        X_poly = poly_features.fit_transform(X)

        poly_reg = LinearRegression()

        print('Training model...')
        poly_reg.fit(X_poly, y)

        io.save_model(poly_reg, "model_demand_" + resolution)

        print('Model saved.')

    def predict_duration(self):

        try:
            trips_duration = io.read_file(path=os.path.join(
                self._datapath, 'processed', self._filename), datetime_cols=['start_time', 'end_time'])
        except FileNotFoundError:
            print(
                'The dataset data/processed/{} does not exist - please run preprocessing first.'.format(self._filename))
            return

        print('Generating features...')

        trips_duration['duration_min'] = trips_duration['duration_sec']/60

        X = trips_duration[['start_plz', 'start_place', 'max_mean_m/s']]

        model = io.read_model("model_duration")
        trips_duration['prediction'] = model.predict(X)

        # extend the usual export with additional features used in this prediction
        export_attributes = self._export_attributes + \
            ['max_mean_m/s', 'prediction']

        io.save_prediction(
            trips_duration[export_attributes], 'duration_prediction')
        print('Saved prediction for further evaluation.')

    # This function predicts for each trip in the data set new_data.csv if its direction is toward the university of Bremen.
    def predict_direction_uni(self):

        try:
            trips_direction = io.read_file(path=os.path.join(
                self._datapath, 'processed', self._filename), datetime_cols=['start_time', 'end_time'])
        except FileNotFoundError:
            print(
                'The dataset data/processed/{} does not exist - please run preprocessing first.'.format(self._filename))
            return

        trips_direction["start_time"] = pd.to_datetime(
            trips_direction["start_time"])

        print('Generating features...')

        # Lists of target variables
        to_uni = []
        to_uni_bool = []

        # Lists of features
        hour = []

        # Iterrate through df and add features to feature lists
        for index, row in tqdm(trips_direction.iterrows(), total=len(trips_direction), desc='Calculating distances:'):

            dist_to_uni = self.distanceToUni(
                row['start_lng'], row['start_lat'], row['end_lng'], row['end_lat'])

            # Save datetime information
            hour.append(row['start_time'].hour)

            # Save distances to corresponding list
            to_uni.append(dist_to_uni)

            if dist_to_uni < 0:
                to_uni_bool.append(0)
            else:
                to_uni_bool.append(1)

        # Add columns to df
        trips_direction['to_uni'] = to_uni
        trips_direction['to_uni_bool'] = to_uni_bool
        trips_direction['hour'] = hour

        print('Predicting if trips are in direction to uni.')
        # Initialize independent and target variables
        X = trips_direction[['start_lng', 'start_lat',
                             'humidity_2m', 'dew_point_2m', 'max_mean_m/s', 'hour']]

        # Load prediction model
        model = io.read_model("model_direction_uni")
        trips_direction['prediction_to_uni'] = model.predict(X)

        # extend the usual export with additional features used in this prediction
        export_attributes = self._export_attributes + \
            ['humidity_2m', 'dew_point_2m', 'max_mean_m/s',
                'hour', 'prediction_to_uni']

        io.save_prediction(
            trips_direction[export_attributes], 'direction_prediction_uni')
        print('Saved prediction for further evaluation.')

    # This function predicts for each trip in the data set new_data.csv if its direction is toward the main station of Bremen.
    def predict_direction_main_station(self):

        try:
            trips_direction = io.read_file(path=os.path.join(
                self._datapath, 'processed', self._filename), datetime_cols=['start_time', 'end_time'])
        except FileNotFoundError:
            print(
                'The dataset data/processed/{} does not exist - please run preprocessing first.'.format(self._filename))
            return

        trips_direction["start_time"] = pd.to_datetime(
            trips_direction["start_time"])

        # Lists of target variables
        to_main_station = []
        to_main_station_bool = []

        # Lists of features
        hour = []

        # Iterrate through df and add features to feature lists
        for index, row in tqdm(trips_direction.iterrows(), total=len(trips_direction), desc='Calculating distances:'):

            dist_to_main_station = self.distanceToMainStation(
                row['start_lng'], row['start_lat'], row['end_lng'], row['end_lat'])

            # Save datetime information
            hour.append(row['start_time'].hour)

            # Save distances to corresponding list
            to_main_station.append(dist_to_main_station)

            if dist_to_main_station < 0:
                to_main_station_bool.append(0)
            else:
                to_main_station_bool.append(1)

        # Add columns to df
        trips_direction['to_main_station'] = to_main_station
        trips_direction['to_main_station_bool'] = to_main_station_bool
        trips_direction['hour'] = hour

        print('Predicting if trips are in direction to main station.')
        # Initialize independent and target variables
        X = trips_direction[['start_lng', 'start_plz',
                             'humidity_2m', 'dew_point_2m', 'max_m/s', 'hour']]

        # Load prediction model
        model = io.read_model("model_direction_main_station")
        trips_direction['prediction_to_main_station'] = model.predict(X)

        # extend the usual export with additional features used in this prediction
        export_attributes = self._export_attributes + \
            ['humidity_2m', 'dew_point_2m', 'max_m/s',
                'hour', 'prediction_to_main_station']

        io.save_prediction(
            trips_direction[export_attributes], 'direction_prediction_main_station')
        print('Saved prediction for further evaluation.')

    def predict_demand(self, resolution):

        try:
            trips_demand = io.read_file(path=os.path.join(
                self._datapath, 'processed', self._filename), datetime_cols=['start_time', 'end_time'])
        except FileNotFoundError:
            print(
                'The dataset data/processed/{} does not exist - please run preprocessing first.'.format(self._filename))
            return

        for col in ['start_time']:
            trips_demand['month'] = pd.DatetimeIndex(
                trips_demand['start_time']).month
            trips_demand['booking_date'] = trips_demand.start_time.dt.date
            trips_demand['weekdays'] = pd.DatetimeIndex(
                trips_demand['start_time']).weekday
            trips_demand['hour'] = trips_demand['start_time'].dt.hour

        features = ['month', "hour", 'temp_2m', "min"]

        trips_demand['number_bookings'] = 1

        trips_demand = self._setDataset(trips_demand, resolution, "start_time", {
                                        "number_bookings": "count", "month": "mean",  "hour": "mean", "temp_2m": "mean", "min": "mean"})
        trips_demand.dropna(axis=0, inplace=True)

        X = trips_demand[features]

        switch = {
            '1H': 5,
            '6H': 3,
            '12H': 2,
            '24H': 1
        }

        poly_features = PolynomialFeatures(
            degree=switch.get(resolution), include_bias=False)
        X_poly = poly_features.fit_transform(X)

        model = io.read_model("model_demand_" + resolution)

        trips_demand['prediction_' + resolution] = model.predict(X_poly)

        io.save_prediction(
            trips_demand, 'demand_prediction_' + resolution)

        print('Saved prediction for further evaluation.')

    # Function that calculates the difference of the distances of start and end location to University of Bremen.
    # Returns the difference of the distances of the start and end location in kilometers.
    # If value positive, end locations is closer to university. That means moved towards university.
    def distanceToUni(self, sLng, sLat, eLng, eLat):
        # approximate radius of earth in km
        R = 6373.0

        sLng = radians(sLng)
        sLat = radians(sLat)
        eLng = radians(eLng)
        eLat = radians(eLat)
        uLat = radians(53.1069302)  # University of Bremen Latitude
        uLng = radians(8.8499603)  # University of Bremen Longitude

        sdlon = uLng - sLng
        sdlat = uLat - sLat

        edlon = uLng - eLng
        edlat = uLat - eLat

        sA = sin(sdlat / 2)**2 + cos(sLat) * cos(uLat) * sin(sdlon / 2)**2
        eA = sin(edlat / 2)**2 + cos(eLat) * cos(uLat) * sin(edlon / 2)**2

        sC = 2 * atan2(sqrt(sA), sqrt(1 - sA))
        eC = 2 * atan2(sqrt(eA), sqrt(1 - eA))

        sDist = R * sC
        eDist = R * eC

        distance = sDist - eDist

        return distance

    # Function that calculates the difference of the distances of start and end location to the main station.
    # Returns the difference of the distances of the start and end location in kilometers.
    # If value positive, end locations is closer to the main station. That means moved towards the main station.

    def distanceToMainStation(self, sLng, sLat, eLng, eLat):
        # approximate radius of earth in km
        R = 6373.0

        sLng = radians(sLng)
        sLat = radians(sLat)
        eLng = radians(eLng)
        eLat = radians(eLat)
        msLat = radians(53.083122)  # Main station Latitude
        msLng = radians(8.813717)  # Main station Latitude

        sdlon = msLng - sLng
        sdlat = msLat - sLat

        edlon = msLng - eLng
        edlat = msLat - eLat

        sA = sin(sdlat / 2)**2 + cos(sLat) * cos(msLat) * sin(sdlon / 2)**2
        eA = sin(edlat / 2)**2 + cos(eLat) * cos(msLat) * sin(edlon / 2)**2

        sC = 2 * atan2(sqrt(sA), sqrt(1 - sA))
        eC = 2 * atan2(sqrt(eA), sqrt(1 - eA))

        sDist = R * sC
        eDist = R * eC

        distance = sDist - eDist

        return distance
