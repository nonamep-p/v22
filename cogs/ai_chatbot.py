import discord
from discord.ext import commands
from discord import app_commands
import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any

try:
    import google.generativeai as genai
    from google.ai import generativelanguage as glm
    from google.generativeai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from config import COLORS, EMOJIS, get_server_config, is_module_enabled, get_ai_api_key
from utils.helpers import create_embed
from replit import db

logger = logging.getLogger(__name__)

class AIChatbotCog(commands.Cog):
    """AI Chatbot using Google Gemini."""

    def __init__(self, bot):
        self.bot = bot

        if not GEMINI_AVAILABLE:
            self.model = None
            logger.warning("Google Generative AI not available - AI features disabled")
            return

        # Configure Gemini
        api_key = get_ai_api_key()
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("GEMINI_API_KEY not found - AI features disabled")

        self.conversation_history = {}  # Store conversation history per user

    def get_conversation_history(self, user_id: int, guild_id: int) -> list:
        """Get conversation history for a user in a guild."""
        key = f"{guild_id}_{user_id}"
        return self.conversation_history.get(key, [])

    def add_to_conversation_history(self, user_id: int, guild_id: int, role: str, content: str):
        """Add message to conversation history."""
        key = f"{guild_id}_{user_id}"
        if key not in self.conversation_history:
            self.conversation_history[key] = []

        self.conversation_history[key].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })

        # Keep only last 20 messages to avoid token limits
        if len(self.conversation_history[key]) > 20:
            self.conversation_history[key] = self.conversation_history[key][-20:]

    def clear_conversation_history(self, user_id: int, guild_id: int):
        """Clear conversation history for a user."""
        key = f"{guild_id}_{user_id}"
        if key in self.conversation_history:
            del self.conversation_history[key]

    async def generate_response(self, user_message: str, user_id: int, guild_id: int, user_name: str) -> str:
        """Generate AI response."""
        if not self.model:
            return "❌ AI service is currently unavailable. Please try again later."

        try:
            # Get conversation history
            history = self.get_conversation_history(user_id, guild_id)

            # Build system prompt
            system_prompt = (
                "You are Plagg, the Kwami of Destruction from Miraculous. You're sarcastic, lazy, and obsessed with cheese (especially Camembert). "
                "You have immense destructive power but would rather nap and eat cheese than work. You're witty and often tease users, "
                "but you're secretly loyal and wise. Respond with a casual, sarcastic tone and occasionally mention cheese or being tired. "
                "You help with Discord server features like RPG games and economy, but act like it's a bother. "
                "Keep responses concise and maintain Plagg's personality - lazy but knowledgeable."
            )

            # Build conversation context
            conversation_parts = []
            for msg in history[-10:]:  # Use last 10 messages for context
                conversation_parts.append(f"{msg['role']}: {msg['content']}")

            # Add current message
            conversation_parts.append(f"user: {user_message}")

            # Create the prompt
            full_prompt = f"{system_prompt}\n\nConversation history:\n" + "\n".join(conversation_parts)

            # Generate response using Gemini
            response = self.model.generate_content(full_prompt)

            return response.text

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return f"❌ Sorry, I encountered an error: {str(e)}"

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle messages for AI chat."""
        if message.author.bot:
            return

        # Check if bot is mentioned or message is a reply to bot
        bot_mentioned = self.bot.user in message.mentions
        reply_to_bot = (message.reference and 
                       message.reference.message_id and 
                       message.reference.cached_message and 
                       message.reference.cached_message.author == self.bot.user)

        if not bot_mentioned and not reply_to_bot:
            return

        # Check if AI is enabled
        if not is_module_enabled("ai_chatbot", message.guild.id):
            return

        # Check if in allowed channels
        config = get_server_config(message.guild.id)
        ai_channels = config.get('ai_channels', [])

        if ai_channels and message.channel.id not in ai_channels:
            return

        # Clean the message content
        content = message.content
        if bot_mentioned:
            content = content.replace(f'<@{self.bot.user.id}>', '').strip()

        if not content:
            content = "Hello!"

        # Show typing indicator
        async with message.channel.typing():
            response = await self.generate_response(
                content, 
                message.author.id, 
                message.guild.id, 
                message.author.display_name
            )

        # Send response
        if len(response) > 2000:
            # Split long responses
            chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
            for chunk in chunks:
                await message.reply(chunk)
        else:
            await message.reply(response)

    @commands.command(name='chat', help='Chat with AI')
    async def chat_command(self, ctx, *, message: str):
        """Direct chat command."""
        if not is_module_enabled("ai_chatbot", ctx.guild.id):
            return

        # Check if in allowed channels
        config = get_server_config(ctx.guild.id)
        ai_channels = config.get('ai_channels', [])

        if ai_channels and ctx.channel.id not in ai_channels:
            await ctx.send("❌ AI chat is not enabled in this channel!")
            return

        async with ctx.typing():
            response = await self.generate_response(
                message, 
                ctx.author.id, 
                ctx.guild.id, 
                ctx.author.display_name
            )

        await ctx.send(response)

    @app_commands.command(name="chat", description="Chat with AI")
    @app_commands.describe(message="Your message to the AI")
    async def chat_slash(self, interaction: discord.Interaction, message: str):
        """Chat with AI (slash command)."""
        if not is_module_enabled("ai_chatbot", interaction.guild.id):
            await interaction.response.send_message("❌ AI chatbot module is disabled!", ephemeral=True)
            return

        # Check if in allowed channels
        config = get_server_config(interaction.guild.id)
        ai_channels = config.get('ai_channels', [])

        if ai_channels and interaction.channel.id not in ai_channels:
            await interaction.response.send_message("❌ AI chat is not enabled in this channel!", ephemeral=True)
            return

        await interaction.response.defer()

        response = await self.generate_response(
            message, 
            interaction.user.id, 
            interaction.guild.id, 
            interaction.user.display_name
        )

        await interaction.followup.send(response)

    @commands.command(name='clear_chat', help='Clear your chat history')
    async def clear_chat_command(self, ctx):
        """Clear user's chat history."""
        if not is_module_enabled("ai_chatbot", ctx.guild.id):
            return

        self.clear_conversation_history(ctx.author.id, ctx.guild.id)

        embed = create_embed(
            "✅ Chat History Cleared",
            "Your conversation history has been cleared!",
            COLORS['success']
        )
        await ctx.send(embed=embed)

    @app_commands.command(name="clear_chat", description="Clear your chat history")
    async def clear_chat_slash(self, interaction: discord.Interaction):
        """Clear user's chat history (slash command)."""
        if not is_module_enabled("ai_chatbot", interaction.guild.id):
            await interaction.response.send_message("❌ AI chatbot module is disabled!", ephemeral=True)
            return

        self.clear_conversation_history(interaction.user.id, interaction.guild.id)

        embed = create_embed(
            "✅ Chat History Cleared",
            "Your conversation history has been cleared!",
            COLORS['success']
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name='ai_status', help='Check AI system status')
    async def ai_status_command(self, ctx):
        """Check AI system status."""
        if not is_module_enabled("ai_chatbot", ctx.guild.id):
            return

        embed = discord.Embed(
            title=f"{EMOJIS['ai']} AI System Status",
            color=COLORS['info']
        )

        # Check AI client status
        if self.model:
            embed.add_field(
                name="🟢 AI Client",
                value="Connected and ready",
                inline=True
            )
        else:
            embed.add_field(
                name="🔴 AI Client",
                value="Not connected",
                inline=True
            )

        # Check configuration
        config = get_server_config(ctx.guild.id)
        ai_channels = config.get('ai_channels', [])

        if ai_channels:
            channel_mentions = [f"<#{ch}>" for ch in ai_channels]
            embed.add_field(
                name="📝 AI Channels",
                value=", ".join(channel_mentions),
                inline=True
            )
        else:
            embed.add_field(
                name="📝 AI Channels",
                value="All channels (when mentioned)",
                inline=True
            )

        # Conversation stats
        user_history = self.get_conversation_history(ctx.author.id, ctx.guild.id)
        embed.add_field(
            name="💬 Your Chat History",
            value=f"{len(user_history)} messages",
            inline=True
        )

        await ctx.send(embed=embed)

    @app_commands.command(name="ai_status", description="Check AI system status")
    async def ai_status_slash(self, interaction: discord.Interaction):
        """Check AI system status (slash command)."""
        if not is_module_enabled("ai_chatbot", interaction.guild.id):
            await interaction.response.send_message("❌ AI chatbot module is disabled!", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{EMOJIS['ai']} AI System Status",
            color=COLORS['info']
        )

        # Check AI client status
        if self.model:
            embed.add_field(
                name="🟢 AI Client",
                value="Connected and ready",
                inline=True
            )
        else:
            embed.add_field(
                name="🔴 AI Client",
                value="Not connected",
                inline=True
            )

        # Check configuration
        config = get_server_config(interaction.guild.id)
        ai_channels = config.get('ai_channels', [])

        if ai_channels:
            channel_mentions = [f"<#{ch}>" for ch in ai_channels]
            embed.add_field(
                name="📝 AI Channels",
                value=", ".join(channel_mentions),
                inline=True
            )
        else:
            embed.add_field(
                name="📝 AI Channels",
                value="All channels (when mentioned)",
                inline=True
            )

        # Conversation stats
        user_history = self.get_conversation_history(interaction.user.id, interaction.guild.id)
        embed.add_field(
            name="💬 Your Chat History",
            value=f"{len(user_history)} messages",
            inline=True
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(AIChatbotCog(bot))