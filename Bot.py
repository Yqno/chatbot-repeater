import discord
import os
import json
import random
import spacy
from discord.ext import commands
from discord import app_commands

# Initialize spaCy and load the English model
nlp = spacy.load('en_core_web_sm')

TOKEN = ""  # Token here
DATA_FILE = 'channel_messages.json'
ALLOWED_CHANNELS = []  # Channel IDs here
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize message counters
message_counters = {}

# Load messages from file if it exists and is valid
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, 'r') as f:
            channel_messages = json.load(f)
    except (json.JSONDecodeError, IOError):
        channel_messages = {}
else:
    channel_messages = {}

@bot.event
async def on_ready():
    await bot.tree.sync()  # Sync the slash commands
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    channel_id = str(message.channel.id)

    # Check if the channel is allowed
    if channel_id not in ALLOWED_CHANNELS:
        return

    # Initialize the counter for the channel if it doesn't exist
    if channel_id not in message_counters:
        message_counters[channel_id] = 0

    # Increment the message counter
    message_counters[channel_id] += 1

    # Add message to channel's list of messages
    if channel_id not in channel_messages:
        channel_messages[channel_id] = []
    channel_messages[channel_id].append(message.content)

    # Save messages to file
    with open(DATA_FILE, 'w') as f:
        json.dump(channel_messages, f)

    # Generate a response if the counter reaches the threshold
    threshold = random.randint(1, 5)
    if message_counters[channel_id] >= threshold:
        message_counters[channel_id] = 0  # Reset the counter

        # Process the messages with spaCy
        doc = nlp(' '.join(channel_messages[channel_id]))

        # Collect nouns from the messages
        nouns = [token.text for token in doc if token.pos_ == 'NOUN']

        # If there are enough nouns, respond with a random selection
        if len(nouns) > 0:
            response = " ".join(random.sample(nouns, min(len(nouns), 10)))
            await message.channel.send(response)

@bot.tree.command(name="clear", description="Löscht alle gespeicherten Nachrichten in diesem Kanal.")
@app_commands.checks.has_permissions(administrator=True)
async def clear(interaction: discord.Interaction):
    channel_id = str(interaction.channel.id)

    # Clear the messages for this channel
    if channel_id in channel_messages:
        channel_messages[channel_id] = []
        with open(DATA_FILE, 'w') as f:
            json.dump(channel_messages, f)
        await interaction.response.send_message('Alle gespeicherten Nachrichten wurden gelöscht.', ephemeral=True)

    # Reset the message counter for this channel
    if channel_id in message_counters:
        message_counters[channel_id] = 0

@clear.error
async def clear_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message('Du hast keine Berechtigung, diesen Befehl auszuführen.', ephemeral=True)

bot.run(TOKEN)
