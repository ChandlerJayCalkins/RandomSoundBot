# Discord bot that joins a random channel with people in it at random times, plays a random sound, then leaves
# Current commands:
#	leave:		makes the bot stop playing and leave the channel
#	stfu:		makes the bot stop playing and leave the channel, and disables the bot from playing until enabled again
#	activate:	re-enables the bot to start waiting to join channels again

# TODO:
# 1. overall optimization (if possible)
# 2. make it so people can deactivate and activate the bot for a certain amount of time with arguments in the stfu command
# 3. make it so people can input multiple commands in the same message

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
	# sets the default frequency of the bot joining channels to 1 - 2 min
	timer_for_guild[guild] = [60, 121]
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
	# waits random amount of time as specified by what the server set it to (0 to 1 min by default)
	await asyncio.sleep(random.randrange(0, timer_for_guild[guild][1] - timer_for_guild[guild][0]))
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
		# waits random amount of time as specified by what the server sets it to (1 - 2 min default)
		await asyncio.sleep(random.randrange(timer_for_guild[guild][0], timer_for_guild[guild][1]))

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
					example_prefix = f"\n`@{client.user.name}`"
					help_message = "List of commands:"
					help_message += f"{example_prefix} help:\n\tGives descriptions of how to use all of this bot's commands"
					help_message += f"{example_prefix} leave:\n\tMakes the bot leave the voice channel it's currently in"
					help_message += f"{example_prefix} stfu:\n\tMakes the bot shut up until you re-enable it with the activate command"
					help_message += f"{example_prefix} activate:\n\tAllows the bot to join channels randomly again after being disabled by the stfu command"
					help_message += f"{example_prefix} on?:\n\tBot will tell you if it is currently enabled or disabled"
					help_message += f"{example_prefix} add {{file attatchment(s)}}:\n\tIf you attatch an mp3 or wav file with this command, the bot will add it to this server's list of sounds it can play (Requires a role called \"Random Sound Bot Adder\")"
					help_message += f"{example_prefix} remove {{file name(s)}}:\n\tRemoves any files listed from this server's sound list (Requires a role called \"Random Sound Bot Remover\")"
					help_message += f"{example_prefix} list:\n\tSends all of the sound files that this server is using"
					help_message += f"{example_prefix} give {{file name(s)}}:\n\tSends sound files from the server"
					help_message += f"{example_prefix} timer {{minimum frequency}} {{maximum frequency}}: \n\tChanges the frequency of when the bot joins channels (arguments must be either a positive integer (seconds) or in colon format (hrs:min:sec or min:sec))"
					await message.reply(help_message)
			# if leave command
			elif command[1].lower() == "leave":
				voice_client = discord.utils.get(client.voice_clients, guild = message.guild)
				# if the bot is connected to a channel in that server, then leave
				if voice_client and voice_client.is_connected():
					voice_client.stop()
			# if stfu (shut the fuck up) command
			elif command[1].lower() == "stfu":
				perms = message.channel.permissions_for(message.guild.me)
				# if the bot is currently active
				if active_in_guild[message.guild]:
					# disable the bot in that server
					active_in_guild[message.guild] = False
					# if the bot is connected to a channel in that server, then leave
					voice_client = discord.utils.get(client.voice_clients, guild = message.guild)
					if voice_client and voice_client.is_connected():
						voice_client.stop()
					# reacts to message with a checkmark emoji when done
					if perms.add_reactions:
						await message.add_reaction("\u2705")
				# if bot is already disabled
				else:
					# react to message with a X emoji
					if perms.add_reactions:
						await message.add_reaction("\u274c")
			# if activate command
			elif command[1].lower() == "activate":
				perms = message.channel.permissions_for(message.guild.me)
				# if the bot is not currently active
				if not active_in_guild[message.guild]:
					# enable the bot in that server
					active_in_guild[message.guild] = True
					# recreate a task for that server
					client.loop.create_task(join_loop(message.guild))
					# reacts to message with a checkmark emoji when done
					if perms.add_reactions:
						await message.add_reaction("\u2705")
				# if bot is already enabled
				else:
					# react to message with a X emoji
					if perms.add_reactions:
						await message.add_reaction("\u274c")
			# if on? command
			elif command[1].lower() == "on?":
				perms = message.channel.permissions_for(message.guild.me)
				# if the bot has permission to add reactions
				if perms.add_reactions:
					# if the bot is enabled, react with checkmark
					if active_in_guild[message.guild]:
						await message.add_reaction("\u2705")
					# if the bot is off, react with X
					else:
						await message.add_reaction("\u274c")
			# if add command
			elif command[1].lower() == "add":
				perms = message.channel.permissions_for(message.guild.me)
				# if the message author has the role that allows them to use this command and the message has attatched files
				if any(role.name == "Random Sound Bot Adder" for role in message.author.roles) and message.attachments:
					errors = []
					# check each file in the message
					for file in message.attachments:
						# if the file is an mp3 or wav file and doesn't contain a "../" in the name (for security redundancy)
						if (file.filename.endswith(".mp3") or file.filename.endswith(".wav")) and not "../" in file.filename:
							# save the file to the directory of the server the message was from
							await file.save(f"Sounds/server_{message.guild.id}/{file.filename}")
						# if the file couldn't be saved, add it to the error list
						else:
							errors.append(file.filename)
					# reacts to message with a checkmark emoji when done
					if perms.add_reactions and len(message.attatchments) > len(errors):
						await message.add_reaction("\u2705")
					# if none of the files could be saved, react with an X emoji
					elif perms.add_reactions:
						await message.add_reaction("\u274c")
					# if there were any files that couldn't be processed, reply with them
					if errors:
						await message.reply(get_file_error_message(errors))
				else:
					# react to message with a X emoji
					if perms.add_reactions:
						await message.add_reaction("\u274c")
			# if remove command
			elif command[1].lower() == "remove":
				perms = message.channel.permissions_for(message.guild.me)
				# if the message author has the role that allows them to use this command and the message command has arguments
				if any(role.name == "Random Sound Bot Remover" for role in message.author.roles) and len(command) > 2:
					dir = f"Sounds/server_{message.guild.id}"
					errors = []
					# go and remove each file in the arguments
					for file in command[2:]:
						filepath = f"{dir}/{file}"
						# if the argument doesn't contain "../" (for security redundancy) and the file exists
						if not "../" in file and os.path.isfile(filepath):
							# delete the file
							os.remove(filepath)
						else:
							errors.append(file)
					# reacts to message with a checkmark emoji when done
					if perms.add_reactions and len(command[2:]) > len(errors):
						await message.add_reaction("\u2705")
					# if no files were deleted, then react with X emoji
					elif perms.add_reactions:
						await message.add_reaction("\u274c")
					# if there were any files that couldn't be processed, reply with them
					if errors:
						await message.reply(get_file_error_message(errors))
				else:
					# react to message with a X emoji
					if perms.add_reactions:
						await message.add_reaction("\u274c")
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
			# if give command
			elif command[1].lower() == "give":
				# if the command has arguments
				if len(command) > 2:
					dir = f"Sounds/server_{message.guild.id}"
					files = []
					errors = []
					# loop through each argument
					for filename in command[2:]:
						filepath = f"{dir}/{filename}"
						# if the argument doesn't contain "../" (for security redundancy), if the file exists, and if the file is less than 10mb (discord limitation)
						if not "../" in filename and os.path.isfile(filepath) and os.path.getsize(filepath) < 10_000_000:
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
			# if timer command
			elif command[1].lower() == "timer":
				perms = message.channel.permissions_for(message.guild.me)
				# if there are enough arguments
				if len(command) > 3:
					min = 0
					max = 0
					# if the first argument is a number, get it
					try:
						min = float(command[2])
					# otherwise, see if it's in colon format
					except:
						if ":" in command[2]:
							min = command[2].split(":", 2)
							# if the argument is not in colon format, stop
							for n in range(0, len(min)):
								try:
									min[n] = int(min[n])
								except:
									# react to message with a X emoji
									if perms.add_reactions:
										await message.add_reaction("\u274c")
									return
							# if the argument has 2 values
							if len(min) == 2:
								# get mins + seconds
								min[0] *= 60
								min = min[0] + min[1]
							# if the agrument has 3 values
							elif len(min) == 3:
								# get hours + mins + seconds
								min[0] *= 3600
								min[1] *= 60
								min = min[0] + min[1] + min[2]
							else:
								# react to message with a X emoji
								if perms.add_reactions:
									await message.add_reaction("\u274c")
								return
						# if there are no colons in first argument, stop
						else:
							# react to message with a X emoji
							if perms.add_reactions:
								await message.add_reaction("\u274c")
							return
					# if the second argument is a number, get it
					try:
						max = float(command[3])
					# otherwise, see if it's in colon format
					except:
						if ":" in command[3]:
							max = command[3].split(":", 2)
							# if the argument is not in colon format, stop
							for n in range(0, len(max)):
								try:
									max[n] = int(max[n])
								except:
									# react to message with a X emoji
									if perms.add_reactions:
										await message.add_reaction("\u274c")
									return
							# if argument has 2 values
							if len(max) == 2:
								# get mins + seconds
								max[0] *= 60
								max = max[0] + max[1]
							# if argument has 3 values
							elif len(max) == 3:
								# get hours + mins + seconds
								max[0] *= 3600
								max[1] *= 60
								max = max[0] + max[1] + max[2]
							else:
								# react to message with a X emoji
								if perms.add_reactions:
									await message.add_reaction("\u274c")
								return
						# if there are not colons in second argument, stop
						else:
							# react to message with a X emoji
							if perms.add_reactions:
								await message.add_reaction("\u274c")
							return
					# double check to make sure min and max timers are valid
					if (type(min) is float or type(min) is int) and (type(max) is float or type(max is int)):
						# makes sure the min is not larger than the max
						if min <= max:
							timer_for_guild[message.guild][0] = min
							timer_for_guild[message.guild][1] = max + 1 # adds 1 since the randrange function uses a delimiter rather than an upper bound
							# reacts to message with a checkmark emoji when done
							if perms.add_reactions:
								await message.add_reaction("\u2705")
						else:
							# react to message with a X emoji
							if perms.add_reactions:
								await message.add_reaction("\u274c")
					else:
						# react to message with a X emoji
						if perms.add_reactions:
							await message.add_reaction("\u274c")
				else:
					# react to message with a X emoji
					if perms.add_reactions:
						await message.add_reaction("\u274c")

# returns an errors message containing files in a list
def get_file_error_message(errors):
	error_message = "```Could not process following files:"
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