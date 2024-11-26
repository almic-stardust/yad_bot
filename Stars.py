# -*- coding: utf-8 -*-

from zoneinfo import ZoneInfo
import datetime
from Config_manager import Config, Users, L10n
from Discord_related import bot
import Discord_related
import DB_manager

# We don’t use on_reaction_add() because it doesn’t work for reactions added to messages sent before# the bot was last started (it only considers reactions added to messages in the bot’s cache)
@bot.event
async def on_raw_reaction_add(Payload):
	"""When a 🌟 reaction is added to a message"""
	if str(Payload.emoji) == "🌟":
		try:
			# Retrieving the info from the bot’s cache, without connecting to discord’s servers. No
			# network request = get_guild() is a synchronous function
			Server = bot.get_guild(Payload.guild_id)
			# We use 0 if it’s a DM
			Server_id = Payload.guild_id if Server else 0
			# Retrieving the info from discord’s servers. Network request = so fetch_user(),
			# fetch_channel() and fetch_message() are asynchronous functions
			Author_reaction = await bot.fetch_user(Payload.user_id)
			Channel = await bot.fetch_channel(Payload.channel_id)
			Message = await Channel.fetch_message(Payload.message_id)
			User = Discord_related.Determine_user(Message)
			if User:
				Localized_replies = L10n[User['language']]
				if Author_reaction.name == Users['bot_owner']['discord_username']:
					DB_manager.Register_star(User, Server_id, Channel.id, Message.id, 1)
					if Config['Log_chan']:
						Chan = await Discord_related.Get_chan(bot.get_guild(User['main_server']), Config['Log_chan'])
						if Chan:
							Message_link = f"https://discord.com/channels/{Message.guild.id}/{Message.channel.id}/{Message.id}"
							await Chan.send(Localized_replies['stars_adding_reaction'].format(Bot_owner=User['bot_owner'], Message_link=Message_link))
					else:
						print(f"Can’t send in #{Config['Log_chan']}")
				else:
					await Channel.send(Localized_replies['stars_not_bot_owner'].format(Bot_owner=User['bot_owner'], User_nick=User['nick']))

		except Exception as Error:
			print(f"Error: [on_raw_reaction_add] {Error}")

@bot.event
async def on_raw_reaction_remove(Payload):
	"""When a 🌟 reaction is removed from a message (even if it’s not in the bot’s cache)"""
	if str(Payload.emoji) == "🌟":
		try:
			Author_reaction = await bot.fetch_user(Payload.user_id)
			if Author_reaction.name == Users['bot_owner']['discord_username']:
				Channel = await bot.fetch_channel(Payload.channel_id)
				Message = await Channel.fetch_message(Payload.message_id)
				User = Discord_related.Determine_user(Message)
				if User:
					DB_manager.Remove_star(User, Payload.message_id)
					if Config['Log_chan']:
						Chan = await Discord_related.Get_chan(bot.get_guild(User['main_server']), Config['Log_chan'])
						if Chan:
							Localized_replies = L10n[User['language']]
							await Chan.send(Localized_replies['stars_deleting_reaction'].format(Bot_owner=User['bot_owner']))
					else:
						print(f"Can’t send in #{Config['Log_chan']}")
		except Exception as Error:
			print(f"Error: [on_raw_reaction_remove] {Error}")
	
@bot.group()
async def stars(Context):
	"""If no subcommand is invoked, display the current balance of 🌟 in the DB"""
	if not Context.invoked_subcommand:
		User = Discord_related.Determine_user(Context.message)
		if User:
			Localized_replies = L10n[User['language']]
			Sum_given_stars, Sum_rewards_used = DB_manager.Get_current_balance(User)
			Current_balance = Sum_given_stars - Sum_rewards_used
			await Context.send(Localized_replies['stars_balance'].format(User_nick=User['nick'], Current_balance=Current_balance, Sum_rewards_used=Sum_rewards_used, Sum_given_stars=Sum_given_stars))

@stars.command(name="help")
async def _help(Context):
	User = Discord_related.Determine_user(Context.message)
	if User:
		Localized_replies = L10n[User['language']]
		Help_text = Localized_replies['stars_help']
		for Message in Discord_related.Split_reply(Help_text):
			await Context.send(Message)

@stars.command(name="revoke")
async def _revoke(Context, Stars_to_revoke: int = None):
	"""Revokes a specified number of stars by adding a negative entry in the DB"""
	User = Discord_related.Determine_user(Context.message)
	if User:
		Localized_replies = L10n[User['language']]
		if not Stars_to_revoke:
			await Context.send(Localized_replies['stars_revoke_number_requiered'])
			return
		if Stars_to_revoke <= 0:
			await Context.send(Localized_replies['stars_revoke_positive_number'])
			return
		if Context.author.name == Users['bot_owner']['discord_username']:
			Server_id = Context.guild.id if Context.guild else 0
			Sum_given_stars, Sum_rewards_used = DB_manager.Get_current_balance(User)
			Old_balance = Sum_given_stars - Sum_rewards_used
			DB_manager.Register_star(User, Server_id, Context.channel.id, Context.message.id, -Stars_to_revoke)
			await Context.send(Localized_replies['stars_revoke'].format(Bot_owner=User['bot_owner'], Stars_to_revoke=Stars_to_revoke, Old_balance=Old_balance, Current_balance=Old_balance-Stars_to_revoke))
		else:
			await Context.send(Localized_replies['stars_revoke_denied'].format(Bot_owner=User['bot_owner']))

@stars.command(name="list")
async def _list(Context, Subcommand: str = None):
	"""Displays a list of all 🌟 in the DB, with their date and a link to the message"""
	Send_as_DM = False
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
		for Message in Discord_related.Split_reply(Stars_list):
			if Send_as_DM:
				await Context.author.send(Message)
			else:
				await Context.send(Message)

@stars.command(name="stats")
async def _stats(Context):
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
