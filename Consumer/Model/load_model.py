import joblib

def loadModel():
    pipe = joblib.load("model.joblib")
    return pipe