import os
import json
from typing import Dict, Any, Optional
from replit import db
import logging

logger = logging.getLogger(__name__)

# Color constants
COLORS = {
    'primary': 0x3498db,
    'secondary': 0x2ecc71,
    'success': 0x27ae60,
    'warning': 0xf39c12,
    'error': 0xe74c3c,
    'info': 0x9b59b6,
    'dark': 0x2c3e50,
    'light': 0xecf0f1
}

# Emoji constants
EMOJIS = {
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'loading': '⏳',
    'coins': '💰',
    'xp': '⭐',
    'level': '🎯',
    'hp': '❤️',
    'attack': '⚔️',
    'defense': '🛡️',
    'inventory': '🎒',
    'shop': '🏪',
    'work': '💼',
    'daily': '🎁',
    'adventure': '🗺️',
    'dungeon': '🏰',
    'battle': '⚔️',
    'profile': '👤',
    'skills': '🎯',
    'ai': '🤖',
    'admin': '👑',
    'moderation': '🔨',
    'rpg': '🎮',
    'economy': '💰'
}

# Default server configuration
DEFAULT_SERVER_CONFIG = {
    'enabled_modules': {
        'rpg_games': True,
        'economy': True,
        'ai_chatbot': True,
        'moderation': True,
        'admin': True
    },
    'allowed_channels': [],  # Empty means all channels allowed
    'ai_enabled_channels': [],  # Empty means all channels allowed
    'ai_custom_prompt': '',
    'auto_moderation': {
        'enabled': False,
        'spam_detection': True,
        'inappropriate_content': True,
        'max_warnings': 3
    },
    'welcome_message': {
        'enabled': False,
        'channel_id': None,
        'message': 'Welcome to the server!'
    },
    'level_roles': {},  # level -> role_id mapping
    'currency_name': 'coins',
    'prefix': '$'
}

def get_server_config(guild_id: int) -> Dict[str, Any]:
    """Get server configuration."""
    try:
        config_key = f"server_config_{guild_id}"
        config = db.get(config_key, DEFAULT_SERVER_CONFIG.copy())
        
        # Ensure all default keys exist
        for key, value in DEFAULT_SERVER_CONFIG.items():
            if key not in config:
                config[key] = value
        
        return config
    except Exception as e:
        logger.error(f"Error getting server config for {guild_id}: {e}")
        return DEFAULT_SERVER_CONFIG.copy()

def update_server_config(guild_id: int, config: Dict[str, Any]) -> bool:
    """Update server configuration."""
    try:
        config_key = f"server_config_{guild_id}"
        db[config_key] = config
        logger.info(f"Updated server config for {guild_id}")
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
        logger.error(f"Error checking module {module_name} for {guild_id}: {e}")
        return True

def is_channel_allowed(channel_id: int, guild_id: int) -> bool:
    """Check if a channel is allowed for bot commands."""
    try:
        config = get_server_config(guild_id)
        allowed_channels = config.get('allowed_channels', [])
        
        # If no channels specified, all are allowed
        if not allowed_channels:
            return True
        
        return channel_id in allowed_channels
    except Exception as e:
        logger.error(f"Error checking channel {channel_id} for {guild_id}: {e}")
        return True

def is_ai_enabled_in_channel(channel_id: int, guild_id: int) -> bool:
    """Check if AI is enabled in a specific channel."""
    try:
        config = get_server_config(guild_id)
        ai_channels = config.get('ai_enabled_channels', [])
        
        # If no channels specified, all are allowed
        if not ai_channels:
            return True
        
        return channel_id in ai_channels
    except Exception as e:
        logger.error(f"Error checking AI channel {channel_id} for {guild_id}: {e}")
        return True

def user_has_permission(member, permission_level: str) -> bool:
    """Check if user has required permission level."""
    try:
        if permission_level == 'admin':
            return (member.guild_permissions.administrator or 
                   member.guild_permissions.manage_guild or
                   member.id == member.guild.owner_id)
        elif permission_level == 'moderator':
            return (member.guild_permissions.manage_messages or
                   member.guild_permissions.kick_members or
                   member.guild_permissions.ban_members or
                   user_has_permission(member, 'admin'))
        elif permission_level == 'helper':
            return (member.guild_permissions.manage_messages or
                   user_has_permission(member, 'moderator'))
        else:
            return True
    except Exception as e:
        logger.error(f"Error checking permissions for {member}: {e}")
        return False

# API Configuration
API_CONFIG = {
    'gemini_api_key': os.getenv('GEMINI_API_KEY', ''),
    'rate_limit_requests': 100,
    'rate_limit_window': 60,
    'max_retries': 3,
    'timeout': 30
}

# Database Configuration
DATABASE_CONFIG = {
    'max_connections': 10,
    'connection_timeout': 30,
    'query_timeout': 10,
    'retry_attempts': 3
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'cache_size': 1000,
    'cache_ttl': 300,  # 5 minutes
    'max_memory_usage': 512,  # MB
    'cleanup_interval': 3600  # 1 hour
}
