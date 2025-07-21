import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta
from replit import db
from utils.database import get_user_data, update_user_data, ensure_user_exists, get_user_rpg_data, update_user_rpg_data
from utils.helpers import create_embed, format_number, level_up_player, get_random_work_job, get_time_until_next_use, format_time_remaining
from utils.constants import SHOP_ITEMS, ITEMS, RPG_CONSTANTS, DAILY_REWARDS
from utils.rng_system import roll_with_luck, generate_loot_with_luck
from config import COLORS, EMOJIS, is_module_enabled
import logging

logger = logging.getLogger(__name__)

class AuctionView(discord.ui.View):
    """View for auction house interactions."""
    
    def __init__(self, auction_data):
        super().__init__(timeout=300)
        self.auction_data = auction_data
        
    @discord.ui.button(label="Place Bid", style=discord.ButtonStyle.primary, emoji="💰")
    async def place_bid(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Place a bid on the auction."""
        # Implementation for bidding
        await interaction.response.send_message("Bidding feature coming soon!", ephemeral=True)

class EconomyCog(commands.Cog):
    """Economy and shop system for the bot."""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_auctions = {}  # auction_id -> auction_data
        self.user_investments = {}  # user_id -> investments
        
    @commands.command(name='work', help='Work to earn coins')
    @commands.cooldown(1, RPG_CONSTANTS['work_cooldown'], commands.BucketType.user)
    async def work(self, ctx):
        """Work to earn coins."""
        if not is_module_enabled("economy", ctx.guild.id):
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
            last_work = player_data.get('last_work')
            if last_work:
                cooldown_remaining = get_time_until_next_use(last_work, RPG_CONSTANTS['work_cooldown'])
                if cooldown_remaining > 0:
                    embed = create_embed(
                        "⏰ Work Cooldown",
                        f"You can work again in {format_time_remaining(cooldown_remaining)}",
                        COLORS['warning']
                    )
                    await ctx.send(embed=embed)
                    return
            
            # Get random job
            job = get_random_work_job()
            base_coins = random.randint(job["min_coins"], job["max_coins"])
            base_xp = random.randint(job["min_xp"], job["max_xp"])
            
            # Apply luck and level bonuses
            loot = generate_loot_with_luck(user_id, {
                'coins': base_coins,
                'xp': base_xp
            })
            
            coins_earned = loot['coins']
            xp_earned = loot['xp']
            
            # Level bonus
            level_bonus = int(coins_earned * 0.1 * player_data['level'])
            coins_earned += level_bonus
            
            # Weekend bonus
            from utils.helpers import get_daily_bonus_multiplier
            weekend_multiplier = get_daily_bonus_multiplier()
            if weekend_multiplier > 1:
                coins_earned = int(coins_earned * weekend_multiplier)
                xp_earned = int(xp_earned * weekend_multiplier)
            
            # Update player data
            player_data['coins'] += coins_earned
            player_data['xp'] += xp_earned
            player_data['last_work'] = datetime.now().isoformat()
            player_data['work_count'] = player_data.get('work_count', 0) + 1
            
            # Update stats
            if 'stats' not in player_data:
                player_data['stats'] = {}
            player_data['stats']['total_coins_earned'] = player_data['stats'].get('total_coins_earned', 0) + coins_earned
            player_data['stats']['total_xp_earned'] = player_data['stats'].get('total_xp_earned', 0) + xp_earned
            
            # Check for level up
            level_up_msg = level_up_player(player_data)
            
            # Random event check
            if roll_with_luck(user_id, 0.1):  # 10% chance
                bonus_coins = random.randint(20, 100)
                player_data['coins'] += bonus_coins
                bonus_msg = f"\n🎲 Lucky bonus: +{bonus_coins} coins!"
            else:
                bonus_msg = ""
                
            # Save data
            update_user_rpg_data(user_id, player_data)
            
            description = (
                f"You worked as a **{job['name']}** and earned:\n"
                f"💰 {format_number(coins_earned)} coins\n"
                f"⭐ {xp_earned} XP\n"
                f"🎯 Level bonus: +{level_bonus} coins{bonus_msg}"
            )
            
            if weekend_multiplier > 1:
                description += f"\n🎊 Weekend bonus applied! ({weekend_multiplier}x)"
            
            description += f"\n\nTotal coins: {format_number(player_data['coins'])}"
            
            embed = create_embed(
                f"💼 Work Complete!",
                description,
                COLORS['success']
            )
            
            if level_up_msg:
                embed.add_field(name="🎉 Level Up!", value=level_up_msg, inline=False)
                
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in work command for {user_id}: {e}")
            await ctx.send("❌ An error occurred while working. Please try again.")
        
    @commands.command(name='daily', help='Claim your daily reward')
    @commands.cooldown(1, RPG_CONSTANTS['daily_cooldown'], commands.BucketType.user)
    async def daily_reward(self, ctx):
        """Claim daily reward."""
        if not is_module_enabled("economy", ctx.guild.id):
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
            last_daily = player_data.get('last_daily')
            if last_daily:
                cooldown_remaining = get_time_until_next_use(last_daily, RPG_CONSTANTS['daily_cooldown'])
                if cooldown_remaining > 0:
                    embed = create_embed(
                        "⏰ Daily Cooldown",
                        f"You can claim your daily reward in {format_time_remaining(cooldown_remaining)}",
                        COLORS['warning']
                    )
                    await ctx.send(embed=embed)
                    return
            
            # Calculate streak
            daily_streak = player_data.get('daily_streak', 0)
            last_daily_dt = None
            
            if last_daily:
                try:
                    last_daily_dt = datetime.fromisoformat(last_daily)
                    # Check if it's been exactly 1 day (with some tolerance)
                    time_diff = datetime.now() - last_daily_dt
                    if time_diff.days == 1:
                        daily_streak += 1
                    elif time_diff.days > 1:
                        daily_streak = 1  # Reset streak
                    else:
                        daily_streak = 1  # First claim
                except:
                    daily_streak = 1
            else:
                daily_streak = 1
            
            # Cap streak at max
            daily_streak = min(daily_streak, DAILY_REWARDS['max_streak'])
            
            # Calculate rewards
            base_reward = DAILY_REWARDS['base']
            level_bonus = player_data['level'] * DAILY_REWARDS['level_multiplier']
            streak_bonus = (daily_streak - 1) * DAILY_REWARDS['streak_bonus']
            
            total_reward = base_reward + level_bonus + streak_bonus
            
            # Apply luck
            loot = generate_loot_with_luck(user_id, {'coins': total_reward})
            final_reward = loot['coins']
            
            # Random bonus
            bonus_text = ""
            if roll_with_luck(user_id, 0.2):  # 20% chance with luck
                bonus_amount = random.randint(100, 500)
                final_reward += bonus_amount
                bonus_text = f"\n🎲 Lucky bonus: +{bonus_amount} coins!"
                
            # Update player data
            player_data['coins'] += final_reward
            player_data['last_daily'] = datetime.now().isoformat()
            player_data['daily_streak'] = daily_streak
            
            # Update stats
            if 'stats' not in player_data:
                player_data['stats'] = {}
            player_data['stats']['total_coins_earned'] = player_data['stats'].get('total_coins_earned', 0) + final_reward
            
            # Save data
            update_user_rpg_data(user_id, player_data)
            
            embed = create_embed(
                "🎁 Daily Reward Claimed!",
                f"You received **{format_number(final_reward)}** coins!\n"
                f"Base reward: {base_reward}\n"
                f"Level bonus: {level_bonus}\n"
                f"Streak bonus: {streak_bonus} (Day {daily_streak}){bonus_text}\n\n"
                f"Total coins: {format_number(player_data['coins'])}",
                COLORS['warning']
            )
            
            if daily_streak >= DAILY_REWARDS['max_streak']:
                embed.add_field(
                    name="🔥 Max Streak!",
                    value=f"You've reached the maximum daily streak of {DAILY_REWARDS['max_streak']} days!",
                    inline=False
                )
            
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in daily command for {user_id}: {e}")
            await ctx.send("❌ An error occurred while claiming daily reward. Please try again.")
        
    @commands.command(name='shop', help='View the item shop')
    async def shop(self, ctx):
        """Display the item shop."""
        if not is_module_enabled("economy", ctx.guild.id):
            return
            
        try:
            embed = discord.Embed(
                title="🏪 Item Shop",
                description="Use `$buy <item>` to purchase items\nUse `$sell <item>` to sell items",
                color=COLORS['info']
            )
            
            for category, items in SHOP_ITEMS.items():
                item_list = []
                for item_name, item_data in items.items():
                    price = item_data.get('price', 0)
                    rarity = item_data.get('rarity', 'common')
                    
                    # Get rarity emoji
                    rarity_emojis = {
                        'common': '⚪',
                        'uncommon': '🟢',
                        'rare': '🔵',
                        'epic': '🟣',
                        'legendary': '🟡',
                        'mythical': '🔴'
                    }
                    rarity_emoji = rarity_emojis.get(rarity, '⚪')
                    
                    # Add stats info
                    stats = []
                    if 'attack' in item_data:
                        stats.append(f"ATK+{item_data['attack']}")
                    if 'defense' in item_data:
                        stats.append(f"DEF+{item_data['defense']}")
                    if 'hp' in item_data:
                        stats.append(f"HP+{item_data['hp']}")
                    
                    stats_text = f" [{', '.join(stats)}]" if stats else ""
                    item_list.append(f"{rarity_emoji} **{item_name}**{stats_text} - 💰 {format_number(price)}")
                    
                embed.add_field(
                    name=f"{category.title()}",
                    value="\n".join(item_list),
                    inline=False
                )
                
            embed.set_footer(text="💡 Higher level items unlock as you progress!")
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in shop command: {e}")
            await ctx.send("❌ An error occurred while displaying the shop. Please try again.")
        
    @commands.command(name='buy', help='Buy an item from the shop')
    async def buy_item(self, ctx, *, item_name: str):
        """Buy an item from the shop."""
        if not is_module_enabled("economy", ctx.guild.id):
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
            
            # Find item in shop
            found_item = None
            item_category = None
            
            for category, items in SHOP_ITEMS.items():
                for shop_item, item_data in items.items():
                    if shop_item.lower() == item_name.lower():
                        found_item = shop_item
                        item_category = category
                        break
                if found_item:
                    break
                    
            if not found_item:
                # Suggest similar items
                suggestions = []
                for category, items in SHOP_ITEMS.items():
                    for shop_item in items.keys():
                        if item_name.lower() in shop_item.lower():
                            suggestions.append(shop_item)
                
                suggestion_text = ""
                if suggestions:
                    suggestion_text = f"\n\n**Did you mean:**\n" + "\n".join(f"• {item}" for item in suggestions[:5])
                
                embed = create_embed(
                    "❌ Item Not Found",
                    f"Item '{item_name}' not found in shop! Use `$shop` to see available items.{suggestion_text}",
                    COLORS['error']
                )
                await ctx.send(embed=embed)
                return
                
            item_data = SHOP_ITEMS[item_category][found_item]
            price = item_data['price']
            
            # Apply guild discount if applicable
            discount = 0
            # TODO: Implement guild discount system
            
            final_price = int(price * (1 - discount))
            
            # Check if player has enough coins
            if player_data['coins'] < final_price:
                embed = create_embed(
                    "❌ Insufficient Funds",
                    f"You need {format_number(final_price)} coins but only have {format_number(player_data['coins'])}.\n"
                    f"You need {format_number(final_price - player_data['coins'])} more coins!",
                    COLORS['error']
                )
                await ctx.send(embed=embed)
                return
                
            # Check inventory space
            if len(player_data.get('inventory', [])) >= RPG_CONSTANTS['max_inventory_size']:
                embed = create_embed(
                    "❌ Inventory Full",
                    f"Your inventory is full! ({RPG_CONSTANTS['max_inventory_size']} items max)\n"
                    f"Sell some items first with `$sell <item>`",
                    COLORS['error']
                )
                await ctx.send(embed=embed)
                return
                
            # Process purchase
            player_data['coins'] -= final_price
            if 'inventory' not in player_data:
                player_data['inventory'] = []
            player_data['inventory'].append(found_item)
            
            # Save data
            update_user_rpg_data(user_id, player_data)
            
            # Create purchase embed
            rarity = item_data.get('rarity', 'common')
            from utils.helpers import get_rarity_color, get_rarity_emoji
            
            embed = discord.Embed(
                title="✅ Purchase Successful!",
                description=f"You bought **{found_item}** for {format_number(final_price)} coins!",
                color=get_rarity_color(rarity)
            )
            
            if discount > 0:
                embed.add_field(
                    name="💰 Discount Applied",
                    value=f"Original price: {format_number(price)}\n"
                          f"Discount: {discount*100:.1f}%\n"
                          f"Final price: {format_number(final_price)}",
                    inline=False
                )
            
            embed.add_field(
                name="💳 Account Balance",
                value=f"Remaining coins: {format_number(player_data['coins'])}",
                inline=False
            )
            
            # Show item stats
            stats = []
            if 'attack' in item_data:
                stats.append(f"⚔️ Attack: +{item_data['attack']}")
            if 'defense' in item_data:
                stats.append(f"🛡️ Defense: +{item_data['defense']}")
            if 'hp' in item_data:
                stats.append(f"❤️ HP: +{item_data['hp']}")
            
            if stats:
                embed.add_field(
                    name="📊 Item Stats",
                    value="\n".join(stats),
                    inline=False
                )
            
            embed.set_footer(text="Use $equip <item> to equip weapons and armor!")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in buy command for {user_id}: {e}")
            await ctx.send("❌ An error occurred while purchasing the item. Please try again.")

    @commands.command(name='sell', help='Sell items from your inventory')
    async def sell_item(self, ctx, *, item_name: str):
        """Sell an item from inventory."""
        if not is_module_enabled("economy", ctx.guild.id):
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
            if 'inventory' not in player_data:
                player_data['inventory'] = []
                
            # Find exact or partial match
            found_item = None
            for item in player_data['inventory']:
                if item.lower() == item_name.lower():
                    found_item = item
                    break
            
            if not found_item:
                # Try partial match
                for item in player_data['inventory']:
                    if item_name.lower() in item.lower():
                        found_item = item
                        break
            
            if not found_item:
                embed = create_embed(
                    "❌ Item Not Found",
                    f"You don't have '{item_name}' in your inventory!\n"
                    f"Use `$inventory` to see your items.",
                    COLORS['error']
                )
                await ctx.send(embed=embed)
                return
                
            # Find item data to determine sell price
            sell_price = 0
            for category, items in SHOP_ITEMS.items():
                if found_item in items:
                    sell_price = int(items[found_item]['price'] * 0.6)  # 60% of buy price
                    break
                    
            if sell_price == 0:
                # Default sell price for non-shop items
                sell_price = random.randint(10, 50)
                
            # Process sale
            player_data['inventory'].remove(found_item)
            player_data['coins'] += sell_price
            
            # Save data
            update_user_rpg_data(user_id, player_data)
            
            embed = create_embed(
                "💰 Item Sold!",
                f"You sold **{found_item}** for {format_number(sell_price)} coins!\n\n"
                f"Total coins: {format_number(player_data['coins'])}",
                COLORS['success']
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in sell command for {user_id}: {e}")
            await ctx.send("❌ An error occurred while selling the item. Please try again.")

    @commands.command(name='auction', help='Access the auction house')
    async def auction_house(self, ctx, action: str = None, *, args: str = None):
        """Access the auction house."""
        if not is_module_enabled("economy", ctx.guild.id):
            return
            
        if action is None:
            # Show active auctions
            embed = discord.Embed(
                title="🏛️ Auction House",
                description="Use `$auction list` to see active auctions\n"
                           "Use `$auction create <item> <starting_bid>` to create an auction",
                color=COLORS['info']
            )
            await ctx.send(embed=embed)
            return
        
        if action.lower() == 'list':
            # Show active auctions
            embed = discord.Embed(
                title="🏛️ Active Auctions",
                description="No active auctions at the moment.",
                color=COLORS['info']
            )
            await ctx.send(embed=embed)
        
        elif action.lower() == 'create':
            # Create new auction
            embed = discord.Embed(
                title="🚧 Coming Soon",
                description="Auction creation is coming in a future update!",
                color=COLORS['warning']
            )
            await ctx.send(embed=embed)
        
        else:
            embed = create_embed(
                "❌ Invalid Action",
                "Valid actions: `list`, `create`",
                COLORS['error']
            )
            await ctx.send(embed=embed)

    @commands.command(name='invest', help='Invest coins for passive income')
    async def invest(self, ctx, amount: int = None):
        """Invest coins for passive income."""
        if not is_module_enabled("economy", ctx.guild.id):
            return
            
        if amount is None:
            # Show investment info
            embed = discord.Embed(
                title="📈 Investment System",
                description="Invest your coins to earn passive income!\n\n"
                           "**How it works:**\n"
                           "• Minimum investment: 1,000 coins\n"
                           "• Daily return: 2-5% (random)\n"
                           "• Risk: You might lose some coins on bad days\n"
                           "• Withdraw anytime with `$invest withdraw`",
                color=COLORS['info']
            )
            await ctx.send(embed=embed)
            return
        
        user_id = str(ctx.author.id)
        
        if not ensure_user_exists(user_id):
            await ctx.send("❌ You need to `$start` your adventure first!")
            return
        
        # Implementation placeholder
        embed = discord.Embed(
            title="🚧 Coming Soon",
            description="Investment system is coming in a future update!",
            color=COLORS['warning']
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
