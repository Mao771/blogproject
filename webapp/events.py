import json
import logging
import os
import ssl
import threading
from abc import ABC, abstractmethod
from uuid import uuid4
from pathlib import Path
import time

import pika
from webapp.models import User
from dotenv import load_dotenv
from pika.compat import url_unquote

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class EventProducer(ABC):

    __instance = None
    __lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            with cls.__lock:
                if cls.__instance is None:
                    cls.__instance = super().__new__(cls, *args, **kwargs)
                    cls.__instance._init()

        return cls.__instance

    def _init(self):
        try:
            # APP_DIR = Path(__file__).resolve().parent
            # ssl_context = ssl.create_default_context(
            #     cafile=os.path.join(APP_DIR, "tls_certificates/ca_certificate.pem")
            # )
            # ssl_context.load_cert_chain(
            #     certfile=os.path.join(APP_DIR, "tls_certificates/client_certificate.pem"),
            #     keyfile=os.path.join(APP_DIR, "tls_certificates/client_key.pem"),
            # )

            for i in range(10):
                try:
                    self.connection = pika.BlockingConnection(
                        pika.ConnectionParameters(
                            host=os.environ['AMQP_HOST'],
                            credentials=pika.credentials.PlainCredentials(
                                url_unquote(os.environ['AMQP_USER']),
                                url_unquote(os.environ['AMQP_PASS'])
                            )
                        )
                    )
                    logger.info("Connected to RabbitMQ")
                    break
                except pika.exceptions.AMQPConnectionError:
                    logger.info(f"Failed to connect to RabbitMQ, attempt {i + 1}/10")
                    time.sleep(3)
            else:
                raise Exception("Failed to connect to RabbitMQ")
            self.channel = self.connection.channel()
            self.success = True
        except Exception as e:
            logger.error(e)
            self.success = False


    def check_connection_and_channel(self):
        if self.connection.is_closed:
            self._init()
        elif self.channel.is_closed:
            self.channel = self.connection.channel()


    def close(self):
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
            if self.connection and self.connection.is_open:
                self.connection.close()
        except Exception as e:
            logger.warning(f"Error while closing EventProducer: {e}")


    @abstractmethod
    def send_event(self, *args, **kwargs):
        pass


class PostProducer(EventProducer):

    def send_event(self, author: User, post_id, post_uri):
        if not self.success:
            logger.error("Producer is not initialized successfully")
            return

        self.check_connection_and_channel()

        logger.info("Sending event upon post creation")
        self.channel.basic_publish(
            exchange=os.environ["EVENT_EXCHANGE"],
            routing_key=os.environ["ROUTING_KEY_MODERATION"],
            body=json.dumps(
                {
                    "correlationId": str(uuid4()),
                    "body": {
                        "event": "BLOG_POST_CREATED",
                        "post": {
                            "id": post_id,
                            "author": {"id": author.id},
                            'uri': post_uri
                        },
                    },
                }
            ),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )


class SubscribeNotificationProducer(EventProducer):

    def send_event(self, user: User, email: str, subscribe: bool = True):
        if not self.success:
            logger.error("Producer is not initialized successfully")
            return

        self.check_connection_and_channel()

        self.channel.basic_publish(
            exchange=os.environ["EVENT_EXCHANGE"],
            routing_key=os.environ["ROUTING_KEY_NOTIFICATION"],
            body=json.dumps(
                {
                    "correlationId": str(uuid4()),
                    "body": {
                        "event": "SUBSCRIBE_NOTIFICATIONS" if subscribe else "UNSUBSCRIBE_NOTIFICATIONS",
                        "user": {"author_id": user.id, "firstname": user.first_name, "email": email},
                    },
                }
            ),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
