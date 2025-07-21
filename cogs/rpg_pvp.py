
import discord
from discord.ext import commands
import random
import asyncio
from utils.helpers import create_embed, format_number
from config import COLORS, is_module_enabled
import logging

logger = logging.getLogger(__name__)

class PvPCombatView(discord.ui.View):
    """PvP combat interface."""
    
    def __init__(self, player_id, opponent_data, rpg_core):
        super().__init__(timeout=300)
        self.player_id = player_id
        self.opponent = opponent_data
        self.rpg_core = rpg_core
        self.combat_log = []
        self.turn = 'player'
        
        # Load player data
        self.player_data = self.rpg_core.get_player_data(player_id)
        
        self.add_log(f"⚔️ PvP Battle: {self.player_data.get('name', 'Player')} vs {self.opponent['name']}")
        
    def add_log(self, text):
        """Add entry to combat log."""
        self.combat_log.append(f"• {text}")
        if len(self.combat_log) > 6:
            self.combat_log.pop(0)

    def create_bar(self, current, maximum, length=8):
        """Create visual progress bar."""
        if maximum == 0:
            return "░" * length
        percentage = current / maximum
        filled = int(percentage * length)
        return "█" * filled + "░" * (length - filled)

    async def create_embed(self):
        """Generate PvP combat embed."""
        embed = discord.Embed(
            title=f"⚔️ PvP Arena Battle",
            color=COLORS['error']
        )

        # Player status
        player_resources = self.player_data['resources']
        player_hp_bar = self.create_bar(player_resources['hp'], player_resources['max_hp'])
        
        embed.add_field(
            name=f"👤 {self.player_data.get('name', 'Player')} (Lv.{self.player_data['level']})",
            value=f"❤️ **HP:** {player_resources['hp']}/{player_resources['max_hp']} {player_hp_bar}\n"
                  f"⚔️ **Attack:** {self.player_data['derived_stats']['attack']}\n"
                  f"🛡️ **Defense:** {self.player_data['derived_stats']['defense']}",
            inline=True
        )

        # Opponent status
        opponent_hp_bar = self.create_bar(self.opponent['hp'], self.opponent['max_hp'])
        
        embed.add_field(
            name=f"🤖 {self.opponent['name']} (Lv.{self.opponent['level']})",
            value=f"❤️ **HP:** {self.opponent['hp']}/{self.opponent['max_hp']} {opponent_hp_bar}\n"
                  f"⚔️ **Attack:** {self.opponent['attack']}\n"
                  f"🛡️ **Defense:** {self.opponent['defense']}",
            inline=True
        )

        # Turn indicator
        turn_text = "🎯 **Your Turn**" if self.turn == 'player' else "🔴 **Opponent's Turn**"
        embed.add_field(name="Current Turn", value=turn_text, inline=False)

        # Combat log
        if self.combat_log:
            log_content = "\n".join(self.combat_log[-6:])
            embed.add_field(name="📜 Combat Log", value=f"```{log_content}```", inline=False)

        return embed

    async def update_view(self):
        """Update combat display."""
        # Update button states
        for item in self.children:
            if hasattr(item, 'label'):
                item.disabled = (
                    self.turn != 'player' or
                    self.player_data['resources']['hp'] <= 0 or
                    self.opponent['hp'] <= 0
                )

        embed = await self.create_embed()
        try:
            await self.message.edit(embed=embed, view=self)
        except discord.NotFound:
            pass

    async def end_combat(self, victory):
        """Handle PvP combat conclusion."""
        if victory:
            # Calculate rating change
            rating_change = random.randint(15, 35)
            self.player_data['arena_rating'] += rating_change
            self.player_data['arena_wins'] += 1
            
            # Rewards
            gold_reward = random.randint(100, 300)
            xp_reward = random.randint(50, 150)
            tokens_reward = random.randint(2, 5)
            
            self.player_data['gold'] += gold_reward
            self.player_data['xp'] += xp_reward
            self.player_data['arena_tokens'] = self.player_data.get('arena_tokens', 0) + tokens_reward
            
            self.add_log(f"🏆 Victory! +{rating_change} rating, +{gold_reward} gold, +{tokens_reward} tokens!")
            
            final_embed = discord.Embed(
                title="🏆 PvP VICTORY! 🏆",
                description=f"**Rewards:**\n"
                           f"• +{rating_change} Arena Rating\n"
                           f"• +{gold_reward} Gold\n"
                           f"• +{xp_reward} XP\n"
                           f"• +{tokens_reward} Arena Tokens\n\n"
                           f"**New Rating:** {self.player_data['arena_rating']}",
                color=COLORS['success']
            )
        else:
            # Defeat
            rating_change = random.randint(-25, -10)
            self.player_data['arena_rating'] = max(0, self.player_data['arena_rating'] + rating_change)
            self.player_data['arena_losses'] += 1
            
            self.add_log(f"💀 Defeat! {rating_change} rating")
            
            final_embed = discord.Embed(
                title="💀 PvP DEFEAT 💀",
                description=f"**Results:**\n"
                           f"• {rating_change} Arena Rating\n"
                           f"• Learn from this defeat!\n\n"
                           f"**Current Rating:** {self.player_data['arena_rating']}",
                color=COLORS['error']
            )

        # Add combat log to final embed
        if self.combat_log:
            log_content = "\n".join(self.combat_log)
            final_embed.add_field(name="📜 Combat Summary", value=f"```{log_content}```", inline=False)

        # Level up check
        levels_gained = self.rpg_core.level_up_check(self.player_data)
        if levels_gained:
            final_embed.add_field(
                name="⭐ Level Up!",
                value=f"You gained {levels_gained} level(s)! You are now level {self.player_data['level']}!",
                inline=False
            )

        self.rpg_core.save_player_data(self.player_id, self.player_data)

        try:
            await self.message.edit(embed=final_embed, view=None)
        except discord.NotFound:
            pass
        self.stop()

    async def opponent_turn(self):
        """AI opponent turn."""
        # Simple AI: attack or use skill randomly
        if random.random() < 0.3:  # 30% chance to use special attack
            damage = random.randint(self.opponent['attack'], self.opponent['attack'] + 20)
            self.add_log(f"{self.opponent['name']} uses Special Attack for {damage} damage!")
        else:
            damage = random.randint(self.opponent['attack'] - 5, self.opponent['attack'] + 5)
            self.add_log(f"{self.opponent['name']} attacks for {damage} damage!")

        # Apply damage to player
        defense = self.player_data['derived_stats']['defense']
        actual_damage = max(1, damage - defense // 2)
        self.player_data['resources']['hp'] = max(0, self.player_data['resources']['hp'] - actual_damage)

        self.turn = 'player'
        await self.update_view()

        # Check for player defeat
        if self.player_data['resources']['hp'] <= 0:
            await self.end_combat(victory=False)

    @discord.ui.button(label="⚔️ Attack", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("Not your PvP match!", ephemeral=True)
            return

        await interaction.response.defer()

        # Player attacks
        base_damage = self.player_data['derived_stats']['attack']
        damage = random.randint(base_damage - 5, base_damage + 10)

        # Check for critical hit
        crit_chance = self.player_data['derived_stats'].get('critical_chance', 0.05)
        if random.random() < crit_chance:
            damage = int(damage * 1.5)
            self.add_log(f"💥 CRITICAL HIT! You deal {damage} damage!")
        else:
            self.add_log(f"⚔️ You attack for {damage} damage!")

        # Apply damage to opponent
        defense = self.opponent['defense']
        actual_damage = max(1, damage - defense // 2)
        self.opponent['hp'] = max(0, self.opponent['hp'] - actual_damage)

        self.turn = 'opponent'
        await self.update_view()
        await asyncio.sleep(1.5)

        # Check for victory
        if self.opponent['hp'] <= 0:
            await self.end_combat(victory=True)
            return

        await self.opponent_turn()

    @discord.ui.button(label="🛡️ Defend", style=discord.ButtonStyle.secondary, emoji="🛡️")
    async def defend(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("Not your PvP match!", ephemeral=True)
            return

        await interaction.response.defer()

        # Defensive stance - reduce next incoming damage
        self.player_data['defending'] = True
        self.add_log("🛡️ You take a defensive stance!")

        self.turn = 'opponent'
        await self.update_view()
        await asyncio.sleep(1)
        await self.opponent_turn()

    @discord.ui.button(label="🏃 Forfeit", style=discord.ButtonStyle.secondary, emoji="🏃")
    async def forfeit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("Not your PvP match!", ephemeral=True)
            return

        await interaction.response.defer()

        self.add_log("🏃 You forfeit the match!")
        await self.end_combat(victory=False)

class RPGPvP(commands.Cog):
    """PvP system with arena battles."""
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="pvp", aliases=["arena"])
    async def pvp_arena(self, ctx):
        """Enter the PvP arena for ranked battles."""
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
            
        if player_data['level'] < 5:
            embed = create_embed(
                "Level Too Low", 
                f"You need Level 5 to enter PvP! Current: {player_data['level']}", 
                COLORS['warning']
            )
            await ctx.send(embed=embed)
            return
            
        if player_data.get('in_combat'):
            embed = create_embed("Already Fighting", "Finish your current battle first!", COLORS['warning'])
            await ctx.send(embed=embed)
            return

        if player_data['resources']['hp'] <= 0:
            embed = create_embed("No Health", "Heal first before entering PvP!", COLORS['error'])
            await ctx.send(embed=embed)
            return

        # Generate AI opponent based on player level and rating
        opponent = self.generate_ai_opponent(player_data)

        embed = discord.Embed(
            title="🔍 Finding PvP Match...",
            description="Searching for a worthy opponent...",
            color=COLORS['primary']
        )
        message = await ctx.send(embed=embed)
        await asyncio.sleep(2)

        # Show opponent found
        embed = discord.Embed(
            title="⚔️ PvP Match Found!",
            description=f"**Opponent:** {opponent['name']} (Level {opponent['level']})\n"
                       f"**Rating:** {opponent['rating']}\n"
                       f"**Record:** {opponent['wins']}-{opponent['losses']}\n\n"
                       f"**Arena Stakes:** Rating points and arena tokens!",
            color=COLORS['error']
        )
        await message.edit(embed=embed)
        await asyncio.sleep(2)

        # Start PvP combat
        combat_view = PvPCombatView(ctx.author.id, opponent, rpg_core)
        combat_view.message = message
        await combat_view.update_view()

    def generate_ai_opponent(self, player_data):
        """Generate AI opponent based on player stats."""
        level_variance = random.randint(-2, 2)
        opponent_level = max(1, player_data['level'] + level_variance)
        
        rating_variance = random.randint(-50, 50)
        opponent_rating = max(100, player_data.get('arena_rating', 1000) + rating_variance)
        
        # Generate stats based on level
        base_hp = 100 + (opponent_level * 10)
        base_attack = 15 + (opponent_level * 3)
        base_defense = 8 + (opponent_level * 2)

        # Generate realistic win/loss record
        total_matches = random.randint(10, 100)
        win_rate = 0.45 + (random.random() * 0.1)  # 45-55% win rate
        wins = int(total_matches * win_rate)
        losses = total_matches - wins
        
        opponent_names = [
            "ShadowStrike", "BladeDancer", "FrostMage", "ArcaneTempest", 
            "StealthHunter", "IronGuard", "LightningBolt", "ChaosReign",
            "MysticSage", "CrimsonFury", "VoidWalker", "StarShaper",
            "DragonSlayer", "PhoenixRise", "DarkKnight", "LightBringer"
        ]
        
        return {
            'name': random.choice(opponent_names),
            'level': opponent_level,
            'hp': base_hp,
            'max_hp': base_hp,
            'attack': base_attack,
            'defense': base_defense,
            'rating': opponent_rating,
            'wins': wins,
            'losses': losses,
            'is_ai': True
        }

    @commands.command(name="rankings", aliases=["leaderboard"])
    async def pvp_rankings(self, ctx):
        """View PvP leaderboards."""
        if not is_module_enabled("rpg", ctx.guild.id):
            return

        embed = discord.Embed(
            title="🏆 PvP Arena Rankings",
            description="Top warriors in competitive combat:",
            color=COLORS['primary']
        )

        # Sample leaderboard (in a real implementation, this would query all players)
        sample_rankings = [
            {"name": "ChampionDestroyer", "rating": 2847, "record": "247-23"},
            {"name": "BladeMaster2000", "rating": 2756, "record": "198-31"},
            {"name": "MysticSage", "rating": 2643, "record": "156-22"},
            {"name": "IronFist", "rating": 2521, "record": "134-28"},
            {"name": "ShadowAssassin", "rating": 2398, "record": "112-19"}
        ]

        ranking_text = ""
        for i, player in enumerate(sample_rankings, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            ranking_text += f"{emoji} **{player['name']}** - {player['rating']} ({player['record']})\n"

        embed.add_field(name="🏆 Top Players", value=ranking_text, inline=False)

        # Show current player's ranking if they have data
        rpg_core = self.bot.get_cog('RPGCore')
        if rpg_core:
            player_data = rpg_core.get_player_data(ctx.author.id)
            if player_data:
                wins = player_data.get('arena_wins', 0)
                losses = player_data.get('arena_losses', 0)
                rating = player_data.get('arena_rating', 1000)
                
                embed.add_field(
                    name="📊 Your Stats",
                    value=f"**Rating:** {rating}\n"
                          f"**Record:** {wins}-{losses}\n"
                          f"**Tokens:** {player_data.get('arena_tokens', 0)}",
                    inline=False
                )

        embed.set_footer(text="Compete in ranked matches to climb the leaderboard!")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RPGPvP(bot))
