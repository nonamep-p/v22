import random
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from utils.database import get_user_rpg_data, update_user_rpg_data
from utils.constants import LUCK_LEVELS

logger = logging.getLogger(__name__)

def get_user_luck_points(user_id: str) -> int:
    """Get user's current luck points."""
    try:
        player_data = get_user_rpg_data(user_id)
        if player_data:
            return player_data.get('luck_points', 0)
        return 0
    except Exception as e:
        logger.error(f"Error getting luck points for {user_id}: {e}")
        return 0

def add_luck_points(user_id: str, points: int) -> bool:
    """Add luck points to a user."""
    try:
        player_data = get_user_rpg_data(user_id)
        if not player_data:
            return False
            
        current_luck = player_data.get('luck_points', 0)
        new_luck = max(-1000, min(9999, current_luck + points))  # Clamp between -1000 and 9999
        
        player_data['luck_points'] = new_luck
        return update_user_rpg_data(user_id, player_data)
    except Exception as e:
        logger.error(f"Error adding luck points for {user_id}: {e}")
        return False

def get_luck_status(user_id: str) -> Dict[str, Any]:
    """Get user's luck status with level and bonus."""
    luck_points = get_user_luck_points(user_id)
    
    # Determine luck level
    luck_level = 'normal'
    for level, data in LUCK_LEVELS.items():
        if data['min'] <= luck_points <= data['max']:
            luck_level = level
            break
    
    luck_data = LUCK_LEVELS[luck_level]
    
    return {
        'level': luck_level,
        'points': luck_points,
        'emoji': luck_data['emoji'],
        'bonus_percent': luck_data['bonus_percent']
    }

def roll_with_luck(user_id: str, base_chance: float) -> bool:
    """Roll with luck bonus applied."""
    try:
        luck_status = get_luck_status(user_id)
        bonus_percent = luck_status['bonus_percent']
        
        # Apply luck bonus to chance
        modified_chance = base_chance * (1 + bonus_percent / 100)
        modified_chance = max(0.0, min(1.0, modified_chance))  # Clamp between 0 and 1
        
        return random.random() < modified_chance
    except Exception as e:
        logger.error(f"Error rolling with luck for {user_id}: {e}")
        return random.random() < base_chance

def generate_loot_with_luck(user_id: str, base_loot: Dict[str, int]) -> Dict[str, int]:
    """Generate loot with luck bonuses applied."""
    try:
        luck_status = get_luck_status(user_id)
        bonus_percent = luck_status['bonus_percent']
        
        enhanced_loot = {}
        for item, amount in base_loot.items():
            # Apply luck bonus
            bonus_multiplier = 1 + (bonus_percent / 100)
            enhanced_amount = int(amount * bonus_multiplier)
            enhanced_loot[item] = max(1, enhanced_amount)  # Minimum 1
            
        return enhanced_loot
    except Exception as e:
        logger.error(f"Error generating loot with luck for {user_id}: {e}")
        return base_loot

def check_rare_event(user_id: str, base_chance: float = 0.01) -> bool:
    """Check if a rare event occurs with luck bonus."""
    return roll_with_luck(user_id, base_chance)

def weighted_random_choice(items: List[Dict[str, Any]], weight_key: str = 'weight') -> Optional[Dict[str, Any]]:
    """Choose a random item from a weighted list."""
    try:
        if not items:
            return None
            
        total_weight = sum(item.get(weight_key, 1) for item in items)
        if total_weight <= 0:
            return random.choice(items)
            
        random_value = random.uniform(0, total_weight)
        current_weight = 0
        
        for item in items:
            current_weight += item.get(weight_key, 1)
            if random_value <= current_weight:
                return item
                
        return items[-1]  # Fallback to last item
    except Exception as e:
        logger.error(f"Error in weighted random choice: {e}")
        return random.choice(items) if items else None

def calculate_critical_chance(user_id: str, base_chance: float = 0.1) -> float:
    """Calculate critical hit chance with luck bonus."""
    try:
        luck_status = get_luck_status(user_id)
        bonus_percent = luck_status['bonus_percent']
        
        # Apply luck bonus to critical chance
        modified_chance = base_chance * (1 + bonus_percent / 100)
        return max(0.0, min(1.0, modified_chance))  # Clamp between 0 and 1
    except Exception as e:
        logger.error(f"Error calculating critical chance for {user_id}: {e}")
        return base_chance

def roll_critical_hit(user_id: str, base_chance: float = 0.1) -> bool:
    """Roll for critical hit with luck bonus."""
    critical_chance = calculate_critical_chance(user_id, base_chance)
    return random.random() < critical_chance

def decay_luck_daily(user_id: str, decay_rate: float = 0.95) -> bool:
    """Apply daily luck decay."""
    try:
        player_data = get_user_rpg_data(user_id)
        if not player_data:
            return False
            
        current_luck = player_data.get('luck_points', 0)
        
        # Only decay if luck is positive
        if current_luck > 0:
            new_luck = int(current_luck * decay_rate)
            player_data['luck_points'] = new_luck
            return update_user_rpg_data(user_id, player_data)
            
        return True
    except Exception as e:
        logger.error(f"Error decaying luck for {user_id}: {e}")
        return False

def random_weighted_choice(items: List[Dict[str, Any]], weight_key: str = 'weight') -> Optional[Dict[str, Any]]:
    """Choose a random item from a weighted list - alias for weighted_random_choice."""
    return weighted_random_choice(items, weight_key)

def generate_random_encounter(user_id: str, location: str) -> Optional[Dict[str, Any]]:
    """Generate a random encounter with luck affecting rarity."""
    try:
        # Base encounter chances
        encounters = [
            {'type': 'treasure', 'rarity': 'common', 'weight': 40},
            {'type': 'monster', 'rarity': 'common', 'weight': 30},
            {'type': 'merchant', 'rarity': 'uncommon', 'weight': 15},
            {'type': 'rare_chest', 'rarity': 'rare', 'weight': 10},
            {'type': 'boss', 'rarity': 'epic', 'weight': 5}
        ]
        
        # Modify weights based on luck
        luck_status = get_luck_status(user_id)
        bonus_percent = luck_status['bonus_percent']
        
        if bonus_percent > 0:
            # Increase rare encounter weights
            for encounter in encounters:
                if encounter['rarity'] in ['rare', 'epic']:
                    encounter['weight'] *= (1 + bonus_percent / 100)
        elif bonus_percent < 0:
            # Decrease rare encounter weights
            for encounter in encounters:
                if encounter['rarity'] in ['rare', 'epic']:
                    encounter['weight'] *= (1 + bonus_percent / 100)
                    encounter['weight'] = max(1, encounter['weight'])
        
        return weighted_random_choice(encounters)
    except Exception as e:
        logger.error(f"Error generating random encounter for {user_id}: {e}")
        return None

def apply_luck_effect(user_id: str, effect_type: str, base_value: Union[int, float]) -> Union[int, float]:
    """Apply luck effect to a value."""
    try:
        luck_status = get_luck_status(user_id)
        bonus_percent = luck_status['bonus_percent']
        
        if effect_type == 'reward':
            # Positive luck increases rewards
            multiplier = 1 + (bonus_percent / 100)
        elif effect_type == 'penalty':
            # Positive luck decreases penalties
            multiplier = 1 - (bonus_percent / 100)
        else:
            # Generic effect
            multiplier = 1 + (bonus_percent / 100)
        
        if isinstance(base_value, int):
            return max(1, int(base_value * multiplier))
        else:
            return max(0.0, base_value * multiplier)
    except Exception as e:
        logger.error(f"Error applying luck effect for {user_id}: {e}")
        return base_value

def get_luck_description(user_id: str) -> str:
    """Get a description of user's current luck status."""
    try:
        luck_status = get_luck_status(user_id)
        level = luck_status['level']
        points = luck_status['points']
        emoji = luck_status['emoji']
        bonus = luck_status['bonus_percent']
        
        descriptions = {
            'cursed': "You are cursed! Bad luck follows you everywhere.",
            'unlucky': "You're having a streak of bad luck.",
            'normal': "Your luck is average, nothing special.",
            'lucky': "You're feeling lucky! Good things are happening.",
            'blessed': "You are blessed with good fortune!",
            'divine': "The gods smile upon you with incredible luck!"
        }
        
        base_desc = descriptions.get(level, "Your luck is mysterious.")
        
        return f"{emoji} **{level.title()}** ({points:+d} points)\n{base_desc}\n*{bonus:+d}% bonus to all activities*"
    except Exception as e:
        logger.error(f"Error getting luck description for {user_id}: {e}")
        return "Your luck is unknown."