"""
System Identification Skill
Analyzes step response data to classify system dynamics (1st order, 2nd order, etc.)
"""
import numpy as np
from scipy import signal
from scipy.optimize import curve_fit
from typing import Dict, Tuple, Optional
import config


class SystemIdentifier:
    """Identifies system dynamics from step response data"""
    
    def __init__(self):
        self.system_type = None
        self.parameters = {}
        self.fit_quality = 0.0
    
    @staticmethod
    def first_order_step_response(t, K, tau, td=0):
        """
        First-order system step response: K * (1 - exp(-(t-td)/tau))
        
        Args:
            t: Time array
            K: System gain
            tau: Time constant
            td: Time delay
            
        Returns:
            Step response values
        """
        response = np.zeros_like(t)
        mask = t >= td
        response[mask] = K * (1 - np.exp(-(t[mask] - td) / tau))
        return response
    
    @staticmethod
    def second_order_step_response(t, K, wn, zeta, td=0):
        """
        Second-order system step response
        
        Args:
            t: Time array
            K: System gain
            wn: Natural frequency
            zeta: Damping ratio
            td: Time delay
            
        Returns:
            Step response values
        """
        response = np.zeros_like(t)
        mask = t >= td
        t_shifted = t[mask] - td
        
        if zeta < 1:  # Underdamped
            wd = wn * np.sqrt(1 - zeta**2)
            response[mask] = K * (1 - np.exp(-zeta * wn * t_shifted) * 
                                 (np.cos(wd * t_shifted) + 
                                  (zeta / np.sqrt(1 - zeta**2)) * np.sin(wd * t_shifted)))
        elif zeta == 1:  # Critically damped
            response[mask] = K * (1 - np.exp(-wn * t_shifted) * (1 + wn * t_shifted))
        else:  # Overdamped
            s1 = -zeta * wn + wn * np.sqrt(zeta**2 - 1)
            s2 = -zeta * wn - wn * np.sqrt(zeta**2 - 1)
            response[mask] = K * (1 + (s1 * np.exp(s2 * t_shifted) - 
                                       s2 * np.exp(s1 * t_shifted)) / (s2 - s1))
        
        return response
    
    def fit_first_order(self, time: np.ndarray, output: np.ndarray) -> Tuple[Dict, float]:
        """
        Fit first-order model to data
        
        Args:
            time: Time array
            output: System output array
            
        Returns:
            Tuple of (parameters dict, R-squared value)
        """
        try:
            # Normalize output to start from 0
            y0 = output[0]
            y_normalized = output - y0
            
            # Initial guess
            K_guess = y_normalized[-1]
            tau_guess = time[len(time) // 2]
            
            # Dynamic bounds based on data
            tau_max = max(10, time[-1] * 2)
            td_max = max(1, time[-1] * 0.5)
            
            # Fit model
            popt, _ = curve_fit(
                self.first_order_step_response,
                time,
                y_normalized,
                p0=[K_guess, tau_guess, 0],
                bounds=([0, 0.001, 0], [np.inf, tau_max, td_max]),
                maxfev=5000
            )
            
            K, tau, td = popt
            
            # Calculate R-squared
            y_pred = self.first_order_step_response(time, K, tau, td)
            ss_res = np.sum((y_normalized - y_pred)**2)
            ss_tot = np.sum((y_normalized - np.mean(y_normalized))**2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            parameters = {
                'gain': K,
                'time_constant': tau,
                'time_delay': td,
                'steady_state_offset': y0
            }
            
            return parameters, r_squared
            
        except Exception as e:
            print(f"Error fitting first-order model: {e}")
            return {}, 0.0
    
    def fit_second_order(self, time: np.ndarray, output: np.ndarray) -> Tuple[Dict, float]:
        """
        Fit second-order model to data
        
        Args:
            time: Time array
            output: System output array
            
        Returns:
            Tuple of (parameters dict, R-squared value)
        """
        try:
            # Normalize output to start from 0
            y0 = output[0]
            y_normalized = output - y0
            
            # Initial guess
            K_guess = y_normalized[-1]
            wn_guess = 10.0
            zeta_guess = 0.5
            
            # Fit model
            popt, _ = curve_fit(
                self.second_order_step_response,
                time,
                y_normalized,
                p0=[K_guess, wn_guess, zeta_guess, 0],
                bounds=([0, 0.1, 0, 0], [np.inf, 100, 2, 1]),
                maxfev=5000
            )
            
            K, wn, zeta, td = popt
            
            # Calculate R-squared
            y_pred = self.second_order_step_response(time, K, wn, zeta, td)
            ss_res = np.sum((y_normalized - y_pred)**2)
            ss_tot = np.sum((y_normalized - np.mean(y_normalized))**2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            parameters = {
                'gain': K,
                'natural_frequency': wn,
                'damping_ratio': zeta,
                'time_delay': td,
                'steady_state_offset': y0
            }
            
            return parameters, r_squared
            
        except Exception as e:
            print(f"Error fitting second-order model: {e}")
            return {}, 0.0
    
    def identify_system(self, data: Dict[str, np.ndarray]) -> Dict:
        """
        Identify system type and parameters from step response data
        
        Args:
            data: Dictionary with 'time', 'setpoint', and 'output' arrays
            
        Returns:
            Dictionary containing system identification results
        """
        time = data['time']
        output = data['output']
        
        # Fit both models
        first_order_params, first_order_r2 = self.fit_first_order(time, output)
        second_order_params, second_order_r2 = self.fit_second_order(time, output)
        
        # Select best model
        if second_order_r2 > first_order_r2 and second_order_r2 > config.SYSTEM_ORDER_THRESHOLD:
            self.system_type = "second_order"
            self.parameters = second_order_params
            self.fit_quality = second_order_r2
        else:
            self.system_type = "first_order"
            self.parameters = first_order_params
            self.fit_quality = first_order_r2
        
        result = {
            'system_type': self.system_type,
            'parameters': self.parameters,
            'fit_quality': self.fit_quality,
            'first_order_r2': first_order_r2,
            'second_order_r2': second_order_r2
        }
        
        print(f"\nSystem Identification Results:")
        print(f"  System Type: {self.system_type}")
        print(f"  Fit Quality (R²): {self.fit_quality:.4f}")
        print(f"  Parameters: {self.parameters}")
        
        return result
    
    def get_transfer_function(self) -> Optional[Tuple]:
        """
        Get transfer function representation of identified system
        
        Returns:
            Tuple of (numerator, denominator) coefficients or None
        """
        if not self.system_type or not self.parameters:
            return None
        
        if self.system_type == "first_order":
            K = self.parameters['gain']
            tau = self.parameters['time_constant']
            # G(s) = K / (tau*s + 1)
            num = [K]
            den = [tau, 1]
            return (num, den)
            
        elif self.system_type == "second_order":
            K = self.parameters['gain']
            wn = self.parameters['natural_frequency']
            zeta = self.parameters['damping_ratio']
            # G(s) = K*wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
            num = [K * wn**2]
            den = [1, 2 * zeta * wn, wn**2]
            return (num, den)
        
        return None


def identify_system(data: Dict[str, np.ndarray]) -> Dict:
    """
    Convenience function to identify system from step response data
    
    Args:
        data: Dictionary with 'time', 'setpoint', and 'output' arrays
        
    Returns:
        Dictionary containing system identification results
    """
    identifier = SystemIdentifier()
    return identifier.identify_system(data)


if __name__ == "__main__":
    # Test system identification with synthetic data
    print("Testing system identification skill...")
    
    # Generate synthetic first-order step response
    t = np.linspace(0, 5, 500)
    K, tau = 100, 0.5
    y = SystemIdentifier.first_order_step_response(t, K, tau) + np.random.normal(0, 1, len(t))
    
    data = {
        'time': t,
        'setpoint': np.ones_like(t) * 100,
        'output': y
    }
    
    result = identify_system(data)
    print(f"\nIdentified system type: {result['system_type']}")
    print(f"Fit quality: {result['fit_quality']:.4f}")
