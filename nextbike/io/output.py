from .utils import *
import os
import pickle


def save_model(model, modelName):
    with open(os.path.join(get_model_path(), '' + modelName + '.pkl'), 'wb') as pickle_file:
        pickle.dump(model, pickle_file)

def save_df(df, name):
    df.to_csv(os.path.join(get_data_path(), 'processed/' + name + '.csv'), index=False)
