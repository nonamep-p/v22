
import discord
from discord.ext import commands
import random
from utils.helpers import create_embed, format_number
from config import COLORS, is_module_enabled
from rpg_data.game_data import ITEMS, RARITY_COLORS
import logging

logger = logging.getLogger(__name__)

class ShopCategoryView(discord.ui.View):
    """Interactive shop category selection."""

    def __init__(self, user_id: str, rpg_core):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.rpg_core = rpg_core

    @discord.ui.select(
        placeholder="🛒 Select a shop category...",
        options=[
            discord.SelectOption(
                label="⚔️ Weapons",
                value="weapons",
                description="Swords, bows, staves and more",
                emoji="⚔️"
            ),
            discord.SelectOption(
                label="🛡️ Armor", 
                value="armor",
                description="Protection for your adventures",
                emoji="🛡️"
            ),
            discord.SelectOption(
                label="🧪 Consumables",
                value="consumables", 
                description="Potions and temporary items",
                emoji="🧪"
            ),
            discord.SelectOption(
                label="💎 Accessories",
                value="accessories",
                description="Rings, amulets and trinkets",
                emoji="💎"
            ),
            discord.SelectOption(
                label="✨ Artifacts",
                value="artifacts",
                description="Rare and powerful items",
                emoji="✨"
            ),
            discord.SelectOption(
                label="🎁 Mystery Boxes",
                value="mystery",
                description="Random rewards await!",
                emoji="🎁"
            )
        ]
    )
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your shop!", ephemeral=True)
            return

        category = select.values[0]
        view = ShopItemView(self.user_id, category, self.rpg_core)
        embed = view.create_category_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="💰 My Gold", style=discord.ButtonStyle.secondary, emoji="💰")
    async def check_gold(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your shop!", ephemeral=True)
            return

        player_data = self.rpg_core.get_player_data(self.user_id)
        if not player_data:
            await interaction.response.send_message("❌ Character not found!", ephemeral=True)
            return

        embed = discord.Embed(
            title="💰 Your Wealth",
            description=f"**Current Gold:** {format_number(player_data['gold'])}\n\n"
                       f"**Recent Transactions:**\n"
                       f"• Last shop visit: Today\n"
                       f"• Items owned: {len(player_data.get('inventory', {}))}\n"
                       f"• Net worth: {format_number(player_data['gold'] * 1.2)}",
            color=COLORS['gold']
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ShopItemView(discord.ui.View):
    """Interactive item browsing and purchasing."""

    def __init__(self, user_id: str, category: str, rpg_core):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.category = category
        self.rpg_core = rpg_core
        self.current_page = 0
        self.items_per_page = 5

        # Filter items by category
        self.category_items = []
        for item_key, item_data in ITEMS.items():
            if item_data.get('type') == category or (category == 'mystery' and 'box' in item_key):
                self.category_items.append((item_key, item_data))

    def create_category_embed(self):
        embed = discord.Embed(
            title=f"🛒 Shop - {self.category.title()}",
            color=COLORS['primary']
        )

        if not self.category_items:
            embed.description = "No items available in this category."
            return embed

        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = self.category_items[start_idx:end_idx]

        items_text = ""
        for i, (item_key, item_data) in enumerate(page_items, start_idx + 1):
            rarity_color = RARITY_COLORS.get(item_data.get('rarity', 'common'), 0x808080)
            price = item_data.get('price', 100)
            
            items_text += f"**{i}.** {item_data['name']}\n"
            items_text += f"💰 {format_number(price)} gold\n"
            items_text += f"⭐ {item_data.get('rarity', 'common').title()}\n"
            items_text += f"📝 {item_data.get('description', 'No description')}\n\n"

        embed.description = items_text
        embed.set_footer(text=f"Page {self.current_page + 1}/{(len(self.category_items) - 1) // self.items_per_page + 1}")

        return embed

    @discord.ui.select(
        placeholder="🛍️ Select an item to purchase...",
        min_values=1,
        max_values=1
    )
    async def item_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your shop!", ephemeral=True)
            return

        # Populate dropdown with current page items
        if not hasattr(self, '_populated'):
            start_idx = self.current_page * self.items_per_page
            end_idx = start_idx + self.items_per_page
            page_items = self.category_items[start_idx:end_idx]

            select.options = []
            for i, (item_key, item_data) in enumerate(page_items):
                select.options.append(
                    discord.SelectOption(
                        label=item_data['name'],
                        value=item_key,
                        description=f"{format_number(item_data.get('price', 100))} gold",
                        emoji="💎" if item_data.get('rarity') == 'legendary' else "⭐"
                    )
                )
            self._populated = True

        item_key = select.values[0]
        view = PurchaseConfirmView(self.user_id, item_key, self.rpg_core)
        embed = view.create_purchase_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your shop!", ephemeral=True)
            return

        if self.current_page > 0:
            self.current_page -= 1
            self._populated = False
            embed = self.create_category_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your shop!", ephemeral=True)
            return

        max_pages = (len(self.category_items) - 1) // self.items_per_page + 1
        if self.current_page < max_pages - 1:
            self.current_page += 1
            self._populated = False
            embed = self.create_category_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔙 Back to Categories", style=discord.ButtonStyle.success)
    async def back_to_categories(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your shop!", ephemeral=True)
            return

        view = ShopCategoryView(self.user_id, self.rpg_core)
        embed = discord.Embed(
            title="🛒 Plagg's Cheese & Combat Shop",
            description="**Welcome to the finest shop in all dimensions!**\n\n"
                       "Here you can find everything from powerful weapons to magical cheese wheels.\n"
                       "Choose a category below to browse available items.\n\n"
                       "💰 **Shop Features:**\n"
                       "• Quality guaranteed by Plagg himself\n"
                       "• Instant delivery to your inventory\n"
                       "• Cheese-powered discounts available\n"
                       "• No returns (destroyed items stay destroyed)",
            color=COLORS['primary']
        )
        embed.set_thumbnail(url="https://i.imgur.com/placeholder.png")
        await interaction.response.edit_message(embed=embed, view=view)

class PurchaseConfirmView(discord.ui.View):
    """Purchase confirmation with quantity selection."""

    def __init__(self, user_id: str, item_key: str, rpg_core):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.item_key = item_key
        self.rpg_core = rpg_core
        self.quantity = 1

    def create_purchase_embed(self):
        item_data = ITEMS.get(self.item_key, {})
        player_data = self.rpg_core.get_player_data(self.user_id)
        
        price = item_data.get('price', 100)
        total_cost = price * self.quantity
        can_afford = player_data['gold'] >= total_cost if player_data else False

        embed = discord.Embed(
            title="🛍️ Purchase Confirmation",
            color=COLORS['success'] if can_afford else COLORS['error']
        )

        embed.add_field(
            name="📦 Item Details",
            value=f"**{item_data.get('name', 'Unknown Item')}**\n"
                  f"⭐ {item_data.get('rarity', 'common').title()}\n"
                  f"📝 {item_data.get('description', 'No description')}\n"
                  f"💰 {format_number(price)} gold each",
            inline=False
        )

        embed.add_field(
            name="🧮 Purchase Summary",
            value=f"**Quantity:** {self.quantity}\n"
                  f"**Total Cost:** {format_number(total_cost)} gold\n"
                  f"**Your Gold:** {format_number(player_data['gold']) if player_data else 'Unknown'}\n"
                  f"**After Purchase:** {format_number(player_data['gold'] - total_cost) if player_data and can_afford else 'Insufficient'}",
            inline=False
        )

        if not can_afford:
            embed.add_field(
                name="❌ Cannot Afford",
                value=f"You need {format_number(total_cost - player_data['gold'])} more gold!",
                inline=False
            )

        return embed

    @discord.ui.select(
        placeholder="📦 Select quantity...",
        options=[
            discord.SelectOption(label="1x", value="1", emoji="1️⃣"),
            discord.SelectOption(label="5x", value="5", emoji="5️⃣"),
            discord.SelectOption(label="10x", value="10", emoji="🔟"),
            discord.SelectOption(label="25x", value="25", emoji="📦"),
            discord.SelectOption(label="50x", value="50", emoji="📦"),
        ]
    )
    async def quantity_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your purchase!", ephemeral=True)
            return

        self.quantity = int(select.values[0])
        embed = self.create_purchase_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="✅ Confirm Purchase", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm_purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your purchase!", ephemeral=True)
            return

        await interaction.response.defer()

        player_data = self.rpg_core.get_player_data(self.user_id)
        if not player_data:
            embed = create_embed("Error", "Character not found!", COLORS['error'])
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
            return

        item_data = ITEMS.get(self.item_key, {})
        total_cost = item_data.get('price', 100) * self.quantity

        if player_data['gold'] < total_cost:
            embed = create_embed("Insufficient Gold", f"You need {format_number(total_cost - player_data['gold'])} more gold!", COLORS['error'])
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
            return

        # Process purchase
        player_data['gold'] -= total_cost
        if self.item_key in player_data['inventory']:
            player_data['inventory'][self.item_key] += self.quantity
        else:
            player_data['inventory'][self.item_key] = self.quantity

        self.rpg_core.save_player_data(self.user_id, player_data)

        embed = discord.Embed(
            title="✅ Purchase Successful!",
            description=f"**Item:** {item_data.get('name', 'Unknown')}\n"
                       f"**Quantity:** {self.quantity}\n"
                       f"**Total Paid:** {format_number(total_cost)} gold\n"
                       f"**Remaining Gold:** {format_number(player_data['gold'])}",
            color=COLORS['success']
        )
        await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel_purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your purchase!", ephemeral=True)
            return

        embed = create_embed("Purchase Cancelled", "No gold was spent.", COLORS['secondary'])
        await interaction.response.edit_message(embed=embed, view=None)

class RPGShop(commands.Cog):
    """Interactive RPG shop system with full UI."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shop", aliases=["store", "buy"])
    async def shop(self, ctx):
        """Open the interactive shop interface."""
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

        view = ShopCategoryView(str(ctx.author.id), rpg_core)
        embed = discord.Embed(
            title="🛒 Plagg's Cheese & Combat Shop",
            description="**Welcome to the finest shop in all dimensions!**\n\n"
                       "Here you can find everything from powerful weapons to magical cheese wheels.\n"
                       "Choose a category below to browse available items.\n\n"
                       "💰 **Shop Features:**\n"
                       "• Quality guaranteed by Plagg himself\n"
                       "• Instant delivery to your inventory\n"
                       "• Cheese-powered discounts available\n"
                       "• No returns (destroyed items stay destroyed)",
            color=COLORS['primary']
        )
        embed.set_thumbnail(url="https://i.imgur.com/placeholder.png")
        embed.set_footer(text=f"Your Gold: {format_number(player_data['gold'])}")
        
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(RPGShop(bot))
