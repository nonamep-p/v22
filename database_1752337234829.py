import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from replit import db

logger = logging.getLogger(__name__)

# Database initialization
def init_database():
    """Initialize database with default structures."""
    try:
        # Create default structures if they don't exist
        if 'users' not in db:
            db['users'] = {}
        if 'guilds' not in db:
            db['guilds'] = {}
        if 'global_stats' not in db:
            db['global_stats'] = {
                'total_users': 0,
                'total_commands': 0,
                'total_guilds': 0,
                'created_at': datetime.now().isoformat()
            }
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

# User data management
def ensure_user_exists(user_id: str) -> bool:
    """Ensure user exists in database."""
    try:
        users = db.get('users', {})
        if user_id not in users:
            users[user_id] = create_user_profile(user_id)
            db['users'] = users
            logger.info(f"Created user profile for {user_id}")
            return True
        return True
    except Exception as e:
        logger.error(f"Error ensuring user exists {user_id}: {e}")
        return False

def create_user_profile(user_id: str) -> Dict[str, Any]:
    """Create a new user profile."""
    return {
        'user_id': user_id,
        'created_at': datetime.now().isoformat(),
        'last_active': datetime.now().isoformat(),
        'rpg_data': {
            'level': 1,
            'xp': 0,
            'max_xp': 100,
            'hp': 100,
            'max_hp': 100,
            'attack': 10,
            'defense': 5,
            'coins': 100,
            'inventory': [],
            'equipped': {
                'weapon': None,
                'armor': None,
                'accessory': None
            },
            'stats': {
                'total_xp_earned': 0,
                'total_coins_earned': 0,
                'battles_won': 0,
                'battles_lost': 0,
                'adventures_completed': 0,
                'dungeons_completed': 0
            },
            'achievements': [],
            'guild_id': None,
            'guild_rank': 'member',
            'last_work': None,
            'last_daily': None,
            'last_adventure': None,
            'last_dungeon': None,
            'work_count': 0,
            'adventure_count': 0,
            'dungeon_count': 0
        },
        'settings': {
            'notifications': True,
            'public_profile': True,
            'auto_equip': True
        }
    }

def get_user_data(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user data from database."""
    try:
        users = db.get('users', {})
        user_data = users.get(user_id)
        if user_data:
            # Update last active
            user_data['last_active'] = datetime.now().isoformat()
            users[user_id] = user_data
            db['users'] = users
        return user_data
    except Exception as e:
        logger.error(f"Error getting user data for {user_id}: {e}")
        return None

def update_user_data(user_id: str, data: Dict[str, Any]) -> bool:
    """Update user data in database."""
    try:
        users = db.get('users', {})
        data['last_active'] = datetime.now().isoformat()
        users[user_id] = data
        db['users'] = users
        return True
    except Exception as e:
        logger.error(f"Error updating user data for {user_id}: {e}")
        return False

def get_user_rpg_data(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user RPG data specifically."""
    try:
        user_data = get_user_data(user_id)
        return user_data.get('rpg_data') if user_data else None
    except Exception as e:
        logger.error(f"Error getting RPG data for {user_id}: {e}")
        return None

def update_user_rpg_data(user_id: str, rpg_data: Dict[str, Any]) -> bool:
    """Update user RPG data specifically."""
    try:
        users = db.get('users', {})
        if user_id in users:
            users[user_id]['rpg_data'] = rpg_data
            users[user_id]['last_active'] = datetime.now().isoformat()
            db['users'] = users
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating RPG data for {user_id}: {e}")
        return False

# Guild data management
def get_guild_data(guild_id: str) -> Optional[Dict[str, Any]]:
    """Get guild data from database."""
    try:
        guilds = db.get('guilds', {})
        return guilds.get(guild_id)
    except Exception as e:
        logger.error(f"Error getting guild data for {guild_id}: {e}")
        return None

def update_guild_data(guild_id: str, data: Dict[str, Any]) -> bool:
    """Update guild data in database."""
    try:
        guilds = db.get('guilds', {})
        data['last_updated'] = datetime.now().isoformat()
        guilds[guild_id] = data
        db['guilds'] = guilds
        return True
    except Exception as e:
        logger.error(f"Error updating guild data for {guild_id}: {e}")
        return False

def create_guild_profile(guild_id: str, name: str) -> Dict[str, Any]:
    """Create a new guild profile."""
    return {
        'guild_id': guild_id,
        'name': name,
        'created_at': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat(),
        'members': [],
        'leader': None,
        'level': 1,
        'xp': 0,
        'treasury': 0,
        'perks': [],
        'settings': {
            'public': True,
            'auto_accept': False,
            'min_level': 1
        },
        'stats': {
            'total_xp': 0,
            'total_coins': 0,
            'battles_won': 0,
            'raids_completed': 0
        }
    }

# Leaderboard functions
def get_leaderboard(category: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get leaderboard for a specific category."""
    try:
        users = db.get('users', {})
        leaderboard = []
        
        for user_id, user_data in users.items():
            rpg_data = user_data.get('rpg_data', {})
            
            if category == 'level':
                value = rpg_data.get('level', 1)
            elif category == 'coins':
                value = rpg_data.get('coins', 0)
            elif category == 'xp':
                value = rpg_data.get('stats', {}).get('total_xp_earned', 0)
            elif category == 'battles':
                value = rpg_data.get('stats', {}).get('battles_won', 0)
            else:
                continue
                
            leaderboard.append({
                'user_id': user_id,
                'value': value,
                'level': rpg_data.get('level', 1)
            })
        
        # Sort by value (descending)
        leaderboard.sort(key=lambda x: x['value'], reverse=True)
        return leaderboard[:limit]
    except Exception as e:
        logger.error(f"Error getting leaderboard for {category}: {e}")
        return []

# Statistics functions
def update_global_stats(stat_name: str, increment: int = 1) -> bool:
    """Update global statistics."""
    try:
        stats = db.get('global_stats', {})
        stats[stat_name] = stats.get(stat_name, 0) + increment
        stats['last_updated'] = datetime.now().isoformat()
        db['global_stats'] = stats
        return True
    except Exception as e:
        logger.error(f"Error updating global stats: {e}")
        return False

def get_global_stats() -> Dict[str, Any]:
    """Get global statistics."""
    try:
        return db.get('global_stats', {})
    except Exception as e:
        logger.error(f"Error getting global stats: {e}")
        return {}

# Utility functions
def backup_database() -> bool:
    """Create a backup of the database."""
    try:
        backup_data = {
            'users': dict(db.get('users', {})),
            'guilds': dict(db.get('guilds', {})),
            'global_stats': dict(db.get('global_stats', {})),
            'backup_timestamp': datetime.now().isoformat()
        }
        
        # Store backup with timestamp
        backup_key = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        db[backup_key] = backup_data
        logger.info(f"Database backup created: {backup_key}")
        return True
    except Exception as e:
        logger.error(f"Error creating database backup: {e}")
        return False

def cleanup_old_data(days: int = 30) -> bool:
    """Clean up old inactive user data."""
    try:
        users = db.get('users', {})
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        inactive_users = []
        for user_id, user_data in users.items():
            last_active = user_data.get('last_active')
            if last_active:
                try:
                    last_active_dt = datetime.fromisoformat(last_active)
                    if last_active_dt.timestamp() < cutoff_date:
                        inactive_users.append(user_id)
                except:
                    pass
        
        # Remove inactive users
        for user_id in inactive_users:
            del users[user_id]
        
        db['users'] = users
        logger.info(f"Cleaned up {len(inactive_users)} inactive users")
        return True
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        return False
