/**
 ******************************************************************************
 * @file    pid_control.h
 * @brief   PID Controller header file for BLDC motor speed control
 * @author  Skill-Agent PID Framework
 ******************************************************************************
 */

#ifndef PID_CONTROL_H
#define PID_CONTROL_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdbool.h>

/* PID Controller Structure */
typedef struct {
    float Kp;              /* Proportional gain */
    float Ki;              /* Integral gain */
    float Kd;              /* Derivative gain */
    float sample_time;     /* Sampling time in seconds */
    
    float prev_error;      /* Previous error for derivative */
    float integral;        /* Integral accumulator */
    float derivative;      /* Filtered derivative term */
    float output;          /* Controller output */
    
    float output_min;      /* Minimum output limit */
    float output_max;      /* Maximum output limit */
} PID_TypeDef;

/* Function Prototypes */

/**
 * @brief Initialize PID controller with default parameters
 * @param pid: Pointer to PID structure
 * @param Kp: Proportional gain
 * @param Ki: Integral gain
 * @param Kd: Derivative gain
 * @param sample_time: Sampling time in seconds
 */
void PID_Init(PID_TypeDef *pid, float Kp, float Ki, float Kd, float sample_time);

/**
 * @brief Compute PID output
 * @param pid: Pointer to PID structure
 * @param setpoint: Desired value
 * @param measurement: Current measured value
 * @return PID controller output
 */
float PID_Compute(PID_TypeDef *pid, float setpoint, float measurement);

/**
 * @brief Reset PID controller state
 * @param pid: Pointer to PID structure
 */
void PID_Reset(PID_TypeDef *pid);

/**
 * @brief Set output limits for PID controller
 * @param pid: Pointer to PID structure
 * @param min: Minimum output value
 * @param max: Maximum output value
 */
void PID_SetOutputLimits(PID_TypeDef *pid, float min, float max);

/**
 * @brief Update PID gains at runtime
 * @param pid: Pointer to PID structure
 * @param Kp: New proportional gain
 * @param Ki: New integral gain
 * @param Kd: New derivative gain
 */
void PID_SetTunings(PID_TypeDef *pid, float Kp, float Ki, float Kd);

#ifdef __cplusplus
}
#endif

#endif /* PID_CONTROL_H */
