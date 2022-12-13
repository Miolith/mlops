from fastapi import FastAPI
import pandas as pd
from train_model import pipe
import pika

app = FastAPI()

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
qd = channel.queue_declare(queue="", durable=True)
callback_queue = qd.method.queue

@app.get("/")
def read_root():
    return {"Hello": "World"}

"""
@app.post("/predict")
def predict(X: str):
    df = pd.DataFrame([X], columns = ["text"])
    result = "positive" if pipe.predict(df["text"])[0] == 1 else "negative"
    return {"prediction": result}
"""

# Send message to RabbitMQ queue and return prediction
@app.post("/predict")
def predict(X: str):
    channel.basic_publish(exchange='', routing_key='hello', body=X, properties=pika.BasicProperties(
        delivery_mode=2,
        reply_to=callback_queue)
    )

    # Wait for response
    result = ""
    def callback(ch, method, properties, body):
        result = body
        ch.stop_consuming()

    channel.basic_consume(queue=callback_queue, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

    return {"prediction": result}


@app.post("/retrain")
def retrain(X: str, y: str):
    df = pd.DataFrame([X], columns = ["text"])
    df["label"] = 1 if y == "positive" else 0
    pipe.fit(df["text"], df["label"])
    return {"status": "success"}