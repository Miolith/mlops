from fastapi import FastAPI
import pandas as pd
import pika
import uuid
import pymongo
import threading
from time import sleep
import random
import os

queueName = os.environ.get("QUEUE_NAME")
rabbitMQHost = os.environ.get("RABBITMQ_HOST")
dbHost = os.environ.get("DB_HOST")

myclient = pymongo.MongoClient("mongodb://" + dbHost + ":27017")
mydb = myclient["mydatabase"]
mycol = mydb["preddata"]
retrain_col = mydb["retraindata"]


app = FastAPI()



class MQClient(object):
    internal_lock = threading.Lock()
    queue = {}

    def __init__(self):

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


    def send_request(self, queue_id, payload):
        corr_id = str(uuid.uuid4())
        self.queue[corr_id] = None
        self.channel.basic_publish(exchange='',
                                   routing_key=queue_id,
                                   properties=pika.BasicProperties(reply_to=self.callback_queue, correlation_id=corr_id),
                                   body=payload)
        return corr_id  

mqClient = MQClient()


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
    corr_id = mqClient.send_request(queueName, id)

    while mqClient.queue[corr_id] is None:
        sleep(0.1)

    prediction = "negative" if mqClient.queue[corr_id] == b'0' else "positive"
    return {"prediction": prediction}


@app.post("/retrain")
async def retrain(X: str, y: str):
    label = 0 if y == "negative" else 1
    id = str(uuid.uuid4())
    mydict = {"id":id, "text":X, "label":label}
    retrain_col.insert_one(mydict)

    mqClient.send_request("retrain", id)

    return {"status": "success"}

@app.get("/drift_detection")
async def drift_detection():

    id = str(uuid.uuid4())
    corr_id = mqClient.send_request("drift", id)

    while mqClient.queue[corr_id] is None:
        sleep(0.1)
    
    return {"drift": mqClient.queue[corr_id] == b'1'}

@app.get("/generate_drift")
async def force_drift():
    
    vocab = ['Abstruse', 'Arduous', 'Byzantine', 'Cognoscenti', 'Daedalian', 'Ennui', 'Gorgonize', 'Hirsute', 'Ingenuous', 'Jactitation', 'Labyrinthine', 'Melancholie', 'Nadir', 'Obsequious', 'Pangolin', 'Quixotic', 'Risible', 'Sagacious', 'Tenebrous', 'Unctuous', 'Vexation', 'Winnows', 'Xanthic', 'Yokel', 'Zephyr']

    for _ in range(2_000):
        mydict = {"id":str(uuid.uuid4()), "text": ' '.join(random.choices(vocab, k=10))}
        mycol.insert_one(mydict)
    return {"status": "success"}

# Empty the database
@app.get("/empty_db")
async def empty_db():
    mycol.delete_many({})
    retrain_col.delete_many({})
    return {"status": "success"}