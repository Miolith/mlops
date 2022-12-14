from datasets import load_dataset
from sklearn.naive_bayes import MultinomialNB
from string import punctuation
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import joblib


def trainModel():
    class CustomTransformer(BaseEstimator, TransformerMixin):
        def fit(self, X, y = None):
            return self

        def partial_fit(self, X, y = None):
            return self
        
        def transform(self, text_list, label = None):
            new_text_list = text_list.copy()
            new_text_list = new_text_list.str.lower()
            new_text_list = new_text_list.str.replace('[{}]'.format(punctuation), ' ', regex=True)
            
            return new_text_list

    imdb_dataset = load_dataset("imdb")
    train_df = imdb_dataset["train"].to_pandas()

    pipe = make_pipeline(CustomTransformer(), CountVectorizer(), MultinomialNB())
    pipe.fit(train_df["text"], train_df["label"])

    # save the model as joblib file
    joblib.dump(pipe, "model.joblib")