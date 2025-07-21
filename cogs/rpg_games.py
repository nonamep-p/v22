import discord
from discord.ext import commands
import random
import time
from utils.helpers import create_embed, format_number
from config import COLORS, is_module_enabled
import logging

logger = logging.getLogger(__name__)

class RPGGames(commands.Cog):
    """Fun RPG mini-games and activities."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hunt")
    async def hunt_monsters(self, ctx):
        """Hunt for monsters and treasure."""
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

        # Check cooldown
        last_hunt = player_data.get('last_hunt', 0)
        cooldown = 1800  # 30 minutes

        if time.time() - last_hunt < cooldown:
            remaining = cooldown - (time.time() - last_hunt)
            minutes = int(remaining // 60)
            await ctx.send(f"⏰ You can hunt again in {minutes} minutes!")
            return

        # Update cooldown
        player_data['last_hunt'] = time.time()

        # Hunt encounter
        encounters = [
            {"name": "Goblin Scout", "xp": 25, "gold": 15, "item": "health_potion"},
            {"name": "Wild Boar", "xp": 30, "gold": 20, "item": None},
            {"name": "Bandit", "xp": 35, "gold": 25, "item": "iron_sword"},
            {"name": "Forest Spirit", "xp": 40, "gold": 30, "item": "mana_potion"}
        ]

        encounter = random.choice(encounters)

        # Battle simulation
        victory = random.random() > 0.3  # 70% success rate

        if victory:
            player_data['xp'] += encounter['xp']
            player_data['gold'] += encounter['gold']

            if encounter['item']:
                if encounter['item'] in player_data['inventory']:
                    player_data['inventory'][encounter['item']] += 1
                else:
                    player_data['inventory'][encounter['item']] = 1

            # Check for level up
            levels_gained = rpg_core.level_up_check(player_data)

            embed = discord.Embed(
                title="🏹 Successful Hunt!",
                description=f"You defeated a **{encounter['name']}**!",
                color=COLORS['success']
            )
            embed.add_field(name="Rewards", value=f"• {encounter['xp']} XP\n• {encounter['gold']} Gold", inline=True)

            if encounter['item']:
                embed.add_field(name="Item Found", value=encounter['item'].replace('_', ' ').title(), inline=True)

            if levels_gained:
                embed.add_field(name="⭐ Level Up!", value=f"You are now level {player_data['level']}!", inline=False)

        else:
            # Failure - lose some health
            damage = random.randint(10, 25)
            player_data['resources']['hp'] = max(1, player_data['resources']['hp'] - damage)

            embed = discord.Embed(
                title="💀 Hunt Failed",
                description=f"You encountered a **{encounter['name']}** but were defeated!",
                color=COLORS['error']
            )
            embed.add_field(name="Consequence", value=f"Lost {damage} HP", inline=True)

        rpg_core.save_player_data(ctx.author.id, player_data)
        await ctx.send(embed=embed)

    @commands.command(name="explore")
    async def explore_world(self, ctx):
        """Explore the world for discoveries."""
        if not is_module_enabled("rpg", ctx.guild.id):
            return

        rpg_core = self.bot.get_cog('RPGCore')
        if not rpg_core:
            await ctx.send("❌ RPG system not loaded.")
            return

        # Check if player is in combat first
        if rpg_core.is_player_in_combat(ctx.author.id):
            embed = discord.Embed(
                title="⚔️ Already Fighting!",
                description="You're currently in combat! Finish your current battle first.",
                color=COLORS['warning']
            )
            from .rpg_core import CombatEscapeView
            view = CombatEscapeView(str(ctx.author.id), rpg_core)
            await ctx.send(embed=embed, view=view)
            return

        player_data = rpg_core.get_player_data(ctx.author.id)
        if not player_data:
            embed = create_embed("No Character", "Use `$startrpg` first!", COLORS['error'])
            await ctx.send(embed=embed)
            return

        # Check cooldown
        last_explore = player_data.get('last_explore', 0)
        cooldown = 2700  # 45 minutes

        if time.time() - last_explore < cooldown:
            remaining = cooldown - (time.time() - last_explore)
            minutes = int(remaining // 60)
            await ctx.send(f"⏰ You can explore again in {minutes} minutes!")
            return

        # Update cooldown
        player_data['last_explore'] = time.time()

        discoveries = [
            {"name": "Ancient Chest", "gold": 50, "item": "rare_gem"},
            {"name": "Hidden Cave", "xp": 40, "gold": 30},
            {"name": "Merchant Camp", "item": "health_potion", "quantity": 3},
            {"name": "Mystical Spring", "heal": 50},
            {"name": "Abandoned Tower", "xp": 60, "gold": 45}
        ]

        discovery = random.choice(discoveries)

        embed = discord.Embed(
            title="🗺️ Exploration Discovery!",
            description=f"You discovered: **{discovery['name']}**",
            color=COLORS['primary']
        )

        rewards = []
        if 'xp' in discovery:
            player_data['xp'] += discovery['xp']
            rewards.append(f"• {discovery['xp']} XP")

        if 'gold' in discovery:
            player_data['gold'] += discovery['gold']
            rewards.append(f"• {discovery['gold']} Gold")

        if 'item' in discovery:
            item_name = discovery['item']
            quantity = discovery.get('quantity', 1)
            if item_name in player_data['inventory']:
                player_data['inventory'][item_name] += quantity
            else:
                player_data['inventory'][item_name] = quantity
            rewards.append(f"• {quantity}x {item_name.replace('_', ' ').title()}")

        if 'heal' in discovery:
            old_hp = player_data['resources']['hp']
            player_data['resources']['hp'] = min(
                player_data['resources']['max_hp'],
                old_hp + discovery['heal']
            )
            actual_heal = player_data['resources']['hp'] - old_hp
            rewards.append(f"• Healed {actual_heal} HP")

        if rewards:
            embed.add_field(name="Rewards", value="\n".join(rewards), inline=False)

        # Check for level up
        levels_gained = rpg_core.level_up_check(player_data)
        if levels_gained:
            embed.add_field(name="⭐ Level Up!", value=f"You are now level {player_data['level']}!", inline=False)

        rpg_core.save_player_data(ctx.author.id, player_data)
        await ctx.send(embed=embed)

    @commands.command(name="dungeon")
    async def enter_dungeon(self, ctx, dungeon_name: str = None):
        """Enter a dungeon for challenging adventures."""
        if not is_module_enabled("rpg", ctx.guild.id):
            return

        rpg_core = self.bot.get_cog('RPGCore')
        if not rpg_core:
            await ctx.send("❌ RPG system not loaded.")
            return

        player_data = rpg_core.get_player_data(ctx.author.id)
        if not player_data:
            embed = create_embed("No Character", "Use `$startrpg` first!", COLORS['error'])
            return

        dungeons = {
            'sewers': {'name': 'Sewer Depths', 'min_level': 1, 'reward_mult': 1.0},
            'cathedral': {'name': 'Abandoned Cathedral', 'min_level': 10, 'reward_mult': 1.5},
            'stronghold': {'name': 'Akuma Stronghold', 'min_level': 20, 'reward_mult': 2.0},
            'shadow': {'name': 'Shadow Realm', 'min_level': 30, 'reward_mult': 2.5},
            'void': {'name': 'Cosmic Void', 'min_level': 40, 'reward_mult': 3.0}
        }

        if not dungeon_name:
            embed = discord.Embed(title="🏰 Available Dungeons", color=COLORS['primary'])
            dungeon_list = ""
            for key, data in dungeons.items():
                dungeon_list += f"• **{data['name']}** (Level {data['min_level']}+)\n"
            embed.add_field(name="Dungeons", value=dungeon_list, inline=False)
            embed.set_footer(text="Use $dungeon <name> to enter")
            await ctx.send(embed=embed)
            return

        # Find dungeon
        dungeon_key = dungeon_name.lower()
        dungeon = None
        for key, data in dungeons.items():
            if key.startswith(dungeon_key) or data['name'].lower().startswith(dungeon_key):
                dungeon = data
                break

        if not dungeon:
            await ctx.send("❌ Dungeon not found! Use `$dungeon` to see available dungeons.")
            return

        if player_data['level'] < dungeon['min_level']:
            await ctx.send(f"❌ You need Level {dungeon['min_level']} to enter {dungeon['name']}!")
            return

        if player_data['resources']['stamina'] < 20:
            await ctx.send("❌ You need 20 Stamina to enter a dungeon!")
            return

        # Consume stamina
        player_data['resources']['stamina'] -= 20

        # Dungeon run simulation
        success = random.random() > 0.4  # 60% success rate

        if success:
            base_xp = 80
            base_gold = 60
            xp_reward = int(base_xp * dungeon['reward_mult'])
            gold_reward = int(base_gold * dungeon['reward_mult'])

            player_data['xp'] += xp_reward
            player_data['gold'] += gold_reward

            # Rare loot chance
            if random.random() < 0.3:  # 30% chance
                rare_items = ['legendary_weapon', 'mythical_armor', 'rare_artifact']
                item = random.choice(rare_items)
                if item in player_data['inventory']:
                    player_data['inventory'][item] += 1
                else:
                    player_data['inventory'][item] = 1

            embed = discord.Embed(
                title="🏆 Dungeon Cleared!",
                description=f"You successfully cleared **{dungeon['name']}**!",
                color=COLORS['success']
            )
            embed.add_field(name="Rewards", value=f"• {xp_reward} XP\n• {gold_reward} Gold", inline=True)

        else:
            # Failure
            damage = random.randint(20, 40)
            player_data['resources']['hp'] = max(1, player_data['resources']['hp'] - damage)

            embed = discord.Embed(
                title="💀 Dungeon Failed",
                description=f"You were defeated in **{dungeon['name']}**!",
                color=COLORS['error']
            )
            embed.add_field(name="Consequence", value=f"Lost {damage} HP", inline=True)

        # Check for level up
        if success:
            levels_gained = rpg_core.level_up_check(player_data)
            if levels_gained:
                embed.add_field(name="⭐ Level Up!", value=f"You are now level {player_data['level']}!", inline=False)

        rpg_core.save_player_data(ctx.author.id, player_data)
        await ctx.send(embed=embed)

    @commands.command(name="miraculous", aliases=["box"])
    async def miraculous_box(self, ctx):
        """Enter the Miraculous Box for artifact farming."""
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

        if player_data['resources']['miraculous_energy'] < 40:
            await ctx.send("❌ You need 40 Miraculous Energy to enter the box!")
            return

        # Consume energy
        player_data['resources']['miraculous_energy'] -= 40

        # Artifact rewards
        artifacts = [
            'ladybug_earrings', 'cat_ring', 'bee_comb', 'fox_necklace',
            'turtle_bracelet', 'peacock_brooch', 'butterfly_pin'
        ]

        artifact = random.choice(artifacts)
        if artifact in player_data['inventory']:
            player_data['inventory'][artifact] += 1
        else:
            player_data['inventory'][artifact] = 1

        xp_reward = random.randint(40, 80)
        player_data['xp'] += xp_reward

        embed = discord.Embed(
            title="✨ Miraculous Box Expedition",
            description="You ventured into the mystical Miraculous Box dimension!",
            color=COLORS['legendary']
        )
        embed.add_field(
            name="Artifact Found",
            value=artifact.replace('_', ' ').title(),
            inline=True
        )
        embed.add_field(name="XP Gained", value=str(xp_reward), inline=True)

        # Check for level up
        levels_gained = rpg_core.level_up_check(player_data)
        if levels_gained:
            embed.add_field(name="⭐ Level Up!", value=f"You are now level {player_data['level']}!", inline=False)

        rpg_core.save_player_data(ctx.author.id, player_data)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RPGGames(bot))