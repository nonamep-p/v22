import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from config import COLORS, EMOJIS, is_module_enabled
from utils.database import get_user_data, update_user_data, ensure_user_exists
from utils.helpers import create_embed, format_number
from rpg_data.game_data import CLASSES, PATHS, ITEMS, RARITY_COLORS
from utils.warning_system import warning_system

logger = logging.getLogger(__name__)

class StartRPGView(discord.ui.View):
    """Button to initiate the RPG start process."""

    def __init__(self):
        super().__init__(timeout=None)  # Persistent view

    @discord.ui.button(label="✨ Start Your Adventure", style=discord.ButtonStyle.success, custom_id="start_rpg_adventure")
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        rpg_core = self.get_rpg_core(interaction.client)
        if not rpg_core:
            await interaction.response.send_message("❌ RPG module not found.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)  # Acknowledge and defer

        user_id = str(interaction.user.id)
        ensure_user_exists(user_id)

        # Check if user already has a character
        player_data = rpg_core.get_player_data(user_id)
        if player_data:
            embed = discord.Embed(
                title="🎮 Adventure Already Started!",
                description=f"Welcome back, {interaction.user.mention}! Your adventure continues...\n\n"
                           f"**Current Character:**\n"
                           f"• **Class:** {CLASSES[player_data['class']]['name']}\n"
                           f"• **Level:** {player_data['level']}\n"
                           f"• **Gold:** {format_number(player_data['gold'])}\n"
                           f"• **HP:** {player_data['resources']['hp']}/{player_data['resources']['max_hp']}\n\n"
                           f"Use `$profile` to view your full character sheet!",
                color=COLORS['info']
            )
            await interaction.followup.send(embed=embed)
            return

        # Create character creation embed
        embed = discord.Embed(
            title="🎭 Begin Your RPG Adventure",
            description="**Welcome to Project: Blood & Cheese!**\n\n"
                       "Choose your character class to start your epic journey!",
            color=COLORS['primary']
        )

        view = ClassSelectionView(user_id, rpg_core)
        await interaction.followup.send(embed=embed, view=view)

    def get_rpg_core(self, bot):
        """Helper to get the RPGCore cog."""
        return bot.get_cog("RPGCore")

class ClassSelectionView(discord.ui.View):
    """Interactive class selection for new characters."""

    def __init__(self, user_id: str, rpg_core):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.rpg_core = rpg_core

    @discord.ui.select(
        placeholder="🎭 Choose your character class...",
        options=[
            discord.SelectOption(
                label="🛡️ Warrior",
                value="warrior",
                description="Tank • High defense and protective abilities",
                emoji="🛡️"
            ),
            discord.SelectOption(
                label="🔮 Mage", 
                value="mage",
                description="DPS • Magical damage with area effects",
                emoji="🔮"
            ),
            discord.SelectOption(
                label="🗡️ Rogue",
                value="rogue", 
                description="DPS • High critical hits and stealth",
                emoji="🗡️"
            ),
            discord.SelectOption(
                label="🏹 Archer",
                value="archer",
                description="DPS • Ranged precision striker",
                emoji="🏹"
            ),
            discord.SelectOption(
                label="❤️ Healer",
                value="healer",
                description="Support • Healing and team buffs",
                emoji="❤️"
            ),
            discord.SelectOption(
                label="⚔️ Battlemage",
                value="battlemage",
                description="Hybrid • Melee and magic fighter",
                emoji="⚔️"
            ),
            discord.SelectOption(
                label="⏰ Chrono Knight",
                value="chrono_knight",
                description="Hidden • Time manipulation specialist",
                emoji="⏰"
            )
        ]
    )
    async def class_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your character creation!", ephemeral=True)
            return

        selected_class = select.values[0]
        class_data = CLASSES[selected_class]

        # Create new character data
        new_character = {
            'level': 1,
            'xp': 0,
            'gold': 1000,
            'class': selected_class,
            'path': None,
            'name': interaction.user.display_name,
            'stats': {
                'strength': class_data['starting_stats']['strength'],
                'dexterity': class_data['starting_stats']['dexterity'],
                'constitution': class_data['starting_stats']['constitution'],
                'intelligence': class_data['starting_stats']['intelligence'],
                'wisdom': class_data['starting_stats']['wisdom'],
                'charisma': class_data['starting_stats']['charisma']
            },
            'resources': {
                'hp': class_data['base_hp'],
                'max_hp': class_data['base_hp'],
                'mana': class_data['base_mp'],
                'max_mana': class_data['base_mp'],
                'stamina': 100,
                'max_stamina': 100,
                'miraculous_energy': 100,
                'max_miraculous_energy': 100,
                'ultimate_energy': 0,
                'technique_points': 3
            },
            'derived_stats': {
                'attack': 10 + class_data['starting_stats']['strength'] * 2,
                'magic_attack': 10 + class_data['starting_stats']['intelligence'] * 2,
                'defense': 5 + class_data['starting_stats']['constitution'],
                'critical_chance': 0.05 + (class_data['starting_stats']['dexterity'] * 0.01),
                'dodge_chance': class_data['starting_stats']['dexterity'] * 0.005,
                'max_ultimate_energy': 100
            },
            'unallocated_points': 0,
            'equipment': {
                'weapon': None,
                'armor': None,
                'accessory': None,
                'artifact': None
            },
            'inventory': {
                'health_potion': 5,
                'mana_potion': 3
            },
            'skills': class_data['starting_skills'].copy(),
            'techniques': ['ambush'],
            'achievements': [],
            'arena_rating': 1000,
            'arena_wins': 0,
            'arena_losses': 0,
            'arena_tokens': 0,
            'faction': None,
            'title': None,
            'in_combat': False,
            'last_hunt': 0,
            'last_adventure': 0,
            'last_explore': 0,
            'last_work': 0,
            'created_at': datetime.now().isoformat(),
            'kwami_artifacts': [],
            'active_buffs': [],
            'chosen_path': None
        }

        # Save character data
        user_data = get_user_data(self.user_id) or {}
        user_data['rpg_data'] = new_character
        update_user_data(self.user_id, user_data)

        embed = discord.Embed(
            title="🎉 Character Created Successfully!",
            description=f"Welcome to your adventure as a **{class_data['name']}**!\n\n"
                       f"**{class_data['description']}**\n\n"
                       f"**Role:** {class_data['role']}\n"
                       f"**Starting Resources:**\n"
                       f"• Level 1 • 1,000 Gold\n"
                       f"• {class_data['base_hp']} HP • {class_data['base_mp']} MP\n"
                       f"• 5 Health Potions • 3 Mana Potions\n\n"
                       f"**Next Steps:**\n"
                       f"• Use `$profile` to view your character\n"
                       f"• Use `$battle` to start combat\n"
                       f"• Use `$help` for all commands",
            color=COLORS['success']
        )

        await interaction.response.edit_message(embed=embed, view=None)

class CombatEscapeView(discord.ui.View):
    """View to handle combat escape options."""

    def __init__(self, user_id: str, rpg_core):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.rpg_core = rpg_core

    @discord.ui.button(label="🏃 Force Exit Combat", style=discord.ButtonStyle.danger)
    async def force_exit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your combat!", ephemeral=True)
            return

        player_data = self.rpg_core.get_player_data(self.user_id)
        if player_data:
            player_data['in_combat'] = False
            player_data['resources']['ultimate_energy'] = 0
            # Small penalty for force exiting
            gold_lost = max(1, int(player_data.get('gold', 0) * 0.05))
            player_data['gold'] = max(0, player_data.get('gold', 0) - gold_lost)
            
            self.rpg_core.save_player_data(self.user_id, player_data)

            embed = discord.Embed(
                title="🏃 Forced Exit from Combat",
                description=f"You forcefully escaped from combat!\n\n"
                           f"**Penalty:** Lost {gold_lost} gold for fleeing.\n"
                           f"You can now use other RPG commands.",
                color=COLORS['warning']
            )
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            await interaction.response.send_message("❌ Player data not found!", ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_action(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your action!", ephemeral=True)
            return

        embed = discord.Embed(
            title="✅ Action Cancelled",
            description="Combat status unchanged. Finish your current battle to continue.",
            color=COLORS['secondary']
        )
        await interaction.response.edit_message(embed=embed, view=None)

class ProfileActionView(discord.ui.View):
    """Buttons for profile-related actions."""

    def __init__(self, target_id: str, requester_id: str):
        super().__init__(timeout=180)
        self.target_id = target_id
        self.requester_id = requester_id

    @discord.ui.button(label="Allocate Stats", style=discord.ButtonStyle.primary)
    async def allocate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.requester_id:
            await interaction.response.send_message("❌ This isn't your profile!", ephemeral=True)
            return

        await interaction.response.send_message("Coming soon! Stat allocation interface...", ephemeral=True)

    @discord.ui.button(label="View Inventory", style=discord.ButtonStyle.secondary)
    async def inventory_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.requester_id:
            await interaction.response.send_message("❌ This isn't your profile!", ephemeral=True)
            return

        await interaction.response.send_message("Coming soon! Inventory interface...", ephemeral=True)

class RPGCore(commands.Cog):
    """Core RPG functionality with proper data management."""

    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(StartRPGView())

    def get_player_data(self, user_id):
        """Get player RPG data safely."""
        user_data = get_user_data(str(user_id))
        if user_data and 'rpg_data' in user_data:
            player_data = user_data['rpg_data']

            # Safety check: ensure resources exist
            if 'resources' not in player_data:
                player_data['resources'] = {
                    'hp': 100,
                    'max_hp': 100,
                    'mana': 50,
                    'max_mana': 50,
                    'stamina': 100,
                    'max_stamina': 100,
                    'miraculous_energy': 100,
                    'max_miraculous_energy': 100,
                    'ultimate_energy': 0,
                    'technique_points': 3
                }
                self.save_player_data(user_id, player_data)

            return player_data
        return None

    def save_player_data(self, user_id, player_data):
        """Save player RPG data safely."""
        user_data = get_user_data(str(user_id)) or {}
        user_data['rpg_data'] = player_data
        update_user_data(str(user_id), user_data)

    def level_up_check(self, player_data):
        """Check and process level ups."""
        current_level = player_data['level']
        current_xp = player_data['xp']

        levels_gained = 0
        while current_xp >= self.calculate_level_xp_requirement(current_level + 1):
            current_level += 1
            levels_gained += 1

            # Give stat points
            player_data['unallocated_points'] = player_data.get('unallocated_points', 0) + 3

            # Heal on level up
            player_data['resources']['hp'] = player_data['resources']['max_hp']
            player_data['resources']['mana'] = player_data['resources']['max_mana']

        player_data['level'] = current_level
        return levels_gained

    def calculate_level_xp_requirement(self, level):
        """Calculate XP needed for a level."""
        return int(100 * (level ** 1.5))

    def is_player_in_combat(self, user_id):
        """Check if player is currently in combat."""
        player_data = self.get_player_data(user_id)
        if not player_data:
            return False
        return player_data.get('in_combat', False)

    @commands.command(name="startrpg", aliases=["start", "create"])
    async def start_rpg(self, ctx):
        """Start your RPG adventure with interactive class selection."""
        if not is_module_enabled("rpg", ctx.guild.id):
            return

        user_id = str(ctx.author.id)
        ensure_user_exists(user_id)

        # Check if player is in combat first
        if self.is_player_in_combat(user_id):
            embed = discord.Embed(
                title="⚔️ Already Fighting!",
                description="You're currently in combat! Finish your current battle first.",
                color=COLORS['warning']
            )
            view = CombatEscapeView(user_id, self)
            await ctx.send(embed=embed, view=view)
            return

        # Check if user already has a character
        player_data = self.get_player_data(user_id)
        if player_data:
            embed = discord.Embed(
                title="🎮 Adventure Already Started!",
                description=f"Welcome back, {ctx.author.mention}! Your adventure continues...\n\n"
                           f"**Current Character:**\n"
                           f"• **Class:** {CLASSES[player_data['class']]['name']}\n"
                           f"• **Level:** {player_data['level']}\n"
                           f"• **Gold:** {format_number(player_data['gold'])}\n"
                           f"• **HP:** {player_data['resources']['hp']}/{player_data['resources']['max_hp']}\n\n"
                           f"Use `$profile` to view your full character sheet!",
                color=COLORS['info']
            )
            await ctx.send(embed=embed)
            return

        # Create character creation embed
        embed = discord.Embed(
            title="🎭 Begin Your RPG Adventure",
            description="**Welcome to Project: Blood & Cheese!**\n\n"
                       "Choose your character class to start your epic journey!",
            color=COLORS['primary']
        )

        view = ClassSelectionView(user_id, self)
        await ctx.send(embed=embed, view=view)

    @commands.command(name='profile', aliases=['me', 'char'])
    async def profile(self, ctx, member: discord.Member = None):
        """View character profile and stats."""
        if not is_module_enabled("rpg", ctx.guild.id):
            return

        target = member or ctx.author
        player_data = self.get_player_data(target.id)

        if not player_data:
            if target == ctx.author:
                embed = discord.Embed(
                    title="🎮 No Character Found",
                    description="You need to create a character before you can view your profile!",
                    color=COLORS['info']
                )
                embed.add_field(
                    name="🌟 Getting Started",
                    value="Click the button below to create your character and begin your journey!",
                    inline=False
                )

                view = StartRPGView()
                await ctx.send(embed=embed, view=view)
            else:
                embed = create_embed("No Character", f"{target.display_name} hasn't started their RPG journey!", COLORS['error'])
                await ctx.send(embed=embed)
            return

        # Check for progression warnings
        progression_warning = warning_system.check_progression_warning(player_data, "level_check")

        # Create profile embed
        embed = discord.Embed(
            title=f"🎮 {target.display_name}'s Profile",
            color=COLORS['primary']
        )

        # Basic info
        embed.add_field(
            name="📊 Basic Info",
            value=f"**Class:** {CLASSES.get(player_data['class'], {}).get('name', player_data['class'].title())}\n"
                  f"**Level:** {player_data['level']}\n"
                  f"**XP:** {format_number(player_data['xp'])}\n"
                  f"**Gold:** {format_number(player_data['gold'])}",
            inline=True
        )

        # Resources
        resources = player_data['resources']
        embed.add_field(
            name="❤️ Resources",
            value=f"**HP:** {resources['hp']}/{resources['max_hp']}\n"
                  f"**MP:** {resources['mana']}/{resources['max_mana']}\n"
                  f"**Stamina:** {resources['stamina']}/{resources['max_stamina']}\n"
                  f"**Energy:** {resources['miraculous_energy']}/{resources['max_miraculous_energy']}",
            inline=True
        )

        # Stats
        stats = player_data['stats']
        embed.add_field(
            name="⚔️ Stats",
            value=f"**STR:** {stats['strength']}\n"
                  f"**DEX:** {stats['dexterity']}\n"
                  f"**CON:** {stats['constitution']}\n"
                  f"**INT:** {stats['intelligence']}\n"
                  f"**WIS:** {stats['wisdom']}\n"
                  f"**CHA:** {stats['charisma']}",
            inline=True
        )

        # Combat stats
        derived = player_data['derived_stats']
        embed.add_field(
            name="⚔️ Combat Stats",
            value=f"**Attack:** {derived['attack']}\n"
                  f"**Magic Attack:** {derived['magic_attack']}\n"
                  f"**Defense:** {derived['defense']}\n"
                  f"**Crit Chance:** {int(derived['critical_chance']*100)}%",
            inline=True
        )

        # PvP info
        embed.add_field(
            name="🏆 PvP Record",
            value=f"**Rating:** {player_data['arena_rating']}\n"
                  f"**Wins:** {player_data['arena_wins']}\n"
                  f"**Losses:** {player_data['arena_losses']}\n"
                  f"**Tokens:** {player_data['arena_tokens']}",
            inline=True
        )

        # Path info if available
        if player_data.get('chosen_path'):
            path_data = PATHS.get(player_data['chosen_path'], {})
            embed.add_field(
                name="🌟 Miraculous Path",
                value=f"**{path_data.get('name', 'Unknown')}**\n"
                      f"{path_data.get('description', 'No description')}",
                inline=False
            )

        embed.set_thumbnail(url=target.display_avatar.url)

        # Calculate last active time
        last_active_times = [player_data.get('last_hunt', 0),
                             player_data.get('last_adventure', 0),
                             player_data.get('last_explore', 0),
                             player_data.get('last_work', 0)]
        last_active = max(last_active_times) if last_active_times else 0
        if isinstance(last_active, (int, float)):
            last_active = datetime.now() - timedelta(seconds=last_active)
            last_active = last_active.strftime('%Y-%m-%d %H:%M:%S')
        else:
            last_active = "N/A"

        embed.set_footer(text=f"⏰ Last Active: {last_active}")

        # Add progression warning if exists
        if progression_warning and target == ctx.author:
            embed.add_field(
                name="💡 Helpful Suggestion",
                value=progression_warning['warnings'][0]['message'],
                inline=False
            )

        view = ProfileActionView(target.id, ctx.author.id) if target == ctx.author else None
        await ctx.send(embed=embed, view=view)

    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx, category: str = None):
        """View your inventory."""
        if not is_module_enabled("rpg", ctx.guild.id):
            return

        player_data = self.get_player_data(ctx.author.id)
        if not player_data:
            embed = create_embed("No Character", "Use `$startrpg` first!", COLORS['error'])
            await ctx.send(embed=embed)
            return

        inventory = player_data.get('inventory', {})

        if not inventory:
            embed = create_embed("Empty Inventory", "Your inventory is empty!", COLORS['warning'])
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"🎒 {ctx.author.display_name}'s Inventory",
            color=COLORS['primary']
        )

        # Group items by type
        weapons = []
        armor = []
        consumables = []
        accessories = []
        artifacts = []
        misc = []

        for item_key, quantity in inventory.items():
            if item_key in ITEMS:
                item_data = ITEMS[item_key]
                item_type = item_data.get('type', 'misc')
                item_name = item_data.get('name', item_key.replace('_', ' ').title())

                item_line = f"• **{item_name}** x{quantity}"

                if item_type == 'weapon':
                    weapons.append(item_line)
                elif item_type == 'armor':
                    armor.append(item_line)
                elif item_type == 'consumable':
                    consumables.append(item_line)
                elif item_type == 'accessory':
                    accessories.append(item_line)
                elif item_type == 'artifact':
                    artifacts.append(item_line)
                else:
                    misc.append(item_line)
            else:
                misc.append(f"• **{item_key.replace('_', ' ').title()}** x{quantity}")

        if weapons:
            embed.add_field(name="⚔️ Weapons", value="\n".join(weapons), inline=True)
        if armor:
            embed.add_field(name="🛡️ Armor", value="\n".join(armor), inline=True)
        if consumables:
            embed.add_field(name="🧪 Consumables", value="\n".join(consumables), inline=True)
        if accessories:
            embed.add_field(name="💎 Accessories", value="\n".join(accessories), inline=True)
        if artifacts:
            embed.add_field(name="✨ Artifacts", value="\n".join(artifacts), inline=True)
        if misc:
            embed.add_field(name="📦 Miscellaneous", value="\n".join(misc), inline=True)

        embed.set_footer(text="Use $equip <item> to equip gear or $use <item> for consumables")
        await ctx.send(embed=embed)

    @commands.command(name="combatstatus", aliases=["cs"])
    async def combat_status(self, ctx):
        """Check your current combat status."""
        if not is_module_enabled("rpg", ctx.guild.id):
            return

        player_data = self.get_player_data(ctx.author.id)
        if not player_data:
            embed = create_embed("No Character", "Use `$startrpg` first!", COLORS['error'])
            await ctx.send(embed=embed)
            return

        in_combat = player_data.get('in_combat', False)
        
        if in_combat:
            embed = discord.Embed(
                title="⚔️ Combat Status",
                description="You are currently **IN COMBAT**.",
                color=COLORS['error']
            )
            embed.add_field(
                name="Options",
                value="• Wait for combat to end naturally\n• Use the Force Exit button if needed",
                inline=False
            )
            view = CombatEscapeView(str(ctx.author.id), self)
            await ctx.send(embed=embed, view=view)
        else:
            embed = discord.Embed(
                title="✅ Combat Status",
                description="You are **NOT IN COMBAT**.\nFree to use all RPG commands!",
                color=COLORS['success']
            )
            await ctx.send(embed=embed)

    @commands.command(name="allocate", aliases=["alloc"])
    async def allocate_stats(self, ctx, stat: str, points: int = 1):
        """Allocate stat points to improve your character."""
        if not is_module_enabled("rpg", ctx.guild.id):
            return

        player_data = self.get_player_data(ctx.author.id)
        if not player_data:
            embed = discord.Embed(
                title="🎮 No Character Found",
                description="You need to create a character before you can allocate stats!",
                color=COLORS['info']
            )
            embed.add_field(
                name="🌟 Getting Started",
                value="Click the button below to create your character and begin your journey!",
                inline=False
            )

            view = StartRPGView()
            await ctx.send(embed=embed, view=view)
            return

        # Validate stat name
        valid_stats = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        if stat.lower() not in valid_stats:
            embed = create_embed("Invalid Stat", f"Valid stats: {', '.join(valid_stats)}", COLORS['error'])
            await ctx.send(embed=embed)
            return

        # Check for stat allocation warnings
        warning_result = warning_system.check_stat_allocation_warning(player_data, stat.lower(), points)
        if warning_result and warning_result['severity'] in ['error']:
            # Block if it's an error-level warning
            await ctx.send(embed=warning_result['embed'])
            return
        elif warning_result:
            # Show warning but allow continuation
            warning_embed = warning_result['embed']
            warning_embed.add_field(
                name="⚡ Continue Anyway?",
                value="React with ✅ to proceed or ❌ to cancel.",
                inline=False
            )

            warning_msg = await ctx.send(embed=warning_embed)
            await warning_msg.add_reaction("✅")
            await warning_msg.add_reaction("❌")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message == warning_msg

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                if str(reaction.emoji) == "❌":
                    await warning_msg.edit(embed=create_embed("Cancelled", "Stat allocation cancelled.", COLORS['secondary']))
                    return
                await warning_msg.delete()
            except asyncio.TimeoutError:
                await warning_msg.edit(embed=create_embed("Timeout", "Stat allocation cancelled due to timeout.", COLORS['secondary']))
                return

        # Check available points
        if player_data['unallocated_points'] < points:
            embed = create_embed("Not Enough Points", f"You only have {player_data['unallocated_points']} unallocated points.", COLORS['error'])
            await ctx.send(embed=embed)
            return

        # Allocate stat points
        player_data['stats'][stat.lower()] += points
        player_data['unallocated_points'] -= points
        self.save_player_data(ctx.author.id, player_data)

        embed = create_embed("Stats Allocated", f"Successfully allocated {points} points to {stat.title()}.", COLORS['success'])
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(RPGCore(bot))