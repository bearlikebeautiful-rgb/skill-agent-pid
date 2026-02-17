"""
Data Collection Skill
Fetches system step response data from STM32 MCU via USB Serial or MQTT
"""
import serial
import time
import json
import numpy as np
from typing import Dict, List, Optional, Tuple
import config

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("Warning: paho-mqtt not available. MQTT functionality will be disabled.")


class DataCollector:
    """Collects step response data from STM32 MCU"""
    
    def __init__(self, use_mqtt: bool = False):
        """
        Initialize data collector
        
        Args:
            use_mqtt: If True, use MQTT instead of serial communication
        """
        self.use_mqtt = use_mqtt and config.MQTT_ENABLED and MQTT_AVAILABLE
        self.serial_conn = None
        self.mqtt_client = None
        self.mqtt_data = []
        
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
            try:
                self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
            except (TypeError, AttributeError):
                self.mqtt_client = mqtt.Client()
            
            if config.MQTT_USERNAME and config.MQTT_PASSWORD:
                self.mqtt_client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
            
            self.mqtt_client.on_message = self._on_mqtt_message
            self.mqtt_client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
            self.mqtt_client.subscribe(config.MQTT_TOPIC_DATA)
            self.mqtt_client.loop_start()
            print(f"MQTT connection established to {config.MQTT_BROKER}")
            return True
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            return False
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Callback for receiving MQTT messages"""
        try:
            data = json.loads(msg.payload.decode())
            self.mqtt_data.append(data)
        except Exception as e:
            print(f"Error parsing MQTT message: {e}")
    
    def request_step_response(self, setpoint: float, amplitude: float) -> bool:
        """
        Request step response data from MCU
        
        Args:
            setpoint: Target setpoint for step response
            amplitude: Step amplitude
            
        Returns:
            True if request sent successfully
        """
        command = {
            "cmd": "step_response",
            "setpoint": setpoint,
            "amplitude": amplitude,
            "duration": config.STEP_RESPONSE_DURATION
        }
        
        if self.use_mqtt and self.mqtt_client:
            self.mqtt_client.publish(config.MQTT_TOPIC_PARAMS, json.dumps(command))
            print("Step response request sent via MQTT")
            return True
        elif self.serial_conn and self.serial_conn.is_open:
            cmd_str = json.dumps(command) + "\n"
            self.serial_conn.write(cmd_str.encode())
            print("Step response request sent via Serial")
            return True
        else:
            print("Error: No active connection")
            return False
    
    def collect_data(self, duration: float = None) -> Dict[str, np.ndarray]:
        """
        Collect step response data
        
        Args:
            duration: Duration to collect data (seconds). If None, uses config default
            
        Returns:
            Dictionary containing time, setpoint, and output arrays
        """
        if duration is None:
            duration = config.STEP_RESPONSE_DURATION
        
        time_data = []
        setpoint_data = []
        output_data = []
        
        if self.use_mqtt and self.mqtt_client:
            # Clear previous data
            self.mqtt_data = []
            start_time = time.time()
            
            # Wait for data collection
            while time.time() - start_time < duration:
                time.sleep(0.1)
            
            # Parse collected data
            for sample in self.mqtt_data:
                time_data.append(sample.get("time", 0))
                setpoint_data.append(sample.get("setpoint", 0))
                output_data.append(sample.get("output", 0))
                
        elif self.serial_conn and self.serial_conn.is_open:
            start_time = time.time()
            
            while time.time() - start_time < duration:
                try:
                    if self.serial_conn.in_waiting:
                        line = self.serial_conn.readline().decode().strip()
                        data = json.loads(line)
                        time_data.append(data.get("time", 0))
                        setpoint_data.append(data.get("setpoint", 0))
                        output_data.append(data.get("output", 0))
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    continue  # Skip invalid data
                except Exception as e:
                    print(f"Error reading data: {e}")
                    break
        else:
            print("Error: No active connection")
            return {}
        
        result = {
            "time": np.array(time_data),
            "setpoint": np.array(setpoint_data),
            "output": np.array(output_data)
        }
        
        print(f"Collected {len(time_data)} data points")
        return result
    
    def disconnect(self):
        """Close all connections"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Serial connection closed")
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            print("MQTT connection closed")
    
    def save_data(self, data: Dict[str, np.ndarray], filename: str):
        """
        Save collected data to file
        
        Args:
            data: Dictionary containing time, setpoint, and output arrays
            filename: Output filename
        """
        import os
        filepath = os.path.join(config.DATA_DIR, filename)
        np.savez(filepath, **data)
        print(f"Data saved to {filepath}")


def collect_step_response(setpoint: float = None, amplitude: float = None, 
                          use_mqtt: bool = False) -> Optional[Dict[str, np.ndarray]]:
    """
    Convenience function to collect step response data
    
    Args:
        setpoint: Target setpoint (uses config default if None)
        amplitude: Step amplitude (uses config default if None)
        use_mqtt: Whether to use MQTT instead of serial
        
    Returns:
        Dictionary containing collected data or None on failure
    """
    if setpoint is None:
        setpoint = config.DEFAULT_SETPOINT
    if amplitude is None:
        amplitude = config.STEP_INPUT_AMPLITUDE
    
    collector = DataCollector(use_mqtt=use_mqtt)
    
    # Connect
    if use_mqtt:
        if not collector.connect_mqtt():
            return None
    else:
        if not collector.connect_serial():
            return None
    
    # Request and collect data
    if not collector.request_step_response(setpoint, amplitude):
        collector.disconnect()
        return None
    
    # Wait a moment for MCU to prepare
    time.sleep(0.5)
    
    # Collect data
    data = collector.collect_data()
    
    # Disconnect
    collector.disconnect()
    
    return data if len(data.get("time", [])) > 0 else None


if __name__ == "__main__":
    # Test data collection
    print("Testing data collection skill...")
    data = collect_step_response()
    
    if data:
        print(f"Successfully collected {len(data['time'])} samples")
        print(f"Time range: {data['time'][0]:.3f} to {data['time'][-1]:.3f} seconds")
    else:
        print("Failed to collect data")
