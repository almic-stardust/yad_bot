#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import asyncio
import datetime

from Config_manager import Config, Users, L10n
from Discord_related import bot
import Discord_related
import DB_manager
import Stars
import Rewards
import Events
import Misc

###############################################################################
# Events when a message is sent or deleted
###############################################################################

@bot.event
async def on_message(Message):

	# The bot ignores its own messages
	if Message.author == bot.user:
		return

	# We set 0 if it’s a DM
	Server_id = Message.guild.id if Message.guild else 0
	Chan = Message.channel
	# Multiuser debug
	print("[on_message]")
	User = Discord_related.Determine_user(Message)
	if User:
		Localized_replies = L10n[User["language"]]
		# When a message contains one or several 🌟
		if "🌟" in Message.content:
			Star_count = Message.content.count("🌟")
			if Message.author.name == Users["bot_owner"]["discord_username"]:
				DB_manager.Register_star(User["name"], Server_id, Chan.id, Message.id, Star_count)
				#if Star_count > 1:
				#	await Chan.send(Localized_replies["stars_in_message_several"].format(Bot_owner=User["bot_owner"], Star_count=Star_count, User_nick=User["nick"]))
				if "log_chan" in User:
					Log_chan = await Discord_related.Get_chan(bot.get_guild(User["main_server"]), User["log_chan"])
					if Log_chan:
						Message_link = f"https://discord.com/channels/{Server_id}/{Chan.id}/{Message.id}"
						if Star_count == 1:
							Number = Localized_replies["stars_just_one"]
						elif Star_count > 1:
							Number = Star_count
						await Log_chan.send(Localized_replies["stars_in_message"].format(Bot_owner=User["bot_owner"], Number=Number, Message_link=Message_link))
					else:
						print(f"Error: Can’t send in #{User['log_chan']}")
	
	# Forward the message back to the bot’s command handler, to allow messages containing commands
	# to be processed
	await bot.process_commands(Message)

@bot.event
async def on_raw_message_delete(Message):
	# Check if the message has been stored in the DB, and if so remove it
	Concerned_user, Message_object = DB_manager.Remove_message(Message.message_id)
	# Multiuser debug
	print("[on_raw_message_delete]")
	print(f"{Concerned_user} (in function)")
	if Concerned_user and "log_chan" in Users[Concerned_user]:
		User = Users[Concerned_user]
		Log_chan = await Discord_related.Get_chan(bot.get_guild(User["main_server"]), User["log_chan"])
		if Log_chan:
			Localized_replies = L10n[User["language"]]
			if Message_object == "Stars":
				Reply = Localized_replies["stars_deleting_message"].format(Bot_owner=User["bot_owner"])
			if Message_object == "Reward":
				Reply = Localized_replies["rewards_deleting_message"].format(Bot_owner=User["bot_owner"])
			await Log_chan.send(Reply)
		else:
			print(f"Error: Can’t send in #{User['log_chan']}")

###############################################################################
# Start the bot
###############################################################################

@bot.event
async def on_ready():
	# Event triggered when the bot has connected to Discord
	print(f"Logged in as {bot.user}")

	# Starting the APOD event at the daily time specified in the configuration
	if "NASA_API_key" in Config and "APOD_time" in Config:
		@Events.APOD.before_loop
		async def Waiting_before_APOD():
			Wanted_time = datetime.datetime.strptime(Config["APOD_time"], "%H:%M").time()
			Delay = Events.Time_until(Wanted_time)
			print(f"Delay until APOD task: {Delay}")
			await asyncio.sleep(Delay.total_seconds())
		Events.APOD.start()

	print("————————————————————————————————————————")

bot.run(Config["Token"])
