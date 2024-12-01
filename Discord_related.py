# -*- coding: utf-8 -*-

import discord
import os
from discord.ext import commands
from Config_manager import Users

intents = discord.Intents.default()
intents.members = True
# Allows to listen to messages events and provides metadata
intents.messages = True
# Allows to read the content of messages
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Can’t remove async, otherwise when on_raw_reaction_add() call this function, we get this error:
# TypeError: object TextChannel can't be used in 'await' expression
async def Get_chan(Server, Chan):
	# Provide a reference to a channel
	for Channel in Server.text_channels:
		if Channel.name == Chan:
			return Channel
	return None

def Split_reply(Reply):
	# Discord limits message size = split the reply into parts of 2000 characters or less
	Splitted_reply = []
	Current_part = ""
	# If the response contains several lines, it must be split into several strings
	Lines = Reply.split("\n")
	for Line in Lines:
		# +1 for the newline character
		if len(Current_part) + len(Line) + 1 > 2000:
			Splitted_reply.append(Current_part)
			# Start a new part
			Current_part = Line
		else:
			if Current_part:
				Current_part += "\n" + Line
			else:
				Current_part = Line
	# Add the remaining part (the string Reply = X parts of 2000c + a remaining part)
	if Current_part:
		Splitted_reply.append(Current_part)
	return Splitted_reply

def Determine_user(Message):
	Determined_user = None
	Server_id = Message.guild.id if Message.guild else 0
	Author_message = Message.author.name
	# If the message was sent by the bot owner, check if it’s a reply/highlight targeting a user
	if Author_message == Users['bot_owner']['discord_username']:
		# If it’s a reply
		if Message.reference and Message.reference.resolved:
			Replied_user = Message.reference.resolved.author.name
			for Name, User in Users.items():
				if Replied_user == User['discord_username'] and Name != "bot_owner":
					Determined_user = User
					# Multiuser debug
					print(f"{Name} (reply)")
					break
		# If it’s a highlight
		elif Message.mentions:
			for Mention in Message.mentions:
				for Name, User in Users.items():
					if Mention.name == User['discord_username'] and Name != "bot_owner":
						Determined_user = User
						# Multiuser debug
						print(f"{Name} (mention)")
						break
	# If the message was sent by one of the users, then it’s that user who is concerned
	else:
		for Name, User in Users.items():
			if Author_message == User['discord_username']:
				Determined_user = User
				# Multiuser debug
				print(f"{Name} (user sent)")
				break
	# If the previous methods have not managed to determine the user, we look if we’re on the main
	# server of one of the users (except for the bot owner)
	if not Determined_user:
		for Name, User in Users.items():
			if Name != "bot_owner":
				if Server_id == User['main_server']:
					Determined_user = User
					# Multiuser debug
					print(f"{Name} (server)")
					break
	# As a last resort, we check if the bot’s directory contains a file Current_user and it’s not
	# empty. In this case, we assume that it contains the name of the current user
	if not Determined_user:
		if os.path.isfile("Current_user"):
			try:
				with open("Current_user", "r", encoding="utf-8") as File:
					Current_user = File.read().strip()
					if Current_user and Current_user in Users:
						Determined_user = Users[Current_user]
						# Multiuser debug
						print(f"{Current_user} (file)")
			except Exception as e:
				print(f"Error: Can’t read the file Current_user: {e}")
		else:
			print("Error: Can't determine the user and the file Current_user isn’t present")
	return Determined_user
