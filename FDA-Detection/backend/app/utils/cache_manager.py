import time
from cachetools import TTLCache
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        # Cache for Shopee Metadata (Title, Images, Shop Attributes)
        # Key: product_id + shop_id
        # TTL: 2 hours (7200 seconds)
        # Max size: 1000 items
        self.metadata_cache = TTLCache(maxsize=1000, ttl=7200)
        
        # Browser Session State (Playwright storage_state)
        self.session_state: Optional[Dict] = None
        self.session_timestamp: float = 0
        self.session_ttl_sec: int = 1800 # 30 minutes session reuse
        
        # Failure Tracker for Circuit Breaker
        # Stores timestamps of recent failures
        self.failure_history = []
        self.failure_threshold = 0.7  # 70% threshold
        self.window_size = 10         # Last 10 requests
        self.failure_window_sec = 300 # 5 minutes window
        self.is_paused = False
        self.pause_start_time = 0
        self.pause_duration = 300     # 5 minutes pause
        
    def get_metadata(self, key: str) -> Optional[Dict]:
        """Retrieve cached metadata if available."""
        return self.metadata_cache.get(key)
    
    def set_metadata(self, key: str, data: Dict):
        """Store metadata in cache."""
        self.metadata_cache[key] = data

    def get_session_state(self) -> Optional[Dict]:
        """Retrieve cached browser session (storage_state) if within TTL."""
        if self.session_state and (time.time() - self.session_timestamp < self.session_ttl_sec):
            return self.session_state
        return None

    def set_session_state(self, state: Dict):
        """Store browser session state (storage_state)."""
        self.session_state = state
        self.session_timestamp = time.time()
        
    def record_success(self):
        """Reset failure counter on success or just record it."""
        # For a simple sliding window, we track both success and failure
        self._add_to_history(True)
        self._check_circuit_state()

    def record_failure(self):
        """Record a scraping failure (Timeout/Blocked)."""
        self._add_to_history(False)
        self._check_circuit_state()
        
    def _add_to_history(self, success: bool):
        now = time.time()
        self.failure_history.append((now, success))
        # Keep only recent history within window or size
        self.failure_history = [
            h for h in self.failure_history 
            if now - h[0] < self.failure_window_sec
        ][-self.window_size:]
        
    def _check_circuit_state(self):
        """Update circuit breaker state based on failure history."""
        if len(self.failure_history) < 5: # Not enough data
            return

        failures = sum(1 for h in self.failure_history if not h[1])
        fail_rate = failures / len(self.failure_history)
        
        if fail_rate >= self.failure_threshold:
            if not self.is_paused:
                logger.error(f"🚨 CIRCUIT BREAKER TRIGGERED: Failure rate {fail_rate*100}%! Pausing scraper.")
                self.is_paused = True
                self.pause_start_time = time.time()
        else:
            if self.is_paused and (time.time() - self.pause_start_time > self.pause_duration):
                logger.info("🟢 CIRCUIT BREAKER RECOVERED: Resuming scraper.")
                self.is_paused = False
                
    def check_scraper_status(self) -> bool:
        """Return True if scraper is allowed to run, False if paused."""
        if self.is_paused:
            # Check if pause duration passed
            if time.time() - self.pause_start_time > self.pause_duration:
                self.is_paused = False
                logger.info("🟢 Circuit breaker timeout expired. Resuming.")
                return True
            return False
        return True

# Global Instance
cache_manager = CacheManager()
