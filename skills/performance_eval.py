"""
Performance Evaluation Skill
Computes performance metrics (overshoot, settling time, etc.) to assess controller performance
"""
import numpy as np
from typing import Dict, Optional
import config
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt


class PerformanceEvaluator:
    """Evaluates PID controller performance from step response data"""
    
    def __init__(self):
        self.metrics = {}
    
    def calculate_rise_time(self, time: np.ndarray, output: np.ndarray, 
                           setpoint: float, thresholds: tuple = (0.1, 0.9)) -> Optional[float]:
        """
        Calculate rise time (time to go from low% to high% of final value)
        
        Args:
            time: Time array
            output: System output array
            setpoint: Target setpoint value
            thresholds: (low%, high%) thresholds, default (10%, 90%)
            
        Returns:
            Rise time in seconds or None if cannot be calculated
        """
        try:
            final_value = setpoint
            low_threshold = final_value * thresholds[0]
            high_threshold = final_value * thresholds[1]
            
            # Find indices where thresholds are crossed
            low_idx = np.where(output >= low_threshold)[0]
            high_idx = np.where(output >= high_threshold)[0]
            
            if len(low_idx) > 0 and len(high_idx) > 0:
                rise_time = time[high_idx[0]] - time[low_idx[0]]
                return rise_time
            
            return None
        except Exception as e:
            print(f"Error calculating rise time: {e}")
            return None
    
    def calculate_overshoot(self, output: np.ndarray, setpoint: float) -> tuple:
        """
        Calculate peak overshoot
        
        Args:
            output: System output array
            setpoint: Target setpoint value
            
        Returns:
            Tuple of (overshoot_percent, peak_value)
        """
        try:
            peak_value = np.max(output)
            overshoot = peak_value - setpoint
            overshoot_percent = (overshoot / setpoint) * 100 if setpoint != 0 else 0
            
            return overshoot_percent, peak_value
        except Exception as e:
            print(f"Error calculating overshoot: {e}")
            return 0.0, setpoint
    
    def calculate_settling_time(self, time: np.ndarray, output: np.ndarray, 
                                setpoint: float, tolerance: float = 0.02) -> Optional[float]:
        """
        Calculate settling time (time to stay within tolerance% of setpoint)
        
        Args:
            time: Time array
            output: System output array
            setpoint: Target setpoint value
            tolerance: Settling tolerance as fraction (default 2%)
            
        Returns:
            Settling time in seconds or None if not settled
        """
        try:
            threshold = setpoint * tolerance
            
            # Find last time output leaves the tolerance band
            outside_band = np.abs(output - setpoint) > threshold
            
            if np.any(outside_band):
                last_outside_idx = np.where(outside_band)[0][-1]
                if last_outside_idx < len(time) - 1:
                    settling_time = time[last_outside_idx + 1]
                    return settling_time
            
            # If never outside band or settled from the start
            return time[0]
            
        except Exception as e:
            print(f"Error calculating settling time: {e}")
            return None
    
    def calculate_steady_state_error(self, output: np.ndarray, setpoint: float,
                                     last_samples: int = 50) -> tuple:
        """
        Calculate steady-state error
        
        Args:
            output: System output array
            setpoint: Target setpoint value
            last_samples: Number of final samples to average
            
        Returns:
            Tuple of (error_value, error_percent)
        """
        try:
            # Average last samples
            steady_state_value = np.mean(output[-last_samples:])
            error = setpoint - steady_state_value
            error_percent = (error / setpoint) * 100 if setpoint != 0 else 0
            
            return error, error_percent
        except Exception as e:
            print(f"Error calculating steady-state error: {e}")
            return 0.0, 0.0
    
    def calculate_iae(self, time: np.ndarray, output: np.ndarray, setpoint: float) -> float:
        """
        Calculate Integral of Absolute Error (IAE)
        
        Args:
            time: Time array
            output: System output array
            setpoint: Target setpoint value
            
        Returns:
            IAE value
        """
        try:
            error = np.abs(setpoint - output)
            # Use trapezoid for numpy >= 2.0, trapz for older versions
            try:
                iae = np.trapezoid(error, time)
            except AttributeError:
                iae = np.trapz(error, time)
            return iae
        except Exception as e:
            print(f"Error calculating IAE: {e}")
            return 0.0
    
    def calculate_itse(self, time: np.ndarray, output: np.ndarray, setpoint: float) -> float:
        """
        Calculate Integral of Time-weighted Squared Error (ITSE)
        
        Args:
            time: Time array
            output: System output array
            setpoint: Target setpoint value
            
        Returns:
            ITSE value
        """
        try:
            error = setpoint - output
            # Use trapezoid for numpy >= 2.0, trapz for older versions
            try:
                itse = np.trapezoid(time * error**2, time)
            except AttributeError:
                itse = np.trapz(time * error**2, time)
            return itse
        except Exception as e:
            print(f"Error calculating ITSE: {e}")
            return 0.0
    
    def evaluate_performance(self, data: Dict[str, np.ndarray]) -> Dict:
        """
        Evaluate overall controller performance
        
        Args:
            data: Dictionary with 'time', 'setpoint', and 'output' arrays
            
        Returns:
            Dictionary containing all performance metrics
        """
        time = data['time']
        output = data['output']
        setpoint = np.mean(data['setpoint'])  # Average setpoint
        
        # Calculate all metrics
        rise_time = self.calculate_rise_time(time, output, setpoint)
        overshoot_pct, peak_value = self.calculate_overshoot(output, setpoint)
        settling_time = self.calculate_settling_time(time, output, setpoint)
        ss_error, ss_error_pct = self.calculate_steady_state_error(output, setpoint)
        iae = self.calculate_iae(time, output, setpoint)
        itse = self.calculate_itse(time, output, setpoint)
        
        self.metrics = {
            'rise_time': rise_time,
            'overshoot_percent': overshoot_pct,
            'peak_value': peak_value,
            'settling_time': settling_time,
            'steady_state_error': ss_error,
            'steady_state_error_percent': ss_error_pct,
            'iae': iae,
            'itse': itse,
            'setpoint': setpoint
        }
        
        # Assess performance quality
        self.metrics['performance_assessment'] = self._assess_performance()
        
        print("\n" + "="*50)
        print("Performance Evaluation Results")
        print("="*50)
        print(f"Rise Time: {rise_time:.3f} s" if rise_time else "Rise Time: N/A")
        print(f"Overshoot: {overshoot_pct:.2f}%")
        print(f"Settling Time: {settling_time:.3f} s" if settling_time else "Settling Time: N/A")
        print(f"Steady-State Error: {ss_error_pct:.2f}%")
        print(f"IAE: {iae:.2f}")
        print(f"ITSE: {itse:.2f}")
        print(f"Assessment: {self.metrics['performance_assessment']}")
        print("="*50)
        
        return self.metrics
    
    def _assess_performance(self) -> str:
        """
        Assess overall performance quality
        
        Returns:
            Performance assessment string
        """
        issues = []
        
        # Check overshoot
        if self.metrics['overshoot_percent'] > config.MAX_OVERSHOOT_PERCENT:
            issues.append(f"High overshoot ({self.metrics['overshoot_percent']:.1f}%)")
        
        # Check settling time
        if self.metrics['settling_time'] and \
           self.metrics['settling_time'] > config.MAX_SETTLING_TIME:
            issues.append(f"Slow settling ({self.metrics['settling_time']:.2f}s)")
        
        # Check steady-state error
        if abs(self.metrics['steady_state_error_percent']) > config.STEADY_STATE_ERROR_THRESHOLD:
            issues.append(f"High SS error ({self.metrics['steady_state_error_percent']:.1f}%)")
        
        if not issues:
            return "EXCELLENT - All metrics within specifications"
        elif len(issues) == 1:
            return f"GOOD - Minor issue: {issues[0]}"
        else:
            return f"NEEDS IMPROVEMENT - Issues: {', '.join(issues)}"
    
    def plot_response(self, data: Dict[str, np.ndarray], filename: str = None):
        """
        Plot step response with annotations
        
        Args:
            data: Dictionary with 'time', 'setpoint', and 'output' arrays
            filename: Output filename (if None, uses default)
        """
        import os
        
        time = data['time']
        setpoint = data['setpoint']
        output = data['output']
        
        plt.figure(figsize=(10, 6))
        plt.plot(time, setpoint, 'r--', label='Setpoint', linewidth=2)
        plt.plot(time, output, 'b-', label='Output', linewidth=1.5)
        
        # Add metric annotations if available
        if self.metrics:
            # Mark overshoot
            if self.metrics['overshoot_percent'] > 0:
                peak_idx = np.argmax(output)
                plt.plot(time[peak_idx], output[peak_idx], 'ro', markersize=8)
                plt.annotate(f"Peak: {output[peak_idx]:.1f}\nOvershoot: {self.metrics['overshoot_percent']:.1f}%",
                           xy=(time[peak_idx], output[peak_idx]),
                           xytext=(time[peak_idx] + 0.2, output[peak_idx]),
                           fontsize=9)
            
            # Mark settling time
            if self.metrics['settling_time']:
                plt.axvline(x=self.metrics['settling_time'], color='g', 
                          linestyle=':', label=f"Settling time: {self.metrics['settling_time']:.2f}s")
        
        plt.xlabel('Time (s)', fontsize=12)
        plt.ylabel('Speed (RPM)', fontsize=12)
        plt.title('PID Controller Step Response', fontsize=14, fontweight='bold')
        plt.legend(loc='best')
        plt.grid(True, alpha=0.3)
        
        if filename is None:
            filename = "step_response.png"
        
        filepath = os.path.join(config.PLOTS_DIR, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Plot saved to: {filepath}")


def evaluate_performance(data: Dict[str, np.ndarray], plot: bool = True) -> Dict:
    """
    Convenience function to evaluate performance
    
    Args:
        data: Dictionary with 'time', 'setpoint', and 'output' arrays
        plot: Whether to generate plot
        
    Returns:
        Dictionary containing performance metrics
    """
    evaluator = PerformanceEvaluator()
    metrics = evaluator.evaluate_performance(data)
    
    if plot:
        evaluator.plot_response(data)
    
    return metrics


if __name__ == "__main__":
    # Test performance evaluation with synthetic data
    print("Testing performance evaluation skill...")
    
    # Generate synthetic step response
    t = np.linspace(0, 5, 500)
    setpoint = 1000
    # Second-order response with overshoot
    wn = 10
    zeta = 0.5
    output = setpoint * (1 - np.exp(-zeta * wn * t) * 
                        (np.cos(wn * np.sqrt(1 - zeta**2) * t) + 
                         (zeta / np.sqrt(1 - zeta**2)) * 
                         np.sin(wn * np.sqrt(1 - zeta**2) * t)))
    
    data = {
        'time': t,
        'setpoint': np.ones_like(t) * setpoint,
        'output': output + np.random.normal(0, 5, len(t))
    }
    
    metrics = evaluate_performance(data, plot=False)
    print(f"\nEvaluation complete!")
