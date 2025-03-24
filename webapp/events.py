import json
import logging
import os
import ssl
import threading
from abc import ABC, abstractmethod
from uuid import uuid4
from pathlib import Path

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
            APP_DIR = Path(__file__).resolve().parent
            ssl_context = ssl.create_default_context(
                cafile=os.path.join(APP_DIR, "tls_certificates/ca_certificate.pem")
            )
            ssl_context.load_cert_chain(
                certfile=os.path.join(APP_DIR, "tls_certificates/client_certificate.pem"),
                keyfile=os.path.join(APP_DIR, "tls_certificates/client_key.pem"),
            )

            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=os.environ["AMQP_HOST"],
                    credentials=pika.credentials.PlainCredentials(
                        url_unquote(os.environ["AMQP_USER"]),
                        url_unquote(os.environ["AMQP_PASS"]),
                    ),
                    ssl_options=pika.SSLOptions(context=ssl_context),
                )
            )
            self.channel = self.connection.channel()
            self.success = True
        except Exception as e:
            logger.error(e)
            self.success = False


    def close(self):
        if self.connection.is_open:
            self.connection.close()


    @abstractmethod
    def send_event(self, *args, **kwargs):
        pass


class PostProducer(EventProducer):

    def send_event(self, author: User, post_id):
        if not self.success:
            logger.error("Producer is not initialized successfully")
            return

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

        self.channel.basic_publish(
            exchange=os.environ["EVENT_EXCHANGE"],
            routing_key=os.environ["ROUTING_KEY_NOTIFICATION"],
            body=json.dumps(
                {
                    "correlationId": str(uuid4()),
                    "body": {
                        "event": "SUBSCRIBE_NOTIFICATIONS" if subscribe else "UNSUBSCRIBE_NOTIFICATIONS",
                        "user": {"firstname": user.first_name, "email": email},
                    },
                }
            ),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
