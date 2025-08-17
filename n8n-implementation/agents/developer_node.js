/**
 * Developer Node for n8n Implementation
 * 
 * This node is responsible for implementing code based on architectural designs.
 * It writes code, handles implementation details, and follows best practices.
 */

// Import required modules
const axios = require('axios');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Constants
const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const OLLAMA_MODEL = process.env.OLLAMA_MODEL_DEVELOPER || 'codellama:13b';
const TEMPERATURE = parseFloat(process.env.TEMPERATURE || '0.7');

/**
 * Developer Node class for n8n
 */
class DeveloperNode {
  /**
   * Constructor for the Developer Node
   */
  constructor() {
    this.description = {
      displayName: 'Developer',
      name: 'developer',
      icon: 'file:developer.svg',
      group: ['ai', 'development'],
      version: 1,
      description: 'Implements code based on architectural designs',
      defaults: {
        name: 'Developer',
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
              name: 'Implement Code',
              value: 'implementCode',
              description: 'Implement code based on design',
            },
            {
              name: 'Refine Code',
              value: 'refineCode',
              description: 'Refine code based on feedback',
            },
          ],
          default: 'implementCode',
          description: 'The operation to perform',
        },
        {
          displayName: 'Task Description',
          name: 'taskDescription',
          type: 'string',
          default: '',
          description: 'Description of the development task',
          displayOptions: {
            show: {
              operation: ['implementCode'],
            },
          },
        },
        {
          displayName: 'Design',
          name: 'design',
          type: 'string',
          typeOptions: {
            rows: 8,
          },
          default: '',
          description: 'The architectural design to implement',
          displayOptions: {
            show: {
              operation: ['implementCode'],
            },
          },
        },
        {
          displayName: 'Code',
          name: 'code',
          type: 'string',
          typeOptions: {
            rows: 12,
          },
          default: '',
          description: 'The code to refine',
          displayOptions: {
            show: {
              operation: ['refineCode'],
            },
          },
        },
        {
          displayName: 'Feedback',
          name: 'feedback',
          type: 'string',
          typeOptions: {
            rows: 4,
          },
          default: '',
          description: 'Feedback to address in the code refinement',
          displayOptions: {
            show: {
              operation: ['refineCode'],
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
          description: 'The programming language to use',
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
      
      let result;
      
      if (operation === 'implementCode') {
        const taskDescription = this.getNodeParameter('taskDescription', i);
        const design = this.getNodeParameter('design', i);
        result = await this.implementCode(taskDescription, design, language, model, temperature);
      } else if (operation === 'refineCode') {
        const code = this.getNodeParameter('code', i);
        const feedback = this.getNodeParameter('feedback', i);
        result = await this.refineCode(code, feedback, language, model, temperature);
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
   * Implement code based on task description and design
   * 
   * @param {string} taskDescription - The task description
   * @param {string} design - The architectural design
   * @param {string} language - The programming language
   * @param {string} model - The model to use
   * @param {number} temperature - The temperature to use
   * @returns {Promise<Object>} - The implementation result
   */
  async implementCode(taskDescription, design, language, model, temperature) {
    const systemPrompt = `
      You are an expert software developer with deep knowledge of programming languages, 
      algorithms, data structures, and best practices. Your role is to:

      1. Implement code based on architectural designs and requirements
      2. Write clean, efficient, and maintainable code
      3. Follow language-specific best practices and conventions
      4. Handle edge cases and error conditions
      5. Document your code thoroughly

      Always think step-by-step and consider performance, readability, and maintainability.
      Explain your implementation decisions and include comments in your code.
    `;
    
    const userPrompt = `
      Implement code for the following task based on the provided design:
      
      Task: ${taskDescription}
      
      Design:
      ${design}
      
      Please implement this in ${language}. Your implementation should include:
      1. Complete implementation with all necessary functions and classes
      2. Proper error handling
      3. Comments and documentation
      4. Any necessary imports
      
      Think step-by-step and consider performance, readability, and maintainability.
      Explain your implementation decisions and include comments in your code.
    `;
    
    try {
      const response = await this.callOllama(model, systemPrompt, userPrompt, temperature);
      
      // Extract code from the response
      const code = this.extractCode(response, language);
      
      return {
        taskDescription,
        design,
        language,
        rawResponse: response,
        code,
      };
    } catch (error) {
      throw new Error(`Error implementing code: ${error.message}`);
    }
  }

  /**
   * Refine code based on feedback
   * 
   * @param {string} code - The code to refine
   * @param {string} feedback - The feedback to address
   * @param {string} language - The programming language
   * @param {string} model - The model to use
   * @param {number} temperature - The temperature to use
   * @returns {Promise<Object>} - The refinement result
   */
  async refineCode(code, feedback, language, model, temperature) {
    const systemPrompt = `
      You are an expert software developer with deep knowledge of programming languages, 
      algorithms, data structures, and best practices. Your role is to refine and improve
      existing code based on feedback.
    `;
    
    const userPrompt = `
      Refine the following ${language} code based on the feedback:
      
      Original Code:
      \`\`\`${language}
      ${code}
      \`\`\`
      
      Feedback:
      ${feedback}
      
      Please provide the improved code with all necessary changes.
      Explain your changes and reasoning.
    `;
    
    try {
      const response = await this.callOllama(model, systemPrompt, userPrompt, temperature);
      
      // Extract code from the response
      const refinedCode = this.extractCode(response, language);
      
      return {
        originalCode: code,
        feedback,
        language,
        rawResponse: response,
        refinedCode,
      };
    } catch (error) {
      throw new Error(`Error refining code: ${error.message}`);
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
}

module.exports = DeveloperNode;