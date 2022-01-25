# Discord bot that joins a random channel with people in it at random times, plays a random sound, then leaves

from audioop import add
import discord
from discord import FFmpegPCMAudio
import asyncio
import random
import os

# ffmpeg options to make it so if corrupt packets are sent, then the bot just reconnects instead of terminating
ffmpeg_options = {
    'options': '-vn',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}

# sets up the bot client
client = discord.Client()

# gets the secret bot token by reading it from a local txt file
with open("BotToken.txt", "r") as f:
	token = f.readline().strip()

# string for the bot to detect commands
prefix = ""

# keeps track of which servers the bot is enabled in and which ones it's not
active_in_guild = {}

# keeps track of how frequently the bot joins in each server
timer_for_guild = {}

# keeps track of currently running task for each server
task_for_guild = {}

# called as soon as the bot is fully online and operational
@client.event
async def on_ready():
	# string that goes at the start of commands to help the bot detect the command
	# it is currently "@{botname}"
	global prefix
	prefix = f"<@!{client.user.id}> "
	
	# sets up and starts running the bot for each server it's in simultaneously
	for guild in client.guilds:
		await start_in_server(guild)
	
	print("Bot is running")

# sets up and starts running the bot in a server
async def start_in_server(guild):
	# sets up its variable that keeps track of whether it's enabled or not
	active_in_guild[guild] = True
	# sets the default frequency of the bot joining channels to 1 min - 2 hours
	timer_for_guild[guild] = [60, 7201]
	# creates a task for the bot to start running in for that server
	task_for_guild[guild] = client.loop.create_task(join_loop(guild))

# waits a random amount of time, joins a voice channel channel, plays a random sound, then leaves and repeats
# this function gets run separately for each server the bot is in
async def join_loop(guild):
	# directory that the sound files are kept in
	sound_directory = f"Sounds/server_{guild.id}"
	if not os.path.isdir(sound_directory):
		os.mkdir(sound_directory)
	# message that the bot sends right before it starts playing sounds
	warning_message = "XBOX LIVE"
	while active_in_guild[guild]:
		# waits random amount of time as specified by what the server sets it to (1 min - 2 hours default)
		await asyncio.sleep(random.randrange(timer_for_guild[guild][0], timer_for_guild[guild][1]))
		# gets a list of all voice channels with people in them currently
		populated_channels = get_populated_vcs(guild)
		# if there are any channels with people in them, then pick and random audio file, join a random channel with people, and play the file
		if len(populated_channels) > 0:
			# pick a random channel to join
			channel = random.choice(populated_channels)
			# pick a random sound to play
			sound = random.choice(get_sounds(sound_directory))
			sound_file = f"{sound_directory}/{sound}"
			# prints the sound it's about to play
			print(f"Now playing in {guild.name}: {sound}")
			# get top channel bot is allowed to read and send messages in for the server
			text_channel = get_warning_channel(guild)
			# if the sound file exists
			if os.path.isfile(sound_file):
				voice_client = discord.utils.get(client.voice_clients, guild=guild)
				# if the bot is already connected to a voice channel in this server, then wait until it leaves
				if voice_client:
					while voice_client.is_connected():
						print("currently in while loop")
						await asyncio.sleep(0.1)
				# join the channel
				voice = await channel.connect()
				# if there is a channel the bot can read + send in, and the last message wasn't a warning message, then send a warning message
				last_message = text_channel.last_message
				if text_channel and not (last_message and last_message.author.id == client.user.id and last_message.content == warning_message):
					await text_channel.send(warning_message)
				# play the file
				voice.play(FFmpegPCMAudio(f"{sound_directory}/{sound}"))
				# wait until bot is not playing anymore audio
				while voice.is_playing():
					await asyncio.sleep(0.1)
				# wait about 1 second since there's a bit of lag with ffmpeg
				await asyncio.sleep(1)
				# then disconnect the bot
				if guild.voice_client:
					await guild.voice_client.disconnect()
			# otherwise, print error message
			else:
				print(f"No sound file found in {guild.name} {{id={guild.id}}})")

# returns a list of all voice channels with at least one person in them
def get_populated_vcs(guild):
	vcs = []
	# for each voice channel in the server
	for c in guild.voice_channels:
		perms = c.permissions_for(guild.me)
		# if the channel has people in it, isn't an afk channel, and the bot has permission to join + speak, add it to the list
		if len(c.voice_states) > 0 and (not guild.afk_channel or c.id != guild.afk_channel.id) and perms.connect and perms.speak:
			vcs.append(c)
	return vcs

# returns a list of all sound files
def get_sounds(directory):
	sounds = []
	# for each subdirectory in the sound directory
	for (path, dir, files) in os.walk(directory):
		# for each file in the sound directory
		for file in files:
			# add all files that end with .mp3 or .wav to the list of sounds
			if file.endswith(".mp3") or file.endswith(".wav"):
				sounds.append(file)
	return sounds

# gets the top channel the bot is allowed to read and message in
def get_warning_channel(guild):
	# for each text channel in the server
	for c in guild.text_channels:
		perms = c.permissions_for(guild.me)
		# if the bot has permission to read and send messages in this channel, use it
		if perms.read_messages and perms.send_messages:
			return c
	# if there are no available channels, return nothing
	return None

# handles commands
@client.event
async def on_message(message):
	# if the message has the command prefix and is not a dm
	if message.content.startswith(prefix) and message.guild:
		command = message.content.split()
		# if the command has any arguments
		if len(command) > 1:
			adder_role = "Random Sound Bot Adder"
			remover_role = "Random Sound Bot Remover"
			sound_dir = f"Sounds/server_{message.guild.id}"
			perms = message.channel.permissions_for(message.guild.me)
			global active
			# if help command
			if command[1].lower() == "help":
				# if the bot has permission to send messages in this channel
				if perms.send_messages:
					# define info for every command to reply with
					example_prefix = f"`@{client.user.name}`"
					help_info = f"{example_prefix} help {{command name (optional)}}:"
					help_info += f"\n> Gives descriptions of how to use all or one of this bot's commands"
					leave_info = f"{example_prefix} leave:"
					leave_info += f"\n> Makes the bot leave the voice channel it's currently in"
					stfu_info = f"{example_prefix} stfu:"
					stfu_info += f"\n> Makes the bot shut up until you re-enable it with the \"activate\" command"
					activate_info = f"{example_prefix} activate:"
					activate_info += f"\n> Allows the bot to join channels randomly again after being disabled by the \"stfu\" command"
					onq_info = f"{example_prefix} on?:"
					onq_info += f"\n> Tells you if the bot is currently enabled or disabled in your server"
					add_info = f"{example_prefix} add {{file attatchment(s)}}:"
					add_info += f"\n> Adds sounds to this server's sound list if you attach mp3 or wav files"
					remove_info = f"{example_prefix} remove {{file name(s)}}:"
					remove_info += f"\n> Deletes any files listed from this server's sound list"
					rename_info = f"{example_prefix} rename {{file name}} {{new name}}:"
					rename_info += f"\n> Renames a file in this server's sound list"
					list_info = f"{example_prefix} list:"
					list_info += f"\n> Sends all of the sound files that this server has to use"
					give_info = f"{example_prefix} give {{file name(s)}}:"
					give_info += f"\n> Sends copies of sound files that are being used on this server"
					timer_info = f"{example_prefix} timer {{minimum frequency}} {{maximum frequency}}:"
					timer_info += f"\n> Changes the frequency of when the bot joins channels"
					timerq_info = f"{example_prefix} timer?:"
					timerq_info += f"\n> Tells you the time range for how often the bot will randomly join"
					reset_info = f"{example_prefix} reset:"
					reset_info += f"\n> Resets the bot's waiting time to join"
					play_info = f"{example_prefix} play {{file name}}:"
					play_info += f"\n> Makes the bot join your voice channel and play a sound from this server's sound list that you input"
					
					# returns a string that lists info about every command
					def get_help_message():
						help_message = "List of commands"
						help_message += f"\n\n{help_info}"
						help_message += f"\n\n{leave_info}"
						help_message += f"\n\n{stfu_info}"
						help_message += f"\n\n{activate_info}"
						help_message += f"\n\n{onq_info}"
						help_message += f"\n\n{add_info}"
						help_message += f"\n\n{remove_info}"
						help_message += f"\n\n{rename_info}"
						help_message += f"\n\n{list_info}"
						help_message += f"\n\n{give_info}"
						help_message += f"\n\n{timer_info}"
						help_message += f"\n\n{timerq_info}"
						help_message += f"\n\n{reset_info}"
						help_message += f"\n\n{play_info}"
						help_message += f"\n\nType \"{example_prefix} help {{command name}}\" for examples and more info about a command"
						return help_message

					# if there is an argument to the help command
					if len(command) > 2:
						# reply with info about the command in the argument
						if command[2].lower() == "help":
							help_info += "\n> Examples:"
							help_info += f"\n> {example_prefix} help"
							help_info += f"\n> {example_prefix} help stfu"
							help_info += f"\n> {example_prefix} help timer"
							await message.reply(help_info)
						elif command[2].lower() == "leave":
							leave_info += "\n> Example:"
							leave_info += f"\n> {example_prefix} leave"
							await message.reply(leave_info)
						elif command[2].lower() == "stfu":
							stfu_info += "\n> Note: This command will reset the bot's waiting time to join a channel"
							stfu_info += "\n> Example:"
							stfu_info += f"\n> {example_prefix} stfu"
							await message.reply(stfu_info)
						elif command[2].lower() == "activate":
							activate_info += "\n> Note: The \"stfu\" command resets the bot's waiting time to join a channel"
							activate_info += "\n> Example:"
							activate_info += f"\n> {example_prefix} activate"
							await message.reply(activate_info)
						elif command[2].lower() == "on?":
							onq_info += "\n> Example:"
							onq_info += f"\n> {example_prefix} on?"
							await message.reply(onq_info)
						elif command[2].lower() == "add":
							add_info += "\n> In order for this command to work:"
							add_info += "\n> The attached files must be in the same message as the command"
							add_info += "\n> The attached files must have names that are less than 128 characters long"
							add_info += "\n> The user must have a role with the name \"Random Sound Bot Adder\" in the server"
							add_info += "\n> Examples:"
							add_info += f"\n> {example_prefix} add {{attached file: example_file.mp3}}"
							add_info += f"\n> {example_prefix} add {{attached file: example_file_1.wav}} {{attached file: example_file_2.mp3}}"
							await message.reply(add_info)
						elif command[2].lower() == "remove":
							remove_info += "\n> In order for this command to work, the user must have a role with the name \"Random Sound Bot Remover\" in the server"
							remove_info += "\n> Examples:"
							remove_info += f"\n> {example_prefix} remove example_file.mp3"
							remove_info += f"\n> {example_prefix} remove example_file_1.wav example_file_2.mp3"
							await message.reply(remove_info)
						elif command[2].lower() == "rename":
							rename_info += "\n> In order for this command to work:"
							rename_info += "\n> The file extension of the new name must match the file extension of the old name"
							rename_info += "\n> The new file name must not contain any slashes or backslashes"
							rename_info += "\n> The new file name must be less than 128 characters long"
							rename_info += "\n> The user must have a role with the name \"Random Sound Bot Adder\" in the server"
							rename_info += "\n> Examples:"
							rename_info += f"\n> {example_prefix} rename old_file_name.mp3 new_file_name.mp3"
							rename_info += f"\n> {example_prefix} rename old_file_name.wav new_file_name.wav"
							await message.reply(rename_info)
						elif command[2].lower() == "list":
							list_info += "\n> Example:"
							list_info += f"\n> {example_prefix} list"
							await message.reply(list_info)
						elif command[2].lower() == "give":
							give_info += "\n> Examples:"
							give_info += f"\n> {example_prefix} give example_file.mp3"
							give_info += f"\n> {example_prefix} give example_file_1.wav example_file_2.mp3"
							await message.reply(give_info)
						elif command[2].lower() == "timer":
							timer_info += "\n> Arguments must either be a positive number of seconds, or in colon format"
							timer_info += "\n> Colon format: \"hrs:min:sec\", Ex: \"1:30:15\" (1 hour, 30 minutes, and 15 seconds)"
							timer_info += "\n> This command does not automatically reset the bot's current countdown to join"
							timer_info += "\n> In other words, this command will not take effect until either the next time the bot joins, or the \"reset\" command is used"
							timer_info += "\n> Examples:"
							timer_info += f"\n> {example_prefix} timer 60 120"
							timer_info += f"\n> {example_prefix} timer 0:30:0 1:0:0"
							timer_info += f"\n> {example_prefix} timer 0:0:30 3600"
							await message.reply(timer_info)
						elif command[2].lower() == "timer?":
							timerq_info += "\n> Example:"
							timerq_info += f"\n> {example_prefix} timer?"
							await message.reply(timerq_info)
						elif command[2].lower() == "reset":
							reset_info += "\n> Use this command after using the \"timer\" command if you want the new frequency you inputted to take effect before the next time the bot joins a channel"
							reset_info += "\n> Example:"
							reset_info += f"\n> {example_prefix} reset"
							await message.reply(reset_info)
						elif command[2].lower() == "play":
							play_info += "\n> If the user is in a voice channel when this command is used, the bot will join the user's voice channel"
							play_info += "\n> If the user is not in a voice channel when this command is used, the bot will pick a random channel with people in it to join"
							play_info += "\n> Examples:"
							play_info += f"\n> {example_prefix} play example_file.mp3"
							play_info += f"\n> {example_prefix} play example_file.wav"
							await message.reply(play_info)
						# otherwise reply with info about every command
						else:
							await message.reply(get_help_message())
					# if there are no arguments
					else:
						# reply with info about every command
						await message.reply(get_help_message())
				else:
					await react_with_x(message)
			# if leave command
			elif command[1].lower() == "leave":
				voice_client = discord.utils.get(client.voice_clients, guild = message.guild)
				# if the bot is connected to a channel in that server, then leave
				if voice_client and voice_client.is_connected():
					voice_client.stop()
				else:
					await react_with_x(message)
			# if stfu (shut the fuck up) command
			elif command[1].lower() == "stfu":
				# if the bot is currently active
				if active_in_guild[message.guild]:
					# disable the bot in that server
					active_in_guild[message.guild] = False
					# stop join loop for server
					task_for_guild[message.guild].cancel()
					# if the bot is connected to a channel in that server, then leave
					voice_client = discord.utils.get(client.voice_clients, guild = message.guild)
					if voice_client and voice_client.is_connected():
						voice_client.stop()
					# reacts to message with a checkmark emoji when done
					await react_with_check(message)
				# if bot is already disabled
				else:
					# react to message with a X emoji
					await react_with_x(message)
			# if activate command
			elif command[1].lower() == "activate":
				# if the bot is not currently active
				if not active_in_guild[message.guild]:
					# enable the bot in that server
					active_in_guild[message.guild] = True
					# recreate a task for that server
					task_for_guild[message.guild] = client.loop.create_task(join_loop(message.guild))
					# reacts to message with a checkmark emoji when done
					await react_with_check(message)
				# if bot is already enabled
				else:
					await react_with_x(message)
			# if on? command
			elif command[1].lower() == "on?":
				# if the bot is enabled, react with checkmark
				if active_in_guild[message.guild]:
					await react_with_check(message)
				# if the bot is off, react with X
				else:
					await react_with_x(message)
			# if add command
			elif command[1].lower() == "add":
				# if the message author has the role that allows them to use this command and the message has attatched files
				if any(role.name == adder_role for role in message.author.roles) and message.attachments:
					errors = []
					# check each file in the message
					for file in message.attachments:
						# if the file is an mp3 or wav file, the file doesn't contain a "/" or "\" in the name (for security redundancy), and the file name is less than 128 characters long
						if (file.filename.endswith(".mp3") or file.filename.endswith(".wav")) and not "/" in file.filename and not "\\" in file.filename and len(file.filename) < 128:
							# save the file to the directory of the server the message was from
							await file.save(f"{sound_dir}/{file.filename}")
						# if the file couldn't be saved, add it to the error list
						else:
							errors.append(file.filename)
					# reacts to message with a checkmark emoji when done
					if len(message.attachments) > len(errors):
						await react_with_check(message)
					# if none of the files could be saved, react with an X emoji
					else:
						await react_with_x(message)
					# if there were any files that couldn't be processed, reply with them
					if errors:
						await message.reply(get_file_error_message(errors))
				else:
					await react_with_x(message)
			# if remove command
			elif command[1].lower() == "remove":
				# if the message author has the role that allows them to use this command and the message command has arguments
				if any(role.name == remover_role for role in message.author.roles) and len(command) > 2:
					errors = []
					# go and remove each file in the arguments
					for file in command[2:]:
						filepath = f"{sound_dir}/{file}"
						# if the argument doesn't contain "/" or "\" (for security redundancy) and the file exists
						if not "/" in file and not "\\" in file and os.path.isfile(filepath):
							# delete the file
							os.remove(filepath)
						else:
							errors.append(file)
					# reacts to message with a checkmark emoji when done
					if len(command[2:]) > len(errors):
						await react_with_check(message)
					# if no files were deleted, then react with X emoji
					else:
						await react_with_x(message)
					# if there were any files that couldn't be processed, reply with them
					if errors:
						await message.reply(get_file_error_message(errors))
				else:
					await react_with_x(message)
			# if rename command
			elif command[1].lower() == "rename":
				# if the person has the role that allows them to use this command and the command has enough arguments
				if any(role.name == adder_role for role in message.author.roles) and len(command) > 3:
					old_dir = f"{sound_dir}/{command[2]}"
					# if the file exists, the arguments don't contain "/" or "\" (for security redundancy), the new name has an mp3 or wav file extension that matches the old file name extension, and the new file name is less than 128 characters long
					if os.path.isfile(old_dir) and not "/" in command[2] and not "\\" in command[2] and not "/" in command[3] and not "\\" in command[3] and (command[2].endswith(".mp3") and (command[3].endswith(".mp3")) or (command[2].endswith(".wav") and command[3].endswith(".wav"))) and len(command[3] < 128):
						# rename the file and react with a check
						new_dir = f"{sound_dir}/{command[3]}"
						os.rename(old_dir, new_dir)
						await react_with_check(message)
					else:
						await react_with_x(message)
				else:
					await react_with_x(message)
			# if list command
			elif command[1].lower() == "list":
				# if the bot has permission to send messages in this channel
				if perms.send_messages:
					# get a list of all sound files in the server's sound folder
					sounds = get_sounds(f"{sound_dir}")
					# sort the sounds in alphabetical order
					sounds.sort()
					sound_message = f"```List of sounds for {message.guild.name[:128]}:"
					# put all of the sounds into a single string
					for s in sounds:
						# if the message length is at the max discord will allow
						if len(f"{sound_message}\n{s}") >= 1997:
							# reply with the current string of files
							sound_message += "```"
							await message.reply(sound_message)
							# start the string over and continue to add more
							sound_message = f"```List of sounds for {message.guild.name[:128]} continued:"
						sound_message += f"\n{s}"
					sound_message += "```"
					# reply with the list of sound files for the server
					await message.reply(sound_message)
				else:
					react_with_x(message)
			# if give command
			elif command[1].lower() == "give":
				# if the command has arguments and the bot can send messages
				if len(command) > 2 and perms.send_messages:
					files = []
					errors = []
					# loop through each argument
					for filename in command[2:]:
						filepath = f"{sound_dir}/{filename}"
						# if the argument doesn't contain "/" (for security redundancy), if the file exists, and if the file is less than 10mb (discord limitation)
						if not "/" in filename and os.path.isfile(filepath) and os.path.getsize(filepath) < 10_000_000:
							# add the file to the list of files to send
							files.append(discord.File(filepath))
							# if there are 10 files in the list
							if len(files) == 10:
								# force send the list then continue adding more files (since discord only lets you send 10 files at once max)
								await message.reply(files=files)
								files = []
						# if the file can't be processed, add to error list
						else:
							errors.append(filename)
					# if there are any files in the list, send it
					if files:
						await message.reply(files=files)
					# if there were any files that couldn't be processed, reply with them
					if errors:
						await message.reply(get_file_error_message(errors))
				else:
					react_with_x(message)
			# if timer command
			elif command[1].lower() == "timer":
				# if there are enough arguments
				if len(command) > 3:
					async def process_args(arg):
						time = None
						# if the argument is a number, get it
						try:
							time = float(arg)
						# otherwise, see if it's in colon format
						except:
							if ":" in arg:
								time = arg.split(":", 2)
								# if the argument is not in colon format, stop
								for n in range(0, len(time)):
									try:
										time[n] = float(time[n])
									except:
										return
								# if the argument has 2 values
								if len(time) == 2:
									time[0] *= 60
									time = time[0] + time[1]
								# if the argument has 3 values
								elif len(time) == 3:
									time[0] *= 3600
									time[1] *= 60
									time = time[0] + time[1] + time[2]
								else:
									return
							else:
								return
						return time
					# try to get the numbers from each argument
					min = await process_args(command[2])
					max = await process_args(command[3])
					# double check to make sure min and max timers are valid
					if type(min) is float and type(max) is float:
						# makes sure the min is not larger than the max
						if min <= max:
							timer_for_guild[message.guild][0] = min
							timer_for_guild[message.guild][1] = max + 1 # adds 1 since the randrange function uses a delimiter rather than an upper bound
							# reacts to message with a checkmark emoji when done
							await react_with_check(message)
						else:
							await react_with_x(message)
					else:
						await react_with_x(message)
				else:
					await react_with_x(message)
			# if timer? command
			elif command[1].lower() == "timer?":
				# if the bot has permission to send messages in the channel of the command
				if perms.send_messages:
					# calculate the hours, minutes, and seconds for min and max
					min_hrs = int(timer_for_guild[message.guild][0] // 3600)
					min_min = int(timer_for_guild[message.guild][0] // 60 % 60)
					min_sec = timer_for_guild[message.guild][0] % 60
					# temp variable for max frequency since it needs to have 1 second subtracted from it
					max_tmp = timer_for_guild[message.guild][1] - 1
					max_hrs = int(max_tmp // 3600)
					max_min = int(max_tmp // 60 % 60)
					max_sec = (max_tmp) % 60
					# reply with bot join frequency
					await message.reply(f"Bot will join every `{min_hrs} hours {min_min} mins {min_sec} secs` to `{max_hrs} hours {max_min} mins {max_sec} secs`")
				else:
					await react_with_x(message)
			# if reset command
			elif command[1].lower() == "reset":
				# reset the task for waiting and joining randomly
				task_for_guild[message.guild].cancel()
				task_for_guild[message.guild] = client.loop.create_task(join_loop(message.guild))
				await react_with_check(message)
			# if play command
			elif command[1].lower() == "play":
				voice_client = discord.utils.get(client.voice_clients, guild = message.guild)
				# if the bot is enabled in the server, there are arguments, the bot isn't already in a voice channel, and the bot has permission to join and speak in the channel
				if active_in_guild[message.guild] and len(command) > 2 and not (voice_client and voice_client.is_connected()):
					channel = None
					v_perms = None
					# if the author is in a voice channel
					if message.author.voice:
						# prepare to join their channel
						channel = message.author.voice.channel
						v_perms = channel.permissions_for(channel.guild.me)
					# if the author is not in a voice channel
					else:
						# pick a random populated voice channel to join in that server
						populated_channels = get_populated_vcs(message.guild)
						if len(populated_channels) > 0:
							channel = random.choice(populated_channels)
							v_perms = channel.permissions_for(channel.guild.me)
					# if the bot has a channel to join that they are allowed to join and speak in
					if channel and v_perms and v_perms.connect and v_perms.speak:
						sound_directory = f"{sound_dir}/{command[2]}"
						# if the argument doesn't contain "/" or "\" (for security redundancy) and the file in the argument exists
						if not "/" in command[2] and not "\\" in command[2] and os.path.isfile(sound_directory):
							# connect and play the audio
							voice = await channel.connect()
							voice.play(FFmpegPCMAudio(sound_directory))
							while voice.is_playing():
								await asyncio.sleep(0.1)
							await asyncio.sleep(1)
							# disconnect when done playing
							if message.guild.voice_client:
								await message.guild.voice_client.disconnect()
						else:
							await react_with_x(message)
					else:
						await react_with_x(message)
				else:
					await react_with_x(message)

# makes the bot react to a message with a checkmark emoji if it's able to
async def react_with_check(message):
	perms = message.channel.permissions_for(message.guild.me)
	if perms.add_reactions:
		await message.add_reaction("\u2705")

# makes the bot react to a message with an X emoji if it's able to
async def react_with_x(message):
	perms = message.channel.permissions_for(message.guild.me)
	if perms.add_reactions:
		await message.add_reaction("\u274c")

# returns an errors message containing files in a list
def get_file_error_message(errors):
	if len(errors) > 0:
		error_message = "```Could not process the following file"
		if len(errors) > 1:
			error_message += "s"
		error_message += ":"
		for s in errors:
			error_message += f"\n{s}"
		error_message += "```"
		return error_message

# sets up the bot every time it joins a new server while running
@client.event
async def on_guild_join(guild):
	start_in_server(guild)

# runs the bot
client.run(token)
