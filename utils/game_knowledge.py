
"""
Game Knowledge Base for AI Assistant Integration
Provides comprehensive game information for AI responses and player assistance.
"""

import json
from typing import Dict, List, Any, Optional
from rpg_data.game_data import (
    CHARACTER_CLASSES, ITEMS, TACTICAL_MONSTERS, KWAMI_ARTIFACT_SETS,
    TECHNIQUES, DAMAGE_TYPES, ULTIMATE_ABILITIES, XP_FOR_NEXT_LEVEL
)

class GameKnowledgeBase:
    """Comprehensive game knowledge for AI assistance."""
    
    def __init__(self):
        self.knowledge = self._build_knowledge_base()
    
    def _build_knowledge_base(self) -> Dict[str, Any]:
        """Build comprehensive game knowledge dictionary."""
        return {
            "game_overview": {
                "name": "Project: Blood & Cheese",
                "type": "Tactical Turn-Based RPG",
                "inspiration": "Honkai: Star Rail",
                "theme": "Miraculous: Tales of Ladybug & Cat Noir",
                "core_mechanics": [
                    "Turn-based tactical combat",
                    "Skill Point resource management", 
                    "Ultimate Energy system",
                    "Weakness Break mechanics",
                    "Character progression",
                    "Equipment and artifact systems",
                    "PvP arena combat",
                    "Dungeon exploration"
                ]
            },
            
            "combat_system": {
                "turn_structure": "Initiative-based turns determined by Speed stat",
                "skill_points": {
                    "description": "Shared team resource for using skills",
                    "starting_amount": 3,
                    "maximum": 5,
                    "generation": "Basic Attacks generate 1 SP",
                    "consumption": "Skills consume 1 SP",
                    "strategy": "Balance generation and consumption for optimal play"
                },
                "ultimate_energy": {
                    "description": "Individual character resource for ultimate abilities",
                    "range": "0-100 energy",
                    "generation": "Gained from actions, taking damage, defeating enemies",
                    "usage": "100 energy required for ultimate ability",
                    "special": "Can be used instantly, even during enemy turns"
                },
                "weakness_break": {
                    "description": "Core tactical mechanic for enemy control",
                    "toughness_bar": "White bar above enemy HP that must be depleted",
                    "weakness_types": list(DAMAGE_TYPES.keys()),
                    "break_effects": [
                        "Enemy turn delay/stun",
                        "Bonus damage on break",
                        "Increased damage taken while broken",
                        "Elemental status effects"
                    ]
                },
                "damage_types": DAMAGE_TYPES
            },
            
            "character_classes": self._format_classes(),
            "progression_system": self._format_progression(),
            "equipment_system": self._format_equipment(),
            "artifact_system": self._format_artifacts(),
            "monsters_and_enemies": self._format_monsters(),
            "pvp_system": self._format_pvp(),
            "commands_and_usage": self._format_commands(),
            "tips_and_strategies": self._format_strategies(),
            "common_questions": self._format_faq()
        }
    
    def _format_classes(self) -> Dict[str, Any]:
        """Format character class information."""
        formatted_classes = {}
        for class_key, class_data in CHARACTER_CLASSES.items():
            formatted_classes[class_key] = {
                "name": class_data["name"],
                "emoji": class_data["emoji"],
                "role": class_data["role"],
                "description": class_data["description"],
                "playstyle": self._get_class_playstyle(class_key),
                "strengths": self._get_class_strengths(class_key),
                "weaknesses": self._get_class_weaknesses(class_key),
                "recommended_for": self._get_class_recommendations(class_key),
                "base_stats": class_data["base_stats"],
                "passive_ability": class_data["passive"],
                "ultimate_ability": class_data["ultimate"],
                "starting_skills": class_data["starting_skills"]
            }
        return formatted_classes
    
    def _get_class_playstyle(self, class_key: str) -> str:
        """Get detailed playstyle description for a class."""
        playstyles = {
            "warrior": "Frontline tank that absorbs damage while dealing consistent physical damage. Uses SP efficiently with basic attacks while building ultimate energy.",
            "mage": "Burst damage dealer focusing on elemental skills. Requires careful SP management but deals devastating area damage.",
            "rogue": "High-damage assassin with critical strike focus. Best at eliminating priority targets quickly.",
            "archer": "Ranged precision attacker with consistent damage output. Excels at exploiting enemy weaknesses from safety.",
            "healer": "Support specialist keeping the team alive. Essential for longer battles and team-based content.",
            "battlemage": "Versatile hybrid combining physical and magical damage. Adaptable to various combat situations.",
            "chrono_knight": "Advanced time manipulator with complex mechanics. Requires mastery but offers unique tactical options."
        }
        return playstyles.get(class_key, "Unique playstyle with specialized mechanics.")
    
    def _get_class_strengths(self, class_key: str) -> List[str]:
        """Get class strengths."""
        strengths = {
            "warrior": ["High survivability", "Reliable damage", "SP efficient", "Great for beginners"],
            "mage": ["Huge burst damage", "Area attacks", "Elemental variety", "Weakness exploitation"],
            "rogue": ["Critical hit specialist", "High single-target damage", "Stealth abilities", "Quick eliminations"],
            "archer": ["Ranged safety", "Consistent damage", "Precision attacks", "Multi-target abilities"],
            "healer": ["Team support", "Healing abilities", "Buff/debuff management", "Team sustainability"],
            "battlemage": ["Versatile damage", "Weapon enchantments", "Balanced approach", "Adaptable builds"],
            "chrono_knight": ["Time manipulation", "Extra turns", "Complex combos", "Unique mechanics"]
        }
        return strengths.get(class_key, ["Specialized abilities", "Unique mechanics"])
    
    def _get_class_weaknesses(self, class_key: str) -> List[str]:
        """Get class weaknesses."""
        weaknesses = {
            "warrior": ["Limited ranged options", "Vulnerable to magic", "Slower movement"],
            "mage": ["Low physical defense", "SP dependent", "Vulnerable in melee"],
            "rogue": ["Lower survivability", "Positioning dependent", "Resource management"],
            "archer": ["Vulnerable in melee", "Limited area damage", "Ammunition/resource dependent"],
            "healer": ["Low personal damage", "Support dependent", "Target priority for enemies"],
            "battlemage": ["Master of none", "Complex resource management", "Requires game knowledge"],
            "chrono_knight": ["Complex mechanics", "Requires planning", "Hidden class (must be unlocked)"]
        }
        return weaknesses.get(class_key, ["Specialized focus", "Situational utility"])
    
    def _get_class_recommendations(self, class_key: str) -> str:
        """Get recommendations for who should play this class."""
        recommendations = {
            "warrior": "New players, those who like straightforward gameplay, tank role lovers",
            "mage": "Players who enjoy burst damage, elemental strategy, and area attacks",
            "rogue": "Assassin playstyle lovers, critical hit enthusiasts, precision players",
            "archer": "Ranged combat fans, precision damage dealers, tactical players",
            "healer": "Support role players, team-focused individuals, strategic thinkers",
            "battlemage": "Versatile players, those who want hybrid playstyles, advanced users",
            "chrono_knight": "Experienced players, complex mechanic enthusiasts, time manipulation fans"
        }
        return recommendations.get(class_key, "Players who enjoy unique and specialized mechanics")
    
    def _format_progression(self) -> Dict[str, Any]:
        """Format progression system information."""
        return {
            "leveling": {
                "xp_sources": ["Combat victories", "Quest completion", "Achievement unlocks", "Daily activities"],
                "xp_formula": "100 * (1.5 ^ (level - 1)) XP needed for next level",
                "stat_points": "2 points per level to allocate",
                "level_benefits": [
                    "Increased base stats",
                    "New abilities unlock",
                    "Equipment access",
                    "Content unlocks"
                ]
            },
            "stat_allocation": {
                "strength": "Increases physical damage and attack power",
                "dexterity": "Improves speed, critical chance, and dodge chance",
                "constitution": "Raises HP, defense, and physical resistance",
                "intelligence": "Boosts magical damage and mana pool",
                "wisdom": "Enhances mana regeneration and magical resistance",
                "charisma": "Affects luck, social interactions, and special events"
            },
            "miraculous_paths": {
                "unlock_level": 20,
                "permanent_choice": True,
                "paths": {
                    "destruction": "Massive damage focus with follow-up attacks",
                    "preservation": "Defensive mastery with damage reduction",
                    "abundance": "Healing and support specialization", 
                    "hunt": "Precision and execution bonuses"
                }
            }
        }
    
    def _format_equipment(self) -> Dict[str, Any]:
        """Format equipment system information."""
        equipment_categories = {}
        for item_key, item_data in ITEMS.items():
            category = item_data.get("type", "misc")
            if category not in equipment_categories:
                equipment_categories[category] = []
            equipment_categories[category].append({
                "name": item_data["name"],
                "rarity": item_data["rarity"],
                "description": item_data["description"],
                "key": item_key
            })
        
        return {
            "categories": equipment_categories,
            "rarity_system": {
                "common": "Basic starter equipment",
                "uncommon": "Improved stats and minor effects",
                "rare": "Significant upgrades with special properties",
                "epic": "Powerful equipment with major bonuses",
                "legendary": "Exceptional gear with unique abilities",
                "mythic": "Incredible power and game-changing effects",
                "divine": "Godlike equipment (admin/special)",
                "cosmic": "Reality-bending power (owner exclusive)"
            },
            "equipment_slots": ["weapon", "armor", "accessory", "artifact"],
            "upgrade_paths": ["Enhancement", "Ascension", "Set collection"]
        }
    
    def _format_artifacts(self) -> Dict[str, Any]:
        """Format artifact system information."""
        return {
            "overview": "Kwami Artifacts are powerful set equipment with unique bonuses",
            "slots": ["head", "hands", "body", "feet"],
            "sets": {set_key: {
                "name": set_data["name"],
                "kwami": set_data["kwami"],
                "bonuses": set_data["bonuses"]
            } for set_key, set_data in KWAMI_ARTIFACT_SETS.items()},
            "acquisition": {
                "primary_source": "Miraculous Box dungeon",
                "cost": "Miraculous Energy",
                "enemies": ["Artifact Guardian", "Kwami Phantom", "Miraculous Sentinel"],
                "drop_rate": "Guaranteed artifact drops from special enemies"
            },
            "strategy": "Collect 4 pieces of the same set for maximum bonuses"
        }
    
    def _format_monsters(self) -> Dict[str, Any]:
        """Format monster and enemy information."""
        formatted_monsters = {}
        for monster_key, monster_data in TACTICAL_MONSTERS.items():
            formatted_monsters[monster_key] = {
                "name": monster_data["name"],
                "emoji": monster_data["emoji"],
                "level_range": "Based on player level",
                "weakness": monster_data["weakness_type"],
                "strategy": self._get_monster_strategy(monster_key),
                "rewards": {
                    "xp": monster_data["xp_reward"],
                    "gold": monster_data["gold_reward"],
                    "loot": monster_data.get("loot_table", {})
                }
            }
        return formatted_monsters
    
    def _get_monster_strategy(self, monster_key: str) -> str:
        """Get strategy tips for fighting specific monsters."""
        strategies = {
            "goblin": "Basic enemy, good for learning. Weak to physical attacks.",
            "orc": "Tanky enemy, focus on weakness break. Ice attacks are most effective.",
            "ice_elemental": "Fire attacks destroy it quickly. Be careful of its freeze abilities.",
            "dragon": "Boss-level enemy requiring team coordination. Lightning weakness is key.",
            "artifact_guardian": "Defensive enemy found in Miraculous Box. Use chaos-type attacks.",
            "kwami_phantom": "Fast, elusive enemy. Miraculous-type damage is most effective.",
            "miraculous_sentinel": "Powerful boss with high resistances. Focus on corruption damage."
        }
        return strategies.get(monster_key, "Study its weakness and adapt your strategy accordingly.")
    
    def _format_pvp(self) -> Dict[str, Any]:
        """Format PvP system information."""
        return {
            "arena_tiers": {
                "rookie": "0-1200 rating, entry level",
                "veteran": "1200-1800 rating, intermediate",
                "master": "1800-2500 rating, advanced",
                "legendary": "2500+ rating, elite players"
            },
            "combat_style": "Asynchronous - fight AI-controlled versions of player teams",
            "rewards": {
                "arena_tokens": "Special currency for exclusive items",
                "rating_points": "Climb tiers for better rewards",
                "seasonal_rewards": "End-of-season bonuses based on final rank"
            },
            "strategy_tips": [
                "Build balanced teams covering multiple damage types",
                "Consider enemy team composition when selecting your lineup",
                "Focus on weakness exploitation",
                "Manage SP carefully in longer battles"
            ]
        }
    
    def _format_commands(self) -> Dict[str, Any]:
        """Format command usage information."""
        return {
            "essential": {
                "$startrpg": "Create your character - required to start playing",
                "$help": "Interactive help system with tutorials and guides",
                "$profile": "View your character stats and progression",
                "$battle": "Start combat encounter for XP and rewards"
            },
            "combat": {
                "$hunt": "Random encounter available every 30 minutes",
                "$miraculous": "Enter artifact farming dungeon (costs energy)",
                "$skills": "View your combat abilities and descriptions",
                "$techniques": "Pre-combat abilities for tactical advantage"
            },
            "progression": {
                "$allocate": "Spend stat points from leveling up",
                "$path": "Choose Miraculous Path specialization at level 20",
                "$achievements": "Track progress and unlock rewards",
                "$inventory": "Manage items and equipment"
            },
            "social": {
                "$pvp": "Enter ranked PvP matchmaking",
                "$guild": "Guild and faction management",
                "$trade": "Trade items with other players",
                "$challenge": "Direct player challenges"
            }
        }
    
    def _format_strategies(self) -> Dict[str, Any]:
        """Format strategy tips and guides."""
        return {
            "new_player_tips": [
                "Start with Warrior class for easier learning curve",
                "Always allocate stat points when you level up",
                "Focus on your class's primary stats first",
                "Don't hoard Skill Points - use them strategically",
                "Target enemy weaknesses for faster victories",
                "Complete daily quests for consistent progression"
            ],
            "combat_strategies": [
                "Use Basic Attacks to generate SP when you need resources",
                "Save Ultimates for crucial moments or boss fights",
                "Focus fire to break enemy toughness quickly",
                "Position matters - protect your support characters",
                "Learn enemy attack patterns and plan accordingly",
                "Combo abilities for maximum effectiveness"
            ],
            "progression_advice": [
                "Specialize your stat allocation to your class role",
                "Choose your Miraculous Path based on your playstyle",
                "Collect artifact sets for powerful bonuses",
                "Complete achievements for hidden rewards",
                "Don't neglect PvP - it provides unique rewards",
                "Join a guild for social benefits and group content"
            ],
            "advanced_tactics": [
                "Master the timing of Ultimate interrupts",
                "Learn to chain weakness breaks across multiple enemies",
                "Optimize your equipment for specific content types",
                "Understand team synergy for group content",
                "Plan your skill rotation for maximum efficiency",
                "Adapt your strategy based on enemy composition"
            ]
        }
    
    def _format_faq(self) -> Dict[str, Any]:
        """Format frequently asked questions."""
        return {
            "getting_started": {
                "How do I create a character?": "Use the $startrpg command and follow the interactive class selection.",
                "Which class should I choose?": "Warrior is recommended for beginners, but choose based on your preferred playstyle.",
                "How does combat work?": "Turn-based tactical combat using Skill Points and Ultimate Energy systems.",
                "Where do I get better equipment?": "Shop, monster drops, quest rewards, and the Miraculous Box dungeon."
            },
            "combat_questions": {
                "What are Skill Points?": "Shared team resource generated by Basic Attacks and consumed by Skills.",
                "How do I use Ultimate abilities?": "Build 100 Ultimate Energy, then use during combat for powerful effects.",
                "What is Weakness Break?": "Depleting enemy toughness with their weakness element stuns them.",
                "Why can't I use skills?": "You need Skill Points - use Basic Attacks to generate them."
            },
            "progression_questions": {
                "How do I level up?": "Gain XP from battles, quests, and achievements.",
                "How do I allocate stats?": "Use $allocate <stat> <points> command after leveling up.",
                "When can I choose a Path?": "Miraculous Paths unlock at Level 20 and are permanent choices.",
                "How do I get artifacts?": "Enter the Miraculous Box dungeon using $miraculous command."
            },
            "system_questions": {
                "Can I change my class?": "No, class choice is permanent (admin can change in special cases).",
                "Can I reset my stats?": "Stat respec will be available in future updates.",
                "Is there a level cap?": "Current max level is 100 with prestige system planned.",
                "Can I play with friends?": "Yes, through PvP, guilds, and planned group content."
            }
        }
    
    def get_help_for_topic(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get help information for a specific topic."""
        topic_lower = topic.lower()
        
        # Direct topic matches
        if topic_lower in self.knowledge:
            return self.knowledge[topic_lower]
        
        # Search within sections
        for section_name, section_data in self.knowledge.items():
            if isinstance(section_data, dict):
                if topic_lower in section_data:
                    return section_data[topic_lower]
                
                # Search for partial matches
                for key, value in section_data.items():
                    if topic_lower in key.lower():
                        return {key: value}
        
        return None
    
    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant information."""
        query_lower = query.lower()
        results = []
        
        def search_recursive(data, path=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    current_path = f"{path}.{key}" if path else key
                    if query_lower in key.lower():
                        results.append({
                            "path": current_path,
                            "key": key,
                            "content": value,
                            "relevance": "high"
                        })
                    elif isinstance(value, str) and query_lower in value.lower():
                        results.append({
                            "path": current_path,
                            "key": key,
                            "content": value,
                            "relevance": "medium"
                        })
                    search_recursive(value, current_path)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, str) and query_lower in item.lower():
                        results.append({
                            "path": f"{path}[{i}]",
                            "content": item,
                            "relevance": "low"
                        })
        
        search_recursive(self.knowledge)
        return results[:10]  # Limit results

# Global knowledge base instance
game_knowledge = GameKnowledgeBase()
