# -*- coding: utf-8 -*-

import random
from Config_manager import L10n
from Discord_related import bot
import Discord_related

@bot.command()
async def roll(Context, Dice: str):
	"""Rolls a dice in NdN format"""
	User = Discord_related.Determine_user(Context.message)
	if User:
		Localized_replies = L10n[User['language']]
		try:
			Rolls, Limit = map(int, Dice.split("d"))
		except Exception:
			await Context.send(Localized_replies['roll_error'])
			return
		Result = ", ".join(str(random.randint(1, Limit)) for r in range(Rolls))
		await Context.send(Result)
