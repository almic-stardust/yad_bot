# -*- coding: utf-8 -*-

import datetime
from zoneinfo import ZoneInfo
import json
import aiohttp
import os
import smtplib
import email.utils
from email.mime.text import MIMEText

from Config_manager import Config, Users
from Discord_related import bot
import DB_manager

def Notification_for_oversized_files(User, Files_URLs):
	User_name = User['name'].capitalize()
	Mail_server = Config.get("Mail_server")
	if not Mail_server:
		print("Error: the mail server must be configured.")
		return
	Bot_mail = Config.get("Bot_mail_address")
	Bot_name = Bot_mail.split("@")[0].replace('_', ' ').capitalize()
	Owner_mail = Users["bot_owner"].get("mail_address")
	if not Bot_mail or not Owner_mail:
		print("Error: both mail addresses (bot and owner) must be configured.")
		return
	Mail = MIMEText(f"Hello {User['bot_owner']},\n\n" + \
			f"{User_name} sent files exceeding the size limit:\n\n" + \
			"\n".join(Files_URLs))
	Mail["Subject"] = f"{User_name} sent oversized attachments"
	Mail["From"] = f"{Bot_name} <{Bot_mail}>"
	Mail["To"] = f"{User['bot_owner']} <{Owner_mail}>"
	Mail["Date"] = email.utils.format_datetime(datetime.datetime.now())
	try:
		with smtplib.SMTP(Mail_server, 25) as Server:
			Server.starttls()
			Server.sendmail(Bot_mail, Owner_mail, Mail.as_string())
			print("Oversized attachment: notification mail sent successfully.")
	except Exception as e:
		print(f"Failed to send mail: {e}")

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
		Notification_for_oversized_files(User, Oversized_files)
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
