/**
 ******************************************************************************
 * @file    motor_driver.h
 * @brief   BLDC Motor driver header for STM32F103
 * @author  Skill-Agent PID Framework
 ******************************************************************************
 */

#ifndef MOTOR_DRIVER_H
#define MOTOR_DRIVER_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdbool.h>

/* Motor Configuration */
#define MOTOR_PWM_FREQUENCY     20000   /* 20 kHz PWM frequency */
#define MOTOR_PWM_RESOLUTION    1000    /* PWM resolution (0-1000) */
#define MOTOR_POLE_PAIRS        7       /* Number of pole pairs */

/* Motor State Structure */
typedef struct {
    float current_speed;        /* Current motor speed in RPM */
    float target_speed;         /* Target motor speed in RPM */
    int16_t pwm_duty;          /* PWM duty cycle (-1000 to 1000) */
    uint8_t direction;         /* Motor direction: 0=CW, 1=CCW */
    bool enabled;              /* Motor enable state */
    uint32_t hall_count;       /* Hall sensor pulse count */
    uint32_t last_hall_time;   /* Last hall sensor timestamp */
} Motor_TypeDef;

/* Function Prototypes */

/**
 * @brief Initialize motor driver
 * @param motor: Pointer to motor structure
 */
void Motor_Init(Motor_TypeDef *motor);

/**
 * @brief Enable or disable motor
 * @param motor: Pointer to motor structure
 * @param enable: true to enable, false to disable
 */
void Motor_Enable(Motor_TypeDef *motor, bool enable);

/**
 * @brief Set motor PWM duty cycle
 * @param motor: Pointer to motor structure
 * @param duty: PWM duty cycle (-1000 to 1000)
 */
void Motor_SetPWM(Motor_TypeDef *motor, int16_t duty);

/**
 * @brief Set motor direction
 * @param motor: Pointer to motor structure
 * @param direction: 0 for CW, 1 for CCW
 */
void Motor_SetDirection(Motor_TypeDef *motor, uint8_t direction);

/**
 * @brief Update motor speed measurement from hall sensors
 * @param motor: Pointer to motor structure
 * @return Current speed in RPM
 */
float Motor_UpdateSpeed(Motor_TypeDef *motor);

/**
 * @brief Hall sensor interrupt callback
 * @param motor: Pointer to motor structure
 * @note Should be called from hall sensor interrupt
 */
void Motor_HallCallback(Motor_TypeDef *motor);

/**
 * @brief Emergency stop motor
 * @param motor: Pointer to motor structure
 */
void Motor_EmergencyStop(Motor_TypeDef *motor);

#ifdef __cplusplus
}
#endif

#endif /* MOTOR_DRIVER_H */
