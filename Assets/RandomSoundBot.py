# Discord bot that joins a random channel with people in it at random times, plays a random sound, then leaves
# Current commands:
#	leave:		makes the bot stop playing and leave the channel
#	stfu:		makes the bot stop playing and leave the channel, and disables the bot from playing until enabled again
#	activate:	re-enables the bot to start waiting to join channels again

# TODO:
# 1. overall optimization (if possible)
# 2. make it so people can deactivate and activate the bot for a certain amount of time with arguments in the stfu command
# 3. make it so people can change how often the bot joins and leaves channels with a command
# 4. make it so people can input multiple commands in the same message
# 5. make it so the bot has separate sound file directories for each server it's in
# 6. make a command where people with a certain role can add and remove sound files from the directory for their server

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
	# creates a task for the bot to start running in for that server
	client.loop.create_task(join_loop(guild))

# waits a random amount of time, joins a voice channel channel, plays a random sound, then leaves and repeats
# this function gets run separately for each server the bot is in
async def join_loop(guild):
	# directory that the sound files are kept in
	sound_directory = f"Sounds/server_{guild.id}"
	if not os.path.isdir(sound_directory):
		os.mkdir(sound_directory)
	# message that the bot sends right before it starts playing sounds
	warning_message = "XBOX LIVE"
	# waits random amount between 0 seconds to 30 min
	await asyncio.sleep(random.randrange(0, 1801))
	while active_in_guild[guild]:
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
				await guild.voice_client.disconnect()
			# otherwise, print error message
			else:
				print(f"No sound file found in {guild.name} {{id={guild.id}}})")
		# waits random amount between 30 - 60 min
		await asyncio.sleep(random.randrange(1800, 3601))

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
	# if the message has the command prefix
	if message.content.startswith(prefix):
		command = message.content.split()
		# if the command has any arguments
		if len(command) > 1:
			global active
			# if help command
			if command[1].lower() == "help":
				perms = message.channel.permissions_for(message.guild.me)
				# if the bot has permission to send messages in this channel
				if (perms.send_messages):
					# send descriptions of how to use all of the commands
					help_message = "List of commands:"
					help_message += f"\n`@{client.user.name}` help:\n\tGives descriptions of how to use all of this bot's commands"
					help_message += f"\n`@{client.user.name}` leave:\n\tMakes the bot leave the voice channel it's currently in"
					help_message += f"\n`@{client.user.name}` stfu:\n\tMakes the bot shut up until you re-enable it with the activate command"
					help_message += f"\n`@{client.user.name}` activate:\n\tAllows the bot to join channels randomly again after being disabled by the stfu command"
					help_message += f"\n`@{client.user.name}` add {{file attatchment(s)}}:\n\tIf you attatch an mp3 or wav file with this command, the bot will add it to this server's list of sounds it can play (Requires a role called \"Random Sound Bot Adder\""
					help_message += f"\n`@{client.user.name}` remove {{file name(s)}}:\n\tRemoves any files listed from this server's sound list (Requires a role called \"Random Sound Bot Remover\""
					help_message += f"\n`@{client.user.name}` list:\n\tSends all of the sound files that this server is using"
					await message.reply(help_message)
			# if leave command
			elif command[1].lower() == "leave":
				voice_client = discord.utils.get(client.voice_clients, guild = message.guild)
				# if the bot is connected to a channel in that server, then leave
				if voice_client and voice_client.is_connected():
					voice_client.stop()
			# if stfu (shut the fuck up) command
			elif command[1].lower() == "stfu":
				# disable the bot in that server
				active_in_guild[message.guild] = False
				print(f"active in guild {message.guild}: {active_in_guild[message.guild]}")
				# if the bot is connected to a channel in that server, then leave
				voice_client = discord.utils.get(client.voice_clients, guild = message.guild)
				if voice_client and voice_client.is_connected():
					voice_client.stop()
			# if activate command
			elif command[1].lower() == "activate":
				# if the bot is not currently active
				if not active_in_guild[message.guild]:
					# enable the bot in that server
					active_in_guild[message.guild] = True
					print(f"active in guild {message.guild}: {active_in_guild[message.guild]}")
					# recreate a task for that server
					client.loop.create_task(join_loop(message.guild))
			# if add command
			elif command[1].lower() == "add":
				# if the message author has the role that allows them to use this command and the message has attatched files
				if any(role.name == "Random Sound Bot Adder" for role in message.author.roles) and message.attachments:
					# check each file in the message
					for file in message.attachments:
						# if the file is an mp3 or wav file and doesn't contain a "../" in the name (for security redundancy)
						if (file.filename.endswith(".mp3") or file.filename.endswith(".wav")) and not "../" in file.filename:
							# save the file to the directory of the server the message was from
							await file.save(f"Sounds/server_{message.guild.id}/{file.filename}")
			# if remove command
			elif command[1].lower() == "remove":
				# if the message author has the role that allows them to use this command and the message command has arguments
				if any(role.name == "Random Sound Bot Remover" for role in message.author.roles) and len(command) > 2:
					dir = f"Sounds/server_{message.guild.id}"
					# go and remove each file in the arguments
					for file in command[2:]:
						filepath = f"{dir}/{file}"
						# if the argument doesn't contain "../" (for security redundancy) and the file exists
						if not "../" in file and os.path.isfile(filepath):
							# delete the file
							os.remove(filepath)
			# if list command
			elif command[1].lower() == "list":
				perms = message.channel.permissions_for(message.guild.me)
				# if the bot has permission to send messages in this channel
				if (perms.send_messages):
					# get a list of all sound files in the server's sound folder
					sounds = get_sounds(f"Sounds/server_{message.guild.id}")
					sound_message = f"```List of sounds for {message.guild.name}:"
					for s in sounds:
						sound_message += f"\n{s}"
					sound_message += "```"
					# send the list of sound files for the server
					await message.reply(sound_message)

# sets up the bot every time it joins a new server while running
@client.event
async def on_guild_join(guild):
	start_in_server(guild)

# runs the bot
client.run(token)