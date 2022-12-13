from fastapi import FastAPI
import pandas as pd
from train_model import pipe

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/predict")
def predict(X: str):
    df = pd.DataFrame([X], columns = ["text"])
    result = "positive" if pipe.predict(df["text"])[0] == 1 else "negative"
    return {"prediction": result}

@app.post("/retrain")
def retrain(X: str, y: str):
    df = pd.DataFrame([X], columns = ["text"])
    df["label"] = 1 if y == "positive" else 0
    pipe.fit(df["text"], df["label"])
    return {"status": "success"}