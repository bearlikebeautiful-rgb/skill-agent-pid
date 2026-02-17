"""
Configuration file for Skill-Agent PID Tuning Framework
Contains API keys, communication settings, and application parameters
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ========================================
# Claude API Configuration
# ========================================
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
CLAUDE_MAX_TOKENS = 4096
CLAUDE_TEMPERATURE = 0.7

# ========================================
# Serial Communication Settings
# ========================================
SERIAL_PORT = os.getenv("SERIAL_PORT", "/dev/ttyUSB0")  # Default USB serial port
SERIAL_BAUDRATE = int(os.getenv("SERIAL_BAUDRATE", "115200"))
SERIAL_TIMEOUT = float(os.getenv("SERIAL_TIMEOUT", "2.0"))

# ========================================
# MQTT Configuration (Optional)
# ========================================
MQTT_ENABLED = os.getenv("MQTT_ENABLED", "False").lower() == "true"
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_DATA = "stm32/pid/data"
MQTT_TOPIC_PARAMS = "stm32/pid/params"
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

# ========================================
# PID Tuning Parameters
# ========================================
DEFAULT_SETPOINT = 1000.0  # Default speed setpoint (RPM)
STEP_INPUT_AMPLITUDE = 500.0  # Step input amplitude for system identification
SAMPLING_TIME = 0.01  # Sampling time in seconds (10ms)
STEP_RESPONSE_DURATION = 5.0  # Duration to collect step response data (seconds)

# ========================================
# System Identification Settings
# ========================================
SYSTEM_ORDER_THRESHOLD = 0.95  # R-squared threshold for model fit
MAX_SYSTEM_ORDER = 2  # Maximum system order to consider (1st or 2nd order)

# ========================================
# Performance Evaluation Thresholds
# ========================================
MAX_OVERSHOOT_PERCENT = 10.0  # Maximum acceptable overshoot percentage
MAX_SETTLING_TIME = 2.0  # Maximum acceptable settling time (seconds)
STEADY_STATE_ERROR_THRESHOLD = 2.0  # Maximum acceptable steady-state error (%)

# ========================================
# Logging Configuration
# ========================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "skill_agent_pid.log"

# ========================================
# Data Storage
# ========================================
DATA_DIR = "data"
PLOTS_DIR = "plots"

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)
