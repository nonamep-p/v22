import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import asyncio
import re
import logging
from typing import Optional, Dict, List, Any

from config import COLORS, EMOJIS, user_has_permission, is_module_enabled, get_server_config, update_server_config
from utils.helpers import create_embed, format_duration
from utils.database import get_user_data, update_user_data
from replit import db

logger = logging.getLogger(__name__)

class ModerationCog(commands.Cog):
    """Enhanced moderation commands with auto-moderation."""
    
    def __init__(self, bot):
        self.bot = bot
        self.muted_users = {}  # Simple in-memory storage for muted users
        self.spam_tracker = {}  # Track spam patterns
        self.warned_users = {}  # Track recently warned users
        
        # Auto-moderation patterns
        self.spam_patterns = [
            r'(.)\1{4,}',  # Repeated characters
            r'[A-Z]{5,}',  # Excessive caps
            r'(.{1,10})\1{3,}',  # Repeated phrases
        ]
        
        # Basic inappropriate words filter (extend as needed)
        self.inappropriate_words = [
            'spam', 'test_inappropriate'  # Add your filter words here
        ]
        
    def can_moderate(self, user: discord.Member, target: discord.Member) -> bool:
        """Check if user can moderate target."""
        if user == user.guild.owner:
            return True
            
        if target == user.guild.owner:
            return False
            
        if user.top_role <= target.top_role:
            return False
            
        return True
        
    def add_warning(self, user_id: int, guild_id: int, reason: str, moderator_id: int) -> int:
        """Add a warning to user."""
        try:
            warnings_key = f"warnings_{guild_id}_{user_id}"
            warnings = db.get(warnings_key, [])
            
            warning = {
                'reason': reason,
                'moderator_id': moderator_id,
                'timestamp': datetime.now().isoformat()
            }
            
            warnings.append(warning)
            db[warnings_key] = warnings
            
            return len(warnings)
        except Exception as e:
            logger.error(f"Error adding warning: {e}")
            return 0
            
    def get_user_warnings(self, user_id: int, guild_id: int) -> List[Dict[str, Any]]:
        """Get user warnings."""
        try:
            warnings_key = f"warnings_{guild_id}_{user_id}"
            return db.get(warnings_key, [])
        except Exception as e:
            logger.error(f"Error getting warnings: {e}")
            return []
            
    def clear_user_warnings(self, user_id: int, guild_id: int) -> bool:
        """Clear user warnings."""
        try:
            warnings_key = f"warnings_{guild_id}_{user_id}"
            db[warnings_key] = []
            return True
        except Exception as e:
            logger.error(f"Error clearing warnings: {e}")
            return False
            
    def is_spam(self, message: discord.Message) -> bool:
        """Check if message is spam."""
        content = message.content.lower()
        
        # Check for repeated characters/patterns
        for pattern in self.spam_patterns:
            if re.search(pattern, content):
                return True
                
        # Check for rapid message sending
        user_id = message.author.id
        channel_id = message.channel.id
        
        if user_id not in self.spam_tracker:
            self.spam_tracker[user_id] = {}
            
        if channel_id not in self.spam_tracker[user_id]:
            self.spam_tracker[user_id][channel_id] = []
            
        now = datetime.now()
        self.spam_tracker[user_id][channel_id].append(now)
        
        # Clean old entries
        cutoff = now - timedelta(seconds=10)
        self.spam_tracker[user_id][channel_id] = [
            ts for ts in self.spam_tracker[user_id][channel_id] if ts > cutoff
        ]
        
        # Check if too many messages in short time
        if len(self.spam_tracker[user_id][channel_id]) > 5:
            return True
            
        return False
        
    def has_inappropriate_content(self, message: discord.Message) -> bool:
        """Check if message has inappropriate content."""
        content = message.content.lower()
        
        for word in self.inappropriate_words:
            if word in content:
                return True
                
        return False
        
    @commands.Cog.listener()
    async def on_message(self, message):
        """Auto-moderation listener."""
        if not message.guild or message.author.bot:
            return
            
        # Check if auto-moderation is enabled
        config = get_server_config(message.guild.id)
        if not config.get('auto_moderation', {}).get('enabled', False):
            return
            
        # Skip if user has moderate permissions
        if user_has_permission(message.author, 'moderator'):
            return
            
        actions_taken = []
        
        # Check for spam
        if config['auto_moderation'].get('spam_detection', True) and self.is_spam(message):
            try:
                await message.delete()
                actions_taken.append("deleted spam message")
                
                # Add warning
                warning_count = self.add_warning(
                    message.author.id, 
                    message.guild.id, 
                    "Automatic spam detection", 
                    self.bot.user.id
                )
                
                # Timeout for repeated spam
                if warning_count >= 3:
                    try:
                        await message.author.timeout(timedelta(minutes=5), reason="Repeated spam")
                        actions_taken.append("5-minute timeout for repeated spam")
                    except discord.Forbidden:
                        pass
                        
            except discord.Forbidden:
                pass
                
        # Check for inappropriate content
        if config['auto_moderation'].get('inappropriate_content', True) and self.has_inappropriate_content(message):
            try:
                await message.delete()
                actions_taken.append("deleted inappropriate content")
                
                # Add warning
                warning_count = self.add_warning(
                    message.author.id, 
                    message.guild.id, 
                    "Inappropriate content", 
                    self.bot.user.id
                )
                
                # Timeout for repeated violations
                if warning_count >= 2:
                    try:
                        await message.author.timeout(timedelta(minutes=10), reason="Repeated inappropriate content")
                        actions_taken.append("10-minute timeout for repeated violations")
                    except discord.Forbidden:
                        pass
                        
            except discord.Forbidden:
                pass
                
        # Log actions to mod log channel if configured
        if actions_taken:
            try:
                log_channel_id = config.get('mod_log_channel')
                if log_channel_id:
                    log_channel = message.guild.get_channel(log_channel_id)
                    if log_channel:
                        embed = discord.Embed(
                            title="🤖 Auto-Moderation Action",
                            description=f"**User:** {message.author.mention}\n"
                                      f"**Channel:** {message.channel.mention}\n"
                                      f"**Actions:** {', '.join(actions_taken)}",
                            color=COLORS['warning']
                        )
                        embed.timestamp = datetime.now()
                        await log_channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Error logging auto-mod action: {e}")
        
    # Traditional Commands
    @commands.command(name='kick', help='Kick a member from the server')
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_command(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member from the server."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        if not self.can_moderate(ctx.author, member):
            await ctx.send("❌ You cannot moderate this user!")
            return
            
        try:
            await member.kick(reason=f"Kicked by {ctx.author}: {reason}")
            
            embed = create_embed(
                "✅ Member Kicked",
                f"**User:** {member.mention}\n"
                f"**Moderator:** {ctx.author.mention}\n"
                f"**Reason:** {reason}",
                COLORS['success']
            )
            await ctx.send(embed=embed)
            
            # Log to mod channel
            await self.log_moderation_action(ctx.guild, "Kick", member, ctx.author, reason)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to kick this user!")
        except Exception as e:
            await ctx.send(f"❌ Error kicking user: {e}")
            
    @commands.command(name='ban', help='Ban a member from the server')
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_command(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a member from the server."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        if not self.can_moderate(ctx.author, member):
            await ctx.send("❌ You cannot moderate this user!")
            return
            
        try:
            await member.ban(reason=f"Banned by {ctx.author}: {reason}")
            
            embed = create_embed(
                "✅ Member Banned",
                f"**User:** {member.mention}\n"
                f"**Moderator:** {ctx.author.mention}\n"
                f"**Reason:** {reason}",
                COLORS['error']
            )
            await ctx.send(embed=embed)
            
            # Log to mod channel
            await self.log_moderation_action(ctx.guild, "Ban", member, ctx.author, reason)
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban this user!")
        except Exception as e:
            await ctx.send(f"❌ Error banning user: {e}")
            
    @commands.command(name='warn', help='Warn a member')
    @commands.has_permissions(kick_members=True)
    async def warn_command(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Warn a member."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        if not self.can_moderate(ctx.author, member):
            await ctx.send("❌ You cannot moderate this user!")
            return
            
        try:
            warning_count = self.add_warning(member.id, ctx.guild.id, reason, ctx.author.id)
            
            embed = create_embed(
                "⚠️ Member Warned",
                f"**User:** {member.mention}\n"
                f"**Moderator:** {ctx.author.mention}\n"
                f"**Reason:** {reason}\n"
                f"**Warning Count:** {warning_count}",
                COLORS['warning']
            )
            await ctx.send(embed=embed)
            
            # Log to mod channel
            await self.log_moderation_action(ctx.guild, "Warn", member, ctx.author, reason)
            
        except Exception as e:
            await ctx.send(f"❌ Error warning user: {e}")
            
    @commands.command(name='warnings', help='View user warnings')
    @commands.has_permissions(kick_members=True)
    async def warnings_command(self, ctx, member: discord.Member = None):
        """View user warnings."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        if not member:
            member = ctx.author
            
        warnings = self.get_user_warnings(member.id, ctx.guild.id)
        
        if not warnings:
            await ctx.send(f"No warnings found for {member.mention}")
            return
            
        embed = discord.Embed(
            title=f"⚠️ Warnings for {member.display_name}",
            color=COLORS['warning']
        )
        
        for i, warning in enumerate(warnings[-10:], 1):  # Show last 10 warnings
            embed.add_field(
                name=f"Warning {i}",
                value=f"**Reason:** {warning['reason']}\n"
                      f"**Moderator:** <@{warning['moderator_id']}>\n"
                      f"**Date:** {warning['timestamp'][:10]}",
                inline=False
            )
            
        await ctx.send(embed=embed)
        
    @commands.command(name='purge', help='Delete multiple messages')
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_command(self, ctx, amount: int):
        """Delete multiple messages."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        if amount < 1 or amount > 100:
            await ctx.send("❌ Please specify a number between 1 and 100!")
            return
            
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
            
            embed = create_embed(
                "✅ Messages Purged",
                f"Deleted {len(deleted) - 1} messages in {ctx.channel.mention}",
                COLORS['success']
            )
            
            # Send confirmation and delete after 5 seconds
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await msg.delete()
            
            # Log to mod channel
            await self.log_moderation_action(ctx.guild, "Purge", None, ctx.author, f"Deleted {len(deleted) - 1} messages")
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete messages!")
        except Exception as e:
            await ctx.send(f"❌ Error purging messages: {e}")
            
    # Slash Commands
    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="The member to kick", reason="Reason for kicking")
    async def kick_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Kick a member (slash command)."""
        if not user_has_permission(interaction.user, 'moderator'):
            await interaction.response.send_message("❌ You need moderator permissions!", ephemeral=True)
            return
            
        if not is_module_enabled("moderation", interaction.guild.id):
            await interaction.response.send_message("❌ Moderation module is disabled!", ephemeral=True)
            return
            
        if not self.can_moderate(interaction.user, member):
            await interaction.response.send_message("❌ You cannot moderate this user!", ephemeral=True)
            return
            
        try:
            await member.kick(reason=f"Kicked by {interaction.user}: {reason}")
            
            embed = create_embed(
                "✅ Member Kicked",
                f"**User:** {member.mention}\n"
                f"**Moderator:** {interaction.user.mention}\n"
                f"**Reason:** {reason}",
                COLORS['success']
            )
            await interaction.response.send_message(embed=embed)
            
            # Log to mod channel
            await self.log_moderation_action(interaction.guild, "Kick", member, interaction.user, reason)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to kick this user!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error kicking user: {e}", ephemeral=True)
            
    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="The member to ban", reason="Reason for banning")
    async def ban_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Ban a member (slash command)."""
        if not user_has_permission(interaction.user, 'moderator'):
            await interaction.response.send_message("❌ You need moderator permissions!", ephemeral=True)
            return
            
        if not is_module_enabled("moderation", interaction.guild.id):
            await interaction.response.send_message("❌ Moderation module is disabled!", ephemeral=True)
            return
            
        if not self.can_moderate(interaction.user, member):
            await interaction.response.send_message("❌ You cannot moderate this user!", ephemeral=True)
            return
            
        try:
            await member.ban(reason=f"Banned by {interaction.user}: {reason}")
            
            embed = create_embed(
                "✅ Member Banned",
                f"**User:** {member.mention}\n"
                f"**Moderator:** {interaction.user.mention}\n"
                f"**Reason:** {reason}",
                COLORS['error']
            )
            await interaction.response.send_message(embed=embed)
            
            # Log to mod channel
            await self.log_moderation_action(interaction.guild, "Ban", member, interaction.user, reason)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to ban this user!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error banning user: {e}", ephemeral=True)
            
    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(member="The member to warn", reason="Reason for warning")
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Warn a member (slash command)."""
        if not user_has_permission(interaction.user, 'moderator'):
            await interaction.response.send_message("❌ You need moderator permissions!", ephemeral=True)
            return
            
        if not is_module_enabled("moderation", interaction.guild.id):
            await interaction.response.send_message("❌ Moderation module is disabled!", ephemeral=True)
            return
            
        if not self.can_moderate(interaction.user, member):
            await interaction.response.send_message("❌ You cannot moderate this user!", ephemeral=True)
            return
            
        try:
            warning_count = self.add_warning(member.id, interaction.guild.id, reason, interaction.user.id)
            
            embed = create_embed(
                "⚠️ Member Warned",
                f"**User:** {member.mention}\n"
                f"**Moderator:** {interaction.user.mention}\n"
                f"**Reason:** {reason}\n"
                f"**Warning Count:** {warning_count}",
                COLORS['warning']
            )
            await interaction.response.send_message(embed=embed)
            
            # Log to mod channel
            await self.log_moderation_action(interaction.guild, "Warn", member, interaction.user, reason)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error warning user: {e}", ephemeral=True)
            
    @app_commands.command(name="warnings", description="View user warnings")
    @app_commands.describe(member="The member to check warnings for")
    async def warnings_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        """View user warnings (slash command)."""
        if not user_has_permission(interaction.user, 'moderator'):
            await interaction.response.send_message("❌ You need moderator permissions!", ephemeral=True)
            return
            
        if not is_module_enabled("moderation", interaction.guild.id):
            await interaction.response.send_message("❌ Moderation module is disabled!", ephemeral=True)
            return
            
        if not member:
            member = interaction.user
            
        warnings = self.get_user_warnings(member.id, interaction.guild.id)
        
        if not warnings:
            await interaction.response.send_message(f"No warnings found for {member.mention}", ephemeral=True)
            return
            
        embed = discord.Embed(
            title=f"⚠️ Warnings for {member.display_name}",
            color=COLORS['warning']
        )
        
        for i, warning in enumerate(warnings[-10:], 1):  # Show last 10 warnings
            embed.add_field(
                name=f"Warning {i}",
                value=f"**Reason:** {warning['reason']}\n"
                      f"**Moderator:** <@{warning['moderator_id']}>\n"
                      f"**Date:** {warning['timestamp'][:10]}",
                inline=False
            )
            
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @app_commands.command(name="purge", description="Delete multiple messages")
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    async def purge_slash(self, interaction: discord.Interaction, amount: int):
        """Delete multiple messages (slash command)."""
        if not user_has_permission(interaction.user, 'moderator'):
            await interaction.response.send_message("❌ You need moderator permissions!", ephemeral=True)
            return
            
        if not is_module_enabled("moderation", interaction.guild.id):
            await interaction.response.send_message("❌ Moderation module is disabled!", ephemeral=True)
            return
            
        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Please specify a number between 1 and 100!", ephemeral=True)
            return
            
        try:
            await interaction.response.defer(ephemeral=True)
            deleted = await interaction.channel.purge(limit=amount)
            
            embed = create_embed(
                "✅ Messages Purged",
                f"Deleted {len(deleted)} messages in {interaction.channel.mention}",
                COLORS['success']
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Log to mod channel
            await self.log_moderation_action(interaction.guild, "Purge", None, interaction.user, f"Deleted {len(deleted)} messages")
            
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to delete messages!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error purging messages: {e}", ephemeral=True)
            
    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.describe(member="The member to timeout", minutes="Duration in minutes", reason="Reason for timeout")
    async def timeout_slash(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason provided"):
        """Timeout a member (slash command)."""
        if not user_has_permission(interaction.user, 'moderator'):
            await interaction.response.send_message("❌ You need moderator permissions!", ephemeral=True)
            return
            
        if not is_module_enabled("moderation", interaction.guild.id):
            await interaction.response.send_message("❌ Moderation module is disabled!", ephemeral=True)
            return
            
        if not self.can_moderate(interaction.user, member):
            await interaction.response.send_message("❌ You cannot moderate this user!", ephemeral=True)
            return
            
        if minutes < 1 or minutes > 40320:  # Discord limit is 28 days
            await interaction.response.send_message("❌ Timeout duration must be between 1 minute and 28 days!", ephemeral=True)
            return
            
        try:
            timeout_until = datetime.now() + timedelta(minutes=minutes)
            await member.timeout(timeout_until, reason=f"Timed out by {interaction.user}: {reason}")
            
            embed = create_embed(
                "🔇 Member Timed Out",
                f"**User:** {member.mention}\n"
                f"**Moderator:** {interaction.user.mention}\n"
                f"**Duration:** {minutes} minutes\n"
                f"**Reason:** {reason}",
                COLORS['warning']
            )
            await interaction.response.send_message(embed=embed)
            
            # Log to mod channel
            await self.log_moderation_action(interaction.guild, "Timeout", member, interaction.user, f"{reason} ({minutes} minutes)")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to timeout this user!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error timing out user: {e}", ephemeral=True)
            
    async def log_moderation_action(self, guild: discord.Guild, action: str, target: Optional[discord.Member], moderator: discord.Member, reason: str):
        """Log moderation action to mod log channel."""
        try:
            config = get_server_config(guild.id)
            log_channel_id = config.get('mod_log_channel')
            
            if not log_channel_id:
                return
                
            log_channel = guild.get_channel(log_channel_id)
            if not log_channel:
                return
                
            embed = discord.Embed(
                title=f"🛡️ Moderation Action: {action}",
                color=COLORS['info']
            )
            
            if target:
                embed.add_field(name="Target", value=target.mention, inline=True)
            embed.add_field(name="Moderator", value=moderator.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.timestamp = datetime.now()
            
            await log_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error logging moderation action: {e}")

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(ModerationCog(bot))
