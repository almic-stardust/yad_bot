# -*- coding: utf-8 -*-

from zoneinfo import ZoneInfo
from Config_manager import Users, Rewards_available, L10n
from Discord_related import bot
import Discord_related
import DB_manager

@bot.group()
async def rewards(Context):
	"""If no subcommand is invoked, display the available rewards"""
	if not Context.invoked_subcommand:
		User = Discord_related.Determine_user(Context.message)
		if User:
			Localized_replies = L10n[User['language']]
			if User['name'] in Rewards_available:
				Display_rewards = []
				Index = 1
				for Reward in Rewards_available[User['name']]:
					Display_rewards.append(f"{Index}. ({Reward[1]} 🌟) {Reward[2]} [{Reward[0]}]")
					Index += 1
				for Message in Discord_related.Split_reply(Display_rewards):
					await Context.send(Message)
			else:
				await Chan.send(Localized_replies['rewards_not_present_error'])

@rewards.command(name="help")
async def _help(Context):
	User = Discord_related.Determine_user(Context.message)
	if User:
		Localized_replies = L10n[User['language']]
		Help_text = Localized_replies['rewards_help'].format(Bot_owner=User['bot_owner'])
		for Message in Discord_related.Split_reply(Help_text):
			await Context.send(Message)

@rewards.command(name="record")
async def _record(Context, Subcommand: str = None):
	"""Command to register a reward"""
	User = Discord_related.Determine_user(Context.message)
	if User:
		Localized_replies = L10n[User['language']]
		if not Subcommand:
			await Context.send(Localized_replies['rewards_record_missing_code'])
			return
		if User['name'] not in Rewards_available:
			await Context.send(Localized_replies['rewards_record_no_reward_listed'].format(User_nick=User['nick']))
			return
		ID_reward = Index = -1
		for Reward in Rewards_available[User['name']]:
			Index += 1
			if Subcommand == Reward[0]:
				ID_reward = Index
				break
		if ID_reward == -1:
			await Context.send(Localized_replies['rewards_record_unknown_reward'].format(Subcommand=Subcommand))
			return

		Cost = Rewards_available[User['name']][ID_reward][1]
		Sum_given_stars, Sum_rewards_used = DB_manager.Get_current_balance(User)
		Current_balance = Sum_given_stars - Sum_rewards_used
		if Current_balance < Cost:
			await Context.send(Localized_replies['rewards_record_insufficient_balance'].format(Cost=Cost, Current_balance=Current_balance))
			return
		if Context.author.name == Users['bot_owner']['discord_username']:
			Server_id = Context.guild.id if Context.guild else 0
			Message_already_present = DB_manager.Register_reward(User, Server_id, Context.channel.id, Context.message.id, Subcommand, Cost)
			if Message_already_present:
				print("Error: this message is already associated with a reward in the DB")
			else:
				await Context.send(Localized_replies['rewards_record_registered'])
		else:
			await Context.send(Localized_replies['rewards_record_denied'].format(Bot_owner=User['bot_owner']))

@rewards.command(name="list")
async def _list(Context, Subcommand: str = None):
	"""Displays a list of all 🌟 in the DB, with their date and a link to the message"""
	Send_as_DM = False
	User = Discord_related.Determine_user(Context.message)
	if User:
		Localized_replies = L10n[User['language']]
		if not Subcommand:
			Rewards_list = DB_manager.Get_rewards_list(User, Limit=10)
		elif Subcommand == "all":
			Rewards_list = DB_manager.Get_rewards_list(User)
		else:
			await Context.send(Localized_replies['rewards_list_unknown_command'].format(Subcommand=Subcommand))
			return
		if not Rewards_list:
			await Context.send(Localized_replies['rewards_list_no_reward_yet'])
			return
		if len(Rewards_list) > 10:
			Send_as_DM = True

		Display_rewards = []
		for Reward in Rewards_list:
			Date, Server_id, Channel_id, Message_id, Code, Cost = Reward
			Server_time = Date.strftime("%d/%m %H:%M")
			User_time = (Date.astimezone(ZoneInfo(User['timezone']))).strftime(User['timeformat'])
			Message_link = f"https://discord.com/channels/{Server_id}/{Channel_id}/{Message_id}"
			Display_rewards.append(f"[{Server_time}]({Message_link}) ({User_time}) {Code} ({Cost} 🌟)")
		# Reverse the list, to show the oldest first and the most recent last
		Display_rewards.reverse()
		for Message in Discord_related.Split_reply(Display_rewards):
			if Send_as_DM:
				await Context.author.send(Message)
			else:
				await Context.send(Message)
