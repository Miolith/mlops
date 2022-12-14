from fastapi import FastAPI
import pandas as pd
from train_model import trainModel
from load_model import loadModel
import pika
import uuid
import pymongo
import threading
from time import sleep

dbHost = "localhost"
myclient = pymongo.MongoClient("mongodb://" + dbHost + ":27017")
mydb = myclient["mydatabase"]
mycol = mydb["preddata"]
rabbitMQHost = "localhost"

app = FastAPI()

# if model.joblib is not present, train the model
try:
    pipe = loadModel()
except:
    trainModel()

pipe = loadModel()


class MQClient(object):
    internal_lock = threading.Lock()
    queue = {}

    def __init__(self, queue_id):

        self.queue_id = queue_id
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(queue="", durable=True)
        self.callback_queue = result.method.queue
        thread = threading.Thread(target=self._process_data_events)
        thread.setDaemon(True)
        thread.start()


    def _process_data_events(self):
        self.channel.basic_consume(on_message_callback=self._on_response, auto_ack=True, queue=self.callback_queue)

        while True:
            with self.internal_lock:
                self.connection.process_data_events()
                sleep(0.1)

    def _on_response(self, ch, method, props, body):
         self.queue[props.correlation_id] = body
         print(body)


    def send_request(self, payload):
        corr_id = str(uuid.uuid4())
        self.queue[corr_id] = None
        self.channel.basic_publish(exchange='',
                                   routing_key=self.queue_id,
                                   properties=pika.BasicProperties(reply_to=self.callback_queue, correlation_id=corr_id),
                                   body=payload)
        return corr_id  

mqClient = MQClient("hello")


@app.get("/")
async def read_root():
    return {"Hello": "World"}

# Send message to RabbitMQ queue and return prediction
@app.post("/predict")
async def predict(X: str):
    # generate unique id for each request
    id = str(uuid.uuid4())
    mydict = {"id":id, "text":X}
    mycol.insert_one(mydict)
    print(" [x] Sent %r" % id)
    corr_id = mqClient.send_request(id)

    while mqClient.queue[corr_id] is None:
        sleep(0.1)

    prediction = "negative" if mqClient.queue[corr_id] == b'0' else "positive"
    return {"prediction": prediction}


@app.post("/retrain")
async def retrain(X: str, y: str):
    df = pd.DataFrame([X], columns = ["text"])
    df["label"] = 1 if y == "positive" else 0
    pipe.fit(df["text"], df["label"])
    return {"status": "success"}