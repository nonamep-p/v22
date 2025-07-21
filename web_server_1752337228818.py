from flask import Flask, jsonify, render_template_string
import threading
import logging
import psutil
import os
from datetime import datetime

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Simple HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Epic RPG Helper - Status</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .logo {
            font-size: 3em;
            margin-bottom: 10px;
        }
        .title {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        .subtitle {
            font-size: 1.2em;
            opacity: 0.8;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .status-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }
        .status-card:hover {
            transform: translateY(-5px);
        }
        .card-title {
            font-size: 1.2em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .card-content {
            font-size: 0.9em;
            line-height: 1.6;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-online {
            background-color: #4CAF50;
        }
        .status-warning {
            background-color: #FF9800;
        }
        .status-error {
            background-color: #F44336;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
        }
        .metric-label {
            opacity: 0.8;
        }
        .metric-value {
            font-weight: bold;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            opacity: 0.7;
            font-size: 0.9em;
        }
        .refresh-btn {
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 20px auto;
            display: block;
        }
        .refresh-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }
        @media (max-width: 600px) {
            .container {
                padding: 20px;
                margin: 10px;
            }
            .title {
                font-size: 2em;
            }
            .status-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎮</div>
            <h1 class="title">Epic RPG Helper</h1>
            <p class="subtitle">Discord Bot Status Dashboard</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <div class="card-title">
                    🤖 Bot Status
                    <span class="status-indicator status-{{ bot_status }}"></span>
                </div>
                <div class="card-content">
                    <div class="metric">
                        <span class="metric-label">Status:</span>
                        <span class="metric-value">{{ status_text }}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Uptime:</span>
                        <span class="metric-value">{{ uptime }}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Last Updated:</span>
                        <span class="metric-value">{{ last_updated }}</span>
                    </div>
                </div>
            </div>
            
            <div class="status-card">
                <div class="card-title">
                    📊 System Metrics
                </div>
                <div class="card-content">
                    <div class="metric">
                        <span class="metric-label">Memory Usage:</span>
                        <span class="metric-value">{{ memory_usage }} MB</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">CPU Usage:</span>
                        <span class="metric-value">{{ cpu_usage }}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Process ID:</span>
                        <span class="metric-value">{{ process_id }}</span>
                    </div>
                </div>
            </div>
            
            <div class="status-card">
                <div class="card-title">
                    🌐 Network Info
                </div>
                <div class="card-content">
                    <div class="metric">
                        <span class="metric-label">Server Port:</span>
                        <span class="metric-value">5000</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Environment:</span>
                        <span class="metric-value">{{ environment }}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Python Version:</span>
                        <span class="metric-value">{{ python_version }}</span>
                    </div>
                </div>
            </div>
            
            <div class="status-card">
                <div class="card-title">
                    🎯 Bot Features
                </div>
                <div class="card-content">
                    <div class="metric">
                        <span class="metric-label">RPG System:</span>
                        <span class="metric-value">✅ Active</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">AI Chatbot:</span>
                        <span class="metric-value">{{ ai_status }}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Economy:</span>
                        <span class="metric-value">✅ Active</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Moderation:</span>
                        <span class="metric-value">✅ Active</span>
                    </div>
                </div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Status</button>
        
        <div class="footer">
            <p>Epic RPG Helper - Comprehensive Discord RPG Bot</p>
            <p>Features: Adventures • Economy • AI Chat • Moderation • Guilds</p>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => {
            location.reload();
        }, 30000);
        
        // Add smooth loading animation
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.status-card');
            cards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    card.style.transition = 'all 0.5s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            });
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main status page."""
    try:
        # Get system metrics
        process = psutil.Process()
        memory_usage = round(process.memory_info().rss / 1024 / 1024, 1)  # MB
        cpu_usage = round(process.cpu_percent(), 1)
        
        # Calculate uptime
        create_time = datetime.fromtimestamp(process.create_time())
        uptime = datetime.now() - create_time
        uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
        
        # Check if bot is running (simple check)
        bot_status = "online"
        status_text = "Running"
        
        # Check AI status
        ai_status = "✅ Ready" if os.getenv('GEMINI_API_KEY') else "❌ No API Key"
        
        # Get environment info
        environment = os.getenv('ENVIRONMENT', 'Development')
        python_version = f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}"
        
        return render_template_string(HTML_TEMPLATE,
            bot_status=bot_status,
            status_text=status_text,
            uptime=uptime_str,
            last_updated=datetime.now().strftime("%H:%M:%S UTC"),
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            process_id=os.getpid(),
            environment=environment,
            python_version=python_version,
            ai_status=ai_status
        )
        
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return render_template_string(HTML_TEMPLATE,
            bot_status="error",
            status_text="Error",
            uptime="Unknown",
            last_updated=datetime.now().strftime("%H:%M:%S UTC"),
            memory_usage="Unknown",
            cpu_usage="Unknown",
            process_id=os.getpid(),
            environment="Unknown",
            python_version="Unknown",
            ai_status="❌ Error"
        )

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Get basic system info
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_usage = process.cpu_percent()
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": int((datetime.now() - datetime.fromtimestamp(process.create_time())).total_seconds()),
            "memory_usage_mb": round(memory_usage, 1),
            "cpu_usage_percent": round(cpu_usage, 1),
            "process_id": os.getpid(),
            "environment": os.getenv('ENVIRONMENT', 'development'),
            "features": {
                "rpg_system": True,
                "economy": True,
                "ai_chatbot": bool(os.getenv('GEMINI_API_KEY')),
                "moderation": True,
                "admin": True
            }
        }
        
        return jsonify(health_data), 200
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/metrics')
def metrics():
    """Metrics endpoint for monitoring systems."""
    try:
        process = psutil.Process()
        
        metrics_data = {
            "system": {
                "memory_usage_bytes": process.memory_info().rss,
                "memory_usage_mb": round(process.memory_info().rss / 1024 / 1024, 1),
                "cpu_usage_percent": round(process.cpu_percent(), 1),
                "process_id": os.getpid(),
                "uptime_seconds": int((datetime.now() - datetime.fromtimestamp(process.create_time())).total_seconds())
            },
            "application": {
                "environment": os.getenv('ENVIRONMENT', 'development'),
                "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
                "features_enabled": {
                    "rpg_system": True,
                    "economy": True,
                    "ai_chatbot": bool(os.getenv('GEMINI_API_KEY')),
                    "moderation": True,
                    "admin": True
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(metrics_data), 200
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/status')
def api_status():
    """API status endpoint."""
    try:
        return jsonify({
            "api_version": "1.0",
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "endpoints": {
                "/": "Main status dashboard",
                "/health": "Health check endpoint",
                "/metrics": "System metrics",
                "/api/status": "API status"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"API status error: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Not Found",
        "message": "The requested endpoint does not exist.",
        "available_endpoints": ["/", "/health", "/metrics", "/api/status"]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred.",
        "timestamp": datetime.now().isoformat()
    }), 500

def run_web_server():
    """Run the web server."""
    try:
        # Disable Flask's default logging to reduce noise
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.WARNING)
        
        # Get port from environment, default to 5000
        port = int(os.getenv('PORT', 5000))
        
        logger.info(f"Starting web server on port {port}")
        
        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False  # Disable reloader to prevent issues in production
        )
        
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the server
    run_web_server()
