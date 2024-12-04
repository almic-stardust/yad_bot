# YAD Bot (Yet Another Discord Bot)

YAD Bot helps your friends achieve their goals. After breaking down their goals into specific tasks, you can give them stars when they complete their tasks.

# Installation

I’m using the bot on a Debian bookworm.

#### Prerequisites

Python 3.9 or later.  
A Discord bot token (see the [help](https://discordpy.readthedocs.io/en/stable/discord.html)).  
A MariaDB or MySQL server.  

Dependencies (Debian packages):
- python3-discord
- python3-yaml
- python3-mysqldb
- python3-requests

#### Database

Create a base, then the tables. Replace \<user\> with the user name in lowercase.

	CREATE TABLE <username>_stars (
	    id              INT AUTO_INCREMENT PRIMARY KEY,
	    date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	    server_id       BIGINT NOT NULL,
	    chan_id         BIGINT NOT NULL,
	    message_id      BIGINT NOT NULL,
	    star_count      INT NOT NULL
	);

	CREATE TABLE <username>_rewards (
	    id              INT AUTO_INCREMENT PRIMARY KEY,
	    date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	    server_id       BIGINT NOT NULL,
	    chan_id         BIGINT NOT NULL,
	    message_id      BIGINT NOT NULL,
	    code            VARCHAR(30) NOT NULL,
	    cost            INT NOT NULL
	);

#### Last steps

	% git clone https://github.com/almic-stardust/yad_bot
	% cd yad_bot

Adjust the configuration to your needs:

Config\_dist.yaml  
Example of configuration file to modify. Rename it as Config.yaml

Localization\_dist.yaml  
Example of localization file to adjust. Rename it as Localization.yaml

	% python3 Bot.py

# Bot’s commands

!stars help  
Show help information about managing the stars.

!rewards help  
Show help information about managing the rewards.

!roll XdY  
Show the result of throwing X dices of Y faces.

# Code structure

The different sections of the bot are separated into modules.

Bot.py  
The main script. Start the bot, and handles events concerning sent/deleted messages (on\_message/on\_raw\_message\_delete).

Config\_manager.py  
Loads and processes the configuration and localizations.

DB\_manager.py  
Manages database-related operations.

Discord\_related.py  
Functions specific to Discord (like splitting replies to stay under Discord’s message size limit).

Stars.py  
Functions to manage the stars.

Rewards.py  
Functions to manage the rewards.
