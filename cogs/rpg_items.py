
import discord
from discord.ext import commands
from rpg_data.game_data import ITEMS, RARITY_COLORS
from utils.helpers import create_embed, format_number
from config import COLORS, is_module_enabled
import logging

logger = logging.getLogger(__name__)

class RPGItems(commands.Cog):
    """RPG item management and equipment system."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="equip")
    async def equip_item(self, ctx, *, item_name: str):
        """Equip weapons, armor, or accessories."""
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
        
        # Find the item
        item_key = None
        item_data = None
        for key, data in ITEMS.items():
            if key == item_name.lower().replace(" ", "_") or data['name'].lower() == item_name.lower():
                item_key = key
                item_data = data
                break
        
        if not item_data:
            await ctx.send(f"❌ Item '{item_name}' not found!")
            return
        
        # Check if player has the item
        if item_key not in player_data.get('inventory', {}) or player_data['inventory'][item_key] <= 0:
            await ctx.send(f"❌ You don't have **{item_data['name']}**!")
            return
        
        # Check if item is equippable
        item_type = item_data['type']
        if item_type not in ['weapon', 'armor', 'accessory', 'artifact']:
            await ctx.send(f"❌ **{item_data['name']}** cannot be equipped!")
            return
        
        # Unequip current item of same type
        current_equipment = player_data.get('equipment', {})
        old_item = current_equipment.get(item_type)
        
        if old_item:
            # Return old item to inventory
            if old_item in player_data['inventory']:
                player_data['inventory'][old_item] += 1
            else:
                player_data['inventory'][old_item] = 1
        
        # Equip new item
        current_equipment[item_type] = item_key
        player_data['equipment'] = current_equipment
        
        # Remove from inventory
        player_data['inventory'][item_key] -= 1
        if player_data['inventory'][item_key] <= 0:
            del player_data['inventory'][item_key]
        
        # Update stats
        self.update_equipment_stats(player_data)
        rpg_core.save_player_data(ctx.author.id, player_data)
        
        rarity_color = RARITY_COLORS.get(item_data['rarity'], COLORS['primary'])
        embed = discord.Embed(
            title="⚔️ Item Equipped!",
            description=f"Successfully equipped **{item_data['name']}**!",
            color=rarity_color
        )
        
        if old_item and old_item in ITEMS:
            embed.add_field(
                name="Previous Item",
                value=f"Unequipped: {ITEMS[old_item]['name']}",
                inline=False
            )
        
        # Show stat changes
        stats_text = ""
        if item_data.get('attack'):
            stats_text += f"⚔️ Attack: +{item_data['attack']}\n"
        if item_data.get('defense'):
            stats_text += f"🛡️ Defense: +{item_data['defense']}\n"
        if item_data.get('hp'):
            stats_text += f"❤️ HP: +{item_data['hp']}\n"
        if item_data.get('mana'):
            stats_text += f"💙 Mana: +{item_data['mana']}\n"
        
        if stats_text:
            embed.add_field(name="📊 Stat Bonuses", value=stats_text, inline=True)
        
        if item_data.get('effects'):
            effects_text = "\n".join(f"✨ {effect}" for effect in item_data['effects'])
            embed.add_field(name="🌟 Special Effects", value=effects_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="unequip")
    async def unequip_item(self, ctx, slot: str):
        """Unequip an item from a specific slot."""
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
        
        valid_slots = ['weapon', 'armor', 'accessory', 'artifact']
        slot = slot.lower()
        
        if slot not in valid_slots:
            await ctx.send(f"❌ Invalid slot! Choose from: {', '.join(valid_slots)}")
            return
        
        current_equipment = player_data.get('equipment', {})
        if slot not in current_equipment or not current_equipment[slot]:
            await ctx.send(f"❌ No item equipped in {slot} slot!")
            return
        
        item_key = current_equipment[slot]
        item_data = ITEMS.get(item_key)
        
        if not item_data:
            await ctx.send("❌ Equipped item data not found!")
            return
        
        # Return item to inventory
        if item_key in player_data.get('inventory', {}):
            player_data['inventory'][item_key] += 1
        else:
            player_data['inventory'][item_key] = 1
        
        # Remove from equipment
        current_equipment[slot] = None
        player_data['equipment'] = current_equipment
        
        # Update stats
        self.update_equipment_stats(player_data)
        rpg_core.save_player_data(ctx.author.id, player_data)
        
        embed = discord.Embed(
            title="📦 Item Unequipped",
            description=f"Unequipped **{item_data['name']}** from {slot} slot.\n\nItem returned to inventory.",
            color=COLORS['secondary']
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="use")
    async def use_item(self, ctx, *, item_name: str):
        """Use a consumable item."""
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
        
        # Find the item
        item_key = None
        item_data = None
        for key, data in ITEMS.items():
            if key == item_name.lower().replace(" ", "_") or data['name'].lower() == item_name.lower():
                item_key = key
                item_data = data
                break
        
        if not item_data:
            await ctx.send(f"❌ Item '{item_name}' not found!")
            return
        
        # Check if player has the item
        if item_key not in player_data.get('inventory', {}) or player_data['inventory'][item_key] <= 0:
            await ctx.send(f"❌ You don't have **{item_data['name']}**!")
            return
        
        # Check if item is consumable
        if item_data['type'] != 'consumable':
            await ctx.send(f"❌ **{item_data['name']}** is not a consumable item!")
            return
        
        # Apply item effects
        effects_applied = []
        
        if item_data.get('heal_amount'):
            heal = item_data['heal_amount']
            current_hp = player_data['resources']['hp']
            max_hp = player_data['resources']['max_hp']
            
            actual_heal = min(heal, max_hp - current_hp)
            player_data['resources']['hp'] += actual_heal
            effects_applied.append(f"❤️ Restored {actual_heal} HP")
        
        if item_data.get('mana_amount'):
            mana = item_data['mana_amount']
            current_mana = player_data['resources']['mana']
            max_mana = player_data['resources']['max_mana']
            
            actual_mana = min(mana, max_mana - current_mana)
            player_data['resources']['mana'] += actual_mana
            effects_applied.append(f"💙 Restored {actual_mana} Mana")
        
        # Remove item from inventory
        player_data['inventory'][item_key] -= 1
        if player_data['inventory'][item_key] <= 0:
            del player_data['inventory'][item_key]
        
        rpg_core.save_player_data(ctx.author.id, player_data)
        
        rarity_color = RARITY_COLORS.get(item_data['rarity'], COLORS['primary'])
        embed = discord.Embed(
            title="✨ Item Used!",
            description=f"You used **{item_data['name']}**!\n\n" + "\n".join(effects_applied),
            color=rarity_color
        )
        
        if item_data.get('effects'):
            embed.add_field(
                name="🌟 Additional Effects",
                value="\n".join(f"• {effect}" for effect in item_data['effects']),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="equipment", aliases=["gear"])
    async def show_equipment(self, ctx):
        """Show currently equipped items."""
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
        
        equipment = player_data.get('equipment', {})
        
        embed = discord.Embed(
            title=f"⚔️ {ctx.author.display_name}'s Equipment",
            color=COLORS['primary']
        )
        
        slots = ['weapon', 'armor', 'accessory', 'artifact']
        
        for slot in slots:
            item_key = equipment.get(slot)
            if item_key and item_key in ITEMS:
                item_data = ITEMS[item_key]
                rarity_emoji = "⚪" if item_data['rarity'] == 'common' else "🟢" if item_data['rarity'] == 'uncommon' else "🔵" if item_data['rarity'] == 'rare' else "🟣"
                
                value = f"{rarity_emoji} **{item_data['name']}**\n"
                
                # Show key stats
                stats = []
                if item_data.get('attack'):
                    stats.append(f"⚔️{item_data['attack']}")
                if item_data.get('defense'):
                    stats.append(f"🛡️{item_data['defense']}")
                if item_data.get('hp'):
                    stats.append(f"❤️{item_data['hp']}")
                if item_data.get('mana'):
                    stats.append(f"💙{item_data['mana']}")
                
                if stats:
                    value += f"*{' | '.join(stats)}*"
                
                embed.add_field(name=f"{slot.title()}", value=value, inline=True)
            else:
                embed.add_field(name=f"{slot.title()}", value="*None equipped*", inline=True)
        
        # Show total stat bonuses
        total_stats = self.calculate_equipment_bonuses(player_data)
        if any(total_stats.values()):
            bonus_text = ""
            if total_stats.get('attack', 0) > 0:
                bonus_text += f"⚔️ Attack: +{total_stats['attack']}\n"
            if total_stats.get('defense', 0) > 0:
                bonus_text += f"🛡️ Defense: +{total_stats['defense']}\n"
            if total_stats.get('hp', 0) > 0:
                bonus_text += f"❤️ HP: +{total_stats['hp']}\n"
            if total_stats.get('mana', 0) > 0:
                bonus_text += f"💙 Mana: +{total_stats['mana']}\n"
            
            embed.add_field(name="📊 Total Equipment Bonuses", value=bonus_text, inline=False)
        
        await ctx.send(embed=embed)
    
    def calculate_equipment_bonuses(self, player_data):
        """Calculate total bonuses from equipped items."""
        bonuses = {'attack': 0, 'defense': 0, 'hp': 0, 'mana': 0}
        equipment = player_data.get('equipment', {})
        
        for slot, item_key in equipment.items():
            if item_key and item_key in ITEMS:
                item_data = ITEMS[item_key]
                bonuses['attack'] += item_data.get('attack', 0)
                bonuses['defense'] += item_data.get('defense', 0)
                bonuses['hp'] += item_data.get('hp', 0)
                bonuses['mana'] += item_data.get('mana', 0)
        
        return bonuses
    
    def update_equipment_stats(self, player_data):
        """Update player's derived stats based on equipment."""
        # Recalculate base derived stats
        base_stats = player_data['stats']
        player_data['derived_stats']['attack'] = 10 + (base_stats['strength'] * 2)
        player_data['derived_stats']['magic_attack'] = 10 + (base_stats['intelligence'] * 2)
        player_data['derived_stats']['defense'] = 5 + base_stats['constitution']
        
        # Add equipment bonuses
        equipment_bonuses = self.calculate_equipment_bonuses(player_data)
        player_data['derived_stats']['attack'] += equipment_bonuses['attack']
        player_data['derived_stats']['defense'] += equipment_bonuses['defense']
        
        # Update max HP and mana
        base_hp = 100 + (base_stats['constitution'] * 10)
        base_mana = 50 + (base_stats['intelligence'] * 5)
        
        new_max_hp = base_hp + equipment_bonuses['hp']
        new_max_mana = base_mana + equipment_bonuses['mana']
        
        # Adjust current HP/mana if max increased
        hp_diff = new_max_hp - player_data['resources']['max_hp']
        mana_diff = new_max_mana - player_data['resources']['max_mana']
        
        player_data['resources']['max_hp'] = new_max_hp
        player_data['resources']['max_mana'] = new_max_mana
        
        if hp_diff > 0:
            player_data['resources']['hp'] += hp_diff
        if mana_diff > 0:
            player_data['resources']['mana'] += mana_diff

async def setup(bot):
    await bot.add_cog(RPGItems(bot))
