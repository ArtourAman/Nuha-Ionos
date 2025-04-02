# Telegram API Configuration
API_ID = ""  
API_HASH = ""  
BOT_TOKEN = ""  
SESSION_STRING = "="

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
