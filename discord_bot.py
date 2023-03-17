import discord
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
import wave
import asyncio
import os

from whisper_transcribe import transcribe_with_whisper
from eleven_labs import send_to_eleven_labs
from chatgpt import send_to_chatgpt
from play_audio import play_audio
from sqlite_database import setup_database, store_elevenlabs_api_key, get_elevenlabs_api_key, store_openai_api_key, get_openai_api_key, view_database_entries
from voices_dictionary import voices_dictionary

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

elevenlabs_api_key = ""
openai_api_key = ""
active_voice_id = voices_dictionary['Dumbledore'][0]

async def play(ctx):
    channel = ctx.author.voice.channel
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if not voice_client:
        voice_client = await channel.connect()
    audio_source = FFmpegPCMAudio('./audio.mp3')
    if not voice_client.is_playing():
        voice_client.play(audio_source, after=None)

    while voice_client.is_playing():
        await asyncio.sleep(1)
    await voice_client.disconnect()

role_message = "Hello, I am your personal assistant. I am here to help you with your daily tasks."
message_list = [
            {"role": "system", "content": role_message},
        ]

async def once_done(sink: discord.sinks, channel: discord.TextChannel, *args):  # Our voice client already passes these in.
    
    ctx = args[0]

    for user_id, audio in sink.audio_data.items():
        with open("output.wav", "wb") as f:
            f.write(audio.file.getbuffer())

    # User response
    print('Transcribing...')
    await update_embed(ctx, 'Transcribing...')

    recording_transcription = transcribe_with_whisper("./output.wav")
    await update_embed(ctx, transcription=recording_transcription)
    message_list.append({"role": "user", "content": recording_transcription})

    
    # AI Response
    print('\nSending to ChatGPT...')
    await update_embed(ctx, 'Sending to ChatGPT...')
    chat_gpt_response = send_to_chatgpt(openai_api_key, message_list)
    print('\nSending to ElevenLabs...\n')
    await update_embed(ctx, 'Sending to ElevenLabs...')
    send_to_eleven_labs(chat_gpt_response, active_voice_id, elevenlabs_api_key)  
    message_list.append({"role": "assistant", "content": chat_gpt_response})
    for message in message_list:
        print(message['role'] + ': ' + message['content'])

    await update_embed(ctx, status='', transcription=recording_transcription, response=chat_gpt_response)
    await play(ctx) # Args[0] is the voice channel context

@bot.command()
async def setup(ctx):
    def check(message):
        return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)

    # Ask for ElevenLabs API key
    await ctx.author.send("Please provide your ElevenLabs API key:")
    try:
        elevenlabs_api_key_message = await bot.wait_for('message', check=check, timeout=60)
        global elevenlabs_api_key
        elevenlabs_api_key = elevenlabs_api_key_message.content
        store_elevenlabs_api_key(conn, ctx.guild.id, elevenlabs_api_key)
    except asyncio.TimeoutError:
        await ctx.author.send("ElevenLabs API key request timed out. Please try the setup command again.")
        return

    # Ask for OpenAI API key
    await ctx.author.send("Please provide your OpenAI API key:")
    try:
        openai_api_key_message = await bot.wait_for('message', check=check, timeout=60)
        global openai_api_key
        openai_api_key = openai_api_key_message.content
        store_openai_api_key(conn, ctx.guild.id, openai_api_key)
        await ctx.author.send("API keys saved successfully!")
    except asyncio.TimeoutError:
        await ctx.author.send("OpenAI API key request timed out. Please try the setup command again.")


    view_database_entries(conn)



connections = {}
@bot.command()
async def record(ctx):  # If you're using commands.Bot, this will also work.
    
    await update_embed(ctx, 'Recording...', transcription='-----',response='-----')

    voice = ctx.author.voice

    if not voice:
        await ctx.send("You aren't in a voice channel!")

    # # Check if the bot is already in a voice channel.
    # if ctx.guild.id not in connections:
    vc = await voice.channel.connect()

    connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.

    vc.start_recording(
        discord.sinks.WaveSink(),  # The sink type to use.
        once_done,  # What to do once done.
        ctx,  # The channel to disconnect from.
        ctx,
    )

@bot.command()
async def stop_recording(ctx):
    vc = connections.get(ctx.guild.id)
    if not vc:
        await ctx.send("I'm not in the voice chat!")

    vc.stop_recording()

class MyView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
    
    all_options = []

    for name, info in voices_dictionary.items():
        option = discord.SelectOption(
            label=name,
            # description=info[1] if len(info) > 1 else None,  # use the description from the dictionary if it exists
        )
        all_options.append(option)

    @discord.ui.select( # the decorator that lets you specify the properties of the select menu
            placeholder = "Select AI Character...", # the placeholder text that will be displayed if nothing is selected
            min_values = 1, # the minimum number of values that must be selected by the users
            max_values = 1, # the maximum number of values that can be selected by the users

            options = all_options
        )
    async def select_callback(self, select, interaction): # the function called when the user is done selecting options
        await interaction.response.defer()
        global active_voice_id
        global role_message
        active_voice_id = voices_dictionary[select.values[0]][0]
        role_message = voices_dictionary[select.values[0]][1]
        await wipe_memory(self.ctx)

    @discord.ui.button(label="Start Recording", style=discord.ButtonStyle.primary, emoji="🔴")
    async def button_callback_1(self, button, interaction):

        # Acknowledge the interaction
        await interaction.response.defer()
        await record(self.ctx)

    @discord.ui.button(label="Stop Recording", style=discord.ButtonStyle.secondary, emoji="⬛")
    async def button_callback_2(self, button, interaction):
        await interaction.response.defer()
        await stop_recording(self.ctx)

    @discord.ui.button(label="Wipe Memory", style=discord.ButtonStyle.secondary, emoji="🧠")
    async def button_callback_3(self, button, interaction):
        await interaction.response.defer()
        await wipe_memory(self.ctx)


message_id = 0

@bot.command()
async def start(ctx):
    # Start only if the user is in a voice channel
    if ctx.author.voice:

        # Get and store api keys if they aren't already stored
        global elevenlabs_api_key
        global openai_api_key
        if not elevenlabs_api_key:
            elevenlabs_api_key = get_elevenlabs_api_key(conn, ctx.guild.id)
        if not openai_api_key:
            openai_api_key = get_openai_api_key(conn, ctx.guild.id)


        await ctx.send(view=MyView(ctx))

        # Send embed with status text
        embed = discord.Embed()

        embed.add_field(name="Transcription", value="-----", inline=False)
        embed.add_field(name="Response", value="-----", inline=False)
        message = await ctx.send(embed=embed)

        global message_id
        message_id = message.id
    else:
        await ctx.send("You are not connected to a voice channel.")

@bot.command()
async def update_embed(ctx, status=None, transcription=None, response=None):
    # Get the original message with the embed
    message = await ctx.channel.fetch_message(message_id)

    embed = message.embeds[0]

    # Modify the embed status
    if status is not None:
        embed.set_footer(text=status)

    # Modify the embed fields if the optional parameters were provided
    if transcription is not None:
        embed.set_field_at(0, name='Transcription', value=transcription, inline=False)
    if response is not None:
            if len(response) <= 1024:
                embed.set_field_at(1, name='Response', value=response, inline=False)
            else:
                # Truncate the response to 1021 characters and add ellipsis to indicate it was truncated
                response = response[:1021] + '...'
                embed.set_field_at(1, name='Response', value=response, inline=False)

    # Update the message with the modified embed
    await message.edit(embed=embed)


@bot.command()
async def wipe_memory(ctx):
    global message_list
    global role_message
    message_list = [
            {"role": "system", "content": role_message},
        ]
    await update_embed(ctx, transcription='-----', response='-----')

# Send elevenlabs apikey to general channel
@bot.command()
async def send_apikey(ctx):

    #send elevenlabs apikey to general channel
    global elevenlabs_api_key
    elevenlabs_api_key = get_elevenlabs_api_key(conn, ctx.guild.id)
    await ctx.send(elevenlabs_api_key)
    #send openai apikey to general channel
    global openai_api_key
    openai_api_key = get_openai_api_key(conn, ctx.guild.id)
    await ctx.send(openai_api_key)

    view_database_entries(conn)

conn = setup_database()
bot.run(os.environ['DISCORD_BOT_TOKEN'])