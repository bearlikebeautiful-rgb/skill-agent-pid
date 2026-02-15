/**
 ******************************************************************************
 * @file    main.c
 * @brief   Main program for BLDC motor PID control with Skill-Agent framework
 * @author  Skill-Agent PID Framework
 ******************************************************************************
 */

#include "stm32f1xx_hal.h"
#include "pid_control.h"
#include "motor_driver.h"
#include "uart_comm.h"
#include <stdbool.h>

/* Private variables */
TIM_HandleTypeDef htim1;  // PWM timer for motor control
TIM_HandleTypeDef htim2;  // Timer for speed measurement
TIM_HandleTypeDef htim3;  // Timer for control loop
UART_HandleTypeDef huart1;  // UART for communication

PID_TypeDef pid_controller;
Motor_TypeDef motor;
UART_Comm_TypeDef uart_comm;

/* System state */
bool system_running = false;
bool step_response_active = false;
float step_start_time = 0.0f;
float step_duration = 5.0f;
float step_setpoint = 1000.0f;

/* Default PID parameters (to be tuned by agent) */
#define DEFAULT_KP  1.0f
#define DEFAULT_KI  0.5f
#define DEFAULT_KD  0.1f
#define SAMPLE_TIME 0.01f  // 10ms sampling time

/* Private function prototypes */
void SystemClock_Config(void);
void GPIO_Init(void);
void TIM1_Init(void);  // PWM timer
void TIM2_Init(void);  // Speed measurement timer
void TIM3_Init(void);  // System timer for control loop
void UART1_Init(void);
void Error_Handler(void);
float GetSystemTime(void);

/* Main program */
int main(void) {
    // Initialize HAL
    HAL_Init();
    
    // Configure system clock
    SystemClock_Config();
    
    // Initialize peripherals
    GPIO_Init();
    TIM1_Init();
    TIM2_Init();
    TIM3_Init();
    UART1_Init();
    
    // Initialize modules
    PID_Init(&pid_controller, DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, SAMPLE_TIME);
    PID_SetOutputLimits(&pid_controller, -1000.0f, 1000.0f);
    Motor_Init(&motor);
    UART_Init(&uart_comm);
    
    // Send startup message
    UART_SendResponse("ok", "System initialized");
    
    // Main loop
    while (1) {
        // Process UART commands
        UART_CommandType cmd = UART_ProcessCommand(&uart_comm);
        
        switch (cmd) {
            case CMD_SET_PID: {
                float Kp, Ki, Kd;
                // Note: Would need to store command string for parsing
                // Simplified: assume parameters are set directly
                PID_SetTunings(&pid_controller, Kp, Ki, Kd);
                UART_SendResponse("ok", "PID parameters updated");
                break;
            }
            
            case CMD_GET_PID: {
                UART_SendPIDParams(pid_controller.Kp, pid_controller.Ki, pid_controller.Kd);
                break;
            }
            
            case CMD_STEP_RESPONSE: {
                // Start step response test
                step_response_active = true;
                step_start_time = GetSystemTime();
                PID_Reset(&pid_controller);
                motor.target_speed = step_setpoint;
                Motor_Enable(&motor, true);
                system_running = true;
                UART_SendResponse("ok", "Step response started");
                break;
            }
            
            case CMD_START_MOTOR: {
                Motor_Enable(&motor, true);
                system_running = true;
                UART_SendResponse("ok", "Motor started");
                break;
            }
            
            case CMD_STOP_MOTOR: {
                Motor_Enable(&motor, false);
                system_running = false;
                step_response_active = false;
                UART_SendResponse("ok", "Motor stopped");
                break;
            }
            
            case CMD_EMERGENCY_STOP: {
                Motor_EmergencyStop(&motor);
                system_running = false;
                step_response_active = false;
                UART_SendResponse("ok", "Emergency stop");
                break;
            }
            
            default:
                break;
        }
        
        // Control loop runs at fixed interval (handled by TIM3 interrupt)
        HAL_Delay(1);
    }
}

/**
 * @brief TIM3 Period elapsed callback (10ms control loop)
 */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) {
    if (htim->Instance == TIM3) {
        // Control loop executed every 10ms
        
        if (system_running && motor.enabled) {
            // Update motor speed measurement
            float current_speed = Motor_UpdateSpeed(&motor);
            
            // Compute PID output
            float control_output = PID_Compute(&pid_controller, 
                                              motor.target_speed, 
                                              current_speed);
            
            // Apply control output to motor
            Motor_SetPWM(&motor, (int16_t)control_output);
            
            // Send data if step response is active
            if (step_response_active) {
                float elapsed = GetSystemTime() - step_start_time;
                
                UART_SendDataSample(elapsed, motor.target_speed, current_speed);
                
                // Stop step response after duration
                if (elapsed >= step_duration) {
                    step_response_active = false;
                }
            }
        }
    }
}

/**
 * @brief UART receive complete callback
 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == USART1) {
        uint8_t received_byte;
        HAL_UART_Receive_IT(&huart1, &received_byte, 1);
        UART_RxCallback(&uart_comm, received_byte);
    }
}

/**
 * @brief Get system time in seconds
 */
float GetSystemTime(void) {
    return (float)HAL_GetTick() / 1000.0f;
}

/**
 * @brief System Clock Configuration (72 MHz for STM32F103)
 */
void SystemClock_Config(void) {
    RCC_OscInitTypeDef RCC_OscInitStruct = {0};
    RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
    
    // Configure oscillator
    RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    RCC_OscInitStruct.HSEState = RCC_HSE_ON;
    RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
    RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;  // 8MHz * 9 = 72MHz
    
    if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK) {
        Error_Handler();
    }
    
    // Configure clocks
    RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK
                                | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
    RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
    RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;
    
    if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK) {
        Error_Handler();
    }
}

/**
 * @brief GPIO Initialization
 */
void GPIO_Init(void) {
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    
    // Configure LED pin (PC13 on Blue Pill)
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    GPIO_InitStruct.Pin = GPIO_PIN_13;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);
}

/**
 * @brief TIM1 Initialization (PWM for motor control)
 */
void TIM1_Init(void) {
    __HAL_RCC_TIM1_CLK_ENABLE();
    
    TIM_MasterConfigTypeDef sMasterConfig = {0};
    TIM_OC_InitTypeDef sConfigOC = {0};
    
    htim1.Instance = TIM1;
    htim1.Init.Prescaler = 72 - 1;  // 1 MHz timer clock
    htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim1.Init.Period = 1000 - 1;  // 1 kHz PWM (adjustable)
    htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim1.Init.RepetitionCounter = 0;
    htim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    
    if (HAL_TIM_PWM_Init(&htim1) != HAL_OK) {
        Error_Handler();
    }
    
    // Configure PWM channels
    sConfigOC.OCMode = TIM_OCMODE_PWM1;
    sConfigOC.Pulse = 0;
    sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
    sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
    
    HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_1);
    HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_2);
    HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_3);
}

/**
 * @brief TIM2 Initialization (speed measurement)
 */
void TIM2_Init(void) {
    __HAL_RCC_TIM2_CLK_ENABLE();
    
    htim2.Instance = TIM2;
    htim2.Init.Prescaler = 72 - 1;  // 1 MHz (1 μs resolution)
    htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim2.Init.Period = 0xFFFFFFFF;  // Maximum period
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    
    if (HAL_TIM_Base_Init(&htim2) != HAL_OK) {
        Error_Handler();
    }
}

/**
 * @brief TIM3 Initialization (10ms control loop interrupt)
 */
void TIM3_Init(void) {
    __HAL_RCC_TIM3_CLK_ENABLE();
    
    htim3.Instance = TIM3;
    htim3.Init.Prescaler = 7200 - 1;  // 10 kHz
    htim3.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim3.Init.Period = 100 - 1;  // 10ms period (100 Hz)
    htim3.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    
    if (HAL_TIM_Base_Init(&htim3) != HAL_OK) {
        Error_Handler();
    }
    
    // Start timer with interrupt
    HAL_TIM_Base_Start_IT(&htim3);
}

/**
 * @brief UART1 Initialization (115200 baud)
 */
void UART1_Init(void) {
    __HAL_RCC_USART1_CLK_ENABLE();
    
    huart1.Instance = USART1;
    huart1.Init.BaudRate = 115200;
    huart1.Init.WordLength = UART_WORDLENGTH_8B;
    huart1.Init.StopBits = UART_STOPBITS_1;
    huart1.Init.Parity = UART_PARITY_NONE;
    huart1.Init.Mode = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    
    if (HAL_UART_Init(&huart1) != HAL_OK) {
        Error_Handler();
    }
    
    // Enable UART receive interrupt
    uint8_t dummy;
    HAL_UART_Receive_IT(&huart1, &dummy, 1);
}

/**
 * @brief Error Handler
 */
void Error_Handler(void) {
    // Disable interrupts
    __disable_irq();
    
    // Flash LED to indicate error
    while (1) {
        HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
        HAL_Delay(100);
    }
}
