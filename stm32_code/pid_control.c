/**
 ******************************************************************************
 * @file    pid_control.c
 * @brief   PID Controller implementation for BLDC motor speed control
 * @author  Skill-Agent PID Framework
 ******************************************************************************
 */

#include "pid_control.h"
#include <string.h>

/**
 * @brief Initialize PID controller
 */
void PID_Init(PID_TypeDef *pid, float Kp, float Ki, float Kd, float sample_time) {
    // Set gains
    pid->Kp = Kp;
    pid->Ki = Ki;
    pid->Kd = Kd;
    pid->sample_time = sample_time;
    
    // Initialize state variables
    pid->prev_error = 0.0f;
    pid->integral = 0.0f;
    pid->derivative = 0.0f;
    pid->output = 0.0f;
    
    // Set default output limits
    pid->output_min = -1000.0f;
    pid->output_max = 1000.0f;
}

/**
 * @brief Compute PID output
 */
float PID_Compute(PID_TypeDef *pid, float setpoint, float measurement) {
    // Calculate error
    float error = setpoint - measurement;
    
    // Proportional term
    float P = pid->Kp * error;
    
    // Integral term with anti-windup
    pid->integral += error * pid->sample_time;
    
    // Prevent integral windup
    float max_integral = (pid->output_max - pid->output_min) / (pid->Ki + 1e-6f);
    if (pid->integral > max_integral) {
        pid->integral = max_integral;
    } else if (pid->integral < -max_integral) {
        pid->integral = -max_integral;
    }
    
    float I = pid->Ki * pid->integral;
    
    // Derivative term with low-pass filter
    float derivative_raw = (error - pid->prev_error) / pid->sample_time;
    pid->derivative = 0.8f * pid->derivative + 0.2f * derivative_raw;
    float D = pid->Kd * pid->derivative;
    
    // Compute total output
    pid->output = P + I + D;
    
    // Apply output limits
    if (pid->output > pid->output_max) {
        pid->output = pid->output_max;
    } else if (pid->output < pid->output_min) {
        pid->output = pid->output_min;
    }
    
    // Save error for next iteration
    pid->prev_error = error;
    
    return pid->output;
}

/**
 * @brief Reset PID controller state
 */
void PID_Reset(PID_TypeDef *pid) {
    pid->prev_error = 0.0f;
    pid->integral = 0.0f;
    pid->derivative = 0.0f;
    pid->output = 0.0f;
}

/**
 * @brief Set output limits
 */
void PID_SetOutputLimits(PID_TypeDef *pid, float min, float max) {
    if (min < max) {
        pid->output_min = min;
        pid->output_max = max;
        
        // Clamp current output
        if (pid->output > max) {
            pid->output = max;
        } else if (pid->output < min) {
            pid->output = min;
        }
        
        // Clamp integral
        float max_integral = (max - min) / (pid->Ki + 1e-6f);
        if (pid->integral > max_integral) {
            pid->integral = max_integral;
        } else if (pid->integral < -max_integral) {
            pid->integral = -max_integral;
        }
    }
}

/**
 * @brief Update PID tunings at runtime
 */
void PID_SetTunings(PID_TypeDef *pid, float Kp, float Ki, float Kd) {
    // Update gains
    pid->Kp = Kp;
    pid->Ki = Ki;
    pid->Kd = Kd;
    
    // Reset integrator to prevent issues when changing gains
    pid->integral = 0.0f;
    pid->prev_error = 0.0f;
    pid->derivative = 0.0f;
}
