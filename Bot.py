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
import History
import Misc

###############################################################################
# Events when a message is sent or deleted
###############################################################################

@bot.event
async def on_message(Message):

	# We set 0 if it’s a DM
	Server_id = Message.guild.id if Message.guild else 0
	Chan = Message.channel

	History.Message_added(Server_id, Chan, Message)

	# The bot ignores its own messages
	if Message.author == bot.user:
		return

	# Multiuser debug
	print("[on_message]")
	User = Discord_related.Determine_user(Message)
	if User:
		if "🌟" in Message.content:
			await Stars.Addition_in_message(User, Server_id, Chan, Message)

	# Forward the message back to the bot’s command handler, to allow messages containing commands
	# to be processed
	await bot.process_commands(Message)

@bot.event
async def on_raw_message_edit(Payload):
	Server_id = Payload.guild_id if bot.get_guild(Payload.guild_id) else 0
	Chan = await bot.fetch_channel(Payload.channel_id)
	Message = await Chan.fetch_message(Payload.message_id)
	History.Message_edited(Server_id, Payload.message_id, Message.content)

@bot.event
async def on_raw_message_delete(Payload):

	History.Message_deleted(Payload)

	# Check if the message has been stored in the DB regarding stars or rewards, and if so remove it
	Concerned_user, Message_subject = DB_manager.Remove_message(Payload.message_id)
	# Multiuser debug
	print("[on_raw_message_delete]")
	print(f"{Concerned_user} (in function)")
	if Concerned_user and "log_chan" in Users[Concerned_user]:
		User = Users[Concerned_user]
		Log_chan = await Discord_related.Get_chan(bot.get_guild(User["main_server"]), User["log_chan"])
		if Log_chan:
			Localized_replies = L10n[User["language"]]
			if Message_subject == "Stars":
				Reply = Localized_replies["stars_deleting_message"].format(Bot_owner=User["bot_owner"])
			if Message_subject == "Reward":
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

	# Start the APOD event, at the daily time specified in the configuration
	if "NASA_API_key" in Config and "APOD_time" in Config:
		if not Events.APOD.is_running():
			@Events.APOD.before_loop
			async def Waiting_before_APOD():
				Wanted_time = datetime.datetime.strptime(Config["APOD_time"], "%H:%M").time()
				Delay = Events.Time_until(Wanted_time)
				print(f"APOD task: scheduled in {Delay}")
				await asyncio.sleep(Delay.total_seconds())
			Events.APOD.start()
		else:
			print("APOD task: already running")

	print("————————————————————————————————————————")

bot.run(Config["Token"])
