import discord
import asyncio

from eleven_labs import add_voice as add_elevenlabs_voice
from sqlite_database import get_elevenlabs_api_key, store_voice_role

class AddVoiceModal(discord.ui.Modal):
    def __init__(self, interaction, conn):
        super().__init__(title="Add Voice")
        self.interaction = interaction
        self.conn = conn

        self.add_item(discord.ui.InputText(label="Voice Name"))
        self.add_item(discord.ui.InputText(label="Voice Audio File URL"))
        self.add_item(discord.ui.InputText(label="Role Message", style=discord.InputTextStyle.long))


    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Modal Results")

        name = self.children[0].value
        file_url = self.children[1].value
        role_message = self.children[2].value


        embed.add_field(name="Voice Name", value=name, inline=False)
        embed.add_field(name="Voice Audio File URL", value=f"[Link]({file_url})", inline=False)
        embed.add_field(name="Role Message", value=role_message, inline=False)
        
        # Add footer
        embed.set_footer(text="📤 Sending to ElevenLabs...")

        sent_message = await interaction.channel.send(embed=embed)

        # Close modal
        await interaction.response.defer()

        """Add a new voice to Eleven Labs Text-to-Speech API"""
        # Call the add_voice function from eleven_labs.py file
        elevenlabs_api_key = get_elevenlabs_api_key(self.conn, interaction.guild.id)
        response = add_elevenlabs_voice(elevenlabs_api_key, name, file_url)


        # Send the response back to the user
        if response is not None:
            # Update the footer based on the response
            embed.set_footer(text="✅ Voice added to ElevenLabs")
            voice_id = response.get('voice_id')
            store_voice_role(self.conn, voice_id, interaction.guild.id, role_message)
        else:
            # Update the footer based on the failed response
            embed.set_footer(text="❌ Failed to add voice to ElevenLabs")

        # Edit the message to replace it with the updated embed
        await sent_message.edit(embed=embed)