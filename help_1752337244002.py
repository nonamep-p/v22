import discord
from discord.ext import commands
from config import COLORS, EMOJIS
import logging

logger = logging.getLogger(__name__)

class HelpView(discord.ui.View):
    """Interactive help menu with pagination and category selection."""
    
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view
        self.current_page = 0
        self.pages = self.create_pages()
        
    def create_pages(self):
        """Create help pages for each category."""
        pages = []
        
        # Main/Overview Page
        main_embed = discord.Embed(
            title="🎮 Epic RPG Helper - Command Help",
            description="A comprehensive RPG bot with AI, economy, moderation, and more!\n\n"
                       "**🎯 Quick Start:**\n"
                       "• Use `$start` to begin your RPG adventure\n"
                       "• Use the dropdown below to navigate categories\n"
                       "• Use the buttons to browse pages\n\n"
                       "**📱 Support:**\n"
                       "Need help? Join our support server or contact an admin!",
            color=COLORS['primary']
        )
        main_embed.add_field(
            name="📊 Bot Statistics",
            value="• Multi-server RPG system\n"
                  "• AI-powered chatbot\n"
                  "• Advanced economy system\n"
                  "• Comprehensive moderation tools\n"
                  "• Interactive adventures & dungeons",
            inline=True
        )
        main_embed.add_field(
            name="🔧 Configuration",
            value="• Customizable server settings\n"
                  "• Module enable/disable\n"
                  "• Channel restrictions\n"
                  "• Auto-moderation settings\n"
                  "• AI personality customization",
            inline=True
        )
        main_embed.set_footer(text="Select a category from the dropdown below to see specific commands")
        pages.append(("Overview", main_embed))
        
        # RPG Games Page
        rpg_embed = discord.Embed(
            title=f"{EMOJIS['rpg']} RPG Games Commands",
            description="Complete RPG system with adventures, dungeons, battles, and more!",
            color=COLORS['primary']
        )
        rpg_embed.add_field(
            name="🎯 Getting Started",
            value="`$start` - Begin your RPG adventure\n"
                  "`$profile` - View your character profile\n"
                  "`$inventory` - Check your items\n"
                  "`$heal` - Restore your health",
            inline=False
        )
        rpg_embed.add_field(
            name="🗺️ Adventures & Exploration",
            value="`$adventure [location]` - Go on adventures\n"
                  "`$dungeon [name]` - Explore dangerous dungeons\n"
                  "`$battle [player]` - Battle monsters or players\n"
                  "`$equip <item>` - Equip weapons and armor",
            inline=False
        )
        rpg_embed.add_field(
            name="🔨 Crafting & Progression",
            value="`$craft [item]` - Craft items from materials\n"
                  "`$leaderboard [category]` - View rankings\n"
                  "`$use <item>` - Use consumable items",
            inline=False
        )
        rpg_embed.set_footer(text="💡 Tip: Start with $start, then try $adventure to begin exploring!")
        pages.append(("RPG", rpg_embed))
        
        # Economy Page
        economy_embed = discord.Embed(
            title=f"{EMOJIS['economy']} Economy Commands",
            description="Earn coins, trade items, and build your wealth!",
            color=COLORS['warning']
        )
        economy_embed.add_field(
            name="💼 Earning Money",
            value="`$work` - Work various jobs to earn coins\n"
                  "`$daily` - Claim your daily reward\n"
                  "`$adventure` - Earn coins from adventures",
            inline=False
        )
        economy_embed.add_field(
            name="🏪 Shopping & Trading",
            value="`$shop` - Browse the item shop\n"
                  "`$buy <item>` - Purchase items\n"
                  "`$sell <item>` - Sell items from inventory\n"
                  "`$auction` - Access the auction house",
            inline=False
        )
        economy_embed.add_field(
            name="📈 Investments",
            value="`$invest [amount]` - Invest for passive income\n"
                  "`$portfolio` - View your investments\n"
                  "`$withdraw` - Withdraw from investments",
            inline=False
        )
        economy_embed.set_footer(text="💡 Tip: Use $work and $daily regularly to build up your coins!")
        pages.append(("Economy", economy_embed))
        
        # AI Chatbot Page
        ai_embed = discord.Embed(
            title=f"{EMOJIS['ai']} AI Chatbot Commands",
            description="Chat with our advanced AI powered by Google Gemini!",
            color=COLORS['info']
        )
        ai_embed.add_field(
            name="💬 Basic Interaction",
            value="`$chat <message>` - Direct chat with AI\n"
                  "`@Epic-Maki <message>` - Mention bot to chat\n"
                  "Reply to bot messages to continue conversation",
            inline=False
        )
        ai_embed.add_field(
            name="⚙️ AI Management",
            value="`$ai_status` - Check AI system status\n"
                  "`$clear_chat` - Clear conversation history\n"
                  "`$ai_persona <prompt>` - Set custom AI personality (Admin)",
            inline=False
        )
        ai_embed.add_field(
            name="🧠 AI Features",
            value="• Contextual conversations\n"
                  "• Persistent conversation memory\n"
                  "• Custom server personalities\n"
                  "• RPG-themed responses\n"
                  "• Natural language understanding",
            inline=False
        )
        ai_embed.set_footer(text="💡 Tip: Just mention the bot or reply to its messages to start chatting!")
        pages.append(("AI", ai_embed))
        
        # Moderation Page
        moderation_embed = discord.Embed(
            title=f"{EMOJIS['moderation']} Moderation Commands",
            description="Powerful moderation tools with auto-moderation features!",
            color=COLORS['error']
        )
        moderation_embed.add_field(
            name="🔨 Basic Moderation",
            value="`$kick <user> [reason]` - Kick a member\n"
                  "`$ban <user> [reason]` - Ban a member\n"
                  "`$unban <user_id> [reason]` - Unban a user\n"
                  "`$timeout <user> <minutes> [reason]` - Timeout a member\n"
                  "`$untimeout <user> [reason]` - Remove timeout",
            inline=False
        )
        moderation_embed.add_field(
            name="⚠️ Warning System",
            value="`$warn <user> [reason]` - Warn a member\n"
                  "`$warnings [user]` - View user warnings\n"
                  "`$clearwarnings <user>` - Clear all warnings",
            inline=False
        )
        moderation_embed.add_field(
            name="🛡️ Auto-Moderation",
            value="`$automod` - Configure auto-moderation\n"
                  "`$modstats` - View moderation statistics\n"
                  "`$slowmode <seconds>` - Set channel slowmode\n"
                  "`$purge <amount>` - Delete multiple messages",
            inline=False
        )
        moderation_embed.set_footer(text="💡 Tip: Configure auto-moderation to automatically handle spam and inappropriate content!")
        pages.append(("Moderation", moderation_embed))
        
        # Admin Page
        admin_embed = discord.Embed(
            title=f"{EMOJIS['admin']} Admin Commands",
            description="Server configuration and administrative tools!",
            color=COLORS['dark']
        )
        admin_embed.add_field(
            name="⚙️ Server Configuration",
            value="`$config` - Interactive server configuration\n"
                  "`$config prefix <new_prefix>` - Change command prefix\n"
                  "`$config currency <name>` - Set currency name\n"
                  "`$config ai_channels` - Configure AI channels",
            inline=False
        )
        admin_embed.add_field(
            name="📊 Statistics & Monitoring",
            value="`$stats` - View bot statistics\n"
                  "`$modstats` - View moderation stats\n"
                  "`$leaderboard` - View server leaderboards",
            inline=False
        )
        admin_embed.add_field(
            name="🔧 Maintenance",
            value="`$backup` - Create database backup\n"
                  "`$cleanup <days>` - Clean old user data\n"
                  "`$reload [cog]` - Reload bot modules (Owner)\n"
                  "`$maintenance` - Toggle maintenance mode (Owner)",
            inline=False
        )
        admin_embed.set_footer(text="💡 Tip: Use $config for an interactive setup menu!")
        pages.append(("Admin", admin_embed))
        
        return pages
    
    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page."""
        self.current_page -= 1
        
        # Update button states
        if self.current_page == 0:
            button.disabled = True
        self.next_button.disabled = False
        
        # Update embed
        _, embed = self.pages[self.current_page]
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page."""
        self.current_page += 1
        
        # Update button states
        if self.current_page == len(self.pages) - 1:
            button.disabled = True
        self.previous_button.disabled = False
        
        # Update embed
        _, embed = self.pages[self.current_page]
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.select(
        placeholder="Select a category...",
        options=[
            discord.SelectOption(label="Overview", description="Bot overview and quick start", emoji="🎮", value="0"),
            discord.SelectOption(label="RPG Games", description="Adventures, dungeons, and battles", emoji="🎯", value="1"),
            discord.SelectOption(label="Economy", description="Coins, shop, and trading", emoji="💰", value="2"),
            discord.SelectOption(label="AI Chatbot", description="Chat with our advanced AI", emoji="🤖", value="3"),
            discord.SelectOption(label="Moderation", description="Moderation and auto-mod tools", emoji="🔨", value="4"),
            discord.SelectOption(label="Admin", description="Server configuration and management", emoji="👑", value="5"),
        ]
    )
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Jump to selected category."""
        self.current_page = int(select.values[0])
        
        # Update button states
        self.previous_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page == len(self.pages) - 1)
        
        # Update embed
        _, embed = self.pages[self.current_page]
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🗑️ Close", style=discord.ButtonStyle.danger, row=1)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close the help menu."""
        # Only allow the original user or users with manage_messages permission to close
        if (hasattr(interaction.message, 'interaction') and 
            interaction.user == interaction.message.interaction.user) or \
           interaction.user.guild_permissions.manage_messages:
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="✅ Help Menu Closed",
                    description="Help menu has been closed.",
                    color=COLORS['success']
                ),
                view=None
            )
        else:
            await interaction.response.send_message(
                "❌ You can only close your own help menu!",
                ephemeral=True
            )

class HelpCog(commands.Cog):
    """Interactive help system."""
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name='help', help='Show this help message')
    async def help_command(self, ctx, *, command: str = None):
        """Interactive help command with UI components."""
        try:
            if command:
                # Show help for specific command
                cmd = self.bot.get_command(command)
                if cmd:
                    embed = discord.Embed(
                        title=f"❓ Help: {cmd.name}",
                        description=cmd.help or "No description available.",
                        color=COLORS['info']
                    )
                    
                    # Add usage info
                    usage = f"$"
                    if cmd.parent:
                        usage += f"{cmd.parent.name} "
                    usage += cmd.name
                    
                    if cmd.signature:
                        usage += f" {cmd.signature}"
                    
                    embed.add_field(
                        name="Usage",
                        value=f"`{usage}`",
                        inline=False
                    )
                    
                    # Add aliases if any
                    if cmd.aliases:
                        embed.add_field(
                            name="Aliases",
                            value=", ".join([f"`{alias}`" for alias in cmd.aliases]),
                            inline=False
                        )
                    
                    # Add cooldown info if any
                    if cmd.cooldown:
                        embed.add_field(
                            name="Cooldown",
                            value=f"{cmd.cooldown.per} seconds",
                            inline=True
                        )
                    
                    # Add permissions required
                    if hasattr(cmd, 'requires_permissions'):
                        perms = cmd.requires_permissions
                        if perms:
                            embed.add_field(
                                name="Required Permissions",
                                value=", ".join(perms),
                                inline=True
                            )
                    
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="❌ Command Not Found",
                        description=f"No command named `{command}` found.",
                        color=COLORS['error']
                    )
                    await ctx.send(embed=embed)
                    
            else:
                # Show interactive help menu
                view = HelpView()
                _, embed = view.pages[0]  # Start with overview page
                await ctx.send(embed=embed, view=view)
                
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while displaying help.",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='commands', help='List all available commands')
    async def list_commands(self, ctx):
        """List all available commands by category."""
        try:
            embed = discord.Embed(
                title="📋 All Commands",
                description="Complete list of available commands",
                color=COLORS['info']
            )
            
            # Group commands by cog
            cog_commands = {}
            
            for command in self.bot.commands:
                if command.hidden:
                    continue
                    
                cog_name = command.cog.qualified_name if command.cog else "No Category"
                
                # Simplify cog names
                cog_display_name = cog_name.replace("Cog", "").replace("Commands", "")
                
                if cog_display_name not in cog_commands:
                    cog_commands[cog_display_name] = []
                    
                cog_commands[cog_display_name].append(f"`${command.name}`")
            
            # Add fields for each category
            for cog_name, commands_list in cog_commands.items():
                if commands_list:
                    # Get appropriate emoji
                    emoji = "📁"
                    if "RPG" in cog_name or "Games" in cog_name:
                        emoji = "🎮"
                    elif "Economy" in cog_name:
                        emoji = "💰"
                    elif "AI" in cog_name or "Chatbot" in cog_name:
                        emoji = "🤖"
                    elif "Moderation" in cog_name:
                        emoji = "🔨"
                    elif "Admin" in cog_name:
                        emoji = "👑"
                    elif "Help" in cog_name:
                        emoji = "❓"
                    
                    embed.add_field(
                        name=f"{emoji} {cog_name}",
                        value=" ".join(commands_list),
                        inline=False
                    )
            
            embed.set_footer(text="Use $help <command> for detailed information about a specific command")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in commands list: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while listing commands.",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='support', help='Get support information')
    async def support_info(self, ctx):
        """Show support information."""
        try:
            embed = discord.Embed(
                title="🆘 Support Information",
                description="Need help with Epic RPG Helper? Here's how to get support:",
                color=COLORS['info']
            )
            
            embed.add_field(
                name="📚 Documentation",
                value="• Use `$help` for interactive command help\n"
                      "• Use `$help <command>` for specific command info\n"
                      "• Use `$commands` to see all available commands",
                inline=False
            )
            
            embed.add_field(
                name="🎮 Getting Started",
                value="• Use `$start` to begin your RPG adventure\n"
                      "• Use `$config` for server setup (admins)\n"
                      "• Check `$stats` for bot status information",
                inline=False
            )
            
            embed.add_field(
                name="🐛 Bug Reports & Feature Requests",
                value="• Contact server administrators\n"
                      "• Report issues in the appropriate channels\n"
                      "• Use `$stats` to provide system information",
                inline=False
            )
            
            embed.add_field(
                name="⚙️ Configuration Help",
                value="• Admins can use `$config` for setup\n"
                      "• Use `$automod` for moderation configuration\n"
                      "• Use `$ai_persona` to customize AI behavior",
                inline=False
            )
            
            embed.set_footer(text="Epic RPG Helper - Your adventure awaits!")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in support command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while displaying support information.",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
