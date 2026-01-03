# MATER_BE/backend/redis_client.py

import redis
import os

# Use Docker Compose service name 'redis' by default
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
