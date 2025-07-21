import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
from replit import db
from config import COLORS, EMOJIS, is_module_enabled
from utils.database import get_user_data, update_user_data, ensure_user_exists, create_user_profile, get_user_rpg_data, update_user_rpg_data, get_guild_data, update_guild_data, create_guild_profile, get_leaderboard
from utils.helpers import create_embed, format_number, create_progress_bar, level_up_player, get_random_adventure_outcome, get_time_until_next_use, format_time_remaining, calculate_battle_damage, generate_random_stats
from utils.rng_system import roll_with_luck, check_rare_event, get_luck_status, generate_loot_with_luck, weighted_random_choice
from utils.constants import RPG_CONSTANTS, MONSTERS, ADVENTURE_LOCATIONS, DUNGEON_TYPES, CRAFTING_RECIPES, GUILD_PERKS, ACHIEVEMENTS, STATUS_EFFECTS, PVP_ARENAS

logger = logging.getLogger(__name__)

class RPGProfileView(discord.ui.View):
    """Interactive view for RPG profile."""

    def __init__(self, user, player_data):
        super().__init__(timeout=300)
        self.user = user
        self.player_data = player_data
        self.current_page = "stats"

    @discord.ui.button(label="📊 Stats", style=discord.ButtonStyle.primary)
    async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show player stats."""
        if interaction.user != self.user:
            await interaction.response.send_message("This is not your profile!", ephemeral=True)
            return

        self.current_page = "stats"
        embed = self.create_stats_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🎒 Inventory", style=discord.ButtonStyle.secondary)
    async def inventory_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show player inventory."""
        if interaction.user != self.user:
            await interaction.response.send_message("This is not your profile!", ephemeral=True)
            return

        self.current_page = "inventory"
        embed = self.create_inventory_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🎯 Skills", style=discord.ButtonStyle.success)
    async def skills_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show player skills."""
        if interaction.user != self.user:
            await interaction.response.send_message("This is not your profile!", ephemeral=True)
            return

        self.current_page = "skills"
        embed = self.create_skills_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🏆 Achievements", style=discord.ButtonStyle.danger)
    async def achievements_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show player achievements."""
        if interaction.user != self.user:
            await interaction.response.send_message("This is not your profile!", ephemeral=True)
            return

        self.current_page = "achievements"
        embed = self.create_achievements_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🍀 Luck", style=discord.ButtonStyle.success)
    async def luck_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show player luck status."""
        if interaction.user != self.user:
            await interaction.response.send_message("This is not your profile!", ephemeral=True)
            return

        self.current_page = "luck"
        embed = self.create_luck_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def create_stats_embed(self):
        """Create stats embed."""
        try:
            xp_progress = (self.player_data['xp'] / self.player_data['max_xp']) * 100
            progress_bar = create_progress_bar(xp_progress)

            embed = discord.Embed(
                title=f"{EMOJIS['profile']} {self.user.display_name}'s Profile",
                description=f"**Level {self.player_data['level']} Adventurer**",
                color=COLORS['primary']
            )
            embed.set_thumbnail(url=self.user.display_avatar.url)

            # Core Stats
            embed.add_field(
                name="📊 Core Stats",
                value=f"**{EMOJIS['level']} Level:** {self.player_data['level']}\n"
                      f"**{EMOJIS['xp']} XP:** {self.player_data['xp']}/{self.player_data['max_xp']}\n"
                      f"{progress_bar}\n"
                      f"**{EMOJIS['hp']} HP:** {self.player_data['hp']}/{self.player_data['max_hp']}\n"
                      f"**{EMOJIS['attack']} Attack:** {self.player_data['attack']}\n"
                      f"**{EMOJIS['defense']} Defense:** {self.player_data['defense']}",
                inline=True
            )

            # Economy & Progress
            embed.add_field(
                name="💰 Economy & Progress",
                value=f"**{EMOJIS['coins']} Coins:** {format_number(self.player_data['coins'])}\n"
                      f"**🎯 Adventures:** {self.player_data.get('adventure_count', 0)}\n"
                      f"**🏰 Dungeons:** {self.player_data.get('dungeon_count', 0)}\n"
                      f"**🎒 Items:** {len(self.player_data.get('inventory', []))}",
                inline=True
            )

            # Equipment
            weapon = self.player_data.get('equipped', {}).get('weapon', 'None')
            armor = self.player_data.get('equipped', {}).get('armor', 'None')
            accessory = self.player_data.get('equipped', {}).get('accessory', 'None')
            
            embed.add_field(
                name="🎯 Equipment",
                value=f"**⚔️ Weapon:** {weapon}\n"
                      f"**🛡️ Armor:** {armor}\n"
                      f"**💍 Accessory:** {accessory}",
                inline=True
            )

            # Status Effects
            status_effects = self.player_data.get('status_effects', [])
            if status_effects:
                effects_text = "\n".join([f"{STATUS_EFFECTS[effect]['emoji']} {effect.title()}" for effect in status_effects])
                embed.add_field(
                    name="⚡ Status Effects",
                    value=effects_text,
                    inline=False
                )

            embed.set_footer(text="Use the buttons below to navigate different sections")
            return embed
        except Exception as e:
            logger.error(f"Error creating stats embed: {e}")
            return create_embed("Error", "Failed to create stats embed.", COLORS['error'])

    def create_inventory_embed(self):
        """Create inventory embed."""
        try:
            embed = discord.Embed(
                title=f"{EMOJIS['inventory']} {self.user.display_name}'s Inventory",
                color=COLORS['secondary']
            )
            embed.set_thumbnail(url=self.user.display_avatar.url)

            inventory = self.player_data.get('inventory', [])

            if not inventory:
                embed.description = "Your inventory is empty! Go on adventures to find items."
            else:
                # Group items by type
                item_groups = {
                    'weapons': [],
                    'armor': [],
                    'consumables': [],
                    'accessories': [],
                    'materials': []
                }

                for item in inventory:
                    item_type = self.get_item_type(item)
                    if item_type in item_groups:
                        item_groups[item_type].append(item)
                    else:
                        item_groups['materials'].append(item)

                # Display grouped items
                for item_type, items in item_groups.items():
                    if not items:
                        continue
                        
                    item_counts = {}
                    for item in items:
                        item_counts[item] = item_counts.get(item, 0) + 1

                    item_list = []
                    for item, count in item_counts.items():
                        if count > 1:
                            item_list.append(f"{item} x{count}")
                        else:
                            item_list.append(item)

                    if item_list:
                        embed.add_field(
                            name=f"{self.get_item_emoji(item_type)} {item_type.title()}",
                            value="\n".join(item_list),
                            inline=True
                        )

            embed.set_footer(text="Use $use <item> to use items | $equip <item> to equip weapons/armor")
            return embed
        except Exception as e:
            logger.error(f"Error creating inventory embed: {e}")
            return create_embed("Error", "Failed to create inventory embed.", COLORS['error'])

    def create_skills_embed(self):
        """Create skills embed."""
        try:
            embed = discord.Embed(
                title=f"{EMOJIS['skills']} {self.user.display_name}'s Skills",
                color=COLORS['info']
            )
            embed.set_thumbnail(url=self.user.display_avatar.url)

            level = self.player_data['level']
            stats = self.player_data.get('stats', {})

            # Calculate skill levels based on player activities
            combat_skill = min(level + self.player_data.get('dungeon_count', 0) // 3, 100)
            exploration_skill = min(level + self.player_data.get('adventure_count', 0) // 5, 100)
            trading_skill = min(level + (self.player_data.get('coins', 0) // 5000), 100)
            crafting_skill = min(level + len(self.player_data.get('crafted_items', [])), 100)

            embed.add_field(
                name="⚔️ Combat",
                value=f"Level {combat_skill}\n{create_progress_bar(combat_skill)}\n"
                      f"Battles Won: {stats.get('battles_won', 0)}",
                inline=True
            )

            embed.add_field(
                name="🗺️ Exploration",
                value=f"Level {exploration_skill}\n{create_progress_bar(exploration_skill)}\n"
                      f"Adventures: {self.player_data.get('adventure_count', 0)}",
                inline=True
            )

            embed.add_field(
                name="💰 Trading",
                value=f"Level {trading_skill}\n{create_progress_bar(trading_skill)}\n"
                      f"Coins Earned: {format_number(stats.get('total_coins_earned', 0))}",
                inline=True
            )

            embed.add_field(
                name="🔨 Crafting",
                value=f"Level {crafting_skill}\n{create_progress_bar(crafting_skill)}\n"
                      f"Items Crafted: {len(self.player_data.get('crafted_items', []))}",
                inline=True
            )

            embed.set_footer(text="Skills improve as you play and gain experience")
            return embed
        except Exception as e:
            logger.error(f"Error creating skills embed: {e}")
            return create_embed("Error", "Failed to create skills embed.", COLORS['error'])

    def create_achievements_embed(self):
        """Create achievements embed."""
        try:
            embed = discord.Embed(
                title=f"🏆 {self.user.display_name}'s Achievements",
                color=COLORS['warning']
            )
            embed.set_thumbnail(url=self.user.display_avatar.url)

            user_achievements = self.player_data.get('achievements', [])
            
            if not user_achievements:
                embed.description = "No achievements yet. Start your adventure to unlock them!"
            else:
                achievement_list = []
                for achievement in user_achievements:
                    if achievement in ACHIEVEMENTS:
                        achievement_list.append(f"🏆 {ACHIEVEMENTS[achievement]['description']}")
                    else:
                        achievement_list.append(f"🏆 {achievement}")
                
                embed.description = "\n".join(achievement_list)

            # Show available achievements
            available_achievements = []
            for ach_name, ach_data in ACHIEVEMENTS.items():
                if ach_name not in user_achievements:
                    if self.check_achievement_requirement(ach_name, ach_data):
                        available_achievements.append(f"✨ {ach_data['description']} (Ready!)")
                    else:
                        available_achievements.append(f"⏳ {ach_data['description']}")

            if available_achievements:
                embed.add_field(
                    name="🎯 Available Achievements",
                    value="\n".join(available_achievements[:5]),  # Show first 5
                    inline=False
                )

            embed.set_footer(text="Complete activities to unlock achievements!")
            return embed
        except Exception as e:
            logger.error(f"Error creating achievements embed: {e}")
            return create_embed("Error", "Failed to create achievements embed.", COLORS['error'])

    def create_luck_embed(self):
        """Create luck status embed."""
        try:
            luck_status = get_luck_status(str(self.user.id))
            
            embed = discord.Embed(
                title=f"🍀 {self.user.display_name}'s Luck Status",
                color=COLORS['info']
            )
            
            # Luck tier with emoji
            luck_emojis = {
                "cursed": "💀",
                "unlucky": "😰",
                "normal": "😐",
                "lucky": "😊",
                "blessed": "✨",
                "divine": "🌟"
            }
            
            luck_emoji = luck_emojis.get(luck_status['luck_tier'], "🍀")
            
            embed.add_field(
                name="🎲 Current Luck",
                value=f"{luck_emoji} **{luck_status['luck_tier'].title()}**\n"
                      f"Luck Value: {luck_status['current_luck']}/100\n"
                      f"Multiplier: {luck_status['luck_multiplier']:.2f}x\n"
                      f"Lucky Streak: {luck_status['lucky_streak']}",
                inline=True
            )
            
            embed.add_field(
                name="📊 Statistics",
                value=f"Total Rolls: {luck_status['total_rolls']}\n"
                      f"Success Rate: {luck_status['success_rate']:.1f}%\n"
                      f"Unlucky Streak: {luck_status['unlucky_streak']}",
                inline=True
            )
            
            # Active conditions
            if luck_status['active_conditions']:
                embed.add_field(
                    name="⚡ Active Conditions",
                    value="\n".join(luck_status['active_conditions']),
                    inline=False
                )
            
            embed.set_footer(text="Luck affects all RNG-based activities!")
            return embed
        except Exception as e:
            logger.error(f"Error creating luck embed: {e}")
            return create_embed("Error", "Failed to create luck embed.", COLORS['error'])

    def get_item_type(self, item_name: str) -> str:
        """Get item type from name."""
        from utils.constants import SHOP_ITEMS
        
        for category, items in SHOP_ITEMS.items():
            if item_name in items:
                return category
        
        # Default categories for special items
        if any(word in item_name.lower() for word in ['sword', 'blade', 'bow', 'staff']):
            return 'weapons'
        elif any(word in item_name.lower() for word in ['armor', 'shield', 'helmet']):
            return 'armor'
        elif any(word in item_name.lower() for word in ['potion', 'elixir', 'scroll']):
            return 'consumables'
        elif any(word in item_name.lower() for word in ['ring', 'amulet', 'cloak']):
            return 'accessories'
        else:
            return 'materials'

    def get_item_emoji(self, item_type: str) -> str:
        """Get emoji for item type."""
        emojis = {
            'weapons': '⚔️',
            'armor': '🛡️',
            'consumables': '🧪',
            'accessories': '💍',
            'materials': '🔨'
        }
        return emojis.get(item_type, '📦')

    def check_achievement_requirement(self, achievement_name: str, achievement_data: Dict[str, Any]) -> bool:
        """Check if player meets achievement requirement."""
        requirement = achievement_data['requirement']
        required_value = achievement_data['value']
        
        if requirement == 'level':
            return self.player_data['level'] >= required_value
        elif requirement == 'coins':
            return self.player_data['coins'] >= required_value
        elif requirement == 'adventures_completed':
            return self.player_data.get('adventure_count', 0) >= required_value
        elif requirement == 'dungeons_completed':
            return self.player_data.get('dungeon_count', 0) >= required_value
        elif requirement == 'battles_won':
            return self.player_data.get('stats', {}).get('battles_won', 0) >= required_value
        
        return False

class BattleView(discord.ui.View):
    """Interactive battle view."""
    
    def __init__(self, ctx, player_data, enemy_data, battle_type="monster"):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.player_data = player_data
        self.enemy_data = enemy_data
        self.battle_type = battle_type
        self.battle_log = []
        
    @discord.ui.button(label="⚔️ Attack", style=discord.ButtonStyle.danger)
    async def attack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Attack the enemy."""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This is not your battle!", ephemeral=True)
            return
            
        # Player attacks
        player_damage = calculate_battle_damage(self.player_data, self.enemy_data)
        
        # Check for critical hit
        from utils.rng_system import calculate_critical_chance
        crit_chance = calculate_critical_chance(str(self.ctx.author.id))
        
        if roll_with_luck(str(self.ctx.author.id), crit_chance):
            player_damage = int(player_damage * 1.5)
            self.battle_log.append(f"💥 Critical hit! You deal {player_damage} damage!")
        else:
            self.battle_log.append(f"⚔️ You attack for {player_damage} damage!")
            
        self.enemy_data['hp'] -= player_damage
        
        # Check if enemy is defeated
        if self.enemy_data['hp'] <= 0:
            await self.end_battle(interaction, victory=True)
            return
            
        # Enemy attacks back
        enemy_damage = calculate_battle_damage(self.enemy_data, self.player_data)
        self.battle_log.append(f"🔴 {self.enemy_data.get('name', 'Enemy')} attacks for {enemy_damage} damage!")
        
        self.player_data['hp'] -= enemy_damage
        
        # Check if player is defeated
        if self.player_data['hp'] <= 0:
            await self.end_battle(interaction, victory=False)
            return
            
        # Update battle embed
        embed = self.create_battle_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        
    @discord.ui.button(label="🛡️ Defend", style=discord.ButtonStyle.secondary)
    async def defend_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Defend against enemy attack."""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This is not your battle!", ephemeral=True)
            return
            
        # Player defends - reduce incoming damage by 50%
        enemy_damage = calculate_battle_damage(self.enemy_data, self.player_data)
        reduced_damage = max(1, enemy_damage // 2)
        
        self.battle_log.append(f"🛡️ You defend! Damage reduced from {enemy_damage} to {reduced_damage}!")
        self.player_data['hp'] -= reduced_damage
        
        # Check if player is defeated
        if self.player_data['hp'] <= 0:
            await self.end_battle(interaction, victory=False)
            return
            
        # Update battle embed
        embed = self.create_battle_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        
    @discord.ui.button(label="🧪 Use Item", style=discord.ButtonStyle.success)
    async def use_item_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Use an item in battle."""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This is not your battle!", ephemeral=True)
            return
            
        # Find health potions in inventory
        health_potions = [item for item in self.player_data.get('inventory', []) if 'Potion' in item]
        
        if not health_potions:
            await interaction.response.send_message("You have no usable items!", ephemeral=True)
            return
            
        # Use first health potion
        potion = health_potions[0]
        self.player_data['inventory'].remove(potion)
        
        # Heal player
        heal_amount = 30  # Basic heal amount
        self.player_data['hp'] = min(self.player_data['max_hp'], self.player_data['hp'] + heal_amount)
        
        self.battle_log.append(f"🧪 You used {potion} and healed {heal_amount} HP!")
        
        # Enemy attacks
        enemy_damage = calculate_battle_damage(self.enemy_data, self.player_data)
        self.battle_log.append(f"🔴 {self.enemy_data.get('name', 'Enemy')} attacks for {enemy_damage} damage!")
        
        self.player_data['hp'] -= enemy_damage
        
        # Check if player is defeated
        if self.player_data['hp'] <= 0:
            await self.end_battle(interaction, victory=False)
            return
            
        # Update battle embed
        embed = self.create_battle_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        
    @discord.ui.button(label="🏃 Flee", style=discord.ButtonStyle.secondary)
    async def flee_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Flee from battle."""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This is not your battle!", ephemeral=True)
            return
            
        # 70% chance to flee successfully
        if roll_with_luck(str(self.ctx.author.id), 0.7):
            embed = discord.Embed(
                title="🏃 Fled Successfully!",
                description="You managed to escape from battle!",
                color=COLORS['warning']
            )
            
            # Remove all buttons
            for item in self.children:
                item.disabled = True
                
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            # Failed to flee, enemy gets a free attack
            enemy_damage = calculate_battle_damage(self.enemy_data, self.player_data)
            self.battle_log.append(f"❌ Failed to flee! {self.enemy_data.get('name', 'Enemy')} attacks for {enemy_damage} damage!")
            
            self.player_data['hp'] -= enemy_damage
            
            # Check if player is defeated
            if self.player_data['hp'] <= 0:
                await self.end_battle(interaction, victory=False)
                return
                
            # Update battle embed
            embed = self.create_battle_embed()
            await interaction.response.edit_message(embed=embed, view=self)
            
    async def end_battle(self, interaction: discord.Interaction, victory: bool):
        """End the battle."""
        # Disable all buttons
        for item in self.children:
            item.disabled = True
            
        if victory:
            # Calculate rewards
            base_xp = self.enemy_data.get('xp', 50)
            base_coins = self.enemy_data.get('coins', 100)
            
            # Apply luck to rewards
            loot = generate_loot_with_luck(str(self.ctx.author.id), {
                'xp': base_xp,
                'coins': base_coins
            })
            
            xp_gained = loot['xp']
            coins_gained = loot['coins']
            
            # Update player data
            self.player_data['xp'] += xp_gained
            self.player_data['coins'] += coins_gained
            
            # Update stats
            if 'stats' not in self.player_data:
                self.player_data['stats'] = {}
            self.player_data['stats']['battles_won'] = self.player_data['stats'].get('battles_won', 0) + 1
            
            # Check for level up
            level_up_msg = level_up_player(self.player_data)
            
            # Save player data
            update_user_rpg_data(str(self.ctx.author.id), self.player_data)
            
            embed = discord.Embed(
                title="🎉 Victory!",
                description=f"You defeated the {self.enemy_data.get('name', 'enemy')}!\n\n"
                           f"**Rewards:**\n"
                           f"⭐ {xp_gained} XP\n"
                           f"💰 {coins_gained} coins",
                color=COLORS['success']
            )
            
            if level_up_msg:
                embed.add_field(name="🎉 Level Up!", value=level_up_msg, inline=False)
                
        else:
            # Player defeated
            self.player_data['hp'] = 1  # Don't let HP go below 1
            
            # Update stats
            if 'stats' not in self.player_data:
                self.player_data['stats'] = {}
            self.player_data['stats']['battles_lost'] = self.player_data['stats'].get('battles_lost', 0) + 1
            
            # Save player data
            update_user_rpg_data(str(self.ctx.author.id), self.player_data)
            
            embed = discord.Embed(
                title="💀 Defeat!",
                description=f"You were defeated by the {self.enemy_data.get('name', 'enemy')}!\n\n"
                           f"Better luck next time!",
                color=COLORS['error']
            )
            
        await interaction.response.edit_message(embed=embed, view=self)
        
    def create_battle_embed(self) -> discord.Embed:
        """Create battle status embed."""
        embed = discord.Embed(
            title=f"⚔️ Battle: {self.ctx.author.display_name} vs {self.enemy_data.get('name', 'Enemy')}",
            color=COLORS['warning']
        )
        
        # Player stats
        player_hp_bar = create_progress_bar((self.player_data['hp'] / self.player_data['max_hp']) * 100)
        embed.add_field(
            name=f"👤 {self.ctx.author.display_name}",
            value=f"❤️ {self.player_data['hp']}/{self.player_data['max_hp']} HP\n{player_hp_bar}\n"
                  f"⚔️ {self.player_data['attack']} ATK | 🛡️ {self.player_data['defense']} DEF",
            inline=True
        )
        
        # Enemy stats
        enemy_hp_bar = create_progress_bar((self.enemy_data['hp'] / self.enemy_data['max_hp']) * 100)
        embed.add_field(
            name=f"👹 {self.enemy_data.get('name', 'Enemy')}",
            value=f"❤️ {self.enemy_data['hp']}/{self.enemy_data['max_hp']} HP\n{enemy_hp_bar}\n"
                  f"⚔️ {self.enemy_data['attack']} ATK | 🛡️ {self.enemy_data['defense']} DEF",
            inline=True
        )
        
        # Battle log
        if self.battle_log:
            embed.add_field(
                name="📜 Battle Log",
                value="\n".join(self.battle_log[-3:]),  # Show last 3 actions
                inline=False
            )
            
        return embed

class DungeonView(discord.ui.View):
    """Interactive dungeon exploration view."""
    
    def __init__(self, ctx, player_data, dungeon_data):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player_data = player_data
        self.dungeon_data = dungeon_data
        self.current_floor = 1
        self.rooms_explored = 0
        
    @discord.ui.button(label="🚪 Next Room", style=discord.ButtonStyle.primary)
    async def next_room_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Explore the next room."""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This is not your dungeon!", ephemeral=True)
            return
            
        self.rooms_explored += 1
        
        # Random encounter
        encounter_type = weighted_random_choice([
            {'type': 'monster', 'weight': 40},
            {'type': 'treasure', 'weight': 25},
            {'type': 'trap', 'weight': 20},
            {'type': 'empty', 'weight': 15}
        ], str(self.ctx.author.id), 'weight')
        
        embed = self.create_dungeon_embed()
        
        if encounter_type['type'] == 'monster':
            # Monster encounter
            monster_name = random.choice(list(MONSTERS.keys()))
            monster_data = MONSTERS[monster_name].copy()
            monster_data['name'] = monster_name
            monster_data['max_hp'] = monster_data['hp']
            
            embed.add_field(
                name="👹 Monster Encounter!",
                value=f"You encounter a {monster_name}!\nPrepare for battle!",
                inline=False
            )
            
            # Start battle
            battle_view = BattleView(self.ctx, self.player_data, monster_data)
            await interaction.response.edit_message(embed=embed, view=battle_view)
            return
            
        elif encounter_type['type'] == 'treasure':
            # Treasure room
            treasure_coins = random.randint(50, 200)
            treasure_xp = random.randint(20, 50)
            
            loot = generate_loot_with_luck(str(self.ctx.author.id), {
                'coins': treasure_coins,
                'xp': treasure_xp
            })
            
            self.player_data['coins'] += loot['coins']
            self.player_data['xp'] += loot['xp']
            
            embed.add_field(
                name="💰 Treasure Found!",
                value=f"You found {loot['coins']} coins and gained {loot['xp']} XP!",
                inline=False
            )
            
        elif encounter_type['type'] == 'trap':
            # Trap room
            if roll_with_luck(str(self.ctx.author.id), 0.6):  # 60% chance to avoid
                embed.add_field(
                    name="🕳️ Trap Avoided!",
                    value="You skillfully avoided a hidden trap!",
                    inline=False
                )
            else:
                trap_damage = random.randint(10, 30)
                self.player_data['hp'] -= trap_damage
                embed.add_field(
                    name="🕳️ Trap Triggered!",
                    value=f"You triggered a trap and took {trap_damage} damage!",
                    inline=False
                )
                
        else:
            # Empty room
            embed.add_field(
                name="🕳️ Empty Room",
                value="This room is empty. You rest for a moment and recover some HP.",
                inline=False
            )
            
            # Small heal
            heal_amount = random.randint(5, 15)
            self.player_data['hp'] = min(self.player_data['max_hp'], self.player_data['hp'] + heal_amount)
            
        # Check if player died
        if self.player_data['hp'] <= 0:
            embed.add_field(
                name="💀 Dungeon Failed!",
                value="You have been defeated in the dungeon!",
                inline=False
            )
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
                
            self.player_data['hp'] = 1  # Don't let HP go below 1
            update_user_rpg_data(str(self.ctx.author.id), self.player_data)
            
            await interaction.response.edit_message(embed=embed, view=self)
            return
            
        # Check if dungeon is complete
        if self.rooms_explored >= self.dungeon_data['floors'] * 3:  # 3 rooms per floor
            await self.complete_dungeon(interaction)
            return
            
        # Move to next floor if needed
        if self.rooms_explored % 3 == 0:
            self.current_floor += 1
            
        await interaction.response.edit_message(embed=embed, view=self)
        
    @discord.ui.button(label="🏃 Exit Dungeon", style=discord.ButtonStyle.danger)
    async def exit_dungeon_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Exit the dungeon early."""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This is not your dungeon!", ephemeral=True)
            return
            
        # Disable all buttons
        for item in self.children:
            item.disabled = True
            
        # Save player data
        update_user_rpg_data(str(self.ctx.author.id), self.player_data)
        
        embed = discord.Embed(
            title="🚪 Exited Dungeon",
            description=f"You exited the dungeon on floor {self.current_floor}.\n"
                       f"Rooms explored: {self.rooms_explored}",
            color=COLORS['warning']
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
        
    async def complete_dungeon(self, interaction: discord.Interaction):
        """Complete the dungeon."""
        # Disable all buttons
        for item in self.children:
            item.disabled = True
            
        # Calculate completion rewards
        base_rewards = self.dungeon_data['rewards']
        coins_reward = random.randint(base_rewards['coins'][0], base_rewards['coins'][1])
        xp_reward = random.randint(base_rewards['xp'][0], base_rewards['xp'][1])
        
        # Apply luck to rewards
        loot = generate_loot_with_luck(str(self.ctx.author.id), {
            'coins': coins_reward,
            'xp': xp_reward
        })
        
        # Update player data
        self.player_data['coins'] += loot['coins']
        self.player_data['xp'] += loot['xp']
        self.player_data['dungeon_count'] = self.player_data.get('dungeon_count', 0) + 1
        
        # Update stats
        if 'stats' not in self.player_data:
            self.player_data['stats'] = {}
        self.player_data['stats']['dungeons_completed'] = self.player_data['stats'].get('dungeons_completed', 0) + 1
        
        # Check for level up
        level_up_msg = level_up_player(self.player_data)
        
        # Save player data
        update_user_rpg_data(str(self.ctx.author.id), self.player_data)
        
        embed = discord.Embed(
            title="🎉 Dungeon Completed!",
            description=f"You successfully completed the {self.dungeon_data['boss']}!\n\n"
                       f"**Rewards:**\n"
                       f"⭐ {loot['xp']} XP\n"
                       f"💰 {loot['coins']} coins",
            color=COLORS['success']
        )
        
        if level_up_msg:
            embed.add_field(name="🎉 Level Up!", value=level_up_msg, inline=False)
            
        await interaction.response.edit_message(embed=embed, view=self)
        
    def create_dungeon_embed(self) -> discord.Embed:
        """Create dungeon status embed."""
        embed = discord.Embed(
            title=f"🏰 {self.dungeon_data['boss']} - Floor {self.current_floor}",
            description=self.dungeon_data['description'],
            color=COLORS['dark']
        )
        
        # Player status
        hp_bar = create_progress_bar((self.player_data['hp'] / self.player_data['max_hp']) * 100)
        embed.add_field(
            name="👤 Player Status",
            value=f"❤️ {self.player_data['hp']}/{self.player_data['max_hp']} HP\n{hp_bar}",
            inline=True
        )
        
        # Dungeon progress
        progress = (self.rooms_explored / (self.dungeon_data['floors'] * 3)) * 100
        progress_bar = create_progress_bar(progress)
        embed.add_field(
            name="🏰 Dungeon Progress",
            value=f"Rooms: {self.rooms_explored}/{self.dungeon_data['floors'] * 3}\n{progress_bar}",
            inline=True
        )
        
        return embed

class RPGGamesCog(commands.Cog):
    """Enhanced RPG games with interactive features."""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_battles = {}  # user_id -> battle_data
        self.active_dungeons = {}  # user_id -> dungeon_data
        
    @commands.command(name='start', help='Start your RPG adventure')
    async def start_adventure(self, ctx):
        """Start the RPG adventure."""
        if not is_module_enabled("rpg_games", ctx.guild.id):
            return
            
        user_id = str(ctx.author.id)
        
        # Check if user already exists
        if ensure_user_exists(user_id):
            user_data = get_user_data(user_id)
            if user_data:
                embed = discord.Embed(
                    title="🎮 Adventure Already Started!",
                    description=f"Welcome back, {ctx.author.mention}! Your adventure continues...\n\n"
                               f"**Current Stats:**\n"
                               f"Level: {user_data['rpg_data']['level']}\n"
                               f"HP: {user_data['rpg_data']['hp']}/{user_data['rpg_data']['max_hp']}\n"
                               f"Coins: {format_number(user_data['rpg_data']['coins'])}\n\n"
                               f"Use `$profile` to see your full stats!",
                    color=COLORS['info']
                )
                await ctx.send(embed=embed)
                return
                
        # Create new user profile
        user_data = create_user_profile(user_id)
        if update_user_data(user_id, user_data):
            embed = discord.Embed(
                title="🎉 Adventure Started!",
                description=f"Welcome to the adventure, {ctx.author.mention}!\n\n"
                           f"**Starting Stats:**\n"
                           f"Level: 1\n"
                           f"HP: 100/100\n"
                           f"Attack: 10\n"
                           f"Defense: 5\n"
                           f"Coins: 100\n\n"
                           f"**Commands to get started:**\n"
                           f"• `$profile` - View your character\n"
                           f"• `$adventure` - Go on adventures\n"
                           f"• `$work` - Earn coins\n"
                           f"• `$shop` - Buy equipment\n"
                           f"• `$help` - See all commands",
                color=COLORS['success']
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to start your adventure. Please try again.",
                color=COLORS['error']
            )
            await ctx.send(embed=embed)
            
    @commands.command(name='profile', help='View your RPG profile')
    async def view_profile(self, ctx, member: discord.Member = None):
        """View RPG profile."""
        if not is_module_enabled("rpg_games", ctx.guild.id):
            return
            
        target_user = member or ctx.author
        user_id = str(target_user.id)
        
        if not ensure_user_exists(user_id):
            if target_user == ctx.author:
                await ctx.send("❌ You need to `$start` your adventure first!")
            else:
                await ctx.send(f"❌ {target_user.mention} hasn't started their adventure yet!")
            return
            
        player_data = get_user_rpg_data(user_id)
        if not player_data:
            await ctx.send("❌ Error retrieving player data. Please try again.")
            return
            
        # Create interactive profile view
        view = RPGProfileView(target_user, player_data)
        embed = view.create_stats_embed()
        
        await ctx.send(embed=embed, view=view)
        
    @commands.command(name='adventure', help='Go on an adventure')
    @commands.cooldown(1, RPG_CONSTANTS['adventure_cooldown'], commands.BucketType.user)
    async def go_adventure(self, ctx, location: str = None):
        """Go on an adventure."""
        if not is_module_enabled("rpg_games", ctx.guild.id):
            return
            
        user_id = str(ctx.author.id)
        
        if not ensure_user_exists(user_id):
            await ctx.send("❌ You need to `$start` your adventure first!")
            return
            
        try:
            player_data = get_user_rpg_data(user_id)
            if not player_data:
                await ctx.send("❌ Error retrieving player data. Please try again.")
                return
                
            # Check cooldown
            last_adventure = player_data.get('last_adventure')
            if last_adventure:
                cooldown_remaining = get_time_until_next_use(last_adventure, RPG_CONSTANTS['adventure_cooldown'])
                if cooldown_remaining > 0:
                    embed = create_embed(
                        "⏰ Adventure Cooldown",
                        f"You can go on another adventure in {format_time_remaining(cooldown_remaining)}",
                        COLORS['warning']
                    )
                    await ctx.send(embed=embed)
                    return
                    
            # Show available locations if none specified
            if location is None:
                embed = discord.Embed(
                    title="🗺️ Adventure Locations",
                    description="Choose a location for your adventure:",
                    color=COLORS['info']
                )
                
                for loc_name, loc_data in ADVENTURE_LOCATIONS.items():
                    difficulty_stars = "⭐" * loc_data['difficulty']
                    embed.add_field(
                        name=f"{loc_name} {difficulty_stars}",
                        value=f"{loc_data['description']}\n"
                              f"Recommended Level: {loc_data['difficulty'] * 2}",
                        inline=False
                    )
                    
                embed.set_footer(text="Use $adventure <location> to explore!")
                await ctx.send(embed=embed)
                return
                
            # Find location
            selected_location = None
            for loc_name, loc_data in ADVENTURE_LOCATIONS.items():
                if location.lower() in loc_name.lower():
                    selected_location = (loc_name, loc_data)
                    break
                    
            if not selected_location:
                await ctx.send("❌ Location not found! Use `$adventure` to see available locations.")
                return
                
            loc_name, loc_data = selected_location
            
            # Check if player level is sufficient
            if player_data['level'] < loc_data['difficulty']:
                embed = create_embed(
                    "❌ Level Too Low",
                    f"You need to be at least level {loc_data['difficulty']} to explore {loc_name}!\n"
                    f"Your current level: {player_data['level']}",
                    COLORS['error']
                )
                await ctx.send(embed=embed)
                return
                
            # Start adventure
            await ctx.send(f"🗺️ Starting adventure in {loc_name}...")
            await asyncio.sleep(2)  # Suspense
            
            # Random outcome
            outcome = get_random_adventure_outcome()
            
            # Calculate rewards based on location difficulty
            base_coins = random.randint(loc_data['rewards']['coins'][0], loc_data['rewards']['coins'][1])
            base_xp = random.randint(loc_data['rewards']['xp'][0], loc_data['rewards']['xp'][1])
            
            # Apply luck to rewards
            loot = generate_loot_with_luck(user_id, {
                'coins': base_coins,
                'xp': base_xp
            })
            
            coins_gained = loot['coins']
            xp_gained = loot['xp']
            
            # Random item from location
            items_gained = []
            if loc_data.get('items') and roll_with_luck(user_id, 0.3):  # 30% chance for item
                item = random.choice(loc_data['items'])
                items_gained.append(item)
                
            # Update player data
            player_data['coins'] += coins_gained
            player_data['xp'] += xp_gained
            player_data['last_adventure'] = datetime.now().isoformat()
            player_data['adventure_count'] = player_data.get('adventure_count', 0) + 1
            
            # Add items to inventory
            if 'inventory' not in player_data:
                player_data['inventory'] = []
            for item in items_gained:
                if len(player_data['inventory']) < RPG_CONSTANTS['max_inventory_size']:
                    player_data['inventory'].append(item)
                    
            # Update stats
            if 'stats' not in player_data:
                player_data['stats'] = {}
            player_data['stats']['adventures_completed'] = player_data['stats'].get('adventures_completed', 0) + 1
            player_data['stats']['total_coins_earned'] = player_data['stats'].get('total_coins_earned', 0) + coins_gained
            player_data['stats']['total_xp_earned'] = player_data['stats'].get('total_xp_earned', 0) + xp_gained
            
            # Check for level up
            level_up_msg = level_up_player(player_data)
            
            # Save data
            update_user_rpg_data(user_id, player_data)
            
            # Create result embed
            embed = discord.Embed(
                title=outcome['title'],
                description=f"**Location:** {loc_name}\n{outcome['description']}\n\n"
                           f"**Rewards:**\n"
                           f"⭐ {xp_gained} XP\n"
                           f"💰 {coins_gained} coins",
                color=COLORS['success']
            )
            
            if items_gained:
                embed.add_field(
                    name="🎒 Items Found",
                    value="\n".join(items_gained),
                    inline=False
                )
                
            if level_up_msg:
                embed.add_field(name="🎉 Level Up!", value=level_up_msg, inline=False)
                
            embed.set_footer(text=f"Total coins: {format_number(player_data['coins'])}")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in adventure command for {user_id}: {e}")
            await ctx.send("❌ An error occurred during your adventure. Please try again.")
            
    @commands.command(name='dungeon', help='Explore a dungeon')
    @commands.cooldown(1, RPG_CONSTANTS['dungeon_cooldown'], commands.BucketType.user)
    async def explore_dungeon(self, ctx, dungeon_name: str = None):
        """Explore a dungeon."""
        if not is_module_enabled("rpg_games", ctx.guild.id):
            return
            
        user_id = str(ctx.author.id)
        
        if not ensure_user_exists(user_id):
            await ctx.send("❌ You need to `$start` your adventure first!")
            return
            
        try:
            player_data = get_user_rpg_data(user_id)
            if not player_data:
                await ctx.send("❌ Error retrieving player data. Please try again.")
                return
                
            # Check cooldown
            last_dungeon = player_data.get('last_dungeon')
            if last_dungeon:
                cooldown_remaining = get_time_until_next_use(last_dungeon, RPG_CONSTANTS['dungeon_cooldown'])
                if cooldown_remaining > 0:
                    embed = create_embed(
                        "⏰ Dungeon Cooldown",
                        f"You can explore another dungeon in {format_time_remaining(cooldown_remaining)}",
                        COLORS['warning']
                    )
                    await ctx.send(embed=embed)
                    return
                    
            # Show available dungeons if none specified
            if dungeon_name is None:
                embed = discord.Embed(
                    title="🏰 Available Dungeons",
                    description="Choose a dungeon to explore:",
                    color=COLORS['dark']
                )
                
                for dung_name, dung_data in DUNGEON_TYPES.items():
                    difficulty_stars = "⭐" * dung_data['difficulty']
                    embed.add_field(
                        name=f"{dung_name} {difficulty_stars}",
                        value=f"{dung_data['description']}\n"
                              f"Floors: {dung_data['floors']}\n"
                              f"Required Level: {dung_data['required_level']}\n"
                              f"Boss: {dung_data['boss']}",
                        inline=False
                    )
                    
                embed.set_footer(text="Use $dungeon <name> to explore!")
                await ctx.send(embed=embed)
                return
                
            # Find dungeon
            selected_dungeon = None
            for dung_name, dung_data in DUNGEON_TYPES.items():
                if dungeon_name.lower() in dung_name.lower():
                    selected_dungeon = (dung_name, dung_data)
                    break
                    
            if not selected_dungeon:
                await ctx.send("❌ Dungeon not found! Use `$dungeon` to see available dungeons.")
                return
                
            dung_name, dung_data = selected_dungeon
            
            # Check level requirement
            if player_data['level'] < dung_data['required_level']:
                embed = create_embed(
                    "❌ Level Too Low",
                    f"You need to be at least level {dung_data['required_level']} to explore {dung_name}!\n"
                    f"Your current level: {player_data['level']}",
                    COLORS['error']
                )
                await ctx.send(embed=embed)
                return
                
            # Check if player has enough HP
            if player_data['hp'] < player_data['max_hp'] * 0.5:
                embed = create_embed(
                    "❌ Low Health",
                    f"You need at least 50% HP to explore a dungeon!\n"
                    f"Current HP: {player_data['hp']}/{player_data['max_hp']}\n"
                    f"Use `$heal` to restore your health.",
                    COLORS['warning']
                )
                await ctx.send(embed=embed)
                return
                
            # Update last dungeon time
            player_data['last_dungeon'] = datetime.now().isoformat()
            update_user_rpg_data(user_id, player_data)
            
            # Start dungeon exploration
            view = DungeonView(ctx, player_data, dung_data)
            embed = view.create_dungeon_embed()
            
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error in dungeon command for {user_id}: {e}")
            await ctx.send("❌ An error occurred while exploring the dungeon. Please try again.")
            
    @commands.command(name='battle', help='Battle another player or monster')
    @commands.cooldown(1, RPG_CONSTANTS['battle_cooldown'], commands.BucketType.user)
    async def battle(self, ctx, target: discord.Member = None):
        """Battle another player or monster."""
        if not is_module_enabled("rpg_games", ctx.guild.id):
            return
            
        user_id = str(ctx.author.id)
        
        if not ensure_user_exists(user_id):
            await ctx.send("❌ You need to `$start` your adventure first!")
            return
            
        try:
            player_data = get_user_rpg_data(user_id)
            if not player_data:
                await ctx.send("❌ Error retrieving player data. Please try again.")
                return
                
            if target is None:
                # Battle random monster
                monster_name = random.choice(list(MONSTERS.keys()))
                monster_data = MONSTERS[monster_name].copy()
                monster_data['name'] = monster_name
                monster_data['max_hp'] = monster_data['hp']
                
                # Scale monster to player level
                level_modifier = player_data['level'] / 5
                monster_data['hp'] = int(monster_data['hp'] * (1 + level_modifier))
                monster_data['max_hp'] = monster_data['hp']
                monster_data['attack'] = int(monster_data['attack'] * (1 + level_modifier))
                monster_data['defense'] = int(monster_data['defense'] * (1 + level_modifier))
                
                # Start battle
                view = BattleView(ctx, player_data, monster_data, "monster")
                embed = view.create_battle_embed()
                
                await ctx.send(embed=embed, view=view)
                
            else:
                # PvP battle
                if target == ctx.author:
                    await ctx.send("❌ You can't battle yourself!")
                    return
                    
                target_id = str(target.id)
                if not ensure_user_exists(target_id):
                    await ctx.send(f"❌ {target.mention} hasn't started their adventure yet!")
                    return
                    
                target_data = get_user_rpg_data(target_id)
                if not target_data:
                    await ctx.send("❌ Error retrieving target player data.")
                    return
                    
                # Check if target accepts PvP
                # For now, just start the battle
                view = BattleView(ctx, player_data, target_data, "pvp")
                embed = view.create_battle_embed()
                
                await ctx.send(f"{target.mention}, you're being challenged to a battle!", embed=embed, view=view)
                
        except Exception as e:
            logger.error(f"Error in battle command for {user_id}: {e}")
            await ctx.send("❌ An error occurred during battle. Please try again.")
            
    @commands.command(name='heal', help='Heal your character')
    async def heal_character(self, ctx):
        """Heal the player's character."""
        if not is_module_enabled("rpg_games", ctx.guild.id):
            return
            
        user_id = str(ctx.author.id)
        
        if not ensure_user_exists(user_id):
            await ctx.send("❌ You need to `$start` your adventure first!")
            return
            
        try:
            player_data = get_user_rpg_data(user_id)
            if not player_data:
                await ctx.send("❌ Error retrieving player data. Please try again.")
                return
                
            # Check if healing is needed
            if player_data['hp'] >= player_data['max_hp']:
                embed = create_embed(
                    "❤️ Full Health",
                    "You're already at full health!",
                    COLORS['success']
                )
                await ctx.send(embed=embed)
                return
                
            # Calculate heal cost
            heal_cost = RPG_CONSTANTS['heal_cost']
            
            # Check if player has enough coins
            if player_data['coins'] < heal_cost:
                embed = create_embed(
                    "❌ Insufficient Coins",
                    f"Healing costs {heal_cost} coins, but you only have {player_data['coins']}.",
                    COLORS['error']
                )
                await ctx.send(embed=embed)
                return
                
            # Heal player
            old_hp = player_data['hp']
            player_data['hp'] = player_data['max_hp']
            player_data['coins'] -= heal_cost
            
            # Save data
            update_user_rpg_data(user_id, player_data)
            
            embed = create_embed(
                "❤️ Fully Healed!",
                f"You restored {player_data['max_hp'] - old_hp} HP for {heal_cost} coins.\n"
                f"Current HP: {player_data['hp']}/{player_data['max_hp']}\n"
                f"Remaining coins: {format_number(player_data['coins'])}",
                COLORS['success']
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in heal command for {user_id}: {e}")
            await ctx.send("❌ An error occurred while healing. Please try again.")
            
    @commands.command(name='equip', help='Equip weapons and armor')
    async def equip_item(self, ctx, *, item_name: str):
        """Equip an item from inventory."""
        if not is_module_enabled("rpg_games", ctx.guild.id):
            return
            
        user_id = str(ctx.author.id)
        
        if not ensure_user_exists(user_id):
            await ctx.send("❌ You need to `$start` your adventure first!")
            return
            
        try:
            player_data = get_user_rpg_data(user_id)
            if not player_data:
                await ctx.send("❌ Error retrieving player data. Please try again.")
                return
                
            # Check if item is in inventory
            inventory = player_data.get('inventory', [])
            found_item = None
            
            for item in inventory:
                if item.lower() == item_name.lower():
                    found_item = item
                    break
                    
            if not found_item:
                # Try partial match
                for item in inventory:
                    if item_name.lower() in item.lower():
                        found_item = item
                        break
                        
            if not found_item:
                embed = create_embed(
                    "❌ Item Not Found",
                    f"You don't have '{item_name}' in your inventory!",
                    COLORS['error']
                )
                await ctx.send(embed=embed)
                return
                
            # Determine item type and equip
            from utils.constants import SHOP_ITEMS
            
            item_type = None
            item_stats = None
            
            for category, items in SHOP_ITEMS.items():
                if found_item in items:
                    item_type = category
                    item_stats = items[found_item]
                    break
                    
            if not item_type or item_type not in ['weapons', 'armor', 'accessories']:
                embed = create_embed(
                    "❌ Not Equipable",
                    f"{found_item} cannot be equipped!",
                    COLORS['error']
                )
                await ctx.send(embed=embed)
                return
                
            # Initialize equipped items
            if 'equipped' not in player_data:
                player_data['equipped'] = {}
                
            # Map item types to equipment slots
            slot_mapping = {
                'weapons': 'weapon',
                'armor': 'armor',
                'accessories': 'accessory'
            }
            
            slot = slot_mapping[item_type]
            old_item = player_data['equipped'].get(slot)
            
            # Unequip old item if exists
            if old_item:
                # Remove old item stats
                old_item_stats = None
                for category, items in SHOP_ITEMS.items():
                    if old_item in items:
                        old_item_stats = items[old_item]
                        break
                        
                if old_item_stats:
                    if 'attack' in old_item_stats:
                        player_data['attack'] -= old_item_stats['attack']
                    if 'defense' in old_item_stats:
                        player_data['defense'] -= old_item_stats['defense']
                    if 'hp' in old_item_stats:
                        player_data['max_hp'] -= old_item_stats['hp']
                        player_data['hp'] = min(player_data['hp'], player_data['max_hp'])
                        
                # Add old item back to inventory
                player_data['inventory'].append(old_item)
                
            # Equip new item
            player_data['equipped'][slot] = found_item
            player_data['inventory'].remove(found_item)
            
            # Apply new item stats
            if 'attack' in item_stats:
                player_data['attack'] += item_stats['attack']
            if 'defense' in item_stats:
                player_data['defense'] += item_stats['defense']
            if 'hp' in item_stats:
                player_data['max_hp'] += item_stats['hp']
                player_data['hp'] += item_stats['hp']  # Also heal when equipping HP items
                
            # Save data
            update_user_rpg_data(user_id, player_data)
            
            embed = create_embed(
                "✅ Item Equipped!",
                f"You equipped **{found_item}**!\n\n"
                f"**Stats:**\n"
                f"Attack: {player_data['attack']}\n"
                f"Defense: {player_data['defense']}\n"
                f"HP: {player_data['hp']}/{player_data['max_hp']}",
                COLORS['success']
            )
            
            if old_item:
                embed.add_field(
                    name="Previous Item",
                    value=f"{old_item} was unequipped and returned to inventory.",
                    inline=False
                )
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in equip command for {user_id}: {e}")
            await ctx.send("❌ An error occurred while equipping the item. Please try again.")
            
    @commands.command(name='inventory', help='View your inventory')
    async def view_inventory(self, ctx):
        """View player inventory."""
        if not is_module_enabled("rpg_games", ctx.guild.id):
            return
            
        user_id = str(ctx.author.id)
        
        if not ensure_user_exists(user_id):
            await ctx.send("❌ You need to `$start` your adventure first!")
            return
            
        try:
            player_data = get_user_rpg_data(user_id)
            if not player_data:
                await ctx.send("❌ Error retrieving player data. Please try again.")
                return
                
            # Create inventory view
            view = RPGProfileView(ctx.author, player_data)
            embed = view.create_inventory_embed()
            
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error in inventory command for {user_id}: {e}")
            await ctx.send("❌ An error occurred while viewing inventory. Please try again.")
            
    @commands.command(name='leaderboard', help='View leaderboards')
    async def view_leaderboard(self, ctx, category: str = 'level'):
        """View leaderboards."""
        if not is_module_enabled("rpg_games", ctx.guild.id):
            return
            
        try:
            valid_categories = ['level', 'coins', 'xp', 'battles']
            if category not in valid_categories:
                embed = create_embed(
                    "❌ Invalid Category",
                    f"Valid categories: {', '.join(valid_categories)}",
                    COLORS['error']
                )
                await ctx.send(embed=embed)
                return
                
            leaderboard = get_leaderboard(category, 10)
            
            if not leaderboard:
                embed = create_embed(
                    "📊 Leaderboard",
                    "No data available yet!",
                    COLORS['info']
                )
                await ctx.send(embed=embed)
                return
                
            embed = discord.Embed(
                title=f"🏆 {category.title()} Leaderboard",
                color=COLORS['warning']
            )
            
            leaderboard_text = ""
            for i, entry in enumerate(leaderboard, 1):
                try:
                    user = await self.bot.fetch_user(int(entry['user_id']))
                    username = user.display_name if user else "Unknown User"
                except:
                    username = "Unknown User"
                    
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                leaderboard_text += f"{medal} **{username}** - {format_number(entry['value'])}\n"
                
            embed.description = leaderboard_text
            embed.set_footer(text=f"Showing top {len(leaderboard)} players")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}")
            await ctx.send("❌ An error occurred while fetching leaderboard. Please try again.")

    @commands.command(name='craft', help='Craft items')
    async def craft_item(self, ctx, *, item_name: str = None):
        """Craft items using materials."""
        if not is_module_enabled("rpg_games", ctx.guild.id):
            return
            
        user_id = str(ctx.author.id)
        
        if not ensure_user_exists(user_id):
            await ctx.send("❌ You need to `$start` your adventure first!")
            return
            
        try:
            player_data = get_user_rpg_data(user_id)
            if not player_data:
                await ctx.send("❌ Error retrieving player data. Please try again.")
                return
                
            # Show available recipes if no item specified
            if item_name is None:
                embed = discord.Embed(
                    title="🔨 Crafting Recipes",
                    description="Available recipes:",
                    color=COLORS['info']
                )
                
                for recipe_name, recipe_data in CRAFTING_RECIPES.items():
                    materials = []
                    for material, amount in recipe_data['materials'].items():
                        materials.append(f"{material} x{amount}")
                        
                    embed.add_field(
                        name=recipe_name,
                        value=f"**Materials:** {', '.join(materials)}\n"
                              f"**Cost:** {recipe_data['cost']} coins\n"
                              f"**Skill Required:** {recipe_data['skill_required']}",
                        inline=False
                    )
                    
                embed.set_footer(text="Use $craft <item> to craft!")
                await ctx.send(embed=embed)
                return
                
            # Find recipe
            recipe = None
            for recipe_name, recipe_data in CRAFTING_RECIPES.items():
                if item_name.lower() in recipe_name.lower():
                    recipe = (recipe_name, recipe_data)
                    break
                    
            if not recipe:
                await ctx.send("❌ Recipe not found! Use `$craft` to see available recipes.")
                return
                
            recipe_name, recipe_data = recipe
            
            # Check skill requirement
            crafting_skill = min(player_data['level'] + len(player_data.get('crafted_items', [])), 100)
            if crafting_skill < recipe_data['skill_required']:
                embed = create_embed(
                    "❌ Insufficient Skill",
                    f"You need crafting skill {recipe_data['skill_required']} to craft {recipe_name}!\n"
                    f"Your crafting skill: {crafting_skill}",
                    COLORS['error']
                )
                await ctx.send(embed=embed)
                return
                
            # Check materials
            inventory = player_data.get('inventory', [])
            missing_materials = []
            
            for material, amount_needed in recipe_data['materials'].items():
                amount_have = inventory.count(material)
                if amount_have < amount_needed:
                    missing_materials.append(f"{material} (need {amount_needed}, have {amount_have})")
                    
            if missing_materials:
                embed = create_embed(
                    "❌ Missing Materials",
                    f"You're missing:\n" + "\n".join(missing_materials),
                    COLORS['error']
                )
                await ctx.send(embed=embed)
                return
                
            # Check coin cost
            if player_data['coins'] < recipe_data['cost']:
                embed = create_embed(
                    "❌ Insufficient Coins",
                    f"You need {recipe_data['cost']} coins but only have {player_data['coins']}.",
                    COLORS['error']
                )
                await ctx.send(embed=embed)
                return
                
            # Craft the item
            for material, amount in recipe_data['materials'].items():
                for _ in range(amount):
                    player_data['inventory'].remove(material)
                    
            player_data['coins'] -= recipe_data['cost']
            
            # Add crafted item to inventory
            if len(player_data['inventory']) < RPG_CONSTANTS['max_inventory_size']:
                player_data['inventory'].append(recipe_name)
                
                # Track crafted items
                if 'crafted_items' not in player_data:
                    player_data['crafted_items'] = []
                player_data['crafted_items'].append(recipe_name)
                
                # Save data
                update_user_rpg_data(user_id, player_data)
                
                embed = create_embed(
                    "✅ Crafting Successful!",
                    f"You crafted **{recipe_name}**!\n\n"
                    f"Remaining coins: {format_number(player_data['coins'])}",
                    COLORS['success']
                )
                
                await ctx.send(embed=embed)
            else:
                embed = create_embed(
                    "❌ Inventory Full",
                    "Your inventory is full! Cannot craft item.",
                    COLORS['error']
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in craft command for {user_id}: {e}")
            await ctx.send("❌ An error occurred while crafting. Please try again.")

async def setup(bot):
    await bot.add_cog(RPGGamesCog(bot))
