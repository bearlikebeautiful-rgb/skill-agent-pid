"""
Code Generation Skill
Generates STM32 C code to update PID parameters
"""
from typing import Dict
import os
import config


class CodeGenerator:
    """Generates C code for STM32 PID parameter updates"""
    
    def __init__(self):
        self.generated_code = ""
    
    def generate_pid_struct_init(self, pid_params: Dict[str, float]) -> str:
        """
        Generate C code to initialize PID structure
        
        Args:
            pid_params: Dictionary with Kp, Ki, Kd values
            
        Returns:
            C code string
        """
        Kp = pid_params.get('Kp', 0.0)
        Ki = pid_params.get('Ki', 0.0)
        Kd = pid_params.get('Kd', 0.0)
        
        code = f"""
/* Auto-generated PID parameters */
/* Method: {pid_params.get('method', 'Unknown')} */
PID_TypeDef pid_controller = {{
    .Kp = {Kp:.6f}f,
    .Ki = {Ki:.6f}f,
    .Kd = {Kd:.6f}f,
    .prev_error = 0.0f,
    .integral = 0.0f,
    .output_min = -1000.0f,
    .output_max = 1000.0f
}};
"""
        return code
    
    def generate_pid_update_function(self, pid_params: Dict[str, float]) -> str:
        """
        Generate C function to update PID parameters at runtime
        
        Args:
            pid_params: Dictionary with Kp, Ki, Kd values
            
        Returns:
            C code string
        """
        Kp = pid_params.get('Kp', 0.0)
        Ki = pid_params.get('Ki', 0.0)
        Kd = pid_params.get('Kd', 0.0)
        
        code = f"""
/**
 * @brief Update PID controller parameters
 * @note Auto-generated function - Method: {pid_params.get('method', 'Unknown')}
 */
void PID_UpdateParameters(PID_TypeDef *pid) {{
    pid->Kp = {Kp:.6f}f;
    pid->Ki = {Ki:.6f}f;
    pid->Kd = {Kd:.6f}f;
    
    // Reset integrator to prevent wind-up issues
    pid->integral = 0.0f;
    pid->prev_error = 0.0f;
}}
"""
        return code
    
    def generate_full_pid_file(self, pid_params: Dict[str, float], 
                               sampling_time: float = None) -> str:
        """
        Generate complete PID controller C file
        
        Args:
            pid_params: Dictionary with Kp, Ki, Kd values
            sampling_time: Sampling time in seconds
            
        Returns:
            Complete C code string
        """
        if sampling_time is None:
            sampling_time = config.SAMPLING_TIME
        
        Kp = pid_params.get('Kp', 0.0)
        Ki = pid_params.get('Ki', 0.0)
        Kd = pid_params.get('Kd', 0.0)
        
        code = f"""/**
 ******************************************************************************
 * @file    pid_control_tuned.c
 * @brief   Auto-tuned PID controller for BLDC motor speed control
 * @author  Skill-Agent PID Framework
 * @date    Generated automatically
 ******************************************************************************
 */

#include "pid_control.h"

/* Auto-generated PID parameters */
/* Tuning Method: {pid_params.get('method', 'Unknown')} */
const float PID_KP = {Kp:.6f}f;
const float PID_KI = {Ki:.6f}f;
const float PID_KD = {Kd:.6f}f;
const float PID_SAMPLE_TIME = {sampling_time:.6f}f;

/**
 * @brief Initialize PID controller with tuned parameters
 * @param pid: Pointer to PID structure
 */
void PID_Init_Tuned(PID_TypeDef *pid) {{
    pid->Kp = PID_KP;
    pid->Ki = PID_KI;
    pid->Kd = PID_KD;
    pid->sample_time = PID_SAMPLE_TIME;
    pid->prev_error = 0.0f;
    pid->integral = 0.0f;
    pid->derivative = 0.0f;
    pid->output = 0.0f;
    pid->output_min = -1000.0f;
    pid->output_max = 1000.0f;
}}

/**
 * @brief Compute PID output
 * @param pid: Pointer to PID structure
 * @param setpoint: Desired value
 * @param measurement: Current measured value
 * @return PID controller output
 */
float PID_Compute(PID_TypeDef *pid, float setpoint, float measurement) {{
    float error = setpoint - measurement;
    
    // Proportional term
    float P = pid->Kp * error;
    
    // Integral term with anti-windup
    pid->integral += error * pid->sample_time;
    
    // Clamp integral to prevent windup
    float max_integral = 999999.0f;
    if (pid->Ki > 0.0001f) {{
        max_integral = (pid->output_max - pid->output_min) / pid->Ki;
    }}
    if (pid->integral > max_integral) {{
        pid->integral = max_integral;
    }} else if (pid->integral < -max_integral) {{
        pid->integral = -max_integral;
    }}
    
    float I = pid->Ki * pid->integral;
    
    // Derivative term with filtering
    float derivative = (error - pid->prev_error) / pid->sample_time;
    pid->derivative = 0.8f * pid->derivative + 0.2f * derivative;  // Low-pass filter
    float D = pid->Kd * pid->derivative;
    
    // Compute output
    pid->output = P + I + D;
    
    // Clamp output
    if (pid->output > pid->output_max) {{
        pid->output = pid->output_max;
    }} else if (pid->output < pid->output_min) {{
        pid->output = pid->output_min;
    }}
    
    // Save error for next iteration
    pid->prev_error = error;
    
    return pid->output;
}}

/**
 * @brief Reset PID controller state
 * @param pid: Pointer to PID structure
 */
void PID_Reset(PID_TypeDef *pid) {{
    pid->prev_error = 0.0f;
    pid->integral = 0.0f;
    pid->derivative = 0.0f;
    pid->output = 0.0f;
}}
"""
        return code
    
    def generate_config_header(self, pid_params: Dict[str, float]) -> str:
        """
        Generate configuration header file with PID parameters
        
        Args:
            pid_params: Dictionary with Kp, Ki, Kd values
            
        Returns:
            C header code string
        """
        Kp = pid_params.get('Kp', 0.0)
        Ki = pid_params.get('Ki', 0.0)
        Kd = pid_params.get('Kd', 0.0)
        
        code = f"""/**
 ******************************************************************************
 * @file    pid_config.h
 * @brief   Auto-tuned PID configuration parameters
 * @author  Skill-Agent PID Framework
 ******************************************************************************
 */

#ifndef PID_CONFIG_H
#define PID_CONFIG_H

/* Auto-generated PID parameters */
/* Tuning Method: {pid_params.get('method', 'Unknown')} */
#define PID_KP  {Kp:.6f}f
#define PID_KI  {Ki:.6f}f
#define PID_KD  {Kd:.6f}f

/* Sampling configuration */
#define PID_SAMPLE_TIME_MS  {config.SAMPLING_TIME * 1000:.1f}f
#define PID_SAMPLE_TIME_S   {config.SAMPLING_TIME:.6f}f

/* Output limits */
#define PID_OUTPUT_MIN  -1000.0f
#define PID_OUTPUT_MAX   1000.0f

#endif /* PID_CONFIG_H */
"""
        return code
    
    def save_generated_code(self, code: str, filename: str, output_dir: str = None):
        """
        Save generated code to file
        
        Args:
            code: Generated C code string
            filename: Output filename
            output_dir: Output directory (if None, uses stm32_code/)
        """
        if output_dir is None:
            output_dir = "stm32_code/generated"
        
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(code)
        
        print(f"Generated code saved to: {filepath}")


def generate_pid_code(pid_params: Dict[str, float], output_dir: str = None) -> Dict[str, str]:
    """
    Convenience function to generate all PID code files
    
    Args:
        pid_params: Dictionary with Kp, Ki, Kd values
        output_dir: Output directory for generated files
        
    Returns:
        Dictionary with filenames and their code content
    """
    generator = CodeGenerator()
    
    # Generate all code variants
    code_files = {
        'pid_control_tuned.c': generator.generate_full_pid_file(pid_params),
        'pid_config.h': generator.generate_config_header(pid_params),
        'pid_update_function.c': generator.generate_pid_update_function(pid_params)
    }
    
    # Save files if output directory specified
    if output_dir:
        for filename, code in code_files.items():
            generator.save_generated_code(code, filename, output_dir)
    
    return code_files


if __name__ == "__main__":
    # Test code generation
    print("Testing code generation skill...")
    
    pid_params = {
        'Kp': 1.5,
        'Ki': 0.8,
        'Kd': 0.2,
        'method': 'Ziegler-Nichols'
    }
    
    code_files = generate_pid_code(pid_params, output_dir="/tmp/stm32_generated")
    
    print("\nGenerated files:")
    for filename in code_files.keys():
        print(f"  - {filename}")
