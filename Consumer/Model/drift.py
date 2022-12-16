from .load_model import loadModel
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

def detect_drift(X_train, X_prod, min_accuracy=0.5):
    """
    Detect distribution drift
    
    In this function, we train the model to distinguish between the training data and the production data.
    If the accuracy is greater than 0.5, then there is a drift.
    """
    size = min(len(X_train), len(X_prod))
    
    if size < 100:
        return False
    
    clf = loadModel()

    # First we sample X_train and X_prod to make sure they have the same length
    if len(X_train) > len(X_prod):
        X_train = X_train.sample(n=size)
    else:
        X_prod = X_prod.sample(n=size)

    y_train = [0] * size
    y_prod = [1] * size

    X = pd.concat([X_train, X_prod], ignore_index=True)
    y = pd.Series(y_train + y_prod)

    # split the data into train and test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4,
                                                              stratify=y,
                                                              shuffle=True)
    
    # train the model
    clf.fit(X_train, y_train)

    # predict
    y_pred = clf.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)

    return accuracy > min_accuracy
