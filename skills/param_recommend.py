"""
Parameter Recommendation Skill
Computes optimized PID parameters based on system model and desired performance
"""
import numpy as np
from typing import Dict, Tuple
import config


class PIDRecommender:
    """Recommends PID parameters based on system identification results"""
    
    def __init__(self):
        self.recommended_params = {}
    
    def ziegler_nichols_first_order(self, K: float, tau: float, td: float = 0) -> Dict[str, float]:
        """
        Ziegler-Nichols tuning for first-order system with time delay
        
        Args:
            K: System gain
            tau: Time constant
            td: Time delay
            
        Returns:
            Dictionary with Kp, Ki, Kd values
        """
        if td < 0.001:  # No significant delay
            # For pure first-order, use lambda tuning
            lambda_factor = 1.0  # Tuning parameter (1-3, smaller = aggressive)
            Kp = tau / (K * lambda_factor)
            Ti = tau
            Td = 0
        else:
            # Ziegler-Nichols for systems with delay
            Kp = (1.2 * tau) / (K * td)
            Ti = 2 * td
            Td = 0.5 * td
        
        Ki = Kp / Ti if Ti > 0 else 0
        Kd = Kp * Td
        
        return {
            'Kp': Kp,
            'Ki': Ki,
            'Kd': Kd,
            'method': 'Ziegler-Nichols (First Order)'
        }
    
    def chien_hrones_reswick_first_order(self, K: float, tau: float, td: float, 
                                         setpoint_regulation: bool = True) -> Dict[str, float]:
        """
        Chien-Hrones-Reswick tuning for first-order system
        
        Args:
            K: System gain
            tau: Time constant
            td: Time delay
            setpoint_regulation: True for setpoint tracking, False for disturbance rejection
            
        Returns:
            Dictionary with Kp, Ki, Kd values
        """
        if td < 0.001:
            td = 0.01  # Minimum delay to avoid division by zero
        
        if setpoint_regulation:
            # 0% overshoot setpoint response
            Kp = (0.6 * tau) / (K * td)
            Ti = tau
            Td = 0.5 * td
        else:
            # 0% overshoot disturbance response
            Kp = (0.95 * tau) / (K * td)
            Ti = 2.4 * td
            Td = 0.42 * td
        
        Ki = Kp / Ti if Ti > 0 else 0
        Kd = Kp * Td
        
        return {
            'Kp': Kp,
            'Ki': Ki,
            'Kd': Kd,
            'method': 'Chien-Hrones-Reswick (First Order)'
        }
    
    def pole_placement_second_order(self, wn: float, zeta: float, K: float,
                                    desired_settling_time: float = None) -> Dict[str, float]:
        """
        Pole placement tuning for second-order system
        
        Args:
            wn: Natural frequency
            zeta: Damping ratio
            K: System gain
            desired_settling_time: Desired settling time (if None, uses config)
            
        Returns:
            Dictionary with Kp, Ki, Kd values
        """
        if desired_settling_time is None:
            desired_settling_time = config.MAX_SETTLING_TIME
        
        # Desired closed-loop characteristics
        desired_zeta = 0.707  # Critical damping
        desired_wn = 4.6 / (desired_zeta * desired_settling_time)  # 2% settling time
        
        # PID controller design for second-order plant
        # Assuming plant: G(s) = K*wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
        
        # Calculate PID gains
        Kp = (2 * desired_zeta * desired_wn - 2 * zeta * wn) / (K * wn**2)
        Ki = (desired_wn**2 - wn**2) / (K * wn**2)
        # Derivative gain for desired closed-loop response
        Kd = (desired_wn**2 / (K * wn**2) - 1) / (desired_wn)
        Kd = max(0, Kd)
        
        # Ensure positive gains
        Kp = max(0.1, Kp)
        Ki = max(0.01, Ki)
        
        return {
            'Kp': Kp,
            'Ki': Ki,
            'Kd': Kd,
            'method': 'Pole Placement (Second Order)'
        }
    
    def imc_tuning(self, system_params: Dict, filter_time: float = None) -> Dict[str, float]:
        """
        Internal Model Control (IMC) tuning
        
        Args:
            system_params: System identification parameters
            filter_time: IMC filter time constant (if None, auto-computed)
            
        Returns:
            Dictionary with Kp, Ki, Kd values
        """
        system_type = system_params.get('system_type', 'first_order')
        
        if system_type == 'first_order':
            K = system_params['gain']
            tau = system_params['time_constant']
            td = system_params.get('time_delay', 0)
            
            if filter_time is None:
                filter_time = max(tau, td)
            
            Kp = tau / (K * filter_time)
            Ki = Kp / tau
            Kd = 0
            
        else:  # second_order
            K = system_params['gain']
            wn = system_params['natural_frequency']
            zeta = system_params['damping_ratio']
            
            if filter_time is None:
                filter_time = 1.0 / wn
            
            tau_eq = 2 * zeta / wn
            Kp = tau_eq / (K * filter_time)
            Ki = Kp / tau_eq
            Kd = 0
        
        return {
            'Kp': Kp,
            'Ki': Ki,
            'Kd': Kd,
            'method': 'IMC'
        }
    
    def recommend_pid(self, system_id_result: Dict, tuning_method: str = 'auto') -> Dict[str, float]:
        """
        Recommend PID parameters based on system identification
        
        Args:
            system_id_result: Result from system identification
            tuning_method: Tuning method ('auto', 'zn', 'chr', 'pole', 'imc')
            
        Returns:
            Dictionary with recommended PID parameters
        """
        system_type = system_id_result.get('system_type')
        parameters = system_id_result.get('parameters', {})
        
        if not system_type or not parameters:
            print("Error: Invalid system identification result")
            return {}
        
        print(f"\nComputing PID parameters for {system_type} system...")
        
        # Collect multiple tuning suggestions
        suggestions = []
        
        if system_type == 'first_order':
            K = parameters['gain']
            tau = parameters['time_constant']
            td = parameters.get('time_delay', 0)
            
            # Try multiple methods
            suggestions.append(self.ziegler_nichols_first_order(K, tau, td))
            suggestions.append(self.chien_hrones_reswick_first_order(K, tau, td, True))
            suggestions.append(self.imc_tuning({'system_type': 'first_order', **parameters}))
            
        else:  # second_order
            K = parameters['gain']
            wn = parameters['natural_frequency']
            zeta = parameters['damping_ratio']
            
            suggestions.append(self.pole_placement_second_order(wn, zeta, K))
            suggestions.append(self.imc_tuning({'system_type': 'second_order', **parameters}))
        
        # Select best suggestion based on method
        if tuning_method == 'auto':
            # Use first suggestion (typically most conservative)
            self.recommended_params = suggestions[0]
        else:
            # Find matching method
            method_map = {'zn': 'Ziegler-Nichols', 'chr': 'Chien-Hrones-Reswick', 
                         'pole': 'Pole Placement', 'imc': 'IMC'}
            target = method_map.get(tuning_method, '')
            
            for suggestion in suggestions:
                if target.lower() in suggestion['method'].lower():
                    self.recommended_params = suggestion
                    break
            else:
                self.recommended_params = suggestions[0]
        
        print(f"Recommended PID Parameters ({self.recommended_params['method']}):")
        print(f"  Kp = {self.recommended_params['Kp']:.4f}")
        print(f"  Ki = {self.recommended_params['Ki']:.4f}")
        print(f"  Kd = {self.recommended_params['Kd']:.4f}")
        
        return self.recommended_params


def recommend_pid(system_id_result: Dict, tuning_method: str = 'auto') -> Dict[str, float]:
    """
    Convenience function to recommend PID parameters
    
    Args:
        system_id_result: Result from system identification
        tuning_method: Tuning method to use
        
    Returns:
        Dictionary with recommended PID parameters
    """
    recommender = PIDRecommender()
    return recommender.recommend_pid(system_id_result, tuning_method)


if __name__ == "__main__":
    # Test parameter recommendation
    print("Testing parameter recommendation skill...")
    
    # Example first-order system
    system_id = {
        'system_type': 'first_order',
        'parameters': {
            'gain': 100.0,
            'time_constant': 0.5,
            'time_delay': 0.1
        }
    }
    
    pid_params = recommend_pid(system_id)
    print(f"\nRecommended parameters: {pid_params}")
    
    # Example second-order system
    system_id2 = {
        'system_type': 'second_order',
        'parameters': {
            'gain': 100.0,
            'natural_frequency': 10.0,
            'damping_ratio': 0.3
        }
    }
    
    pid_params2 = recommend_pid(system_id2)
    print(f"\nRecommended parameters: {pid_params2}")
