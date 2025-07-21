import discord
from discord.ext import commands
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

class AutoModView(discord.ui.View):
    """View for auto-moderation settings."""
    
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.config = get_server_config(guild_id)
        
    @discord.ui.button(label="Toggle Spam Detection", style=discord.ButtonStyle.secondary)
    async def toggle_spam(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Toggle spam detection."""
        if not user_has_permission(interaction.user, 'admin'):
            await interaction.response.send_message("❌ You need admin permissions!", ephemeral=True)
            return
            
        self.config['auto_moderation']['spam_detection'] = not self.config['auto_moderation']['spam_detection']
        update_server_config(self.guild_id, self.config)
        
        status = "enabled" if self.config['auto_moderation']['spam_detection'] else "disabled"
        await interaction.response.send_message(f"✅ Spam detection {status}!", ephemeral=True)
        
    @discord.ui.button(label="Toggle Content Filter", style=discord.ButtonStyle.secondary)
    async def toggle_content(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Toggle inappropriate content filter."""
        if not user_has_permission(interaction.user, 'admin'):
            await interaction.response.send_message("❌ You need admin permissions!", ephemeral=True)
            return
            
        self.config['auto_moderation']['inappropriate_content'] = not self.config['auto_moderation']['inappropriate_content']
        update_server_config(self.guild_id, self.config)
        
        status = "enabled" if self.config['auto_moderation']['inappropriate_content'] else "disabled"
        await interaction.response.send_message(f"✅ Content filter {status}!", ephemeral=True)

class WarningView(discord.ui.View):
    """View for warning management."""
    
    def __init__(self, user_id: int, guild_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.guild_id = guild_id
        
    @discord.ui.button(label="View Warnings", style=discord.ButtonStyle.primary, emoji="📋")
    async def view_warnings(self, interaction: discord.Interaction, button: discord.ui.Button):
        """View user warnings."""
        warnings = self.get_user_warnings(self.user_id, self.guild_id)
        
        if not warnings:
            await interaction.response.send_message("No warnings found for this user.", ephemeral=True)
            return
            
        embed = discord.Embed(
            title=f"Warnings for {interaction.guild.get_member(self.user_id)}",
            color=COLORS['warning']
        )
        
        for i, warning in enumerate(warnings[-5:], 1):  # Show last 5 warnings
            embed.add_field(
                name=f"Warning {i}",
                value=f"**Reason:** {warning['reason']}\n"
                      f"**Moderator:** <@{warning['moderator_id']}>\n"
                      f"**Date:** {warning['timestamp'][:10]}",
                inline=False
            )
            
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @discord.ui.button(label="Clear Warnings", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def clear_warnings(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Clear user warnings."""
        if not user_has_permission(interaction.user, 'admin'):
            await interaction.response.send_message("❌ You need admin permissions!", ephemeral=True)
            return
            
        self.clear_user_warnings(self.user_id, self.guild_id)
        await interaction.response.send_message("✅ All warnings cleared!", ephemeral=True)
        
    def get_user_warnings(self, user_id: int, guild_id: int) -> List[Dict[str, Any]]:
        """Get user warnings from database."""
        try:
            warnings_key = f"warnings_{guild_id}_{user_id}"
            return db.get(warnings_key, [])
        except Exception as e:
            logger.error(f"Error getting warnings: {e}")
            return []
            
    def clear_user_warnings(self, user_id: int, guild_id: int):
        """Clear user warnings."""
        try:
            warnings_key = f"warnings_{guild_id}_{user_id}"
            db[warnings_key] = []
        except Exception as e:
            logger.error(f"Error clearing warnings: {e}")

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
        
        self.inappropriate_words = [
            # Add your inappropriate words list here
            # This is a basic example - in production you'd use a comprehensive list
            'badword1', 'badword2', 'badword3'
        ]
        
    def can_moderate(self, ctx, target):
        """Check if user can moderate target."""
        if ctx.author == ctx.guild.owner:
            return True
            
        if target == ctx.guild.owner:
            return False
            
        if ctx.author.top_role <= target.top_role:
            return False
            
        return True
        
    def add_warning(self, user_id: int, guild_id: int, reason: str, moderator_id: int):
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
                        embed.timestamp = datetime.utcnow()
                        await log_channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Error logging auto-mod action: {e}")
        
    @commands.command(name='kick', help='Kick a member from the server')
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member from the server."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        if not self.can_moderate(ctx, member):
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="You cannot kick someone with a higher or equal role!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            return
            
        if member.top_role >= ctx.guild.me.top_role:
            embed = discord.Embed(
                title="❌ Bot Missing Permissions",
                description="I cannot kick someone with a higher or equal role than me!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            return
            
        try:
            # Send DM to user before kicking
            try:
                dm_embed = discord.Embed(
                    title=f"Kicked from {ctx.guild.name}",
                    description=f"**Reason:** {reason}\n**Moderator:** {ctx.author}",
                    color=COLORS['error']
                )
                await member.send(embed=dm_embed)
            except:
                pass  # User might have DMs disabled
                
            await member.kick(reason=f"Kicked by {ctx.author} - {reason}")
            
            # Create log embed
            embed = discord.Embed(
                title="👢 Member Kicked",
                description=f"**Member:** {member.mention} ({member})\n"
                           f"**Moderator:** {ctx.author.mention}\n"
                           f"**Reason:** {reason}",
                color=COLORS['warning']
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to kick this member!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in kick command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='ban', help='Ban a member from the server')
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a member from the server."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        if not self.can_moderate(ctx, member):
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="You cannot ban someone with a higher or equal role!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            return
            
        if member.top_role >= ctx.guild.me.top_role:
            embed = discord.Embed(
                title="❌ Bot Missing Permissions",
                description="I cannot ban someone with a higher or equal role than me!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            return
            
        try:
            # Send DM to user before banning
            try:
                dm_embed = discord.Embed(
                    title=f"Banned from {ctx.guild.name}",
                    description=f"**Reason:** {reason}\n**Moderator:** {ctx.author}",
                    color=COLORS['error']
                )
                await member.send(embed=dm_embed)
            except:
                pass  # User might have DMs disabled
                
            await member.ban(reason=f"Banned by {ctx.author} - {reason}")
            
            # Create log embed
            embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"**Member:** {member.mention} ({member})\n"
                           f"**Moderator:** {ctx.author.mention}\n"
                           f"**Reason:** {reason}",
                color=COLORS['error']
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to ban this member!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in ban command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='unban', help='Unban a user from the server')
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban_member(self, ctx, user_id: int, *, reason="No reason provided"):
        """Unban a user from the server."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author} - {reason}")
            
            embed = discord.Embed(
                title="✅ Member Unbanned",
                description=f"**User:** {user.mention} ({user})\n"
                           f"**Moderator:** {ctx.author.mention}\n"
                           f"**Reason:** {reason}",
                color=COLORS['success']
            )
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
            
        except discord.NotFound:
            embed = discord.Embed(
                title="❌ User Not Found",
                description="User not found or not banned!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in unban command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='timeout', help='Timeout a member')
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout_member(self, ctx, member: discord.Member, duration: int, *, reason="No reason provided"):
        """Timeout a member for specified minutes."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        if not self.can_moderate(ctx, member):
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="You cannot timeout someone with a higher or equal role!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            return
            
        if duration > 10080:  # 7 days max
            embed = discord.Embed(
                title="❌ Invalid Duration",
                description="Maximum timeout duration is 7 days (10080 minutes)!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            return
            
        try:
            timeout_until = datetime.utcnow() + timedelta(minutes=duration)
            await member.timeout(timeout_until, reason=f"Timed out by {ctx.author} - {reason}")
            
            embed = discord.Embed(
                title="⏰ Member Timed Out",
                description=f"**Member:** {member.mention} ({member})\n"
                           f"**Moderator:** {ctx.author.mention}\n"
                           f"**Duration:** {duration} minutes\n"
                           f"**Reason:** {reason}",
                color=COLORS['warning']
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to timeout this member!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in timeout command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='untimeout', help='Remove timeout from a member')
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def untimeout_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Remove timeout from a member."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        if not member.is_timed_out():
            embed = discord.Embed(
                title="❌ Not Timed Out",
                description="Member is not currently timed out!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            return
            
        try:
            await member.timeout(None, reason=f"Timeout removed by {ctx.author} - {reason}")
            
            embed = discord.Embed(
                title="✅ Timeout Removed",
                description=f"**Member:** {member.mention} ({member})\n"
                           f"**Moderator:** {ctx.author.mention}\n"
                           f"**Reason:** {reason}",
                color=COLORS['success']
            )
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to remove timeout from this member!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in untimeout command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='warn', help='Warn a member')
    @commands.has_permissions(manage_messages=True)
    async def warn_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Warn a member."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        if not self.can_moderate(ctx, member):
            embed = discord.Embed(
                title="❌ Insufficient Permissions",
                description="You cannot warn someone with a higher or equal role!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            return
            
        try:
            # Add warning to database
            warning_count = self.add_warning(member.id, ctx.guild.id, reason, ctx.author.id)
            
            # Send DM to user
            try:
                dm_embed = discord.Embed(
                    title=f"Warning in {ctx.guild.name}",
                    description=f"**Reason:** {reason}\n**Moderator:** {ctx.author}\n**Warning #{warning_count}**",
                    color=COLORS['warning']
                )
                await member.send(embed=dm_embed)
            except:
                pass  # User might have DMs disabled
                
            embed = discord.Embed(
                title="⚠️ Member Warned",
                description=f"**Member:** {member.mention} ({member})\n"
                           f"**Moderator:** {ctx.author.mention}\n"
                           f"**Reason:** {reason}\n"
                           f"**Warning Count:** {warning_count}",
                color=COLORS['warning']
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.timestamp = datetime.utcnow()
            
            # Auto-actions based on warning count
            config = get_server_config(ctx.guild.id)
            max_warnings = config.get('auto_moderation', {}).get('max_warnings', 3)
            
            if warning_count >= max_warnings:
                try:
                    await member.timeout(timedelta(hours=1), reason=f"Reached {max_warnings} warnings")
                    embed.add_field(
                        name="🚨 Auto-Action",
                        value=f"Member automatically timed out for 1 hour (reached {max_warnings} warnings)",
                        inline=False
                    )
                except discord.Forbidden:
                    pass
                    
            # Add view for warning management
            view = WarningView(member.id, ctx.guild.id)
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error in warn command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='warnings', help='View warnings for a member')
    @commands.has_permissions(manage_messages=True)
    async def view_warnings(self, ctx, member: discord.Member = None):
        """View warnings for a member."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        if member is None:
            member = ctx.author
            
        warnings = self.get_user_warnings(member.id, ctx.guild.id)
        
        if not warnings:
            embed = discord.Embed(
                title="📋 No Warnings",
                description=f"{member.mention} has no warnings.",
                color=COLORS['success']
            )
            await ctx.send(embed=embed)
            return
            
        embed = discord.Embed(
            title=f"📋 Warnings for {member.display_name}",
            description=f"Total warnings: {len(warnings)}",
            color=COLORS['warning']
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Show recent warnings
        for i, warning in enumerate(warnings[-5:], 1):
            moderator = ctx.guild.get_member(warning['moderator_id'])
            moderator_name = moderator.display_name if moderator else "Unknown"
            
            embed.add_field(
                name=f"Warning {len(warnings) - 5 + i}",
                value=f"**Reason:** {warning['reason']}\n"
                      f"**Moderator:** {moderator_name}\n"
                      f"**Date:** {warning['timestamp'][:10]}",
                inline=False
            )
            
        if len(warnings) > 5:
            embed.set_footer(text=f"Showing last 5 of {len(warnings)} warnings")
            
        await ctx.send(embed=embed)
        
    @commands.command(name='clearwarnings', help='Clear warnings for a member')
    @commands.has_permissions(manage_guild=True)
    async def clear_warnings(self, ctx, member: discord.Member):
        """Clear all warnings for a member."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        try:
            warnings_key = f"warnings_{ctx.guild.id}_{member.id}"
            old_count = len(db.get(warnings_key, []))
            db[warnings_key] = []
            
            embed = discord.Embed(
                title="✅ Warnings Cleared",
                description=f"Cleared {old_count} warning(s) for {member.mention}",
                color=COLORS['success']
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error clearing warnings: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while clearing warnings.",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='automod', help='Configure auto-moderation settings')
    @commands.has_permissions(manage_guild=True)
    async def automod_config(self, ctx):
        """Configure auto-moderation settings."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        config = get_server_config(ctx.guild.id)
        automod = config.get('auto_moderation', {})
        
        embed = discord.Embed(
            title="🤖 Auto-Moderation Settings",
            description="Configure automatic moderation features",
            color=COLORS['info']
        )
        
        embed.add_field(
            name="Current Settings",
            value=f"**Enabled:** {'✅' if automod.get('enabled', False) else '❌'}\n"
                  f"**Spam Detection:** {'✅' if automod.get('spam_detection', True) else '❌'}\n"
                  f"**Content Filter:** {'✅' if automod.get('inappropriate_content', True) else '❌'}\n"
                  f"**Max Warnings:** {automod.get('max_warnings', 3)}",
            inline=False
        )
        
        view = AutoModView(ctx.guild.id)
        await ctx.send(embed=embed, view=view)
        
    @commands.command(name='modstats', help='View moderation statistics')
    @commands.has_permissions(manage_messages=True)
    async def mod_stats(self, ctx):
        """View moderation statistics."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        try:
            # Count warnings
            total_warnings = 0
            warned_users = 0
            
            for key in db.keys():
                if key.startswith(f"warnings_{ctx.guild.id}_"):
                    warnings = db[key]
                    if warnings:
                        total_warnings += len(warnings)
                        warned_users += 1
                        
            embed = discord.Embed(
                title="📊 Moderation Statistics",
                description=f"Statistics for {ctx.guild.name}",
                color=COLORS['info']
            )
            
            embed.add_field(
                name="Warning Stats",
                value=f"**Total Warnings:** {total_warnings}\n"
                      f"**Users with Warnings:** {warned_users}",
                inline=True
            )
            
            embed.add_field(
                name="Auto-Mod Stats",
                value=f"**Spam Messages Deleted:** {len(self.spam_tracker)}\n"
                      f"**Active Timeouts:** {len([u for u in ctx.guild.members if u.is_timed_out()])}",
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in modstats command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while fetching statistics.",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)

    @commands.command(name='slowmode', help='Set channel slowmode')
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def set_slowmode(self, ctx, seconds: int = 0):
        """Set slowmode for the current channel."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        if seconds < 0 or seconds > 21600:  # Max 6 hours
            embed = discord.Embed(
                title="❌ Invalid Duration",
                description="Slowmode must be between 0 and 21600 seconds (6 hours)!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            return
            
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            
            if seconds == 0:
                description = "Slowmode disabled for this channel."
            else:
                description = f"Slowmode set to {seconds} seconds for this channel."
                
            embed = discord.Embed(
                title="✅ Slowmode Updated",
                description=description,
                color=COLORS['success']
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to manage this channel!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in slowmode command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)

    @commands.command(name='purge', help='Delete multiple messages')
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_messages(self, ctx, amount: int):
        """Delete multiple messages."""
        if not is_module_enabled("moderation", ctx.guild.id):
            return
            
        if amount < 1 or amount > 100:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Amount must be between 1 and 100!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            return
            
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 for the command message
            
            embed = discord.Embed(
                title="✅ Messages Purged",
                description=f"Deleted {len(deleted) - 1} message(s) in {ctx.channel.mention}",
                color=COLORS['success']
            )
            
            # Send confirmation and delete it after 5 seconds
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await msg.delete()
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to delete messages!",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in purge command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
