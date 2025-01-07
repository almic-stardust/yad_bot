# -*- coding: utf-8 -*-

import datetime
from zoneinfo import ZoneInfo
import json
import aiohttp
import os
import glob
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
	Mail = MIMEText(f"Hello {User['bot_owner']},\n\n"
			f"{User_name} sent files exceeding the size limit:\n\n"
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
						Base_name, File_ext = os.path.splitext(Attachment.filename)
						Base_name = Base_name.replace("—", "_")
						Base_name = f"{Date}—" + Base_name
						Filename = f"{Base_name}{File_ext}"
						File_pattern = os.path.join(Storage_dir, f"{Base_name}*{File_ext}")
						Matching_files = glob.glob(File_pattern)
						if Matching_files:
							# If there’s only one file, we rename it to add “—1” at the end of its
							# base name, and the current file will have “—2” in its base name
							if len(Matching_files) == 1:
								Old_file_old_path = os.path.join(Storage_dir, Filename)
								Old_file_new_name = f"{Base_name}—1{File_ext}"
								Old_file_new_path = os.path.join(Storage_dir, Old_file_new_name)
								os.rename(Old_file_old_path, Old_file_new_path)
								Filename = f"{Base_name}—2{File_ext}"
							# If there’re several files already, we determine the biggest suffix
							# that has already been assigned, so that the current file gets a unique
							# number at the end of its base name. This avoids problems if one of the
							# duplicates has been deleted before the current file was posted
							else:
								Duplicates_suffixes = []
								for File in Matching_files:
									Parts = os.path.splitext(os.path.basename(File))[0].split("—")
									# If the filename matches AAAAMMJJ—Name_from_Discord—Number.ext
									if len(Parts) == 3 and Parts[-1].isdigit():
										Duplicates_suffixes.append(int(Parts[-1]))
								Suffix = max(Duplicates_suffixes) + 1
								Filename = f"{Base_name}—{Suffix}{File_ext}"
						File_path = os.path.join(Storage_dir, Filename)
						with open(File_path, "wb") as File:
							File.write(await Response.read())
						Attachments_filenames.append(Filename)
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
			DB_manager.History_addition(User["name"],
					Message.created_at.astimezone(ZoneInfo("Europe/Paris")).isoformat(),
					Server_id, Chan.id, Message.id,
					Replied_message_id,
					Message.author.name, Message.content, Attachments)
			break

def Message_edited(Server_id, Message_id, New_content):
	for User in Users.values():
		if Server_id == User.get("main_server"):
			if not "history" in User or not User["history"]:
				return
			DB_manager.History_edition(User["name"],
					Message_id,
					datetime.datetime.now().isoformat(),
					New_content)
			break

def Message_deleted(Server_id, Message_id):
	for User in Users.values():
		if Server_id == User.get("main_server"):
			if not "history" in User or not User["history"]:
				return
			Message = DB_manager.History_fetch_message(User["name"], Message_id)
			if Message:
				Discord_username, Attachments = Message[5], Message[7]
				# The variable User doesn’t necessarily identify the author of the message
				for Look_for_author in Users.values():
					if Discord_username == Look_for_author["discord_username"]:
						Author = Look_for_author
					break
				Attachments = json.loads(Attachments) if Attachments else None
				if Attachments:
					Storage_dir = User.get("hist_files_storage")
					if not Storage_dir:
						print(f"Error: The folder where {User['name']}’s attachments were stored isn’t accessible.")
						return
					Updated_filenames = []
					for Filename in Attachments:
						File_path = os.path.join(Storage_dir, Filename)
						if os.path.exists(File_path):
							if "hist_keep_all" in Author and Author["hist_keep_all"]:
								Base_name, File_ext = os.path.splitext(Filename)
								# Split the filename into the date and the rest of it
								Parts = Base_name.split("—", 1)
								if len(Parts) == 2:
									New_base_name = f"{Parts[0]}—DELETED—{Parts[1]}"
								else:
									# Fallback for unexpected cases
									New_base_name = f"DELETED—{Base_name}"
								New_filename = f"{New_base_name}{File_ext}"
								New_file_path = os.path.join(Storage_dir, New_filename)
								os.rename(File_path, New_file_path)
								Updated_filenames.append((Filename, New_filename))
							else:
								if os.path.exists(File_path):
									try:
										os.remove(File_path)
									except OSError as e:
										print(f"Error deleting file {Filename}: {e}")
						else:
							print(f"Error: File {Filename} not found.")
				DB_manager.History_deletion(User["name"],
					Message_id,
					Author,
					datetime.datetime.now().isoformat(),
					Updated_filenames)
			break
