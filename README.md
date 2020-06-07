# PDS_Project
 
## Installation
### Prerequisites:
Prior to installing the package itself, please install it's one external dependency: `geopandas`.
This can easily be done by executing the following (assuming you have activated your conda environment):
```conda install geopandas```

### Nextbike Package:
Within the same folder as ```setup.py```run ```pip install .``` to install the package. 
Use flag ```-e``` to install in development mode. 

In subdirectory ```notebooks``` run ```pip install ..``` to install the package. 
Import via ```import nextbike```.

### Development Dependencies:
Additional dependencies for Jupyter Notebooks in the `notebooks` folder are:
```folium``` - https://python-visualization.github.io/folium/installing.html
```h3``` - https://github.com/uber/h3-py#installation

## Usage
This package implements a command line interface with three main commands:

``` 
Usage: nextbike [OPTIONS] COMMAND [ARGS]...

  This Package exposes a CLI to transform, train on and predict unseeen
  Nextbike data for various scopes.

Options:
  --help  Show this message and exit.

Commands:
  predict    Predict trip duration, direction or bike demand.
  train      Train duration, direction or demand models.
  transform  Transforms raw nNextbike format to trips-indexed format.
```

Commands have the following usage:

### Transformation to Trips:
```
Usage: nextbike transform [OPTIONS] FILENAME

  This command allows for transforming raw Nextbike data to a more human and
  machine-learning friendly format indexed by trips.

  Input             -> Output

  data/raw/FILENAME -> data/preprocessed/FILENAME

Options:
  -r, --refresh  If this flag is given, then intermediate datatsets are
                 disregarded.
```

### Training:
```
Usage: nextbike train [OPTIONS] <model>

  This command allows for training several machine-learning models for
  different scopes on preprocessed Nextbike data. A trips-indexed Nextbike
  file for the city of Bremen must exist in data/processed/.

  Duration, direction and demand models are available. Models are saved
  after training as pre-trained models in pickle format under /models/.

Options:
  -t, --resolution <temporal resolution>
                                  The temporal resolution used for resampling
                                  the data in combination with demand
                                  prediction.
```

### Prediction:
```
Usage: nextbike predict [OPTIONS] <model> FILENAME

  Predict several aspects (duration, direction and demand) of unseen
  Nextbike Data. Requires the respective trained model. Data has to be in
  trips-indexed format (use the transform command) in /data/processed/.

  When predicting the direction of trips, please specify a direction using
  the "--uni" or "--mainstation" flag. When predicting the demand of bikes,
  please specify a temporal resolution (1, 6, 12, 24).

  Predictions are saved under /data/predicted/

Options:
  --uni                           Specifies direction towards Bremen
                                  university, when predicting direction.

  --mainstation                   Specifies direction towards Bremen main
                                  station, when predicting direction.

  -t, --resolution <temporal resolution>
                                  The temporal resolution used for resampling
                                  the data in combination with demand
                                  prediction.
```

