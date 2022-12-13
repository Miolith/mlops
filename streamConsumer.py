import pika
from train_model import pipe
import pandas as pd
import sys
import os

def main():

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)

        df = pd.DataFrame([body.decode("utf-8")], columns = ["text"])
        result = "positive" if pipe.predict(df["text"])[0] == 1 else "negative"

        print(" [x] Sent %r" % result)
        # send to callback queue
        ch.basic_publish(exchange='', routing_key=properties.reply_to, body=result, properties=pika.BasicProperties(
            delivery_mode=2,
        ))
        #ch.basic_ack(delivery_tag = method.delivery_tag)

    channel.basic_consume(
        queue='hello', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)