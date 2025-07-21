import random
import math
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class LuckSystem:
    """Advanced luck system for the RPG bot."""
    
    def __init__(self):
        self.user_luck = {}  # user_id -> luck_data
        self.luck_modifiers = {
            'cursed': -20,
            'unlucky': -10,
            'normal': 0,
            'lucky': 10,
            'blessed': 20,
            'divine': 30
        }
    
    def get_user_luck(self, user_id: str) -> Dict[str, Any]:
        """Get user's current luck data."""
        if user_id not in self.user_luck:
            self.user_luck[user_id] = {
                'base_luck': 50,  # 0-100 scale
                'temporary_modifiers': [],
                'lucky_streak': 0,
                'unlucky_streak': 0,
                'last_roll': None,
                'total_rolls': 0,
                'successful_rolls': 0
            }
        return self.user_luck[user_id]
    
    def add_luck_modifier(self, user_id: str, modifier: str, value: int, duration: int):
        """Add a temporary luck modifier."""
        luck_data = self.get_user_luck(user_id)
        expiry = datetime.now() + timedelta(seconds=duration)
        
        luck_data['temporary_modifiers'].append({
            'modifier': modifier,
            'value': value,
            'expiry': expiry
        })
    
    def calculate_current_luck(self, user_id: str) -> int:
        """Calculate user's current luck value."""
        luck_data = self.get_user_luck(user_id)
        base_luck = luck_data['base_luck']
        
        # Apply temporary modifiers
        total_modifier = 0
        active_modifiers = []
        
        for modifier in luck_data['temporary_modifiers']:
            if datetime.now() < modifier['expiry']:
                total_modifier += modifier['value']
                active_modifiers.append(modifier)
        
        # Update active modifiers
        luck_data['temporary_modifiers'] = active_modifiers
        
        # Apply streak bonuses
        if luck_data['lucky_streak'] > 3:
            total_modifier += min(luck_data['lucky_streak'] * 2, 20)
        elif luck_data['unlucky_streak'] > 3:
            total_modifier -= min(luck_data['unlucky_streak'] * 2, 20)
        
        current_luck = max(0, min(100, base_luck + total_modifier))
        return current_luck
    
    def get_luck_tier(self, luck_value: int) -> str:
        """Get luck tier based on value."""
        if luck_value < 10:
            return 'cursed'
        elif luck_value < 30:
            return 'unlucky'
        elif luck_value < 70:
            return 'normal'
        elif luck_value < 85:
            return 'lucky'
        elif luck_value < 95:
            return 'blessed'
        else:
            return 'divine'
    
    def roll_luck(self, user_id: str, difficulty: int = 50) -> Tuple[bool, int]:
        """Roll for luck-based success."""
        luck_data = self.get_user_luck(user_id)
        current_luck = self.calculate_current_luck(user_id)
        
        # Calculate success chance
        success_chance = current_luck + (100 - difficulty)
        success_chance = max(5, min(95, success_chance))  # Clamp between 5-95%
        
        # Roll
        roll = random.randint(1, 100)
        success = roll <= success_chance
        
        # Update streak
        if success:
            luck_data['lucky_streak'] += 1
            luck_data['unlucky_streak'] = 0
        else:
            luck_data['unlucky_streak'] += 1
            luck_data['lucky_streak'] = 0
        
        # Update stats
        luck_data['total_rolls'] += 1
        if success:
            luck_data['successful_rolls'] += 1
        luck_data['last_roll'] = datetime.now()
        
        return success, roll

# Global luck system instance
luck_system = LuckSystem()

def roll_with_luck(user_id: str, base_chance: float, difficulty: int = 50) -> bool:
    """Roll with luck modifiers applied."""
    try:
        current_luck = luck_system.calculate_current_luck(user_id)
        
        # Apply luck modifier to base chance
        luck_modifier = (current_luck - 50) / 100  # -0.5 to 0.5
        modified_chance = base_chance * (1 + luck_modifier)
        
        # Ensure reasonable bounds
        modified_chance = max(0.01, min(0.99, modified_chance))
        
        success, roll = luck_system.roll_luck(user_id, difficulty)
        
        # Additional roll for base chance
        return random.random() < modified_chance or success
    except Exception as e:
        logger.error(f"Error in roll_with_luck: {e}")
        return random.random() < base_chance

def check_rare_event(user_id: str, base_probability: float) -> bool:
    """Check for rare event occurrence with luck."""
    try:
        current_luck = luck_system.calculate_current_luck(user_id)
        
        # Luck affects rare events more dramatically
        luck_multiplier = 1 + ((current_luck - 50) / 50)  # 0.5x to 2x multiplier
        modified_probability = base_probability * luck_multiplier
        
        return random.random() < modified_probability
    except Exception as e:
        logger.error(f"Error in check_rare_event: {e}")
        return random.random() < base_probability

def get_luck_status(user_id: str) -> Dict[str, Any]:
    """Get comprehensive luck status for user."""
    try:
        luck_data = luck_system.get_user_luck(user_id)
        current_luck = luck_system.calculate_current_luck(user_id)
        tier = luck_system.get_luck_tier(current_luck)
        
        # Calculate success rate
        success_rate = 0
        if luck_data['total_rolls'] > 0:
            success_rate = (luck_data['successful_rolls'] / luck_data['total_rolls']) * 100
        
        # Get active conditions
        active_conditions = []
        for modifier in luck_data['temporary_modifiers']:
            if datetime.now() < modifier['expiry']:
                remaining = int((modifier['expiry'] - datetime.now()).total_seconds())
                active_conditions.append(f"{modifier['modifier']} ({remaining}s)")
        
        return {
            'current_luck': current_luck,
            'luck_tier': tier,
            'luck_multiplier': 1 + ((current_luck - 50) / 100),
            'lucky_streak': luck_data['lucky_streak'],
            'unlucky_streak': luck_data['unlucky_streak'],
            'success_rate': success_rate,
            'total_rolls': luck_data['total_rolls'],
            'active_conditions': active_conditions
        }
    except Exception as e:
        logger.error(f"Error getting luck status: {e}")
        return {
            'current_luck': 50,
            'luck_tier': 'normal',
            'luck_multiplier': 1.0,
            'lucky_streak': 0,
            'unlucky_streak': 0,
            'success_rate': 0,
            'total_rolls': 0,
            'active_conditions': []
        }

def apply_luck_potion(user_id: str, duration: int = 3600):
    """Apply luck potion effect."""
    try:
        luck_system.add_luck_modifier(user_id, 'Luck Potion', 15, duration)
        logger.info(f"Applied luck potion to user {user_id}")
    except Exception as e:
        logger.error(f"Error applying luck potion: {e}")

def trigger_curse(user_id: str, duration: int = 1800):
    """Trigger a curse effect."""
    try:
        luck_system.add_luck_modifier(user_id, 'Cursed', -20, duration)
        logger.info(f"Applied curse to user {user_id}")
    except Exception as e:
        logger.error(f"Error triggering curse: {e}")

def blessing_ritual(user_id: str, duration: int = 7200):
    """Apply blessing effect."""
    try:
        luck_system.add_luck_modifier(user_id, 'Blessed', 25, duration)
        logger.info(f"Applied blessing to user {user_id}")
    except Exception as e:
        logger.error(f"Error applying blessing: {e}")

def calculate_critical_chance(user_id: str, base_chance: float = 0.1) -> float:
    """Calculate critical hit chance with luck."""
    try:
        current_luck = luck_system.calculate_current_luck(user_id)
        luck_modifier = (current_luck - 50) / 200  # -0.25 to 0.25
        return min(0.5, max(0.01, base_chance + luck_modifier))
    except Exception as e:
        logger.error(f"Error calculating critical chance: {e}")
        return base_chance

def weighted_random_choice(items: List[Dict[str, Any]], user_id: str, weight_key: str = 'weight') -> Any:
    """Choose random item from list with luck-weighted probability."""
    try:
        if not items:
            return None
        
        current_luck = luck_system.calculate_current_luck(user_id)
        luck_modifier = (current_luck - 50) / 100  # -0.5 to 0.5
        
        # Adjust weights based on luck (higher luck = better items more likely)
        adjusted_items = []
        for item in items:
            weight = item.get(weight_key, 1)
            rarity_modifier = 1.0
            
            # If item has rarity, adjust weight
            if 'rarity' in item:
                rarity_weights = {
                    'common': 1.0,
                    'uncommon': 0.8,
                    'rare': 0.6,
                    'epic': 0.4,
                    'legendary': 0.2
                }
                rarity_modifier = rarity_weights.get(item['rarity'], 1.0)
            
            # Apply luck modifier (good luck makes rare items more likely)
            if luck_modifier > 0:
                adjusted_weight = weight * (1 + luck_modifier * (1 - rarity_modifier))
            else:
                adjusted_weight = weight * (1 + luck_modifier * rarity_modifier)
            
            adjusted_items.append((item, max(0.1, adjusted_weight)))
        
        # Weighted random selection
        total_weight = sum(weight for _, weight in adjusted_items)
        if total_weight <= 0:
            return random.choice(items)
        
        rand_value = random.random() * total_weight
        current_weight = 0
        
        for item, weight in adjusted_items:
            current_weight += weight
            if rand_value <= current_weight:
                return item
        
        return adjusted_items[-1][0]  # Fallback
    except Exception as e:
        logger.error(f"Error in weighted_random_choice: {e}")
        return random.choice(items) if items else None

def generate_loot_with_luck(user_id: str, base_loot: Dict[str, Any]) -> Dict[str, Any]:
    """Generate loot with luck modifiers."""
    try:
        luck_status = get_luck_status(user_id)
        luck_multiplier = luck_status['luck_multiplier']
        
        # Apply luck to coin rewards
        coins = base_loot.get('coins', 0)
        if isinstance(coins, tuple):
            min_coins, max_coins = coins
            coins = random.randint(min_coins, max_coins)
        
        adjusted_coins = int(coins * luck_multiplier)
        
        # Apply luck to XP rewards
        xp = base_loot.get('xp', 0)
        if isinstance(xp, tuple):
            min_xp, max_xp = xp
            xp = random.randint(min_xp, max_xp)
        
        adjusted_xp = int(xp * luck_multiplier)
        
        # Check for bonus items with luck
        bonus_items = []
        if check_rare_event(user_id, 0.1):  # 10% base chance for bonus
            bonus_items = ['Lucky Charm', 'Rare Gem', 'Ancient Coin']
        
        return {
            'coins': adjusted_coins,
            'xp': adjusted_xp,
            'items': base_loot.get('items', []) + bonus_items,
            'luck_applied': True,
            'luck_multiplier': luck_multiplier
        }
    except Exception as e:
        logger.error(f"Error generating loot with luck: {e}")
        return base_loot
