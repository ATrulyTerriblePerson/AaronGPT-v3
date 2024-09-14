# Import Statements
import os
import random
import time
import asyncio
import json
import math
import wave
from pathlib import Path
import youtube_dl
import asyncio
import re

import discord
from discord.ext import commands, tasks
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands
from discord.ui import Button, View

from gpt4all import GPT4All
import fitz  # PyMuPDF
from dotenv import load_dotenv
import yt_dlp as youtube_dl
import pafy
import pyaudio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from fuzzywuzzy import process

#These import statements were made by an idiot (me)


TOKEN = # DO NOT SHARE WITH ANYONE ELSE





# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

#Definitions
# Load trivia questions
def load_questions(category):
    try:
        with open(r'C:\Users\docto\Documents{category}.json', 'r') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        print(f"Error loading JSON file for category {category}: {e}")
        return []

# Ensure trivia files exist
def ensure_trivia_files_exist():
    base_path = Path(r"C:\Users\docto\Documents")
    categories = ["StarCraft.json", "history.json"]

    for category in categories:
        file_path = base_path / category
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as file:
                json.dump([], file)  # Initialize with an empty list
            print(f"Created {file_path}")
        else:
            print(f"{file_path} already exists")

# Call the function to ensure files exist
ensure_trivia_files_exist()

# Save trivia questions
def save_question(category, question):
    file_path = f'C:/Users/docto/PycharmProjects/pythonProject1/.venv/trivia/{category}.json'

    # Check if the file exists
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            questions = json.load(file)
    else:
        questions = []

    questions.append(question)

    with open(file_path, 'w') as file:
        json.dump(questions, file, indent=4)

# Global variables to track scores and streaks
scores = {}
streaks = {}






# STARCRAFT STUFF
with open('terran_units.json', 'r') as f:
    terran_units = json.load(f)
with open('zerg_units.json', 'r') as f:
    zerg_units = json.load(f)
with open('protoss_units.json', 'r') as f:
    protoss_units = json.load(f)

# Combine all units into one dictionary
units = {**terran_units, **zerg_units, **protoss_units}

# Define colors for each race
colors = {
    "Terran": discord.Color.red(),
    "Zerg": discord.Color.purple(),
    "Protoss": discord.Color.gold()
}

# Function to get unit race
def get_unit_race(unit_name):
    if unit_name in terran_units:
        return "Terran"
    elif unit_name in zerg_units:
        return "Zerg"
    elif unit_name in protoss_units:
        return "Protoss"
    return None


# QUOTE stuff
# Path to the quotes JSON file
quotes_file_path = 'quotes.json'

# Ensure the quotes JSON file exists
if not os.path.exists(quotes_file_path):
    with open(quotes_file_path, 'w') as f:
        json.dump([], f)

# Function to read quotes from the JSON file
def read_quotes():
    with open(quotes_file_path, 'r') as f:
        return json.load(f)

# Function to add a new quote to the JSON file
def add_quote(new_quote):
    quotes = read_quotes()
    quotes.append(new_quote)
    with open(quotes_file_path, 'w') as f:
        json.dump(quotes, f)

# Function to search quotes by keyword
def search_quotes(keyword):
    quotes = read_quotes()
    return [quote for quote in quotes if keyword.lower() in quote.lower()]









# Commands !
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')



# List of commands
# This uses the help part of each command to list the how commands work for !help
@bot.command(name='commands', help='Lists all available commands')
async def list_commands(ctx):
    commands_list = [command.name for command in bot.commands]
    await ctx.send(f"Available commands: {', '.join(commands_list)}")

# Say hello (:
@bot.command(name='hello', help='Says hello')
async def hello(ctx):
    await ctx.send('Hello!')

# Example: !add 2 3
@bot.command(name='add', help='Adds two numbers')
async def add(ctx, a: int, b: int):
    await ctx.send(a + b)

# Trivia command - Not very modular.
@bot.command(name='trivia', help='Starts a trivia game')
async def trivia(ctx, category: str = None):
    if category is None:
        # Prompt the user to select a category
        categories = ['StarCraft', 'history']
        buttons = [discord.ui.Button(label=cat, style=discord.ButtonStyle.primary, custom_id=cat) for cat in categories]

        async def category_callback(interaction):
            selected_category = interaction.data['custom_id']
            await interaction.response.defer()
            await ask_question(ctx, selected_category)

        view = discord.ui.View(timeout=None)
        for button in buttons:
            button.callback = category_callback
            view.add_item(button)

        await ctx.send("Which category?", view=view)
        return

async def ask_question(ctx, category):
    questions = load_questions(category)
    if not questions:
        await ctx.send(f"No questions available for the {category} category.")
        return
    question = random.choice(questions)
    options = question['options']
    random.shuffle(options)

    buttons = [discord.ui.Button(label=opt, style=discord.ButtonStyle.primary, custom_id=opt) for opt in options]
    correct_users = []

    # Load or initialize the storage file
    storage_path = 'C:/Users/docto/PycharmProjects/pythonProject1/.venv/trivia/coins.json'
    if os.path.exists(storage_path):
        with open(storage_path, 'r') as f:
            storage = json.load(f)
    else:
        storage = {}

    async def button_callback(interaction):
        await interaction.response.defer()  # Acknowledge the interaction
        if interaction.user != ctx.author:
            await interaction.followup.send("This is not your question!", ephemeral=True)
            return

        selected_option = interaction.data['custom_id']
        user_id = str(ctx.author.id)
        if selected_option == question['answer']:
            if user_id not in storage:
                storage[user_id] = {
                    'username': str(ctx.author),
                    'coins': 0,
                    'streak': 0
                }
            storage[user_id]['streak'] += 1
            multiplier = 1 + (storage[user_id]['streak'] * 0.1)
            coins_earned = int(20 * multiplier)
            storage[user_id]['coins'] += coins_earned
            correct_users.append(ctx.author)

            # Debugging print statements
            print(f"User ID: {user_id}")
            print(f"Username: {storage[user_id]['username']}")
            print(f"Streak: {storage[user_id]['streak']}")
            print(f"Multiplier: {multiplier}")
            print(f"Coins Earned: {coins_earned}")
            print(f"Total Coins: {storage[user_id]['coins']}")
        else:
            storage[user_id]['streak'] = 0
            await interaction.followup.send(f"You answered: {selected_option}", ephemeral=True)

        # Update the button label to show the user's choice
        for button in view.children:
            if button.custom_id == selected_option:
                button.label = f"You chose: {selected_option}"
                button.disabled = True
            else:
                button.disabled = True

        await interaction.message.edit(view=view)

        # Save the storage file
        with open(storage_path, 'w') as f:
            json.dump(storage, f)

    for button in buttons:
        button.callback = button_callback

    view = discord.ui.View(timeout=None)  # Make the view persistent
    for button in buttons:
        view.add_item(button)

    async def send_question():
        await ctx.send(f"**{question['question']}**", view=view)
        await asyncio.sleep(30)
        # After 30 seconds, send a message mentioning those who got it right
        if correct_users:
            mentions = ', '.join(user.mention for user in correct_users)
            streak_messages = []
            for user in correct_users:
                streak = storage[str(user.id)]['streak']
                if streak > 5:
                    streak_messages.append(f"{user.mention} has a streak of {streak}! They're on a roll!")
            streak_message = ' '.join(streak_messages)
            await ctx.send(f"Time's up! Congratulations to {mentions} for getting it right! {streak_message}")
        else:
            await ctx.send("Time's up! No one got it right this time.")

        # Add the "New Question" button
        another_question_button = discord.ui.Button(label="Ask another question", style=discord.ButtonStyle.secondary)
        another_question_button.callback = ask_another_question
        new_view = discord.ui.View(timeout=None)
        new_view.add_item(another_question_button)
        await ctx.send("Click the button below to ask another question:", view=new_view)

    async def ask_another_question(interaction):
        await interaction.response.defer()
        await ask_question(ctx, category)

    await send_question()

# StarCraft Unit Command - this is connected to a json file
@bot.command(name='unit', aliases=['Unit'], help='Displays information about a specified unit')
async def unit(ctx, *, unit_name: str = None):
    if unit_name is None:
        unit_name = random.choice(list(units.keys()))
    else:
        unit_name = unit_name.capitalize()

    if unit_name in units:
        unit = units[unit_name]
        race = get_unit_race(unit_name)
        color = colors[race]

        embed = discord.Embed(title=f"{unit_name} Information", color=color)
        embed.add_field(name="Health", value=unit["health"], inline=False)
        embed.add_field(name="Mineral Cost", value=unit["mineral_cost"], inline=False)
        embed.add_field(name="Vespene Cost", value=unit["vespene_cost"], inline=False)
        embed.add_field(name="Building Time", value=unit["building_time"], inline=False)
        embed.add_field(name="Armour", value=unit["armour"], inline=False)
        embed.add_field(name="Shield", value=unit["shield"], inline=False)
        embed.add_field(name="Damage", value=unit["damage"], inline=False)

        await ctx.send(embed=embed)
    else:
        await ctx.send(f"Unit {unit_name} not found.")

#Clear Messages
@bot.command(name='clearmsg', help='Deletes a specified number of text messages')
async def clearmsg(ctx, num_messages: int = None):
    if num_messages is None:
        await ctx.send('Please specify the number of messages to delete. Usage: !clearmsg <number>')
        return

    def is_text_message(m):
        return not m.attachments

    try:
        deleted = await ctx.channel.purge(limit=num_messages, check=is_text_message)
        await ctx.send(f'{len(deleted)} text messages have been cleared.')
    except Exception as e:
        await ctx.send(f'An error occurred: {str(e)}')

#Clear Media
@bot.command(name='clearmedia', help='Deletes all media messages')
async def clearmedia(ctx):
    def is_media_message(m):
        return bool(m.attachments)

    try:
        deleted = await ctx.channel.purge(check=is_media_message)
        await ctx.send('Media messages have been cleared.')
    except Exception as e:
        await ctx.send(f'An error occurred: {str(e)}')


#Quote stuff
@bot.command(name='quote', help='Displays a random quote')
async def quote(ctx):
    quotes = read_quotes()
    if quotes:
        quote = random.choice(quotes)
        await ctx.send(quote)
    else:
        await ctx.send('No quotes available.')
@bot.command(name='addquote', help='Adds a new quote')
async def addquote(ctx, *, new_quote: str):
    add_quote(new_quote)
    await ctx.send('New quote added!')
@bot.command(name='searchquote', help='Searches for quotes containing a keyword')
async def searchquote(ctx, *, keyword: str):
    results = search_quotes(keyword)
    if results:
        await ctx.send('\n'.join(results))
    else:
        await ctx.send('No quotes found.')


#Bot Details Command
@bot.command(name='botdetails', help='Displays bot details')
async def botdetails(ctx):
    creators = "(yourname)"  # Fill in with your name
    servers = [guild.name for guild in bot.guilds]

    response = f"**Bot Creators:** {creators}\n"
    response += "**Servers:**\n"
    for server in servers:
        response += f"{server}\n"

    await ctx.send(response)

#Server Details Command
@bot.command(name='server', aliases=['serverdetails', 'sd'], help='Displays server details')
async def server(ctx):
    server = ctx.guild
    members = server.members
    member_count = server.member_count

    response = f"**Server Name:** {server.name}\n"
    response += f"**Total Members:** {member_count}\n\n"
    response += "**Member Details:**\n"
    for member in members:
        response += f"{member.name} - Joined Server: {member.joined_at.strftime('%Y-%m-%d')} - Joined Discord: {member.created_at.strftime('%Y-%m-%d')}\n"

    await ctx.send(response)

#8-Ball Command
@bot.command(name='8ball', help='Answers a yes/no question')
async def eight_ball(ctx):
    responses = [
        "It is certain.",
        "Without a doubt.",
        "You may rely on it.",
        "Yes, definitely.",
        "As I see it, yes.",
        "Most likely.",
        "Outlook good.",
        "Yes.",
        "Signs point to yes.",
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Very doubtful."
    ]
    await ctx.send(random.choice(responses))

#Create Role Command - not very useful. I just did it for the funnies.
@bot.command(name='createrole', help='Creates a new role with specified name and color, and assigns it to mentioned users')
async def createrole(ctx, *, args: str):
    parts = args.split(' ')
    name = None
    color = None
    members = []

    for part in parts:
        if part.startswith('name:'):
            name = part[len('name:'):]
        elif part.startswith('colour:'):
            color = part[len('colour:'):]
        elif part.startswith('<@') and part.endswith('>'):
            member_id = int(part[2:-1])
            member = ctx.guild.get_member(member_id)
            if member:
                members.append(member)

    if name and color:
        color = discord.Colour(int(color.lstrip('#'), 16))
        role = await ctx.guild.create_role(name=name, colour=color)
        for member in members:
            await member.add_roles(role)
        await ctx.send(f'Role `{name}` created with color `{color}` and assigned to mentioned users.')
    else:
        await ctx.send('Please provide a valid name and color for the role (e.g., !createrole name:Example colour:#FF5733 giveto:@user1 @user2).')


@bot.command(name='changestatus', help='Changes the bot status')
async def changestatus(ctx, *, new_status: str):
    if ctx.author.id in authorized_users:
        await bot.change_presence(activity=discord.Game(name=new_status))
        await ctx.send(f'Status changed to: {new_status}')
    else:
        await ctx.send('You are not authorized to use this command.')

@bot.command(name='remindme', help='Sets a reminder')
async def remindme(ctx, time: int, *, reminder: str):
    await ctx.send(f'Reminder set for {time} seconds.')
    await asyncio.sleep(time)
    await ctx.send(f'Reminder: {reminder}')



#I created this bot to use my own AI model using the GPT4ALL APi/library, however it would sometimes say bad things, so this command was so users could tell me if the bot said bad things. It got abused easily, so use it at your own risk (:
@bot.command(name='(your name)', help='Sends a message to specified users')
async def aaron(ctx, *, user_message: str):
    user_ids = [123456789]  # Replace with actual user IDs

    for user_id in user_ids:
        user = await bot.fetch_user(user_id)
        await user.send(user_message)

    await ctx.send('Message sent to specified users.')
    print(f'Message sent to users {user_ids}: {user_message}')



queue = []

@bot.command(name='play', aliases=['Play'], help='Plays a song from YouTube')
async def play(ctx, *, search: str = None):
    if search is None:
        await ctx.send('Usage: !play [song title]')
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch',
        'quiet': True,
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search, download=False)
        url = info['entries'][0]['url']
        title = info['entries'][0]['title']

    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client is None:
        await ctx.send('I am not connected to a voice channel.')
        return

    queue.append((url, title))

    if not voice_client.is_playing():
        await play_next(ctx)

    await ctx.send(f'Added to queue: {title}')


# Ensure the playlists directory exists
if not os.path.exists('playlists'):
    os.makedirs('playlists')


#Music command(s)
async def play_next(ctx):
    if queue:
        url, title = queue.pop(0)
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        # Extract video thumbnail
        with youtube_dl.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            thumbnail = info.get('thumbnail', 'https://example.com/default_thumbnail.jpg')  # Use a default URL if thumbnail is not found

        # Validate the thumbnail URL
        if not re.match(r'^https?://', thumbnail):
            thumbnail = 'https://example.com/default_thumbnail.jpg'  # Replace with an actual default URL

        # Create embed with video thumbnail
        embed = discord.Embed(title="Now Playing", description=title, color=0x00ff00)
        embed.set_image(url=thumbnail)

        # Define button callbacks
        async def pause_callback(interaction):
            if voice_client.is_playing():
                voice_client.pause()
                await interaction.response.send_message("Paused the current song.", ephemeral=True)

        async def resume_callback(interaction):
            if voice_client.is_paused():
                voice_client.resume()
                await interaction.response.send_message("Resumed the current song.", ephemeral=True)

        async def skip_callback(interaction):
            if voice_client.is_playing():
                voice_client.stop()
                await interaction.response.send_message("Skipped the current song.", ephemeral=True)
                await play_next(ctx)

        async def loop_callback(interaction):
            global loop, loop_single
            loop = not loop
            loop_single = False
            await interaction.response.send_message(f"Looping is now {'enabled' if loop else 'disabled'}.", ephemeral=True)

        async def playlist_callback(interaction):
            await interaction.response.send_message("Please enter the name of the playlist to add this song to:", ephemeral=True)

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                msg = await bot.wait_for('message', check=check, timeout=30)
                playlist_name = msg.content
                playlist_path = f'playlists/{ctx.guild.id}_{playlist_name}.json'

                if os.path.exists(playlist_path):
                    with open(playlist_path, 'r') as f:
                        playlist = json.load(f)
                else:
                    playlist = []

                playlist.append({'url': url, 'title': title})
                with open(playlist_path, 'w') as f:
                    json.dump(playlist, f, indent=4)

                await interaction.followup.send(f"Added {title} to playlist {playlist_name}.", ephemeral=True)
            except asyncio.TimeoutError:
                await interaction.followup.send("You took too long to respond.", ephemeral=True)

        # Create buttons
        pause_button = Button(label="Pause", style=discord.ButtonStyle.primary)
        pause_button.callback = pause_callback

        resume_button = Button(label="Resume", style=discord.ButtonStyle.primary)
        resume_button.callback = resume_callback

        skip_button = Button(label="Skip", style=discord.ButtonStyle.primary)
        skip_button.callback = skip_callback

        loop_button = Button(label="Loop", style=discord.ButtonStyle.primary)
        loop_button.callback = loop_callback

        playlist_button = Button(label="Playlist", style=discord.ButtonStyle.primary)
        playlist_button.callback = playlist_callback

        # Create view and add buttons
        view = View()
        view.add_item(pause_button)
        view.add_item(resume_button)
        view.add_item(skip_button)
        view.add_item(loop_button)
        view.add_item(playlist_button)

        # Play the audio
        voice_client.play(discord.FFmpegPCMAudio(url), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(embed=embed, view=view)

@bot.command(name='queue', help='Displays the current song queue')
async def queue(ctx):
    if queue:
        embed = discord.Embed(title="Queue",
                              description="\n".join([f"{i + 1}. {title}" for i, (_, title) in enumerate(queue)]),
                              color=0x00ff00)
    else:
        embed = discord.Embed(title="Queue", description="The queue is empty.", color=0x00ff00)

    await ctx.send(embed=embed)

@bot.command(name='skip', help='Skips the current song')
async def skip(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Skipped the current song.")
    else:
        await ctx.send("No song is currently playing.")

@bot.command(name='pause', help='Pauses the current song')
async def pause(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Paused the current song.")
    else:
        await ctx.send("No song is currently playing.")

@bot.command(name='resume', help='Resumes the paused song')
async def resume(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Resumed the current song.")
    else:
        await ctx.send("No song is currently paused.")

#This is repeated later down the line for reasons
loop = False
loop_single = False

@bot.command(name='loop', help='Loops the queue or the current song')
async def loop(ctx, mode: str = None):
    global loop, loop_single

    if mode is None:
        await ctx.send('Usage: !loop [queue/single/off]')
        return

    mode = mode.lower()

    if mode == 'queue':
        loop = True
        loop_single = False
        await ctx.send("Looping the queue.")
    elif mode == 'single':
        loop = False
        loop_single = True
        await ctx.send("Looping the current song.")
    elif mode == 'off':
        loop = False
        loop_single = False
        await ctx.send("Looping is turned off.")
    else:
        await ctx.send("Invalid mode. Use 'queue', 'single', or 'off'.")


@bot.command(name='leave', help='Disconnects the bot from the voice channel')
async def leave(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client:
        await voice_client.disconnect()
        await ctx.send('Disconnected from the voice channel.')
    else:
        await ctx.send('I am not connected to a voice channel.')


#This makes the bot join the voice channel - I couldn't make it work when I did !play, so it's a seperate command & check. This is my first bot, forgive me.
@bot.command(name='join', help='Joins the voice channel that the user is in')
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f'Joined {channel}')
    else:
        await ctx.send('You are not connected to a voice channel.')

@bot.command(name='playlist')
async def playlist(ctx, name=None):
    if name:
        playlist_path = f'playlists/{ctx.guild.id}_{name}.json'
        if os.path.exists(playlist_path):
            with open(playlist_path, 'r') as f:
                playlist = json.load(f)
            songs = '\n'.join([f"{song['title']} ({song['url']})" for song in playlist])
            await ctx.send(f"Playlist {name}:\n{songs}")
        else:
            await ctx.send(f"Playlist {name} does not exist.")
    else:
        playlists = [f.split('_')[1].replace('.json', '') for f in os.listdir('playlists') if f.startswith(f'{ctx.guild.id}_')]
        await ctx.send(f"Available playlists: {', '.join(playlists)}")

@bot.command(name='manage_playlists')
async def manage_playlists(ctx, action=None, playlist_name=None):
    if ctx.author.id not in authorized_users:
        await ctx.send("You do not have permission to use this command.")
        return

    if action == "list":
        playlists = [f.replace('.json', '') for f in os.listdir('playlists')]
        await ctx.send(f"Available playlists: {', '.join(playlists)}")
    elif action == "delete" and playlist_name:
        playlist_path = f'playlists/{playlist_name}.json'
        if os.path.exists(playlist_path):
            os.remove(playlist_path)
            await ctx.send(f"Deleted playlist {playlist_name}.")
        else:
            await ctx.send(f"Playlist {playlist_name} does not exist.")
    else:
        await ctx.send("Invalid action. Use `list` to view playlists or `delete <playlist_name>` to delete a playlist.")


#Play playlists.
@bot.command(name='play_playlist',aliases=['pp','PP','Pp']) #very funny... But i did this because people wouldn't spell it right - you could use the fuzzywuzzy library for some sort of error correction/check
async def play_playlist(ctx, playlist_name=None):
    if playlist_name:
        playlist_path = f'playlists/{ctx.guild.id}_{playlist_name}.json'
        if not os.path.exists(playlist_path):
            await ctx.send(f"Playlist {playlist_name} does not exist.")
            return

        with open(playlist_path, 'r') as f:
            playlist = json.load(f)

        if not playlist:
            await ctx.send(f"Playlist {playlist_name} is empty.")
            return

        for song in playlist:
            queue.append((song['url'], song['title']))

        await ctx.send(f"Added {len(playlist)} songs from {playlist_name} to the queue.")
        await play_next(ctx)
    else:
        playlists = [f.split('_')[1].replace('.json', '') for f in os.listdir('playlists') if f.startswith(f'{ctx.guild.id}_')]
        if not playlists:
            await ctx.send("No playlists found for this server.")
            return

        # Create buttons for each playlist
        buttons = []
        for playlist in playlists:
            button = Button(label=playlist, style=discord.ButtonStyle.primary)
            button.callback = create_playlist_callback(ctx, playlist)
            buttons.append(button)

        # Create view and add buttons
        view = View()
        for button in buttons:
            view.add_item(button)

        await ctx.send("Select a playlist to play:", view=view)

#Playlists will be stored by Server, though there is somewhat of a way to get playlists from other servers.

#Create playlists from the Discord Interact
def create_playlist_callback(ctx, playlist_name):
    async def callback(interaction):
        playlist_path = f'playlists/{ctx.guild.id}_{playlist_name}.json'
        if not os.path.exists(playlist_path):
            await interaction.response.send_message(f"Playlist {playlist_name} does not exist.", ephemeral=True)
            return

        with open(playlist_path, 'r') as f:
            playlist = json.load(f)

        if not playlist:
            await interaction.response.send_message(f"Playlist {playlist_name} is empty.", ephemeral=True)
            return

        for song in playlist:
            queue.append((song['url'], song['title']))

        await interaction.response.send_message(f"Added {len(playlist)} songs from {playlist_name} to the queue.", ephemeral=True)
        await play_next(ctx)

    return callback


FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -reconnect_at_eof 1 -reconnect_streamed 1 -reconnect_delay_max 2',
    'options': '-vn -bufsize 64k'
}
#Explanation of above code:
# -reconnect_at_eof 1: This option ensures that FFMPEG will attempt to reconnect if the connection is lost at the end of the file.
# -reconnect_streamed 1: This option tells FFMPEG to reconnect if the stream is interrupted.
# -reconnect_delay_max 2: This reduces the maximum delay between reconnection attempts to 2 seconds.
# -bufsize 64k: This sets the buffer size to 64k, which can help with smoother streaming.


# Ensure the playlists directory exists
if not os.path.exists(r'"C:\Users\docto\Documents"'):
    os.makedirs('playlists')

#Music Shit
queue = []
loop = False
loop_single = False

#These are the users you allow to change the bot's status and etc. I'd suggest not using this, but feel free to.
authorized_users = [123465789] #Replace with actual ids

# Run the bot
bot.run(TOKEN)