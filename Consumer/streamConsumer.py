import pika
import pandas as pd
from Model.train_model import trainModel, loadData
from Model.load_model import loadModel
from Model.drift import detect_drift
import sys
import os
import pymongo

dbHost = os.environ.get("DB_HOST")
rabbitMQHost = os.environ.get("RABBITMQ_HOST")
queueName = os.environ.get("QUEUE_NAME")
heartBeatTimeOut = int(os.environ.get("HEART_BEAT_TIMEOUT"))
blockedConnectionTimeOut = int(os.environ.get("BLOCKED_CONNECTION_TIMEOUT"))

def main():

    # if file model.joblib does not exist, train the model
    if not os.path.exists("model.joblib"):
        trainModel()

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost, 
                                        heartbeat=heartBeatTimeOut,
                                        blocked_connection_timeout=blockedConnectionTimeOut)
    )
    channel = connection.channel()

    channel.queue_declare(queue=queueName)
    channel.queue_declare(queue="retrain")
    channel.queue_declare(queue="drift")

    def callback_predict(ch, method, properties, body):
        """
        Callback function for prediction queue
        """
        pipe = loadModel()

        print(" [x] Received %r" % body.decode())
        idVal = body.decode()
        print(" [x] Done")

        values = mycol.find_one({"id":idVal})

        predict_input = pd.Series([values['text']])
        print(" [x]  Prediction input: ", predict_input[0])
        predict_val = int(pipe.predict(predict_input)[0])
        query_val = {"id":idVal}
        print(" [x] Prediction value: ", predict_val)
        pred_val_query = {"$set":{"prediction":predict_val}}
        mycol.update_one(query_val, pred_val_query)

        ch.basic_publish(exchange='',
                        routing_key=properties.reply_to,
                        properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                        body=str(predict_val)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def callback_retrain(ch, method, properties, body):
        """
        Callback function for training the model
        with new data
        """
        print(" [x] Retraining model with new data")
        print(" [x] Received %r" % body.decode())
        idVal = body.decode()

        values = retrain_col.find_one({"id":idVal})

        retrain_input = [values['text']]
        label = [values['label']]

        trainModel(retrain_input, label)
        print(" [x] Done")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def callback_drift(ch, method, properties, body):
        """
        Callback function for checking distribution shift
        """
        print(" [x] Checking for drift")
        print(" [x] Received %r" % body.decode())

        data = mycol.find()
        X = pd.Series([x['text'] for x in data])
        print(" [x] Production size: ", len(X))

        df = loadData()
        print(" [x] Training size: ", len(df['text']))
        drift = detect_drift(X_train=df['text'], X_prod=X)

        print(" [x] Done")
        ch.basic_publish(exchange='',
                        routing_key=properties.reply_to,
                        properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                        body='1' if drift else '0'
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    
    
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=queueName, on_message_callback=callback_predict)
    
    channel.basic_consume(
        queue="retrain", on_message_callback=callback_retrain)
    
    channel.basic_consume(
        queue="drift", on_message_callback=callback_drift
    )

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()



myclient = pymongo.MongoClient("mongodb://" + dbHost + ":27017")
mydb = myclient["mydatabase"]
mycol = mydb["preddata"]
retrain_col = mydb["retraindata"]


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)