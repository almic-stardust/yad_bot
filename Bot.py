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

	try:
		User = Discord_related.Determine_user(Message)
		if User:
			Localized_replies = L10n[User['language']]
			# When a message contains one or several 🌟
			if "🌟" in Message.content:
				Star_count = Message.content.count("🌟")
				if Message.author.name == Users['bot_owner']['discord_username']:
					Server = Message.guild
					Server_id = Message.guild.id if Server else 0
					DB_manager.Register_star(User, Server_id, Message.channel.id, Message.id, Star_count)
					if Star_count > 1:
						await Message.channel.send(Localized_replies['stars_in_message_several'].format(Star_count=Star_count, User_nick=User['nick']))
					if Config['Log_chan']:
						Chan = await Discord_related.Get_chan(bot.get_guild(User['main_server']), Config['Log_chan'])
						if Chan:
							Message_link = f"https://discord.com/channels/{Server_id}/{Message.channel.id}/{Message.id}"
							if Star_count == 1:
								Number = Localized_replies['stars_in_message_just_one']
							elif Star_count > 1:
								Number = str(Star_count)
							await Chan.send(Localized_replies['stars_in_message'].format(Bot_owner=User['bot_owner'], Number=Number, Message_link=Message_link))
						else:
							print(f"Can’t send in #{Config['Log_chan']}")
	
	except Exception as Error:
		print(f"Error: [on_message] {Error}")

	# Forward the message back to the bot’s command handler, to allow messages containing commands
	# to be processed
	await bot.process_commands(Message)

@bot.event
async def on_raw_message_delete(Payload):
	""" Check if the message has been stored in the DB, and if so remove it"""
	try:
		if not Config['Log_chan']:
			DB_manager.Remove_message(Payload.message_id)
		else:
			Concerned_user, Message_subject = DB_manager.Remove_message(Payload.message_id)
			if Concerned_user:
				Chan = await Discord_related.Get_chan(bot.get_guild(Users[Concerned_user]['main_server']), Config['Log_chan'])
				if Chan:
					Localized_replies = L10n[Users[Concerned_user]['language']]
					if Message_subject == "Stars":
						await Chan.send(Localized_replies['stars_deleting_message'].format(Bot_owner=Users[Concerned_user]['bot_owner']))
					if Message_subject == "Reward":
						await Chan.send(Localized_replies['rewards_deleting_message'].format(Bot_owner=Users[Concerned_user]['bot_owner']))
				else:
					print(f"Can’t send in #{Config['Log_chan']}")
	except Exception as Error:
		print(f"Error: [on_raw_message_delete] {Error}")

###############################################################################
# Start the bot
###############################################################################

@bot.event
async def on_ready():
	"""Event triggered when the bot has connected to Discord"""
	print(f"Logged in as {bot.user} (ID: {bot.user.id})")
	print("——————————————————————————————————————")

bot.run(Config['Token'])
