
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.database import get_user_rpg_data, update_user_rpg_data
from utils.helpers import create_embed
from config import COLORS

logger = logging.getLogger(__name__)

# Achievement definitions with tiers and hidden unlocks
ACHIEVEMENTS = {
    # Combat Achievements
    "first_blood": {
        "name": "First Blood",
        "description": "Win your first battle",
        "type": "combat",
        "requirement": {"battles_won": 1},
        "rewards": {"coins": 100, "xp": 50},
        "hidden": False,
        "tier": "bronze"
    },
    "battle_veteran": {
        "name": "Battle Veteran",
        "description": "Win 100 battles",
        "type": "combat",
        "requirement": {"battles_won": 100},
        "rewards": {"coins": 5000, "xp": 2000, "title": "Veteran"},
        "hidden": False,
        "tier": "gold"
    },
    "untouchable": {
        "name": "Untouchable",
        "description": "Win 10 battles without taking damage",
        "type": "combat",
        "requirement": {"perfect_battles": 10},
        "rewards": {"coins": 3000, "xp": 1500, "title": "Untouchable"},
        "hidden": True,
        "tier": "platinum"
    },
    "god_slayer": {
        "name": "God Slayer",
        "description": "Defeat a Legendary boss while 10 levels below it",
        "type": "combat",
        "requirement": {"legendary_underdog_kills": 1},
        "rewards": {"coins": 50000, "xp": 25000, "title": "God Slayer", "unlock_class": "divine_champion"},
        "hidden": True,
        "tier": "legendary"
    },
    
    # Exploration Achievements
    "first_steps": {
        "name": "First Steps",
        "description": "Complete your first adventure",
        "type": "exploration",
        "requirement": {"adventures_completed": 1},
        "rewards": {"coins": 50, "xp": 25},
        "hidden": False,
        "tier": "bronze"
    },
    "world_walker": {
        "name": "World Walker",
        "description": "Visit every location in Paris",
        "type": "exploration",
        "requirement": {"unique_locations": 25},
        "rewards": {"coins": 10000, "xp": 5000, "title": "World Walker"},
        "hidden": False,
        "tier": "gold"
    },
    "dimension_hopper": {
        "name": "Dimension Hopper",
        "description": "Complete the Miraculous Box 50 times",
        "type": "exploration",
        "requirement": {"miraculous_box_completions": 50},
        "rewards": {"coins": 25000, "xp": 15000, "title": "Dimension Hopper", "unlock_class": "reality_bender"},
        "hidden": True,
        "tier": "legendary"
    },
    
    # Collection Achievements
    "collector": {
        "name": "Collector",
        "description": "Own 50 different items",
        "type": "collection",
        "requirement": {"unique_items_owned": 50},
        "rewards": {"coins": 2000, "xp": 1000},
        "hidden": False,
        "tier": "silver"
    },
    "artifact_master": {
        "name": "Artifact Master",
        "description": "Collect a full set of each Kwami artifact type",
        "type": "collection",
        "requirement": {"complete_artifact_sets": 5},
        "rewards": {"coins": 100000, "xp": 50000, "title": "Artifact Master", "unlock_class": "kwami_chosen"},
        "hidden": True,
        "tier": "legendary"
    },
    
    # Hidden Class Unlock Achievements
    "cheese_connoisseur": {
        "name": "Cheese Connoisseur",
        "description": "Consume 1000 cheese items and defeat Plagg's Shadow",
        "type": "hidden_class",
        "requirement": {"cheese_consumed": 1000, "plagg_shadow_defeated": 1},
        "rewards": {"unlock_class": "cheese_sage", "title": "Plagg's Chosen"},
        "hidden": True,
        "tier": "mythic"
    },
    "time_master": {
        "name": "Master of Time",
        "description": "Use Chrono Weaver abilities 500 times and complete the Time Rift dungeon",
        "type": "hidden_class",
        "requirement": {"chrono_abilities_used": 500, "time_rift_completed": 1},
        "rewards": {"unlock_class": "temporal_lord", "title": "Time Lord"},
        "hidden": True,
        "tier": "mythic"
    },
    "shadow_walker": {
        "name": "Shadow Walker",
        "description": "Win 100 PvP matches using only stealth abilities",
        "type": "hidden_class",
        "requirement": {"stealth_pvp_wins": 100},
        "rewards": {"unlock_class": "shadow_assassin", "title": "Shadow Lord"},
        "hidden": True,
        "tier": "mythic"
    },
    
    # Special Achievements
    "plagg_favorite": {
        "name": "Plagg's Favorite",
        "description": "Complete all cheese-related quests and achievements",
        "type": "special",
        "requirement": {"cheese_achievements": 10, "cheese_quests": 15},
        "rewards": {"coins": 1000000, "title": "Plagg's Avatar", "special_ability": "cheese_mastery"},
        "hidden": True,
        "tier": "mythic"
    }
}

# Hidden classes that can only be unlocked through achievements
HIDDEN_CLASSES = {
    "divine_champion": {
        "name": "Divine Champion",
        "emoji": "👑",
        "description": "Blessed by the gods themselves, transcending mortal limits",
        "role": "Transcendent DPS",
        "unlock_requirement": "god_slayer",
        "base_stats": {
            "strength": 20,
            "dexterity": 15,
            "constitution": 18,
            "intelligence": 12,
            "wisdom": 15,
            "charisma": 20
        },
        "starting_skills": ["divine_strike", "heavenly_shield", "gods_wrath"],
        "ultimate": "Divine Intervention",
        "passive": "Divine Blessing - All stats +25%, immunity to debuffs"
    },
    "reality_bender": {
        "name": "Reality Bender",
        "emoji": "🌀",
        "description": "Master of dimensional forces, bending reality itself",
        "role": "Reality Controller",
        "unlock_requirement": "dimension_hopper",
        "base_stats": {
            "strength": 10,
            "dexterity": 18,
            "constitution": 14,
            "intelligence": 22,
            "wisdom": 18,
            "charisma": 18
        },
        "starting_skills": ["reality_tear", "dimension_shift", "void_walk"],
        "ultimate": "Reality Storm",
        "passive": "Dimensional Mastery - Can attack from any dimension"
    },
    "kwami_chosen": {
        "name": "Kwami Chosen",
        "emoji": "✨",
        "description": "Selected by the Kwami themselves as their champion",
        "role": "Miraculous Master",
        "unlock_requirement": "artifact_master",
        "base_stats": {
            "strength": 16,
            "dexterity": 16,
            "constitution": 16,
            "intelligence": 16,
            "wisdom": 16,
            "charisma": 20
        },
        "starting_skills": ["kwami_bond", "miraculous_power", "unified_strength"],
        "ultimate": "Kwami Unification",
        "passive": "Miraculous Harmony - All abilities cost 50% less energy"
    },
    "cheese_sage": {
        "name": "Cheese Sage",
        "emoji": "🧀",
        "description": "The ultimate cheese master, blessed by Plagg himself",
        "role": "Chaos Incarnate",
        "unlock_requirement": "cheese_connoisseur",
        "base_stats": {
            "strength": 25,
            "dexterity": 20,
            "constitution": 20,
            "intelligence": 15,
            "wisdom": 10,
            "charisma": 25
        },
        "starting_skills": ["cheese_storm", "cataclysm", "chaos_field"],
        "ultimate": "Plagg's Wrath",
        "passive": "Chaos Incarnate - Random massive stat boosts each turn"
    },
    "temporal_lord": {
        "name": "Temporal Lord",
        "emoji": "⏰",
        "description": "Master of all time and space",
        "role": "Time Controller",
        "unlock_requirement": "time_master",
        "base_stats": {
            "strength": 12,
            "dexterity": 25,
            "constitution": 16,
            "intelligence": 22,
            "wisdom": 20,
            "charisma": 15
        },
        "starting_skills": ["time_stop", "temporal_rewind", "future_sight"],
        "ultimate": "Temporal Mastery",
        "passive": "Time Lord - Can act twice per turn"
    },
    "shadow_assassin": {
        "name": "Shadow Assassin",
        "emoji": "🌑",
        "description": "One with the shadows, death incarnate",
        "role": "Ultimate Assassin",
        "unlock_requirement": "shadow_walker",
        "base_stats": {
            "strength": 18,
            "dexterity": 25,
            "constitution": 12,
            "intelligence": 15,
            "wisdom": 18,
            "charisma": 12
        },
        "starting_skills": ["shadow_kill", "void_step", "darkness_embrace"],
        "ultimate": "Shadow Realm",
        "passive": "Shadow Master - Invisible until attacking, +200% crit damage"
    }
}

def check_achievement_progress(user_id: str, achievement_key: str, player_data: Dict[str, Any]) -> bool:
    """Check if a player has completed an achievement."""
    achievement = ACHIEVEMENTS.get(achievement_key)
    if not achievement:
        return False
    
    # Check if already completed
    completed_achievements = player_data.get('completed_achievements', [])
    if achievement_key in completed_achievements:
        return False
    
    # Check requirements
    requirements = achievement['requirement']
    for req_key, req_value in requirements.items():
        player_value = player_data.get('stats', {}).get(req_key, 0)
        if player_value < req_value:
            return False
    
    return True

def award_achievement(user_id: str, achievement_key: str) -> Optional[Dict[str, Any]]:
    """Award an achievement to a player and return the achievement data."""
    player_data = get_user_rpg_data(user_id)
    if not player_data:
        return None
    
    achievement = ACHIEVEMENTS.get(achievement_key)
    if not achievement:
        return None
    
    # Check if already completed
    completed_achievements = player_data.get('completed_achievements', [])
    if achievement_key in completed_achievements:
        return None
    
    # Award the achievement
    completed_achievements.append(achievement_key)
    player_data['completed_achievements'] = completed_achievements
    
    # Apply rewards
    rewards = achievement.get('rewards', {})
    if 'coins' in rewards:
        player_data['gold'] = player_data.get('gold', 0) + rewards['coins']
    if 'xp' in rewards:
        player_data['xp'] = player_data.get('xp', 0) + rewards['xp']
    if 'title' in rewards:
        titles = player_data.get('titles', [])
        if rewards['title'] not in titles:
            titles.append(rewards['title'])
            player_data['titles'] = titles
    if 'unlock_class' in rewards:
        unlocked_classes = player_data.get('unlocked_hidden_classes', [])
        if rewards['unlock_class'] not in unlocked_classes:
            unlocked_classes.append(rewards['unlock_class'])
            player_data['unlocked_hidden_classes'] = unlocked_classes
    
    # Add achievement timestamp
    achievement_data = {
        'key': achievement_key,
        'unlocked_at': datetime.now().isoformat(),
        'tier': achievement.get('tier', 'bronze')
    }
    
    update_user_rpg_data(user_id, player_data)
    return achievement_data

def get_available_achievements(user_id: str) -> List[Dict[str, Any]]:
    """Get list of achievements visible to the player."""
    player_data = get_user_rpg_data(user_id)
    if not player_data:
        return []
    
    completed = player_data.get('completed_achievements', [])
    available = []
    
    for key, achievement in ACHIEVEMENTS.items():
        # Skip hidden achievements unless requirements are close to being met
        if achievement.get('hidden', False):
            # Check if player is close to unlocking (80% of requirements met)
            requirements = achievement['requirement']
            progress = 0
            total = len(requirements)
            
            for req_key, req_value in requirements.items():
                player_value = player_data.get('stats', {}).get(req_key, 0)
                if player_value >= req_value * 0.8:  # 80% progress
                    progress += 1
            
            if progress < total:
                continue
        
        achievement_info = {
            'key': key,
            'name': achievement['name'],
            'description': achievement['description'],
            'tier': achievement.get('tier', 'bronze'),
            'completed': key in completed,
            'hidden': achievement.get('hidden', False),
            'rewards': achievement.get('rewards', {})
        }
        
        # Add progress info if not completed
        if key not in completed:
            progress_info = {}
            for req_key, req_value in achievement['requirement'].items():
                player_value = player_data.get('stats', {}).get(req_key, 0)
                progress_info[req_key] = {
                    'current': player_value,
                    'required': req_value,
                    'percentage': min(100, int((player_value / req_value) * 100))
                }
            achievement_info['progress'] = progress_info
        
        available.append(achievement_info)
    
    return sorted(available, key=lambda x: (x['completed'], x['tier']))

def check_hidden_class_unlock(user_id: str, class_key: str) -> bool:
    """Check if player can unlock a hidden class."""
    player_data = get_user_rpg_data(user_id)
    if not player_data:
        return False
    
    hidden_class = HIDDEN_CLASSES.get(class_key)
    if not hidden_class:
        return False
    
    # Check if already unlocked
    unlocked_classes = player_data.get('unlocked_hidden_classes', [])
    if class_key in unlocked_classes:
        return True
    
    # Check unlock requirement (achievement)
    unlock_req = hidden_class['unlock_requirement']
    completed_achievements = player_data.get('completed_achievements', [])
    
    return unlock_req in completed_achievements
