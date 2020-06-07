from .utils import *
import os
import pickle


def save_model(model, modelName):
    with open(os.path.join(get_model_path(), '' + modelName + '.pkl'), 'wb') as pickle_file:
        pickle.dump(model, pickle_file)


def save_df(df, name):
    path = os.path.join(get_data_path(), 'processed/' +
                        name.replace('.csv', '') + '.csv')
    df.to_csv(path, index=False)
    print('Dataframe saved to', path)


def save_prediction(df, name):
    path = os.path.join(get_data_path(), 'predicted/' +
                        name.replace('.csv', '') + '.csv')
    df.to_csv(path, index=False)
    print('Prediction saved to', path)
