import joblib
import os

def loadModel():
    pipe = joblib.load("model.joblib")
    return pipe