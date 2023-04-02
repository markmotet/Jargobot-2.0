import discord
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
import wave
import asyncio
import os
import openai

from whisper_transcribe import transcribe_with_whisper
from eleven_labs import text_to_speech, UnauthorizedError, add_voice as add_elevenlabs_voice, delete_voice as delete_elevenlabs_voice, edit_voice as edit_elevenlabs_voice, get_voices as get_elevenlabs_voices, get_voice_metadata as get_elevenlabs_voice_metadata
from chatgpt import send_to_chatgpt
from play_audio import play_audio
from sqlite_database import setup_database, store_elevenlabs_api_key, get_elevenlabs_api_key, store_openai_api_key, get_openai_api_key, get_role_message, set_role_message, voice_id_exists, get_server_data, append_to_message_list, set_server_data, show_table
from voices_dictionary import voices_dictionary
from modals import *

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.slash_command()
async def play(ctx):
    print('Playing audio...')
    channel = ctx.author.voice.channel
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if not voice_client:
        print('Connecting to voice channel...')
        voice_client = await channel.connect()
    audio_source = FFmpegPCMAudio('./audio.mp3')
    if not voice_client.is_playing():
        print('Playing audio...')
        voice_client.play(audio_source, after=None)

    while voice_client.is_playing():
        await asyncio.sleep(1)
    await voice_client.disconnect()

role_message = "Hello, I am your personal assistant. I am here to help you with your daily tasks."


async def once_done(sink: discord.sinks, channel: discord.TextChannel, *args):  # Our voice client already passes these in.
    
    ctx = args[0]

    for user_id, audio in sink.audio_data.items():
        with open("output.wav", "wb") as f:
            f.write(audio.file.getbuffer())

    try:
        print('Transcribing...')
        await update_embed(ctx, '✍️ Transcribing...')
        recording_transcription = transcribe_with_whisper("./output.wav")

        print('\nSending to ChatGPT...')
        await update_embed(ctx, '🤖 Sending to ChatGPT...', transcription=recording_transcription)

        append_to_message_list(conn, ctx.guild.id, {"role": "user", "content": recording_transcription})
        message_list = get_server_data(conn, ctx.guild.id, 'message_list')
        chat_gpt_response = send_to_chatgpt(get_openai_api_key(conn, ctx.guild.id), message_list)

        print('\nSending to ElevenLabs...\n')
        await update_embed(ctx, '💬 Sending to ElevenLabs...', response=f"||{chat_gpt_response}||")

        text_to_speech(chat_gpt_response, get_server_data(conn, ctx.guild.id, 'active_voice_id'), get_elevenlabs_api_key(conn, ctx.guild.id))

        append_to_message_list(conn, ctx.guild.id, {"role": "assistant", "content": chat_gpt_response})
        message_list =  get_server_data(conn, ctx.guild.id, 'message_list')

        await update_embed(ctx, '🔊 Playing audio...', response=f"{chat_gpt_response}")
        await play(ctx) # Args[0] is the voice channel context
        await update_embed(ctx, '')
    except openai.error.AuthenticationError as e:
        await update_embed(ctx, "⚠️ Your OpenAI API key is invalid. Please use the !setup command to set a valid OpenAI API key.")
    except UnauthorizedError as e:        
        await update_embed(ctx, "⚠️ Your ElevenLabs API key is invalid. Please use the !setup command to set a valid ElevenLabs API key.")

async def send_instructions_embed(ctx, service_name, instructions, image_url):
    embed = discord.Embed(
        title=f"Find your {service_name} API key",
        description=instructions,
        color=discord.Color.blue()
    )
    embed.set_image(url=image_url)
    await ctx.author.send(embed=embed)


@bot.slash_command()
async def setup(ctx):
   
    def check(message):
        return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)
    
    # Send embed telling user to check their DMs
    embed = discord.Embed(
        title="Setup",
        description="Please check your DMs for instructions on how to set up your API keys.",
        color=discord.Color.blue()
    )
    await ctx.respond(embed=embed)
    
    # Ask for ElevenLabs API key
    elevenlabs_instructions = (
        "1. Log in to your ElevenLabs account at https://beta.elevenlabs.io/\n"
        "2. Click on your profile picture and then Profile.\n"
        "3. Click on the eye icon next to your API key to reveal it.\n"
        "3. Copy your API key and paste it here."
    )
    elevenlabs_image_url = "https://i.imgur.com/HmF5DP9.png"
    await send_instructions_embed(ctx, "ElevenLabs", elevenlabs_instructions, elevenlabs_image_url)
    await ctx.author.send("Please provide your ElevenLabs API key:")
    try:
        elevenlabs_api_key_message = await bot.wait_for('message', check=check, timeout=60)
        elevenlabs_api_key = elevenlabs_api_key_message.content
        store_elevenlabs_api_key(conn, ctx.guild.id, elevenlabs_api_key)
    except asyncio.TimeoutError:
        await ctx.author.send("ElevenLabs API key request timed out. Please try the setup command again.")
        return

    # Ask for OpenAI API key
    openai_instructions = (
        "1. Log in to your OpenAI account at https://platform.openai.com/account/api-keys/\n"
        "2. Click *Create new secret key*.\n"
        "3. Copy your API key and paste it here."
    )
    openai_image_url = "https://i.imgur.com/ONvQFiQ.png"
    await send_instructions_embed(ctx, "OpenAI", openai_instructions, openai_image_url)
    await ctx.author.send("Please provide your OpenAI API key:")
    try:
        openai_api_key_message = await bot.wait_for('message', check=check, timeout=60)
        openai_api_key = openai_api_key_message.content
        store_openai_api_key(conn, ctx.guild.id, openai_api_key)
        await ctx.author.send("API keys saved successfully!")
    except asyncio.TimeoutError:
        await ctx.author.send("OpenAI API key request timed out. Please try the setup command again.")


connections = {}
async def record(ctx):  # If you're using commands.Bot, this will also work.
    
    await update_embed(ctx, '🔴 Recording...', transcription='-----',response='-----')

    voice = ctx.author.voice

    if not voice:
        await ctx.respond("You aren't in a voice channel!")

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

async def stop_recording(ctx):
    vc = connections.get(ctx.guild.id)
    if not vc:
        await ctx.respond("I'm not in the voice chat!")

    vc.stop_recording()

def get_voices(ctx):
    elevenlabs_api_key = get_elevenlabs_api_key(conn, ctx.guild.id)
    response = get_elevenlabs_voices(elevenlabs_api_key)

    if response is None:
        print("Failed to get voices. Please check your API key.")
        return

    # voice_list = "\n".join([f"{voice['name']} ({voice['voice_id']})" for voice in response['voices']])
    # await ctx.respond(f"Available voices:\n{voice_list}")
    
    # Return a dictionary of voice names and IDs
    voices_dictionary = {voice['name']: voice['voice_id'] for voice in response['voices']}
    print(voices_dictionary)
    return voices_dictionary


class VoiceSelect(discord.ui.Select):
    def __init__(self, ctx, all_options):
        super().__init__(placeholder="Select an option", min_values=1, max_values=1, options=all_options)
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        selected_voice_id = self.values[0]
        # Do something with the selected_voice_id, e.g., change the bot's voice or send a message
        
        #defer the interaction
        await interaction.response.defer()
        
        print(f'Selected voice: {selected_voice_id}')


        set_server_data(conn, self.ctx.guild.id, 'active_voice_id', selected_voice_id)

        # print voice_id
        print(get_server_data(conn, self.ctx.guild.id, 'active_voice_id'))

        await wipe_memory(self.ctx)

class MyView(discord.ui.View):
    
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.is_recording = False  # Add an attribute to track the button's state

        self.all_options = []
        
        for name, id in get_voices(self.ctx).items():
            option = discord.SelectOption(
                label=name,
                value=id
                # description=info[1] if len(info) > 1 else None,  # use the description from the dictionary if it exists
            )
            self.all_options.append(option)

            # Only add max 25 options
            if len(self.all_options) == 25:
                break

        voice_dropdown = VoiceSelect(self.ctx, self.all_options)

        self.add_item(voice_dropdown)

    @discord.ui.button(label="Start Recording", style=discord.ButtonStyle.secondary, emoji="🔴")
    async def toggle_recording_button(self, button, interaction):
        if not self.is_recording:  # If not recording, start recording
            self.is_recording = True
            button.label = "Stop Recording"
            button.style = discord.ButtonStyle.primary
            button.emoji = "⬛"
            await interaction.response.edit_message(view=self)  # Update the button

            await record(self.ctx)

        else:  # If recording, stop recording
            self.is_recording = False
            button.label = "Start Recording"
            button.style = discord.ButtonStyle.secondary
            button.emoji = "🔴"
            await interaction.response.edit_message(view=self)  # Update the button

            await stop_recording(self.ctx)

    @discord.ui.button(label="Wipe Memory", style=discord.ButtonStyle.red, emoji="🧠")
    async def button_callback_3(self, button, interaction):
        await interaction.response.defer()
        await wipe_memory(self.ctx)


message_id = 0


@bot.slash_command()
async def start(interaction: discord.Interaction):

    # Check if the API keys are set up
    elevenlabs_api_key = get_elevenlabs_api_key(conn, interaction.guild.id)
    openai_api_key = get_openai_api_key(conn, interaction.guild.id)

    if not elevenlabs_api_key or not openai_api_key:
        await interaction.respond("API keys are not set up properly. Please use the `!setup` command to configure them.")
        return

    # Start only if the user is in a voice channel
    if interaction.user.voice:

        await interaction.respond(view=MyView(interaction))

        # Send embed with status text
        embed = discord.Embed()

        embed.add_field(name="Transcription", value="-----", inline=False)
        embed.add_field(name="Response", value="-----", inline=False)
        message = await interaction.respond(embed=embed)

        global message_id
        message_id = message.id
    else:
        await interaction.respond("You are not connected to a voice channel.")

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


async def wipe_memory(ctx):
    active_voice_id = get_server_data(conn, ctx.guild.id, 'active_voice_id')
    role_message = get_role_message(conn, active_voice_id)

    if role_message is None:

        active_voice_name = get_elevenlabs_voice_metadata('6KOFFSnEErfEPlIDFRAG', '1704283141ae07b8be59633963340465')['name']
        role_message = f"Respond as though you are {active_voice_name}."

        # Set the role message in the database
        set_role_message(conn, active_voice_id, ctx.guild.id, role_message)

    set_server_data(conn, ctx.guild.id, 'message_list', [{"role": "system", "content": role_message}])

    await update_embed(ctx, transcription='-----', response='-----')



@bot.slash_command()
async def add_voice(interaction: discord.Interaction):
    """Shows an example of a modal dialog being invoked from a slash command."""
    modal = AddVoiceModal(interaction, conn)
    await interaction.send_modal(modal)



@bot.slash_command()
async def delete_voice(interaction: discord.Interaction, voice_id):
    """Delete a voice from Eleven Labs Text-to-Speech API"""
    await interaction.trigger_typing()

    # Call the delete_voice function from eleven_labs.py file
    elevenlabs_api_key = get_elevenlabs_api_key(conn, interaction.guild.id)
    response = delete_elevenlabs_voice(voice_id, elevenlabs_api_key)
    
    # Send the response back to the user
    if response is not None:
        await interaction.respond(f"Voice `{voice_id}` deleted successfully.")
    else:
        await interaction.respond("Failed to delete voice. Please check your API key and voice ID.")

@bot.slash_command()
async def edit_voice(interaction: discord.Interaction):
    """Shows an example of a modal dialog being invoked from a slash command."""
    modal = EditVoiceModal(interaction, conn)
    await interaction.send_modal(modal)


conn = setup_database()
bot.run(os.environ['DISCORD_BOT_TOKEN'])