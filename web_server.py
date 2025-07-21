from flask import Flask, jsonify, render_template_string
import logging
import os
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variables to store bot status
bot_status = {
    'is_online': False,
    'start_time': datetime.now(),
    'guilds': 0,
    'users': 0,
    'latency': 0,
    'uptime': 0,
    'reconnect_count': 0,
    'last_heartbeat': datetime.now(),
    'uptime_percentage': 100.0
}

# Track uptime statistics
uptime_tracker = {
    'total_checks': 0,
    'successful_checks': 0,
    'last_downtime': None,
    'total_downtime': 0
}

def update_bot_status(bot=None):
    """Update bot status for web server."""
    global bot_status, uptime_tracker

    current_time = datetime.now()
    uptime_tracker['total_checks'] += 1

    if bot and hasattr(bot, 'guilds') and bot.is_ready():
        bot_status['is_online'] = True
        bot_status['guilds'] = len(bot.guilds)
        bot_status['users'] = sum(guild.member_count for guild in bot.guilds)
        bot_status['latency'] = round(bot.latency * 1000, 2) if bot.latency else 0
        bot_status['last_heartbeat'] = current_time
        uptime_tracker['successful_checks'] += 1
        
        # End downtime tracking if we were down
        if uptime_tracker['last_downtime']:
            downtime_duration = (current_time - uptime_tracker['last_downtime']).total_seconds()
            uptime_tracker['total_downtime'] += downtime_duration
            uptime_tracker['last_downtime'] = None
    else:
        bot_status['is_online'] = False
        # Start downtime tracking if not already started
        if not uptime_tracker['last_downtime']:
            uptime_tracker['last_downtime'] = current_time

    # Calculate uptime percentage
    if uptime_tracker['total_checks'] > 0:
        bot_status['uptime_percentage'] = (uptime_tracker['successful_checks'] / uptime_tracker['total_checks']) * 100

    # Calculate total uptime
    bot_status['uptime'] = int((current_time - bot_status['start_time']).total_seconds())

def continuous_monitoring():
    """Continuously monitor bot status for 24/7 tracking."""
    while True:
        try:
            update_bot_status()
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            time.sleep(60)

# Start monitoring thread
monitoring_thread = threading.Thread(target=continuous_monitoring, daemon=True)
monitoring_thread.start()

start_time = datetime.now()
@app.route('/ping')
def ping():
    """Enhanced health check endpoint."""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.now().isoformat(),
        'uptime': str(datetime.now() - start_time) if start_time else 'unknown',
        'bot_online': bot_status['is_online'],
        'uptime_percentage': round(bot_status['uptime_percentage'], 2),
        'message': '24/7 Keep-Alive Service Active'
    })

@app.route('/status')
def status():
    """Comprehensive bot status endpoint."""
    current_time = datetime.now()
    
    return jsonify({
        'bot_status': 'online' if bot_status['is_online'] else 'offline',
        'server_time': current_time.isoformat(),
        'uptime_seconds': bot_status['uptime'],
        'uptime_percentage': round(bot_status['uptime_percentage'], 2),
        'guilds': bot_status['guilds'],
        'users': bot_status['users'],
        'latency': bot_status['latency'],
        'last_heartbeat': bot_status['last_heartbeat'].isoformat(),
        'reconnect_count': bot_status['reconnect_count'],
        'total_checks': uptime_tracker['total_checks'],
        'successful_checks': uptime_tracker['successful_checks'],
        'total_downtime': uptime_tracker['total_downtime'],
        'health': 'excellent' if bot_status['uptime_percentage'] >= 99 else 'good' if bot_status['uptime_percentage'] >= 95 else 'fair'
    })

@app.route('/health')
def health():
    """Simple health endpoint for external monitoring."""
    is_healthy = (
        bot_status['is_online'] and 
        (datetime.now() - bot_status['last_heartbeat']).total_seconds() < 300
    )
    
    return jsonify({
        'healthy': is_healthy,
        'timestamp': datetime.now().isoformat()
    }), 200 if is_healthy else 503

@app.route('/')
def home():
    """24/7 monitoring dashboard."""
    dashboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Plagg Bot - 24/7 Monitoring</title>
        <meta http-equiv="refresh" content="30">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: #fff; }
            .status { padding: 20px; border-radius: 8px; margin: 20px 0; }
            .online { background: #2d5a2d; border-left: 5px solid #4CAF50; }
            .offline { background: #5a2d2d; border-left: 5px solid #f44336; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
            .stat { background: #333; padding: 15px; border-radius: 5px; }
            .title { color: #4CAF50; font-size: 24px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="title">🧀 Plagg Bot - 24/7 Monitoring Dashboard</div>
        
        <div class="status {{ 'online' if bot_online else 'offline' }}">
            <h2>Bot Status: {{ 'ONLINE' if bot_online else 'OFFLINE' }}</h2>
            <p>Last Update: {{ current_time }}</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <h3>Uptime</h3>
                <p>{{ uptime_str }}</p>
                <p>{{ uptime_percentage }}% reliability</p>
            </div>
            <div class="stat">
                <h3>Servers</h3>
                <p>{{ guilds }} guilds</p>
                <p>{{ users }} total users</p>
            </div>
            <div class="stat">
                <h3>Performance</h3>
                <p>{{ latency }}ms latency</p>
                <p>{{ successful_checks }}/{{ total_checks }} checks passed</p>
            </div>
            <div class="stat">
                <h3>Reliability</h3>
                <p>{{ reconnect_count }} reconnections</p>
                <p>{{ total_downtime }}s total downtime</p>
            </div>
        </div>
        
        <p><em>Auto-refresh every 30 seconds | 24/7 Support Active</em></p>
    </body>
    </html>
    """
    
    current_time = datetime.now()
    uptime_seconds = bot_status['uptime']
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"
    
    return render_template_string(dashboard_html,
        bot_online=bot_status['is_online'],
        current_time=current_time.strftime('%Y-%m-%d %H:%M:%S'),
        uptime_str=uptime_str,
        uptime_percentage=round(bot_status['uptime_percentage'], 1),
        guilds=bot_status['guilds'],
        users=bot_status['users'],
        latency=bot_status['latency'],
        successful_checks=uptime_tracker['successful_checks'],
        total_checks=uptime_tracker['total_checks'],
        reconnect_count=bot_status['reconnect_count'],
        total_downtime=int(uptime_tracker['total_downtime'])
    )

def run_web_server():
    """Run the web server."""
    try:
        # Disable Flask's default logging to reduce noise
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.WARNING)

        # Get port from environment, default to 5000
        port = int(os.getenv('PORT', 5000))

        logger.info(f"🌍 Starting minimal web server on 0.0.0.0:{port}")

        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False
        )

    except Exception as e:
        logger.error(f"❌ Failed to start web server: {e}")

# Function to be called by the bot to update status
def set_bot_online(bot):
    """Set bot as online and update stats."""
    update_bot_status(bot)

def set_bot_offline():
    """Set bot as offline."""
    global bot_status
    bot_status['is_online'] = False
    bot_status['guilds'] = 0
    bot_status['users'] = 0
    bot_status['latency'] = 0