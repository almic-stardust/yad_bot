# -*- coding: utf-8 -*-

import MySQLdb

from Config_manager import Config, Users

def Connect_DB():
	try:
		Connection = MySQLdb.connect(**Config["DB_config"])
		return Connection
	except MySQLdb.Error as Error:
		print(f"Error: [MariaDB connection] {Error}")
		sys.exit(1)

def Register_star(User_table, Server_id, Chan_id, Message_id, Star_count):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		# Check if the message is already in the DB
		Cursor.execute(f"""
				SELECT id FROM {User_table}_stars
				WHERE message_id = %s""",
				(Message_id,))
		Result = Cursor.fetchone()
		if Result:
			# Message already recorded = updating its star count
			Cursor.execute(f"""
					UPDATE {User_table}_stars
					SET star_count = star_count + %s
					WHERE message_id = %s""",
					(Star_count, Message_id))
		else:
			# Insert a new record
			Cursor.execute(f"""
					INSERT INTO {User_table}_stars
					(server_id, chan_id, message_id, star_count)
					VALUES (%s, %s, %s, %s)""",
					(Server_id, Chan_id, Message_id, Star_count)
			)
		Connection.commit()
	finally:
		Cursor.close()
		Connection.close()

def Remove_star(User_table, Message_id):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		# Get the current star count
		Cursor.execute(f"""
				SELECT star_count FROM {User_table}_stars
				WHERE message_id = %s""",
				(Message_id,))
		Result = Cursor.fetchone()
		if Result:
			Current_star_count = Result[0]
			if Current_star_count == 1:
				# The star count was 1 and we’re removing it = delete the message from the DB
				Cursor.execute(f"""
						DELETE FROM {User_table}_stars
						WHERE message_id = %s""",
						(Message_id,))
			elif Current_star_count > 1:
				# Decrease the star count by 1
				Cursor.execute(f"""
						UPDATE {User_table}_stars
						SET star_count = star_count - 1
						WHERE message_id = %s""",
						(Message_id,))
			Connection.commit()
	finally:
		Cursor.close()
		Connection.close()

def Remove_message(Message_id):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	Message_subject = Concerned_user = None
	try:
		# Get a list of the *_stars and *_rewards tables in the DB
		Cursor.execute("SHOW TABLES LIKE '%\\_stars'")
		Tables = [Table[0] for Table in Cursor.fetchall()]
		Cursor.execute("SHOW TABLES LIKE '%\\_rewards'")
		Tables += [Table[0] for Table in Cursor.fetchall()]
		for Table in Tables:
			# Check if the table contains a column message_id
			Cursor.execute(f"SHOW COLUMNS FROM {Table} LIKE 'message_id'")
			if Cursor.fetchone():
				Cursor.execute(f"""
						SELECT id FROM {Table}
						WHERE message_id = %s""",
						(Message_id,))
				Result = Cursor.fetchone()
				# If we found an entry matching the deleted message
				if Result:
					# The name of the concerned user is the prefix of the table
					Concerned_user = Table.split("_")[0]
					if "_stars" in Table:
						Message_subject = "Stars"
					elif "_rewards" in Table:
						Message_subject = "Reward"
					Cursor.execute(f"""
							DELETE FROM {Table}
							WHERE message_id = %s""",
							(Message_id,))
					Connection.commit()
					break
		return Concerned_user, Message_subject
	finally:
		Cursor.close()
		Connection.close()

def Get_stars_list(User_table, Limit=None):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		# If Limit is provided, fetch only that many records, else fetch all
		if Limit:
			Cursor.execute(f"""
					SELECT date, server_id, chan_id, message_id, star_count
					FROM {User_table}_stars ORDER BY id DESC LIMIT %s""",
					(Limit,))
		else:
			Cursor.execute(f"""
					SELECT date, server_id, chan_id, message_id, star_count
					FROM {User_table}_stars ORDER BY id DESC""")
		Stars = Cursor.fetchall()
		return Stars
	finally:
		Cursor.close()
		Connection.close()

def Register_reward(User_table, Server_id, Chan_id, Message_id, Code, Cost):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		# Check if the message is already in the DB
		Cursor.execute(f"""
				SELECT id FROM {User_table}_stars
				WHERE message_id = %s""",
				(Message_id,))
		Result = Cursor.fetchone()
		Message_already_present = False
		if Result:
			Message_already_present = True
		else:
			Cursor.execute(f"""
					INSERT INTO {User_table}_rewards
					(server_id, chan_id, message_id, code, cost)
					VALUES (%s, %s, %s, %s, %s)""",
					(Server_id, Chan_id, Message_id, Code, Cost)
			)
		Connection.commit()
		return Message_already_present
	finally:
		Cursor.close()
		Connection.close()

def Get_rewards_list(User_table, Limit=None):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		# If Limit is provided, fetch only that many records, else fetch all
		Request_supplement = ""
		if Limit:
			Request_supplement = f" LIMIT {Limit}"
		Cursor.execute(f"""
				SELECT date, server_id, chan_id, message_id, code, cost
				FROM {User_table}_rewards ORDER BY id DESC{Request_supplement}""")
		Rewards = Cursor.fetchall()
		return Rewards
	finally:
		Cursor.close()
		Connection.close()

def Get_current_balance(User_table):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		#Cursor.execute(
		#	"SELECT "
		#	f"(SELECT SUM(star_count) FROM {User_table}_stars) AS total_stars, "
		#	f"(SELECT SUM(cost) FROM {User_table}_rewards) AS total_rewards"
		#)
		Cursor.execute("""
				SELECT
				(SELECT SUM(star_count) FROM {User_table}_stars)
				AS total_stars,
				(SELECT SUM(cost) FROM {User_table}_rewards)
				AS total_rewards""")
		Result = Cursor.fetchone()
		Sum_given_stars = Result[0] or 0
		Sum_rewards_used = Result[1] or 0
		return Sum_given_stars, Sum_rewards_used
	finally:
		Cursor.close()
		Connection.close()

def History_addition(User_table, Date, Server_id, Chan_id, Message_id, Replied_message_id, Discord_username, Content, Attachments):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		# Check if the message is already in the DB
		Cursor.execute(f"""
				SELECT message_id FROM {User_table}_history
				WHERE message_id = %s""",
				(Message_id,))
		Result = Cursor.fetchone()
		if not Result:
			Cursor.execute(f"""
					INSERT INTO {User_table}_history (
					date_creation,
					server_id, chan_id, message_id,
					reply_to,
					user_name, content, attachments)
					VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (
					Date,
					Server_id, Chan_id, Message_id,
					Replied_message_id,
					Discord_username, Content, Attachments)
			)
		Connection.commit()
	finally:
		Cursor.close()
		Connection.close()

def History_edition(User_table, Message_id, Date, New_content):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		# Check if the message is present in the DB
		Cursor.execute(f"""
				SELECT user_name, content FROM {User_table}_history
				WHERE message_id = %s""",
				(Message_id,))
		Result = Cursor.fetchone()
		if Result:
			Discord_username = Result[0]
			for User in Users.values():
				if Discord_username == User["discord_username"]:
					if "hist_keep_all" in User and User["hist_keep_all"]:
						Old_content = Result[1]
						Edited_content = f"{Old_content}\n\n<|--- Edited {Date} ---|>\n\n{New_content}"
						Request = f"""
								UPDATE {User_table}_history
								SET content = %s, edited = TRUE
								WHERE message_id = %s"""
					else:
						Edited_content = New_content
						Request = f"""
								UPDATE {User_table}_history
								SET content = %s
								WHERE message_id = %s"""
					Cursor.execute(Request, (Edited_content, Message_id))
					break
		Connection.commit()
	finally:
		Cursor.close()
		Connection.close()

def History_deletion(User_table, Message_id, Keep_history, Date, Updated_filenames):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		# Check if the message is in the DB
		Cursor.execute(f"SELECT user_name FROM {User_table}_history WHERE message_id = %s", (Message_id,))
		Result = Cursor.fetchone()
		if Result:
			if Keep_history:
				if Updated_filenames:
					Cursor.execute(f"""
							UPDATE {User_table}_history
							SET attachments = %s, date_deletion = %s
							WHERE message_id = %s""",
							(Updated_filenames, Date, Message_id))
				else:
					Cursor.execute(f"""
							UPDATE {User_table}_history
							SET date_deletion = %s
							WHERE message_id = %s""",
							(Date, Message_id))
			else:
				Cursor.execute(f"""
						DELETE FROM {User_table}_history
						WHERE message_id = %s""",
						(Message_id,))
		Connection.commit()
	finally:
		Cursor.close()
		Connection.close()

def History_fetch_message(User_table, Message_id):
	Connection = Connect_DB()
	Cursor = Connection.cursor()
	try:
		Cursor.execute(f"""
					SELECT
					date_creation,
					server_id,
					chan_id,
					message_id,
					reply_to,
					user_name,
					content,
					attachments,
					reactions,
					date_deletion
					FROM {User_table}_history WHERE message_id = %s""",
					(Message_id,))
		return Cursor.fetchone()
	finally:
		Cursor.close()
		Connection.close()
