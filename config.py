# Telegram API Configuration
API_ID = "24913689"  
API_HASH = "eed0b126502a0cc2b2651bfe52ceae43"  
BOT_TOKEN = "7964837083:AAEcvntTfUMNGGveWFwQnmUS5Q4qjC88dMQ"  
SESSION_STRING = "1BVtsOIkBu4KN08A9kxt2XaygWm6PUHvfaJCSaMfKyKUrZxM1EEf_BmxyZClZ9xZSdGLyvXRMnXaLQ1ZDKCLD2ZyRBJDXYyl5B_uVXRv6HPJXLJui_2SJqimyjdwS3y2q4HS16jt8rWJt7eqVb2zMRivjZsVb43WU2f7nV9uqbD9Qb1KEh2CjZsz0974k0Vr-gLz1KR6XN17ddkZ3Ob1zAeZr5bopi_a0Nk4eqo6ob5uf3qduv3JdJvA0g5M5cQSZBOHqTzW5qdeApLvs-Xxds-4iHMJIjFF-PHwka7yG7bBISMqePipWZ4z2Xa74K7Y1HpXOkWd_MqGOsGrKWrbWXt1uyuhaUxU="

# Channel Configuration
SOURCE_CHANNEL = [-1001397152032]  # Source channel ID
TARGET_CHANNEL = [-1002570648989]  # Target channel ID

# Forward Timing Configuration
FORWARD_DELAY_MIN = 15    # Increase minimum delay to 15 seconds
FORWARD_DELAY_MAX = 20    # Increase maximum delay to 20 seconds
BATCH_SIZE = 360         # Reduce batch size to 300 videos
BATCH_BREAK_MIN = 600    # Increase minimum break to 10 minutes
BATCH_BREAK_MAX = 1200   # Increase maximum break to 20 minutes
DAILY_SLEEP_HOURS = 14 # Hours to run before taking long break
DAILY_BREAK_HOURS = 1  # Hours to sleep after running DAILY_SLEEP_HOURS
