import discord
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import time

from config import COLORS, EMOJIS

logger = logging.getLogger(__name__)

def create_embed(title: str, description: str, color: int = COLORS['primary']) -> discord.Embed:
    """Create a standardized embed."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now()
    )
    return embed

def format_number(number):
    """Format large numbers with commas."""
    return "{:,}".format(number)

def calculate_level_xp(level: int) -> int:
    """Calculate XP needed for a specific level."""
    if level <= 1:
        return 100
    return int(100 * (1.5 ** (level - 1)))

def create_progress_bar(percentage: float, length: int = 10) -> str:
    """Create a visual progress bar."""
    filled = int(percentage / 100 * length)
    empty = length - filled
    return f"{'█' * filled}{'░' * empty} {percentage:.1f}%"

def get_random_work_job() -> Dict[str, Any]:
    """Get a random work job with Plagg theme."""
    jobs = [
        {"name": "Cheese Mining", "min_coins": 50, "max_coins": 100, "min_xp": 5, "max_xp": 15},
        {"name": "Kwami Farming", "min_coins": 30, "max_coins": 80, "min_xp": 3, "max_xp": 10},
        {"name": "Miraculous Trading", "min_coins": 70, "max_coins": 120, "min_xp": 8, "max_xp": 20},
        {"name": "Cheese Crafting", "min_coins": 60, "max_coins": 110, "min_xp": 6, "max_xp": 18},
        {"name": "Kwami Watching", "min_coins": 40, "max_coins": 90, "min_xp": 4, "max_xp": 12},
        {"name": "Camembert Aging", "min_coins": 80, "max_coins": 130, "min_xp": 10, "max_xp": 25}
    ]
    return random.choice(jobs)

def get_random_adventure_outcome() -> Dict[str, Any]:
    """Get a random adventure outcome."""
    outcomes = [
        {
            "description": "You discovered a hidden treasure chest!",
            "coins": (100, 300),
            "xp": (50, 100),
            "items": ["Health Potion", "Mana Potion", "Ancient Coin"]
        },
        {
            "description": "You helped a lost traveler and received a reward!",
            "coins": (80, 200),
            "xp": (30, 70),
            "items": ["Traveler's Map", "Lucky Charm", "Bread"]
        },
        {
            "description": "You found rare materials while exploring!",
            "coins": (60, 150),
            "xp": (40, 80),
            "items": ["Iron Ore", "Mystic Crystal", "Healing Herbs"]
        },
        {
            "description": "You completed a mysterious quest!",
            "coins": (120, 250),
            "xp": (60, 120),
            "items": ["Quest Scroll", "Magic Ring", "Gold Coin"]
        }
    ]

    return random.choice(outcomes)

def level_up_player(player_data: Dict[str, Any]) -> Optional[str]:
    """Check if player levels up and apply bonuses."""
    current_level = player_data.get('level', 1)
    current_xp = player_data.get('xp', 0)
    max_xp = player_data.get('max_xp', 100)

    if current_xp >= max_xp:
        # Level up!
        new_level = current_level + 1

        # Calculate new max XP (exponential growth)
        new_max_xp = int(max_xp * 1.5)

        # Apply stat bonuses
        hp_bonus = random.randint(15, 25)
        attack_bonus = random.randint(3, 7)
        defense_bonus = random.randint(2, 5)
        coin_bonus = new_level * 50

        player_data['level'] = new_level
        player_data['xp'] = current_xp - max_xp  # Carry over excess XP
        player_data['max_xp'] = new_max_xp
        player_data['max_hp'] = player_data.get('max_hp', 100) + hp_bonus
        player_data['hp'] = player_data['max_hp']  # Full heal on level up
        player_data['attack'] = player_data.get('attack', 10) + attack_bonus
        player_data['defense'] = player_data.get('defense', 5) + defense_bonus
        player_data['coins'] = player_data.get('coins', 0) + coin_bonus

        return (f"Level {new_level}! "
                f"HP +{hp_bonus}, ATK +{attack_bonus}, DEF +{defense_bonus}, "
                f"Coins +{coin_bonus}")

    return None

def calculate_battle_damage(attacker_stats: Dict[str, Any], defender_stats: Dict[str, Any]) -> int:
    """Calculate damage in battle."""
    attack = attacker_stats.get('attack', 10)
    defense = defender_stats.get('defense', 5)

    # Base damage calculation
    base_damage = max(1, attack - defense)

    # Add some randomness (80% - 120% of base damage)
    damage_multiplier = random.uniform(0.8, 1.2)
    final_damage = int(base_damage * damage_multiplier)

    return max(1, final_damage)

def generate_random_stats() -> Dict[str, int]:
    """Generate random stats for monsters/items."""
    return {
        'hp': random.randint(50, 150),
        'attack': random.randint(8, 20),
        'defense': random.randint(3, 12)
    }

def format_time_remaining(seconds):
    """Format time remaining in a readable format."""
    if seconds <= 0:
        return "Ready!"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def check_weapon_unlock_conditions(player_data, weapon_name):
    """Check if player meets unlock conditions for a weapon."""
    from utils.constants import WEAPON_UNLOCK_CONDITIONS

    if weapon_name not in WEAPON_UNLOCK_CONDITIONS:
        return True, "No special conditions"

    conditions = WEAPON_UNLOCK_CONDITIONS[weapon_name]["requirements"]
    failed_conditions = []

    for condition in conditions:
        if condition["type"] == "boss_defeat":
            # Check if player has defeated the required boss
            boss_defeats = player_data.get("boss_defeats", {})
            boss_name = condition["boss"]

            if boss_name not in boss_defeats:
                failed_conditions.append(f"Must defeat {boss_name.replace('_', ' ').title()}")
            elif condition.get("player_level_max"):
                # Check if they were low enough level when they defeated it
                defeat_data = boss_defeats[boss_name]
                if defeat_data.get("player_level", 999) > condition["player_level_max"]:
                    failed_conditions.append(f"Must defeat {boss_name.replace('_', ' ').title()} at level {condition['player_level_max']} or lower")

        elif condition["type"] == "class_unlock":
            required_class = condition["class"]
            if player_data.get("player_class") != required_class:
                failed_conditions.append(f"Must be {required_class.replace('_', ' ').title()} class")

        elif condition["type"] == "health_condition":
            # This would be checked during combat, not here
            failed_conditions.append(f"Must complete challenge at {condition['max_hp_percent']}% HP or lower")

        elif condition["type"] == "dungeon_clear":
            dungeon_clears = player_data.get("dungeon_clears", {})
            dungeon_name = condition["dungeon"]
            required_floors = condition.get("floors", 1)

            if dungeon_name not in dungeon_clears or dungeon_clears[dungeon_name] < required_floors:
                failed_conditions.append(f"Must clear {dungeon_name.replace('_', ' ').title()} ({required_floors} floors)")

        elif condition["type"] == "item_required":
            inventory = player_data.get("inventory", [])
            required_item = condition["item"]

            if required_item not in inventory:
                failed_conditions.append(f"Must possess {required_item.replace('_', ' ').title()}")

    return len(failed_conditions) == 0, failed_conditions

def award_weapon_unlock(player_data, weapon_name):
    """Award a special weapon to the player."""
    from utils.constants import WEAPON_UNLOCK_CONDITIONS

    # Add to inventory
    inventory = player_data.get("inventory", [])
    if weapon_name not in inventory:
        inventory.append(weapon_name)
        player_data["inventory"] = inventory

    # Record the unlock
    unlocked_weapons = player_data.get("unlocked_weapons", [])
    if weapon_name not in unlocked_weapons:
        unlocked_weapons.append(weapon_name)
        player_data["unlocked_weapons"] = unlocked_weapons

    # Get unlock message
    unlock_info = WEAPON_UNLOCK_CONDITIONS.get(weapon_name, {})
    unlock_message = unlock_info.get("unlock_message", f"You have unlocked {weapon_name}!")

    return unlock_message

def level_up_profession(player_data, profession, xp_gained):
    """Handle profession leveling with XP gain."""
    if not profession:
        return None

    current_level = player_data.get('profession_level', 1)
    current_xp = player_data.get('profession_xp', 0)

    new_xp = current_xp + xp_gained
    player_data['profession_xp'] = new_xp

    # Calculate XP needed for next level (profession levels are harder)
    xp_needed = 200 * (current_level ** 1.2)

    if new_xp >= xp_needed:
        new_level = current_level + 1
        remaining_xp = new_xp - xp_needed

        player_data['profession_level'] = new_level
        player_data['profession_xp'] = remaining_xp

        return f"🔨 Profession Level Up! {profession.title()} is now level {new_level}!"

    return None

def calculate_craft_success_rate(player_data, recipe):
    """Calculate crafting success rate based on player skill."""
    base_rate = recipe.get('success_rate', 0.5)
    profession_level = player_data.get('profession_level', 1)

    # Higher level = better success rate
    level_bonus = min(0.3, profession_level * 0.02)  # Max 30% bonus

    # Luck bonus
    luck_points = player_data.get('luck_points', 0)
    luck_bonus = min(0.1, luck_points / 1000)  # Max 10% from luck

    final_rate = min(0.95, base_rate + level_bonus + luck_bonus)  # Cap at 95%
    return final_rate

def calculate_prestige_cost(level):
    """Calculate cost for prestiging based on level."""
    base_cost = 10000
    level_multiplier = level * 100
    return base_cost + level_multiplier

def format_faction_info(faction_name):
    """Format faction information for display."""
    from utils.constants import FACTIONS

    if faction_name not in FACTIONS:
        return "Unknown faction"

    faction = FACTIONS[faction_name]
    info = f"**{faction['name']}**\n"
    info += f"{faction['description']}\n\n"
    info += f"**Alignment:** {faction['alignment'].title()}\n"
    info += f"**Perks:** {', '.join(faction['perks'])}\n"

    if faction['enemies']:
        info += f"**Enemies:** {', '.join([FACTIONS[e]['name'] for e in faction['enemies']])}"

    return info

def generate_dynamic_quest(user_id, quest_type):
    """Generate a dynamic quest based on type."""
    from utils.constants import QUEST_TYPES
    import random

    if quest_type not in QUEST_TYPES:
        return None

    quest_template = QUEST_TYPES[quest_type]

    # Generate basic quest structure
    quest = {
        'id': f"quest_{user_id}_{int(time.time())}",
        'type': quest_type,
        'title': f"Dynamic {quest_template['name']}",
        'description': quest_template['description'],
        'location': random.choice(['paris_streets', 'cheese_dimension', 'kwami_realm']),
        'progress': 0,
        'target': random.randint(5, 15),
        'rewards': quest_template['rewards'],
        'created_at': time.time()
    }

    return quest

def format_quest_progress(quest):
    """Format quest progress for display."""
    progress = quest.get('progress', 0)
    target = quest.get('target', 1)
    percentage = (progress / target) * 100 if target > 0 else 0

    progress_bar = create_progress_bar(percentage)
    return f"Progress: {progress}/{target}\n{progress_bar}"

def get_time_until_next_use(last_use: Optional[datetime], cooldown_seconds: int) -> int:
    """Get seconds until next use of a cooldown-based command."""
    if not last_use:
        return 0

    next_use = last_use + timedelta(seconds=cooldown_seconds)
    now = datetime.now()

    if now >= next_use:
        return 0

    return int((next_use - now).total_seconds())

def get_rarity_color(rarity: str) -> int:
    """Get color for item rarity."""
    rarity_colors = {
        'common': 0x95A5A6,      # Gray
        'uncommon': 0x2ECC71,    # Green
        'rare': 0x3498DB,        # Blue
        'epic': 0x9B59B6,        # Purple
        'legendary': 0xF39C12,   # Orange
        'mythical': 0xE74C3C     # Red
    }
    return rarity_colors.get(rarity.lower(), 0x95A5A6)

def get_rarity_emoji(rarity: str) -> str:
    """Get emoji for item rarity."""
    rarity_emojis = {
        'common': '⚪',
        'uncommon': '🟢',
        'rare': '🔵',
        'epic': '🟣',
        'legendary': '🟠',
        'mythical': '🔴'
    }
    return rarity_emojis.get(rarity.lower(), '⚪')

def deduplicate_items(items_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate items based on ID or name."""
    seen_ids = set()
    seen_names = set()
    unique_items = []

    for item in items_list:
        item_id = item.get('id')
        item_name = item.get('name')

        # Use ID if available, otherwise use name
        identifier = item_id if item_id else item_name

        if item_id and item_id not in seen_ids:
            seen_ids.add(item_id)
            unique_items.append(item)
        elif not item_id and item_name and item_name not in seen_names:
            seen_names.add(item_name)
            unique_items.append(item)

    return unique_items

def format_shop_item(item_data: Dict[str, Any]) -> str:
    """Format a single shop item for display."""
    rarity = item_data.get('rarity', 'common')
    emoji = get_rarity_emoji(rarity)
    name = item_data.get('name', 'Unknown Item')
    price = item_data.get('price', 0)

    # Add attack/defense info if it's a weapon/armor
    stats = []
    if item_data.get('attack'):
        stats.append(f"⚔️{item_data['attack']}")
    if item_data.get('defense'):
        stats.append(f"🛡️{item_data['defense']}")

    stats_str = f" ({'/'.join(stats)})" if stats else ""

    return f"{emoji} **{name}**{stats_str} - {format_number(price)} coins"

def clear_item_cache():
    """Clear any cached item data to prevent duplicates."""
    logger.info("Item cache cleared")
    return True

def validate_shop_data() -> Dict[str, Any]:
    """Validate shop data for duplicates and errors."""
    from utils.constants import SHOP_ITEMS

    validation_results = {
        "total_items": len(SHOP_ITEMS),
        "duplicates_found": [],
        "missing_data": [],
        "valid": True
    }

    seen_names = set()

    # Check for required fields and name duplicates
    for item_id, item_data in SHOP_ITEMS.items():
        # Check required fields
        if not item_data.get('name'):
            validation_results["missing_data"].append(f"Item {item_id} missing name")
            validation_results["valid"] = False
        if not item_data.get('price'):
            validation_results["missing_data"].append(f"Item {item_id} missing price")
            validation_results["valid"] = False
        if not item_data.get('category'):
            validation_results["missing_data"].append(f"Item {item_id} missing category")
            validation_results["valid"] = False

        # Check for duplicate names
        name = item_data.get('name')
        if name:
            if name in seen_names:
                validation_results["duplicates_found"].append(f"Duplicate name: {name}")
                validation_results["valid"] = False
            seen_names.add(name)

    return validation_results

def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to fit within Discord limits."""
    if len(text) <= max_length:
        return text

    return text[:max_length-3] + "..."

def get_user_display_name(user: discord.User) -> str:
    """Get the best display name for a user."""
    return getattr(user, 'display_name', user.name)

def create_success_embed(title: str, description: str) -> discord.Embed:
    """Create a success embed."""
    return create_embed(title, description, COLORS['success'])

def create_error_embed(title: str, description: str) -> discord.Embed:
    """Create an error embed."""
    return create_embed(title, description, COLORS['error'])

def create_warning_embed(title: str, description: str) -> discord.Embed:
    """Create a warning embed."""
    return create_embed(title, description, COLORS['warning'])

def create_info_embed(title: str, description: str) -> discord.Embed:
    """Create an info embed."""
    return create_embed(title, description, COLORS['info'])

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 0: 
        seconds = 0
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds > 0:
            return f"{minutes} minutes, {remaining_seconds} seconds"
        return f"{minutes} minutes"
    elif seconds < 86400:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        if remaining_minutes > 0:
            return f"{hours} hours, {remaining_minutes} minutes"
        return f"{hours} hours"
    else:
        days = seconds // 86400
        remaining_hours = (seconds % 86400) // 3600
        if remaining_hours > 0:
            return f"{days} days, {remaining_hours} hours"
        return f"{days} days"

def check_weapon_unlock_conditions(user_id: str, weapon_name: str) -> tuple[bool, str]:
    """Check if user meets weapon unlock conditions."""
    from utils.constants import WEAPON_UNLOCK_CONDITIONS
    from utils.database import get_user_rpg_data

    if weapon_name not in WEAPON_UNLOCK_CONDITIONS:
        return True, "No special conditions required"

    player_data = get_user_rpg_data(user_id)
    if not player_data:
        return False, "Player data not found"

    conditions = WEAPON_UNLOCK_CONDITIONS[weapon_name]["requirements"]
    failed_conditions = []

    for condition in conditions:
        if condition["type"] == "boss_defeat":
            boss_defeats = player_data.get("boss_defeats", {})
            if condition["boss"] not in boss_defeats:
                failed_conditions.append(f"Must defeat {condition['boss']}")
            elif condition.get("min_level") and player_data.get("level", 1) < condition["min_level"]:
                failed_conditions.append(f"Must be level {condition['min_level']} or higher")

        elif condition["type"] == "class_unlock":
            if player_data.get("player_class") != condition["class"]:
                failed_conditions.append(f"Must be {condition['class']} class")

        elif condition["type"] == "item_required":
            inventory = player_data.get("inventory", [])
            if condition["item"] not in inventory:
                failed_conditions.append(f"Must have {condition['item']}")

    if failed_conditions:
        return False, "; ".join(failed_conditions)

    return True, "All conditions met"

def check_chrono_weave_unlock(user_id: str) -> tuple[bool, str]:
    """Check if user can unlock Chrono Weave class."""
    from utils.database import get_user_rpg_data

    player_data = get_user_rpg_data(user_id)
    if not player_data:
        return False, "Player data not found"

    # Check boss defeat condition
    boss_defeats = player_data.get("boss_defeats", {})
    if "time_rift_dragon" not in boss_defeats:
        return False, "Must defeat Time Rift Dragon while level 30 or lower"

    # Check quest completion
    completed_quests = player_data.get("completed_quests", [])
    if "chrono_whispers" not in [q.get("name", "") for q in completed_quests]:
        return False, "Must complete Chrono Whispers quest"

    # Check ancient relics
    inventory = player_data.get("inventory", [])
    required_relics = ["relic_of_past", "relic_of_future", "relic_of_present"]
    missing_relics = [relic for relic in required_relics if relic not in inventory]

    if missing_relics:
        return False, f"Missing relics: {', '.join(missing_relics)}"

    return True, "All Chrono Weave requirements met"

def calculate_weapon_stats(weapon_name: str, player_data: dict) -> dict:
    """Calculate effective weapon stats based on player data."""
    from utils.constants import WEAPONS

    if weapon_name not in WEAPONS:
        return {"attack": 0, "defense": 0}

    weapon = WEAPONS[weapon_name]
    stats = {
        "attack": weapon.get("attack", 0),
        "defense": weapon.get("defense", 0)
    }

    # Apply class bonuses
    player_class = player_data.get("player_class")
    weapon_class = weapon.get("class_req")

    if weapon_class == "any" or player_class == weapon_class:
        # Apply special effects
        if weapon.get("special") == "randomized_boost" and weapon.get("random_stat_chance", 0) > 0:
            import random
            if random.random() < (weapon["random_stat_chance"] / 100):
                boost_stat = random.choice(["attack", "defense", "crit_chance"])
                boost_amount = weapon.get("random_stat_boost", 0)
                if boost_stat in stats:
                    stats[boost_stat] += boost_amount
                else:
                    stats[boost_stat] = boost_amount

    return stats

def format_weapon_info(weapon_name: str) -> str:
    """Format weapon information for display."""
    from utils.constants import WEAPONS, RARITY_COLORS

    if weapon_name not in WEAPONS:
        return f"Unknown weapon: {weapon_name}"

    weapon = WEAPONS[weapon_name]
    rarity = weapon.get("rarity", "common")

    info = f"**{weapon_name}** ({rarity.title()})\n"
    info += f"⚔️ Attack: {weapon.get('attack', 0)}\n"
    info += f"🛡️ Defense: {weapon.get('defense', 0)}\n"

    if weapon.get("class_req") != "any":
        info += f"🎭 Class: {weapon['class_req'].title()}\n"

    if weapon.get("special"):
        info += f"✨ Special: {weapon['special'].replace('_', ' ').title()}\n"

    return info

def get_all_shop_items():
    """Get all shop items."""
    from utils.constants import SHOP_ITEMS
    return SHOP_ITEMS

def apply_item_effect(user_id: str, item_name: str, player_data: dict):
    """Apply item effect (placeholder)."""
    # Remove item from inventory
    if item_name in player_data.get('inventory', {}):
        player_data['inventory'][item_name] -= 1
        if player_data['inventory'][item_name] <= 0:
            del player_data['inventory'][item_name]
        return True, f"Used {item_name}"
    return False, "Item not found"

def calculate_effective_stats(player_data: dict):
    """Calculate effective stats with equipment (placeholder)."""
    base_stats = player_data.get('stats', {})
    return {
        'strength': base_stats.get('strength', 10),
        'dexterity': base_stats.get('dexterity', 10),
        'constitution': base_stats.get('constitution', 10),
        'intelligence': base_stats.get('intelligence', 10),
        'wisdom': base_stats.get('wisdom', 10),
        'charisma': base_stats.get('charisma', 10),
        'attack': base_stats.get('strength', 10) * 2,
        'defense': base_stats.get('constitution', 10),
        'max_hp': player_data.get('max_hp', 100),
        'max_mana': player_data.get('max_mana', 50)
    }