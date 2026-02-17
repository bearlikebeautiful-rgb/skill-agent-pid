#!/usr/bin/env python3
"""
Example: Simulate PID Tuning Without Hardware
Demonstrates the Skill-Agent PID framework using synthetic data
"""
import numpy as np
import sys
import tempfile
import os
sys.path.insert(0, '.')

from skills import system_identify, param_recommend, code_generate, performance_eval
import config

def simulate_step_response(Kp=1.0, Ki=0.5, Kd=0.1, system_type='first_order'):
    """
    Simulate a step response for testing without hardware
    
    Args:
        Kp, Ki, Kd: PID parameters to simulate
        system_type: 'first_order' or 'second_order'
        
    Returns:
        Dictionary with time, setpoint, and output arrays
    """
    print(f"\n{'='*70}")
    print(f"Simulating {system_type} system with PID controller")
    print(f"PID Parameters: Kp={Kp:.3f}, Ki={Ki:.3f}, Kd={Kd:.3f}")
    print(f"{'='*70}")
    
    # Time array
    dt = config.SAMPLING_TIME
    duration = config.STEP_RESPONSE_DURATION
    t = np.arange(0, duration, dt)
    
    # System parameters
    if system_type == 'first_order':
        K = 100.0  # System gain
        tau = 0.5  # Time constant
        
        # Generate step response (open-loop for identification)
        y = K * (1 - np.exp(-t / tau))
        
    else:  # second_order
        K = 100.0
        wn = 10.0  # Natural frequency
        zeta = 0.4  # Damping ratio (underdamped)
        
        # Generate underdamped step response
        wd = wn * np.sqrt(1 - zeta**2)
        y = K * (1 - np.exp(-zeta * wn * t) * 
                (np.cos(wd * t) + (zeta / np.sqrt(1 - zeta**2)) * np.sin(wd * t)))
    
    # Add some measurement noise
    noise = np.random.normal(0, 2, len(t))
    y_noisy = y + noise
    
    # Create data dictionary
    setpoint = np.ones_like(t) * K
    
    data = {
        'time': t,
        'setpoint': setpoint,
        'output': y_noisy
    }
    
    print(f"Generated {len(t)} data points over {duration}s")
    return data


def main():
    """Run complete PID tuning simulation"""
    
    print("\n" + "="*70)
    print("SKILL-AGENT PID TUNING FRAMEWORK - SIMULATION MODE")
    print("="*70)
    print("\nThis demo simulates the complete tuning workflow without hardware.")
    print("It demonstrates system identification, parameter recommendation,")
    print("code generation, and performance evaluation.")
    
    # Step 1: Generate synthetic step response data
    print("\n" + "="*70)
    print("STEP 1: Data Collection (Simulated)")
    print("="*70)
    
    # Try both first and second order systems
    for system_type in ['first_order', 'second_order']:
        data = simulate_step_response(system_type=system_type)
        
        # Step 2: System Identification
        print("\n" + "="*70)
        print("STEP 2: System Identification")
        print("="*70)
        
        result = system_identify.identify_system(data)
        
        # Step 3: Parameter Recommendation
        print("\n" + "="*70)
        print("STEP 3: PID Parameter Recommendation")
        print("="*70)
        
        pid_params = param_recommend.recommend_pid(result, tuning_method='auto')
        
        # Step 4: Code Generation
        print("\n" + "="*70)
        print("STEP 4: STM32 Code Generation")
        print("="*70)
        
        output_dir = os.path.join(tempfile.gettempdir(), f"stm32_generated_{system_type}")
        code_files = code_generate.generate_pid_code(pid_params, output_dir=output_dir)
        
        print(f"\nGenerated {len(code_files)} C code files in {output_dir}/")
        for filename in code_files.keys():
            print(f"  - {filename}")
        
        # Step 5: Performance Evaluation
        print("\n" + "="*70)
        print("STEP 5: Performance Evaluation")
        print("="*70)
        
        # For simulation, evaluate the original data
        # In real use, you would collect new data after applying PID parameters
        metrics = performance_eval.evaluate_performance(data, plot=False)
        
        print("\n" + "-"*70 + "\n")
    
    # Final Summary
    print("\n" + "="*70)
    print("SIMULATION COMPLETE")
    print("="*70)
    print("\nThe Skill-Agent PID framework successfully demonstrated:")
    print("  ✓ System identification from step response")
    print("  ✓ Automated PID parameter calculation")
    print("  ✓ STM32 C code generation")
    print("  ✓ Performance metric evaluation")
    print("\nTo use with real hardware:")
    print("  1. Set up your STM32 with the generated firmware")
    print("  2. Connect via USB serial or MQTT")
    print("  3. Run: python agent.py")
    print("\nFor Claude AI integration:")
    print("  1. Set CLAUDE_API_KEY in .env file")
    print("  2. Install: pip install anthropic")
    print("  3. Run: python agent.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
