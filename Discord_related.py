# -*- coding: utf-8 -*-

import discord
from discord.ext import commands
from Config_manager import Users

intents = discord.Intents.default()
intents.members = True
# Allows to listen to messages events and provides metadata
intents.messages = True
# Allows to read the content of messages
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Can’t remove async, otherwise when on_raw_reaction_add() call this function, we get this error:
# TypeError: object TextChannel can't be used in 'await' expression
async def Get_chan(Server, Chan):
	"""Provide a reference to a chan"""
	for Channel in Server.text_channels:
		if Channel.name == Chan:
			return Channel
	return None

def Split_reply(Reply):
	"""Discord limits message size = split the reply into parts of 2000 characters or less"""
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
	User = None
	Server = Message.guild.id
	Author_message = Message.author.name
	# If the message was sent by the bot owner, check if it’s a reply/highlight targeting a user
	if Author_message == Users['bot_owner']['discord_username']:
		# If it’s a reply
		if Message.reference and Message.reference.resolved:
			Replied_user = Message.reference.resolved.author.name
			for Name, User_data in Users.items():
				if Replied_user == User_data['discord_username'] and Name != "bot_owner":
					User = User_data
					User['name'] = Name
					break
		# If it’s a highlight
		elif Message.mentions:
			for Mention in Message.mentions:
				for Name, User_data in Users.items():
					if Mention.name == User_data['discord_username'] and Name != "bot_owner":
						User = User_data
						User['name'] = Name
						break
	# If the message was sent by one of the users, then it’s that user who is concerned
	else:
		for Name, User_data in Users.items():
			if Author_message == User_data['discord_username']:
				User = User_data
				User['name'] = Name
				break
	# If the previous methods have not managed to determine the user, we look if we’re on the main
	# server of one of the users (except for the bot owner)
	if not User:
		for Name, User_data in Users.items():
			if Name != "bot_owner":
				if Server == User_data['main_server']:
					User = User_data
					User['name'] = Name
					break
	if not User:
		print("Wait, I’m confused. I can't figure out which user is concerned!")
	return User
