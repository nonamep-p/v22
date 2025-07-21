from typing import Dict, Any, List

# RPG Constants
RPG_CONSTANTS = {
    'max_inventory_size': 50,
    'max_level': 100,
    'base_hp': 100,
    'base_attack': 10,
    'base_defense': 5,
    'work_cooldown': 3600,  # 1 hour
    'daily_cooldown': 86400,  # 24 hours
    'adventure_cooldown': 1800,  # 30 minutes
    'dungeon_cooldown': 7200,  # 2 hours
    'battle_cooldown': 300,  # 5 minutes
    'heal_cost': 50,
    'respawn_time': 300,  # 5 minutes
    'max_guild_members': 20,
    'guild_creation_cost': 5000
}

# Daily rewards
DAILY_REWARDS = {
    'base': 100,
    'level_multiplier': 10,
    'streak_bonus': 25,
    'max_streak': 7
}

# Shop items
SHOP_ITEMS = {
    'weapons': {
        'Iron Sword': {'price': 200, 'attack': 5, 'rarity': 'common'},
        'Steel Sword': {'price': 500, 'attack': 10, 'rarity': 'uncommon'},
        'Enchanted Blade': {'price': 1200, 'attack': 20, 'rarity': 'rare'},
        'Dragon Slayer': {'price': 3000, 'attack': 35, 'rarity': 'epic'},
        'Legendary Sword': {'price': 7500, 'attack': 50, 'rarity': 'legendary'}
    },
    'armor': {
        'Leather Armor': {'price': 150, 'defense': 3, 'rarity': 'common'},
        'Chain Mail': {'price': 400, 'defense': 7, 'rarity': 'uncommon'},
        'Plate Armor': {'price': 1000, 'defense': 15, 'rarity': 'rare'},
        'Dragon Scale': {'price': 2500, 'defense': 25, 'rarity': 'epic'},
        'Legendary Plate': {'price': 6000, 'defense': 40, 'rarity': 'legendary'}
    },
    'consumables': {
        'Health Potion': {'price': 50, 'heal': 30, 'rarity': 'common'},
        'Mana Potion': {'price': 40, 'mana': 25, 'rarity': 'common'},
        'Strength Potion': {'price': 100, 'attack_boost': 5, 'duration': 300, 'rarity': 'uncommon'},
        'Defense Potion': {'price': 100, 'defense_boost': 5, 'duration': 300, 'rarity': 'uncommon'},
        'Luck Potion': {'price': 200, 'luck_boost': 10, 'duration': 600, 'rarity': 'rare'}
    },
    'accessories': {
        'Ring of Power': {'price': 800, 'attack': 3, 'defense': 2, 'rarity': 'uncommon'},
        'Amulet of Health': {'price': 1000, 'hp': 50, 'rarity': 'rare'},
        'Cloak of Shadows': {'price': 1500, 'defense': 8, 'stealth': True, 'rarity': 'rare'},
        'Crown of Kings': {'price': 5000, 'attack': 15, 'defense': 10, 'hp': 100, 'rarity': 'legendary'}
    }
}

# Items dictionary for easy lookup
ITEMS = {}
for category, items in SHOP_ITEMS.items():
    ITEMS.update(items)

# Monsters for battles
MONSTERS = {
    'Goblin': {'hp': 30, 'attack': 8, 'defense': 2, 'level': 1, 'xp': 15, 'coins': 20},
    'Orc': {'hp': 50, 'attack': 12, 'defense': 4, 'level': 2, 'xp': 25, 'coins': 35},
    'Skeleton': {'hp': 40, 'attack': 10, 'defense': 3, 'level': 2, 'xp': 20, 'coins': 30},
    'Troll': {'hp': 80, 'attack': 18, 'defense': 8, 'level': 4, 'xp': 50, 'coins': 75},
    'Dragon': {'hp': 200, 'attack': 35, 'defense': 15, 'level': 8, 'xp': 150, 'coins': 250},
    'Demon': {'hp': 150, 'attack': 28, 'defense': 12, 'level': 6, 'xp': 100, 'coins': 180},
    'Lich': {'hp': 120, 'attack': 25, 'defense': 10, 'level': 5, 'xp': 80, 'coins': 150},
    'Phoenix': {'hp': 250, 'attack': 40, 'defense': 20, 'level': 10, 'xp': 200, 'coins': 350}
}

# Adventure locations
ADVENTURE_LOCATIONS = {
    'Whispering Woods': {
        'description': 'A mysterious forest filled with ancient secrets.',
        'difficulty': 1,
        'rewards': {'coins': (20, 60), 'xp': (15, 40)},
        'monsters': ['Goblin', 'Skeleton'],
        'items': ['Wooden Stick', 'Herb', 'Stone']
    },
    'Forgotten Caves': {
        'description': 'Dark caves that echo with unknown dangers.',
        'difficulty': 2,
        'rewards': {'coins': (40, 100), 'xp': (25, 60)},
        'monsters': ['Orc', 'Troll'],
        'items': ['Iron Ore', 'Crystal', 'Gem']
    },
    'Cursed Swamp': {
        'description': 'A treacherous swamp where evil lurks.',
        'difficulty': 3,
        'rewards': {'coins': (60, 150), 'xp': (40, 80)},
        'monsters': ['Demon', 'Lich'],
        'items': ['Cursed Relic', 'Poison Vial', 'Dark Crystal']
    },
    'Dragon\'s Lair': {
        'description': 'The legendary lair of an ancient dragon.',
        'difficulty': 5,
        'rewards': {'coins': (150, 300), 'xp': (100, 200)},
        'monsters': ['Dragon', 'Phoenix'],
        'items': ['Dragon Scale', 'Phoenix Feather', 'Ancient Treasure']
    }
}

# Dungeon types
DUNGEON_TYPES = {
    'Goblin Cave': {
        'description': 'A network of caves inhabited by goblins.',
        'floors': 3,
        'difficulty': 1,
        'boss': 'Goblin King',
        'rewards': {'coins': (100, 200), 'xp': (80, 150)},
        'required_level': 1
    },
    'Orc Stronghold': {
        'description': 'A fortified stronghold controlled by orcs.',
        'floors': 5,
        'difficulty': 2,
        'boss': 'Orc Chieftain',
        'rewards': {'coins': (200, 400), 'xp': (150, 300)},
        'required_level': 3
    },
    'Undead Crypt': {
        'description': 'An ancient crypt filled with undead horrors.',
        'floors': 7,
        'difficulty': 3,
        'boss': 'Skeleton Lord',
        'rewards': {'coins': (300, 600), 'xp': (250, 500)},
        'required_level': 5
    },
    'Demon Citadel': {
        'description': 'A towering citadel ruled by demons.',
        'floors': 10,
        'difficulty': 4,
        'boss': 'Demon Lord',
        'rewards': {'coins': (500, 1000), 'xp': (400, 800)},
        'required_level': 7
    },
    'Dragon\'s Tower': {
        'description': 'The ultimate challenge - a tower guarded by dragons.',
        'floors': 15,
        'difficulty': 5,
        'boss': 'Ancient Dragon',
        'rewards': {'coins': (1000, 2000), 'xp': (800, 1500)},
        'required_level': 10
    }
}

# Crafting recipes
CRAFTING_RECIPES = {
    'Iron Sword': {
        'materials': {'Iron Ore': 3, 'Wood': 1},
        'cost': 100,
        'skill_required': 1
    },
    'Steel Sword': {
        'materials': {'Steel Ingot': 2, 'Iron Ore': 1, 'Wood': 1},
        'cost': 300,
        'skill_required': 3
    },
    'Health Potion': {
        'materials': {'Herb': 2, 'Water': 1},
        'cost': 25,
        'skill_required': 1
    },
    'Leather Armor': {
        'materials': {'Leather': 5, 'Thread': 2},
        'cost': 80,
        'skill_required': 2
    }
}

# Guild perks
GUILD_PERKS = {
    'Treasure Hunter': {
        'description': 'Increases coin rewards from adventures by 20%',
        'cost': 1000,
        'effect': 'coin_bonus',
        'value': 0.2
    },
    'Experience Boost': {
        'description': 'Increases XP rewards from all activities by 15%',
        'cost': 1500,
        'effect': 'xp_bonus',
        'value': 0.15
    },
    'Combat Training': {
        'description': 'Increases attack and defense by 5%',
        'cost': 2000,
        'effect': 'combat_bonus',
        'value': 0.05
    },
    'Merchant Connections': {
        'description': 'Reduces shop prices by 10%',
        'cost': 1200,
        'effect': 'shop_discount',
        'value': 0.1
    }
}

# Achievement definitions
ACHIEVEMENTS = {
    'First Steps': {
        'description': 'Complete your first adventure',
        'requirement': 'adventures_completed',
        'value': 1,
        'reward': {'coins': 100, 'xp': 50}
    },
    'Explorer': {
        'description': 'Complete 10 adventures',
        'requirement': 'adventures_completed',
        'value': 10,
        'reward': {'coins': 500, 'xp': 200}
    },
    'Dungeon Crawler': {
        'description': 'Complete your first dungeon',
        'requirement': 'dungeons_completed',
        'value': 1,
        'reward': {'coins': 200, 'xp': 100}
    },
    'Veteran': {
        'description': 'Reach level 10',
        'requirement': 'level',
        'value': 10,
        'reward': {'coins': 1000, 'xp': 500}
    },
    'Wealthy': {
        'description': 'Accumulate 10,000 coins',
        'requirement': 'coins',
        'value': 10000,
        'reward': {'coins': 2000, 'xp': 300}
    },
    'Battle Master': {
        'description': 'Win 50 battles',
        'requirement': 'battles_won',
        'value': 50,
        'reward': {'coins': 1500, 'xp': 400}
    }
}

# Status effects
STATUS_EFFECTS = {
    'poisoned': {
        'name': 'Poisoned',
        'description': 'Takes damage over time',
        'emoji': '☠️',
        'duration': 5,
        'effect': 'damage_over_time',
        'value': 5
    },
    'blessed': {
        'name': 'Blessed',
        'description': 'Increased luck and healing',
        'emoji': '✨',
        'duration': 10,
        'effect': 'luck_boost',
        'value': 15
    },
    'cursed': {
        'name': 'Cursed',
        'description': 'Reduced luck and damage',
        'emoji': '💀',
        'duration': 8,
        'effect': 'luck_penalty',
        'value': -10
    },
    'strengthened': {
        'name': 'Strengthened',
        'description': 'Increased attack power',
        'emoji': '💪',
        'duration': 5,
        'effect': 'attack_boost',
        'value': 10
    },
    'protected': {
        'name': 'Protected',
        'description': 'Increased defense',
        'emoji': '🛡️',
        'duration': 5,
        'effect': 'defense_boost',
        'value': 8
    }
}

# Random events
RANDOM_EVENTS = {
    'merchant_discount': {
        'name': 'Merchant Discount',
        'description': 'A traveling merchant offers you a 20% discount!',
        'probability': 0.05,
        'effect': 'shop_discount',
        'value': 0.2,
        'duration': 3600  # 1 hour
    },
    'lucky_find': {
        'name': 'Lucky Find',
        'description': 'You found some coins on the ground!',
        'probability': 0.08,
        'effect': 'instant_coins',
        'value': (50, 200)
    },
    'double_xp': {
        'name': 'Double XP',
        'description': 'You feel enlightened and gain double XP for the next hour!',
        'probability': 0.03,
        'effect': 'xp_multiplier',
        'value': 2.0,
        'duration': 3600  # 1 hour
    },
    'curse': {
        'name': 'Ancient Curse',
        'description': 'You\'ve been cursed! Your luck is reduced for the next 30 minutes.',
        'probability': 0.02,
        'effect': 'luck_penalty',
        'value': -15,
        'duration': 1800  # 30 minutes
    }
}

# PvP arenas
PVP_ARENAS = {
    'Training Ground': {
        'description': 'A safe place for beginners to practice',
        'level_range': (1, 10),
        'entry_cost': 0,
        'rewards': {'coins': (10, 50), 'xp': (5, 25)}
    },
    'Colosseum': {
        'description': 'Where warriors prove their worth',
        'level_range': (5, 25),
        'entry_cost': 100,
        'rewards': {'coins': (50, 200), 'xp': (25, 100)}
    },
    'Arena of Champions': {
        'description': 'Only the strongest survive here',
        'level_range': (20, 50),
        'entry_cost': 500,
        'rewards': {'coins': (200, 800), 'xp': (100, 400)}
    },
    'Legendary Battlefield': {
        'description': 'The ultimate test of skill',
        'level_range': (40, 100),
        'entry_cost': 2000,
        'rewards': {'coins': (800, 3000), 'xp': (400, 1500)}
    }
}
