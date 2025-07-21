# Epic RPG Helper - Discord Bot

## Overview

This is a comprehensive Discord bot built with Python using discord.py that combines Epic RPG gameplay, economy systems, moderation tools, and AI-powered conversation features. The bot uses a modular cog-based architecture and is designed to run on Replit's hosting platform with persistent data storage.

**Current Status:** Fully operational with all modules loaded and running successfully. Bot is connected to Discord and ready for use.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Framework
- **Language**: Python 3.11+
- **Bot Framework**: discord.py with custom command prefix system
- **Hosting Platform**: Replit with Flask-based keep-alive mechanism
- **Database**: Replit DB (key-value store) for persistent data storage
- **Architecture Pattern**: Modular cog-based design for feature separation
- **AI Integration**: Google Gemini API for conversational AI capabilities

### Bot Configuration
- **Command Prefix**: Configurable per server (default: `$`)
- **Intents**: Full permissions including message content, members, guilds
- **Persistence**: Persistent UI views that survive bot restarts
- **Logging**: Comprehensive logging system with file and console output

## Key Components

### 1. Main Bot (`main.py`)
- **Purpose**: Core bot initialization and event handling
- **Features**: 
  - Custom bot class with dynamic prefix system
  - Automatic cog loading and management
  - Database initialization on startup
  - Persistent view registration for UI components
- **Event Handlers**: on_ready, on_guild_join, on_member_join

### 2. Keep-Alive System (`web_server.py`)
- **Purpose**: Maintains bot uptime on Replit platform
- **Implementation**: Flask web server running in separate thread
- **Endpoints**: 
  - `/` - Basic status with HTML interface
  - `/health` - System health monitoring
  - `/status` - Detailed bot statistics
- **Features**: System resource monitoring, uptime tracking

### 3. Configuration System (`config.py`)
- **Purpose**: Centralized configuration management
- **Features**:
  - Server-specific settings stored in database
  - Module enable/disable functionality
  - Color scheme and emoji constants
  - Permission checking utilities
- **Settings**: Prefixes, enabled modules, AI channels, custom prompts

### 4. Database Layer (`utils/database.py`)
- **Purpose**: Abstraction layer for Replit DB operations
- **Features**:
  - User profile management with automatic creation
  - Guild-specific data storage
  - Global statistics tracking
  - Backup and cleanup utilities
- **Data Structure**: JSON-based nested dictionaries

### 5. Helper Utilities (`utils/helpers.py`)
- **Purpose**: Common utility functions across the bot
- **Features**:
  - Embed creation with consistent styling
  - Number formatting and progress bars
  - Level calculation and XP management
  - Time formatting and duration calculations

### 6. Advanced RNG System (`utils/rng_system.py`)
- **Purpose**: Sophisticated random number generation with luck mechanics
- **Features**:
  - Dynamic luck multipliers based on hidden conditions
  - Rare event detection with extremely low probabilities
  - Time-based conditions (midnight blessing, prime time hours)
  - User-specific luck patterns and streaks
  - Celestial events and permanent stat boosts

## Key Components

### RPG Games Module (`cogs/rpg_games.py`)
- **Character System**: Level-based progression with XP, HP, attack, defense
- **Adventure System**: Random encounters with location-based outcomes
- **Dungeon System**: Multi-floor exploration with increasing difficulty
- **Interactive UI**: Button-based interfaces for all RPG actions
- **Battle System**: Turn-based combat with equipment effects
- **Guild System**: Player organizations with shared benefits

### Economy Module (`cogs/economy.py`)
- **Work System**: Time-gated job system with level-based rewards
- **Daily Rewards**: Progressive daily bonuses with streak mechanics
- **Shop System**: Buy/sell items with dynamic pricing
- **Inventory Management**: Item storage with rarity system
- **Auction House**: Player-to-player trading system

### Moderation Module (`cogs/moderation.py`)
- **User Management**: Kick, ban, mute with proper permission checks
- **Message Control**: Bulk delete, slowmode, auto-moderation
- **Warning System**: Progressive discipline tracking
- **Role Hierarchy**: Respects Discord's role-based permissions
- **Auto-Moderation**: Spam detection and content filtering

### AI Chatbot Module (`cogs/ai_chatbot.py`)
- **Conversation AI**: Google Gemini integration for natural responses
- **Context Management**: Maintains conversation history per channel
- **Custom Prompts**: Server-specific AI personality customization
- **Channel Control**: Enable/disable AI responses in specific channels
- **Smart Triggers**: Responds to mentions, replies, and keywords

### Admin Module (`cogs/admin.py`)
- **System Monitoring**: Bot performance statistics and health checks
- **Module Management**: Enable/disable bot features per server
- **Database Tools**: Backup, cleanup, and maintenance utilities
- **Configuration UI**: Interactive server settings management
- **Cog Control**: Runtime reloading of bot modules

### Interactive Help System (`cogs/help.py`)
- **Paginated Interface**: Category-based command organization
- **Interactive Navigation**: Dropdown menus and button controls
- **Persistent Views**: Survives bot restarts with proper registration
- **Dynamic Content**: Commands organized by enabled modules
- **User-Friendly**: Clear descriptions and usage examples

## Data Flow

### User Interaction Flow
1. **Command Reception**: Discord message triggers command processing
2. **Permission Check**: Verify user permissions and module availability
3. **Data Retrieval**: Fetch user/guild data from Replit DB
4. **Business Logic**: Process command with appropriate cog
5. **Database Update**: Save changes to persistent storage
6. **Response Generation**: Create embed with interactive components
7. **UI Interaction**: Handle button clicks and dropdown selections

### Data Storage Pattern
- **User Data**: Nested structure with RPG, economy, and system data
- **Guild Data**: Server-specific configurations and statistics
- **Global Data**: Bot-wide statistics and administrative information
- **Caching**: In-memory caching for frequently accessed data

## External Dependencies

### Required Packages
- **discord.py**: Core Discord bot functionality
- **google-generativeai**: Google Gemini API integration
- **flask**: Web server for keep-alive system
- **psutil**: System monitoring and resource tracking
- **replit**: Database integration for persistent storage

### API Integrations
- **Discord API**: Full bot functionality through discord.py
- **Google Gemini API**: AI conversation capabilities using gemini-1.5-flash model
- **Replit DB**: Key-value storage for all persistent data

### Environment Variables
- **DISCORD_TOKEN**: Bot authentication token
- **GEMINI_API_KEY**: Google AI API key for chatbot functionality

## Deployment Strategy

### Replit Configuration
- **Runtime**: Python 3.11+ with automatic dependency management
- **Database**: Built-in Replit DB with automatic backups
- **Networking**: Flask web server on port 5000 for keep-alive
- **Process Management**: Main bot process with web server thread

### Scalability Considerations
- **Modular Design**: Easy to add/remove features via cog system
- **Database Optimization**: Efficient data structures and cleanup routines
- **Memory Management**: Proper cleanup of temporary data and caches
- **Error Handling**: Comprehensive logging and graceful failure recovery

### Monitoring and Maintenance
- **Health Checks**: Web endpoints for uptime monitoring
- **Performance Metrics**: System resource tracking and reporting
- **Database Maintenance**: Automated cleanup and backup systems
- **Error Logging**: Detailed logs for debugging and issue resolution