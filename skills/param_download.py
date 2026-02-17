"""
Parameter Download Skill
Sends new tuning parameters to the MCU via Serial or MQTT
"""
import serial
import json
import time
from typing import Dict, Optional
import config

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("Warning: paho-mqtt not available. MQTT functionality will be disabled.")


class ParameterDownloader:
    """Downloads PID parameters to STM32 MCU"""
    
    def __init__(self, use_mqtt: bool = False):
        """
        Initialize parameter downloader
        
        Args:
            use_mqtt: If True, use MQTT instead of serial communication
        """
        self.use_mqtt = use_mqtt and config.MQTT_ENABLED and MQTT_AVAILABLE
        self.serial_conn = None
        self.mqtt_client = None
        self.ack_received = False
    
    def connect_serial(self) -> bool:
        """
        Establish serial connection to STM32
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.serial_conn = serial.Serial(
                port=config.SERIAL_PORT,
                baudrate=config.SERIAL_BAUDRATE,
                timeout=config.SERIAL_TIMEOUT
            )
            time.sleep(2)  # Wait for connection to stabilize
            print(f"Serial connection established on {config.SERIAL_PORT}")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to serial port: {e}")
            return False
    
    def connect_mqtt(self) -> bool:
        """
        Establish MQTT connection
        
        Returns:
            True if connection successful, False otherwise
        """
        if not MQTT_AVAILABLE:
            print("MQTT library not available")
            return False
            
        try:
            self.mqtt_client = mqtt.Client()
            
            if config.MQTT_USERNAME and config.MQTT_PASSWORD:
                self.mqtt_client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
            
            self.mqtt_client.on_message = self._on_mqtt_message
            self.mqtt_client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
            self.mqtt_client.subscribe("stm32/pid/ack")
            self.mqtt_client.loop_start()
            print(f"MQTT connection established to {config.MQTT_BROKER}")
            return True
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            return False
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Callback for receiving MQTT messages"""
        try:
            if msg.topic == "stm32/pid/ack":
                data = json.loads(msg.payload.decode())
                if data.get("status") == "ok":
                    self.ack_received = True
                    print("ACK received via MQTT")
        except Exception as e:
            print(f"Error parsing MQTT message: {e}")
    
    def send_parameters_serial(self, pid_params: Dict[str, float]) -> bool:
        """
        Send PID parameters via serial
        
        Args:
            pid_params: Dictionary with Kp, Ki, Kd values
            
        Returns:
            True if parameters sent successfully
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Error: Serial connection not open")
            return False
        
        try:
            # Format command
            command = {
                "cmd": "set_pid",
                "Kp": float(pid_params.get('Kp', 0)),
                "Ki": float(pid_params.get('Ki', 0)),
                "Kd": float(pid_params.get('Kd', 0))
            }
            
            # Send command
            cmd_str = json.dumps(command) + "\n"
            self.serial_conn.write(cmd_str.encode())
            print(f"Sent PID parameters via Serial: Kp={command['Kp']:.4f}, "
                  f"Ki={command['Ki']:.4f}, Kd={command['Kd']:.4f}")
            
            # Wait for acknowledgment
            timeout = 5.0
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.serial_conn.in_waiting:
                    try:
                        line = self.serial_conn.readline().decode().strip()
                        response = json.loads(line)
                        
                        if response.get("status") == "ok":
                            print("ACK received: Parameters updated successfully")
                            return True
                        elif response.get("status") == "error":
                            print(f"Error from MCU: {response.get('message', 'Unknown error')}")
                            return False
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
                
                time.sleep(0.1)
            
            print("Warning: No acknowledgment received (timeout)")
            return False
            
        except Exception as e:
            print(f"Error sending parameters via serial: {e}")
            return False
    
    def send_parameters_mqtt(self, pid_params: Dict[str, float]) -> bool:
        """
        Send PID parameters via MQTT
        
        Args:
            pid_params: Dictionary with Kp, Ki, Kd values
            
        Returns:
            True if parameters sent successfully
        """
        if not self.mqtt_client:
            print("Error: MQTT client not initialized")
            return False
        
        try:
            # Format command
            command = {
                "cmd": "set_pid",
                "Kp": float(pid_params.get('Kp', 0)),
                "Ki": float(pid_params.get('Ki', 0)),
                "Kd": float(pid_params.get('Kd', 0))
            }
            
            # Send command
            self.ack_received = False
            self.mqtt_client.publish(config.MQTT_TOPIC_PARAMS, json.dumps(command))
            print(f"Sent PID parameters via MQTT: Kp={command['Kp']:.4f}, "
                  f"Ki={command['Ki']:.4f}, Kd={command['Kd']:.4f}")
            
            # Wait for acknowledgment
            timeout = 5.0
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.ack_received:
                    print("Parameters updated successfully")
                    return True
                time.sleep(0.1)
            
            print("Warning: No acknowledgment received (timeout)")
            return False
            
        except Exception as e:
            print(f"Error sending parameters via MQTT: {e}")
            return False
    
    def download_parameters(self, pid_params: Dict[str, float]) -> bool:
        """
        Download PID parameters to MCU
        
        Args:
            pid_params: Dictionary with Kp, Ki, Kd values
            
        Returns:
            True if parameters downloaded successfully
        """
        if self.use_mqtt and self.mqtt_client:
            return self.send_parameters_mqtt(pid_params)
        elif self.serial_conn and self.serial_conn.is_open:
            return self.send_parameters_serial(pid_params)
        else:
            print("Error: No active connection")
            return False
    
    def verify_parameters(self) -> Optional[Dict[str, float]]:
        """
        Read back parameters from MCU to verify
        
        Returns:
            Dictionary with current PID parameters or None on failure
        """
        command = {"cmd": "get_pid"}
        
        if self.use_mqtt and self.mqtt_client:
            # MQTT readback implementation
            self.mqtt_client.publish(config.MQTT_TOPIC_PARAMS, json.dumps(command))
            # Would need to implement response handling
            print("MQTT parameter verification not fully implemented")
            return None
            
        elif self.serial_conn and self.serial_conn.is_open:
            try:
                # Send get command
                cmd_str = json.dumps(command) + "\n"
                self.serial_conn.write(cmd_str.encode())
                
                # Wait for response
                timeout = 3.0
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    if self.serial_conn.in_waiting:
                        try:
                            line = self.serial_conn.readline().decode().strip()
                            response = json.loads(line)
                            
                            if "Kp" in response:
                                print(f"Current MCU parameters: Kp={response['Kp']:.4f}, "
                                      f"Ki={response['Ki']:.4f}, Kd={response['Kd']:.4f}")
                                return response
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
                    
                    time.sleep(0.1)
                
                print("Warning: No response received for parameter readback")
                return None
                
            except Exception as e:
                print(f"Error verifying parameters: {e}")
                return None
        else:
            print("Error: No active connection")
            return None
    
    def disconnect(self):
        """Close all connections"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Serial connection closed")
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            print("MQTT connection closed")


def download_pid_parameters(pid_params: Dict[str, float], use_mqtt: bool = False,
                           verify: bool = True) -> bool:
    """
    Convenience function to download PID parameters to MCU
    
    Args:
        pid_params: Dictionary with Kp, Ki, Kd values
        use_mqtt: Whether to use MQTT instead of serial
        verify: Whether to verify parameters after download
        
    Returns:
        True if download successful
    """
    downloader = ParameterDownloader(use_mqtt=use_mqtt)
    
    # Connect
    if use_mqtt:
        if not downloader.connect_mqtt():
            return False
    else:
        if not downloader.connect_serial():
            return False
    
    # Download parameters
    success = downloader.download_parameters(pid_params)
    
    # Verify if requested
    if success and verify and not use_mqtt:
        time.sleep(0.5)
        current_params = downloader.verify_parameters()
        if current_params:
            # Check if parameters match (within tolerance)
            tolerance = 0.001
            matches = (
                abs(current_params['Kp'] - pid_params['Kp']) < tolerance and
                abs(current_params['Ki'] - pid_params['Ki']) < tolerance and
                abs(current_params['Kd'] - pid_params['Kd']) < tolerance
            )
            if not matches:
                print("Warning: Verified parameters don't match sent parameters")
                success = False
    
    # Disconnect
    downloader.disconnect()
    
    return success


if __name__ == "__main__":
    # Test parameter download
    print("Testing parameter download skill...")
    
    pid_params = {
        'Kp': 1.5,
        'Ki': 0.8,
        'Kd': 0.2
    }
    
    # Note: This will fail without actual hardware connection
    success = download_pid_parameters(pid_params, use_mqtt=False, verify=False)
    
    if success:
        print("Parameters downloaded successfully!")
    else:
        print("Failed to download parameters (expected without hardware)")
