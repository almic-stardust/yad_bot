# -*- coding: utf-8 -*-

from zoneinfo import ZoneInfo
import datetime
from Config_manager import Config, Users, L10n
from Discord_related import bot
import Discord_related
import DB_manager

# We don’t use on_reaction_add() because it only considers reactions added to messages in the bot’s
# cache. We need on_raw_reaction_add() to handle reactions added to messages sent before the bot was
# last started
@bot.event
async def on_raw_reaction_add(Payload):
	# When a 🌟 reaction is added to a message
	if str(Payload.emoji) == "🌟":
		Author_reaction = await bot.fetch_user(Payload.user_id)
		Server_id = Payload.guild_id if bot.get_guild(Payload.guild_id) else 0
		Origin_chan = await bot.fetch_channel(Payload.channel_id)
		Message = await Origin_chan.fetch_message(Payload.message_id)
		# Multiuser debug
		print("[on_raw_reaction_add]")
		User = Discord_related.Determine_user(Message)
		if User:
			Localized_replies = L10n[User['language']]
			if Author_reaction.name == Users['bot_owner']['discord_username']:
				DB_manager.Register_star(User, Server_id, Origin_chan.id, Message.id, 1)
				if "log_chan" in User:
					Log_chan = await Discord_related.Get_chan(bot.get_guild(User['main_server']), User['log_chan'])
					if Log_chan:
						Message_link = f"https://discord.com/channels/{Server_id}/{Origin_chan.id}/{Message.id}"
						await Log_chan.send(Localized_replies['stars_adding_reaction'].format(Bot_owner=User['bot_owner'], Message_link=Message_link))
					else:
						print(f"Error: Can’t send in #{User['log_chan']}")
			else:
				await Origin_chan.send(Localized_replies['stars_not_bot_owner'].format(Bot_owner=User['bot_owner'], User_nick=User['nick']))

@bot.event
async def on_raw_reaction_remove(Payload):
	# When a 🌟 reaction is removed from a message, even if it’s not in the bot’s cache
	if str(Payload.emoji) == "🌟":
		Author_reaction = await bot.fetch_user(Payload.user_id)
		if Author_reaction.name == Users['bot_owner']['discord_username']:
			Origin_chan = await bot.fetch_channel(Payload.channel_id)
			Message = await Origin_chan.fetch_message(Payload.message_id)
			# Multiuser debug
			print("[on_raw_reaction_remove]")
			User = Discord_related.Determine_user(Message)
			if User:
				DB_manager.Remove_star(User, Payload.message_id)
				if "log_chan" in User:
					Log_chan = await Discord_related.Get_chan(bot.get_guild(User['main_server']), User['log_chan'])
					if Log_chan:
						Localized_replies = L10n[User['language']]
						await Log_chan.send(Localized_replies['stars_deleting_reaction'].format(Bot_owner=User['bot_owner']))
					else:
						print(f"Error: Can’t send in #{User['log_chan']}")
	
@bot.group()
async def stars(Context):
	# If no subcommand is invoked, display the current balance of 🌟 in the DB
	if not Context.invoked_subcommand:
		# Multiuser debug
		print("[!stars]")
		User = Discord_related.Determine_user(Context.message)
		if User:
			Localized_replies = L10n[User['language']]
			Sum_given_stars, Sum_rewards_used = DB_manager.Get_current_balance(User)
			Current_balance = Sum_given_stars - Sum_rewards_used
			await Context.send(Localized_replies['stars_balance'].format(User_nick=User['nick'], Current_balance=Current_balance, Sum_rewards_used=Sum_rewards_used, Sum_given_stars=Sum_given_stars))

@stars.command(name="help")
async def Stars_help(Context):
	# Multiuser debug
	print("[!stars help]")
	User = Discord_related.Determine_user(Context.message)
	if User:
		Localized_replies = L10n[User['language']]
		Help_text = Localized_replies['stars_help']
		for Message in Discord_related.Split_reply(Help_text):
			await Context.send(Message)

@stars.command(name="revoke")
async def Stars_revoke(Context, Stars_to_revoke: int = None):
	# Revoke a specified number of stars by adding a negative entry in the DB
	# Multiuser debug
	print("[!stars revoke]")
	User = Discord_related.Determine_user(Context.message)
	if User:
		Localized_replies = L10n[User['language']]
		if Context.author.name != Users['bot_owner']['discord_username']:
			await Context.send(Localized_replies['stars_revoke_denied'].format(Bot_owner=User['bot_owner']))
			return
		if not Stars_to_revoke or Stars_to_revoke <= 0:
			await Context.send(Localized_replies['stars_revoke_positive_number'])
			return
		Server_id = Context.guild.id if Context.guild else 0
		Sum_given_stars, Sum_rewards_used = DB_manager.Get_current_balance(User)
		Old_balance = Sum_given_stars - Sum_rewards_used
		DB_manager.Register_star(User, Server_id, Context.channel.id, Context.message.id, -Stars_to_revoke)
		if Stars_to_revoke == 1:
			Number = Localized_replies['stars_just_one']
		elif Stars_to_revoke > 1:
			Number = Stars_to_revoke
		await Context.send(Localized_replies['stars_revoke'].format(Bot_owner=User['bot_owner'], Number=Number, Old_balance=Old_balance, Current_balance=Old_balance-Stars_to_revoke))

@stars.command(name="list")
async def Stars_list(Context, Subcommand: str = None):
	# Display a list of all 🌟 in the DB, with their date and a link to the message
	Send_as_DM = False
	# Multiuser debug
	print("[!stars list]")
	User = Discord_related.Determine_user(Context.message)
	if User:
		Localized_replies = L10n[User['language']]
		if not Subcommand:
			# No subcommand is given = fetch only the last 10 entries
			Stars = DB_manager.Get_stars_list(User, Limit=10)
		elif Subcommand == "all":
			Stars = DB_manager.Get_stars_list(User)
		else:
			await Context.send(Localized_replies['stars_list_unknown_command'].format(Subcommand=Subcommand))
			return
		if not Stars:
			await Context.send(Localized_replies['stars_list_no_star_yet'])
			return
		# If we’re listing all entries and there are more than 10, send it by DM
		if len(Stars) > 10:
			Send_as_DM = True
	
		Stars_list = []
		for Star in Stars:
			Date, Server_id, Channel_id, Message_id, Star_count = Star
			Server_time = Date.strftime("%d/%m %H:%M")
			User_time = (Date.astimezone(ZoneInfo(User['timezone']))).strftime(User['timeformat'])
			Message_link = f"https://discord.com/channels/{Server_id}/{Channel_id}/{Message_id}"
			Line = f"[{Server_time}]({Message_link}) ({User_time}) "
			for Index in range(Star_count):
				Line += "🌟"
			Stars_list.append(Line)
		# Reverse the list, to show the oldest first and the most recent last
		Stars_list.reverse()
		# Split_reply() has a general use case, so its input is a single string
		Stars_list = "\n".join(Stars_list)
		for Message in Discord_related.Split_reply(Stars_list):
			if Send_as_DM:
				await Context.author.send(Message)
			else:
				await Context.send(Message)

@stars.command(name="stats")
async def Stars_stats(Context):
	# Multiuser debug
	print("[!stars stats]")
	User = Discord_related.Determine_user(Context.message)
	if User:
		Localized_replies = L10n[User['language']]
		Sum_given_stars = float(DB_manager.Get_current_balance(User)[0])
		Number_days = (datetime.date.today() - User['start_date']).days
		Number_weeks = Number_days / 7
		if Number_weeks < 1:
			Number_weeks = 1
		Daily_average = round(Sum_given_stars / Number_days, 1)
		Weekly_average = round(Sum_given_stars / Number_weeks, 1)
		await Context.send(Localized_replies['stars_stats'].format(User_nick=User['nick'], Daily_average=Daily_average, Weekly_average=Weekly_average))
