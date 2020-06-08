![](https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Nextbike_Logo.svg/2000px-Nextbike_Logo.svg.png)

# The Nextbike Package
## Introduction
This package implements typical transformation and cleaning steps that are useful when working with raw Nextbike data.
This package also implements various machine-learning models for different targets that can be used (when trained) on unseen/new Nextbike data.

## Installation
### Prerequisites:
Prior to installing the package itself, please install it's one external dependency: `geopandas`.
This can easily be done by executing the following (assuming you have activated your conda environment):
```conda install geopandas``` (https://geopandas.org/install.html)

### Nextbike Package:
Within the same folder as ```setup.py```run ```pip install .``` to install the package. 
Use flag ```-e``` to install in development mode. 

In subdirectory ```notebooks``` run ```pip install ..``` to install the package. 
Import via ```import nextbike```.

### Development Dependencies:
Additional dependencies for Jupyter Notebooks in the `notebooks` folder are:

```folium``` - https://python-visualization.github.io/folium/installing.html or `conda install folium`

```h3``` - https://github.com/uber/h3-py#installation or `pip install h3`

### Alternative using environment.yml:
Install everything at once using `conda env create -f environment.yml` from the root directory of this project.
This assumes an installation of (mini)conda.

## Usage
The usual workflow is as follows:
1. **Transform** both the training data (e.g. `bremen.csv`) and the unseen/new data (e.g. `bremen_test.csv`). These need to be in `/data/raw/`.

1. **Train** on the processed (now in `/data/processed/`) training data. (no need to specify filename)
    * Both the models `duration` and `direction`  do not need an additional parameter.
    * `demand` takes an additional parameter `--resolution` or short `-t` that specifies the temporal resolution, the model should be trained on. 
    
        (Usage: `nextbike train -t 12 demand` for a demand model with temporal resolution of 12 hours)

    **Training won't work without doing step 1 first.**

1. **Predict** processed (now in `/data/processed/`) unseen/new data with a specified filename (e.g. `bremen_test.csv`)
    * The model `duration` does not need an additional parameter.
    * The model `direction` requires a flag (either `--uni` or `--mainstation` to be set as an option) to know which direction to predict.

        (Usage: `nextbike predict --uni direction` for a prediction wheter a trip is headed towards the University of Bremen)
    * The model `demand` takes the same additional parameter as with training.
    
    **Prediction won't work without doing steps 1 and 2 first.**
    
If the user does not want to predict stuff, but rather only wants to use the transformation of raw Nextbike data to a more human-friendly format indexed by trips, step 1 provides an intermediate DataFrame named `FILENAME_trips.csv` under `/data/processed/`.

### Command-Line Interface
This package implements a command line interface for the three main commands used during a typical workflow.

Commands have the following usage (this can also be displayed using the `--help` option for each sub-command):

#### Transformation to Trips:
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

#### Training:
```
Usage: nextbike train [OPTIONS] <model>

  This command allows for training several machine-learning models for
  different scopes on preprocessed Nextbike data. A trips-indexed Nextbike
  file for the city of Bremen must exist in data/processed/.

  Duration, direction and demand models are available. Models are saved
  after training as pre-trained models in pickle format under /models/.

Options:
  -t, --resolution <temporal resolution>
                                  The temporal resolution in hours used for resampling
                                  the data in combination with demand
                                  prediction. (1, 6, 12 or 24)
```

#### Prediction:
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

### Caveats:

#### pip vs pip3
Please ensure that there is only Python 3 installed in your environment. Python 2 installations and bad aliases can cause pip installs to fail because pip links to python instead of python3.

#### installation of folium and geopandas
Folium and Geopandas do not provide pre-built wheels (at least not through pip) for each operating system and have a lot of requirements that cannot just be installed by doing a `pip install`.
In most cases this can be fixed by using the conda package manager to install them, because there, pre-built wheels do exist.
Otherwise please follow the installation instructions for your operating system and install dependencies of these two packages **before** installing them.
