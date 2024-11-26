# -*- coding: utf-8 -*-

import yaml

###############################################################################
# Config file
###############################################################################

with open("Config.yaml", "r") as File:
	Config = yaml.safe_load(File)

Users = Config['Users']
for Name, User_data in Users.items():
	if 'reminders' in User_data:
		User_data['reminders'] = tuple(User_data['reminders'][0])

Rewards_available = {
	Name: tuple(tuple(Task) for Task in Tasks)
	for Name, Tasks in Config['Rewards_available'].items()
}

###############################################################################
# Localization
###############################################################################

with open("Localization.yaml", "r") as File:
	L10n = yaml.safe_load(File)
