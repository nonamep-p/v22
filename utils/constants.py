"""
Enhanced Constants for the Epic RPG Bot with Plagg theme
"""
from typing import Dict, Any, List

# RPG System Constants
RPG_CONSTANTS = {
    # Cooldowns (in seconds)
    'work_cooldown': 3600,      # 1 hour
    'daily_cooldown': 86400,    # 24 hours
    'adventure_cooldown': 1800,  # 30 minutes
    'battle_cooldown': 300,     # 5 minutes
    'dungeon_cooldown': 7200,   # 2 hours
    'craft_cooldown': 600,      # 10 minutes
    'gather_cooldown': 900,     # 15 minutes
    'trade_cooldown': 1800,     # 30 minutes
    'quest_cooldown': 3600,     # 1 hour

    # Costs
    'heal_cost': 50,            # Cost to heal
    'revive_cost': 100,         # Cost to revive
    'guild_creation_cost': 5000, # Cost to create guild
    'profession_unlock_cost': 1000, # Cost to unlock profession

    # Level system
    'base_xp': 100,             # XP needed for level 2
    'xp_multiplier': 1.5,       # XP multiplier per level
    'max_level': 100,           # Maximum player level
    'prestige_level': 50,       # Level required for prestige

    # Battle system
    'critical_chance': 0.1,     # 10% critical hit chance
    'critical_multiplier': 2.0,  # 2x damage on critical
    'max_party_size': 4,        # Maximum party members

    # Luck system
    'luck_decay': 0.95,         # Luck decay per day
    'max_luck': 1000,           # Maximum luck points
}

# Weapon Database
WEAPONS = {
    "rusty_dagger": {
        "name": "Rusty Dagger",
        "attack": 8,
        "rarity": "common",
        "price": 25,
        "description": "A worn but reliable blade"
    },
    "iron_sword": {
        "name": "Iron Sword",
        "attack": 15,
        "rarity": "common",
        "price": 100,
        "description": "A sturdy iron blade for beginners"
    },
    "steel_longsword": {
        "name": "Steel Longsword",
        "attack": 25,
        "rarity": "uncommon",
        "price": 300,
        "description": "A well-crafted steel sword"
    },
    "mithril_blade": {
        "name": "Mithril Blade",
        "attack": 40,
        "rarity": "rare",
        "price": 800,
        "description": "A lightweight yet powerful blade"
    },
    "dragon_slayer": {
        "name": "Dragon Slayer",
        "attack": 60,
        "rarity": "epic",
        "price": 2000,
        "description": "Forged to slay the mightiest beasts",
        "special": "bonus_vs_dragons"
    },
    "excalibur": {
        "name": "Excalibur",
        "attack": 100,
        "rarity": "legendary",
        "price": 10000,
        "description": "The legendary sword of kings",
        "special": "holy_light"
    },
    "world_ender": {
        "name": "World Ender",
        "attack": 999999,
        "rarity": "omnipotent",
        "price": 999999999,
        "description": "A weapon capable of ending worlds",
        "special": "ultimate_destruction"
    }
}

# Armor Database
ARMOR = {
    "cloth_robe": {
        "name": "Cloth Robe",
        "defense": 5,
        "rarity": "common",
        "price": 20,
        "description": "Simple cloth protection"
    },
    "leather_armor": {
        "name": "Leather Armor",
        "defense": 12,
        "rarity": "common",
        "price": 75,
        "description": "Basic leather protection"
    },
    "chainmail": {
        "name": "Chainmail",
        "defense": 20,
        "rarity": "uncommon",
        "price": 250,
        "description": "Interlocked metal rings"
    },
    "plate_armor": {
        "name": "Plate Armor",
        "defense": 35,
        "rarity": "rare",
        "price": 600,
        "description": "Heavy metal plate protection"
    },
    "dragon_scale_mail": {
        "name": "Dragon Scale Mail",
        "defense": 50,
        "rarity": "epic",
        "price": 1500,
        "description": "Armor made from dragon scales",
        "special": "fire_resistance"
    },
    "divine_protection": {
        "name": "Divine Protection",
        "defense": 80,
        "rarity": "legendary",
        "price": 8000,
        "description": "Blessed armor of the gods",
        "special": "damage_reflect"
    }
}

# Rarity Colors and Weights
RARITY_COLORS = {
    "common": 0x808080,      # Gray
    "uncommon": 0x1eff00,    # Green
    "rare": 0x0099ff,        # Blue
    "epic": 0x9966cc,        # Purple
    "legendary": 0xff8000,   # Orange
    "mythic": 0xff0040,      # Red
    "divine": 0xffff00,      # Yellow
    "omnipotent": 0xff69b4   # Pink
}

RARITY_WEIGHTS = {
    "common": 0.5,      # 50%
    "uncommon": 0.25,   # 25%
    "rare": 0.15,       # 15%
    "epic": 0.08,       # 8%
    "legendary": 0.015, # 1.5%
    "mythic": 0.004,    # 0.4%
    "divine": 0.001,    # 0.1%
    "omnipotent": 0.0001 # 0.01%
}

# PvP Arenas
PVP_ARENAS = {
    "training_ground": {
        "name": "Training Ground",
        "entry_fee": 50,
        "winner_multiplier": 1.5,
        "description": "A safe place to practice combat"
    },
    "colosseum": {
        "name": "Colosseum",
        "entry_fee": 200,
        "winner_multiplier": 2.0,
        "description": "The grand arena of champions"
    },
    "shadow_pit": {
        "name": "Shadow Pit",
        "entry_fee": 500,
        "winner_multiplier": 3.0,
        "description": "A dangerous underground arena"
    }
}

# Omnipotent Item (Reality Stone)
OMNIPOTENT_ITEM = {
    "Reality Stone": {
        "name": "Reality Stone",
        "rarity": "omnipotent",
        "price": 999999999,
        "description": "Grants the power to have any non-omnipotent item",
        "special": "reality_manipulation"
    }
}

# Shop Items (Consolidated)
SHOP_ITEMS = {
    # Weapons
    "rusty_dagger": {
        "name": "Rusty Dagger",
        "category": "weapons",
        "attack": 8,
        "rarity": "common",
        "price": 25,
        "description": "A worn but reliable blade"
    },
    "iron_sword": {
        "name": "Iron Sword",
        "category": "weapons",
        "attack": 15,
        "rarity": "common",
        "price": 100,
        "description": "A sturdy iron blade for beginners"
    },
    "steel_longsword": {
        "name": "Steel Longsword",
        "category": "weapons",
        "attack": 25,
        "rarity": "uncommon",
        "price": 300,
        "description": "A well-crafted steel sword"
    },
    "mithril_blade": {
        "name": "Mithril Blade",
        "category": "weapons",
        "attack": 40,
        "rarity": "rare",
        "price": 800,
        "description": "A lightweight yet powerful blade"
    },
    "dragon_slayer": {
        "name": "Dragon Slayer",
        "category": "weapons",
        "attack": 60,
        "rarity": "epic",
        "price": 2000,
        "description": "Forged to slay the mightiest beasts",
        "effect": "bonus_vs_dragons"
    },

    # Armor
    "cloth_robe": {
        "name": "Cloth Robe",
        "category": "armor",
        "defense": 5,
        "rarity": "common",
        "price": 20,
        "description": "Simple cloth protection"
    },
    "leather_armor": {
        "name": "Leather Armor",
        "category": "armor",
        "defense": 12,
        "rarity": "common",
        "price": 75,
        "description": "Basic leather protection"
    },
    "chainmail": {
        "name": "Chainmail",
        "category": "armor",
        "defense": 20,
        "rarity": "uncommon",
        "price": 250,
        "description": "Interlocked metal rings"
    },
    "plate_armor": {
        "name": "Plate Armor",
        "category": "armor",
        "defense": 35,
        "rarity": "rare",
        "price": 600,
        "description": "Heavy metal plate protection"
    },

    # Consumables
    "health_potion": {
        "name": "Health Potion",
        "category": "consumables",
        "rarity": "common",
        "price": 50,
        "description": "Restores 50 HP",
        "effect": "heal_50"
    },
    "golden_elixir": {
        "name": "Golden Elixir",
        "category": "consumables",
        "rarity": "rare",
        "price": 500,
        "description": "Restores 500 HP",
        "effect": "heal_500"
    },
    "mana_potion": {
        "name": "Mana Potion",
        "category": "consumables",
        "rarity": "common",
        "price": 40,
        "description": "Restores 50 MP",
        "effect": "mana_50"
    },
    "lucky_charm": {
        "name": "Lucky Charm",
        "category": "consumables",
        "rarity": "uncommon",
        "price": 200,
        "description": "Increases luck for next adventure",
        "effect": "luck_boost"
    },
    "xp_bottle": {
        "name": "XP Bottle",
        "category": "consumables",
        "rarity": "uncommon",
        "price": 150,
        "description": "Grants 100 XP when used",
        "effect": "xp_100"
    },
    "lootbox": {
        "name": "Lootbox",
        "category": "consumables",
        "rarity": "rare",
        "price": 1000,
        "description": "Contains random rewards",
        "effect": "random_reward"
    },

    # Accessories
    "iron_ring": {
        "name": "Iron Ring",
        "category": "accessories",
        "rarity": "common",
        "price": 100,
        "description": "A simple iron ring",
        "attack": 2
    },
    "silver_amulet": {
        "name": "Silver Amulet",
        "category": "accessories",
        "rarity": "uncommon",
        "price": 300,
        "description": "Increases magical power",
        "mana": 20
    },
    "golden_crown": {
        "name": "Golden Crown",
        "category": "accessories",
        "rarity": "rare",
        "price": 1000,
        "description": "Increases all stats",
        "attack": 5,
        "defense": 5,
        "hp": 50
    }
}

# Player Classes
PLAYER_CLASSES = {
    "cheese_guardian": {
        "name": "Cheese Guardian",
        "emoji": "🛡️",
        "description": "Warriors who protect the sacred cheese vaults of Paris",
        "base_stats": {
            "strength": 15,
            "dexterity": 8,
            "constitution": 14,
            "intelligence": 6,
            "wisdom": 10,
            "charisma": 7,
            "hp": 120,
            "mana": 30,
            "stamina": 80
        },
        "special_ability": "Cheese Shield - Reduces incoming damage by 25%"
    },
    "kwami_sorcerer": {
        "name": "Kwami Sorcerer", 
        "emoji": "✨",
        "description": "Mages who channel the power of ancient kwamis",
        "base_stats": {
            "strength": 6,
            "dexterity": 10,
            "constitution": 8,
            "intelligence": 16,
            "wisdom": 14,
            "charisma": 12,
            "hp": 80,
            "mana": 120,
            "stamina": 50
        },
        "special_ability": "Miraculous Magic - Spells cost 20% less mana"
    },
    "shadow_cat": {
        "name": "Shadow Cat",
        "emoji": "🐾", 
        "description": "Rogues who move unseen through Parisian shadows",
        "base_stats": {
            "strength": 10,
            "dexterity": 16,
            "constitution": 9,
            "intelligence": 12,
            "wisdom": 8,
            "charisma": 11,
            "hp": 90,
            "mana": 60,
            "stamina": 100
        },
        "special_ability": "Shadow Strike - 30% chance for critical hits"
    },
    "cheese_hunter": {
        "name": "Cheese Hunter",
        "emoji": "🏹",
        "description": "Archers who track down the finest cheeses across the world",
        "base_stats": {
            "strength": 12,
            "dexterity": 15,
            "constitution": 10,
            "intelligence": 9,
            "wisdom": 13,
            "charisma": 8,
            "hp": 100,
            "mana": 50,
            "stamina": 90
        },
        "special_ability": "Eagle Eye - Ranged attacks have increased accuracy"
    },
    "tikki_disciple": {
        "name": "Tikki Disciple",
        "emoji": "🍪",
        "description": "Healers blessed by the kwami of creation",
        "base_stats": {
            "strength": 7,
            "dexterity": 9,
            "constitution": 12,
            "intelligence": 13,
            "wisdom": 16,
            "charisma": 14,
            "hp": 95,
            "mana": 110,
            "stamina": 60
        },
        "special_ability": "Healing Light - Healing spells are 50% more effective"
    },
    "chrono_weave": {
        "name": "Chrono Weave",
        "emoji": "⏰",
        "description": "Hidden masters of time manipulation (LOCKED)",
        "base_stats": {
            "strength": 12,
            "dexterity": 14,
            "constitution": 11,
            "intelligence": 15,
            "wisdom": 13,
            "charisma": 10,
            "hp": 105,
            "mana": 130,
            "stamina": 85
        },
        "special_ability": "Temporal Control - Can manipulate time in combat",
        "locked": True
    }
}

# Professions
PROFESSIONS = {
    "blacksmith": {
        "name": "Blacksmith",
        "description": "Forge powerful weapons and armor",
        "max_level": 50,
        "gathering_spots": ["iron_mine", "coal_deposit", "gem_cave"]
    },
    "alchemist": {
        "name": "Alchemist",
        "description": "Create potions and magical items",
        "max_level": 50,
        "gathering_spots": ["herb_garden", "mushroom_grove", "crystal_spring"]
    },
    "enchanter": {
        "name": "Enchanter",
        "description": "Enhance items with magical properties",
        "max_level": 50,
        "gathering_spots": ["magic_library", "ley_line", "arcane_tower"]
    }
}

# Crafting Materials
GATHERING_MATERIALS = {
    "iron_ore": {
        "name": "Iron Ore",
        "base_chance": 0.6,
        "locations": ["iron_mine"]
    },
    "coal": {
        "name": "Coal",
        "base_chance": 0.5,
        "locations": ["coal_deposit"]
    },
    "healing_herb": {
        "name": "Healing Herb",
        "base_chance": 0.7,
        "locations": ["herb_garden"]
    },
    "magic_crystal": {
        "name": "Magic Crystal",
        "base_chance": 0.3,
        "locations": ["crystal_spring", "gem_cave"]
    }
}

# Crafting Recipes
CRAFTING_RECIPES = {
    "iron_sword_craft": {
        "name": "Iron Sword",
        "profession": "blacksmith",
        "level_required": 5,
        "materials": {
            "iron_ore": 3,
            "coal": 1
        },
        "result": {
            "name": "Iron Sword",
            "type": "weapon"
        },
        "success_rate": 0.8
    },
    "health_potion_craft": {
        "name": "Health Potion",
        "profession": "alchemist",
        "level_required": 1,
        "materials": {
            "healing_herb": 2
        },
        "result": {
            "name": "Health Potion",
            "type": "consumable"
        },
        "success_rate": 0.9
    }
}

# Factions
FACTIONS = {
    "guardians": {
        "name": "Order of Guardians",
        "description": "Protectors of peace and justice",
        "alignment": "good"
    },
    "shadows": {
        "name": "Shadow Brotherhood",
        "description": "Masters of stealth and cunning",
        "alignment": "neutral"
    },
    "chaos": {
        "name": "Chaos Legion",
        "description": "Embracers of destruction and change",
        "alignment": "evil"
    }
}

# Quest Types
QUEST_TYPES = {
    "kill": {
        "name": "Elimination",
        "description": "Defeat specific monsters"
    },
    "collect": {
        "name": "Collection",
        "description": "Gather specific items"
    },
    "explore": {
        "name": "Exploration",
        "description": "Visit specific locations"
    },
    "craft": {
        "name": "Crafting",
        "description": "Create specific items"
    }
}

# Legacy Modifiers
LEGACY_MODIFIERS = {
    "descendant_of_heroes": {
        "name": "Descendant of Heroes",
        "description": "Your noble bloodline grants +10% XP gain",
        "effect": "xp_boost_10"
    },
    "blessed_by_kwami": {
        "name": "Blessed by Kwami",
        "description": "Divine favor grants +5% to all stats",
        "effect": "stat_boost_5"
    },
    "master_of_cheese": {
        "name": "Master of Cheese",
        "description": "Plagg's favorite grants +20% luck",
        "effect": "luck_boost_20"
    }
}

# Mini-Games
MINI_GAMES = {
    "cheese_fishing": {
        "name": "Cheese Pond Fishing",
        "cost": 100,
        "description": "Fish in magical cheese ponds for rare aquatic pets"
    },
    "plagg_trivia": {
        "name": "Plagg's Cheese Trivia",
        "cost": 50,
        "description": "Test your knowledge of cheese and Miraculous lore"
    }
}

# Luck Levels
LUCK_LEVELS = {
    0: {"name": "Cursed", "emoji": "💀", "multiplier": 0.5},
    100: {"name": "Unlucky", "emoji": "😞", "multiplier": 0.8},
    500: {"name": "Normal", "emoji": "😐", "multiplier": 1.0},
    1000: {"name": "Lucky", "emoji": "🍀", "multiplier": 1.2},
    2000: {"name": "Blessed", "emoji": "✨", "multiplier": 1.5},
    5000: {"name": "Divine", "emoji": "🌟", "multiplier": 2.0}
}

def get_all_shop_items():
    """Get all shop items consolidated."""
    return SHOP_ITEMS

# Daily Rewards
DAILY_REWARDS = {
    'base': 100,
    'level_multiplier': 10,
    'streak_bonus': 25,
    'max_streak': 7
}

# Status Effects
STATUS_EFFECTS = {
    'blessed': {'duration': 1800, 'effects': {'luck_bonus': 100, 'xp_bonus': 1.2}},
    'cursed': {'duration': 1800, 'effects': {'luck_penalty': -50, 'damage_penalty': 0.8}},
    'cheese_power': {'duration': 600, 'effects': {'attack_bonus': 1.3, 'cheese_immunity': True}},
    'kwami_protection': {'duration': 900, 'effects': {'defense_bonus': 1.5, 'magic_resistance': 0.5}}
}

# World Locations with cheese theme
WORLD_LOCATIONS = {
    'paris_streets': {
        'name': 'Streets of Paris',
        'description': 'The familiar streets where miraculous holders patrol',
        'level_range': (1, 10),
        'monsters': ['akuma_victim', 'sentimonster'],
        'resources': ['city_materials', 'tourist_coins']
    },
    'cheese_dimension': {
        'name': 'Plagg\'s Cheese Dimension',
        'description': 'A realm made entirely of different cheeses',
        'level_range': (15, 30),
        'monsters': ['cheese_golem', 'cheddar_spirit'],
        'resources': ['aged_cheese', 'mystical_dairy']
    },
    'kwami_realm': {
        'name': 'The Kwami Realm',
        'description': 'The mystical home dimension of all kwamis',
        'level_range': (25, 50),
        'monsters': ['rogue_kwami', 'guardian_spirit'],
        'resources': ['kwami_essence', 'miraculous_energy']
    }
}