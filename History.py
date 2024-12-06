# -*- coding: utf-8 -*-

import datetime
import json
from Config_manager import Users
from Discord_related import bot
import DB_manager

def Message_added(Server_id, Chan, Message):
	for User in Users.values():
		if Server_id == User.get("main_server"):
			# Check if history recording is disabled for this user
			if "history" in User and not User["history"]:
				return
			# We don’t record the content of the bot’s log chan
			if "log_chan" in User and str(Chan) == User["log_chan"]:
				return
			if len(Message.attachments) > 0:
				Attachments = [Attachment.url for Attachment in Message.attachments]
				Attachments = json.dumps(Attachments)
			else:
				Attachments = None
			Replied_message_id = 0
			if Message.reference and Message.reference.resolved:
				Replied_message_id = Message.reference.resolved.id
			DB_manager.History_addition(User["name"], \
					datetime.datetime.now().isoformat(), \
					Server_id, Chan.id, Message.id, \
					Replied_message_id, \
					Message.author.name, Message.content, Attachments)
			break

def Message_deleted(Message):
	Server_id = Message.guild_id
	for User in Users.values():
		if Server_id == User.get("main_server"):
			if "history" in User and not User["history"]:
				return
			DB_manager.History_deletion(User["name"], datetime.datetime.now().isoformat(), Message.message_id)
			break
