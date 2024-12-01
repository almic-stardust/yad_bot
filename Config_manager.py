# -*- coding: utf-8 -*-

import yaml

###############################################################################
# Config file
###############################################################################

with open("Config.yaml", "r") as File:
	Config = yaml.safe_load(File)

Users = Config["Users"]
for Name, User in Users.items():
	if Name != "bot_owner":
		User["name"] = Name
	if "reminders" in User:
		User["reminders"] = tuple(User["reminders"][0])

Rewards_available = {
	Name: tuple(tuple(Task) for Task in Tasks)
	for Name, Tasks in Config["Rewards_available"].items()
}

###############################################################################
# Localization
###############################################################################

with open("Localization.yaml", "r") as File:
	L10n = yaml.safe_load(File)
