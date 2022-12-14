import pika
import pandas as pd
from train_model import trainModel
from load_model import loadModel
import sys
import os
import pymongo

try:
    pipe = loadModel()
except:
    trainModel()

pipe = loadModel()

def main():

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body.decode())
        idVal = body.decode()
        print(" [x] Done")

        values = list(mycol.find({"id":idVal},{"_id":0, "text":""}))[0]

        predict_val = pipe.predict([values['text']])
        query_val = {"id":idVal}
        print("Prediction value" + str(predict_val[0]))
        pred_val_query = {"$set":{"prediction":predict_val[0]}}
        mycol.update_one(query_val, pred_val_query)

        ch.basic_publish(exchange='',
                        routing_key=properties.reply_to,
                        properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                        body=str(predict_val[0])
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue='hello', on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

dbHost = "localhost"
myclient = pymongo.MongoClient("mongodb://" + dbHost + ":27017")
mydb = myclient["mydatabase"]
mycol = mydb["preddata"]


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)