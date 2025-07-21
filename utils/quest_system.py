
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
from utils.database import get_user_rpg_data, update_user_rpg_data
from utils.helpers import create_embed
from config import COLORS

logger = logging.getLogger(__name__)

# Quest types and templates
QUEST_TEMPLATES = {
    "kill_monsters": {
        "name": "Monster Slayer",
        "description": "Defeat {target} {monster_type} monsters",
        "type": "combat",
        "base_rewards": {"coins": 500, "xp": 200},
        "difficulty_multiplier": {"easy": 1, "medium": 2, "hard": 3, "extreme": 5}
    },
    "collect_items": {
        "name": "Treasure Hunter",
        "description": "Collect {target} {item_type} items",
        "type": "collection",
        "base_rewards": {"coins": 300, "xp": 150},
        "difficulty_multiplier": {"easy": 1, "medium": 2, "hard": 3, "extreme": 5}
    },
    "complete_dungeons": {
        "name": "Dungeon Crawler",
        "description": "Complete {target} {dungeon_type} dungeons",
        "type": "exploration",
        "base_rewards": {"coins": 1000, "xp": 500},
        "difficulty_multiplier": {"easy": 1, "medium": 2, "hard": 3, "extreme": 5}
    },
    "win_pvp": {
        "name": "Arena Champion",
        "description": "Win {target} PvP battles",
        "type": "pvp",
        "base_rewards": {"coins": 800, "xp": 400},
        "difficulty_multiplier": {"easy": 1, "medium": 2, "hard": 3, "extreme": 5}
    }
}

# Special story quests
STORY_QUESTS = {
    "plagg_awakening": {
        "name": "Plagg's Awakening",
        "description": "Help Plagg remember his true power by collecting ancient cheese artifacts",
        "type": "story",
        "requirements": {"level": 5},
        "objectives": [
            {"type": "collect", "target": "ancient_cheese", "amount": 3},
            {"type": "defeat", "target": "cheese_guardian", "amount": 1},
            {"type": "visit", "target": "cheese_dimension", "amount": 1}
        ],
        "rewards": {
            "coins": 5000,
            "xp": 2500,
            "items": ["plagg_blessing", "ancient_camembert"],
            "unlock": "cheese_dimension"
        },
        "next_quest": "plagg_trials"
    },
    "plagg_trials": {
        "name": "Plagg's Trials",
        "description": "Prove your worth in Plagg's chaotic trials",
        "type": "story",
        "requirements": {"level": 15, "completed_quests": ["plagg_awakening"]},
        "objectives": [
            {"type": "survive", "target": "chaos_trial", "amount": 1},
            {"type": "defeat", "target": "destruction_avatar", "amount": 1},
            {"type": "resist", "target": "chaos_corruption", "amount": 1}
        ],
        "rewards": {
            "coins": 15000,
            "xp": 7500,
            "title": "Chaos Survivor",
            "unlock_class": "destruction_adept"
        },
        "next_quest": "kwami_council"
    },
    "hidden_miraculous": {
        "name": "The Hidden Miraculous",
        "description": "Discover the lost Miraculous hidden in the depths of Paris",
        "type": "secret",
        "requirements": {"level": 25, "artifact_sets": 2},
        "objectives": [
            {"type": "explore", "target": "paris_catacombs", "amount": 1},
            {"type": "solve", "target": "ancient_riddle", "amount": 3},
            {"type": "defeat", "target": "guardian_specter", "amount": 1}
        ],
        "rewards": {
            "coins": 50000,
            "xp": 25000,
            "items": ["lost_miraculous", "guardian_seal"],
            "unlock_class": "miraculous_guardian"
        },
        "hidden": True
    }
}

# Daily/Weekly quest pools
DAILY_QUEST_POOL = [
    {"template": "kill_monsters", "difficulty": "easy", "target_range": (5, 15)},
    {"template": "collect_items", "difficulty": "easy", "target_range": (3, 8)},
    {"template": "win_pvp", "difficulty": "medium", "target_range": (1, 3)}
]

WEEKLY_QUEST_POOL = [
    {"template": "kill_monsters", "difficulty": "hard", "target_range": (50, 100)},
    {"template": "complete_dungeons", "difficulty": "medium", "target_range": (3, 7)},
    {"template": "collect_items", "difficulty": "hard", "target_range": (20, 40)}
]

def generate_daily_quest(user_id: str) -> Optional[Dict[str, Any]]:
    """Generate a daily quest for the player."""
    player_data = get_user_rpg_data(user_id)
    if not player_data:
        return None
    
    # Check if player already has a daily quest
    active_quests = player_data.get('active_quests', [])
    for quest in active_quests:
        if quest.get('quest_type') == 'daily':
            return None
    
    # Generate random daily quest
    quest_config = random.choice(DAILY_QUEST_POOL)
    template = QUEST_TEMPLATES[quest_config['template']]
    
    target = random.randint(*quest_config['target_range'])
    difficulty = quest_config['difficulty']
    multiplier = template['difficulty_multiplier'][difficulty]
    
    quest = {
        'id': f"daily_{user_id}_{int(datetime.now().timestamp())}",
        'quest_type': 'daily',
        'template': quest_config['template'],
        'name': template['name'],
        'description': template['description'].format(target=target, monster_type="various", item_type="various", dungeon_type="various"),
        'difficulty': difficulty,
        'target': target,
        'progress': 0,
        'rewards': {
            'coins': int(template['base_rewards']['coins'] * multiplier),
            'xp': int(template['base_rewards']['xp'] * multiplier)
        },
        'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
        'created_at': datetime.now().isoformat()
    }
    
    return quest

def generate_weekly_quest(user_id: str) -> Optional[Dict[str, Any]]:
    """Generate a weekly quest for the player."""
    player_data = get_user_rpg_data(user_id)
    if not player_data:
        return None
    
    # Check if player already has a weekly quest
    active_quests = player_data.get('active_quests', [])
    for quest in active_quests:
        if quest.get('quest_type') == 'weekly':
            return None
    
    # Generate random weekly quest
    quest_config = random.choice(WEEKLY_QUEST_POOL)
    template = QUEST_TEMPLATES[quest_config['template']]
    
    target = random.randint(*quest_config['target_range'])
    difficulty = quest_config['difficulty']
    multiplier = template['difficulty_multiplier'][difficulty]
    
    quest = {
        'id': f"weekly_{user_id}_{int(datetime.now().timestamp())}",
        'quest_type': 'weekly',
        'template': quest_config['template'],
        'name': f"Weekly {template['name']}",
        'description': template['description'].format(target=target, monster_type="various", item_type="various", dungeon_type="various"),
        'difficulty': difficulty,
        'target': target,
        'progress': 0,
        'rewards': {
            'coins': int(template['base_rewards']['coins'] * multiplier * 3),
            'xp': int(template['base_rewards']['xp'] * multiplier * 3)
        },
        'expires_at': (datetime.now() + timedelta(days=7)).isoformat(),
        'created_at': datetime.now().isoformat()
    }
    
    return quest

def update_quest_progress(user_id: str, action_type: str, details: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Update quest progress based on player actions."""
    player_data = get_user_rpg_data(user_id)
    if not player_data:
        return []
    
    active_quests = player_data.get('active_quests', [])
    completed_quests = []
    
    for quest in active_quests:
        if quest.get('completed'):
            continue
        
        # Check if this action applies to the quest
        template = quest.get('template')
        if template == 'kill_monsters' and action_type == 'monster_killed':
            quest['progress'] += 1
        elif template == 'collect_items' and action_type == 'item_collected':
            quest['progress'] += 1
        elif template == 'complete_dungeons' and action_type == 'dungeon_completed':
            quest['progress'] += 1
        elif template == 'win_pvp' and action_type == 'pvp_won':
            quest['progress'] += 1
        
        # Check if quest is completed
        if quest['progress'] >= quest['target']:
            quest['completed'] = True
            quest['completed_at'] = datetime.now().isoformat()
            completed_quests.append(quest)
            
            # Award rewards
            rewards = quest.get('rewards', {})
            if 'coins' in rewards:
                player_data['gold'] = player_data.get('gold', 0) + rewards['coins']
            if 'xp' in rewards:
                player_data['xp'] = player_data.get('xp', 0) + rewards['xp']
    
    # Update player data
    player_data['active_quests'] = active_quests
    update_user_rpg_data(user_id, player_data)
    
    return completed_quests

def get_available_story_quests(user_id: str) -> List[Dict[str, Any]]:
    """Get story quests available to the player."""
    player_data = get_user_rpg_data(user_id)
    if not player_data:
        return []
    
    completed_quest_names = [q.get('name') for q in player_data.get('completed_quests', [])]
    available_quests = []
    
    for quest_key, quest_data in STORY_QUESTS.items():
        # Skip hidden quests unless requirements are met
        if quest_data.get('hidden') and not meets_quest_requirements(player_data, quest_data):
            continue
        
        # Skip if already completed
        if quest_data['name'] in completed_quest_names:
            continue
        
        # Check requirements
        if meets_quest_requirements(player_data, quest_data):
            available_quests.append({
                'key': quest_key,
                'name': quest_data['name'],
                'description': quest_data['description'],
                'type': quest_data['type'],
                'objectives': quest_data['objectives'],
                'rewards': quest_data['rewards']
            })
    
    return available_quests

def meets_quest_requirements(player_data: Dict[str, Any], quest_data: Dict[str, Any]) -> bool:
    """Check if player meets quest requirements."""
    requirements = quest_data.get('requirements', {})
    
    # Level requirement
    if 'level' in requirements:
        if player_data.get('level', 1) < requirements['level']:
            return False
    
    # Completed quests requirement
    if 'completed_quests' in requirements:
        completed_names = [q.get('name') for q in player_data.get('completed_quests', [])]
        for required_quest in requirements['completed_quests']:
            if required_quest not in completed_names:
                return False
    
    # Artifact sets requirement
    if 'artifact_sets' in requirements:
        equipped_artifacts = player_data.get('equipped_artifacts', {})
        set_counts = {}
        for artifact in equipped_artifacts.values():
            if artifact:
                set_name = artifact['set']
                set_counts[set_name] = set_counts.get(set_name, 0) + 1
        
        complete_sets = sum(1 for count in set_counts.values() if count >= 4)
        if complete_sets < requirements['artifact_sets']:
            return False
    
    return True
