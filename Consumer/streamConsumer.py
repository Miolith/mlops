import pika
import pandas as pd
from Model.train_model import trainModel
from Model.load_model import loadModel
import sys
import os
import pymongo

dbHost = os.environ.get("DB_HOST")
rabbitMQHost = os.environ.get("RABBITMQ_HOST")
queueName = os.environ.get("QUEUE_NAME")
heartBeatTimeOut = int(os.environ.get("HEART_BEAT_TIMEOUT"))
blockedConnectionTimeOut = int(os.environ.get("BLOCKED_CONNECTION_TIMEOUT"))

def main():

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
    channel = connection.channel()

    channel.queue_declare(queue=queueName)

    def callback(ch, method, properties, body):
        try:
            pipe = loadModel()
        except:
            trainModel()
        pipe = loadModel()


        print(" [x] Received %r" % body.decode())
        idVal = body.decode()
        print(" [x] Done")

        values = mycol.find_one({"id":idVal})

        predict_input = pd.DataFrame([values['text']], columns=['text'])
        print("Prediction input: ", predict_input["text"])
        predict_val = int(pipe.predict(predict_input["text"])[0])
        query_val = {"id":idVal}
        print("Prediction value: ", predict_val)
        pred_val_query = {"$set":{"prediction":predict_val}}
        mycol.update_one(query_val, pred_val_query)

        ch.basic_publish(exchange='',
                        routing_key=properties.reply_to,
                        properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                        body=str(predict_val)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=queueName, on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()



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