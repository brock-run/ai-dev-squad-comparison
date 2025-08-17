/**
 * Architect Node for n8n Implementation
 * 
 * This node is responsible for system design and architecture decisions.
 * It analyzes requirements and creates high-level designs.
 */

// Import required modules
const axios = require('axios');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Constants
const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const OLLAMA_MODEL = process.env.OLLAMA_MODEL_ARCHITECT || 'llama3.1:8b';
const TEMPERATURE = parseFloat(process.env.TEMPERATURE || '0.7');

/**
 * Architect Node class for n8n
 */
class ArchitectNode {
  /**
   * Constructor for the Architect Node
   */
  constructor() {
    this.description = {
      displayName: 'Architect',
      name: 'architect',
      icon: 'file:architect.svg',
      group: ['ai', 'development'],
      version: 1,
      description: 'Creates software architecture designs based on requirements',
      defaults: {
        name: 'Architect',
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
              name: 'Create Design',
              value: 'createDesign',
              description: 'Create a high-level design based on requirements',
            },
            {
              name: 'Analyze Requirements',
              value: 'analyzeRequirements',
              description: 'Analyze requirements and extract key considerations',
            },
          ],
          default: 'createDesign',
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
              operation: ['createDesign'],
            },
          },
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
      const requirements = this.getNodeParameter('requirements', i)
        .split('\n')
        .filter(req => req.trim() !== '');
      
      let result;
      
      if (operation === 'createDesign') {
        const taskDescription = this.getNodeParameter('taskDescription', i);
        result = await this.createDesign(taskDescription, requirements, model, temperature);
      } else if (operation === 'analyzeRequirements') {
        result = await this.analyzeRequirements(requirements, model, temperature);
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
   * Create a design based on task description and requirements
   * 
   * @param {string} taskDescription - The task description
   * @param {string[]} requirements - The requirements
   * @param {string} model - The model to use
   * @param {number} temperature - The temperature to use
   * @returns {Promise<Object>} - The design result
   */
  async createDesign(taskDescription, requirements, model, temperature) {
    const requirementsText = requirements.map(req => `- ${req}`).join('\n');
    
    const systemPrompt = `
      You are an expert software architect with deep knowledge of software design patterns, 
      system architecture, and best practices. Your role is to:

      1. Analyze requirements and create high-level designs
      2. Make architectural decisions based on requirements
      3. Define interfaces between components
      4. Consider scalability, maintainability, and performance
      5. Provide clear design documentation

      Always think step-by-step and consider trade-offs in your design decisions.
      Explain your reasoning clearly and provide diagrams or pseudocode when helpful.
    `;
    
    const userPrompt = `
      Create a high-level design for the following task:
      
      Task: ${taskDescription}
      
      Requirements:
      ${requirementsText}
      
      Please provide:
      1. Component breakdown
      2. Interface definitions
      3. Data flow
      4. Key design patterns to use
      5. Potential challenges and solutions
    `;
    
    try {
      const response = await this.callOllama(model, systemPrompt, userPrompt, temperature);
      
      // Extract structured information from the response
      const design = this.extractDesignComponents(response);
      
      return {
        taskDescription,
        requirements,
        rawResponse: response,
        design,
      };
    } catch (error) {
      throw new Error(`Error creating design: ${error.message}`);
    }
  }

  /**
   * Analyze requirements and extract key considerations
   * 
   * @param {string[]} requirements - The requirements
   * @param {string} model - The model to use
   * @param {number} temperature - The temperature to use
   * @returns {Promise<Object>} - The analysis result
   */
  async analyzeRequirements(requirements, model, temperature) {
    const requirementsText = requirements.map(req => `- ${req}`).join('\n');
    
    const systemPrompt = `
      You are an expert software architect with deep knowledge of software design patterns, 
      system architecture, and best practices. Your role is to analyze requirements and
      extract key architectural considerations.
    `;
    
    const userPrompt = `
      Analyze the following requirements and extract key architectural considerations:
      
      Requirements:
      ${requirementsText}
      
      Please identify:
      1. Key functional requirements
      2. Non-functional requirements (performance, scalability, etc.)
      3. Technical constraints
      4. Potential architectural approaches
      5. Trade-offs to consider
    `;
    
    try {
      const response = await this.callOllama(model, systemPrompt, userPrompt, temperature);
      
      // Extract structured information from the response
      const considerations = this.extractConsiderations(response);
      
      return {
        requirements,
        rawResponse: response,
        considerations,
      };
    } catch (error) {
      throw new Error(`Error analyzing requirements: ${error.message}`);
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
   * Extract design components from text
   * 
   * @param {string} text - The text to extract from
   * @returns {Object} - The extracted design components
   */
  extractDesignComponents(text) {
    // This is a simplified implementation
    // In a real implementation, this would use more sophisticated parsing
    
    // Simple extraction of sections
    const components = [];
    const interfaces = [];
    const dataFlow = [];
    const designPatterns = [];
    const challenges = [];
    
    let currentSection = null;
    
    for (const line of text.split('\n')) {
      const trimmedLine = line.trim();
      
      if (!trimmedLine) {
        continue;
      }
      
      if (/component/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'components';
        continue;
      } else if (/interface/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'interfaces';
        continue;
      } else if (/data flow/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'dataFlow';
        continue;
      } else if (/design pattern/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'designPatterns';
        continue;
      } else if (/challenge/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'challenges';
        continue;
      }
      
      if (currentSection === 'components' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
          (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        components.push(trimmedLine);
      } else if (currentSection === 'interfaces' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
                (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        interfaces.push(trimmedLine);
      } else if (currentSection === 'dataFlow' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
                (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        dataFlow.push(trimmedLine);
      } else if (currentSection === 'designPatterns' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
                (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        designPatterns.push(trimmedLine);
      } else if (currentSection === 'challenges' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
                (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        challenges.push(trimmedLine);
      }
    }
    
    return {
      components,
      interfaces,
      dataFlow,
      designPatterns,
      challenges,
    };
  }

  /**
   * Extract considerations from text
   * 
   * @param {string} text - The text to extract from
   * @returns {Object} - The extracted considerations
   */
  extractConsiderations(text) {
    // This is a simplified implementation
    // In a real implementation, this would use more sophisticated parsing
    
    // Simple extraction of sections
    const functionalRequirements = [];
    const nonFunctionalRequirements = [];
    const technicalConstraints = [];
    const architecturalApproaches = [];
    const tradeoffs = [];
    
    let currentSection = null;
    
    for (const line of text.split('\n')) {
      const trimmedLine = line.trim();
      
      if (!trimmedLine) {
        continue;
      }
      
      if (/functional requirement/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'functionalRequirements';
        continue;
      } else if (/non-functional/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'nonFunctionalRequirements';
        continue;
      } else if (/technical constraint/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'technicalConstraints';
        continue;
      } else if (/architectural approach/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'architecturalApproaches';
        continue;
      } else if (/trade-off/i.test(trimmedLine) && (/:/.test(trimmedLine) || /s$/.test(trimmedLine))) {
        currentSection = 'tradeoffs';
        continue;
      }
      
      if (currentSection === 'functionalRequirements' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
          (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        functionalRequirements.push(trimmedLine);
      } else if (currentSection === 'nonFunctionalRequirements' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
                (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        nonFunctionalRequirements.push(trimmedLine);
      } else if (currentSection === 'technicalConstraints' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
                (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        technicalConstraints.push(trimmedLine);
      } else if (currentSection === 'architecturalApproaches' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
                (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        architecturalApproaches.push(trimmedLine);
      } else if (currentSection === 'tradeoffs' && (/^-/.test(trimmedLine) || /^\*/.test(trimmedLine) || 
                (trimmedLine.length > 2 && /^\d\./.test(trimmedLine)))) {
        tradeoffs.push(trimmedLine);
      }
    }
    
    return {
      functionalRequirements,
      nonFunctionalRequirements,
      technicalConstraints,
      architecturalApproaches,
      tradeoffs,
    };
  }
}

module.exports = ArchitectNode;