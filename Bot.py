#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import asyncio

from Config_manager import Config, Users, L10n
from Discord_related import bot
import Discord_related
import DB_manager
import Stars
import Rewards
import Misc

###############################################################################
# Events when a message is sent or deleted
###############################################################################

@bot.event
async def on_message(Message):

	# The bot ignores its own messages
	if Message.author == bot.user:
		return

	# Multiuser debug
	print("[on_message]")
	User = Discord_related.Determine_user(Message)
	if User:
		Localized_replies = L10n[User['language']]
		# When a message contains one or several 🌟
		if "🌟" in Message.content:
			Star_count = Message.content.count("🌟")
			if Message.author.name == Users['bot_owner']['discord_username']:
				# We set 0 if it’s a DM
				Server_id = Message.guild.id if Message.guild else 0
				Origin_chan = Message.channel
				DB_manager.Register_star(User, Server_id, Origin_chan.id, Message.id, Star_count)
				if Star_count > 1:
					await Origin_chan.send(Localized_replies['stars_in_message_several'].format(Star_count=Star_count, User_nick=User['nick']))
				if User['log_chan']:
					Server = await bot.get_guild(User['main_server'])
					Log_chan = await Discord_related.Get_chan(Server, User['log_chan'])
					if Log_chan:
						Message_link = f"https://discord.com/channels/{Server_id}/{Origin_chan.id}/{Message.id}"
						if Star_count == 1:
							Number = Localized_replies['stars_in_message_just_one']
						elif Star_count > 1:
							Number = str(Star_count)
						await Log_chan.send(Localized_replies['stars_in_message'].format(Bot_owner=User['bot_owner'], Number=Number, Message_link=Message_link))
					else:
						print(f"Error: Can’t send in #{User['log_chan']}")
	
	# Forward the message back to the bot’s command handler, to allow messages containing commands
	# to be processed
	await bot.process_commands(Message)

@bot.event
async def on_raw_message_delete(Payload):
	""" Check if the message has been stored in the DB, and if so remove it"""
	Concerned_user, Message_object = DB_manager.Remove_message(Payload.message_id)
	# Multiuser debug
	print("[on_raw_message_delete]")
	print(f"{Concerned_user} (without Discord_related.Determine_user)")
	if Users[Concerned_user]['log_chan']:
		User = Users[Concerned_user]
		Server = await bot.get_guild(User['main_server'])
		Log_chan = await Discord_related.Get_chan(Server, User['log_chan'])
		if Log_chan:
			Localized_replies = L10n[User['language']]
			if Message_object == "Stars":
				Reply = Localized_replies['stars_deleting_message'].format(Bot_owner=User['bot_owner'])
			if Message_object == "Reward":
				Reply = Localized_replies['rewards_deleting_message'].format(Bot_owner=User['bot_owner'])
			await Log_chan.send(Reply)
		else:
			print(f"Error: Can’t send in #{Users['log_chan']}")

###############################################################################
# Start the bot
###############################################################################

@bot.event
async def on_ready():
	"""Event triggered when the bot has connected to Discord"""
	print(f"Logged in as {bot.user} (ID: {bot.user.id})")
	print("——————————————————————————————————————")

bot.run(Config['Token'])
