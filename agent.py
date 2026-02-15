"""
Main Agent Orchestration Script
Interfaces with Claude Opus 4.6 LLM for PID tuning workflow orchestration
"""
import os
import sys
import json
import logging
from typing import Dict, Optional, List

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic package not installed. Claude API features will be disabled.")
    print("Install with: pip install anthropic")

import config
from skills.data_collect import collect_step_response
from skills.system_identify import identify_system
from skills.param_recommend import recommend_pid
from skills.code_generate import generate_pid_code
from skills.performance_eval import evaluate_performance
from skills.param_download import download_pid_parameters


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SkillAgentPID:
    """Main orchestration agent for PID tuning workflow"""
    
    def __init__(self, use_mqtt: bool = False):
        """
        Initialize the Skill-Agent PID framework
        
        Args:
            use_mqtt: Use MQTT instead of serial communication
        """
        self.use_mqtt = use_mqtt
        self.client = None
        self.conversation_history = []
        
        # Initialize Claude client
        if config.CLAUDE_API_KEY and ANTHROPIC_AVAILABLE:
            try:
                self.client = Anthropic(api_key=config.CLAUDE_API_KEY)
                logger.info("Claude API client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}")
                print("Warning: Claude API not available. Running in manual mode.")
        else:
            if not ANTHROPIC_AVAILABLE:
                logger.warning("Anthropic package not installed. Running in manual mode.")
                print("Note: Install anthropic package for Claude API support: pip install anthropic")
            else:
                logger.warning("Claude API key not set. Running in manual mode.")
                print("Warning: Claude API key not set in config. Set CLAUDE_API_KEY environment variable.")
        
        # Workflow state
        self.collected_data = None
        self.system_model = None
        self.pid_parameters = None
        self.performance_metrics = None
    
    def ask_claude(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """
        Send a query to Claude Opus 4.6
        
        Args:
            prompt: User prompt to send
            system_prompt: Optional system prompt
            
        Returns:
            Claude's response or None if unavailable
        """
        if not self.client:
            logger.warning("Claude client not available")
            return None
        
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": prompt
            })
            
            # Create message
            if system_prompt:
                response = self.client.messages.create(
                    model=config.CLAUDE_MODEL,
                    max_tokens=config.CLAUDE_MAX_TOKENS,
                    temperature=config.CLAUDE_TEMPERATURE,
                    system=system_prompt,
                    messages=self.conversation_history
                )
            else:
                response = self.client.messages.create(
                    model=config.CLAUDE_MODEL,
                    max_tokens=config.CLAUDE_MAX_TOKENS,
                    temperature=config.CLAUDE_TEMPERATURE,
                    messages=self.conversation_history
                )
            
            # Extract response
            assistant_message = response.content[0].text
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            logger.info(f"Received response from Claude ({len(assistant_message)} chars)")
            return assistant_message
            
        except Exception as e:
            logger.error(f"Error querying Claude: {e}")
            return None
    
    def step_1_data_collection(self) -> bool:
        """
        Step 1: Collect step response data from MCU
        
        Returns:
            True if successful
        """
        logger.info("="*60)
        logger.info("STEP 1: Data Collection")
        logger.info("="*60)
        
        print("\n" + "="*60)
        print("STEP 1: Collecting Step Response Data from MCU")
        print("="*60)
        
        # Collect data
        self.collected_data = collect_step_response(
            setpoint=config.DEFAULT_SETPOINT,
            amplitude=config.STEP_INPUT_AMPLITUDE,
            use_mqtt=self.use_mqtt
        )
        
        if self.collected_data and len(self.collected_data.get('time', [])) > 0:
            logger.info(f"Successfully collected {len(self.collected_data['time'])} data points")
            print(f"✓ Collected {len(self.collected_data['time'])} data points")
            return True
        else:
            logger.error("Failed to collect data")
            print("✗ Data collection failed")
            return False
    
    def step_2_system_identification(self) -> bool:
        """
        Step 2: Identify system dynamics
        
        Returns:
            True if successful
        """
        logger.info("="*60)
        logger.info("STEP 2: System Identification")
        logger.info("="*60)
        
        print("\n" + "="*60)
        print("STEP 2: Identifying System Dynamics")
        print("="*60)
        
        if not self.collected_data:
            logger.error("No data available for system identification")
            print("✗ No data available")
            return False
        
        # Identify system
        self.system_model = identify_system(self.collected_data)
        
        if self.system_model and self.system_model.get('system_type'):
            logger.info(f"System identified as: {self.system_model['system_type']}")
            logger.info(f"Fit quality: {self.system_model['fit_quality']:.4f}")
            print(f"✓ System type: {self.system_model['system_type']}")
            print(f"✓ Fit quality (R²): {self.system_model['fit_quality']:.4f}")
            
            # Ask Claude for interpretation if available
            if self.client:
                prompt = f"""I have identified a control system from step response data.
                
System Type: {self.system_model['system_type']}
Parameters: {json.dumps(self.system_model['parameters'], indent=2)}
Fit Quality (R²): {self.system_model['fit_quality']:.4f}

Please provide a brief analysis of this system's characteristics and what this means for PID tuning."""
                
                response = self.ask_claude(prompt, system_prompt="You are an expert in control systems and PID tuning.")
                if response:
                    print(f"\nClaude's Analysis:\n{response}\n")
            
            return True
        else:
            logger.error("System identification failed")
            print("✗ System identification failed")
            return False
    
    def step_3_parameter_recommendation(self, method: str = 'auto') -> bool:
        """
        Step 3: Recommend PID parameters
        
        Args:
            method: Tuning method to use
            
        Returns:
            True if successful
        """
        logger.info("="*60)
        logger.info("STEP 3: Parameter Recommendation")
        logger.info("="*60)
        
        print("\n" + "="*60)
        print("STEP 3: Computing Optimal PID Parameters")
        print("="*60)
        
        if not self.system_model:
            logger.error("No system model available")
            print("✗ No system model available")
            return False
        
        # Recommend parameters
        self.pid_parameters = recommend_pid(self.system_model, method)
        
        if self.pid_parameters and 'Kp' in self.pid_parameters:
            logger.info(f"PID parameters recommended: {self.pid_parameters}")
            print(f"✓ Recommended PID Parameters:")
            print(f"   Kp = {self.pid_parameters['Kp']:.6f}")
            print(f"   Ki = {self.pid_parameters['Ki']:.6f}")
            print(f"   Kd = {self.pid_parameters['Kd']:.6f}")
            print(f"   Method: {self.pid_parameters.get('method', 'Unknown')}")
            
            # Ask Claude for validation if available
            if self.client:
                prompt = f"""I have computed PID parameters for the identified system.

PID Parameters:
- Kp = {self.pid_parameters['Kp']:.6f}
- Ki = {self.pid_parameters['Ki']:.6f}
- Kd = {self.pid_parameters['Kd']:.6f}
- Tuning Method: {self.pid_parameters.get('method', 'Unknown')}

System Type: {self.system_model['system_type']}

Do these parameters look reasonable? Any concerns or suggestions for adjustment?"""
                
                response = self.ask_claude(prompt)
                if response:
                    print(f"\nClaude's Validation:\n{response}\n")
            
            return True
        else:
            logger.error("Parameter recommendation failed")
            print("✗ Parameter recommendation failed")
            return False
    
    def step_4_code_generation(self) -> bool:
        """
        Step 4: Generate C code for STM32
        
        Returns:
            True if successful
        """
        logger.info("="*60)
        logger.info("STEP 4: Code Generation")
        logger.info("="*60)
        
        print("\n" + "="*60)
        print("STEP 4: Generating STM32 C Code")
        print("="*60)
        
        if not self.pid_parameters:
            logger.error("No PID parameters available")
            print("✗ No PID parameters available")
            return False
        
        # Generate code
        output_dir = "stm32_code/generated"
        code_files = generate_pid_code(self.pid_parameters, output_dir)
        
        if code_files:
            logger.info(f"Generated {len(code_files)} code files")
            print(f"✓ Generated {len(code_files)} C code files:")
            for filename in code_files.keys():
                print(f"   - {output_dir}/{filename}")
            return True
        else:
            logger.error("Code generation failed")
            print("✗ Code generation failed")
            return False
    
    def step_5_parameter_download(self, skip_on_failure: bool = True) -> bool:
        """
        Step 5: Download parameters to MCU
        
        Args:
            skip_on_failure: Skip and continue if download fails
            
        Returns:
            True if successful or skipped
        """
        logger.info("="*60)
        logger.info("STEP 5: Parameter Download")
        logger.info("="*60)
        
        print("\n" + "="*60)
        print("STEP 5: Downloading Parameters to MCU")
        print("="*60)
        
        if not self.pid_parameters:
            logger.error("No PID parameters available")
            print("✗ No PID parameters available")
            return False
        
        # Download parameters
        success = download_pid_parameters(
            self.pid_parameters,
            use_mqtt=self.use_mqtt,
            verify=True
        )
        
        if success:
            logger.info("Parameters downloaded successfully")
            print("✓ Parameters downloaded to MCU")
            return True
        else:
            logger.warning("Parameter download failed")
            print("✗ Parameter download failed (hardware may not be connected)")
            if skip_on_failure:
                print("  Continuing anyway...")
                return True
            return False
    
    def step_6_performance_evaluation(self) -> bool:
        """
        Step 6: Evaluate controller performance
        
        Returns:
            True if successful
        """
        logger.info("="*60)
        logger.info("STEP 6: Performance Evaluation")
        logger.info("="*60)
        
        print("\n" + "="*60)
        print("STEP 6: Evaluating Controller Performance")
        print("="*60)
        
        # For now, evaluate on collected data
        # In real scenario, would collect new data after downloading parameters
        if not self.collected_data:
            logger.error("No data available for evaluation")
            print("✗ No data available")
            return False
        
        # Evaluate performance
        self.performance_metrics = evaluate_performance(self.collected_data, plot=True)
        
        if self.performance_metrics:
            logger.info(f"Performance evaluation complete")
            print(f"✓ Performance evaluation complete")
            
            # Ask Claude for assessment if available
            if self.client:
                prompt = f"""I have evaluated the PID controller performance with the following metrics:

{json.dumps(self.performance_metrics, indent=2, default=str)}

Assessment: {self.performance_metrics.get('performance_assessment', 'N/A')}

Based on these metrics, should we:
1. Accept these parameters
2. Iterate and try different tuning
3. Adjust specific parameters

Please provide your recommendation."""
                
                response = self.ask_claude(prompt)
                if response:
                    print(f"\nClaude's Assessment:\n{response}\n")
            
            return True
        else:
            logger.error("Performance evaluation failed")
            print("✗ Performance evaluation failed")
            return False
    
    def run_full_tuning_cycle(self) -> bool:
        """
        Execute complete PID tuning workflow
        
        Returns:
            True if all steps successful
        """
        logger.info("\n" + "="*70)
        logger.info("STARTING SKILL-AGENT PID TUNING WORKFLOW")
        logger.info("="*70)
        
        print("\n" + "="*70)
        print("SKILL-AGENT PID TUNING FRAMEWORK")
        print("STM32F103 BLDC Motor Speed Control")
        print("="*70)
        
        # Execute workflow steps
        steps = [
            ("Data Collection", self.step_1_data_collection),
            ("System Identification", self.step_2_system_identification),
            ("Parameter Recommendation", self.step_3_parameter_recommendation),
            ("Code Generation", self.step_4_code_generation),
            ("Parameter Download", lambda: self.step_5_parameter_download(skip_on_failure=True)),
            ("Performance Evaluation", self.step_6_performance_evaluation)
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                logger.error(f"Workflow failed at: {step_name}")
                print(f"\n✗ Workflow failed at: {step_name}")
                return False
        
        logger.info("="*70)
        logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        
        print("\n" + "="*70)
        print("✓ TUNING WORKFLOW COMPLETED SUCCESSFULLY")
        print("="*70)
        
        return True
    
    def print_summary(self):
        """Print workflow summary"""
        print("\n" + "="*70)
        print("TUNING SUMMARY")
        print("="*70)
        
        if self.system_model:
            print(f"\nSystem Type: {self.system_model.get('system_type', 'N/A')}")
            print(f"Fit Quality: {self.system_model.get('fit_quality', 0):.4f}")
        
        if self.pid_parameters:
            print(f"\nPID Parameters:")
            print(f"  Kp = {self.pid_parameters.get('Kp', 0):.6f}")
            print(f"  Ki = {self.pid_parameters.get('Ki', 0):.6f}")
            print(f"  Kd = {self.pid_parameters.get('Kd', 0):.6f}")
            print(f"  Method: {self.pid_parameters.get('method', 'N/A')}")
        
        if self.performance_metrics:
            print(f"\nPerformance Metrics:")
            print(f"  Overshoot: {self.performance_metrics.get('overshoot_percent', 0):.2f}%")
            print(f"  Settling Time: {self.performance_metrics.get('settling_time', 0):.3f}s")
            print(f"  SS Error: {self.performance_metrics.get('steady_state_error_percent', 0):.2f}%")
            print(f"  Assessment: {self.performance_metrics.get('performance_assessment', 'N/A')}")
        
        print("="*70)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Skill-Agent PID Tuning Framework')
    parser.add_argument('--mqtt', action='store_true', help='Use MQTT instead of serial')
    parser.add_argument('--manual', action='store_true', help='Run without Claude API')
    
    args = parser.parse_args()
    
    # Create agent
    agent = SkillAgentPID(use_mqtt=args.mqtt)
    
    # Run full workflow
    success = agent.run_full_tuning_cycle()
    
    # Print summary
    agent.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
