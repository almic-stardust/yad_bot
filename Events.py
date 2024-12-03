# -*- coding: utf-8 -*-

import requests
import datetime
from discord.ext import tasks
from Config_manager import Config, Users
from Discord_related import bot
import Discord_related

def Time_until(Wanted_time):
	Now = datetime.datetime.now()
	# In the current day, the daily time wanted for the task
	Task_time = datetime.datetime.combine(Now.date(), Wanted_time)
	# If the bot was started after the wanted daily time, then we launch the task the following day
	if Now > Task_time:
		Task_time += datetime.timedelta(days=1)
	Delay = Task_time - Now
	return Delay

# The time interval (hours=24) is the delay between consecutive executions. The task runs every day
# at the same time, corresponding to the time when the task was executed for the first time. Without
# additional measures, the first execution of the task happens when the bot starts, and then each
# day at the same time. So when the bot is started, we need to delay the first execution of the
# task, in order for this first execution to happen at the daily time wanted for the task. We use
# Time_until(Wanted_time) in Events.APOD.before_loop in Bot.py, to calculate the delay between the
# time when the bot is started, and the daily time for the task
@tasks.loop(hours=24)
async def APOD():
	URL = f"https://api.nasa.gov/planetary/apod?api_key={Config['NASA_API_key']}"
	APOD_json = requests.get(URL)
	APOD_json.raise_for_status()
	APOD_json = APOD_json.json()
	for User in Users.values():
		if "events" in User and "apod" in User["events"]:
			if "main_server" in User and "main_chan" in User:
				Chan = await Discord_related.Get_chan(bot.get_guild(User["main_server"]), User["main_chan"])
				if Chan:
					APOD_date = datetime.date.today().strftime("%y%m%d")
					APOD_title = f"[**{APOD_json.get('title')[:1900]}**](<https://apod.nasa.gov/apod/ap{APOD_date}.html>)"
					APOD_description = APOD_json.get("explanation", "No description available.")
					Thread_start = await Chan.send(APOD_title)
					Thread = await Thread_start.create_thread(name="More information")
					for Message in Discord_related.Split_reply(APOD_description):
						await Thread.send(Message)
					await Chan.send(APOD_json.get("hdurl", APOD_json["url"]))
				else:
					print(f"Error: Can’t send in {User['main_chan']}")
			else:
				print("Main channel not found or configured incorrectly")
