from .utils import get_data_path
import os
import pickle


def save_model(model):
    pickle.dump(model, open(os.path.join(get_data_path(), "output/model.pkl"), 'wb'))

def save_df(df, name):
    df.to_csv(os.path.join(get_data_path(), 'processed/' + name + '.csv'), index=False)
