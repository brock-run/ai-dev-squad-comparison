using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using SemanticKernelAIDevSquad.Plugins;

namespace SemanticKernelAIDevSquad.Workflows
{
    /// <summary>
    /// Orchestrates the development workflow using the architect, developer, and tester plugins.
    /// </summary>
    public class DevelopmentWorkflow
    {
        /// <summary>
        /// Create a kernel with all development plugins registered.
        /// </summary>
        /// <returns>Configured kernel.</returns>
        public static IKernel CreateDevelopmentKernel()
        {
            // Create a new kernel
            var kernel = new KernelBuilder().Build();
            
            // Configure Ollama as the AI service
            var ollamaBaseUrl = Environment.GetEnvironmentVariable("OLLAMA_BASE_URL") ?? "http://localhost:11434";
            var ollamaModel = Environment.GetEnvironmentVariable("OLLAMA_MODEL") ?? "llama3.1:8b";
            
            // Add Ollama as the AI service
            // Note: In a real implementation, this would use the actual Ollama client
            // For this template, we're just showing the structure
            kernel.Config.AddTextCompletionService("ollama", config =>
            {
                config.SetOllamaTextCompletionService(ollamaModel, ollamaBaseUrl);
            });
            
            // Register plugins
            kernel.ImportSkill(new ArchitectPlugin(kernel), "architect");
            kernel.ImportSkill(new DeveloperPlugin(kernel), "developer");
            kernel.ImportSkill(new TesterPlugin(kernel), "tester");
            
            return kernel;
        }

        /// <summary>
        /// Run the development workflow for a given task and requirements.
        /// </summary>
        /// <param name="task">Description of the development task.</param>
        /// <param name="requirements">List of requirements.</param>
        /// <param name="language">Programming language to use.</param>
        /// <returns>Results of the development process.</returns>
        public static async Task<Dictionary<string, string>> RunDevelopmentWorkflowAsync(
            string task, 
            List<string> requirements, 
            string language = "csharp")
        {
            // Create kernel with plugins
            var kernel = CreateDevelopmentKernel();
            
            // Format requirements as a string
            var requirementsText = string.Join("\n", requirements);
            
            // Step 1: Create design with architect
            var variables = new ContextVariables();
            variables.Set("task", task);
            variables.Set("requirements", requirementsText);
            
            var designResult = await kernel.RunAsync(variables, kernel.Skills.GetFunction("architect", "CreateDesign"));
            var design = designResult.Result.ToString();
            
            // Step 2: Implement code with developer
            variables = new ContextVariables();
            variables.Set("design", design);
            variables.Set("language", language);
            
            var codeResult = await kernel.RunAsync(variables, kernel.Skills.GetFunction("developer", "ImplementCode"));
            var code = codeResult.Result.ToString();
            
            // Step 3: Create test cases with tester
            variables = new ContextVariables();
            variables.Set("code", code);
            variables.Set("requirements", requirementsText);
            variables.Set("language", language);
            
            var testCasesResult = await kernel.RunAsync(variables, kernel.Skills.GetFunction("tester", "CreateTestCases"));
            var testCases = testCasesResult.Result.ToString();
            
            // Step 4: Run tests with tester
            variables = new ContextVariables();
            variables.Set("code", code);
            variables.Set("tests", testCases);
            variables.Set("language", language);
            
            var testResultsResult = await kernel.RunAsync(variables, kernel.Skills.GetFunction("tester", "RunTests"));
            var testResults = testResultsResult.Result.ToString();
            
            // Step 5: Evaluate code with tester
            variables = new ContextVariables();
            variables.Set("code", code);
            variables.Set("requirements", requirementsText);
            variables.Set("test_results", testResults);
            
            var evaluationResult = await kernel.RunAsync(variables, kernel.Skills.GetFunction("tester", "EvaluateCode"));
            var evaluation = evaluationResult.Result.ToString();
            
            // Step 6: Refine code if needed
            if (evaluation.ToLower().Contains("improvements needed") || evaluation.ToLower().Contains("issues found"))
            {
                variables = new ContextVariables();
                variables.Set("code", code);
                variables.Set("feedback", evaluation);
                
                var refinedCodeResult = await kernel.RunAsync(variables, kernel.Skills.GetFunction("developer", "RefineCode"));
                code = refinedCodeResult.Result.ToString();
                
                // Re-run tests and evaluation
                variables = new ContextVariables();
                variables.Set("code", code);
                variables.Set("tests", testCases);
                variables.Set("language", language);
                
                testResultsResult = await kernel.RunAsync(variables, kernel.Skills.GetFunction("tester", "RunTests"));
                testResults = testResultsResult.Result.ToString();
                
                variables = new ContextVariables();
                variables.Set("code", code);
                variables.Set("requirements", requirementsText);
                variables.Set("test_results", testResults);
                
                evaluationResult = await kernel.RunAsync(variables, kernel.Skills.GetFunction("tester", "EvaluateCode"));
                evaluation = evaluationResult.Result.ToString();
            }
            
            // Return results
            return new Dictionary<string, string>
            {
                { "task", task },
                { "requirements", requirementsText },
                { "design", design },
                { "code", code },
                { "test_cases", testCases },
                { "test_results", testResults },
                { "evaluation", evaluation }
            };
        }
    }
}