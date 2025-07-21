
import discord
from discord.ext import commands
import random
import time
from datetime import datetime, timedelta
from utils.helpers import create_embed, format_number
from utils.database import get_user_data, update_user_data, ensure_user_exists
from config import COLORS, is_module_enabled
import logging

logger = logging.getLogger(__name__)

class JobSelectionView(discord.ui.View):
    """Interactive job selection interface."""

    def __init__(self, user_id: str):
        super().__init__(timeout=180)
        self.user_id = user_id

    @discord.ui.select(
        placeholder="💼 Choose your job...",
        options=[
            discord.SelectOption(
                label="🧀 Cheese Taster",
                value="cheese_taster",
                description="Earn 100-200 gold • 1 hour cooldown",
                emoji="🧀"
            ),
            discord.SelectOption(
                label="🏛️ Museum Guide",
                value="museum_guide", 
                description="Earn 150-250 gold • 1 hour cooldown",
                emoji="🏛️"
            ),
            discord.SelectOption(
                label="🥖 Baker",
                value="baker",
                description="Earn 200-300 gold • 1 hour cooldown", 
                emoji="🥖"
            ),
            discord.SelectOption(
                label="🎭 Street Performer",
                value="performer",
                description="Earn 80-400 gold • Random results",
                emoji="🎭"
            ),
            discord.SelectOption(
                label="🕵️ Detective",
                value="detective",
                description="Earn 300-500 gold • 2 hour cooldown",
                emoji="🕵️"
            ),
            discord.SelectOption(
                label="⚔️ Akuma Hunter",
                value="akuma_hunter",
                description="Earn 500-800 gold • 3 hour cooldown • Dangerous",
                emoji="⚔️"
            )
        ]
    )
    async def job_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your job board!", ephemeral=True)
            return

        job = select.values[0]
        view = JobConfirmView(self.user_id, job)
        embed = view.create_job_embed()
        await interaction.response.edit_message(embed=embed, view=view)

class JobConfirmView(discord.ui.View):
    """Job confirmation and execution."""

    def __init__(self, user_id: str, job: str):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.job = job

        self.job_data = {
            'cheese_taster': {
                'name': '🧀 Cheese Taster',
                'description': 'Sample fine cheeses for Parisian restaurants',
                'min_pay': 100, 'max_pay': 200,
                'cooldown': 3600, 'risk': 0.05
            },
            'museum_guide': {
                'name': '🏛️ Museum Guide', 
                'description': 'Guide tourists through the Louvre',
                'min_pay': 150, 'max_pay': 250,
                'cooldown': 3600, 'risk': 0.02
            },
            'baker': {
                'name': '🥖 Baker',
                'description': 'Bake fresh bread and pastries',
                'min_pay': 200, 'max_pay': 300,
                'cooldown': 3600, 'risk': 0.03
            },
            'performer': {
                'name': '🎭 Street Performer',
                'description': 'Entertain crowds with your talents',
                'min_pay': 80, 'max_pay': 400,
                'cooldown': 3600, 'risk': 0.15
            },
            'detective': {
                'name': '🕵️ Detective',
                'description': 'Solve mysteries around Paris',
                'min_pay': 300, 'max_pay': 500,
                'cooldown': 7200, 'risk': 0.10
            },
            'akuma_hunter': {
                'name': '⚔️ Akuma Hunter',
                'description': 'Hunt dangerous akumatized villains',
                'min_pay': 500, 'max_pay': 800,
                'cooldown': 10800, 'risk': 0.25
            }
        }

    def create_job_embed(self):
        job_info = self.job_data[self.job]
        
        embed = discord.Embed(
            title=f"💼 Job Details: {job_info['name']}",
            description=job_info['description'],
            color=COLORS['primary']
        )

        embed.add_field(
            name="💰 Payment Range",
            value=f"{format_number(job_info['min_pay'])} - {format_number(job_info['max_pay'])} gold",
            inline=True
        )

        embed.add_field(
            name="⏰ Cooldown",
            value=f"{job_info['cooldown'] // 3600} hour(s)",
            inline=True
        )

        embed.add_field(
            name="⚠️ Risk Level",
            value=f"{int(job_info['risk'] * 100)}% chance of failure",
            inline=True
        )

        # Add job-specific flavor text
        flavor_texts = {
            'cheese_taster': "**Requirements:** Strong stomach, refined palate\n**Perks:** Free cheese samples!",
            'museum_guide': "**Requirements:** Art knowledge, patience\n**Perks:** Cultural enlightenment",
            'baker': "**Requirements:** Early rising, steady hands\n**Perks:** Warm workplace, free bread",
            'performer': "**Requirements:** Talent, thick skin\n**Perks:** Creative expression, tips vary wildly",
            'detective': "**Requirements:** Sharp mind, attention to detail\n**Perks:** Exciting cases, good reputation",
            'akuma_hunter': "**Requirements:** Combat experience, bravery\n**Perks:** Hero status, danger pay"
        }

        embed.add_field(
            name="📋 Job Information",
            value=flavor_texts.get(self.job, "Standard job requirements."),
            inline=False
        )

        return embed

    @discord.ui.button(label="✅ Accept Job", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_job(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your job!", ephemeral=True)
            return

        await interaction.response.defer()

        user_data = get_user_data(self.user_id) or {}
        last_work = user_data.get('last_work', 0)
        job_info = self.job_data[self.job]

        # Check cooldown
        if time.time() - last_work < job_info['cooldown']:
            remaining = job_info['cooldown'] - (time.time() - last_work)
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            
            embed = create_embed(
                "⏰ Still Working",
                f"You can work again in {hours}h {minutes}m!",
                COLORS['warning']
            )
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
            return

        # Work execution
        success = random.random() > job_info['risk']
        
        if success:
            earnings = random.randint(job_info['min_pay'], job_info['max_pay'])
            
            # Bonus chances
            bonus_chance = random.random()
            bonus_text = ""
            
            if bonus_chance < 0.1:  # 10% chance
                bonus = int(earnings * 0.5)
                earnings += bonus
                bonus_text = f"\n🎉 **Bonus:** +{bonus} gold for excellent work!"
            elif bonus_chance < 0.05:  # 5% chance  
                rare_bonus = int(earnings * 1.0)
                earnings += rare_bonus
                bonus_text = f"\n⭐ **Exceptional Work:** +{rare_bonus} gold bonus!"

            user_data['balance'] = user_data.get('balance', 0) + earnings
            user_data['last_work'] = time.time()
            
            # Work-specific success messages
            success_messages = {
                'cheese_taster': f"You identified a perfect aged Roquefort! The restaurant was impressed.",
                'museum_guide': f"Your tour group left glowing reviews! Tips included.",
                'baker': f"Your croissants were perfect! Customers lined up around the block.",
                'performer': f"Your performance drew a huge crowd! Hat filled with coins.",
                'detective': f"Case solved! Your deductive skills impressed the client.",
                'akuma_hunter': f"Akuma defeated! Paris is safer thanks to your bravery."
            }

            embed = discord.Embed(
                title="✅ Work Completed Successfully!",
                description=f"{success_messages.get(self.job, 'Job completed!')}\n\n"
                           f"💰 **Earned:** {format_number(earnings)} gold{bonus_text}",
                color=COLORS['success']
            )

        else:
            # Failure scenarios
            failure_messages = {
                'cheese_taster': "You got food poisoning from a bad cheese sample!",
                'museum_guide': "You gave incorrect information and were complained about!",
                'baker': "You burnt the bread and had to compensate for damages!",
                'performer': "Your performance flopped and you were booed off stage!",
                'detective': "The case went cold and the client refused to pay!",
                'akuma_hunter': "The akuma defeated you and you needed medical attention!"
            }

            penalty = random.randint(50, 150)
            user_data['balance'] = max(0, user_data.get('balance', 0) - penalty)
            user_data['last_work'] = time.time()

            embed = discord.Embed(
                title="❌ Work Failed!",
                description=f"{failure_messages.get(self.job, 'Job failed!')}\n\n"
                           f"💸 **Lost:** {format_number(penalty)} gold",
                color=COLORS['error']
            )

        update_user_data(self.user_id, user_data)
        await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.danger, emoji="❌")
    async def decline_job(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your job!", ephemeral=True)
            return

        embed = create_embed("Job Declined", "Maybe next time!", COLORS['secondary'])
        await interaction.response.edit_message(embed=embed, view=None)

class CasinoView(discord.ui.View):
    """Interactive casino with multiple games."""

    def __init__(self, user_id: str):
        super().__init__(timeout=300)
        self.user_id = user_id

    @discord.ui.select(
        placeholder="🎰 Choose your game...",
        options=[
            discord.SelectOption(
                label="🎰 Slot Machine",
                value="slots",
                description="Classic 3-reel slots • Various payouts",
                emoji="🎰"
            ),
            discord.SelectOption(
                label="🃏 Blackjack",
                value="blackjack",
                description="Beat the dealer • 21 or bust",
                emoji="🃏"
            ),
            discord.SelectOption(
                label="🎲 Dice Roll",
                value="dice",
                description="Roll doubles to win big",
                emoji="🎲"
            ),
            discord.SelectOption(
                label="🔮 Crystal Ball",
                value="crystal",
                description="Mystical predictions • High risk/reward",
                emoji="🔮"
            ),
            discord.SelectOption(
                label="🧀 Cheese Wheel",
                value="cheese_wheel",
                description="Plagg's favorite game • Cheese multipliers",
                emoji="🧀"
            )
        ]
    )
    async def game_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your casino!", ephemeral=True)
            return

        game = select.values[0]
        
        if game == "slots":
            view = SlotsView(self.user_id)
        elif game == "blackjack":
            view = BlackjackView(self.user_id)
        elif game == "dice":
            view = DiceView(self.user_id)
        elif game == "crystal":
            view = CrystalBallView(self.user_id)
        elif game == "cheese_wheel":
            view = CheeseWheelView(self.user_id)
        else:
            await interaction.response.send_message("Game not implemented yet!", ephemeral=True)
            return

        embed = view.create_game_embed()
        await interaction.response.edit_message(embed=embed, view=view)

class SlotsView(discord.ui.View):
    """Interactive slot machine game."""

    def __init__(self, user_id: str):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.bet_amount = 100

    def create_game_embed(self):
        embed = discord.Embed(
            title="🎰 Plagg's Slot Machine",
            description="**Welcome to the cheesiest slots in Paris!**\n\n"
                       "🧀 🧀 🧀 = 50x payout\n"
                       "💎 💎 💎 = 25x payout\n"
                       "⭐ ⭐ ⭐ = 10x payout\n"
                       "🍒 🍒 🍒 = 5x payout\n"
                       "Any 2 match = 2x payout\n\n"
                       f"**Current Bet:** {format_number(self.bet_amount)} gold",
            color=COLORS['gold']
        )
        return embed

    @discord.ui.select(
        placeholder="💰 Select bet amount...",
        options=[
            discord.SelectOption(label="100 gold", value="100", emoji="💰"),
            discord.SelectOption(label="500 gold", value="500", emoji="💰"),
            discord.SelectOption(label="1,000 gold", value="1000", emoji="💰"),
            discord.SelectOption(label="5,000 gold", value="5000", emoji="💰"),
            discord.SelectOption(label="10,000 gold", value="10000", emoji="💰"),
        ]
    )
    async def bet_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Not your game!", ephemeral=True)
            return

        self.bet_amount = int(select.values[0])
        embed = self.create_game_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🎰 SPIN!", style=discord.ButtonStyle.success, emoji="🎰")
    async def spin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Not your game!", ephemeral=True)
            return

        await interaction.response.defer()

        user_data = get_user_data(self.user_id) or {}
        balance = user_data.get('balance', 0)

        if balance < self.bet_amount:
            embed = create_embed("Insufficient Funds", f"You need {format_number(self.bet_amount)} gold to play!", COLORS['error'])
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
            return

        # Slot symbols
        symbols = ['🧀', '💎', '⭐', '🍒', '🎭', '🏆']
        weights = [5, 10, 20, 30, 25, 10]  # Cheese is rarest
        
        # Spin the reels
        reel1 = random.choices(symbols, weights=weights)[0]
        reel2 = random.choices(symbols, weights=weights)[0]  
        reel3 = random.choices(symbols, weights=weights)[0]

        # Calculate winnings
        multiplier = 0
        if reel1 == reel2 == reel3:
            if reel1 == '🧀':
                multiplier = 50
            elif reel1 == '💎':
                multiplier = 25
            elif reel1 == '⭐':
                multiplier = 10
            elif reel1 == '🍒':
                multiplier = 5
            else:
                multiplier = 3
        elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
            multiplier = 2

        winnings = self.bet_amount * multiplier
        net_change = winnings - self.bet_amount

        user_data['balance'] = balance + net_change
        update_user_data(self.user_id, user_data)

        if multiplier > 0:
            embed = discord.Embed(
                title="🎰 Slot Machine Results",
                description=f"**{reel1} {reel2} {reel3}**\n\n"
                           f"🎉 **Winner!** {multiplier}x multiplier\n"
                           f"💰 **Won:** {format_number(winnings)} gold\n"
                           f"📈 **Net:** +{format_number(net_change)} gold\n"
                           f"💳 **Balance:** {format_number(user_data['balance'])} gold",
                color=COLORS['success']
            )
        else:
            embed = discord.Embed(
                title="🎰 Slot Machine Results", 
                description=f"**{reel1} {reel2} {reel3}**\n\n"
                           f"💸 **No match!**\n"
                           f"📉 **Lost:** {format_number(self.bet_amount)} gold\n"
                           f"💳 **Balance:** {format_number(user_data['balance'])} gold",
                color=COLORS['error']
            )

        await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)

class Economy(commands.Cog):
    """Enhanced economy system with interactive UI."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="work", aliases=["job"])
    async def work(self, ctx):
        """Open the interactive job board."""
        if not is_module_enabled("economy", ctx.guild.id):
            return

        ensure_user_exists(str(ctx.author.id))
        
        view = JobSelectionView(str(ctx.author.id))
        embed = discord.Embed(
            title="💼 Paris Job Board",
            description="**Welcome to the Paris Employment Center!**\n\n"
                       "Choose from various jobs around the city to earn gold.\n"
                       "Each job has different pay rates, cooldowns, and risk levels.\n\n"
                       "💡 **Tips:**\n"
                       "• Higher risk = Higher reward\n"
                       "• Some jobs have longer cooldowns\n"
                       "• Success rate varies by job type\n"
                       "• Bonuses possible with excellent work",
            color=COLORS['primary']
        )
        embed.set_thumbnail(url="https://i.imgur.com/placeholder.png")
        
        await ctx.send(embed=embed, view=view)

    @commands.command(name="casino", aliases=["gamble", "bet"])
    async def casino(self, ctx):
        """Open the interactive casino."""
        if not is_module_enabled("economy", ctx.guild.id):
            return

        ensure_user_exists(str(ctx.author.id))
        
        view = CasinoView(str(ctx.author.id))
        embed = discord.Embed(
            title="🎰 Plagg's Lucky Casino",
            description="**Welcome to the most chaotic casino in Paris!**\n\n"
                       "Try your luck at various games of chance.\n"
                       "Remember: The house always wins... usually.\n\n"
                       "🎮 **Available Games:**\n"
                       "• Slot Machine - Classic 3-reel fun\n"
                       "• Blackjack - Beat the dealer\n"
                       "• Dice Roll - Double or nothing\n"
                       "• Crystal Ball - Mystical predictions\n"
                       "• Cheese Wheel - Plagg's special game",
            color=COLORS['gold']
        )
        embed.set_footer(text="⚠️ Gamble responsibly! Only bet what you can afford to lose.")
        
        await ctx.send(embed=embed, view=view)

    @commands.command(name="balance", aliases=["bal", "money"])
    async def balance(self, ctx, member: discord.Member = None):
        """Check gold balance with interactive display."""
        target = member or ctx.author
        user_data = get_user_data(str(target.id)) or {}
        balance = user_data.get('balance', 0)

        embed = discord.Embed(
            title=f"💰 {target.display_name}'s Wealth",
            color=COLORS['gold']
        )

        embed.add_field(
            name="Current Balance",
            value=f"💰 {format_number(balance)} gold",
            inline=False
        )

        # Add wealth ranking
        if balance >= 1000000:
            rank = "🏆 Millionaire"
        elif balance >= 100000:
            rank = "💎 Rich"
        elif balance >= 10000:
            rank = "💰 Well-off"
        elif balance >= 1000:
            rank = "🥉 Comfortable"
        else:
            rank = "🪙 Getting Started"

        embed.add_field(name="Wealth Rank", value=rank, inline=True)

        # Add recent activity if available
        last_work = user_data.get('last_work', 0)
        if last_work > 0:
            time_since = time.time() - last_work
            if time_since < 86400:  # Less than 24 hours
                hours = int(time_since // 3600)
                embed.add_field(name="Last Worked", value=f"{hours} hours ago", inline=True)

        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
