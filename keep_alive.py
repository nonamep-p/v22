
import requests
import time
import logging
from threading import Thread
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class KeepAliveMonitor:
    """Enhanced keep-alive monitor for 24/7 operation."""
    
    def __init__(self):
        self.port = os.getenv('PORT', 5000)
        self.base_url = f"http://0.0.0.0:{self.port}"
        self.ping_interval = 300  # 5 minutes
        self.health_check_interval = 60  # 1 minute
        self.running = True
        self.consecutive_failures = 0
        self.max_failures = 5
        
    def ping_self(self):
        """Enhanced ping with failure tracking."""
        while self.running:
            try:
                response = requests.get(f"{self.base_url}/ping", timeout=15)
                if response.status_code == 200:
                    self.consecutive_failures = 0
                    logger.debug("✅ Keep-alive ping successful")
                    
                    # Parse response for additional info
                    try:
                        data = response.json()
                        uptime_pct = data.get('uptime_percentage', 0)
                        if uptime_pct < 95:
                            logger.warning(f"⚠️ Low uptime percentage: {uptime_pct}%")
                    except:
                        pass
                else:
                    self.consecutive_failures += 1
                    logger.warning(f"⚠️ Keep-alive ping returned {response.status_code} (failure #{self.consecutive_failures})")
                    
            except Exception as e:
                self.consecutive_failures += 1
                logger.error(f"❌ Keep-alive ping failed: {e} (failure #{self.consecutive_failures})")
                
                # If too many consecutive failures, try to restart
                if self.consecutive_failures >= self.max_failures:
                    logger.error("🚨 Too many consecutive failures, system may need attention")
                    self.consecutive_failures = 0  # Reset counter
            
            time.sleep(self.ping_interval)
    
    def health_monitor(self):
        """Monitor detailed health status."""
        while self.running:
            try:
                response = requests.get(f"{self.base_url}/health", timeout=10)
                if response.status_code == 200:
                    logger.debug("💚 Health check passed")
                elif response.status_code == 503:
                    logger.warning("🟡 Health check indicates bot issues")
                else:
                    logger.warning(f"🔶 Health check unexpected status: {response.status_code}")
                    
            except Exception as e:
                logger.debug(f"Health check failed: {e}")
            
            time.sleep(self.health_check_interval)
    
    def external_ping(self):
        """Ping external services to maintain network connectivity."""
        external_urls = [
            "https://discord.com/api/v10/gateway",
            "https://httpbin.org/get"
        ]
        
        while self.running:
            for url in external_urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        logger.debug(f"🌐 External ping successful: {url}")
                    else:
                        logger.warning(f"⚠️ External ping failed: {url} ({response.status_code})")
                except Exception as e:
                    logger.debug(f"External ping error for {url}: {e}")
                
                time.sleep(30)  # Space out external pings
            
            time.sleep(600)  # Check external connectivity every 10 minutes
    
    def start_monitoring(self):
        """Start all monitoring threads."""
        # Start ping thread
        ping_thread = Thread(target=self.ping_self, daemon=True, name="KeepAlivePing")
        ping_thread.start()
        
        # Start health monitoring thread
        health_thread = Thread(target=self.health_monitor, daemon=True, name="HealthMonitor")
        health_thread.start()
        
        # Start external connectivity thread
        external_thread = Thread(target=self.external_ping, daemon=True, name="ExternalPing")
        external_thread.start()
        
        logger.info("🔄 Enhanced 24/7 keep-alive monitoring started")
        logger.info(f"📍 Monitoring endpoints: {self.base_url}")
        logger.info(f"⏱️ Ping interval: {self.ping_interval}s, Health interval: {self.health_check_interval}s")
    
    def stop_monitoring(self):
        """Stop all monitoring."""
        self.running = False
        logger.info("🛑 Keep-alive monitoring stopped")

# Global monitor instance
monitor = KeepAliveMonitor()

def ping_self():
    """Legacy function for backward compatibility."""
    monitor.ping_self()

def start_keep_alive():
    """Start the enhanced keep-alive monitoring system."""
    monitor.start_monitoring()

def stop_keep_alive():
    """Stop the keep-alive monitoring system."""
    monitor.stop_monitoring()
