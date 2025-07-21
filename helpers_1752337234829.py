import discord
import random
import math
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def create_embed(title: str, description: str, color: int, **kwargs) -> discord.Embed:
    """Create a Discord embed with consistent styling."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    
    # Add optional fields
    if 'thumbnail' in kwargs:
        embed.set_thumbnail(url=kwargs['thumbnail'])
    if 'image' in kwargs:
        embed.set_image(url=kwargs['image'])
    if 'footer' in kwargs:
        embed.set_footer(text=kwargs['footer'])
    if 'author' in kwargs:
        embed.set_author(name=kwargs['author'])
    if 'timestamp' in kwargs:
        embed.timestamp = kwargs['timestamp']
    
    return embed

def format_number(number: int) -> str:
    """Format large numbers with commas."""
    return f"{number:,}"

def create_progress_bar(percentage: float, length: int = 10) -> str:
    """Create a text progress bar."""
    filled = int(percentage / 100 * length)
    empty = length - filled
    return f"{'█' * filled}{'░' * empty} {percentage:.1f}%"

def calculate_level_xp(level: int) -> int:
    """Calculate XP required for a level."""
    return int(100 * (level ** 1.5))

def level_up_player(player_data: Dict[str, Any]) -> Optional[str]:
    """Check if player levels up and apply level up bonuses."""
    try:
        current_level = player_data.get('level', 1)
        current_xp = player_data.get('xp', 0)
        max_xp = player_data.get('max_xp', 100)
        
        level_up_msg = None
        
        # Check for level up
        while current_xp >= max_xp:
            current_xp -= max_xp
            current_level += 1
            
            # Calculate new max XP
            max_xp = calculate_level_xp(current_level)
            
            # Apply level up bonuses
            hp_bonus = random.randint(5, 15)
            attack_bonus = random.randint(2, 8)
            defense_bonus = random.randint(1, 5)
            
            player_data['level'] = current_level
            player_data['xp'] = current_xp
            player_data['max_xp'] = max_xp
            player_data['max_hp'] += hp_bonus
            player_data['hp'] = player_data['max_hp']  # Full heal on level up
            player_data['attack'] += attack_bonus
            player_data['defense'] += defense_bonus
            
            level_up_msg = (
                f"Level {current_level}! "
                f"HP +{hp_bonus}, ATK +{attack_bonus}, DEF +{defense_bonus}"
            )
            
            logger.info(f"Player leveled up to {current_level}")
        
        # Update player data
        player_data['level'] = current_level
        player_data['xp'] = current_xp
        player_data['max_xp'] = max_xp
        
        return level_up_msg
    except Exception as e:
        logger.error(f"Error in level_up_player: {e}")
        return None

def get_random_work_job() -> Dict[str, Any]:
    """Get a random work job."""
    jobs = [
        {"name": "Blacksmith", "min_coins": 20, "max_coins": 50, "min_xp": 5, "max_xp": 15},
        {"name": "Merchant", "min_coins": 15, "max_coins": 40, "min_xp": 3, "max_xp": 12},
        {"name": "Guard", "min_coins": 25, "max_coins": 60, "min_xp": 8, "max_xp": 20},
        {"name": "Farmer", "min_coins": 10, "max_coins": 30, "min_xp": 2, "max_xp": 8},
        {"name": "Miner", "min_coins": 30, "max_coins": 70, "min_xp": 10, "max_xp": 25},
        {"name": "Hunter", "min_coins": 20, "max_coins": 55, "min_xp": 6, "max_xp": 18},
        {"name": "Alchemist", "min_coins": 35, "max_coins": 80, "min_xp": 12, "max_xp": 30},
        {"name": "Bard", "min_coins": 12, "max_coins": 35, "min_xp": 4, "max_xp": 10}
    ]
    return random.choice(jobs)

def get_random_adventure_outcome() -> Dict[str, Any]:
    """Get a random adventure outcome."""
    outcomes = [
        {
            "type": "treasure",
            "title": "🏆 Treasure Found!",
            "description": "You discovered a hidden treasure chest!",
            "coins": (50, 200),
            "xp": (20, 50),
            "items": ["Gold Ring", "Silver Coin", "Gem"]
        },
        {
            "type": "monster",
            "title": "⚔️ Monster Encounter!",
            "description": "You faced a dangerous monster in battle!",
            "coins": (30, 100),
            "xp": (25, 60),
            "items": ["Monster Claw", "Potion", "Weapon Fragment"]
        },
        {
            "type": "merchant",
            "title": "🏪 Traveling Merchant",
            "description": "You met a traveling merchant and made a deal!",
            "coins": (20, 80),
            "xp": (10, 30),
            "items": ["Trade Goods", "Map", "Supplies"]
        },
        {
            "type": "puzzle",
            "title": "🧩 Ancient Puzzle",
            "description": "You solved an ancient puzzle mechanism!",
            "coins": (40, 150),
            "xp": (30, 70),
            "items": ["Ancient Artifact", "Scroll", "Key"]
        },
        {
            "type": "nothing",
            "title": "🌿 Peaceful Journey",
            "description": "You had a peaceful but uneventful journey.",
            "coins": (5, 25),
            "xp": (5, 15),
            "items": ["Herb", "Stone", "Stick"]
        }
    ]
    return random.choice(outcomes)

def get_time_until_next_use(last_use: Optional[str], cooldown_seconds: int) -> int:
    """Get time remaining until next use."""
    if not last_use:
        return 0
    
    try:
        last_use_dt = datetime.fromisoformat(last_use)
        next_use_dt = last_use_dt + timedelta(seconds=cooldown_seconds)
        now = datetime.now()
        
        if now >= next_use_dt:
            return 0
        
        return int((next_use_dt - now).total_seconds())
    except Exception as e:
        logger.error(f"Error calculating time until next use: {e}")
        return 0

def format_time_remaining(seconds: int) -> str:
    """Format seconds into human-readable time."""
    if seconds <= 0:
        return "Ready!"
    
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def calculate_battle_damage(attacker_stats: Dict[str, Any], defender_stats: Dict[str, Any]) -> int:
    """Calculate battle damage between two entities."""
    try:
        base_damage = attacker_stats.get('attack', 10)
        defense = defender_stats.get('defense', 5)
        
        # Add randomness
        damage_variance = random.uniform(0.8, 1.2)
        damage = int(base_damage * damage_variance)
        
        # Apply defense reduction
        damage = max(1, damage - defense)
        
        return damage
    except Exception as e:
        logger.error(f"Error calculating battle damage: {e}")
        return 1

def get_rarity_color(rarity: str) -> int:
    """Get color for item rarity."""
    colors = {
        'common': 0x95a5a6,
        'uncommon': 0x2ecc71,
        'rare': 0x3498db,
        'epic': 0x9b59b6,
        'legendary': 0xf39c12,
        'mythical': 0xe74c3c
    }
    return colors.get(rarity.lower(), 0x95a5a6)

def get_rarity_emoji(rarity: str) -> str:
    """Get emoji for item rarity."""
    emojis = {
        'common': '⚪',
        'uncommon': '🟢',
        'rare': '🔵',
        'epic': '🟣',
        'legendary': '🟡',
        'mythical': '🔴'
    }
    return emojis.get(rarity.lower(), '⚪')

def paginate_list(items: List[Any], page: int, per_page: int = 10) -> Tuple[List[Any], int]:
    """Paginate a list of items."""
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    total_pages = math.ceil(len(items) / per_page)
    
    return items[start_idx:end_idx], total_pages

def generate_random_stats(level: int) -> Dict[str, int]:
    """Generate random stats for monsters/NPCs based on level."""
    base_hp = 50 + (level * 10)
    base_attack = 8 + (level * 2)
    base_defense = 3 + level
    
    return {
        'hp': base_hp + random.randint(-10, 10),
        'max_hp': base_hp + random.randint(-10, 10),
        'attack': base_attack + random.randint(-2, 3),
        'defense': base_defense + random.randint(-1, 2)
    }

def calculate_guild_contribution(member_level: int, activity_score: int) -> int:
    """Calculate guild contribution score."""
    base_score = member_level * 10
    activity_bonus = activity_score * 5
    return base_score + activity_bonus

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}m {seconds}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def is_weekend() -> bool:
    """Check if it's weekend (Saturday or Sunday)."""
    return datetime.now().weekday() >= 5

def get_daily_bonus_multiplier() -> float:
    """Get daily bonus multiplier (higher on weekends)."""
    return 1.5 if is_weekend() else 1.0

def validate_user_input(input_str: str, max_length: int = 100) -> str:
    """Validate and sanitize user input."""
    if not input_str:
        return ""
    
    # Remove potentially harmful characters
    cleaned = ''.join(char for char in input_str if char.isprintable())
    
    # Truncate if too long
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned.strip()

def calculate_luck_modifier(luck_score: int) -> float:
    """Calculate luck modifier based on luck score."""
    if luck_score < 20:
        return 0.8  # Unlucky
    elif luck_score < 40:
        return 0.9  # Below average
    elif luck_score < 60:
        return 1.0  # Average
    elif luck_score < 80:
        return 1.1  # Above average
    else:
        return 1.2  # Very lucky
