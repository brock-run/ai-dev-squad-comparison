/**
 * Tests for the developer node module.
 * 
 * This module contains tests for the developer node functionality,
 * including node creation and method execution.
 */

// Import required modules
const DeveloperNode = require('../../agents/developer_node');

// Mock dependencies
jest.mock('axios', () => require('../mocks/axios.mock'));
jest.mock('dotenv', () => require('../mocks/dotenv.mock'));

describe('DeveloperNode', () => {
  let developerNode;
  let mockItems;
  let mockGetNodeParameter;

  beforeEach(() => {
    // Create a new instance of DeveloperNode
    developerNode = new DeveloperNode();

    // Mock the getNodeParameter method
    mockGetNodeParameter = jest.fn();
    developerNode.getNodeParameter = mockGetNodeParameter;

    // Mock items for testing
    mockItems = [
      {
        json: {
          task: 'Build a calculator app',
          design: 'Design for calculator app'
        }
      }
    ];
  });

  describe('constructor', () => {
    it('should initialize with correct properties', () => {
      expect(developerNode.description).toBeDefined();
      expect(developerNode.description.name).toBe('developer');
      expect(developerNode.description.displayName).toBe('Developer');
      expect(developerNode.description.properties).toBeInstanceOf(Array);
    });

    it('should have the required operations', () => {
      const operations = developerNode.description.properties.find(
        prop => prop.name === 'operation'
      ).options.map(option => option.value);
      
      expect(operations).toContain('implementCode');
      expect(operations).toContain('refineCode');
    });
  });

  describe('execute', () => {
    it('should call implementCode when operation is implementCode', async () => {
      // Setup mocks
      mockGetNodeParameter.mockImplementation((param, index) => {
        if (param === 'operation') return 'implementCode';
        if (param === 'model') return 'codellama:13b';
        if (param === 'temperature') return 0.7;
        if (param === 'language') return 'javascript';
        if (param === 'taskDescription') return 'Build a calculator app';
        if (param === 'design') return 'Design for calculator app';
        return null;
      });

      // Spy on implementCode method
      const implementCodeSpy = jest.spyOn(developerNode, 'implementCode');
      implementCodeSpy.mockResolvedValue({
        taskDescription: 'Build a calculator app',
        design: 'Design for calculator app',
        language: 'javascript',
        rawResponse: 'Mock implementation response',
        code: 'function calculator() { /* implementation */ }'
      });

      // Execute the node
      const result = await developerNode.execute(mockItems);

      // Assertions
      expect(implementCodeSpy).toHaveBeenCalled();
      expect(result).toBeInstanceOf(Array);
      expect(result[0].json).toHaveProperty('taskDescription', 'Build a calculator app');
      expect(result[0].json).toHaveProperty('code');
    });

    it('should call refineCode when operation is refineCode', async () => {
      // Setup mocks
      mockGetNodeParameter.mockImplementation((param, index) => {
        if (param === 'operation') return 'refineCode';
        if (param === 'model') return 'codellama:13b';
        if (param === 'temperature') return 0.7;
        if (param === 'language') return 'javascript';
        if (param === 'code') return 'function calculator() { /* implementation */ }';
        if (param === 'feedback') return 'Add error handling';
        return null;
      });

      // Spy on refineCode method
      const refineCodeSpy = jest.spyOn(developerNode, 'refineCode');
      refineCodeSpy.mockResolvedValue({
        originalCode: 'function calculator() { /* implementation */ }',
        feedback: 'Add error handling',
        language: 'javascript',
        rawResponse: 'Mock refinement response',
        refinedCode: 'function calculator() { try { /* implementation */ } catch (error) { /* error handling */ } }'
      });

      // Execute the node
      const result = await developerNode.execute(mockItems);

      // Assertions
      expect(refineCodeSpy).toHaveBeenCalled();
      expect(result).toBeInstanceOf(Array);
      expect(result[0].json).toHaveProperty('originalCode');
      expect(result[0].json).toHaveProperty('refinedCode');
    });
  });

  describe('implementCode', () => {
    it('should implement code based on task description and design', async () => {
      // Mock callOllama method
      const callOllamaSpy = jest.spyOn(developerNode, 'callOllama');
      callOllamaSpy.mockResolvedValue(`
        Here's the implementation for the calculator app:

        \`\`\`javascript
        function calculator(a, b, operation) {
          switch (operation) {
            case 'add':
              return a + b;
            case 'subtract':
              return a - b;
            case 'multiply':
              return a * b;
            case 'divide':
              if (b === 0) {
                throw new Error('Division by zero');
              }
              return a / b;
            default:
              throw new Error('Invalid operation');
          }
        }
        \`\`\`
      `);

      // Call implementCode
      const result = await developerNode.implementCode(
        'Build a calculator app',
        'Design for calculator app',
        'javascript',
        'codellama:13b',
        0.7
      );

      // Assertions
      expect(callOllamaSpy).toHaveBeenCalled();
      expect(result).toHaveProperty('taskDescription', 'Build a calculator app');
      expect(result).toHaveProperty('design', 'Design for calculator app');
      expect(result).toHaveProperty('language', 'javascript');
      expect(result).toHaveProperty('rawResponse');
      expect(result).toHaveProperty('code');
      expect(result.code).toContain('function calculator');
    });

    it('should handle errors when implementing code', async () => {
      // Mock callOllama method to throw an error
      const callOllamaSpy = jest.spyOn(developerNode, 'callOllama');
      callOllamaSpy.mockRejectedValue(new Error('API error'));

      // Call implementCode and expect it to throw
      await expect(
        developerNode.implementCode(
          'Build a calculator app',
          'Design for calculator app',
          'javascript',
          'codellama:13b',
          0.7
        )
      ).rejects.toThrow('Error implementing code: API error');
    });
  });

  describe('refineCode', () => {
    it('should refine code based on feedback', async () => {
      // Mock callOllama method
      const callOllamaSpy = jest.spyOn(developerNode, 'callOllama');
      callOllamaSpy.mockResolvedValue(`
        Here's the refined implementation with error handling:

        \`\`\`javascript
        function calculator(a, b, operation) {
          try {
            switch (operation) {
              case 'add':
                return a + b;
              case 'subtract':
                return a - b;
              case 'multiply':
                return a * b;
              case 'divide':
                if (b === 0) {
                  throw new Error('Division by zero');
                }
                return a / b;
              default:
                throw new Error('Invalid operation');
            }
          } catch (error) {
            console.error('Calculator error:', error.message);
            throw error;
          }
        }
        \`\`\`
      `);

      // Call refineCode
      const result = await developerNode.refineCode(
        'function calculator(a, b, operation) { /* implementation */ }',
        'Add error handling',
        'javascript',
        'codellama:13b',
        0.7
      );

      // Assertions
      expect(callOllamaSpy).toHaveBeenCalled();
      expect(result).toHaveProperty('originalCode');
      expect(result).toHaveProperty('feedback', 'Add error handling');
      expect(result).toHaveProperty('language', 'javascript');
      expect(result).toHaveProperty('rawResponse');
      expect(result).toHaveProperty('refinedCode');
      expect(result.refinedCode).toContain('try {');
      expect(result.refinedCode).toContain('catch (error)');
    });

    it('should handle errors when refining code', async () => {
      // Mock callOllama method to throw an error
      const callOllamaSpy = jest.spyOn(developerNode, 'callOllama');
      callOllamaSpy.mockRejectedValue(new Error('API error'));

      // Call refineCode and expect it to throw
      await expect(
        developerNode.refineCode(
          'function calculator(a, b, operation) { /* implementation */ }',
          'Add error handling',
          'javascript',
          'codellama:13b',
          0.7
        )
      ).rejects.toThrow('Error refining code: API error');
    });
  });

  describe('extractCode', () => {
    it('should extract code from markdown code blocks', () => {
      const text = `
        Here's the implementation:

        \`\`\`javascript
        function calculator(a, b, operation) {
          return a + b;
        }
        \`\`\`

        And here's another function:

        \`\`\`javascript
        function displayResult(result) {
          console.log(result);
        }
        \`\`\`
      `;

      const result = developerNode.extractCode(text, 'javascript');

      expect(result).toContain('function calculator');
      expect(result).toContain('function displayResult');
      expect(result).not.toContain('Here\'s the implementation');
    });

    it('should extract code heuristically when no code blocks are present', () => {
      const text = `
        Here's the implementation:

        function calculator(a, b, operation) {
          return a + b;
        }

        function displayResult(result) {
          console.log(result);
        }
      `;

      const result = developerNode.extractCode(text, 'javascript');

      expect(result).toContain('function calculator');
      expect(result).toContain('function displayResult');
    });
  });
});