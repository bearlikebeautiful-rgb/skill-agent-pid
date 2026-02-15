/**
 ******************************************************************************
 * @file    uart_comm.h
 * @brief   UART Communication header for Python-MCU interface
 * @author  Skill-Agent PID Framework
 ******************************************************************************
 */

#ifndef UART_COMM_H
#define UART_COMM_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdbool.h>

/* UART Configuration */
#define UART_RX_BUFFER_SIZE     256
#define UART_TX_BUFFER_SIZE     512
#define UART_TIMEOUT_MS         100

/* Command Types */
typedef enum {
    CMD_UNKNOWN = 0,
    CMD_SET_PID,
    CMD_GET_PID,
    CMD_STEP_RESPONSE,
    CMD_START_MOTOR,
    CMD_STOP_MOTOR,
    CMD_EMERGENCY_STOP
} UART_CommandType;

/* UART Communication Structure */
typedef struct {
    uint8_t rx_buffer[UART_RX_BUFFER_SIZE];
    uint8_t tx_buffer[UART_TX_BUFFER_SIZE];
    uint16_t rx_head;
    uint16_t rx_tail;
    bool command_ready;
} UART_Comm_TypeDef;

/* Function Prototypes */

/**
 * @brief Initialize UART communication
 * @param comm: Pointer to UART comm structure
 */
void UART_Init(UART_Comm_TypeDef *comm);

/**
 * @brief Process received UART data
 * @param comm: Pointer to UART comm structure
 * @return Command type if command received, CMD_UNKNOWN otherwise
 */
UART_CommandType UART_ProcessCommand(UART_Comm_TypeDef *comm);

/**
 * @brief Send JSON response via UART
 * @param status: Status string ("ok" or "error")
 * @param message: Optional message string
 */
void UART_SendResponse(const char *status, const char *message);

/**
 * @brief Send data sample via UART (for step response)
 * @param time: Time in seconds
 * @param setpoint: Target setpoint value
 * @param output: Current output value
 */
void UART_SendDataSample(float time, float setpoint, float output);

/**
 * @brief Send PID parameters via UART
 * @param Kp: Proportional gain
 * @param Ki: Integral gain
 * @param Kd: Derivative gain
 */
void UART_SendPIDParams(float Kp, float Ki, float Kd);

/**
 * @brief Parse SET_PID command
 * @param json_str: JSON string containing PID parameters
 * @param Kp: Output - Proportional gain
 * @param Ki: Output - Integral gain
 * @param Kd: Output - Derivative gain
 * @return true if parsing successful
 */
bool UART_ParseSetPID(const char *json_str, float *Kp, float *Ki, float *Kd);

/**
 * @brief Parse STEP_RESPONSE command
 * @param json_str: JSON string containing step parameters
 * @param setpoint: Output - Target setpoint
 * @param amplitude: Output - Step amplitude
 * @param duration: Output - Duration in seconds
 * @return true if parsing successful
 */
bool UART_ParseStepResponse(const char *json_str, float *setpoint, 
                           float *amplitude, float *duration);

/**
 * @brief UART receive interrupt callback
 * @param comm: Pointer to UART comm structure
 * @param data: Received byte
 */
void UART_RxCallback(UART_Comm_TypeDef *comm, uint8_t data);

#ifdef __cplusplus
}
#endif

#endif /* UART_COMM_H */
