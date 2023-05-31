from dotenv import load_dotenv
import os
import json
import pika
from main import solve


load_dotenv()

connection = pika.BlockingConnection(pika.URLParameters(os.environ['CLOUDAMQP_URL']))
channel = connection.channel()
channel.queue_declare(queue='rpc_queue')


def process(data, update_callback):
    shifts = data['shifts']
    persons = data['persons']
    rules_stages = data['rules']

    solve(shifts, persons, rules_stages, update_callback)
    # return solve(shifts, persons, rules_stages, update_callback)


def on_request(ch, method, props, body):

    def update_callback(status, result, rules):
        print('update')
        response = json.dumps({
            'status': status,
            'result': result,
            'rules': rules
        })
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body=response)

    data = json.loads(body.decode('utf-8'))

    print(" [.] process" % data)
    # response = json.dumps(process(data, update_callback))
    process(data, update_callback)

    '''ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id),
                     body=response)'''
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='rpc_queue', on_message_callback=on_request)

print(" [x] Awaiting RPC requests")
channel.start_consuming()
