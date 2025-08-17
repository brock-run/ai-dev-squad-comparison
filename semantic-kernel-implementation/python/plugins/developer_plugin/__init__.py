"""
Developer Plugin for Semantic Kernel Implementation

This plugin is responsible for code implementation based on specifications.
"""

import semantic_kernel as sk
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter
import re
from typing import List, Optional

class DeveloperPlugin:
    """
    Plugin for code implementation and development.
    """
    
    def __init__(self, kernel: sk.Kernel):
        self.kernel = kernel
    
    @sk_function(
        description="Implement code based on design specifications",
        name="implement_code"
    )
    @sk_function_context_parameter(
        name="design",
        description="Design specifications"
    )
    @sk_function_context_parameter(
        name="language",
        description="Programming language to use"
    )
    def implement_code(self, context: sk.SKContext) -> str:
        """
        Implement code based on design specifications.
        
        Args:
            context: Contains design specifications and language
            
        Returns:
            Implemented code as string
        """
        design = context["design"]
        language = context["language"]
        
        prompt = f"""
        Implement code based on the following design specifications:
        
        Design:
        {design}
        
        Programming Language: {language}
        
        Please provide:
        1. Complete implementation
        2. Clear comments
        3. Error handling
        4. Documentation
        
        Think step-by-step and ensure your code follows best practices for {language}.
        """
        
        # In a real implementation, this would use the kernel to process the prompt
        # For now, we'll return a placeholder
        return f"Code implementation in {language}:\n\nBased on design:\n{design[:100]}...\n\n[Code would be generated here]"
    
    @sk_function(
        description="Refine code based on feedback",
        name="refine_code"
    )
    @sk_function_context_parameter(
        name="code",
        description="Original code"
    )
    @sk_function_context_parameter(
        name="feedback",
        description="Feedback on the code"
    )
    def refine_code(self, context: sk.SKContext) -> str:
        """
        Refine code based on feedback.
        
        Args:
            context: Contains original code and feedback
            
        Returns:
            Refined code as string
        """
        code = context["code"]
        feedback = context["feedback"]
        
        prompt = f"""
        Refine the following code based on the provided feedback:
        
        Original Code:
        ```
        {code}
        ```
        
        Feedback:
        {feedback}
        
        Please provide:
        1. Updated implementation addressing all feedback points
        2. Explanation of changes made
        
        Ensure your code maintains readability and follows best practices.
        """
        
        # In a real implementation, this would use the kernel to process the prompt
        # For now, we'll return a placeholder
        return f"Refined code:\n\nBased on feedback:\n{feedback[:100]}...\n\n[Refined code would be generated here]"
    
    @staticmethod
    def extract_code_from_message(message: str, language: str = "python") -> Optional[str]:
        """
        Extract code blocks from a message.
        
        Args:
            message: Message containing code blocks
            language: Programming language to extract
            
        Returns:
            Extracted code or None if no code found
        """
        # Look for code blocks with the specified language
        pattern = f"```{language}(.*?)```"
        matches = re.findall(pattern, message, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no language-specific blocks found, try generic code blocks
        pattern = r"```(.*?)```"
        matches = re.findall(pattern, message, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        return None