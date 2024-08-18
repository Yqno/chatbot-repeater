import discord
import os
import json
import random
import re
from discord.ext import commands
from discord import app_commands



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

def generate_sentence(words):
    if not words:
        return ""

    # Create bigrams from the word list
    bigrams = list(zip(words, words[1:]))

    # Start the sentence with a random word
    current_word = random.choice(words)
    sentence = [current_word]

    while len(sentence) < 10:  # Limit sentence length to 10 words
        # Find all bigrams that can follow the current word
        candidates = [b[1] for b in bigrams if b[0] == current_word]
        if not candidates:
            break
        next_word = random.choice(candidates)
        sentence.append(next_word)
        current_word = next_word

    return " ".join(sentence)

def clean_message(content):
    # Remove links (http, https, www)
    content = re.sub(r'http\S+|www\S+', '', content)
    
    # Remove Discord IDs (17-19 digit numbers)
    content = re.sub(r'\b\d{17,19}\b', '', content)
    
    # Remove emojis (using regex for Unicode emoji ranges)
    content = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002700-\U000027BF]', '', content)
    
    return content

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

        # Flatten all words in the channel's messages and clean them
        all_words = []
        for msg in channel_messages[channel_id]:
            cleaned_msg = clean_message(msg.lower())  # Clean the message to remove unwanted parts
            words = re.findall(r'\b\w+\b', cleaned_msg)  # Extract remaining words
            all_words.extend(words)

        # Generate a sentence from the words
        response = generate_sentence(all_words)

        if response:
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
