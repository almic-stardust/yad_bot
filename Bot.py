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
async def on_raw_message_delete(Message):
	await Stars.Deletion_in_message(Message)

###############################################################################
# Start the bot
###############################################################################

@bot.event
async def on_ready():
	# Event triggered when the bot has connected to Discord
	print(f"Logged in as {bot.user}")

	# Start the APOD event, at the daily time specified in the configuration
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
