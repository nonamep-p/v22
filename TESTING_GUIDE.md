
# 🧪 Plagg Bot Testing Guide

## ✅ What We've Added So Far

### 🔧 Admin Control Panel (`$adminpanel`)
- **Player Management**: Modify levels, XP, currency, inventory
- **Item Management**: Create custom items, give/remove items
- **Game Settings**: XP multipliers, drop rates, max levels  
- **Economy Control**: Currency rates, shop prices, economy reset

### 🛡️ Enhanced Reliability
- **Auto-reconnection**: Exponential backoff for connection failures
- **Better Error Handling**: Detailed logging and debug info
- **Command Debugging**: Owner can use `$debug` to check commands
- **Message Logging**: Track command attempts for troubleshooting

### 🌐 Improved Keep-Alive
- **Multiple Endpoints**: `/ping`, `/status`, `/`
- **No Web Preview**: Clean JSON responses, no HTML interface
- **Health Monitoring**: Detailed uptime and status tracking

## 🧪 Testing Sequence

### 1. **Basic Bot Functionality**
```
$help                    # Should show interactive help menu
$debug                   # (Owner only) Check command list  
$ping                    # Basic response test
```

### 2. **RPG Core Features**
```
$startrpg               # Create character
$profile                # View character stats
$adventure              # Test adventure system
$battle                 # Test combat system
```

### 3. **Admin Panel Testing**
```
$adminpanel             # Open admin control panel
# Test each button:
# - Player Management → Search Player
# - Item Management → Give Items
# - Game Settings → XP Multipliers
# - Economy Control → Currency Rates
```

### 4. **Economy System**
```
$balance                # Check currency
$shop                   # View shop
$buy <item>             # Purchase test
$inventory              # Check inventory
```

### 5. **AI Chatbot**
```
@Plagg hello            # Mention bot
# Reply to bot message  # Test conversation
```

## 🚨 Troubleshooting Guide

### **Problem: Command Does Nothing (No Response)**

#### **Step 1: Check Logs**
Look for these patterns in console:
- `Command attempt: $command by User#1234` (message received)
- `Unknown command attempted: $command` (command not found)
- Any error messages

#### **Step 2: Use Debug Command**
```
$debug                  # List all commands
$debug commandname      # Check specific command
```

#### **Step 3: Check Module Status**
Commands might be disabled:
```
$config                 # Check enabled modules
# Enable missing modules in server config
```

#### **Step 4: Permission Issues**
- Bot needs proper permissions in channel
- User needs required role permissions
- Check Discord permission settings

#### **Step 5: Database Issues**
If RPG commands fail:
```
$startrpg               # Initialize user profile
# Try command again
```

### **Problem: Bot Goes Offline**

#### **Auto-Reconnection**
- Bot will attempt reconnection up to 10 times
- Uses exponential backoff (5s, 10s, 20s, 40s...)
- Check console for reconnection attempts

#### **Manual Restart**
1. Click "Stop" button in Replit
2. Wait 10 seconds
3. Click "Run" button
4. Monitor console for successful connection

#### **Connection Diagnostics**
```bash
# Check if Discord is reachable
curl -I https://discord.com
```

### **Problem: Admin Panel Not Working**

#### **Permission Check**
- User must have Administrator permission
- Bot must be in server with proper roles

#### **Module Check**
```
$config                 # Ensure admin module is enabled
```

### **Problem: Database Errors**

#### **Profile Creation**
Many commands require user profile:
```
$startrpg               # Creates profile if missing
```

#### **Data Corruption**
```
$adminpanel → Player Management → Search Player
# Check if player data exists and is valid
```

## 🔄 Keep-Alive Monitoring

### **Endpoints to Check**
- `https://your-repl-url.replit.dev/ping` - Basic health
- `https://your-repl-url.replit.dev/status` - Detailed status

### **Expected Responses**
```json
{
  "status": "alive",
  "timestamp": "2025-01-21T05:36:22.123456",
  "uptime": "0:15:30.123456",
  "message": "Bot is running"
}
```

## 📊 Performance Monitoring

### **Console Indicators**
- `✅ MODULE_NAME module loaded successfully` - All modules working
- `🚀 Starting bot connection...` - Connection attempt
- `✅ Bot User: Name#1234` - Successful login
- `🧀 Plagg has awakened!` - Bot fully ready

### **Error Patterns to Watch**
- `❌ FAILED` - Module loading issues
- `Connection refused` - Network problems
- `Invalid token` - Authentication issues
- `Rate limited` - Too many requests

## 🎯 Advanced Testing

### **Load Testing**
1. Use multiple commands rapidly
2. Test with multiple users simultaneously
3. Monitor response times and memory usage

### **Edge Cases**
```
$adminpanel             # Test with non-admin user
$give invalid_item      # Test invalid inputs
$battle                 # Test without character
```

### **Recovery Testing**
1. Force bot offline (stop process)
2. Verify auto-reconnection works
3. Test command functionality after reconnect

## 📞 Support Checklist

When reporting issues, provide:
1. **Exact command used**
2. **Console output** (last 20 lines)
3. **User permissions** (admin/regular)
4. **Server info** (members, channels)
5. **Steps to reproduce**

The bot now has comprehensive admin controls, better reliability, and detailed debugging tools. Use `$adminpanel` for full game control and `$debug` when commands aren't working!
