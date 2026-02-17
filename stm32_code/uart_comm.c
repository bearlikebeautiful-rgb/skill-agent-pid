/**
 ******************************************************************************
 * @file    uart_comm.c
 * @brief   UART Communication implementation for Python-MCU interface
 * @author  Skill-Agent PID Framework
 ******************************************************************************
 */

#include "uart_comm.h"
#include "stm32f1xx_hal.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* External UART handle (to be defined in main.c) */
extern UART_HandleTypeDef huart1;

/**
 * @brief Initialize UART communication
 */
void UART_Init(UART_Comm_TypeDef *comm) {
    comm->rx_head = 0;
    comm->rx_tail = 0;
    comm->command_ready = false;
    
    // Clear buffers
    memset(comm->rx_buffer, 0, UART_RX_BUFFER_SIZE);
    memset(comm->tx_buffer, 0, UART_TX_BUFFER_SIZE);
}

/**
 * @brief UART receive callback
 */
void UART_RxCallback(UART_Comm_TypeDef *comm, uint8_t data) {
    // Add data to circular buffer
    comm->rx_buffer[comm->rx_head] = data;
    comm->rx_head = (comm->rx_head + 1) % UART_RX_BUFFER_SIZE;
    
    // Check for newline (command complete)
    if (data == '\n') {
        comm->command_ready = true;
    }
}

/**
 * @brief Process received command
 */
UART_CommandType UART_ProcessCommand(UART_Comm_TypeDef *comm) {
    if (!comm->command_ready) {
        return CMD_UNKNOWN;
    }
    
    // Extract command string
    char cmd_str[UART_RX_BUFFER_SIZE];
    uint16_t idx = 0;
    
    while (comm->rx_tail != comm->rx_head && idx < UART_RX_BUFFER_SIZE - 1) {
        char c = comm->rx_buffer[comm->rx_tail];
        comm->rx_tail = (comm->rx_tail + 1) % UART_RX_BUFFER_SIZE;
        
        if (c == '\n' || c == '\r') {
            break;
        }
        
        cmd_str[idx++] = c;
    }
    cmd_str[idx] = '\0';
    
    comm->command_ready = false;
    
    // Parse command type
    if (strstr(cmd_str, "\"cmd\":\"set_pid\"") != NULL) {
        return CMD_SET_PID;
    } else if (strstr(cmd_str, "\"cmd\":\"get_pid\"") != NULL) {
        return CMD_GET_PID;
    } else if (strstr(cmd_str, "\"cmd\":\"step_response\"") != NULL) {
        return CMD_STEP_RESPONSE;
    } else if (strstr(cmd_str, "\"cmd\":\"start_motor\"") != NULL) {
        return CMD_START_MOTOR;
    } else if (strstr(cmd_str, "\"cmd\":\"stop_motor\"") != NULL) {
        return CMD_STOP_MOTOR;
    } else if (strstr(cmd_str, "\"cmd\":\"emergency_stop\"") != NULL) {
        return CMD_EMERGENCY_STOP;
    }
    
    return CMD_UNKNOWN;
}

/**
 * @brief Send JSON response
 */
void UART_SendResponse(const char *status, const char *message) {
    char buffer[UART_TX_BUFFER_SIZE];
    
    if (message != NULL) {
        snprintf(buffer, UART_TX_BUFFER_SIZE, 
                "{\"status\":\"%s\",\"message\":\"%s\"}\n", status, message);
    } else {
        snprintf(buffer, UART_TX_BUFFER_SIZE, 
                "{\"status\":\"%s\"}\n", status);
    }
    
    HAL_UART_Transmit(&huart1, (uint8_t*)buffer, strlen(buffer), UART_TIMEOUT_MS);
}

/**
 * @brief Send data sample
 */
void UART_SendDataSample(float time, float setpoint, float output) {
    char buffer[UART_TX_BUFFER_SIZE];
    
    snprintf(buffer, UART_TX_BUFFER_SIZE, 
            "{\"time\":%.3f,\"setpoint\":%.2f,\"output\":%.2f}\n",
            time, setpoint, output);
    
    HAL_UART_Transmit(&huart1, (uint8_t*)buffer, strlen(buffer), UART_TIMEOUT_MS);
}

/**
 * @brief Send PID parameters
 */
void UART_SendPIDParams(float Kp, float Ki, float Kd) {
    char buffer[UART_TX_BUFFER_SIZE];
    
    snprintf(buffer, UART_TX_BUFFER_SIZE, 
            "{\"Kp\":%.6f,\"Ki\":%.6f,\"Kd\":%.6f}\n",
            Kp, Ki, Kd);
    
    HAL_UART_Transmit(&huart1, (uint8_t*)buffer, strlen(buffer), UART_TIMEOUT_MS);
}

/**
 * @brief Simple JSON parsing for SET_PID command
 */
bool UART_ParseSetPID(const char *json_str, float *Kp, float *Ki, float *Kd) {
    char *ptr;
    
    // Find Kp
    ptr = strstr(json_str, "\"Kp\":");
    if (ptr != NULL) {
        *Kp = atof(ptr + 5);
    } else {
        return false;
    }
    
    // Find Ki
    ptr = strstr(json_str, "\"Ki\":");
    if (ptr != NULL) {
        *Ki = atof(ptr + 5);
    } else {
        return false;
    }
    
    // Find Kd
    ptr = strstr(json_str, "\"Kd\":");
    if (ptr != NULL) {
        *Kd = atof(ptr + 5);
    } else {
        return false;
    }
    
    return true;
}

/**
 * @brief Simple JSON parsing for STEP_RESPONSE command
 */
bool UART_ParseStepResponse(const char *json_str, float *setpoint, 
                           float *amplitude, float *duration) {
    char *ptr;
    
    // Find setpoint
    ptr = strstr(json_str, "\"setpoint\":");
    if (ptr != NULL) {
        *setpoint = atof(ptr + 11);
    } else {
        return false;
    }
    
    // Find amplitude
    ptr = strstr(json_str, "\"amplitude\":");
    if (ptr != NULL) {
        *amplitude = atof(ptr + 12);
    } else {
        return false;
    }
    
    // Find duration
    ptr = strstr(json_str, "\"duration\":");
    if (ptr != NULL) {
        *duration = atof(ptr + 11);
    } else {
        return false;
    }
    
    return true;
}
