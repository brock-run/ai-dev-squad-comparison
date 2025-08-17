/**
 * Tester Node for n8n Implementation
 * 
 * This node is responsible for testing implemented code.
 * It creates test cases, runs tests, and evaluates code quality.
 */

// Import required modules
const axios = require('axios');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Constants
const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const OLLAMA_MODEL = process.env.OLLAMA_MODEL_TESTER || 'llama3.1:8b';
const TEMPERATURE = parseFloat(process.env.TEMPERATURE || '0.7');

/**
 * Tester Node class for n8n
 */
class TesterNode {
  /**
   * Constructor for the Tester Node
   */
  constructor() {
    this.description = {
      displayName: 'Tester',
      name: 'tester',
      icon: 'file:tester.svg',
      group: ['ai', 'development'],
      version: 1,
      description: 'Creates and runs tests for implemented code',
      defaults: {
        name: 'Tester',
      },
      inputs: ['main'],
      outputs: ['main'],
      properties: [
        {
          displayName: 'Operation',
          name: 'operation',
          type: 'options',
          options: [
            {
              name: 'Create Test Cases',
              value: 'createTestCases',
              description: 'Create test cases for implemented code',
            },
            {
              name: 'Evaluate Code',
              value: 'evaluateCode',
              description: 'Evaluate code against requirements',
            },
            {
              name: 'Run Tests',
              value: 'runTests',
              description: 'Run tests on implemented code',
            },
          ],
          default: 'createTestCases',
          description: 'The operation to perform',
        },
        {
          displayName: 'Code',
          name: 'code',
          type: 'string',
          typeOptions: {
            rows: 12,
          },
          default: '',
          description: 'The code to test or evaluate',
        },
        {
          displayName: 'Requirements',
          name: 'requirements',
          type: 'string',
          typeOptions: {
            rows: 4,
          },
          default: '',
          description: 'Requirements for the task (one per line)',
          displayOptions: {
            show: {
              operation: ['createTestCases', 'evaluateCode'],
            },
          },
        },
        {
          displayName: 'Test Cases',
          name: 'testCases',
          type: 'string',
          typeOptions: {
            rows: 8,
          },
          default: '',
          description: 'Test cases to run',
          displayOptions: {
            show: {
              operation: ['runTests'],
            },
          },
        },
        {
          displayName: 'Test Results',
          name: 'testResults',
          type: 'string',
          typeOptions: {
            rows: 4,
          },
          default: '',
          description: 'Results of running tests',
          displayOptions: {
            show: {
              operation: ['evaluateCode'],
            },
          },
        },
        {
          displayName: 'Programming Language',
          name: 'language',
          type: 'options',
          options: [
            {
              name: 'Python',
              value: 'python',
            },
            {
              name: 'JavaScript',
              value: 'javascript',
            },
            {
              name: 'TypeScript',
              value: 'typescript',
            },
            {
              name: 'Java',
              value: 'java',
            },
            {
              name: 'C#',
              value: 'csharp',
            },
          ],
          default: 'python',
          description: 'The programming language of the code',
        },
        {
          displayName: 'Model',
          name: 'model',
          type: 'string',
          default: OLLAMA_MODEL,
          description: 'The Ollama model to use',
        },
        {
          displayName: 'Temperature',
          name: 'temperature',
          type: 'number',
          default: TEMPERATURE,
          description: 'The temperature to use for generation',
        },
      ],
    };
  }

  /**
   * Execute the node functionality
   * 
   * @param {Object} items - The input items
   * @returns {Promise<Object[]>} - The output items
   */
  async execute(items) {
    const returnData = [];
    
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      const operation = this.getNodeParameter('operation', i);
      const model = this.getNodeParameter('model', i);
      const temperature = this.getNodeParameter('temperature', i);
      const language = this.getNodeParameter('language', i);
      const code = this.getNodeParameter('code', i);
      
      let result;
      
      if (operation === 'createTestCases') {
        const requirements = this.getNodeParameter('requirements', i)
          .split('\n')
          .filter(req => req.trim() !== '');
        result = await this.createTestCases(code, requirements, language, model, temperature);
      } else if (operation === 'evaluateCode') {
        const requirements = this.getNodeParameter('requirements', i)
          .split('\n')
          .filter(req => req.trim() !== '');
        const testResults = this.getNodeParameter('testResults', i);
        result = await this.evaluateCode(code, requirements, testResults, language, model, temperature);
      } else if (operation === 'runTests') {
        const testCases = this.getNodeParameter('testCases', i);
        result = await this.runTests(code, testCases, language, model, temperature);
      }
      
      returnData.push({
        json: {
          ...result,
        },
      });
    }
    
    return returnData;
  }

  /**
   * Create test cases for implemented code
   * 
   * @param {string} code - The code to test
   * @param {string[]} requirements - The requirements
   * @param {string} language - The programming language
   * @param {string} model - The model to use
   * @param {number} temperature - The temperature to use
   * @returns {Promise<Object>} - The test cases result
   */
  async createTestCases(code, requirements, language, model, temperature) {
    const requirementsText = requirements.map(req => `- ${req}`).join('\n');
    
    const systemPrompt = `
      You are an expert software tester with deep knowledge of testing methodologies, 
      test frameworks, and quality assurance. Your role is to:

      1. Create comprehensive test cases for code implementations
      2. Cover edge cases and error conditions
      3. Ensure all requirements are tested
      4. Use appropriate testing frameworks for the language
      5. Write clear and maintainable test code

      Always think step-by-step and consider different testing scenarios.
      Explain your testing approach and include comments in your test code.
    `;
    
    const userPrompt = `
      Create comprehensive test cases for the following ${language} code:
      
      Code:
      \`\`\`${language}
      ${code}
      \`\`\`
      
      Requirements:
      ${requirementsText}
      
      Please provide:
      1. Unit tests covering all functionality
      2. Edge case tests
      3. Performance tests if applicable
      4. Test for each requirement
      
      Use appropriate testing framework for ${language}.
      Include setup and teardown code if needed.
    `;
    
    try {
      const response = await this.callOllama(model, systemPrompt, userPrompt, temperature);
      
      // Extract test code from the response
      const testCode = this.extractCode(response, language);
      
      return {
        code,
        requirements,
        language,
        rawResponse: response,
        testCode,
      };
    } catch (error) {
      throw new Error(`Error creating test cases: ${error.message}`);
    }
  }

  /**
   * Evaluate code against requirements
   * 
   * @param {string} code - The code to evaluate
   * @param {string[]} requirements - The requirements
   * @param {string} testResults - The test results
   * @param {string} language - The programming language
   * @param {string} model - The model to use
   * @param {number} temperature - The temperature to use
   * @returns {Promise<Object>} - The evaluation result
   */
  async evaluateCode(code, requirements, testResults, language, model, temperature) {
    const requirementsText = requirements.map(req => `- ${req}`).join('\n');
    
    const systemPrompt = `
      You are an expert software quality assurance engineer with deep knowledge of 
      code quality, testing, and software engineering best practices. Your role is to:

      1. Evaluate code against requirements
      2. Assess code quality and maintainability
      3. Identify potential improvements
      4. Provide constructive feedback
      5. Rate the overall implementation

      Always be thorough and specific in your evaluation.
      Provide actionable feedback that can be used to improve the code.
    `;
    
    const userPrompt = `
      Evaluate the following ${language} code against the requirements:
      
      Code:
      \`\`\`${language}
      ${code}
      \`\`\`
      
      Requirements:
      ${requirementsText}
      
      Test Results:
      ${testResults}
      
      Please provide:
      1. Assessment of how well the code meets each requirement
      2. Code quality evaluation
      3. Potential improvements
      4. Overall rating (1-10)
      
      Be thorough and specific in your evaluation.
    `;
    
    try {
      const response = await this.callOllama(model, systemPrompt, userPrompt, temperature);
      
      // Extract structured evaluation from the response
      const evaluation = this.extractEvaluation(response);
      
      return {
        code,
        requirements,
        testResults,
        language,
        rawResponse: response,
        evaluation,
      };
    } catch (error) {
      throw new Error(`Error evaluating code: ${error.message}`);
    }
  }

  /**
   * Run tests on implemented code
   * 
   * @param {string} code - The code to test
   * @param {string} testCases - The test cases
   * @param {string} language - The programming language
   * @param {string} model - The model to use
   * @param {number} temperature - The temperature to use
   * @returns {Promise<Object>} - The test results
   */
  async runTests(code, testCases, language, model, temperature) {
    const systemPrompt = `
      You are an expert software tester with deep knowledge of testing methodologies, 
      test frameworks, and quality assurance. Your role is to simulate running tests
      on code and provide realistic test results.
    `;
    
    const userPrompt = `
      Simulate running the following tests on the provided ${language} code:
      
      Code:
      \`\`\`${language}
      ${code}
      \`\`\`
      
      Test Cases:
      \`\`\`${language}
      ${testCases}
      \`\`\`
      
      Please provide:
      1. Test execution results (pass/fail for each test)
      2. Code coverage information
      3. Performance metrics if applicable
      4. Any issues or errors encountered
      
      Be realistic in your simulation. If there are obvious issues in the code that would cause tests to fail,
      reflect that in your results.
    `;
    
    try {
      const response = await this.callOllama(model, systemPrompt, userPrompt, temperature);
      
      // Extract structured test results from the response
      const testResults = this.extractTestResults(response);
      
      return {
        code,
        testCases,
        language,
        rawResponse: response,
        testResults,
      };
    } catch (error) {
      throw new Error(`Error running tests: ${error.message}`);
    }
  }

  /**
   * Call the Ollama API
   * 
   * @param {string} model - The model to use
   * @param {string} systemPrompt - The system prompt
   * @param {string} userPrompt - The user prompt
   * @param {number} temperature - The temperature to use
   * @returns {Promise<string>} - The response text
   */
  async callOllama(model, systemPrompt, userPrompt, temperature) {
    try {
      const response = await axios.post(`${OLLAMA_BASE_URL}/api/chat`, {
        model,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt },
        ],
        temperature,
      });
      
      return response.data.message.content;
    } catch (error) {
      throw new Error(`Error calling Ollama API: ${error.message}`);
    }
  }

  /**
   * Extract code from text
   * 
   * @param {string} text - The text to extract from
   * @param {string} language - The programming language
   * @returns {string} - The extracted code
   */
  extractCode(text, language) {
    // Look for code blocks with language-specific markers
    const codeBlockRegex = new RegExp(`\`\`\`(?:${language})?([\\s\\S]*?)\`\`\``, 'g');
    const matches = [...text.matchAll(codeBlockRegex)];
    
    if (matches.length > 0) {
      // Join all code blocks
      return matches.map(match => match[1].trim()).join('\n\n');
    }
    
    // If no code blocks with markers were found, try to extract code heuristically
    // This is a simplified approach and might not work for all cases
    const lines = text.split('\n');
    const codeLines = [];
    let inCodeSection = false;
    
    for (const line of lines) {
      // Heuristics to identify code sections without markers
      if (line.trim().startsWith('def ') || 
          line.trim().startsWith('class ') || 
          line.trim().startsWith('function ') || 
          line.trim().startsWith('import ') || 
          line.trim().startsWith('from ') ||
          line.trim().startsWith('@test') ||
          line.trim().startsWith('test') ||
          (line.includes('=') && !line.trim().startsWith('//'))) {
        inCodeSection = true;
      }
      
      if (inCodeSection) {
        codeLines.push(line);
      }
    }
    
    if (codeLines.length > 0) {
      return codeLines.join('\n');
    }
    
    // If all else fails, return the entire text
    return text;
  }

  /**
   * Extract evaluation from text
   * 
   * @param {string} text - The text to extract from
   * @returns {Object} - The extracted evaluation
   */
  extractEvaluation(text) {
    // This is a simplified implementation
    // In a real implementation, this would use more sophisticated parsing
    
    // Simple extraction of sections
    const requirementAssessments = [];
    const codeQuality = [];
    const improvements = [];
    let rating = null;
    
    let currentSection = null;
    
    for (const line of text.split('\n')) {
      const trimmedLine = line.trim();
      
      if (!trimmedLine) {
        continue;
      }
      
      if (/requirement|assessment/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'requirementAssessments';
        continue;
      } else if (/code quality|quality/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'codeQuality';
        continue;
      } else if (/improvement|potential/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'improvements';
        continue;
      } else if (/rating|overall/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'rating';
        continue;
      }
      
      if (currentSection === 'requirementAssessments' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
          (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        requirementAssessments.push(trimmedLine);
      } else if (currentSection === 'codeQuality' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
                (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        codeQuality.push(trimmedLine);
      } else if (currentSection === 'improvements' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
                (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        improvements.push(trimmedLine);
      } else if (currentSection === 'rating') {
        // Try to extract a numeric rating
        const ratingMatch = trimmedLine.match(/(\d+)(?:\s*\/\s*10)?/);
        if (ratingMatch) {
          rating = parseInt(ratingMatch[1], 10);
          currentSection = null; // Move on after finding the rating
        }
      }
    }
    
    return {
      requirementAssessments,
      codeQuality,
      improvements,
      rating,
    };
  }

  /**
   * Extract test results from text
   * 
   * @param {string} text - The text to extract from
   * @returns {Object} - The extracted test results
   */
  extractTestResults(text) {
    // This is a simplified implementation
    // In a real implementation, this would use more sophisticated parsing
    
    // Simple extraction of sections
    const passedTests = [];
    const failedTests = [];
    let coverage = null;
    const performanceMetrics = [];
    
    let currentSection = null;
    
    for (const line of text.split('\n')) {
      const trimmedLine = line.trim();
      
      if (!trimmedLine) {
        continue;
      }
      
      if (/pass|passed|success/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'passedTests';
        continue;
      } else if (/fail|failed|failure/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'failedTests';
        continue;
      } else if (/coverage/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'coverage';
        continue;
      } else if (/performance|metrics/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'performanceMetrics';
        continue;
      }
      
      if (currentSection === 'passedTests' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
          (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        passedTests.push(trimmedLine);
      } else if (currentSection === 'failedTests' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
                (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        failedTests.push(trimmedLine);
      } else if (currentSection === 'coverage') {
        // Try to extract a coverage percentage
        const coverageMatch = trimmedLine.match(/(\d+(?:\.\d+)?)%/);
        if (coverageMatch) {
          coverage = parseFloat(coverageMatch[1]);
          currentSection = null; // Move on after finding the coverage
        }
      } else if (currentSection === 'performanceMetrics' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
                (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        performanceMetrics.push(trimmedLine);
      }
    }
    
    return {
      passedTests,
      failedTests,
      coverage,
      performanceMetrics,
      summary: {
        totalTests: passedTests.length + failedTests.length,
        passedTests: passedTests.length,
        failedTests: failedTests.length,
        coverage,
      },
    };
  }
}

module.exports = TesterNode;