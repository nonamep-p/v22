import discord
from replit import db
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Bot configuration
COLORS = {
    'primary': 0x3498db,
    'secondary': 0x2ecc71,
    'success': 0x27ae60,
    'warning': 0xf39c12,
    'error': 0xe74c3c,
    'info': 0x3498db,
    'dark': 0x2c3e50,
    'legendary': 0xff6b35,
    'rarity_common': 0x95a5a6,
    'rarity_uncommon': 0x2ecc71,
    'rarity_rare': 0x3498db,
    'rarity_epic': 0x9b59b6,
    'rarity_legendary': 0xff6b35,
    'rarity_mythical': 0xe74c3c,
    'rarity_divine': 0xf1c40f,
    'rarity_cosmic': 0xe91e63
}

EMOJIS = {
    'rpg': '🎮',
    'economy': '💰',
    'moderation': '🔨',
    'admin': '👑',
    'ai': '🧀',
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'loading': '⏳',
    'profile': '👤',
    'inventory': '🎒',
    'skills': '🎯',
    'level': '📊',
    'xp': '⭐',
    'hp': '❤️',
    'attack': '⚔️',
    'defense': '🛡️',
    'coins': '💰',
    'luck': '🍀'
}

def get_server_config(guild_id: int) -> Dict[str, Any]:
    """Get server configuration from database."""
    try:
        config_key = f"server_config_{guild_id}"
        config = db.get(config_key, {})
        
        # Ensure default values exist
        default_config = {
            'prefix': '$',
            'currency_name': 'coins',
            'enabled_modules': {
                'rpg': True,
                'economy': True,
                'moderation': True,
                'ai_chatbot': True,
                'admin': True
            },
            'ai_channels': [],
            'mod_log_channel': None,
            'auto_moderation': {
                'enabled': True,
                'spam_detection': True,
                'inappropriate_content': True,
                'max_warnings': 3
            }
        }
        
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
                
        return config
    except Exception as e:
        logger.error(f"Error getting server config for {guild_id}: {e}")
        return {}

def update_server_config(guild_id: int, config: Dict[str, Any]) -> bool:
    """Update server configuration in database."""
    try:
        config_key = f"server_config_{guild_id}"
        db[config_key] = config
        return True
    except Exception as e:
        logger.error(f"Error updating server config for {guild_id}: {e}")
        return False

def is_module_enabled(module_name: str, guild_id: int) -> bool:
    """Check if a module is enabled for a guild."""
    try:
        config = get_server_config(guild_id)
        return config.get('enabled_modules', {}).get(module_name, True)
    except Exception as e:
        logger.error(f"Error checking module status: {e}")
        return True  # Default to enabled

def user_has_permission(user: discord.Member, permission_level: str) -> bool:
    """Check if user has required permission level."""
    if not user.guild:
        return False
        
    # Owner always has all permissions
    if user.id == user.guild.owner_id:
        return True
        
    # Check Discord permissions
    if permission_level == 'admin':
        return user.guild_permissions.administrator
    elif permission_level == 'moderator':
        return (user.guild_permissions.kick_members or 
                user.guild_permissions.ban_members or 
                user.guild_permissions.manage_messages or
                user.guild_permissions.administrator)
    elif permission_level == 'manage_channels':
        return user.guild_permissions.manage_channels
    elif permission_level == 'manage_roles':
        return user.guild_permissions.manage_roles
        
    return False

def get_ai_api_key() -> Optional[str]:
    """Get AI API key from environment."""
    return os.getenv('GEMINI_API_KEY')

def get_discord_token() -> Optional[str]:
    """Get Discord bot token from environment."""
    return os.getenv('DISCORD_TOKEN')

# Default server settings
DEFAULT_SERVER_CONFIG = {
    'prefix': '$',
    'currency_name': 'coins',
    'enabled_modules': {
        'rpg': True,
        'economy': True,
        'moderation': True,
        'ai_chatbot': True,
        'admin': True
    },
    'ai_channels': [],
    'mod_log_channel': None,
    'auto_moderation': {
        'enabled': True,
        'spam_detection': True,
        'inappropriate_content': True,
        'max_warnings': 3
    }
}
