import discord
from discord.ext import commands
import random
import asyncio
from rpg_data.game_data import CLASSES, ITEMS, RARITY_COLORS, TACTICAL_MONSTERS
from utils.helpers import create_embed, format_number
from config import COLORS, is_module_enabled
import logging

logger = logging.getLogger(__name__)

# Enhanced monster data with weaknesses
ENHANCED_MONSTERS = {
    'goblin': {
        'name': 'Goblin Warrior',
        'emoji': '👹',
        'hp': 120,
        'max_hp': 120,
        'toughness': 60,
        'max_toughness': 60,
        'weakness_type': 'physical',
        'attack': 25,
        'defense': 8,
        'level': 3,
        'xp_reward': 35,
        'gold_reward': 15,
        'skills': ['quick_slash'],
        'loot_table': {'health_potion': 0.4, 'iron_sword': 0.2}
    },
    'orc': {
        'name': 'Orc Berserker',
        'emoji': '👺',
        'hp': 180,
        'max_hp': 180,
        'toughness': 80,
        'max_toughness': 80,
        'weakness_type': 'ice',
        'attack': 35,
        'defense': 12,
        'level': 6,
        'xp_reward': 60,
        'gold_reward': 25,
        'skills': ['berserker_rage'],
        'loot_table': {'health_potion': 0.3, 'steel_armor': 0.15}
    },
    'ice_elemental': {
        'name': 'Ice Elemental',
        'emoji': '🧊',
        'hp': 150,
        'max_hp': 150,
        'toughness': 70,
        'max_toughness': 70,
        'weakness_type': 'fire',
        'attack': 30,
        'defense': 15,
        'level': 5,
        'xp_reward': 50,
        'gold_reward': 20,
        'skills': ['ice_blast'],
        'loot_table': {'mana_potion': 0.5, 'ice_crystal': 0.3}
    },
    'dragon': {
        'name': 'Ancient Dragon',
        'emoji': '🐉',
        'hp': 400,
        'max_hp': 400,
        'toughness': 120,
        'max_toughness': 120,
        'weakness_type': 'lightning',
        'attack': 60,
        'defense': 25,
        'level': 15,
        'xp_reward': 200,
        'gold_reward': 100,
        'skills': ['dragon_breath', 'tail_sweep'],
        'loot_table': {'dragon_scale': 0.8, 'legendary_weapon': 0.1}
    }
}

# Enhanced skills with SP costs
TACTICAL_SKILLS = {
    'power_strike': {
        'name': 'Power Strike',
        'cost': 1,
        'damage': 40,
        'toughness_damage': 15,
        'damage_type': 'physical',
        'ultimate_gain': 20,
        'description': 'A powerful physical attack that costs 1 SP.'
    },
    'flame_slash': {
        'name': 'Flame Slash',
        'cost': 1,
        'damage': 35,
        'toughness_damage': 20,
        'damage_type': 'fire',
        'ultimate_gain': 20,
        'description': 'A burning sword technique that costs 1 SP.'
    },
    'ice_lance': {
        'name': 'Ice Lance',
        'cost': 1,
        'damage': 38,
        'toughness_damage': 18,
        'damage_type': 'ice',
        'ultimate_gain': 20,
        'description': 'A piercing ice attack that costs 1 SP.'
    },
    'heal': {
        'name': 'Healing Light',
        'cost': 1,
        'heal': 50,
        'ultimate_gain': 15,
        'description': 'Restores health using 1 SP.'
    }
}

# Ultimate abilities by class
ULTIMATE_ABILITIES = {
    'warrior': {
        'name': 'Blade Storm',
        'description': 'Unleashes a devastating series of strikes',
        'damage': 120,
        'toughness_damage': 50,
        'damage_type': 'physical'
    },
    'mage': {
        'name': 'Arcane Devastation',
        'description': 'Channels pure magical energy',
        'damage': 100,
        'toughness_damage': 60,
        'damage_type': 'quantum'
    },
    'rogue': {
        'name': 'Shadow Assassination',
        'description': 'Strikes from the shadows with lethal precision',
        'damage': 110,
        'toughness_damage': 40,
        'damage_type': 'physical'
    },
    'archer': {
        'name': 'Rain of Arrows',
        'description': 'Unleashes a devastating arrow barrage',
        'damage': 105,
        'toughness_damage': 35,
        'damage_type': 'physical'
    },
    'healer': {
        'name': 'Divine Intervention',
        'description': 'Calls upon divine power for massive healing',
        'heal': 150,
        'damage': 80,
        'toughness_damage': 30,
        'damage_type': 'divine'
    },
    'battlemage': {
        'name': 'Elemental Fury',
        'description': 'Combines magic and melee in perfect harmony',
        'damage': 115,
        'toughness_damage': 45,
        'damage_type': 'elemental'
    },
    'chrono_knight': {
        'name': 'Time Fracture',
        'description': 'Manipulates time to deal devastating damage',
        'damage': 130,
        'toughness_damage': 55,
        'damage_type': 'temporal'
    }
}

# Active combat sessions
active_combats = {}

class TacticalCombatView(discord.ui.View):
    """Enhanced combat view with tactical mechanics."""

    def __init__(self, player_id, monster_key, initial_message, rpg_core_cog):
        super().__init__(timeout=300)
        self.player_id = player_id
        self.monster_key = monster_key
        self.message = initial_message
        self.rpg_core = rpg_core_cog
        self.combat_log = []
        self.turn_count = 0

        # Load player data
        self.player_data = self.rpg_core.get_player_data(player_id)
        if not self.player_data:
            return

        # Initialize combat state with tactical elements
        monster_data = ENHANCED_MONSTERS.get(monster_key, ENHANCED_MONSTERS['goblin']).copy()

        self.combat_state = {
            'in_combat': True,
            'skill_points': 3,
            'max_skill_points': 5,
            'enemy': monster_data,
            'turn': 'player',
            'enemy_broken_turns': 0
        }

        self.add_log(f"⚔️ A wild **{monster_data['name']} {monster_data['emoji']}** appears!")
        self.add_log(f"🔍 Enemy weakness: {monster_data['weakness_type'].title()}")

    def add_log(self, text):
        """Add entry to combat log."""
        self.combat_log.append(f"• {text}")
        if len(self.combat_log) > 8:
            self.combat_log.pop(0)

    def create_bar(self, current, maximum, length=10, fill="█", empty="░"):
        """Create visual progress bar."""
        if maximum == 0:
            return empty * length
        percentage = current / maximum
        filled = int(percentage * length)
        empty_count = length - filled
        return fill * filled + empty * empty_count

    def create_sp_display(self):
        """Create skill points display."""
        sp = self.combat_state['skill_points']
        max_sp = self.combat_state['max_skill_points']
        filled = "💎" * sp
        empty = "▢" * (max_sp - sp)
        return f"{filled}{empty} ({sp}/{max_sp})"

    async def create_embed(self):
        """Generate comprehensive tactical combat embed."""
        enemy = self.combat_state['enemy']
        resources = self.player_data['resources']

        embed = discord.Embed(
            title=f"⚔️ Tactical Combat: {self.player_data.get('name', 'Player')} vs. {enemy['name']}", 
            color=COLORS['error']
        )

        # Skill Points display
        embed.add_field(
            name="💎 Skill Points",
            value=f"**SP:** {self.create_sp_display()}",
            inline=False
        )

        # Player status
        player_hp_bar = self.create_bar(resources['hp'], resources['max_hp'])
        ultimate_bar = self.create_bar(
            resources.get('ultimate_energy', 0), 
            100
        )

        embed.add_field(
            name=f"👤 {self.player_data.get('name', 'Player')}",
            value=f"❤️ **HP:** {resources['hp']}/{resources['max_hp']} {player_hp_bar}\n"
                  f"⚡ **Ultimate:** {ultimate_bar} ({resources.get('ultimate_energy', 0)}/100)",
            inline=True
        )

        # Enemy status with toughness
        enemy_hp_bar = self.create_bar(enemy['hp'], enemy['max_hp'])

        if enemy.get('is_broken', False):
            toughness_display = "💥 [ BROKEN ] 💥"
        else:
            toughness_bar = self.create_bar(enemy['toughness'], enemy['max_toughness'])
            toughness_display = f"🛡️ {enemy['toughness']}/{enemy['max_toughness']} {toughness_bar}"

        embed.add_field(
            name=f"{enemy['emoji']} {enemy['name']}",
            value=f"❤️ **HP:** {enemy['hp']}/{enemy['max_hp']} {enemy_hp_bar}\n"
                  f"{toughness_display}\n"
                  f"🔍 **Weakness:** {enemy['weakness_type'].title()}",
            inline=True
        )

        # Turn indicator
        turn_text = "🎯 **Your Turn**" if self.combat_state['turn'] == 'player' else "🔴 **Enemy Turn**"
        if enemy.get('is_broken', False):
            turn_text += " (Enemy Stunned!)"

        embed.add_field(name="Current Turn", value=f"{turn_text} | Turn {self.turn_count + 1}", inline=False)

        # Combat log
        if self.combat_log:
            log_content = "\n".join(self.combat_log[-6:])
            embed.add_field(name="📜 Combat Log", value=f"```{log_content}```", inline=False)

        return embed

    async def update_view(self):
        """Update combat display and button states."""
        enemy = self.combat_state['enemy']
        resources = self.player_data['resources']

        # Update button availability
        for item in self.children:
            if hasattr(item, 'label'):
                if item.label == "💥 ULTIMATE":
                    item.disabled = (
                        self.combat_state['turn'] != 'player' or
                        resources.get('ultimate_energy', 0) < 100 or
                        resources['hp'] <= 0 or
                        enemy['hp'] <= 0
                    )
                    item.style = discord.ButtonStyle.success if resources.get('ultimate_energy', 0) >= 100 else discord.ButtonStyle.secondary
                else:
                    item.disabled = (
                        self.combat_state['turn'] != 'player' or
                        resources['hp'] <= 0 or
                        enemy['hp'] <= 0
                    )

        embed = await self.create_embed()
        try:
            await self.message.edit(embed=embed, view=self)
        except (discord.NotFound, discord.HTTPException, discord.Forbidden) as e:
            logger.warning(f"Failed to update combat view: {e}")
            # Try to handle the error gracefully
            if hasattr(self, 'message') and hasattr(self.message, 'channel'):
                try:
                    await self.message.channel.send(f"⚠️ Combat display error - use `$profile` to check your status!")
                except:
                    pass

    async def check_weakness_break(self, damage_type, toughness_damage):
        """Check and handle weakness break mechanics."""
        enemy = self.combat_state['enemy']
        weakness_match = damage_type == enemy['weakness_type']

        if weakness_match and toughness_damage > 0:
            old_toughness = enemy['toughness']
            enemy['toughness'] = max(0, enemy['toughness'] - toughness_damage)
            self.add_log(f"💥 Weakness hit! Toughness damage: {toughness_damage}")

            # Check for break
            if old_toughness > 0 and enemy['toughness'] == 0:
                enemy['is_broken'] = True
                self.combat_state['enemy_broken_turns'] = 1
                self.add_log(f"🔥 WEAKNESS BREAK! {enemy['name']} is stunned!")
                return True

        return False

    async def end_combat(self, victory):
        """Handle combat conclusion with enhanced rewards."""
        self.player_data['in_combat'] = False
        enemy = self.combat_state['enemy']

        if victory:
            # Calculate rewards
            base_xp = enemy['xp_reward']
            base_gold = enemy['gold_reward']

            # Level multiplier
            level_mult = 1 + (self.player_data['level'] - 1) * 0.1
            xp_gained = int(base_xp * level_mult)
            gold_gained = int(base_gold * level_mult)

            self.player_data['xp'] += xp_gained
            self.player_data['gold'] += gold_gained

            # Loot drops
            loot_found = []
            for item_name, chance in enemy.get('loot_table', {}).items():
                if random.random() < chance:
                    if item_name in self.player_data['inventory']:
                        self.player_data['inventory'][item_name] += 1
                    else:
                        self.player_data['inventory'][item_name] = 1
                    loot_found.append(item_name)

            self.add_log(f"🏆 Victory! Gained {xp_gained} XP and {gold_gained} gold!")
            if loot_found:
                items_str = ", ".join([item.replace('_', ' ').title() for item in loot_found])
                self.add_log(f"💎 Found: {items_str}")

            # Check for level up
            levels_gained = self.rpg_core.level_up_check(self.player_data)
            if levels_gained:
                self.add_log(f"⭐ LEVEL UP! You are now level {self.player_data['level']}!")

            final_embed = discord.Embed(
                title="🏆 TACTICAL VICTORY! 🏆",
                description="\n".join(self.combat_log),
                color=COLORS['success']
            )
        else:
            # Defeat consequences
            gold_lost = max(1, int(self.player_data['gold'] * 0.15))
            self.player_data['gold'] = max(0, self.player_data['gold'] - gold_lost)
            self.player_data['resources']['hp'] = max(1, self.player_data['resources']['max_hp'] // 4)

            self.add_log(f"💀 Defeat! Lost {gold_lost} gold and most of your health.")

            final_embed = discord.Embed(
                title="☠️ TACTICAL DEFEAT ☠️",
                description="\n".join(self.combat_log),
                color=COLORS['error']
            )

        # Reset ultimate energy
        self.player_data['resources']['ultimate_energy'] = 0
        self.rpg_core.save_player_data(self.player_id, self.player_data)

        try:
            await self.message.edit(content="Combat concluded.", embed=final_embed, view=None)
        except discord.NotFound:
            pass

        if self.message.channel.id in active_combats:
            del active_combats[self.message.channel.id]
        self.stop()

    async def monster_turn(self):
        """Enhanced monster AI."""
        enemy = self.combat_state['enemy']

        # Check if broken/stunned
        if enemy.get('is_broken', False):
            if self.combat_state['enemy_broken_turns'] > 0:
                self.add_log(f"💫 {enemy['name']} is stunned and skips their turn!")
                self.combat_state['enemy_broken_turns'] -= 1

                if self.combat_state['enemy_broken_turns'] <= 0:
                    enemy['is_broken'] = False
                    enemy['toughness'] = enemy['max_toughness']
                    self.add_log(f"🛡️ {enemy['name']} recovers!")

                self.combat_state['turn'] = 'player'
                await self.update_view()
                return

        # Monster attacks
        damage = random.randint(enemy['attack'] - 5, enemy['attack'] + 10)
        self.player_data['resources']['hp'] = max(0, self.player_data['resources']['hp'] - damage)
        self.add_log(f"{enemy['name']} attacks for {damage} damage!")

        self.combat_state['turn'] = 'player'
        self.turn_count += 1
        await self.update_view()

        # Check for player defeat
        if self.player_data['resources']['hp'] <= 0:
            await self.end_combat(victory=False)

    # Combat buttons
    @discord.ui.button(label="⚔️ Basic Attack", style=discord.ButtonStyle.secondary, emoji="⚔️")
    async def basic_attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("Not your combat!", ephemeral=True)
            return

        await interaction.response.defer()

        # Basic attack generates SP and ultimate energy
        base_damage = 20 + self.player_data['derived_stats']['attack'] // 2
        damage = random.randint(base_damage - 5, base_damage + 8)

        # Check for critical hit
        crit_chance = self.player_data['derived_stats'].get('critical_chance', 0.05)
        is_critical = random.random() < crit_chance

        if is_critical:
            damage = int(damage * 1.5)
            self.add_log(f"💥 CRITICAL HIT! (150% damage)")

        # Generate SP
        if self.combat_state['skill_points'] < self.combat_state['max_skill_points']:
            self.combat_state['skill_points'] += 1
            sp_gained = 1
        else:
            sp_gained = 0

        # Generate ultimate energy
        ultimate_gain = 15
        old_ultimate = self.player_data['resources'].get('ultimate_energy', 0)
        self.player_data['resources']['ultimate_energy'] = min(100, old_ultimate + ultimate_gain)

        # Check for weakness (basic attacks are physical)
        enemy = self.combat_state['enemy']
        if enemy['weakness_type'] == 'physical':
            toughness_damage = 10
            await self.check_weakness_break('physical', toughness_damage)

        # Apply damage multiplier if enemy is broken
        if enemy.get('is_broken', False):
            damage = int(damage * 1.3)
            self.add_log(f"💥 Bonus damage on broken enemy!")

        enemy['hp'] = max(0, enemy['hp'] - damage)

        log_msg = f"⚔️ Basic Attack! Dealt {damage} damage"
        if sp_gained > 0:
            log_msg += f", gained {sp_gained} SP"
        log_msg += f", gained {ultimate_gain} Ultimate Energy!"

        self.add_log(log_msg)

        self.combat_state['turn'] = 'monster'
        await self.update_view()
        await asyncio.sleep(1.5)

        if enemy['hp'] <= 0:
            await self.end_combat(victory=True)
            return

        await self.monster_turn()

    @discord.ui.button(label="✨ Power Strike", style=discord.ButtonStyle.primary, emoji="✨")
    async def power_strike(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("Not your combat!", ephemeral=True)
            return

        await interaction.response.defer()

        # Check SP
        if self.combat_state['skill_points'] < 1:
            self.add_log(f"❌ Not enough Skill Points! Need 1 SP.")
            await self.update_view()
            return

        # Consume SP
        self.combat_state['skill_points'] -= 1

        enemy = self.combat_state['enemy']
        base_damage = 40 + self.player_data['derived_stats']['attack'] // 2
        damage = random.randint(base_damage - 5, base_damage + 10)

        # Check for weakness break
        toughness_damage = 15
        was_broken = await self.check_weakness_break('physical', toughness_damage)

        # Apply damage multiplier if enemy is broken
        if enemy.get('is_broken', False):
            damage = int(damage * 1.5)
            self.add_log(f"💥 Bonus damage on broken enemy!")

        enemy['hp'] = max(0, enemy['hp'] - damage)
        self.add_log(f"⚔️ Power Strike! Dealt {damage} physical damage for 1 SP.")

        # Grant ultimate energy
        ultimate_gain = 20
        old_ultimate = self.player_data['resources'].get('ultimate_energy', 0)
        self.player_data['resources']['ultimate_energy'] = min(100, old_ultimate + ultimate_gain)

        # End turn
        self.combat_state['turn'] = 'monster'
        await self.update_view()
        await asyncio.sleep(1.5)

        # Check for victory
        if enemy['hp'] <= 0:
            await self.end_combat(victory=True)
            return

        await self.monster_turn()

    @discord.ui.button(label="💥 ULTIMATE", style=discord.ButtonStyle.secondary, emoji="💥")
    async def ultimate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("Not your combat!", ephemeral=True)
            return

        # Check if ultimate is ready
        if self.player_data['resources'].get('ultimate_energy', 0) < 100:
            await interaction.response.send_message("❌ Ultimate not ready!", ephemeral=True)
            return

        await interaction.response.defer()

        # Get ultimate based on class
        player_class = self.player_data.get('class', 'warrior')
        ultimate_data = ULTIMATE_ABILITIES.get(player_class, ULTIMATE_ABILITIES['warrior'])

        # Consume ultimate energy
        self.player_data['resources']['ultimate_energy'] = 0

        enemy = self.combat_state['enemy']

        # Calculate ultimate damage
        if 'damage' in ultimate_data:
            base_damage = ultimate_data['damage']
            damage = random.randint(base_damage - 10, base_damage + 20)

            # Check for weakness break
            toughness_damage = ultimate_data.get('toughness_damage', 30)
            damage_type = ultimate_data.get('damage_type', 'physical')
            await self.check_weakness_break(damage_type, toughness_damage)

            # Apply damage multiplier if enemy is broken
            if enemy.get('is_broken', False):
                damage = int(damage * 1.8)
                self.add_log(f"💥 Massive bonus damage on broken enemy!")

            enemy['hp'] = max(0, enemy['hp'] - damage)
            self.add_log(f"🌟 ULTIMATE: {ultimate_data['name']}!")
            self.add_log(f"💥 Dealt {damage} {damage_type} damage!")

        # Healing ultimates
        if 'heal' in ultimate_data:
            heal_amount = ultimate_data['heal']
            old_hp = self.player_data['resources']['hp']
            self.player_data['resources']['hp'] = min(
                self.player_data['resources']['max_hp'],
                old_hp + heal_amount
            )
            actual_heal = self.player_data['resources']['hp'] - old_hp
            self.add_log(f"✨ Healed {actual_heal} HP!")

        await self.update_view()

        if enemy['hp'] <= 0:
            await self.end_combat(victory=True)
            return

    @discord.ui.button(label="🧪 Heal", style=discord.ButtonStyle.success, emoji="🧪")
    async def use_potion(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("Not your combat!", ephemeral=True)
            return

        # Quick health potion use
        if 'health_potion' in self.player_data['inventory'] and self.player_data['inventory']['health_potion'] > 0:
            self.player_data['inventory']['health_potion'] -= 1
            heal_amount = 60
            old_hp = self.player_data['resources']['hp']
            self.player_data['resources']['hp'] = min(
                self.player_data['resources']['max_hp'], 
                old_hp + heal_amount
            )
            actual_heal = self.player_data['resources']['hp'] - old_hp

            # Generate small ultimate energy
            ultimate_gain = 10
            old_ultimate = self.player_data['resources'].get('ultimate_energy', 0)
            self.player_data['resources']['ultimate_energy'] = min(100, old_ultimate + ultimate_gain)

            self.add_log(f"🧪 Used Health Potion! Healed {actual_heal} HP!")
            await interaction.response.defer()

            self.combat_state['turn'] = 'monster'
            await self.update_view()
            await asyncio.sleep(1)
            await self.monster_turn()
        else:
            await interaction.response.send_message("❌ No health potions available!", ephemeral=True)

    @discord.ui.button(label="🏃 Flee", style=discord.ButtonStyle.secondary, emoji="🏃")
    async def flee(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("Not your combat!", ephemeral=True)
            return

        await interaction.response.defer()

        # Flee always succeeds but has consequences
        self.add_log("🏃 You fled from combat!")
        self.player_data['in_combat'] = False
        self.player_data['resources']['ultimate_energy'] = 0
        self.rpg_core.save_player_data(self.player_id, self.player_data)

        embed = await self.create_embed()
        embed.title = "🏃 Fled from Combat"
        embed.color = COLORS['warning']

        try:
            await self.message.edit(content="You escaped!", embed=embed, view=None)
        except discord.NotFound:
            pass

        if self.message.channel.id in active_combats:
            del active_combats[self.message.channel.id]
        self.stop()

class RPGCombat(commands.Cog):
    """Enhanced RPG combat system with tactical mechanics."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="battle", aliases=["fight", "combat"])
    async def battle(self, ctx, monster_name: str = None):
        """Initiate tactical combat with enhanced mechanics."""
        if not is_module_enabled("rpg", ctx.guild.id):
            return

        rpg_core = self.bot.get_cog('RPGCore')
        if not rpg_core:
            await ctx.send("❌ RPG system not loaded.")
            return

        player_data = rpg_core.get_player_data(ctx.author.id)
        if not player_data:
            embed = create_embed("No Character", "Use `$startrpg` first!", COLORS['error'])
            await ctx.send(embed=embed)
            return

        if player_data.get('in_combat') or ctx.channel.id in active_combats:
            embed = create_embed("Already Fighting", "Finish your current battle first!", COLORS['warning'])
            await ctx.send(embed=embed)
            return

        if player_data['resources']['hp'] <= 0:
            embed = create_embed("No Health", "You need to heal first! Use a health potion.", COLORS['error'])
            await ctx.send(embed=embed)
            return

        # Select monster
        if monster_name:
            monster_key = monster_name.lower().replace(' ', '_')
            if monster_key not in ENHANCED_MONSTERS:
                available = ", ".join(ENHANCED_MONSTERS.keys())
                embed = create_embed("Monster Not Found", f"Available: {available}", COLORS['error'])
                await ctx.send(embed=embed)
                return
        else:
            # Level-appropriate random monster
            level = player_data.get('level', 1)
            if level >= 10:
                available_monsters = list(ENHANCED_MONSTERS.keys())
            elif level >= 5:
                available_monsters = ['goblin', 'orc', 'ice_elemental']
            else:
                available_monsters = ['goblin']

            monster_key = random.choice(available_monsters)

        # Start tactical combat
        player_data['in_combat'] = True
        rpg_core.save_player_data(ctx.author.id, player_data)

        embed = discord.Embed(
            title="⚔️ Tactical Combat Initiated!", 
            description="Preparing for enhanced battle...", 
            color=COLORS['primary']
        )
        message = await ctx.send(embed=embed)

        await asyncio.sleep(1)

        view = TacticalCombatView(ctx.author.id, monster_key, message, rpg_core)
        active_combats[ctx.channel.id] = view

        await view.update_view()

async def setup(bot):
    await bot.add_cog(RPGCombat(bot))