# Quick Start Guide - Skill-Agent PID Framework

This guide helps you get started with the Skill-Agent PID tuning framework in under 5 minutes.

## Prerequisites

- Python 3.8+
- pip package manager
- (Optional) STM32F103 hardware with BLDC motor

## Installation

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/bearlikebeautiful-rgb/skill-agent-pid.git
cd skill-agent-pid
pip install -r requirements.txt
```

### 2. Configuration (Optional)

For Claude AI integration (recommended):
```bash
cp .env.example .env
# Edit .env and add your Claude API key
echo "CLAUDE_API_KEY=your_key_here" >> .env
```

For hardware connection:
```bash
# Edit .env to set your serial port
echo "SERIAL_PORT=/dev/ttyUSB0" >> .env  # Linux/Mac
# or
echo "SERIAL_PORT=COM3" >> .env  # Windows
```

## Usage

### Option 1: Simulation Mode (No Hardware Required)

Run the example simulation to see the complete workflow:

```bash
python3 example_simulation.py
```

This will:
- Generate synthetic step response data
- Identify system dynamics (1st and 2nd order)
- Calculate optimal PID parameters
- Generate STM32 C code
- Evaluate performance metrics

### Option 2: With Real Hardware

#### Step 1: Flash STM32 Firmware

1. Open `stm32_code/` in STM32CubeIDE
2. Add all `.c` and `.h` files to your project
3. Configure peripherals:
   - TIM1 for PWM (motor control)
   - TIM2 for speed measurement
   - TIM3 for 10ms control loop
   - USART1 at 115200 baud
4. Build and flash to STM32F103

#### Step 2: Connect Hardware

```bash
# Connect STM32 via USB
# Verify connection
ls /dev/ttyUSB*  # Linux/Mac
# or use Device Manager on Windows
```

#### Step 3: Run Agent

```bash
# Without Claude AI
python3 agent.py --manual

# With Claude AI (recommended)
python3 agent.py
```

The agent will:
1. Collect step response from MCU
2. Identify your system
3. Calculate optimal PID parameters
4. Generate C code
5. Download parameters to MCU
6. Evaluate performance

### Option 3: Using Individual Skills

Use skills programmatically in your own code:

```python
from skills import *

# Collect data (or load from file)
data = collect_step_response(setpoint=1000, amplitude=500)

# Identify system
system_model = identify_system(data)

# Get PID recommendations
pid_params = recommend_pid(system_model)

# Generate C code
code_files = generate_pid_code(pid_params, output_dir='./generated')

# Evaluate performance
metrics = evaluate_performance(data, plot=True)

# Download to MCU
success = download_pid_parameters(pid_params)
```

## Command Line Options

```bash
python3 agent.py --help

Options:
  --mqtt      Use MQTT instead of serial communication
  --manual    Run without Claude API
```

## Expected Output

### Simulation Mode

```
======================================================================
SKILL-AGENT PID TUNING FRAMEWORK - SIMULATION MODE
======================================================================

STEP 1: Data Collection (Simulated)
✓ Generated 500 data points

STEP 2: System Identification
✓ System type: second_order
✓ Fit quality (R²): 0.9847

STEP 3: PID Parameter Recommendation
✓ Recommended PID Parameters:
   Kp = 0.100000
   Ki = 0.010000
   Kd = 0.000095

STEP 4: STM32 Code Generation
✓ Generated 3 C code files

STEP 5: Performance Evaluation
✓ Overshoot: 10.5%
✓ Settling Time: 1.8s
✓ Assessment: EXCELLENT

✅ TUNING WORKFLOW COMPLETED SUCCESSFULLY
```

### With Hardware

```
STEP 1: Collecting Step Response Data from MCU
Serial connection established on /dev/ttyUSB0
✓ Collected 500 data points

[Claude's Analysis]
This second-order system exhibits underdamped characteristics...

STEP 2: System Identification
✓ System type: second_order
✓ Fit quality: 0.9847

[Additional Claude insights and recommendations...]

✓ TUNING WORKFLOW COMPLETED SUCCESSFULLY
```

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Serial port not found"
- Check USB connection
- Verify port in .env file
- Check permissions: `sudo chmod 666 /dev/ttyUSB0`

### "Claude API error"
- Verify API key in .env
- Install anthropic: `pip install anthropic`
- Or use --manual flag

## File Locations

After running, you'll find:

- **Generated C code**: `stm32_code/generated/` or `/tmp/stm32_generated_*/`
- **Performance plots**: `plots/`
- **Collected data**: `data/`
- **Logs**: `skill_agent_pid.log`

## Next Steps

1. **Simulation**: Run `python3 example_simulation.py`
2. **Hardware**: Flash firmware, connect, run `python3 agent.py`
3. **Iterate**: Adjust performance thresholds in `config.py`
4. **Explore**: Check `README.md` for detailed documentation

## Key Files

- `agent.py` - Main orchestration
- `config.py` - Configuration settings
- `skills/` - All skill modules
- `stm32_code/` - STM32 firmware
- `example_simulation.py` - Demo without hardware

## Support

- Check `README.md` for detailed documentation
- View examples in `example_simulation.py`
- Open issues on GitHub for bugs/questions

---

**Happy Tuning! 🎯**
