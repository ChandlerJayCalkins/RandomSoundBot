# Discord bot that joins a random channel with people in it at random times, plays a random sound, then leaves

# Permissions Required:
# Read Messages/View Channels
# Send Messages
# Attach Files
# Read Message History
# Add Reactions
# Connect
# Speak

# Recommended Permissions (for testing new features):
# Change Nickname
# Read Messages / View Channels
# Send Messages
# Create Public Threads
# Create Private Threads
# Send Messages in Threads
# Embed Links
# Attach Files
# Read Message History
# Use External Emojis
# Use External Stickers
# Add Reactions
# Use Slash Commands
# Connect
# Speak
# Video

# TODO
# 1. Make it so the bot can log events and activity
# 2. Make it so users can change what channel the bot sends alert messages in
# 2. Combine the stfu, on, alertoff, and alerton code into one function if reasonable

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
enabled_in_guild = {}

# keeps track of how frequently the bot joins in each server
timer_for_guild = {}

# keeps track of whether or not the alert is enabled in each server
alerton_for_guild = {}

# keeps track of the message the bot sends when it randomly joins a channel for each server
alert_for_guild = {}

# keeps track of currently running task for each server
task_for_guild = {}

# keeps track of timed stfu and on commands
twaiter_for_guild = {}

# keeps track of timed alerton and alertoff commands
awaiter_for_guild = {}

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
	folder_name = f"server_{guild.id}"
	sound_directory = f"Sounds/{folder_name}"
	setting_directory = f"Settings/{folder_name}"
	log_directory = f"Logs/{folder_name}"
	# if the server does not have sound, setting, or log folders, then make whichever ones are missing
	if not os.path.isdir(sound_directory):
		os.mkdir(sound_directory)
	if not os.path.isdir(setting_directory):
		os.mkdir(setting_directory)
	if not os.path.isdir(log_directory):
		os.mkdir(log_directory)
	settings_file = f"{setting_directory}/Settings.set"
	# bot is enabled by default
	default_enabled = True
	# default random time to join is 1 min - 2 hours
	default_min_timer = 60.0
	default_max_timer = 7201.0
	# bot's alert message is on by default
	default_alerton = True
	# default message that the bot sends when it joins a channel randomly
	default_alert = ""
	with open("DefaultAlert.txt", "r") as file:
		default_alert = file.read(2000).strip()
	# if the server alread has a settings file, then read from it
	if os.path.isfile(settings_file):
		settings = []
		# expected size of settings
		num_of_settings = 6
		# flat to tell the bot to rewrite to the settings file if an error was found in it
		error_detected = False
		with open(settings_file, "r") as file:
			settings = file.readlines()
		# if the enabled setting is in the file
		if len(settings) > 1 and settings[1].startswith("enabled:"):
			# read the enabled setting
			try:
				enabled_in_guild[guild] = settings[1][8:].strip().lower() == "true"
			# remake the enabled setting
			except:
				enabled_in_guild[guild] = default_enabled
				settings[1] = f"enabled: {default_enabled}\n"
				error_detected = True
		# remake the enabled setting
		else:
			enabled_in_guild[guild] = default_enabled
			if len(settings) > 1:
				settings[1] = f"enabled: {default_enabled}\n"
			else:
				settings.append(f"enabled: {default_enabled}\n")
			error_detected = True
		timer_for_guild[guild] = [default_min_timer, default_max_timer]
		# if the min timer setting is in the file
		if len(settings) > 2 and settings[2].startswith("min_timer:"):
			# read the min timer setting
			try:
				timer_for_guild[guild][0] = float(settings[2][10:].strip())
			# remake the min timer setting
			except:
				timer_for_guild[guild][0] = default_min_timer
				settings[2] = f"min_timer: {default_min_timer}\n"
				error_detected = True
		# remake the min timer setting
		else:
			timer_for_guild[0] = default_min_timer
			if len(settings) > 2:
				settings[2] = f"min_timer: {default_min_timer}\n"
			else:
				settings.append(f"min_timer: {default_min_timer}\n")
			error_detected = True
		# if the max timer setting is in the file
		if len(settings) > 3 and settings[3].startswith("max_timer:"):
			# read the max timer setting
			try:
				timer_for_guild[guild][1] = float(settings[3][10:].strip())
			# remake the max timer setting
			except:
				timer_for_guild[guild][1] = default_max_timer
				settings[3] = f"max_timer: {default_max_timer}\n"
				error_detected = True
		# remake the max timer setting
		else:
			timer_for_guild[guild][1] = default_max_timer
			if len(settings) > 3:
				settings[3] = f"max_timer: {default_max_timer}\n"
			else:
				settings.append(f"max_timer: {default_max_timer}\n")
			error_detected = True
		# if the alert on setting is in the file
		if len(settings) > 4 and settings[4].startswith("alert_on:"):
			# read the alert on setting
			try:
				alerton_for_guild[guild] = settings[4][9:].strip().lower == "true"
			# remake the alert on setting
			except:
				alerton_for_guild[guild] = default_alerton
				settings[4] = f"alert_on: {default_alerton}\n"
				error_detected = True
		# remake the alert on setting
		else:
			alerton_for_guild[guild] = default_alerton
			if len(settings) > 4:
				settings[4] = f"alert_on: {default_alerton}\n"
			else:
				settings.append(f"alert_on: {default_alerton}\n")
			error_detected = True
		# if the alert message setting is in the file
		if len(settings) > 5 and settings[5].startswith("alert:"):
			# read the alert message setting
			try:
				alert_for_guild[guild] = settings[5][6:].strip()
			# remake the alert message setting
			except:
				alert_for_guild[guild] = default_alert
				settings[5] = f"alert: {default_alert}\n"
				error_detected = True
		# remake the alert message setting
		else:
			alert_for_guild[guild] = default_alert
			if len(settings) > 5:
				settings[5] = f"alert: {default_alert}\n"
			else:
				settings.append(f"alert: {default_alert}\n")
			error_detected = True
		# if any settings had to be remade or there are extra lines in the settings file
		if error_detected or len(settings) > num_of_settings:
			# write the corrections to the settings file
			with open(settings_file, "w") as file:
				# cut the extra lines off of the settings file
				settings = settings[:num_of_settings+1]
				settings_str = ""
				for s in settings:
					settings_str += s
				file.write(settings_str)
	# if no settings file exists
	else:
		# create a new one with default values
		with open(settings_file, "a") as file:
			file.write(f"server: {guild.id}\n")
			file.write(f"enabled: {default_enabled}\n")
			file.write(f"min_timer: {default_min_timer}\n")
			file.write(f"max_timer: {default_max_timer}\n")
			file.write(f"alert: {default_alert}\n")
			enabled_in_guild[guild] = default_enabled
			timer_for_guild[guild] = [default_min_timer, default_max_timer]
	# declares a spot in the twaiter dictionary for this server
	twaiter_for_guild[guild] = None
	# declares a spot in the awaiter dictionary for this server
	awaiter_for_guild[guild] = None
	# creates a task for the bot to start running in for that server so multiple while loops can be running at once without the program freezing
	task_for_guild[guild] = client.loop.create_task(join_loop(guild))

# waits a random amount of time, joins a voice channel channel, plays a random sound, then leaves and repeats
# this function gets run separately for each server the bot is in
async def join_loop(guild):
	# directory that the sound files are kept in
	sound_directory = f"Sounds/server_{guild.id}"
	while enabled_in_guild[guild]:
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
			sound_path = f"{sound_directory}/{sound}"
			# prints the sound it's about to play
			print(f"Now playing in {guild.name}: {sound}")
			# get top channel bot is allowed to read and send messages in for the server
			text_channel = get_alert_channel(guild)
			# if the sound file exists
			if os.path.isfile(sound_path):
				voice_client = discord.utils.get(client.voice_clients, guild=guild)
				# if the bot is already connected to a voice channel in this server, then wait until it leaves
				if voice_client:
					while voice_client.is_connected():
						await asyncio.sleep(0.1)
				# if there is a channel the bot can read + send in, the last message wasn't an alert message, and there is an alert message
				last_message = text_channel.last_message
				alert = alert_for_guild[guild]
				if text_channel and not (last_message and last_message.author.id == client.user.id and last_message.content == alert) and len(alert) > 0:
					# send an alert message
					await text_channel.send(alert)
				# join the channel and play the sound
				await play_sound(channel, sound_path)

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
def get_alert_channel(guild):
	# for each text channel in the server
	for c in guild.text_channels:
		perms = c.permissions_for(guild.me)
		# if the bot has permission to read and send messages in this channel, use it
		if perms.read_messages and perms.send_messages:
			return c
	# if there are no available channels, return nothing
	return None

# plays a sound in a voice channel
async def play_sound(channel, sound_path):
	# connects to the voice channel
	voice = await channel.connect()
	# starts playing the audio
	voice.play(FFmpegPCMAudio(sound_path))
	# waits until the audio is done playing or until the bot is not in the channel anymore
	while voice.is_playing() and channel.guild.voice_client.channel == channel:
		await asyncio.sleep(0.1)
	# waits for a bit since there's a bit of lag to register that the bot is still playing audio
	await asyncio.sleep(0.5)
	# if the bot is still in a voice channel
	if channel.guild.voice_client:
		# disconnect
		await channel.guild.voice_client.disconnect()

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
			# if help command
			if command[1].lower() == "help":
				# if the bot has permission to send messages in this channel
				if perms.send_messages:
					# define info for every command to reply with
					example_prefix = f"`@{client.user.name}`"
					help_info = f"{example_prefix} help {{command name (optional)}}:"
					leave_info = f"{example_prefix} leave:"
					stfu_info = f"{example_prefix} stfu {{time (optional)}}:"
					on_info = f"{example_prefix} on {{time (optional)}}:"
					onq_info = f"{example_prefix} on?:"
					add_info = f"{example_prefix} add {{file attatchment(s)}}:"
					remove_info = f"{example_prefix} remove {{file name(s)}}:"
					rename_info = f"{example_prefix} rename {{file name}} {{new name}}:"
					list_info = f"{example_prefix} list:"
					give_info = f"{example_prefix} give {{file name(s)}}:"
					timer_info = f"{example_prefix} timer {{minimum frequency}} {{maximum frequency}}:"
					timerq_info = f"{example_prefix} timer?:"
					reset_info = f"{example_prefix} reset:"
					play_info = f"{example_prefix} play {{file name}}:"
					alertoff_info = f"{example_prefix} alertoff {{time (optional)}}:"
					alerton_info = f"{example_prefix} alerton {{time (optional)}}:"
					alertonq_info = f"{example_prefix} alerton?:"
					alert_info = f"{example_prefix} alert {{new alert message}}:"
					alertq_info = f"{example_prefix} alert?:"
					alertqf_info = f"{example_prefix} alert?f:"
					
					# returns a string that lists info about every command
					def get_help_message():
						help_message = "List of commands"
						help_message += f"\n\n{help_info}"
						help_message += f"\n\n{leave_info}"
						help_message += f"\n\n{stfu_info}"
						help_message += f"\n\n{on_info}"
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
						help_message += f"\n\n{alertoff_info}"
						help_message += f"\n\n{alerton_info}"
						help_message += f"\n\n{alertonq_info}"
						help_message += f"\n\n{alert_info}"
						help_message += f"\n\n{alertq_info}"
						help_message += f"\n\n{alertqf_info}"
						help_message += f"\n\nType \"{example_prefix} help {{command name}}\" for examples and more info about a command (Ex: \"{example_prefix} help timer\")"
						return help_message

					# if there is an argument to the help command
					if len(command) > 2:
						# reply with info about the command in the argument
						if command[2].lower() == "help":
							help_info += "\n> Gives descriptions of how to use all or one of this bot's commands"
							help_info += "\n> If this command is not given any arguments, it will list brief descriptions of all commands this bot has"
							help_info += "\n> If this command is given the name of a command as an argument, it will list some more info about the command along with some examples"
							help_info += "\n> (As you've likely already found out)"
							help_info += "\n> Examples:"
							help_info += f"\n> {example_prefix} help"
							help_info += f"\n> {example_prefix} help stfu"
							help_info += f"\n> {example_prefix} help timer"
							await message.reply(help_info)
						elif command[2].lower() == "leave":
							leave_info += "\n> Makes the bot leave the voice channel it's currently in"
							leave_info += "\n> Example:"
							leave_info += f"\n> {example_prefix} leave"
							await message.reply(leave_info)
						elif command[2].lower() == "stfu":
							stfu_info += "\n> Makes the bot shut up and stop joining channels (for a certain amount of time if given an argument)"
							stfu_info += "\n> If this command is given a time argument, the bot will be disabled for that much time, and then re-enable itself after the time has expired"
							stfu_info += "\n> The argument must either be a positive number of seconds, or be in colon format"
							stfu_info += "\n> Colon format: \"hrs:min:sec\" or \"min:sec\", Ex: \"1:30:15\" (1 hour, 30 minutes, and 15 seconds), \"45:0\" (45 minutes and 0 seconds)"
							stfu_info += "\n> If this command is not given any arguments, the bot will stay disabled until another command is used to re-enable it"
							stfu_info += "\n> To re-enable the bot, either use the \"on\" command, or use this command again with an argument for how long until it re-enables"
							stfu_info += "\n> Note: This command will reset the bot's waiting time to join a channel (like the reset command)"
							stfu_info += "\n> Examples:"
							stfu_info += f"\n> {example_prefix} stfu"
							stfu_info += f"\n> {example_prefix} stfu 60"
							stfu_info += f"\n> {example_prefix} stfu 1:30:0"
							stfu_info += f"\n> {example_prefix} stfu 30:0"
							stfu_info += f"\n> {example_prefix} stfu 0:90:0"
							stfu_info += f"\n> {example_prefix} stfu 0:120"
							await message.reply(stfu_info)
						elif command[2].lower() == "on":
							on_info += "\n> Enables the bot to randomly join channels (for a certain amount of time if given an argument)"
							on_info += "\n> If this command is given a time argument, the bot will stay enabled for that much time, and then disable itself after the time has expired"
							on_info += "\n> The argument must either be a positive number of seconds, or be in colon format"
							on_info += "\n> Colon format: \"hrs:min:sec\" or \"min:sec\", Ex: \"1:30:15\" (1 hour, 30 minutes, and 15 seconds), \"45:0\" (45 minutes and 0 seconds)"
							on_info += "\n> If this command is not given any arguments, the bot will stay enabled until another command is used to disable it"
							on_info += "\n> To disable the bot, either use the \"stfu\" command, or use this command again with an argument for how long until it should disable"
							on_info += "\n> Note: When the bot re-enables after being disabled, its waiting time to join a channel will have been reset (like the reset command)"
							on_info += "\n> Examples:"
							on_info += f"\n> {example_prefix} on"
							on_info += f"\n> {example_prefix} on 60"
							on_info += f"\n> {example_prefix} on 1:30:0"
							on_info += f"\n> {example_prefix} on 30:0"
							on_info += f"\n> {example_prefix} on 0:90:0"
							on_info += f"\n> {example_prefix} on 0:120"
							await message.reply(on_info)
						elif command[2].lower() == "on?":
							onq_info += "\n> Tells you if the bot is currently enabled or disabled in this server"
							onq_info += "\n> Example:"
							onq_info += f"\n> {example_prefix} on?"
							await message.reply(onq_info)
						elif command[2].lower() == "add":
							add_info += "\n> Adds sounds to this server's sound list if you attach mp3 or wav files"
							add_info += "\n> In order for this command to work:"
							add_info += "\n> The user must have a role with the name \"Random Sound Bot Adder\" in the server"
							add_info += "\n> The attached files must be in the same message as the command"
							add_info += "\n> The attached files must have names that are less than 128 characters long"
							add_info += "\n> Examples:"
							add_info += f"\n> {example_prefix} add {{attached file: example_file.mp3}}"
							add_info += f"\n> {example_prefix} add {{attached file: example_file_1.wav}} {{attached file: example_file_2.mp3}}"
							await message.reply(add_info)
						elif command[2].lower() == "remove":
							remove_info += "\n> Deletes any files listed from this server's sound list"
							remove_info += "\n> In order for this command to work, the user must have a role with the name \"Random Sound Bot Remover\" in the server"
							remove_info += "\n> Examples:"
							remove_info += f"\n> {example_prefix} remove example_file.mp3"
							remove_info += f"\n> {example_prefix} remove example_file_1.wav example_file_2.mp3"
							await message.reply(remove_info)
						elif command[2].lower() == "rename":
							rename_info += "\n> Renames a file in this server's sound list"
							rename_info += "\n> In order for this command to work:"
							rename_info += "\n> The user must have a role with the name \"Random Sound Bot Adder\" in the server"
							rename_info += "\n> The file extension of the new name must match the file extension of the old name"
							rename_info += "\n> The new file name cannot be the same as any existing files"
							rename_info += "\n> The new file name must not contain any slashes or backslashes"
							rename_info += "\n> The new file name must be less than 128 characters long"
							rename_info += "\n> Examples:"
							rename_info += f"\n> {example_prefix} rename old_file_name.mp3 new_file_name.mp3"
							rename_info += f"\n> {example_prefix} rename old_file_name.wav new_file_name.wav"
							await message.reply(rename_info)
						elif command[2].lower() == "list":
							list_info += "\n> Sends all of the sound files that this server has to use"
							list_info += "\n> If there enough characters in the list (>2000), this command will take several replies to complete"
							list_info += "\n> Example:"
							list_info += f"\n> {example_prefix} list"
							await message.reply(list_info)
						elif command[2].lower() == "give":
							give_info += "\n> Sends copies of sound files that are being used on this server"
							give_info += "\n> If you request more than 10 files, this command will take multiple replies to complete"
							give_info += "\n> Examples:"
							give_info += f"\n> {example_prefix} give example_file.mp3"
							give_info += f"\n> {example_prefix} give example_file_1.wav example_file_2.mp3"
							await message.reply(give_info)
						elif command[2].lower() == "timer":
							timer_info += "\n> Changes the frequency of when the bot joins channels"
							timer_info += "\n> Arguments must either be a positive number of seconds, or be in colon format"
							timer_info += "\n> Colon format: \"hrs:min:sec\" or \"min:sec\", Ex: \"1:30:15\" (1 hour, 30 minutes, and 15 seconds), \"45:0\" (45 minutes and 0 seconds)"
							timer_info += "\n> This command does not automatically reset the bot's current countdown to join"
							timer_info += "\n> In other words, this command will not take effect until either the next time the bot joins, or the \"reset\" command is used"
							timer_info += "\n> Examples:"
							timer_info += f"\n> {example_prefix} timer 60 120"
							timer_info += f"\n> {example_prefix} timer 0:30:0 1:0:0"
							timer_info += f"\n> {example_prefix} timer 15:0 60:0"
							timer_info += f"\n> {example_prefix} timer 0:0:30 3600"
							timer_info += f"\n> {example_prefix} timer 60:0 0:90:0"
							timer_info += f"\n> {example_prefix} timer 0 60:0"
							await message.reply(timer_info)
						elif command[2].lower() == "timer?":
							timerq_info += "\n> Tells you the time range for how often the bot will randomly join"
							timerq_info += "\n> Example:"
							timerq_info += f"\n> {example_prefix} timer?"
							await message.reply(timerq_info)
						elif command[2].lower() == "reset":
							reset_info += "\n> Resets the bot's waiting time to join"
							reset_info += "\n> Use this command after using the \"timer\" command if you want the new frequency you inputted to take effect before the next time the bot joins a channel"
							reset_info += "\n> Example:"
							reset_info += f"\n> {example_prefix} reset"
							await message.reply(reset_info)
						elif command[2].lower() == "play":
							play_info += "\n> Makes the bot join your voice channel and play a sound from this server's sound list that you input"
							play_info += "\n> If the user is in a voice channel when this command is used, the bot will join the user's voice channel"
							play_info += "\n> If the user is not in a voice channel when this command is used, the bot will pick a random channel with people in it to join"
							play_info += "\n> Examples:"
							play_info += f"\n> {example_prefix} play example_file.mp3"
							play_info += f"\n> {example_prefix} play example_file.wav"
							await message.reply(play_info)
						elif command[2].lower() == "alertoff":
							alertoff_info += "\n> Disables the bot's alert messages that it sends when it joins a channel randomly (for a certain amount of time if given an argument)"
							alertoff_info += "\n> If this command is given a time argument, alert messages will be disabled for that much time, and then be re-enabled after the time has expired"
							alertoff_info += "\n> The argument must either be a positive number of seconds, or be in colon format"
							alertoff_info += "\n> Colon format: \"hrs:min:sec\" or \"min:sec\", Ex: \"1:30:15\" (1 hour, 30 minutes, and 15 seconds), \"45:0\" (45 minutes and 0 seconds)"
							alertoff_info += "\n> If this command is not given any arguments, alert messages will stay disabled until another command is used to re-enable them"
							alertoff_info += "\n> To re-enable alert messages, either use the \"alerton\" command, or use this command again with an argument for how long until they re-enable"
							alertoff_info += "\n> Examples:"
							alertoff_info += f"\n> {example_prefix} alertoff"
							alertoff_info += f"\n> {example_prefix} alertoff 60"
							alertoff_info += f"\n> {example_prefix} alertoff 1:30:0"
							alertoff_info += f"\n> {example_prefix} alertoff 30:0"
							alertoff_info += f"\n> {example_prefix} alertoff 0:90:0"
							alertoff_info += f"\n> {example_prefix} alertoff 0:120"
							await message.reply(alertoff_info)
						elif command[2].lower() == "alerton":
							alerton_info += "\n> Enables the bot's alert messages that it sends when it joins a channel randomly (for a certain amount of time if given an argument)"
							alerton_info += "\n> If this command is given a time argument, alert messages will stay enabled for that much time, and then be disabled after the time has expired"
							alerton_info += "\n> The argument must either be a positive number of seconds, or be in colon format"
							alerton_info += "\n> Colon format: \"hrs:min:sec\" or \"min:sec\", Ex: \"1:30:15\" (1 hour, 30 minutes, and 15 seconds), \"45:0\" (45 minutes and 0 seconds)"
							alerton_info += "\n> If this command is not given any arguments, alert messages will stay enabled until another command is used to disable them"
							alerton_info += "\n> To disable alert messages, either use the \"alertoff\" command, or use this command again with an argument for how long until they disable"
							alerton_info += "\n> Examples:"
							alerton_info += f"\n> {example_prefix} alerton"
							alerton_info += f"\n> {example_prefix} alerton 60"
							alerton_info += f"\n> {example_prefix} alerton 1:30:0"
							alerton_info += f"\n> {example_prefix} alerton 30:0"
							alerton_info += f"\n> {example_prefix} alerton 0:90:0"
							alerton_info += f"\n> {example_prefix} alerton 0:120"
							await message.reply(alerton_info)
						elif command[2].lower() == "alerton?":
							alertonq_info += "\n> Tells you if the bot's alert messages are currently enabled or disabled in this server"
							alertonq_info += "\n> Example:"
							alertonq_info += f"\n> {example_prefix} alerton?"
							await message.reply(alertonq_info)
						elif command[2].lower() == "alert":
							alert_info += "\n> Changes the alert message that the bot sends when it joins a channel randomly in this server"
							alert_info += "\n> Note: This command will only take the first 2000 characters of the input due to the discord message size limit"
							alert_info += "\n> Examples:"
							alert_info += f"\n> {example_prefix} alert New Alert Message"
							alert_info += f"\n> {example_prefix} alert __Alert Message Underlined With Discord Formatting__"
							alert_info += f"\n> {example_prefix} alert **CHAOSCHAOSCHAOSCHAOSCHAOSCHAOSCHAOSCHAOSCHAOSCHAOS**"
							await message.reply(alert_info)
						elif command[2].lower() == "alert?":
							alertq_info += "\n> Tells you what the bot's current alert message is for this server that it uses when it joins a channel randomly"
							alertq_info += "\n> Example:"
							alertq_info += f"\n> {example_prefix} alert?"
							await message.reply(alertq_info)
						elif command[2].lower() == "alert?f":
							alertqf_info += "\n> Gives you the un-formatted, raw characters of the bot's current alert message for this server"
							alertqf_info += "\n> Note: This command may send out triple backticks (\"\\`\\`\\`\") in alert messages like this (\"\\\\\\`\\\\\\`\\\\\\`\")"
							alertqf_info += "\n> This is due to the fact that the discord developers forgot to make functioning escapes for the code block symbols"
							alertqf_info += "\n> Example:"
							alertqf_info += f"\n> {example_prefix} alert?f"
							await message.reply(alertqf_info)
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
					await voice_client.disconnect()
				else:
					await react_with_x(message)
			# if stfu (shut the fuck up) command
			elif command[1].lower() == "stfu":
				# if the bot is currently enabled
				if enabled_in_guild[message.guild]:
					# disable the bot in that server
					enabled_in_guild[message.guild] = False
					# changes the enabled setting in the server's settings file
					file_setting(message.guild, "enabled", False, 1)
					# stop join loop for server
					task_for_guild[message.guild].cancel()
					# if the bot is currently waiting for an sftu or on command to finish, cancel it
					if twaiter_for_guild[message.guild]:
						twaiter_for_guild[message.guild].cancel()
					# if the bot is connected to a channel in that server, then leave
					voice_client = discord.utils.get(client.voice_clients, guild = message.guild)
					if voice_client and voice_client.is_connected():
						voice_client.stop()
				# if the command has any arguments
				if len(command) > 2:
					time = process_time(command[2])
					# if the argument can be processed as a number of seconds
					if not time is None:
						# start a countdown until the enabled flag gets flipped for this server
						twaiter_for_guild[message.guild] = client.loop.create_task(wait_to_flip("t", message.guild, time))
						await react_with_check(message)
					else:
						await react_with_x(message)
				else:
					await react_with_check(message)
			# if on command
			elif command[1].lower() == "on":
				# if the bot is not currently enabled
				if not enabled_in_guild[message.guild]:
					# enable the bot in that server
					enabled_in_guild[message.guild] = True
					# changes the enabled setting in the server's settings file
					file_setting(message.guild, "enabled", True, 1)
					# recreate a task for that server
					task_for_guild[message.guild] = client.loop.create_task(join_loop(message.guild))
					# if the bot is currently waiting for an sftu or on command to finish, cancel it
					if twaiter_for_guild[message.guild]:
						twaiter_for_guild[message.guild].cancel()
				# if the command has any arguments
				if len(command) > 2:
					time = process_time(command[2])
					# if the argument can be processed as a number of seconds
					if not time is None:
						# start a countdown until the enabled flat gets flipped for this server
						twaiter_for_guild[message.guild] = client.loop.create_task(wait_to_flip("t", message.guild, time))
						await react_with_check(message)
					else:
						await react_with_x(message)
				else:
					await react_with_check(message)
			# if on? command
			elif command[1].lower() == "on?":
				# if the bot is enabled, react with checkmark
				if enabled_in_guild[message.guild]:
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
						is_sound_file = file.filename.endswith(".mp3") or file.filename.endswith(".wav")
						# if the file is an mp3 or wav file, the file doesn't contain a "/" or "\" in the name (for security redundancy), 
						# the file name is less than 128 characters long, and the file size is less than 10mb (discord limitation)
						if is_sound_file and not "/" in file.filename and not "\\" in file.filename and len(file.filename) < 128 and file.size < 10_000_000:
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
					no_slashes = not "/" in command[2] and not "\\" in command[2] and not "/" in command[3] and not "\\" in command[3]
					correct_file_extensions = (command[2].endswith(".mp3") and command[3].endswith(".mp3")) or (command[2].endswith(".wav") and command[3].endswith(".wav"))
					not_a_dupe = get_sounds(sound_dir).count(command[3]) < 1
					# if the file exists, the arguments don't contain "/" or "\" (for security redundancy), the new name has an mp3 or wav file extension that matches the old file name extension, 
					# the new file name is not already being used, and the new file name is less than 128 characters long
					if os.path.isfile(old_dir) and no_slashes and correct_file_extensions and not_a_dupe and len(command[3]) < 128:
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
					sounds = get_sounds(sound_dir)
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
					# try to get the numbers from each argument
					min = process_time(command[2])
					max = process_time(command[3])
					# double check to make sure min and max timers are valid
					if type(min) is float and type(max) is float:
						# makes sure the min is not larger than the max
						if min <= max:
							max += 1 # adds 1 since the randrange function uses a delimiter rather than an upper bound
							# set the min and max timer values for the server
							timer_for_guild[message.guild][0] = min
							timer_for_guild[message.guild][1] = max
							# change the min and max timer values for the server in the server's settings file
							file_setting(message.guild, "min_timer", min, 2)
							file_setting(message.guild, "max_timer", max, 3)
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
				# if the bot is enabled in the server, there are arguments, and the bot isn't already in a voice channel
				if enabled_in_guild[message.guild] and len(command) > 2 and voice_client is None:
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
						sound_path = f"{sound_dir}/{command[2]}"
						# if the argument doesn't contain "/" or "\" (for security redundancy) and the file in the argument exists
						if not "/" in command[2] and not "\\" in command[2] and os.path.isfile(sound_path):
							# join the voice channel and play the sound
							await play_sound(channel, sound_path)
						else:
							await react_with_x(message)
					else:
						await react_with_x(message)
				else:
					await react_with_x(message)
			# if alertoff command
			elif command[1].lower() == "alertoff":
				# if the bot's alert messages are currently enabled
				if alerton_for_guild[message.guild]:
					# disabled them
					alerton_for_guild[message.guild] = False
					file_setting(message.guild, "alert_on", False, 4)
					# if the bot is currently waiting for an alerton or alertoff command to finish, cancel it
					if awaiter_for_guild[message.guild]:
						awaiter_for_guild[message.guild].cancel()
				# if the command has an argument
				if len(command) > 2:
					time = process_time(command[2])
					# if the argument can be processed as a number of seconds
					if not time is None:
						# start a countdown until the alerton flag is flipped for this server
						awaiter_for_guild[message.guild] = client.loop.create_task(wait_to_flip("a", message.guild, time))
						await react_with_check(message)
					else:
						await react_with_x(message)
				else:
					await react_with_check(message)
			# if alerton command
			elif command[1].lower() == "alerton":
				# if the bot's alert messages are currently enabled
				if not alerton_for_guild[message.guild]:
					# disabled them
					alerton_for_guild[message.guild] = True
					file_setting(message.guild, "alert_on", True, 4)
					# if the bot is currently waiting for an alerton or alertoff command to finish, cancel it
					if awaiter_for_guild[message.guild]:
						awaiter_for_guild[message.guild].cancel()
				# if the command has an argument
				if len(command) > 2:
					time = process_time(command[2])
					# if the argument can be processed as a number of seconds
					if not time is None:
						# start a countdown until the alerton flag is flipped for this server
						awaiter_for_guild[message.guild] = client.loop.create_task(wait_to_flip("a", message.guild, time))
						await react_with_check(message)
					else:
						await react_with_x(message)
				else:
					await react_with_check(message)
			# if alerton? command
			elif command[1].lower() == "alerton?":
				# if alerts are enabled for this server, react with a check
				if alerton_for_guild[message.guild]:
					await react_with_check(message)
				# if alerts are disabeld for this server, react with an x
				else:
					await react_with_x(message)
			# if alert command
			elif command[1].lower() == "alert":
				# if the command has an argument
				if len(command) > 2:
					# turns the first 2000 characters after the alert command into the server's alert message
					alert_for_guild[message.guild] = message.content[message.content.index("alert")+5:].strip()[:2000]
					file_setting(message.guild, "alert", alert_for_guild[message.guild], 5)
					await react_with_check(message)
				# if the command has no arguments
				else:
					await react_with_x(message)
			# if alert? command
			elif command[1].lower() == "alert?":
				# if the bot has permission to send messages in this channel
				if perms.send_messages:
					# reply with the server's alert message
					await message.reply(alert_for_guild[message.guild])
			# if alert?f command
			elif command[1].lower() == "alert?f":
				# if the bot has permission to send messages in this channel
				if perms.send_messages:
					# reply with the unformatted, raw characters of the server's alert message
					deformatted_alert = alert_for_guild[message.guild].replace("```", "\\`\\`\\`")
					await message.reply(f"```\n{deformatted_alert}\n```")

# changes the value of a setting in a server's settings folder
def file_setting(guild, name, value, index):
	settings_file = f"Settings/server_{guild.id}/Settings.set"
	settings = []
	with open(settings_file, "r") as file:
		settings = file.readlines()
	if len(settings) > index:
		settings[index] = f"{name}: {value}\n"
	else:
		settings.append(f"{name}: {value}\n")
	settings_str = ""
	for s in settings:
		settings_str += s
	with open(settings_file, "w") as file:
		file.write(settings_str)

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

# takes a string either of a positive number of a time in colon format and returns a float number of seconds
def process_time(arg):
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

# starts a timer until the enabled flat for a server gets flipped
async def wait_to_flip(dict, guild, time):
	await asyncio.sleep(time)
	if dict == "t":
		enabled_in_guild[guild] = not enabled_in_guild[guild]
		file_setting(guild, "enabled", enabled_in_guild[guild], 1)
	elif dict == "a":
		alerton_for_guild[guild] = not alerton_for_guild[guild]
		file_setting(guild, "alert_on", alerton_for_guild[guild], 4)

# sets up the bot every time it joins a new server while running
@client.event
async def on_guild_join(guild):
	await start_in_server(guild)

# runs the bot
client.run(token)