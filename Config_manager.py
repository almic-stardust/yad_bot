# -*- coding: utf-8 -*-

import yaml

###############################################################################
# Configuration
###############################################################################

with open("Config.yaml", "r") as File:
	Config = yaml.safe_load(File)

Users = Config["Users"]
for Name, User in Users.items():
	User["name"] = Name
	if "events" in User:
		User["events"] = tuple(User["events"][0])

Rewards_available = {
	Name: tuple(tuple(Task) for Task in Tasks)
	for Name, Tasks in Config["Rewards_available"].items()
}

###############################################################################
# Localization
###############################################################################

with open("Localization.yaml", "r") as File:
	L10n = yaml.safe_load(File)
