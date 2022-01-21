# Discord bot that joins a random channel with people in it at random times, plays a random sound, then leaves
# Current commands:
#	leave:		makes the bot stop playing and leave the channel
#	stfu:		makes the bot stop playing and leave the channel, and disables the bot from playing until enabled again
#	activate:	re-enables the bot to start waiting to join channels again

# TODO:
# 1. overall optimization (if possible)
# 2. make it so people can deactivate and activate the bot for a certain amount of time with arguments in the command
# 3. make it so people can change how often the bot joins and leaves channels with commands
# 4. make it so people can input multiple commands in the same message

import discord
from discord import FFmpegPCMAudio
import asyncio
import random
from os import walk

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
# this is defined at the end of the file after client.run(token), change it there
prefix = ""

# keeps track of which servers the bot is enabled in and which ones it's not
active_in_guild = {}

# called as soon as the bot is fully online and operational
@client.event
async def on_ready():
	print("Bot is ready")
	
	# initializes the active variables for each server
	for guild in client.guilds:
		active_in_guild[guild] = True

	# starts running the bot for each server it's in simultaneously
	for guild in client.guilds:
		client.loop.create_task(join_loop(guild))

# waits a random amount of time, joins a voice channel channel, plays a random sound, then leaves and repeats
async def join_loop(guild):
	# directory that the sound files are kept in
	sound_directory = "Sounds"
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
			# prints the sound it's about to play
			print(f"Now playing in {guild.name}: {sound}")
			# get top channel bot is allowed to read and send messages in for the server
			text_channel = get_warning_channel(guild)
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
			# wait about 1 seconds since there's a bit of lag with ffmpeg
			await asyncio.sleep(1)
			# then disconnect the bot
			await guild.voice_client.disconnect()
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
	for (path, dir, files) in walk(directory):
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
			# if leave command
			if command[1].lower() == "leave":
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

# runs the bot
client.run(token)

# string that goes at the start of commands to help the bot detect the command
# it is currently "@{botname}"
prefix = f"<@!{client.user.id}> "