import discord
from discord.ext import commands
import asyncio
import logging
import psutil
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from config import COLORS, EMOJIS, user_has_permission, is_module_enabled, get_server_config, update_server_config, DEFAULT_SERVER_CONFIG
from utils.helpers import create_embed, format_number, format_duration
from utils.database import get_global_stats, backup_database, cleanup_old_data, get_leaderboard
from replit import db

logger = logging.getLogger(__name__)

class ConfigView(discord.ui.View):
    """Interactive view for server configuration."""
    
    def __init__(self, guild_id: int, config: Dict[str, Any]):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.config = config
        
    @discord.ui.select(
        placeholder="Select a module to toggle...",
        options=[
            discord.SelectOption(label="RPG Games", value="rpg_games", emoji="🎮"),
            discord.SelectOption(label="Economy", value="economy", emoji="💰"),
            discord.SelectOption(label="AI Chatbot", value="ai_chatbot", emoji="🤖"),
            discord.SelectOption(label="Moderation", value="moderation", emoji="🔨"),
            discord.SelectOption(label="Admin", value="admin", emoji="👑")
        ]
    )
    async def module_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Toggle module on/off."""
        if not user_has_permission(interaction.user, 'admin'):
            await interaction.response.send_message("❌ You need admin permissions!", ephemeral=True)
            return
            
        module = select.values[0]
        current_status = self.config['enabled_modules'].get(module, True)
        self.config['enabled_modules'][module] = not current_status
        
        # Update database
        update_server_config(self.guild_id, self.config)
        
        status = "enabled" if not current_status else "disabled"
        await interaction.response.send_message(f"✅ {module.replace('_', ' ').title()} module {status}!", ephemeral=True)
        
    @discord.ui.button(label="Configure AI", style=discord.ButtonStyle.secondary, emoji="🤖")
    async def configure_ai(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Configure AI settings."""
        if not user_has_permission(interaction.user, 'admin'):
            await interaction.response.send_message("❌ You need admin permissions!", ephemeral=True)
            return
            
        embed = discord.Embed(
            title="🤖 AI Configuration",
            description="Use `$ai_persona <prompt>` to set a custom AI personality.\n"
                       "Use `$config ai_channels` to configure AI channels.",
            color=COLORS['info']
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @discord.ui.button(label="Auto-Mod Settings", style=discord.ButtonStyle.secondary, emoji="🛡️")
    async def automod_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Configure auto-moderation."""
        if not user_has_permission(interaction.user, 'admin'):
            await interaction.response.send_message("❌ You need admin permissions!", ephemeral=True)
            return
            
        automod = self.config.get('auto_moderation', {})
        
        embed = discord.Embed(
            title="🛡️ Auto-Moderation Settings",
            description=f"**Enabled:** {'✅' if automod.get('enabled', False) else '❌'}\n"
                       f"**Spam Detection:** {'✅' if automod.get('spam_detection', True) else '❌'}\n"
                       f"**Content Filter:** {'✅' if automod.get('inappropriate_content', True) else '❌'}\n"
                       f"**Max Warnings:** {automod.get('max_warnings', 3)}",
            color=COLORS['warning']
        )
        embed.add_field(
            name="Commands",
            value="`$automod` - Full auto-moderation configuration\n"
                  "`$config automod_toggle` - Toggle auto-mod on/off",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class AdminCog(commands.Cog):
    """Administrative commands and server management."""
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.now()
        
    @commands.command(name='config', help='Configure server settings')
    @commands.has_permissions(manage_guild=True)
    async def server_config(self, ctx, setting: str = None, *, value: str = None):
        """Configure server settings."""
        if not is_module_enabled("admin", ctx.guild.id):
            return
            
        config = get_server_config(ctx.guild.id)
        
        if setting is None:
            # Show current configuration with interactive view
            embed = discord.Embed(
                title="⚙️ Server Configuration",
                description=f"Current settings for **{ctx.guild.name}**",
                color=COLORS['info']
            )
            
            # Enabled modules
            modules = config.get('enabled_modules', {})
            module_status = []
            for module, enabled in modules.items():
                status = "✅" if enabled else "❌"
                module_status.append(f"{status} {module.replace('_', ' ').title()}")
            
            embed.add_field(
                name="📦 Enabled Modules",
                value="\n".join(module_status),
                inline=True
            )
            
            # Channel restrictions
            allowed_channels = config.get('allowed_channels', [])
            ai_channels = config.get('ai_enabled_channels', [])
            
            channel_info = f"**Command Channels:** {'All' if not allowed_channels else f'{len(allowed_channels)} restricted'}\n"
            channel_info += f"**AI Channels:** {'All' if not ai_channels else f'{len(ai_channels)} restricted'}"
            
            embed.add_field(
                name="🔒 Channel Settings",
                value=channel_info,
                inline=True
            )
            
            # Auto-moderation
            automod = config.get('auto_moderation', {})
            embed.add_field(
                name="🛡️ Auto-Moderation",
                value=f"**Enabled:** {'✅' if automod.get('enabled', False) else '❌'}\n"
                      f"**Max Warnings:** {automod.get('max_warnings', 3)}",
                inline=True
            )
            
            embed.set_footer(text="Use the buttons below to configure settings")
            
            view = ConfigView(ctx.guild.id, config)
            await ctx.send(embed=embed, view=view)
            return
            
        # Handle specific settings
        if setting == "prefix":
            if value is None:
                await ctx.send(f"Current prefix: `{config.get('prefix', '$')}`")
                return
                
            config['prefix'] = value
            update_server_config(ctx.guild.id, config)
            
            embed = create_embed(
                "✅ Prefix Updated",
                f"Command prefix changed to: `{value}`",
                COLORS['success']
            )
            await ctx.send(embed=embed)
            
        elif setting == "currency":
            if value is None:
                await ctx.send(f"Current currency name: `{config.get('currency_name', 'coins')}`")
                return
                
            config['currency_name'] = value
            update_server_config(ctx.guild.id, config)
            
            embed = create_embed(
                "✅ Currency Updated",
                f"Currency name changed to: `{value}`",
                COLORS['success']
            )
            await ctx.send(embed=embed)
            
        elif setting == "ai_channels":
            if value == "reset":
                config['ai_enabled_channels'] = []
                update_server_config(ctx.guild.id, config)
                await ctx.send("✅ AI enabled in all channels.")
                return
                
            if value == "current":
                current_channels = config.get('ai_enabled_channels', [])
                if ctx.channel.id in current_channels:
                    current_channels.remove(ctx.channel.id)
                    action = "removed from"
                else:
                    current_channels.append(ctx.channel.id)
                    action = "added to"
                    
                config['ai_enabled_channels'] = current_channels
                update_server_config(ctx.guild.id, config)
                
                await ctx.send(f"✅ {ctx.channel.mention} {action} AI-enabled channels.")
                return
                
            await ctx.send("Usage: `$config ai_channels current` (toggle this channel) or `$config ai_channels reset` (enable all)")
            
        elif setting == "automod_toggle":
            automod = config.get('auto_moderation', {})
            automod['enabled'] = not automod.get('enabled', False)
            config['auto_moderation'] = automod
            update_server_config(ctx.guild.id, config)
            
            status = "enabled" if automod['enabled'] else "disabled"
            embed = create_embed(
                "✅ Auto-Moderation Updated",
                f"Auto-moderation has been {status}.",
                COLORS['success']
            )
            await ctx.send(embed=embed)
            
        else:
            embed = create_embed(
                "❌ Invalid Setting",
                "Available settings: `prefix`, `currency`, `ai_channels`, `automod_toggle`",
                COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='stats', help='View bot statistics')
    @commands.has_permissions(manage_guild=True)
    async def stats_command(self, ctx):
        """View comprehensive bot statistics."""
        if not is_module_enabled("admin", ctx.guild.id):
            return
            
        try:
            # Get system stats
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            cpu_usage = process.cpu_percent()
            
            # Get bot stats
            uptime = datetime.now() - self.start_time
            guild_count = len(self.bot.guilds)
            user_count = len(self.bot.users)
            
            # Get database stats
            global_stats = get_global_stats()
            
            embed = discord.Embed(
                title="📊 Bot Statistics",
                color=COLORS['info']
            )
            
            # System Stats
            embed.add_field(
                name="🖥️ System",
                value=f"**Memory:** {memory_usage:.1f} MB\n"
                      f"**CPU:** {cpu_usage:.1f}%\n"
                      f"**Uptime:** {format_duration(int(uptime.total_seconds()))}",
                inline=True
            )
            
            # Bot Stats
            embed.add_field(
                name="🤖 Bot",
                value=f"**Guilds:** {guild_count}\n"
                      f"**Users:** {user_count}\n"
                      f"**Latency:** {round(self.bot.latency * 1000)}ms",
                inline=True
            )
            
            # Database Stats
            embed.add_field(
                name="💾 Database",
                value=f"**Total Users:** {global_stats.get('total_users', 0)}\n"
                      f"**Total Commands:** {global_stats.get('total_commands', 0)}\n"
                      f"**Total Guilds:** {global_stats.get('total_guilds', 0)}",
                inline=True
            )
            
            # Guild-specific stats
            try:
                users_db = db.get('users', {})
                guild_users = 0
                for user_id, user_data in users_db.items():
                    # Count users who have been active in this guild
                    guild_users += 1  # Simplified for now
                    
                embed.add_field(
                    name=f"🏰 {ctx.guild.name}",
                    value=f"**Active Users:** {guild_users}\n"
                          f"**Channels:** {len(ctx.guild.channels)}\n"
                          f"**Roles:** {len(ctx.guild.roles)}",
                    inline=True
                )
            except Exception as e:
                logger.error(f"Error getting guild stats: {e}")
                
            embed.timestamp = datetime.utcnow()
            embed.set_footer(text="Statistics updated")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in stats command: {e}")
            embed = create_embed(
                "❌ Error",
                "Failed to retrieve statistics.",
                COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='backup', help='Create database backup')
    @commands.has_permissions(administrator=True)
    async def create_backup(self, ctx):
        """Create a database backup."""
        if not is_module_enabled("admin", ctx.guild.id):
            return
            
        try:
            if backup_database():
                embed = create_embed(
                    "✅ Backup Created",
                    "Database backup has been created successfully.",
                    COLORS['success']
                )
            else:
                embed = create_embed(
                    "❌ Backup Failed",
                    "Failed to create database backup.",
                    COLORS['error']
                )
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in backup command: {e}")
            embed = create_embed(
                "❌ Error",
                "An error occurred while creating backup.",
                COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='cleanup', help='Clean up old user data')
    @commands.has_permissions(administrator=True)
    async def cleanup_data(self, ctx, days: int = 30):
        """Clean up old inactive user data."""
        if not is_module_enabled("admin", ctx.guild.id):
            return
            
        if days < 7:
            embed = create_embed(
                "❌ Invalid Days",
                "Minimum cleanup period is 7 days.",
                COLORS['error']
            )
            await ctx.send(embed=embed)
            return
            
        try:
            # Confirmation
            embed = discord.Embed(
                title="⚠️ Data Cleanup Confirmation",
                description=f"This will remove user data for accounts inactive for {days} days.\n"
                           f"This action cannot be undone!\n\n"
                           f"React with ✅ to confirm or ❌ to cancel.",
                color=COLORS['warning']
            )
            
            msg = await ctx.send(embed=embed)
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id
                
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                if str(reaction.emoji) == "✅":
                    if cleanup_old_data(days):
                        embed = create_embed(
                            "✅ Cleanup Complete",
                            f"Cleaned up inactive user data older than {days} days.",
                            COLORS['success']
                        )
                    else:
                        embed = create_embed(
                            "❌ Cleanup Failed",
                            "Failed to clean up user data.",
                            COLORS['error']
                        )
                else:
                    embed = create_embed(
                        "❌ Cleanup Cancelled",
                        "Data cleanup has been cancelled.",
                        COLORS['warning']
                    )
                    
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                
            except asyncio.TimeoutError:
                embed = create_embed(
                    "⏰ Timeout",
                    "Cleanup confirmation timed out.",
                    COLORS['warning']
                )
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                
        except Exception as e:
            logger.error(f"Error in cleanup command: {e}")
            embed = create_embed(
                "❌ Error",
                "An error occurred during cleanup.",
                COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='announce', help='Send announcement to all servers')
    @commands.is_owner()
    async def announce(self, ctx, *, message: str):
        """Send announcement to all servers (bot owner only)."""
        try:
            embed = discord.Embed(
                title="📢 Bot Announcement",
                description=message,
                color=COLORS['info']
            )
            embed.set_footer(text=f"Announcement from {ctx.author}")
            embed.timestamp = datetime.utcnow()
            
            sent_count = 0
            failed_count = 0
            
            for guild in self.bot.guilds:
                try:
                    # Find suitable channel
                    channel = None
                    
                    # Try to find announcement or general channel
                    for ch in guild.text_channels:
                        if ch.name.lower() in ['announcements', 'general', 'bot-updates']:
                            if ch.permissions_for(guild.me).send_messages:
                                channel = ch
                                break
                                
                    # If no suitable channel found, try first available
                    if not channel:
                        for ch in guild.text_channels:
                            if ch.permissions_for(guild.me).send_messages:
                                channel = ch
                                break
                                
                    if channel:
                        await channel.send(embed=embed)
                        sent_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to send announcement to {guild.name}: {e}")
                    failed_count += 1
                    
            result_embed = create_embed(
                "📢 Announcement Sent",
                f"Sent to {sent_count} servers, {failed_count} failed.",
                COLORS['success'] if failed_count == 0 else COLORS['warning']
            )
            
            await ctx.send(embed=result_embed)
            
        except Exception as e:
            logger.error(f"Error in announce command: {e}")
            embed = create_embed(
                "❌ Error",
                "Failed to send announcement.",
                COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='maintenance', help='Toggle maintenance mode')
    @commands.is_owner()
    async def maintenance_mode(self, ctx, mode: str = None):
        """Toggle maintenance mode for the bot."""
        try:
            current_mode = db.get('maintenance_mode', False)
            
            if mode is None:
                status = "enabled" if current_mode else "disabled"
                await ctx.send(f"Maintenance mode is currently **{status}**.")
                return
                
            if mode.lower() in ['on', 'enable', 'true']:
                db['maintenance_mode'] = True
                embed = create_embed(
                    "🔧 Maintenance Mode Enabled",
                    "Bot is now in maintenance mode. Most commands will be disabled.",
                    COLORS['warning']
                )
            elif mode.lower() in ['off', 'disable', 'false']:
                db['maintenance_mode'] = False
                embed = create_embed(
                    "✅ Maintenance Mode Disabled",
                    "Bot is now operational. All commands are available.",
                    COLORS['success']
                )
            else:
                embed = create_embed(
                    "❌ Invalid Mode",
                    "Valid modes: `on`, `off`, `enable`, `disable`",
                    COLORS['error']
                )
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in maintenance command: {e}")
            embed = create_embed(
                "❌ Error",
                "Failed to toggle maintenance mode.",
                COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='reload', help='Reload bot cogs')
    @commands.is_owner()
    async def reload_cogs(self, ctx, cog_name: str = None):
        """Reload bot cogs."""
        try:
            if cog_name:
                # Reload specific cog
                try:
                    await self.bot.reload_extension(f'cogs.{cog_name}')
                    embed = create_embed(
                        "✅ Cog Reloaded",
                        f"Successfully reloaded `{cog_name}` cog.",
                        COLORS['success']
                    )
                except Exception as e:
                    embed = create_embed(
                        "❌ Reload Failed",
                        f"Failed to reload `{cog_name}`: {str(e)}",
                        COLORS['error']
                    )
            else:
                # Reload all cogs
                cogs = ['help', 'ai_chatbot', 'economy', 'moderation', 'rpg_games', 'admin']
                reloaded = []
                failed = []
                
                for cog in cogs:
                    try:
                        await self.bot.reload_extension(f'cogs.{cog}')
                        reloaded.append(cog)
                    except Exception as e:
                        failed.append(f"{cog}: {str(e)}")
                        
                embed = discord.Embed(
                    title="🔄 Cog Reload Results",
                    color=COLORS['success'] if not failed else COLORS['warning']
                )
                
                if reloaded:
                    embed.add_field(
                        name="✅ Successfully Reloaded",
                        value="\n".join(reloaded),
                        inline=False
                    )
                    
                if failed:
                    embed.add_field(
                        name="❌ Failed to Reload",
                        value="\n".join(failed),
                        inline=False
                    )
                    
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in reload command: {e}")
            embed = create_embed(
                "❌ Error",
                "Failed to reload cogs.",
                COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='eval', help='Evaluate Python code (owner only)')
    @commands.is_owner()
    async def evaluate_code(self, ctx, *, code: str):
        """Evaluate Python code (dangerous - owner only)."""
        try:
            # Remove code blocks if present
            if code.startswith('```python'):
                code = code[9:-3]
            elif code.startswith('```'):
                code = code[3:-3]
                
            # Prepare environment
            env = {
                'bot': self.bot,
                'ctx': ctx,
                'guild': ctx.guild,
                'channel': ctx.channel,
                'author': ctx.author,
                'db': db,
                'discord': discord,
                'commands': commands
            }
            
            # Execute code
            result = eval(code, env)
            
            # Handle async results
            if asyncio.iscoroutine(result):
                result = await result
                
            # Format result
            if result is None:
                output = "None"
            else:
                output = str(result)
                
            # Truncate if too long
            if len(output) > 1900:
                output = output[:1900] + "..."
                
            embed = discord.Embed(
                title="🐍 Code Evaluation",
                description=f"```python\n{code}```",
                color=COLORS['success']
            )
            embed.add_field(
                name="Output",
                value=f"```python\n{output}```",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Evaluation Error",
                description=f"```python\n{code}```",
                color=COLORS['error']
            )
            embed.add_field(
                name="Error",
                value=f"```python\n{str(e)}```",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
    @commands.command(name='shutdown', help='Shutdown the bot (owner only)')
    @commands.is_owner()
    async def shutdown_bot(self, ctx):
        """Shutdown the bot."""
        try:
            embed = create_embed(
                "⚠️ Shutdown Confirmation",
                "Are you sure you want to shutdown the bot?\n"
                "React with ✅ to confirm or ❌ to cancel.",
                COLORS['warning']
            )
            
            msg = await ctx.send(embed=embed)
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id
                
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                if str(reaction.emoji) == "✅":
                    embed = create_embed(
                        "🔌 Shutting Down",
                        "Bot is shutting down...",
                        COLORS['error']
                    )
                    await msg.edit(embed=embed)
                    await self.bot.close()
                else:
                    embed = create_embed(
                        "❌ Shutdown Cancelled",
                        "Bot shutdown has been cancelled.",
                        COLORS['success']
                    )
                    await msg.edit(embed=embed)
                    
                await msg.clear_reactions()
                
            except asyncio.TimeoutError:
                embed = create_embed(
                    "⏰ Timeout",
                    "Shutdown confirmation timed out.",
                    COLORS['warning']
                )
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                
        except Exception as e:
            logger.error(f"Error in shutdown command: {e}")
            embed = create_embed(
                "❌ Error",
                "Failed to shutdown bot.",
                COLORS['error']
            )
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Track command usage."""
        try:
            # Update global stats
            from utils.database import update_global_stats
            update_global_stats('total_commands', 1)
        except Exception as e:
            logger.error(f"Error tracking command usage: {e}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Handle bot joining new guild."""
        try:
            # Update global stats
            from utils.database import update_global_stats
            update_global_stats('total_guilds', 1)
            
            logger.info(f"Bot joined new guild: {guild.name} ({guild.id})")
        except Exception as e:
            logger.error(f"Error handling guild join: {e}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Handle bot leaving guild."""
        try:
            # Update global stats
            from utils.database import update_global_stats
            update_global_stats('total_guilds', -1)
            
            logger.info(f"Bot left guild: {guild.name} ({guild.id})")
        except Exception as e:
            logger.error(f"Error handling guild remove: {e}")

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
