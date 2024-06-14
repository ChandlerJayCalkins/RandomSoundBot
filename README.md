RandomSoundBot

Discord bot that joins a random channel with people in it at random times, plays a random sound, then leaves

Things you can do with the bot:
	- Tell it to leave the voice channel it's in
	- Disable / enable it temporarily in your server
	- Add, remove, and rename custom sound files that the bot can play in your server (Requires roles called "Random Sound Bot Adder" and "Random Sound Bot Remover")
	- Change how often the bot randomly joins to play sounds
	- Ask the bot to join and play a certain sound
	- Change what alert message the bot sends when it joins a channel randomly to play a sound
	- Disable / enable alert messages temporarily in your server
	- Change what channel the bot sends alert messages in for your server

Permissions Required:
	- Read Messages/View Channels
	- Send Messages
	- Attach Files
	- Read Message History
	- Add Reactions
	- Connect
	- Speak

Bot Setup Instructions for Servers:
	1. Give the bot required permissions (as listed above)
	2. Create a new role in your server called "Random Sound Bot Adder" to allow people to add and rename sound files for your server
	3. Create a new role in your server called "Random Sound Bot Remover" to allow people to remove sound files from your server
	4. If desired, change the random join timer, alert message, and alert channel with commands (use "help" command for more info)

Bot Setup for Running it on your own:
	Dependencies:
		- FFMPEG
			1. Go to [https://ffmpeg.org/](https://ffmpeg.org/) and download your desired version of FFMPEG for your OS.
			2. Extract the folder from the downloaded zip file and move it to where you want it to stay on your computer.
			3. Add the bin folder in the the FFMPEG folder to PATH.
		- Discord.py
			1. Use the command `pip install -U discord.py[voice]`.
		- FFMPEG Python Library
			1. Use the command `pip install -U ffmpeg`.
	Running the bot on your own:
		1. Clone the repo to your own machine
		2. Go into the "Assets" folder
		3. Create a file called "BotToken.txt" and paste your bot's token in there
		4. Create a file called "DefaultAlert.txt" and type in what you would like the bot's default alert message to be