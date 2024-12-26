# -*- coding: utf-8 -*-

import datetime
from zoneinfo import ZoneInfo
import json
import aiohttp
import os

from Config_manager import Users
from Discord_related import bot
import DB_manager

async def Download_attachments(User, Message):
	Attachments_filenames = []
	Oversized_files = []
	Max_size = 10485760 # 10 MB
	Storage_dir = User.get("hist_files_storage")
	if not Storage_dir:
		print(f"Error: No indication where to store the attachments for {User['name']}")
		return
	if not os.path.exists(Storage_dir):
		os.makedirs(Storage_dir)
	for Attachment in Message.attachments:
		async with aiohttp.ClientSession() as Session:
			async with Session.get(Attachment.url) as Response:
				if Response.status == 200:
					File_size = int(Response.headers.get("Content-Length", 0))
					if File_size > Max_size:
						Oversized_files.append(Attachment.url)
						Attachments_filenames.append(Attachment.url)
					else:
						Date = Message.created_at.astimezone(ZoneInfo("Europe/Paris")).strftime('%Y%m%d')
						File_name = f"{Date}—{Attachment.filename}"
						File_path = os.path.join(Storage_dir, File_name)
						with open(File_path, "wb") as File:
							File.write(await Response.read())
						Attachments_filenames.append(File_name)
	if Oversized_files:
		print(f"Error: {User['name']} sent an oversized file! {Oversized_file}")
	Attachments_filenames = json.dumps(Attachments_filenames)
	return Attachments_filenames

async def Message_added(Server_id, Chan, Message):
	for User in Users.values():
		if Server_id == User.get("main_server"):
			# Check if history recording is enabled for this user
			if not "history" in User or not User["history"]:
				return
			# We don’t record the content of the bot’s log chan
			if "log_chan" in User and str(Chan) == User["log_chan"]:
				return
			if len(Message.attachments) > 0:
				Attachments = await Download_attachments(User, Message)
			else:
				Attachments = None
			Replied_message_id = 0
			if Message.reference and Message.reference.resolved:
				Replied_message_id = Message.reference.resolved.id
			DB_manager.History_addition(User["name"], \
					Message.created_at.astimezone(ZoneInfo("Europe/Paris")).isoformat(), \
					Server_id, Chan.id, Message.id, \
					Replied_message_id, \
					Message.author.name, Message.content, Attachments)
			break

def Message_edited(Server_id, Message_id, New_content):
	for User in Users.values():
		if Server_id == User.get("main_server"):
			if not "history" in User or not User["history"]:
				return
			DB_manager.History_edition(User["name"], \
					datetime.datetime.now().isoformat(),
					Message_id, New_content)
			break

def Message_deleted(Server_id, Message_id):
	for User in Users.values():
		if Server_id == User.get("main_server"):
			if not "history" in User or not User["history"]:
				return
			DB_manager.History_deletion(User["name"], \
					datetime.datetime.now().isoformat(), \
					Message_id)
			break
