using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace SemanticKernelAIDevSquad.Plugins
{
    /// <summary>
    /// Plugin for code implementation and development.
    /// </summary>
    public class DeveloperPlugin
    {
        private readonly IKernel _kernel;

        /// <summary>
        /// Initializes a new instance of the <see cref="DeveloperPlugin"/> class.
        /// </summary>
        /// <param name="kernel">The semantic kernel instance.</param>
        public DeveloperPlugin(IKernel kernel)
        {
            _kernel = kernel;
        }

        /// <summary>
        /// Implement code based on design specifications.
        /// </summary>
        /// <param name="design">Design specifications.</param>
        /// <param name="context">The context for the function.</param>
        /// <returns>Implemented code as string.</returns>
        [SKFunction("Implement code based on design specifications")]
        [SKFunctionName("ImplementCode")]
        [SKFunctionInput(Description = "Design specifications")]
        [SKFunctionContextParameter(Name = "language", Description = "Programming language to use")]
        public async Task<string> ImplementCodeAsync(string design, SKContext context)
        {
            var language = context.Variables.ContainsKey("language") 
                ? context.Variables["language"] 
                : "csharp";

            var prompt = $@"
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
";

            // In a real implementation, this would use the kernel to process the prompt
            // For now, we'll return a placeholder
            return $"Code implementation in {language}:\n\nBased on design:\n{design.Substring(0, Math.Min(100, design.Length))}...\n\n[Code would be generated here]";
        }

        /// <summary>
        /// Refine code based on feedback.
        /// </summary>
        /// <param name="code">Original code.</param>
        /// <param name="context">The context for the function.</param>
        /// <returns>Refined code as string.</returns>
        [SKFunction("Refine code based on feedback")]
        [SKFunctionName("RefineCode")]
        [SKFunctionInput(Description = "Original code")]
        [SKFunctionContextParameter(Name = "feedback", Description = "Feedback on the code")]
        public async Task<string> RefineCodeAsync(string code, SKContext context)
        {
            var feedback = context.Variables.ContainsKey("feedback") 
                ? context.Variables["feedback"] 
                : string.Empty;

            var prompt = $@"
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
";

            // In a real implementation, this would use the kernel to process the prompt
            // For now, we'll return a placeholder
            return $"Refined code:\n\nBased on feedback:\n{feedback.Substring(0, Math.Min(100, feedback.Length))}...\n\n[Refined code would be generated here]";
        }

        /// <summary>
        /// Extract code blocks from a message.
        /// </summary>
        /// <param name="message">Message containing code blocks.</param>
        /// <param name="language">Programming language to extract.</param>
        /// <returns>Extracted code or null if no code found.</returns>
        public static string ExtractCodeFromMessage(string message, string language = "csharp")
        {
            // Look for code blocks with the specified language
            var pattern = $"```{language}(.*?)```";
            var matches = Regex.Matches(message, pattern, RegexOptions.Singleline);
            
            if (matches.Count > 0)
            {
                return matches[0].Groups[1].Value.Trim();
            }
            
            // If no language-specific blocks found, try generic code blocks
            pattern = @"```(.*?)```";
            matches = Regex.Matches(message, pattern, RegexOptions.Singleline);
            
            if (matches.Count > 0)
            {
                return matches[0].Groups[1].Value.Trim();
            }
            
            return null;
        }
    }
}