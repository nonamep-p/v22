import discord
from discord.ext import commands
from replit import db
import random
import asyncio
from datetime import datetime
from rpg_data.game_data import TACTICAL_MONSTERS, ITEMS
from utils.helpers import create_embed, format_number
from config import COLORS, is_module_enabled
import logging

logger = logging.getLogger(__name__)

# Dungeon definitions
DUNGEONS = {
    'goblin_caves': {
        'name': 'Goblin Caves',
        'emoji': '🕳️',
        'min_level': 1,
        'max_level': 5,
        'floors': 3,
        'description': 'Dark caves filled with goblin tribes and their treasure hoards.',
        'monsters': ['goblin_warrior', 'goblin_warrior', 'frost_elemental'],
        'boss': 'goblin_chieftain',
        'rewards': {
            'xp_multiplier': 1.5,
            'gold_multiplier': 1.3,
            'rare_materials': ['goblin_fang', 'cave_crystal', 'iron_ore']
        }
    },
    'shadow_fortress': {
        'name': 'Shadow Fortress',
        'emoji': '🏰',
        'min_level': 8,
        'max_level': 15,
        'floors': 5,
        'description': 'An ancient fortress consumed by darkness and shadowy beings.',
        'monsters': ['shadow_assassin', 'shadow_assassin', 'frost_elemental'],
        'boss': 'shadow_lord',
        'rewards': {
            'xp_multiplier': 2.0,
            'gold_multiplier': 1.8,
            'rare_materials': ['shadow_essence', 'dark_crystal', 'enchanted_steel']
        }
    },
    'dragons_lair': {
        'name': "Dragon's Lair",
        'emoji': '🐉',
        'min_level': 20,
        'max_level': 30,
        'floors': 7,
        'description': 'The lair of an ancient dragon, filled with legendary treasures.',
        'monsters': ['ancient_dragon', 'frost_elemental', 'shadow_assassin'],
        'boss': 'ancient_red_dragon',
        'rewards': {
            'xp_multiplier': 3.0,
            'gold_multiplier': 2.5,
            'rare_materials': ['dragon_scale', 'dragon_heart', 'legendary_gem']
        }
    }
}

class DungeonExplorationView(discord.ui.View):
    """Interactive dungeon exploration interface."""

    def __init__(self, player_id, dungeon_key, rpg_core):
        super().__init__(timeout=600)  # 10 minute timeout
        self.player_id = player_id
        self.dungeon_key = dungeon_key
        self.rpg_core = rpg_core
        self.dungeon_data = DUNGEONS[dungeon_key]

        # Dungeon state
        self.current_floor = 1
        self.rooms_explored = 0
        self.total_rooms = self.dungeon_data['floors'] * 3  # 3 rooms per floor
        self.completed = False
        self.treasures_found = []
        self.monsters_defeated = 0

        # Load player data
        self.player_data = self.rpg_core.get_player_data(player_id)
        if not self.player_data:
            self.stop()
            return

    async def update_view(self):
        """Update the dungeon exploration interface."""
        embed = self.create_dungeon_embed()

        # Clear existing buttons
        self.clear_items()

        if not self.completed:
            if self.rooms_explored < self.total_rooms:
                self.add_item(ExploreButton())
                self.add_item(SearchButton())
                self.add_item(RestButton())
                self.add_item(ExitDungeonButton())
            else:
                # Boss room
                self.add_item(FightBossButton())
                self.add_item(ExitDungeonButton())

        try:
            await self.message.edit(embed=embed, view=self)
        except discord.NotFound:
            pass

    def create_dungeon_embed(self):
        """Create the dungeon exploration display."""
        embed = discord.Embed(
            title=f"{self.dungeon_data['emoji']} {self.dungeon_data['name']}",
            description=self.dungeon_data['description'],
            color=COLORS['warning']
        )

        # Player status
        player_resources = self.player_data['resources']
        hp_bar = self.create_health_bar(player_resources['hp'], player_resources['max_hp'])

        status_text = (f"**Level:** {self.player_data['level']}\n"
                      f"**HP:** {hp_bar} {player_resources['hp']}/{player_resources['max_hp']}\n"
                      f"**Gold:** {format_number(self.player_data['gold'])}")
        embed.add_field(name="🛡️ Adventurer Status", value=status_text, inline=True)

        # Dungeon progress
        progress_percentage = (self.rooms_explored / self.total_rooms) * 100
        progress_bar = self.create_progress_bar(progress_percentage)

        progress_text = (f"**Floor:** {self.current_floor}/{self.dungeon_data['floors']}\n"
                        f"**Rooms:** {self.rooms_explored}/{self.total_rooms}\n"
                        f"**Progress:** {progress_bar} {int(progress_percentage)}%")
        embed.add_field(name="🗺️ Exploration Progress", value=progress_text, inline=True)

        # Dungeon stats
        stats_text = (f"**Monsters Defeated:** {self.monsters_defeated}\n"
                     f"**Treasures Found:** {len(self.treasures_found)}\n"
                     f"**Recommended Level:** {self.dungeon_data['min_level']}-{self.dungeon_data['max_level']}")
        embed.add_field(name="📊 Dungeon Stats", value=stats_text, inline=True)

        if self.rooms_explored >= self.total_rooms and not self.completed:
            embed.add_field(
                name="🐉 Boss Encounter!",
                value=f"You've reached the final chamber!\n**Boss:** {self.dungeon_data['boss'].replace('_', ' ').title()}\n\nPrepare for the ultimate challenge!",
                inline=False
            )

        if self.treasures_found:
            treasure_text = ", ".join([t.replace('_', ' ').title() for t in self.treasures_found[-5:]])  # Show last 5
            embed.add_field(name="💎 Recent Treasures", value=treasure_text, inline=False)

        embed.set_footer(text="Choose your next action carefully - dungeons are dangerous!")
        return embed

    def create_health_bar(self, current, maximum):
        """Create a visual health bar."""
        if maximum == 0:
            return "▱▱▱▱▱▱▱▱▱▱"

        percentage = current / maximum
        filled_blocks = int(percentage * 10)
        empty_blocks = 10 - filled_blocks

        return "▰" * filled_blocks + "▱" * empty_blocks

    def create_progress_bar(self, percentage):
        """Create a visual progress bar."""
        filled_blocks = int(percentage / 10)
        empty_blocks = 10 - filled_blocks

        return "🟦" * filled_blocks + "⬜" * empty_blocks

class ExploreButton(discord.ui.Button):
    """Explore the next room in the dungeon."""

    def __init__(self):
        super().__init__(label="🔍 Explore Room", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if interaction.user.id != view.player_id:
            await interaction.response.send_message("Not your dungeon exploration!", ephemeral=True)
            return

        # Explore next room
        view.rooms_explored += 1

        # Update current floor
        view.current_floor = ((view.rooms_explored - 1) // 3) + 1

        # Random encounter
        encounter_roll = random.random()

        if encounter_roll < 0.6:  # 60% chance for monster
            await view.encounter_monster(interaction)
        elif encounter_roll < 0.8:  # 20% chance for treasure
            await view.find_treasure(interaction)
        else:  # 20% chance for special event
            await view.special_event(interaction)

    async def encounter_monster(self, interaction):
        """Handle monster encounter."""
        view = self.view
        available_monsters = view.dungeon_data['monsters']
        monster_key = random.choice(available_monsters)

        if monster_key in TACTICAL_MONSTERS:
            # Start combat
            from cogs.rpg_combat import TacticalCombatView, active_combats

            embed = discord.Embed(
                title="⚔️ Monster Encounter!",
                description=f"A wild **{TACTICAL_MONSTERS[monster_key]['name']}** blocks your path!\n\nPreparing for combat...",
                color=COLORS['error']
            )

            # Check if interaction was already responded to
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=None)
            else:
                await interaction.response.edit_message(embed=embed, view=None)

            # Create combat instance with unique key
            combat_key = f"{interaction.channel.id}_{interaction.user.id}_{datetime.now().timestamp()}"
            combat_view = TacticalCombatView(view.player_id, monster_key, view.message, view.rpg_core)
            combat_view.is_dungeon_combat = True
            combat_view.dungeon_view = view
            active_combats[combat_key] = combat_view

            await combat_view.update_view()
            view.monsters_defeated += 1
        else:
            if not interaction.response.is_done():
                await interaction.response.send_message("Monster encounter system needs updating!", ephemeral=True)

    async def find_treasure(self, interaction):
        """Handle treasure discovery."""
        view = self.view

        # Random treasure based on dungeon
        possible_treasures = view.dungeon_data['rewards']['rare_materials']
        treasure = random.choice(possible_treasures)
        quantity = random.randint(1, 3)

        # Add to inventory
        if treasure in view.player_data['inventory']:
            view.player_data['inventory'][treasure] += quantity
        else:
            view.player_data['inventory'][treasure] = quantity

        view.treasures_found.append(treasure)

        # Gold reward
        gold_reward = random.randint(50, 200) * view.dungeon_data['rewards']['gold_multiplier']
        view.player_data['gold'] += int(gold_reward)

        view.rpg_core.save_player_data(view.player_id, view.player_data)

        embed = discord.Embed(
            title="💎 Treasure Found!",
            description=f"You discovered a hidden chest!\n\n"
                       f"**Found:**\n"
                       f"• {treasure.replace('_', ' ').title()} x{quantity}\n"
                       f"• {format_number(int(gold_reward))} Gold",
            color=COLORS['success']
        )

        await interaction.response.edit_message(embed=embed, view=view)
        await asyncio.sleep(2)
        await view.update_view()

    async def special_event(self, interaction):
        """Handle special dungeon events."""
        view = self.view

        events = [
            {
                'title': '🔮 Mystical Fountain',
                'description': 'You find a magical fountain that restores your health!',
                'effect': 'heal'
            },
            {
                'title': '💀 Cursed Altar',
                'description': 'A cursed altar saps some of your health but grants mysterious power...',
                'effect': 'curse'
            },
            {
                'title': '📚 Ancient Tome',
                'description': 'You discover an ancient tome that grants you knowledge!',
                'effect': 'xp'
            }
        ]

        event = random.choice(events)

        if event['effect'] == 'heal':
            heal_amount = view.player_data['resources']['max_hp'] // 3
            view.player_data['resources']['hp'] = min(
                view.player_data['resources']['max_hp'],
                view.player_data['resources']['hp'] + heal_amount
            )
        elif event['effect'] == 'curse':
            damage = view.player_data['resources']['max_hp'] // 4
            view.player_data['resources']['hp'] = max(1, view.player_data['resources']['hp'] - damage)
        elif event['effect'] == 'xp':
            xp_bonus = view.player_data['level'] * 50
            view.player_data['xp'] += xp_bonus
            view.rpg_core.level_up_check(view.player_data)

        view.rpg_core.save_player_data(view.player_id, view.player_data)

        embed = discord.Embed(
            title=event['title'],
            description=event['description'],
            color=COLORS['info']
        )

        await interaction.response.edit_message(embed=embed, view=view)
        await asyncio.sleep(2)
        await view.update_view()

class SearchButton(discord.ui.Button):
    """Search the current room more thoroughly."""

    def __init__(self):
        super().__init__(label="🔎 Search Thoroughly", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if interaction.user.id != view.player_id:
            await interaction.response.send_message("Not your dungeon exploration!", ephemeral=True)
            return

        # Thorough search has chance for better rewards but takes time
        search_roll = random.random()

        if search_roll < 0.3:  # 30% chance for special find
            rare_materials = view.dungeon_data['rewards']['rare_materials']
            item = random.choice(rare_materials)
            quantity = random.randint(2, 5)  # More than normal exploration

            if item in view.player_data['inventory']:
                view.player_data['inventory'][item] += quantity
            else:
                view.player_data['inventory'][item] = quantity

            view.rpg_core.save_player_data(view.player_id, view.player_data)

            embed = discord.Embed(
                title="🔍 Thorough Search Success!",
                description=f"Your careful search pays off!\n\n**Found:** {item.replace('_', ' ').title()} x{quantity}",
                color=COLORS['success']
            )
        else:
            embed = discord.Embed(
                title="🔍 Search Complete",
                description="You search the room carefully but find nothing of value.\n\nSometimes patience doesn't pay off...",
                color=COLORS['secondary']
            )

        await interaction.response.edit_message(embed=embed, view=view)
        await asyncio.sleep(2)
        await view.update_view()

class RestButton(discord.ui.Button):
    """Rest to recover health and mana."""

    def __init__(self):
        super().__init__(label="😴 Rest", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if interaction.user.id != view.player_id:
            await interaction.response.send_message("Not your dungeon exploration!", ephemeral=True)
            return

        # Rest mechanics
        hp_restored = view.player_data['resources']['max_hp'] // 4
        mana_restored = view.player_data['resources']['max_mana'] // 3

        view.player_data['resources']['hp'] = min(
            view.player_data['resources']['max_hp'],
            view.player_data['resources']['hp'] + hp_restored
        )
        view.player_data['resources']['mana'] = min(
            view.player_data['resources']['max_mana'],
            view.player_data['resources']['mana'] + mana_restored
        )

        view.rpg_core.save_player_data(view.player_id, view.player_data)

        # Small chance of random encounter while resting
        if random.random() < 0.15:  # 15% chance
            embed = discord.Embed(
                title="😴 Ambushed While Resting!",
                description="Your rest is interrupted by a monster attack!\n\nYou managed to recover some health before the fight...",
                color=COLORS['warning']
            )
            await interaction.response.edit_message(embed=embed, view=view)
            await asyncio.sleep(2)

            # Trigger monster encounter
            await ExploreButton().encounter_monster(interaction)
        else:
            embed = discord.Embed(
                title="😴 Peaceful Rest",
                description=f"You rest safely and recover your strength.\n\n"
                           f"**Recovered:**\n"
                           f"• {hp_restored} HP\n"
                           f"• {mana_restored} Mana",
                color=COLORS['success']
            )
            await interaction.response.edit_message(embed=embed, view=view)
            await asyncio.sleep(2)
            await view.update_view()

class FightBossButton(discord.ui.Button):
    """Fight the dungeon boss."""

    def __init__(self):
        super().__init__(label="🐉 Fight Boss", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if interaction.user.id != view.player_id:
            await interaction.response.send_message("Not your dungeon exploration!", ephemeral=True)
            return

        boss_key = view.dungeon_data['boss']

        embed = discord.Embed(
            title="🐉 BOSS ENCOUNTER!",
            description=f"You face the master of this dungeon!\n\n**{boss_key.replace('_', ' ').title()}** awaits in the final chamber!\n\nThis will be your greatest challenge yet...",
            color=COLORS['error']
        )

        await interaction.response.edit_message(embed=embed, view=None)

        # Start boss combat
        from cogs.rpg_combat import TacticalCombatView, active_combats

        combat_view = TacticalCombatView(view.player_id, boss_key, view.message, view.rpg_core)
        combat_view.is_boss_fight = True
        combat_view.dungeon_view = view
        active_combats[interaction.channel.id] = combat_view

        await combat_view.update_view()

class ExitDungeonButton(discord.ui.Button):
    """Exit the dungeon."""

    def __init__(self):
        super().__init__(label="🚪 Exit Dungeon", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if interaction.user.id != view.player_id:
            await interaction.response.send_message("Not your dungeon exploration!", ephemeral=True)
            return

        # Mark player as no longer in dungeon
        view.player_data['in_combat'] = False
        view.rpg_core.save_player_data(view.player_id, view.player_data)

        embed = discord.Embed(
            title="🚪 Exited Dungeon",
            description=f"You emerge from the **{view.dungeon_data['name']}**.\n\n"
                       f"**Final Stats:**\n"
                       f"• Rooms Explored: {view.rooms_explored}/{view.total_rooms}\n"
                       f"• Monsters Defeated: {view.monsters_defeated}\n"
                       f"• Treasures Found: {len(view.treasures_found)}",
            color=COLORS['secondary']
        )

        await interaction.response.edit_message(embed=embed, view=None)
        view.stop()

class RPGDungeons(commands.Cog):
    """Advanced dungeon exploration system."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="dungeons")
    async def dungeons(self, ctx, dungeon_name: str = None):
        """Enter a dungeon for extended exploration and greater rewards."""
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

        if player_data.get('in_combat'):
            embed = create_embed("Already Exploring", "Finish your current adventure first!", COLORS['warning'])
            await ctx.send(embed=embed)
            return

        if not dungeon_name:
            # Show available dungeons
            embed = discord.Embed(
                title="🏰 Available Dungeons",
                description="Choose your dungeon adventure wisely!",
                color=COLORS['warning']
            )

            for dungeon_key, dungeon_data in DUNGEONS.items():
                level_range = f"Level {dungeon_data['min_level']}-{dungeon_data['max_level']}"
                floors = f"{dungeon_data['floors']} floors"

                embed.add_field(
                    name=f"{dungeon_data['emoji']} {dungeon_data['name']}",
                    value=f"{dungeon_data['description']}\n\n**Difficulty:** {level_range}\n**Size:** {floors}",
                    inline=False
                )

            embed.set_footer(text="Use $dungeons <name> to enter a specific dungeon")
            await ctx.send(embed=embed)
            return

        # Find dungeon
        dungeon_key = None
        for key, data in DUNGEONS.items():
            if dungeon_name.lower() in data['name'].lower().replace(' ', '_'):
                dungeon_key = key
                break

        if not dungeon_key:
            embed = create_embed("Dungeon Not Found", f"No dungeon named '{dungeon_name}' exists!", COLORS['error'])
            await ctx.send(embed=embed)
            return

        dungeon_data = DUNGEONS[dungeon_key]

        # Check level requirement
        if player_data['level'] < dungeon_data['min_level']:
            embed = create_embed(
                "Level Too Low", 
                f"You need to be at least Level {dungeon_data['min_level']} to enter {dungeon_data['name']}!\nCurrent level: {player_data['level']}", 
                COLORS['warning']
            )
            await ctx.send(embed=embed)
            return

        # Check health
        if player_data['resources']['hp'] < player_data['resources']['max_hp'] * 0.5:
            embed = create_embed("Low Health", "You should heal before entering a dangerous dungeon!", COLORS['warning'])
            await ctx.send(embed=embed)
            return

        # Mark player as in dungeon
        player_data['in_combat'] = True
        rpg_core.save_player_data(ctx.author.id, player_data)

        # Create dungeon exploration
        embed = discord.Embed(
            title=f"🏰 Entering {dungeon_data['name']}",
            description=f"{dungeon_data['description']}\n\nYou step into the dark entrance...\n\nPrepare for an extended adventure!",
            color=COLORS['warning']
        )

        message = await ctx.send(embed=embed)

        # Start exploration
        view = DungeonExplorationView(ctx.author.id, dungeon_key, rpg_core)
        view.message = message

        await asyncio.sleep(2)
        await view.update_view()

    

async def setup(bot):
    await bot.add_cog(RPGDungeons(bot))