from sklearn.naive_bayes import MultinomialNB
from string import punctuation
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import joblib
import os

class CustomTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y = None):
        return self
    
    def transform(self, text_list, label = None):
        new_text_list = text_list.copy()
        new_text_list = new_text_list.str.lower()
        new_text_list = new_text_list.str.replace('[{}]'.format(punctuation), ' ', regex=True)
        
        return new_text_list

def loadData():
    train_df = pd.read_csv(os.path.join(os.path.dirname(__file__), "data/imdb.csv"))
    return train_df

def trainModel(more_text = [], more_label = []):


    train_df = loadData()

    # add more text and label
    if len(more_text) > 0:
        train_df = pd.concat([train_df, pd.DataFrame({"text": more_text, "label": more_label})], ignore_index=True)

    pipe = make_pipeline(CustomTransformer(), CountVectorizer(), MultinomialNB())
    pipe.fit(train_df["text"], train_df["label"])

    # save the model as joblib file
    joblib.dump(pipe, "model.joblib")