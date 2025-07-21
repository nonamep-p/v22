import discord
from discord.ext import commands
import os
import logging
import asyncio
from datetime import datetime
import threading
from web_server import run_web_server
from config import COLORS, EMOJIS, get_server_config
from utils.database import init_database
from cogs.help import HelpView

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(
    command_prefix='$',
    intents=intents,
    help_command=None,  # We'll implement our own
    case_insensitive=True
)

@bot.event
async def on_ready():
    """Called when the bot is ready."""
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Add persistent views
    bot.add_view(HelpView())
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Game(name="Epic RPG Adventures | $help")
    )

@bot.event
async def on_guild_join(guild):
    """Called when the bot joins a new guild."""
    logger.info(f"Joined new guild: {guild.name} ({guild.id})")
    
    # Try to send welcome message
    try:
        # Find a suitable channel to send welcome message
        channel = None
        
        # Try to find general or welcome channel
        for ch in guild.text_channels:
            if ch.name.lower() in ['general', 'welcome', 'bot-commands']:
                if ch.permissions_for(guild.me).send_messages:
                    channel = ch
                    break
        
        # If no suitable channel found, try the first channel we can send to
        if not channel:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    channel = ch
                    break
        
        if channel:
            embed = discord.Embed(
                title="🎉 Thanks for adding Epic RPG Helper!",
                description=(
                    "I'm your comprehensive RPG companion bot!\n\n"
                    "**🎯 Main Features:**\n"
                    "• Complete RPG system with adventures, dungeons, and combat\n"
                    "• Economy system with work, shop, and trading\n"
                    "• AI chatbot powered by Google Gemini\n"
                    "• Moderation tools and utilities\n"
                    "• Admin controls and server management\n\n"
                    "**🚀 Getting Started:**\n"
                    "Use `$help` for the interactive help menu\n"
                    "Use `$start` to begin your RPG adventure\n"
                    "Use `$config` to configure server settings\n\n"
                    "Need help? Join our support server or use `$support`"
                ),
                color=COLORS['success']
            )
            embed.set_thumbnail(url=bot.user.display_avatar.url)
            embed.set_footer(text="Epic RPG Helper | Ready to adventure!")
            
            await channel.send(embed=embed)
    except Exception as e:
        logger.error(f"Error sending welcome message to {guild.name}: {e}")

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for commands."""
    if isinstance(error, commands.CommandNotFound):
        # Don't respond to unknown commands
        return
    
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Missing Permissions",
            description="You don't have the required permissions to use this command.",
            color=COLORS['error']
        )
        await ctx.send(embed=embed)
    
    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(
            title="❌ Bot Missing Permissions",
            description="I don't have the required permissions to execute this command.",
            color=COLORS['error']
        )
        await ctx.send(embed=embed)
    
    elif isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(
            title="⏰ Command on Cooldown",
            description=f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
            color=COLORS['warning']
        )
        await ctx.send(embed=embed)
    
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="❌ Missing Required Argument",
            description=f"Missing required argument: `{error.param.name}`\n\nUse `$help {ctx.command.name}` for more info.",
            color=COLORS['error']
        )
        await ctx.send(embed=embed)
    
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            title="❌ Invalid Argument",
            description=f"Invalid argument provided. Use `$help {ctx.command.name}` for correct usage.",
            color=COLORS['error']
        )
        await ctx.send(embed=embed)
    
    else:
        logger.error(f"Unhandled error in command {ctx.command}: {error}")
        embed = discord.Embed(
            title="❌ An Error Occurred",
            description="An unexpected error occurred. Please try again later.",
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

@bot.event
async def on_error(event, *args, **kwargs):
    """Global error handler for events."""
    logger.error(f"Error in event {event}: {args}")

async def load_cogs():
    """Load all cogs."""
    cogs = [
        'cogs.help',
        'cogs.ai_chatbot',
        'cogs.economy',
        'cogs.moderation',
        'cogs.rpg_games',
        'cogs.admin'
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"Loaded cog: {cog}")
        except Exception as e:
            logger.error(f"Failed to load cog {cog}: {e}")

async def main():
    """Main function to run the bot."""
    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Load cogs
    await load_cogs()
    
    # Get token from environment
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        return
    
    # Run the bot
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
