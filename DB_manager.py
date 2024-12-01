# -*- coding: utf-8 -*-

import MySQLdb
from Config_manager import Config

def Connect_DB():
	try:
		Connection = MySQLdb.connect(**Config["DB_config"])
		return Connection
	except MySQLdb.Error as Error:
		print(f"Error: [MariaDB connection] {Error}")
		sys.exit(1)

def Register_star(User, Server_id, Channel_id, Message_id, Star_count):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		# Check if the message is already in the DB
		Cursor.execute(f"SELECT id FROM {User['name']}_stars WHERE message_id = %s", (Message_id,))
		Result = Cursor.fetchone()
		if Result:
			# Message already recorded = updating its star count
			Cursor.execute(f"UPDATE {User['name']}_stars SET star_count = star_count + %s WHERE message_id = %s", (Star_count, Message_id))
		else:
			# Insert a new record
			Cursor.execute(
				f"INSERT INTO {User['name']}_stars (server_id, channel_id, message_id, star_count) VALUES (%s, %s, %s, %s)",
				(Server_id, Channel_id, Message_id, Star_count)
			)
		Connection.commit()
	finally:
		Cursor.close()
		Connection.close()

def Remove_star(User, Message_id):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		# Get the current star count
		Cursor.execute(f"SELECT star_count FROM {User['name']}_stars WHERE message_id = %s", (Message_id,))
		Result = Cursor.fetchone()
		if Result:
			Current_star_count = Result[0]
			if Current_star_count == 1:
				# The star count was 1 and we’re removing it = delete the message from the DB
				Cursor.execute(f"DELETE FROM {User['name']}_stars WHERE message_id = %s", (Message_id,))
			elif Current_star_count > 1:
				# Decrease the star count by 1
				Cursor.execute(
					f"UPDATE {User['name']}_stars SET star_count = star_count - 1 WHERE message_id = %s", (Message_id,))
			Connection.commit()
	finally:
		Cursor.close()
		Connection.close()

def Remove_message(Message_id):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	Message_object = Concerned_user = None
	try:
		# Get a list of all tables in the DB
		Cursor.execute("SHOW TABLES")
		Tables = [Table[0] for Table in Cursor.fetchall()]
		for Table in Tables:
			# Check if the table contains a column message_id
			Cursor.execute(f"SHOW COLUMNS FROM {Table} LIKE 'message_id'")
			if Cursor.fetchone():
				Cursor.execute(f"SELECT id FROM {Table} WHERE message_id = %s", (Message_id,))
				Result = Cursor.fetchone()
				# If we found an entry matching the deleted message
				if Result:
					# The name of the concerned user is the prefix of the table
					Concerned_user = Table.split("_")[0]
					if "_stars" in Table:
						Message_object = "Stars"
					elif "_rewards" in Table:
						Message_object = "Reward"
					Cursor.execute(f"DELETE FROM {Table} WHERE message_id = %s", (Message_id,))
					Connection.commit()
					break
		return Concerned_user, Message_object
	finally:
		Cursor.close()
		Connection.close()

def Get_stars_list(User, Limit=None):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		# If Limit is provided, fetch only that many records, else fetch all
		if Limit:
			Cursor.execute(f"SELECT date, server_id, channel_id, message_id, star_count FROM {User['name']}_stars ORDER BY id DESC LIMIT %s", (Limit,))
		else:
			Cursor.execute(f"SELECT date, server_id, channel_id, message_id, star_count FROM {User['name']}_stars ORDER BY id DESC")
		Stars = Cursor.fetchall()
		return Stars
	finally:
		Cursor.close()
		Connection.close()

def Register_reward(User, Server_id, Channel_id, Message_id, Code, Cost):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		# Check if the message is already in the DB
		Cursor.execute(f"SELECT id FROM {User['name']}_stars WHERE message_id = %s", (Message_id,))
		Result = Cursor.fetchone()
		Message_already_present = False
		if Result:
			Message_already_present = True
		else:
			Cursor.execute(
				f"INSERT INTO {User['name']}_rewards (server_id, channel_id, message_id, code, cost) VALUES (%s, %s, %s, %s, %s)",
				(Server_id, Channel_id, Message_id, Code, Cost)
			)
		Connection.commit()
		return Message_already_present
	finally:
		Cursor.close()
		Connection.close()

def Get_rewards_list(User, Limit=None):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		# If Limit is provided, fetch only that many records, else fetch all
		Request_supplement = ""
		if Limit:
			Request_supplement = f" LIMIT {Limit}"
		Cursor.execute(f"SELECT date, server_id, channel_id, message_id, code, cost FROM {User['name']}_rewards ORDER BY id DESC{Request_supplement}")
		Rewards = Cursor.fetchall()
		return Rewards
	finally:
		Cursor.close()
		Connection.close()

def Get_current_balance(User):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		Cursor.execute(
			"SELECT "
			f"(SELECT SUM(star_count) FROM {User['name']}_stars) AS total_stars, "
			f"(SELECT SUM(cost) FROM {User['name']}_rewards) AS total_rewards"
		)
		Result = Cursor.fetchone()
		Sum_given_stars = Result[0] or 0
		Sum_rewards_used = Result[1] or 0
		return Sum_given_stars, Sum_rewards_used
	finally:
		Cursor.close()
		Connection.close()
