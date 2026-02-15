/**
 ******************************************************************************
 * @file    motor_driver.c
 * @brief   BLDC Motor driver implementation for STM32F103
 * @author  Skill-Agent PID Framework
 ******************************************************************************
 */

#include "motor_driver.h"
#include "stm32f1xx_hal.h"  // STM32 HAL library
#include <string.h>

/* External timer handle for PWM (to be defined in main.c) */
extern TIM_HandleTypeDef htim1;
extern TIM_HandleTypeDef htim2;

/* PWM channels for 3-phase BLDC */
#define PWM_CHANNEL_U   TIM_CHANNEL_1
#define PWM_CHANNEL_V   TIM_CHANNEL_2
#define PWM_CHANNEL_W   TIM_CHANNEL_3

/**
 * @brief Initialize motor driver
 */
void Motor_Init(Motor_TypeDef *motor) {
    // Initialize motor state
    motor->current_speed = 0.0f;
    motor->target_speed = 0.0f;
    motor->pwm_duty = 0;
    motor->direction = 0;
    motor->enabled = false;
    motor->hall_count = 0;
    motor->last_hall_time = 0;
    
    // Initialize PWM timers
    HAL_TIM_PWM_Start(&htim1, PWM_CHANNEL_U);
    HAL_TIM_PWM_Start(&htim1, PWM_CHANNEL_V);
    HAL_TIM_PWM_Start(&htim1, PWM_CHANNEL_W);
    
    // Set initial PWM to zero
    __HAL_TIM_SET_COMPARE(&htim1, PWM_CHANNEL_U, 0);
    __HAL_TIM_SET_COMPARE(&htim1, PWM_CHANNEL_V, 0);
    __HAL_TIM_SET_COMPARE(&htim1, PWM_CHANNEL_W, 0);
    
    // Initialize hall sensor timer for speed measurement
    HAL_TIM_Base_Start(&htim2);
}

/**
 * @brief Enable or disable motor
 */
void Motor_Enable(Motor_TypeDef *motor, bool enable) {
    motor->enabled = enable;
    
    if (!enable) {
        // Stop motor immediately
        Motor_SetPWM(motor, 0);
    }
}

/**
 * @brief Set motor PWM duty cycle
 */
void Motor_SetPWM(Motor_TypeDef *motor, int16_t duty) {
    // Clamp duty cycle
    if (duty > MOTOR_PWM_RESOLUTION) {
        duty = MOTOR_PWM_RESOLUTION;
    } else if (duty < -MOTOR_PWM_RESOLUTION) {
        duty = -MOTOR_PWM_RESOLUTION;
    }
    
    motor->pwm_duty = duty;
    
    // Set direction based on sign
    if (duty < 0) {
        motor->direction = 1;  // CCW
        duty = -duty;
    } else {
        motor->direction = 0;  // CW
    }
    
    // Apply PWM only if motor is enabled
    if (motor->enabled) {
        // Simplified 6-step commutation for BLDC
        // In real application, this would be based on hall sensor feedback
        __HAL_TIM_SET_COMPARE(&htim1, PWM_CHANNEL_U, duty);
        __HAL_TIM_SET_COMPARE(&htim1, PWM_CHANNEL_V, duty / 2);
        __HAL_TIM_SET_COMPARE(&htim1, PWM_CHANNEL_W, 0);
    } else {
        __HAL_TIM_SET_COMPARE(&htim1, PWM_CHANNEL_U, 0);
        __HAL_TIM_SET_COMPARE(&htim1, PWM_CHANNEL_V, 0);
        __HAL_TIM_SET_COMPARE(&htim1, PWM_CHANNEL_W, 0);
    }
}

/**
 * @brief Set motor direction
 */
void Motor_SetDirection(Motor_TypeDef *motor, uint8_t direction) {
    motor->direction = direction;
}

/**
 * @brief Update motor speed measurement
 */
float Motor_UpdateSpeed(Motor_TypeDef *motor) {
    // Calculate speed based on hall sensor pulses
    uint32_t current_time = __HAL_TIM_GET_COUNTER(&htim2);
    uint32_t delta_time = current_time - motor->last_hall_time;
    
    if (delta_time > 0) {
        // Calculate RPM from pulse frequency
        // Speed (RPM) = (pulses / time) * 60 / (pole_pairs * 6)
        // Assuming timer is in microseconds
        float frequency = 1000000.0f / (float)delta_time;  // Hz
        motor->current_speed = (frequency * 60.0f) / (MOTOR_POLE_PAIRS * 6.0f);
    }
    
    // Timeout check - if no pulses for too long, speed is zero
    if (delta_time > 1000000) {  // 1 second timeout
        motor->current_speed = 0.0f;
    }
    
    return motor->current_speed;
}

/**
 * @brief Hall sensor interrupt callback
 */
void Motor_HallCallback(Motor_TypeDef *motor) {
    uint32_t current_time = __HAL_TIM_GET_COUNTER(&htim2);
    
    // Update timing
    motor->last_hall_time = current_time;
    motor->hall_count++;
    
    // Update speed
    Motor_UpdateSpeed(motor);
    
    // In real implementation, this would also handle commutation
    // based on hall sensor state to properly drive the BLDC motor
}

/**
 * @brief Emergency stop motor
 */
void Motor_EmergencyStop(Motor_TypeDef *motor) {
    motor->enabled = false;
    motor->pwm_duty = 0;
    motor->target_speed = 0.0f;
    
    // Immediately stop all PWM outputs
    __HAL_TIM_SET_COMPARE(&htim1, PWM_CHANNEL_U, 0);
    __HAL_TIM_SET_COMPARE(&htim1, PWM_CHANNEL_V, 0);
    __HAL_TIM_SET_COMPARE(&htim1, PWM_CHANNEL_W, 0);
    
    // Optionally, disable PWM outputs
    HAL_TIM_PWM_Stop(&htim1, PWM_CHANNEL_U);
    HAL_TIM_PWM_Stop(&htim1, PWM_CHANNEL_V);
    HAL_TIM_PWM_Stop(&htim1, PWM_CHANNEL_W);
}
