import click
from .model.Model import Model
import os
import pathlib
from .preprocessing.Preprocessor import Preprocessor
import sys
from nextbike.io import get_data_path


@click.group()
def cli():
    """This Package exposes a CLI to transform, train on and predict unseeen Nextbike data for various scopes."""
    pass


@cli.command(short_help='Transforms raw Nextbike format to trips-indexed format.')
@click.argument('filename', type=click.Path(), required=True)
@click.option('-r', '--refresh',
              is_flag=True,
              default=False,
              help='If this flag is given, then intermediate datatsets are disregarded.')
def transform(filename, refresh):
    """
    This command allows for transforming raw Nextbike data to a more human and machine-learning friendly format indexed by trips.

    Input             -> Output\n
    data/raw/FILENAME -> data/preprocessed/FILENAME
    """
    p = Preprocessor(filename=filename, refresh=refresh)
    p.run()


@cli.command(short_help='Train duration, direction or demand models.')
@click.argument('whatmodel', metavar='<model>',
                nargs=1,
                type=click.Choice(['duration', 'direction', 'demand']),
                required=True)
@click.option('-t', '--resolution',
              metavar='<temporal resolution>',
              type=click.Choice(['1', '6', '12', '24']),
              default=None,
              help='The temporal resolution used for resampling the data in combination with demand prediction.')
def train(whatmodel, resolution):
    """
    This command allows for training several machine-learning models for different scopes on preprocessed Nextbike data.
    A trips-indexed Nextbike file for the city of Bremen must exist in data/processed/.

    Duration, direction and demand models are available.
    Models are saved after training as pre-trained models in pickle format under /models/.
    """

    if not os.path.isfile(os.path.join(get_data_path(), 'processed/bremen.csv')):
        click.echo(
            'Could not find /data/processed/bremen.csv - please run preprocessing first using " nextbike transform".', err=True)
        sys.exit(0)

    m = Model('bremen.csv')
    if whatmodel == 'duration':
        m.train_duration()
    elif whatmodel == 'direction':
        m.train_direction_uni()
        m.train_direction_main_station()
    elif whatmodel == 'demand':
        if resolution is None:
            click.echo(
                'No temporal resolution defined, please specify using the -t/--resolution parameter.')
            sys.exit(0)
        else:
            m.train_demand(resolution +'H')


@cli.command(short_help='Predict trip duration, direction or bike demand.')
@click.argument('whatmodel', metavar='<model>',
                nargs=1,
                type=click.Choice(['duration', 'direction', 'demand']),
                required=True)
@click.option('--uni', 'direction', flag_value='uni', help='Specifies direction towards Bremen university, when predicting direction.')
@click.option('--mainstation', 'direction', flag_value='hbf', help='Specifies direction towards Bremen main station, when predicting direction.')
@click.option('-t', '--resolution',
              metavar='<temporal resolution>',
              type=click.Choice(['1', '6', '12', '24']),
              default=None,
              help='The temporal resolution used for resampling the data in combination with demand prediction.')
@click.argument('filename', type=click.Path(), required=True)
def predict(whatmodel, direction, resolution, filename):
    """
    Predict several aspects (duration, direction and demand) of unseen Nextbike Data.
    Requires the respective trained model.
    Data has to be in trips-indexed format (use the transform command) in /data/processed/.

    When predicting the direction of trips, please specify a direction using the "--uni" or "--mainstation" flag.
    When predicting the demand of bikes, please specify a temporal resolution (1, 6, 12, 24).

    Predictions are saved under /data/predicted/
    """

    m = Model(filename)
    if whatmodel == 'duration':
        m.predict_duration()
    elif whatmodel == 'direction':
        if direction is None:
            click.echo(
                'No direction defined, please specify using the --uni/--mainstation flag.')
        elif direction == 'uni':
            m.predict_direction_uni()
        elif direction == 'hbf':
            m.predict_direction_main_station()
    elif whatmodel == 'demand':
        if resolution is None:
            click.echo(
                'No temporal resolution defined, please specify using the -t/--resolution parameter.')
            sys.exit(0)
        else:
            m.predict_demand(resolution + 'H')


if __name__ == '__main__':
    cli()
