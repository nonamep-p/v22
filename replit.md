# Epic RPG Helper - Discord Bot

## Overview

This is a comprehensive Discord bot built with Python using discord.py that combines Epic RPG gameplay, economy systems, moderation tools, and AI-powered conversation features. The bot uses a modular cog-based architecture for feature separation and includes persistent UI components for enhanced user interaction.

**Current Status:** Bot code is present but has incomplete module implementations and missing cog registration. The bot structure is sound but requires completion of key components for full functionality.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Framework
- **Language**: Python 3.11+
- **Bot Framework**: discord.py with custom command prefix system and slash command support
- **Hosting Platform**: Replit with Flask-based keep-alive mechanism
- **Database**: Replit DB (key-value store) for persistent data storage
- **Architecture Pattern**: Modular cog-based design for feature separation
- **AI Integration**: Google Gemini API for conversational AI capabilities

### Bot Configuration
- **Command Prefix**: Configurable per server (default: `$`)
- **Intents**: Full permissions including message content, members, guilds, reactions
- **Persistence**: Persistent UI views that survive bot restarts
- **Logging**: Comprehensive logging system with file and console output
- **Error Handling**: Robust error handling with traceback logging

## Key Components

### 1. Main Bot (`main.py`)
- **Purpose**: Core bot initialization and event handling
- **Features**: 
  - Custom EpicRPGBot class with dynamic prefix system
  - Automatic cog loading and management
  - Database initialization on startup
  - Persistent view registration for UI components
  - Comprehensive intents configuration
- **Event Handlers**: on_ready, on_guild_join, on_member_join, on_application_command_error
- **Command Tree**: Slash command synchronization across guilds

### 2. Keep-Alive System (`web_server.py`)
- **Purpose**: Maintains bot uptime on Replit platform
- **Implementation**: Flask web server running in separate thread
- **Endpoints**: 
  - `/` - Basic status with health check
  - `/health` - Detailed system health monitoring
  - `/stats` - Bot performance statistics
- **Features**: System resource monitoring, uptime tracking, bot status updates

### 3. Configuration System (`config.py`)
- **Purpose**: Centralized configuration management
- **Features**:
  - Server-specific configuration storage
  - Module enable/disable functionality
  - Permission system with role-based access
  - Color and emoji constants
  - Default configuration templates
- **Database Integration**: Uses Replit DB for persistent server configs

### 4. Moderation Module (`moderation.py`)
- **Purpose**: Comprehensive moderation tools
- **Features**:
  - Auto-moderation with spam detection
  - Inappropriate content filtering
  - User warning system
  - Timeout and ban management
  - Interactive configuration views
- **Commands**: Kick, ban, timeout, warn, purge, automod settings
- **Auto-Features**: Pattern-based spam detection, excessive caps filtering

### 5. Admin Module (`admin.py`)
- **Purpose**: Server administration and bot management
- **Features**:
  - Interactive configuration interface
  - Module management
  - Server statistics
  - Bot maintenance functions
- **UI Components**: ConfigView, ModuleConfigView, PrefixModal
- **Permissions**: Admin-only access with permission checking

### 6. AI Chatbot Module (`ai_chatbot.py`)
- **Purpose**: AI-powered conversational interface
- **Features**:
  - Google Gemini API integration
  - Conversation history management
  - Context-aware responses
  - Channel-specific AI settings
- **AI Features**: Natural language processing, contextual memory, personality customization

## Data Flow

### User Interaction Flow
1. **Command Processing**: Commands parsed through dynamic prefix system
2. **Permission Checking**: Role-based permission validation
3. **Module Verification**: Check if module is enabled for guild
4. **Database Operations**: User/guild data retrieval and updates
5. **Response Generation**: Embed creation and interaction handling

### Database Structure
- **User Data**: Individual user profiles with RPG stats, economy data
- **Guild Data**: Server-specific configurations and settings
- **Global Stats**: Bot-wide statistics and performance metrics
- **Conversation History**: AI chat context and user interactions

### AI Integration Flow
1. **Message Detection**: Monitor for AI-enabled channels
2. **Context Retrieval**: Load conversation history
3. **API Request**: Send to Google Gemini with context
4. **Response Processing**: Format and deliver AI response
5. **History Update**: Store interaction for future context

## External Dependencies

### Required APIs
- **Discord API**: Core bot functionality (discord.py)
- **Google Gemini API**: AI conversational capabilities
- **Replit DB**: Persistent data storage

### Python Packages
- `discord.py`: Discord bot framework
- `google-generativeai`: Google AI integration
- `flask`: Web server for keep-alive
- `psutil`: System monitoring
- `asyncio`: Asynchronous operation handling

### Environment Variables
- `DISCORD_BOT_TOKEN`: Discord bot authentication
- `GEMINI_API_KEY`: Google AI API access
- Additional configuration through Replit secrets

## Deployment Strategy

### Replit Platform
- **Hosting**: Replit cloud environment
- **Keep-Alive**: Flask web server prevents sleeping
- **Database**: Integrated Replit DB for persistence
- **Secrets**: Environment variables through Replit secrets manager

### Scaling Considerations
- **Cog-based Architecture**: Modular loading for resource optimization
- **Database Optimization**: Efficient key-value operations
- **Memory Management**: Conversation history cleanup
- **Rate Limiting**: Discord API rate limit compliance

### Maintenance Features
- **Health Monitoring**: System resource tracking
- **Error Logging**: Comprehensive error tracking and logging
- **Database Backups**: Periodic data backup functionality
- **Module Hot-Loading**: Dynamic cog loading/unloading

## Current Implementation Status

### Completed Components
- Core bot framework with proper intents
- Web server keep-alive system
- Configuration management system
- Database utility functions
- Helper functions and constants

### Incomplete Components
- Missing cog registration in main.py
- Incomplete admin.py implementation (missing modal classes)
- Moderation module lacks complete slash command implementations
- AI chatbot module missing complete setup function
- Missing utils directory structure completion

### Required Fixes
1. Complete cog loading system in main.py
2. Implement missing UI modal classes in admin.py
3. Add proper slash command decorators in moderation.py
4. Complete AI initialization in ai_chatbot.py
5. Ensure all utility modules are properly structured