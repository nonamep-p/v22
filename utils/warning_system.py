
"""
Warning System for Player Guidance
Provides warnings for potentially suboptimal choices without blocking them.
"""

import discord
from typing import Dict, List, Optional, Tuple
from rpg_data.game_data import CHARACTER_CLASSES, ITEMS
from utils.helpers import create_embed
from config import COLORS

class WarningSystem:
    """Comprehensive warning system for player guidance."""
    
    def __init__(self):
        self.warning_types = {
            "stat_allocation": "Stat point allocation suggestions",
            "equipment": "Equipment choice warnings",
            "combat": "Combat strategy alerts",
            "progression": "Character progression guidance",
            "economy": "Economic decision warnings",
            "pvp": "PvP preparation alerts"
        }
    
    def check_stat_allocation_warning(self, player_data: Dict, stat: str, points: int) -> Optional[Dict]:
        """Check for stat allocation warnings."""
        player_class = player_data.get('class', 'warrior')
        class_data = CHARACTER_CLASSES.get(player_class, {})
        current_stats = player_data.get('stats', {})
        
        warnings = []
        
        # Class-specific stat recommendations
        recommended_stats = self._get_recommended_stats(player_class)
        non_recommended = self._get_non_recommended_stats(player_class)
        
        if stat in non_recommended:
            warnings.append({
                "level": "caution",
                "title": f"Not Optimal for {class_data.get('name', 'Your Class')}",
                "message": f"**{stat.title()}** is not a primary stat for {class_data.get('name', 'your class')}. "
                          f"Consider investing in **{', '.join(recommended_stats)}** instead for better combat effectiveness.",
                "impact": "Your character may not perform optimally in their intended role."
            })
        
        # Check for stat imbalance
        total_allocated = sum(current_stats.values()) + points
        highest_stat = max(current_stats.values()) if current_stats else 0
        
        if current_stats.get(stat, 0) + points > highest_stat + 10:
            warnings.append({
                "level": "info",
                "title": "High Stat Concentration",
                "message": f"You're investing heavily in **{stat.title()}**. While specialization can be powerful, "
                          "consider some balance for survivability and versatility.",
                "impact": "Extreme specialization may make you vulnerable in certain situations."
            })
        
        # Low-level Constitution warning
        if (player_data.get('level', 1) > 10 and 
            current_stats.get('constitution', 0) < 5 and 
            stat != 'constitution'):
            warnings.append({
                "level": "warning",
                "title": "Low Constitution Detected",
                "message": "Your Constitution is quite low for your level. Consider investing some points in "
                          "Constitution to improve your survivability in combat.",
                "impact": "Low HP may cause frequent defeats in higher-level content."
            })
        
        return self._format_warning_response(warnings) if warnings else None
    
    def check_equipment_warning(self, player_data: Dict, item_key: str, action: str) -> Optional[Dict]:
        """Check for equipment-related warnings."""
        if item_key not in ITEMS:
            return None
            
        item_data = ITEMS[item_key]
        player_class = player_data.get('class', 'warrior')
        player_level = player_data.get('level', 1)
        current_equipment = player_data.get('equipment', {})
        
        warnings = []
        
        # Level requirement warnings
        required_level = item_data.get('level_requirement', 1)
        if player_level < required_level:
            warnings.append({
                "level": "error",
                "title": "Level Requirement Not Met",
                "message": f"**{item_data['name']}** requires Level **{required_level}**. "
                          f"You are currently Level **{player_level}**.",
                "impact": "You cannot equip this item until you reach the required level."
            })
        
        # Class compatibility warnings
        if action == "equip":
            class_data = CHARACTER_CLASSES.get(player_class, {})
            preferred_weapons = class_data.get('preferred_weapons', [])
            
            if (item_data.get('type') == 'weapon' and 
                preferred_weapons and 
                item_key not in preferred_weapons):
                warnings.append({
                    "level": "caution",
                    "title": "Non-Optimal Weapon Type",
                    "message": f"**{item_data['name']}** is not an optimal weapon for your **{class_data.get('name', 'class')}**. "
                              f"Consider weapons like: {', '.join(preferred_weapons)}",
                    "impact": "May not synergize well with your class abilities and bonuses."
                })
        
        # Expensive purchase warnings
        if action == "buy":
            player_gold = player_data.get('gold', 0)
            item_price = item_data.get('price', 0)
            
            if item_price > player_gold * 0.8:  # More than 80% of gold
                warnings.append({
                    "level": "warning",
                    "title": "Expensive Purchase",
                    "message": f"**{item_data['name']}** costs **{item_price}** gold, which is most of your current wealth. "
                              "Make sure you really need this item!",
                    "impact": "You'll have little gold left for other purchases or upgrades."
                })
        
        # Selling valuable items
        if action == "sell":
            if item_data.get('rarity') in ['legendary', 'mythic', 'divine']:
                warnings.append({
                    "level": "warning",
                    "title": "Selling Rare Item",
                    "message": f"**{item_data['name']}** is a **{item_data['rarity']}** item! "
                              "These are very rare and difficult to obtain again.",
                    "impact": "You may regret selling this item later in your progression."
                })
        
        return self._format_warning_response(warnings) if warnings else None
    
    def check_combat_warning(self, player_data: Dict, action: str, context: Dict = None) -> Optional[Dict]:
        """Check for combat-related warnings."""
        warnings = []
        
        # Low health combat warning
        current_hp = player_data['resources'].get('hp', 0)
        max_hp = player_data['resources'].get('max_hp', 100)
        
        if action == "battle" and current_hp < max_hp * 0.3:  # Less than 30% HP
            warnings.append({
                "level": "warning",
                "title": "Low Health",
                "message": f"You have **{current_hp}/{max_hp}** HP. Consider healing before battle!",
                "impact": "You may be defeated quickly in combat."
            })
        
        # No equipment warnings
        equipment = player_data.get('equipment', {})
        if action == "battle" and not any(equipment.values()):
            warnings.append({
                "level": "caution",
                "title": "No Equipment",
                "message": "You're not wearing any equipment! Visit the shop or check your inventory for gear.",
                "impact": "Combat will be much more difficult without proper equipment."
            })
        
        # Skill Point management
        if context and action == "use_skill":
            current_sp = context.get('current_sp', 0)
            if current_sp <= 1:
                warnings.append({
                    "level": "info",
                    "title": "Low Skill Points",
                    "message": "Using this skill will leave you with few Skill Points. "
                              "Consider if you need to save SP for emergency situations.",
                    "impact": "You may not be able to use skills when you need them most."
                })
        
        return self._format_warning_response(warnings) if warnings else None
    
    def check_progression_warning(self, player_data: Dict, action: str, target: str = None) -> Optional[Dict]:
        """Check for character progression warnings."""
        warnings = []
        
        # Unallocated stat points
        if action == "level_check":
            unallocated = player_data.get('unallocated_points', 0)
            if unallocated > 5:
                warnings.append({
                    "level": "info",
                    "title": "Unallocated Stat Points",
                    "message": f"You have **{unallocated}** unallocated stat points. "
                              "Use `$allocate <stat> <points>` to improve your character!",
                    "impact": "Your character is weaker than they could be."
                })
        
        # Path choice timing
        if action == "path_choice":
            player_level = player_data.get('level', 1)
            if player_level < 20:
                warnings.append({
                    "level": "error",
                    "title": "Path Choice Unavailable",
                    "message": f"Miraculous Paths unlock at Level 20. You are Level **{player_level}**.",
                    "impact": "Continue leveling to unlock this powerful progression option."
                })
        
        # PvP readiness
        if action == "pvp_entry":
            player_level = player_data.get('level', 1)
            if player_level < 10:
                warnings.append({
                    "level": "warning",
                    "title": "Low Level for PvP",
                    "message": f"PvP unlocks at Level 10. You are Level **{player_level}**.",
                    "impact": "Focus on PvE content and leveling first."
                })
            elif player_level < 15:
                warnings.append({
                    "level": "caution",
                    "title": "Early PvP Entry",
                    "message": "You can enter PvP, but higher-level players will have significant advantages. "
                              "Consider more preparation.",
                    "impact": "You may face much stronger opponents."
                })
        
        return self._format_warning_response(warnings) if warnings else None
    
    def _get_recommended_stats(self, player_class: str) -> List[str]:
        """Get recommended stats for a class."""
        recommendations = {
            "warrior": ["strength", "constitution", "dexterity"],
            "mage": ["intelligence", "wisdom", "constitution"],
            "rogue": ["dexterity", "strength", "intelligence"],
            "archer": ["dexterity", "wisdom", "constitution"],
            "healer": ["wisdom", "intelligence", "charisma"],
            "battlemage": ["intelligence", "strength", "constitution"],
            "chrono_knight": ["intelligence", "dexterity", "wisdom"]
        }
        return recommendations.get(player_class, ["strength", "constitution"])
    
    def _get_non_recommended_stats(self, player_class: str) -> List[str]:
        """Get non-recommended stats for a class."""
        non_recommended = {
            "warrior": ["intelligence", "wisdom", "charisma"],
            "mage": ["strength", "dexterity"],
            "rogue": ["wisdom", "charisma", "constitution"],
            "archer": ["strength", "intelligence", "charisma"],
            "healer": ["strength", "dexterity"],
            "battlemage": ["charisma"],
            "chrono_knight": ["strength", "charisma"]
        }
        return non_recommended.get(player_class, [])
    
    def _format_warning_response(self, warnings: List[Dict]) -> Dict:
        """Format warnings into a response dictionary."""
        if not warnings:
            return None
        
        # Determine overall severity
        severity_levels = {"error": 3, "warning": 2, "caution": 1, "info": 0}
        max_severity = max(severity_levels.get(w["level"], 0) for w in warnings)
        
        severity_names = {3: "error", 2: "warning", 1: "caution", 0: "info"}
        overall_severity = severity_names[max_severity]
        
        # Create formatted response
        return {
            "severity": overall_severity,
            "warnings": warnings,
            "embed": self._create_warning_embed(warnings, overall_severity)
        }
    
    def _create_warning_embed(self, warnings: List[Dict], severity: str) -> discord.Embed:
        """Create a warning embed."""
        colors = {
            "error": COLORS['error'],
            "warning": COLORS['warning'], 
            "caution": COLORS['secondary'],
            "info": COLORS['primary']
        }
        
        emojis = {
            "error": "🚫",
            "warning": "⚠️",
            "caution": "💡",
            "info": "ℹ️"
        }
        
        embed = discord.Embed(
            title=f"{emojis[severity]} Player Guidance",
            description="The game has detected some things you might want to consider:",
            color=colors[severity]
        )
        
        for i, warning in enumerate(warnings, 1):
            level_emoji = emojis.get(warning["level"], "ℹ️")
            embed.add_field(
                name=f"{level_emoji} {warning['title']}",
                value=f"{warning['message']}\n\n**Impact:** {warning['impact']}",
                inline=False
            )
        
        embed.set_footer(text="These are suggestions - you can still proceed with your choice!")
        return embed

# Global warning system instance
warning_system = WarningSystem()
