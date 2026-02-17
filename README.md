# Skill-Agent PID Tuning Framework

A complete Skill-Agent framework for automated PID tuning of STM32F103 microcontrollers controlling BLDC motors. This implementation enables intelligent, closed-loop PID parameter optimization using Claude Opus 4.6 as the core LLM.

## Overview

This framework combines Python-based Skills with STM32 C code to create an autonomous PID tuning system for BLDC motor speed control. The system collects step response data, identifies system dynamics, recommends optimal PID parameters, generates C code, and validates performance - all with intelligent oversight from Claude AI.

## Features

### 🎯 Core Capabilities

- **Automated System Identification**: Analyzes step response data to classify system dynamics (1st/2nd order)
- **Intelligent PID Tuning**: Multiple tuning methods (Ziegler-Nichols, CHR, IMC, Pole Placement)
- **Code Generation**: Automatically generates STM32 C code for optimized PID parameters
- **Performance Evaluation**: Comprehensive metrics (overshoot, settling time, steady-state error)
- **LLM Integration**: Claude Opus 4.6 provides intelligent analysis and recommendations
- **Flexible Communication**: Supports both USB Serial and MQTT protocols

### 🔧 Technical Stack

- **Hardware**: STM32F103 (Blue Pill), BLDC Motor with optional Hall sensors
- **Communication**: USB Serial (UART), MQTT (optional)
- **LLM**: Claude Opus 4.6 via Anthropic API
- **Languages**: Python 3.8+ (Agent/Skills), C (STM32 firmware)
- **Control Theory**: First and second-order system identification, multiple PID tuning algorithms

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Python Agent Layer                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Claude Opus 4.6 LLM                      │  │
│  │      (Analysis, Recommendations, Validation)          │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
│  ┌─────────────────────────▼──────────────────────────────┐│
│  │                    agent.py                            ││
│  │           (Workflow Orchestration)                     ││
│  └────────────────────────┬───────────────────────────────┘│
│                            │                                 │
│  ┌────────────────────────┴───────────────────────────────┐│
│  │                   Skills Layer                          ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ││
│  │  │   Data   │ │  System  │ │Parameter │ │   Code   │ ││
│  │  │ Collect  │ │ Identify │ │Recommend │ │ Generate │ ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ ││
│  │  ┌──────────┐ ┌──────────┐                            ││
│  │  │   Perf   │ │Parameter │                            ││
│  │  │   Eval   │ │ Download │                            ││
│  │  └──────────┘ └──────────┘                            ││
│  └────────────────────────────────────────────────────────┘│
└─────────────────────────┬───────────────────────────────────┘
                          │ USB Serial / MQTT
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                  STM32F103 MCU Layer                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  main.c: Control Loop + Command Processing           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │ pid_control  │ │motor_driver  │ │  uart_comm   │       │
│  │     .c/.h    │ │    .c/.h     │ │    .c/.h     │       │
│  └──────────────┘ └──────────────┘ └──────────────┘       │
└─────────────────────────┬───────────────────────────────────┘
                          │ PWM Control
                          │
                   ┌──────▼──────┐
                   │ BLDC Motor  │
                   └─────────────┘
```

## Installation

### Prerequisites

- Python 3.8 or higher
- STM32CubeIDE or ARM GCC toolchain (for STM32 development)
- STM32F103 microcontroller
- BLDC motor with driver circuit
- USB-Serial adapter or MQTT broker (optional)

### Python Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/bearlikebeautiful-rgb/skill-agent-pid.git
cd skill-agent-pid
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Create .env file
echo "CLAUDE_API_KEY=your_api_key_here" > .env
echo "SERIAL_PORT=/dev/ttyUSB0" >> .env
echo "SERIAL_BAUDRATE=115200" >> .env
```

### STM32 Firmware Setup

1. Open the `stm32_code/` directory in STM32CubeIDE or your preferred IDE
2. Configure your project for STM32F103
3. Include all `.c` and `.h` files from `stm32_code/`
4. Configure the following peripherals:
   - TIM1: PWM generation for motor control
   - TIM2: Hall sensor timing/speed measurement
   - TIM3: 10ms control loop timer
   - USART1: 115200 baud for communication
5. Build and flash the firmware to your STM32

## Usage

### Quick Start

Run the complete tuning workflow:

```bash
python agent.py
```

This will:
1. Collect step response data from the MCU
2. Identify system dynamics
3. Recommend optimal PID parameters
4. Generate STM32 C code
5. Download parameters to MCU
6. Evaluate performance

### Using MQTT Instead of Serial

```bash
python agent.py --mqtt
```

### Manual Mode (Without Claude API)

```bash
python agent.py --manual
```

### Using Individual Skills

You can also use skills independently:

```python
from skills.data_collect import collect_step_response
from skills.system_identify import identify_system
from skills.param_recommend import recommend_pid

# Collect data
data = collect_step_response(setpoint=1000, amplitude=500)

# Identify system
system_model = identify_system(data)

# Get PID recommendations
pid_params = recommend_pid(system_model, method='auto')

print(f"Recommended Kp={pid_params['Kp']:.4f}, "
      f"Ki={pid_params['Ki']:.4f}, Kd={pid_params['Kd']:.4f}")
```

## Configuration

Edit `config.py` to customize:

- **Claude API settings**: Model, temperature, max tokens
- **Serial/MQTT settings**: Port, baudrate, broker address
- **PID tuning parameters**: Setpoint, step amplitude, sampling time
- **Performance thresholds**: Max overshoot, settling time, steady-state error

## File Structure

```
skill-agent-pid/
├── skills/                      # Python Skills modules
│   ├── data_collect.py         # MCU data collection
│   ├── system_identify.py      # System dynamics identification
│   ├── param_recommend.py      # PID parameter calculation
│   ├── code_generate.py        # C code generation
│   ├── performance_eval.py     # Performance metrics
│   └── param_download.py       # Parameter download to MCU
├── stm32_code/                 # STM32 C firmware
│   ├── main.c                  # Main control program
│   ├── pid_control.c/.h        # PID controller
│   ├── motor_driver.c/.h       # BLDC motor driver
│   ├── uart_comm.c/.h          # UART communication
│   └── generated/              # Auto-generated code output
├── agent.py                    # Main orchestration agent
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── .gitignore                 # Git ignore rules
└── README.md                   # This file
```

## Communication Protocol

### Commands (Python → STM32)

JSON commands sent via Serial/MQTT:

```json
{"cmd": "set_pid", "Kp": 1.5, "Ki": 0.8, "Kd": 0.2}
{"cmd": "get_pid"}
{"cmd": "step_response", "setpoint": 1000, "amplitude": 500, "duration": 5.0}
{"cmd": "start_motor"}
{"cmd": "stop_motor"}
{"cmd": "emergency_stop"}
```

### Responses (STM32 → Python)

```json
{"status": "ok", "message": "PID parameters updated"}
{"status": "error", "message": "Invalid command"}
{"Kp": 1.5, "Ki": 0.8, "Kd": 0.2}
{"time": 0.100, "setpoint": 1000, "output": 850}
```

## Tuning Methods

The framework supports multiple PID tuning methods:

1. **Ziegler-Nichols**: Classic tuning for first-order systems
2. **Chien-Hrones-Reswick (CHR)**: Optimized for minimal overshoot
3. **Internal Model Control (IMC)**: Robust tuning with filter parameter
4. **Pole Placement**: For second-order systems with specific performance requirements

## Performance Metrics

The framework evaluates:

- **Rise Time**: Time to reach 90% of setpoint
- **Overshoot**: Peak value above setpoint (%)
- **Settling Time**: Time to stay within 2% of setpoint
- **Steady-State Error**: Final error from setpoint (%)
- **IAE**: Integral of Absolute Error
- **ITSE**: Integral of Time-weighted Squared Error

## Safety Features

- Emergency stop command
- Output limiting and anti-windup
- Integral clamping
- Derivative filtering
- Timeout detection for zero speed

## Examples

### Example Output

```
====================================================================
SKILL-AGENT PID TUNING FRAMEWORK
STM32F103 BLDC Motor Speed Control
====================================================================

============================================================
STEP 1: Collecting Step Response Data from MCU
============================================================
Serial connection established on /dev/ttyUSB0
✓ Collected 500 data points

============================================================
STEP 2: Identifying System Dynamics
============================================================
✓ System type: second_order
✓ Fit quality (R²): 0.9847

Claude's Analysis:
This second-order system exhibits underdamped characteristics with a 
damping ratio of 0.3, indicating significant oscillatory behavior...

============================================================
STEP 3: Computing Optimal PID Parameters
============================================================
✓ Recommended PID Parameters:
   Kp = 1.234567
   Ki = 0.456789
   Kd = 0.123456
   Method: Pole Placement (Second Order)

============================================================
✓ TUNING WORKFLOW COMPLETED SUCCESSFULLY
====================================================================
```

## Troubleshooting

### Connection Issues
- Verify serial port: `ls /dev/tty*`
- Check baudrate matches (115200)
- Ensure STM32 is powered and programmed

### Poor Tuning Results
- Collect longer step response (increase duration)
- Verify motor is mechanically sound
- Check for electrical noise
- Try different tuning methods

### Claude API Issues
- Verify API key in `.env` file
- Check internet connectivity
- Use `--manual` flag to skip LLM

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is open source. See LICENSE file for details.

## Acknowledgments

- Claude Opus 4.6 by Anthropic for intelligent analysis
- STM32 community for HAL libraries and examples
- Control systems literature for tuning algorithms

## Support

For questions or support, please open an issue on GitHub.

---

**Note**: This framework is designed for educational and prototyping purposes. For production systems, additional safety measures, error handling, and testing are recommended.