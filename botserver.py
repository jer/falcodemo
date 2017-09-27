import socket
import traceback
import logging
import sys
import os
import json
import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Job

logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

token = os.environ['TOKEN']
token = token.replace('\n', '')

def cmd_start(bot, update):
    chat_id = update.message.chat_id
    logger.info("Start from %s", chat_id)
    bot.send_message(chat_id=update.message.chat_id, text="Ready to send updates")

def subscriber_cmd(subscriptions):
    def cmd_subscribe(bot, update, args):
      """Subscribes to a falco priority"""
      chat_id = update.message.chat_id
      try:
          # args[0] should contain the priority to subscribe to
          priority = " ".join(args)
          chat_ids = subscriptions.get(priority, [])
          chat_ids.append(chat_id)
          subscriptions[priority] = chat_ids
          logger.info("id " + str(chat_id) + " subscribed to " + priority)
          update.message.reply_text("Subscribed to falco priority " + priority)
      except (IndexError, ValueError):
          update.message.reply_text('Usage: /subscribe <priority name>')
    return cmd_subscribe


def unsubscriber_cmd(subscriptions):
    def cmd_unsubscribe(bot, update, args):
      """Unsubscribes from a falco priority"""
      chat_id = update.message.chat_id
      try:
          # args[0] should contain the priority to subscribe to
          priority = " ".join(args)
          chat_ids = subscriptions.get(priority, [])
          new_chat_ids = []

          for chat in chat_ids:
              if chat != chat_id:
                  new_chat_ids.append(chat)

          subscriptions[priority] = new_chat_ids
          logger.info("id " + str(chat_id) + " unsubscribed from " + priority)
          update.message.reply_text("Unsubscribed from falco priority " + priority)
      except (IndexError, ValueError):
          update.message.reply_text('Usage: /unsubscribe <priority name>')
    return cmd_unsubscribe


updater = Updater(token=token)
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', cmd_start)
dispatcher.add_handler(start_handler)

subscriptions = {}
subscribe_handler = CommandHandler('subscribe', subscriber_cmd(subscriptions), pass_args=True)
dispatcher.add_handler(subscribe_handler)

unsubscribe_handler = CommandHandler('unsubscribe', unsubscriber_cmd(subscriptions), pass_args=True)
dispatcher.add_handler(unsubscribe_handler)

s = socket.socket()
host = "0.0.0.0"
port = 8089
s.bind((host,port))
s.listen(5)

updater.start_polling()

def dispatch_message(data, subscriptions, bot):
    try:
        payload = json.loads(data)
    except ValueError:
        logger.info("Unparsable data received: " + data)
        return

    chat_ids = subscriptions.get(payload['priority'], [])
    for chat_id in chat_ids:
        bot.send_message(chat_id=chat_id, text=data)


logger.info("Waiting for data")
try:
    while True:
        c, addr = s.accept()
        data = str(c.recv(1026))
        logger.info(repr(addr[1]) + ": " + data)
        dispatch_message(data, subscriptions, updater.bot)
        c.close()
except:
    logging.error(traceback.format_exc())
    logger.info("Quitting.")
    updater.stop()
