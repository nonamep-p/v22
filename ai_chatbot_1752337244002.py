import discord
from discord.ext import commands
import os
import asyncio
import logging
from datetime import datetime, timedelta
from replit import db
from config import is_ai_enabled_in_channel, is_channel_allowed, is_module_enabled, get_server_config
from utils.helpers import create_embed
from config import COLORS
import json

logger = logging.getLogger(__name__)

class AIChatbotCog(commands.Cog):
    """AI Chatbot functionality using Google Gemini."""

    def __init__(self, bot):
        self.bot = bot
        self.conversation_history = {}  # guild_id -> channel_id -> messages
        self.active_conversations = {}  # guild_id -> channel_id -> last_message_time
        self.conversation_timeout = 300  # 5 minutes timeout
        self.user_conversation_context = {}  # user_id -> last_context
        self.setup_gemini()

    def setup_gemini(self):
        """Setup Google Gemini API."""
        try:
            import google.generativeai as genai
            
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logger.error("GEMINI_API_KEY not found in environment variables!")
                self.gemini_available = False
                return

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.gemini_available = True
            logger.info("Google Gemini API initialized successfully")
        except ImportError:
            logger.error("google-generativeai package not installed!")
            self.gemini_available = False
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {e}")
            self.gemini_available = False

    def get_conversation_key(self, guild_id, channel_id):
        """Get unique conversation key."""
        return f"{guild_id}_{channel_id}"

    def add_to_conversation_history(self, guild_id, channel_id, role, content, user_id=None):
        """Add message to conversation history."""
        key = self.get_conversation_key(guild_id, channel_id)

        if key not in self.conversation_history:
            self.conversation_history[key] = []

        # Add message to history
        message_data = {
            'role': role,
            'content': content,
            'timestamp': datetime.now(),
            'user_id': str(user_id) if user_id else None
        }

        self.conversation_history[key].append(message_data)

        # Keep only last 20 messages for better memory
        if len(self.conversation_history[key]) > 20:
            self.conversation_history[key] = self.conversation_history[key][-20:]

        # Save to database for persistence
        self.save_conversation_to_db(key)

    def save_conversation_to_db(self, conversation_key):
        """Save conversation to database."""
        try:
            # Convert datetime objects to strings for JSON serialization
            conversation_data = []
            for msg in self.conversation_history.get(conversation_key, []):
                msg_copy = msg.copy()
                msg_copy['timestamp'] = msg_copy['timestamp'].isoformat()
                conversation_data.append(msg_copy)
            
            db[f"conversation_{conversation_key}"] = conversation_data
        except Exception as e:
            logger.error(f"Error saving conversation to DB: {e}")

    def load_conversation_from_db(self, conversation_key):
        """Load conversation from database."""
        try:
            conversation_data = db.get(f"conversation_{conversation_key}", [])
            
            # Convert timestamp strings back to datetime objects
            for msg in conversation_data:
                msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
            
            self.conversation_history[conversation_key] = conversation_data
        except Exception as e:
            logger.error(f"Error loading conversation from DB: {e}")

    def build_conversation_context(self, guild_id, channel_id, user_id=None):
        """Build conversation context for Gemini."""
        key = self.get_conversation_key(guild_id, channel_id)

        # Load from database if not in memory
        if key not in self.conversation_history:
            self.load_conversation_from_db(key)

        if key not in self.conversation_history:
            return []

        # Filter out old messages (older than 2 hours for better memory)
        cutoff_time = datetime.now() - timedelta(hours=2)
        recent_messages = [
            msg for msg in self.conversation_history[key]
            if msg['timestamp'] > cutoff_time
        ]

        # Update history with filtered messages
        self.conversation_history[key] = recent_messages

        # Build context for Gemini - focus on recent conversation
        context = []
        for msg in recent_messages[-10:]:  # Last 10 messages
            if msg['role'] == 'user':
                context.append(f"User: {msg['content']}")
            else:
                context.append(f"Assistant: {msg['content']}")

        return context

    def should_respond_to_message(self, message):
        """Check if bot should respond to this message."""
        # Don't respond to bots or own messages
        if message.author.bot:
            return False

        # Don't respond to commands
        if message.content.startswith(('$', '!', '?', '.', '/')):
            return False

        # Check if bot is mentioned
        if self.bot.user.mentioned_in(message):
            return True

        # Check if replying to bot's message
        if (message.reference and 
            message.reference.resolved and 
            message.reference.resolved.author == self.bot.user):
            return True

        # Check for direct messages
        if isinstance(message.channel, discord.DMChannel):
            return True

        # Check for active conversation continuation
        key = self.get_conversation_key(message.guild.id, message.channel.id)
        current_time = datetime.now()

        # If there's an active conversation
        if key in self.active_conversations:
            last_message_time = self.active_conversations[key]
            time_diff = (current_time - last_message_time).total_seconds()

            # If within timeout and user was recently chatting with bot
            if time_diff <= self.conversation_timeout:
                if key in self.conversation_history:
                    recent_history = self.conversation_history[key]
                    user_id = str(message.author.id)

                    # Check if user was in recent conversation (last 5 messages)
                    for msg in recent_history[-5:]:
                        if msg.get('user_id') == user_id:
                            return True
            else:
                # Conversation timed out, remove from active conversations
                del self.active_conversations[key]

        return False

    async def generate_ai_response(self, message_content, guild_id, channel_id, user_id=None):
        """Generate AI response using Gemini."""
        if not self.gemini_available:
            return "I'm sorry, but my AI capabilities are currently unavailable. Please check if the GEMINI_API_KEY is properly configured."

        try:
            # Get custom prompt or use default
            server_config = get_server_config(guild_id)
            custom_prompt = server_config.get('ai_custom_prompt', '')

            # Create system prompt
            if custom_prompt:
                system_prompt = f"""{custom_prompt}

Important: Keep responses SHORT (1-2 sentences max), casual, and engaging. Don't be overly verbose."""
            else:
                system_prompt = """You are Epic-Maki, a friendly Discord bot for an RPG server. Be conversational and helpful.

Key traits:
- Keep responses SHORT (1-2 sentences max)
- Be casual, warm, and engaging
- Ask brief follow-up questions occasionally
- Stay positive and encouraging
- Chat naturally about any topic
- Reference RPG/gaming themes when appropriate
- Remember context from recent messages

Goal: Be a fun, memorable chat companion without being wordy."""

            # Build conversation context
            context = self.build_conversation_context(guild_id, channel_id, user_id)

            # Create full prompt with context
            if context:
                context_text = "\n".join(context[-5:])  # Use last 5 messages
                full_prompt = f"{system_prompt}\n\nRecent conversation:\n{context_text}\n\nUser: {message_content}"
            else:
                full_prompt = f"{system_prompt}\n\nUser: {message_content}"

            # Generate response
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.model.generate_content(full_prompt)
            )

            return response.text

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I'm having trouble processing that right now. Please try again later!"

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages and respond with AI when appropriate."""
        # Skip if not in guild (unless DM)
        if not message.guild and not isinstance(message.channel, discord.DMChannel):
            return

        # For DMs, always respond
        if isinstance(message.channel, discord.DMChannel):
            if message.author.bot:
                return
            
            # Generate response for DM
            async with message.channel.typing():
                response = await self.generate_ai_response(
                    message.content, 
                    0,  # No guild for DMs
                    message.channel.id,
                    message.author.id
                )
                await message.channel.send(response)
            return

        # Check if module is enabled
        if not is_module_enabled("ai_chatbot", message.guild.id):
            return

        # Check if channel is allowed
        if not is_channel_allowed(message.channel.id, message.guild.id):
            return

        # Check if AI is enabled in this channel
        if not is_ai_enabled_in_channel(message.channel.id, message.guild.id):
            return

        # Check if we should respond
        if not self.should_respond_to_message(message):
            return

        # Clean the message content for AI processing
        clean_content = message.content

        # Remove bot mentions from the message
        if self.bot.user.mentioned_in(message):
            clean_content = message.content.replace(f'<@{self.bot.user.id}>', '').replace(f'<@!{self.bot.user.id}>', '').strip()

        # Remove other user mentions to avoid confusion
        import re
        clean_content = re.sub(r'<@!?\d+>', '', clean_content).strip()

        # If message is empty after cleaning, use a default greeting
        if not clean_content:
            clean_content = "Hello!"

        # Add user message to history
        self.add_to_conversation_history(
            message.guild.id, 
            message.channel.id, 
            'user', 
            clean_content,
            message.author.id
        )

        # Update active conversation timestamp
        key = self.get_conversation_key(message.guild.id, message.channel.id)
        self.active_conversations[key] = datetime.now()

        # Show typing indicator
        async with message.channel.typing():
            # Generate response
            response = await self.generate_ai_response(
                clean_content, 
                message.guild.id, 
                message.channel.id,
                message.author.id
            )

            # Split response if too long
            if len(response) > 2000:
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                for chunk in chunks:
                    await message.channel.send(chunk)
                # Add last chunk to history
                self.add_to_conversation_history(
                    message.guild.id, 
                    message.channel.id, 
                    'assistant', 
                    chunks[-1]
                )
            else:
                await message.channel.send(response)
                # Add response to history
                self.add_to_conversation_history(
                    message.guild.id, 
                    message.channel.id, 
                    'assistant', 
                    response
                )

    @commands.command(name='chat', help='Start a conversation with the AI')
    async def chat_command(self, ctx, *, message: str):
        """Direct chat command for AI interaction."""
        if not is_module_enabled("ai_chatbot", ctx.guild.id):
            return
            
        if not self.gemini_available:
            embed = discord.Embed(
                title="❌ AI Unavailable",
                description="AI features are currently unavailable. Please ask an admin to configure the GEMINI_API_KEY.",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            return

        # Add user message to history
        self.add_to_conversation_history(
            ctx.guild.id, 
            ctx.channel.id, 
            'user', 
            message,
            ctx.author.id
        )

        # Show typing indicator
        async with ctx.typing():
            # Generate response
            response = await self.generate_ai_response(
                message, 
                ctx.guild.id, 
                ctx.channel.id,
                ctx.author.id
            )

            # Create embed for response
            embed = discord.Embed(
                title="🤖 AI Response",
                description=response,
                color=COLORS['info']
            )
            embed.set_footer(text=f"Requested by {ctx.author}")

            await ctx.send(embed=embed)

            # Add response to history
            self.add_to_conversation_history(
                ctx.guild.id, 
                ctx.channel.id, 
                'assistant', 
                response
            )

    @commands.command(name='clear_chat', help='Clear AI conversation history')
    async def clear_chat_history(self, ctx):
        """Clear conversation history for current channel."""
        if not is_module_enabled("ai_chatbot", ctx.guild.id):
            return
            
        key = self.get_conversation_key(ctx.guild.id, ctx.channel.id)

        if key in self.conversation_history:
            del self.conversation_history[key]

        if key in self.active_conversations:
            del self.active_conversations[key]

        # Clear from database
        try:
            if f"conversation_{key}" in db:
                del db[f"conversation_{key}"]
        except Exception as e:
            logger.error(f"Error clearing conversation from DB: {e}")

        embed = discord.Embed(
            title="✅ Chat History Cleared",
            description="AI conversation history has been cleared for this channel.",
            color=COLORS['success']
        )
        await ctx.send(embed=embed)

    @commands.command(name='ai_status', help='Check AI system status')
    async def ai_status(self, ctx):
        """Check AI system status."""
        if not is_module_enabled("ai_chatbot", ctx.guild.id):
            return
            
        embed = discord.Embed(
            title="🤖 AI System Status",
            color=COLORS['info']
        )
        
        # Check API status
        if self.gemini_available:
            embed.add_field(
                name="🟢 API Status",
                value="Google Gemini API is connected and ready",
                inline=False
            )
        else:
            embed.add_field(
                name="🔴 API Status",
                value="Google Gemini API is not available",
                inline=False
            )
        
        # Show conversation stats
        key = self.get_conversation_key(ctx.guild.id, ctx.channel.id)
        conversation_count = len(self.conversation_history.get(key, []))
        
        embed.add_field(
            name="💬 Conversation Stats",
            value=f"Messages in history: {conversation_count}\n"
                  f"Active conversations: {len(self.active_conversations)}",
            inline=False
        )
        
        # Show AI settings
        server_config = get_server_config(ctx.guild.id)
        custom_prompt = server_config.get('ai_custom_prompt', 'None')
        
        embed.add_field(
            name="⚙️ Settings",
            value=f"Custom prompt: {'Set' if custom_prompt else 'Default'}\n"
                  f"Timeout: {self.conversation_timeout} seconds",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='ai_persona', help='Set AI personality/prompt for this server')
    @commands.has_permissions(manage_guild=True)
    async def set_ai_persona(self, ctx, *, prompt: str = None):
        """Set custom AI personality for the server."""
        if not is_module_enabled("ai_chatbot", ctx.guild.id):
            return
            
        server_config = get_server_config(ctx.guild.id)
        
        if prompt is None:
            # Show current prompt
            current_prompt = server_config.get('ai_custom_prompt', 'None set')
            embed = discord.Embed(
                title="🎭 Current AI Persona",
                description=f"```{current_prompt}```" if current_prompt != 'None set' else "No custom persona set.",
                color=COLORS['info']
            )
            await ctx.send(embed=embed)
            return
        
        # Validate prompt length
        if len(prompt) > 500:
            embed = discord.Embed(
                title="❌ Prompt Too Long",
                description="AI persona must be 500 characters or less.",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            return
        
        # Update server config
        server_config['ai_custom_prompt'] = prompt
        from config import update_server_config
        
        if update_server_config(ctx.guild.id, server_config):
            embed = discord.Embed(
                title="✅ AI Persona Updated",
                description=f"New AI persona set:\n```{prompt}```",
                color=COLORS['success']
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to update AI persona. Please try again.",
                color=COLORS['error']
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AIChatbotCog(bot))
