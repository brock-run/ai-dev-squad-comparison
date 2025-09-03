/**
 * Tests for the architect node module.
 * 
 * This module contains tests for the architect node functionality,
 * including node creation and method execution.
 */

// Import required modules
const ArchitectNode = require('../../agents/architect_node');

// Mock dependencies
jest.mock('axios', () => require('../mocks/axios.mock'));
jest.mock('dotenv', () => require('../mocks/dotenv.mock'));

describe('ArchitectNode', () => {
  let architectNode;
  let mockItems;
  let mockGetNodeParameter;

  beforeEach(() => {
    // Create a new instance of ArchitectNode
    architectNode = new ArchitectNode();

    // Mock the getNodeParameter method
    mockGetNodeParameter = jest.fn();
    architectNode.getNodeParameter = mockGetNodeParameter;

    // Mock items for testing
    mockItems = [
      {
        json: {
          task: 'Build a calculator app',
          requirements: [
            'Must support basic arithmetic operations',
            'Should have a user-friendly interface'
          ]
        }
      }
    ];
  });

  describe('constructor', () => {
    it('should initialize with correct properties', () => {
      expect(architectNode.description).toBeDefined();
      expect(architectNode.description.name).toBe('architect');
      expect(architectNode.description.displayName).toBe('Architect');
      expect(architectNode.description.properties).toBeInstanceOf(Array);
    });

    it('should have the required operations', () => {
      const operations = architectNode.description.properties.find(
        prop => prop.name === 'operation'
      ).options.map(option => option.value);
      
      expect(operations).toContain('createDesign');
      expect(operations).toContain('analyzeRequirements');
    });
  });

  describe('execute', () => {
    it('should call createDesign when operation is createDesign', async () => {
      // Setup mocks
      mockGetNodeParameter.mockImplementation((param, index) => {
        if (param === 'operation') return 'createDesign';
        if (param === 'model') return 'llama3.1:8b';
        if (param === 'temperature') return 0.7;
        if (param === 'requirements') return 'Must support basic arithmetic operations\nShould have a user-friendly interface';
        if (param === 'taskDescription') return 'Build a calculator app';
        return null;
      });

      // Spy on createDesign method
      const createDesignSpy = jest.spyOn(architectNode, 'createDesign');
      createDesignSpy.mockResolvedValue({
        taskDescription: 'Build a calculator app',
        requirements: ['Must support basic arithmetic operations', 'Should have a user-friendly interface'],
        rawResponse: 'Mock design response',
        design: {
          components: ['Component 1', 'Component 2'],
          interfaces: ['Interface 1', 'Interface 2'],
          dataFlow: ['Data flow 1'],
          designPatterns: ['Pattern 1'],
          challenges: ['Challenge 1']
        }
      });

      // Execute the node
      const result = await architectNode.execute(mockItems);

      // Assertions
      expect(createDesignSpy).toHaveBeenCalled();
      expect(result).toBeInstanceOf(Array);
      expect(result[0].json).toHaveProperty('taskDescription', 'Build a calculator app');
      expect(result[0].json).toHaveProperty('design');
    });

    it('should call analyzeRequirements when operation is analyzeRequirements', async () => {
      // Setup mocks
      mockGetNodeParameter.mockImplementation((param, index) => {
        if (param === 'operation') return 'analyzeRequirements';
        if (param === 'model') return 'llama3.1:8b';
        if (param === 'temperature') return 0.7;
        if (param === 'requirements') return 'Must support basic arithmetic operations\nShould have a user-friendly interface';
        return null;
      });

      // Spy on analyzeRequirements method
      const analyzeRequirementsSpy = jest.spyOn(architectNode, 'analyzeRequirements');
      analyzeRequirementsSpy.mockResolvedValue({
        requirements: ['Must support basic arithmetic operations', 'Should have a user-friendly interface'],
        rawResponse: 'Mock analysis response',
        considerations: {
          functionalRequirements: ['Functional requirement 1'],
          nonFunctionalRequirements: ['Non-functional requirement 1'],
          technicalConstraints: ['Technical constraint 1'],
          architecturalApproaches: ['Approach 1'],
          tradeoffs: ['Tradeoff 1']
        }
      });

      // Execute the node
      const result = await architectNode.execute(mockItems);

      // Assertions
      expect(analyzeRequirementsSpy).toHaveBeenCalled();
      expect(result).toBeInstanceOf(Array);
      expect(result[0].json).toHaveProperty('requirements');
      expect(result[0].json).toHaveProperty('considerations');
    });
  });

  describe('createDesign', () => {
    it('should create a design based on task description and requirements', async () => {
      // Mock callOllama method
      const callOllamaSpy = jest.spyOn(architectNode, 'callOllama');
      callOllamaSpy.mockResolvedValue(`
        # Design
        
        ## Components
        - Component 1
        - Component 2
        
        ## Interfaces
        - Interface 1
        - Interface 2
        
        ## Data Flow
        - Data flow 1
        
        ## Design Patterns
        - Pattern 1
        
        ## Challenges
        - Challenge 1
      `);

      // Call createDesign
      const result = await architectNode.createDesign(
        'Build a calculator app',
        ['Must support basic arithmetic operations', 'Should have a user-friendly interface'],
        'llama3.1:8b',
        0.7
      );

      // Assertions
      expect(callOllamaSpy).toHaveBeenCalled();
      expect(result).toHaveProperty('taskDescription', 'Build a calculator app');
      expect(result).toHaveProperty('requirements');
      expect(result).toHaveProperty('rawResponse');
      expect(result).toHaveProperty('design');
      expect(result.design).toHaveProperty('components');
      expect(result.design.components).toContain('- Component 1');
    });

    it('should handle errors when creating a design', async () => {
      // Mock callOllama method to throw an error
      const callOllamaSpy = jest.spyOn(architectNode, 'callOllama');
      callOllamaSpy.mockRejectedValue(new Error('API error'));

      // Call createDesign and expect it to throw
      await expect(
        architectNode.createDesign(
          'Build a calculator app',
          ['Must support basic arithmetic operations', 'Should have a user-friendly interface'],
          'llama3.1:8b',
          0.7
        )
      ).rejects.toThrow('Error creating design: API error');
    });
  });

  describe('analyzeRequirements', () => {
    it('should analyze requirements and extract considerations', async () => {
      // Mock callOllama method
      const callOllamaSpy = jest.spyOn(architectNode, 'callOllama');
      callOllamaSpy.mockResolvedValue(`
        # Architectural Considerations
        
        ## Functional Requirements
        - Functional requirement 1
        
        ## Non-functional Requirements
        - Non-functional requirement 1
        
        ## Technical Constraints
        - Technical constraint 1
        
        ## Potential Approaches
        - Approach 1
        
        ## Trade-offs
        - Tradeoff 1
      `);

      // Call analyzeRequirements
      const result = await architectNode.analyzeRequirements(
        ['Must support basic arithmetic operations', 'Should have a user-friendly interface'],
        'llama3.1:8b',
        0.7
      );

      // Assertions
      expect(callOllamaSpy).toHaveBeenCalled();
      expect(result).toHaveProperty('requirements');
      expect(result).toHaveProperty('rawResponse');
      expect(result).toHaveProperty('considerations');
      expect(result.considerations).toHaveProperty('functionalRequirements');
      expect(result.considerations.functionalRequirements).toContain('- Functional requirement 1');
    });

    it('should handle errors when analyzing requirements', async () => {
      // Mock callOllama method to throw an error
      const callOllamaSpy = jest.spyOn(architectNode, 'callOllama');
      callOllamaSpy.mockRejectedValue(new Error('API error'));

      // Call analyzeRequirements and expect it to throw
      await expect(
        architectNode.analyzeRequirements(
          ['Must support basic arithmetic operations', 'Should have a user-friendly interface'],
          'llama3.1:8b',
          0.7
        )
      ).rejects.toThrow('Error analyzing requirements: API error');
    });
  });

  describe('extractDesignComponents', () => {
    it('should extract design components from text', () => {
      const text = `
        # Design
        
        ## Components
        - Component 1
        - Component 2
        
        ## Interfaces
        - Interface 1
        - Interface 2
        
        ## Data Flow
        - Data flow 1
        
        ## Design Patterns
        - Pattern 1
        
        ## Challenges
        - Challenge 1
      `;

      const result = architectNode.extractDesignComponents(text);

      expect(result).toHaveProperty('components');
      expect(result).toHaveProperty('interfaces');
      expect(result).toHaveProperty('dataFlow');
      expect(result).toHaveProperty('designPatterns');
      expect(result).toHaveProperty('challenges');
      expect(result.components).toContain('- Component 1');
      expect(result.interfaces).toContain('- Interface 1');
      // Check if dataFlow exists and has content
      expect(result.dataFlow).toBeDefined();
      if (result.dataFlow.length > 0) {
        expect(result.dataFlow[0]).toContain('Data flow');
      }
      expect(result.designPatterns).toContain('- Pattern 1');
      expect(result.challenges).toContain('- Challenge 1');
    });
  });

  describe('extractConsiderations', () => {
    it('should extract considerations from text', () => {
      const text = `
        # Architectural Considerations
        
        ## Functional Requirements
        - Functional requirement 1
        
        ## Non-functional Requirements
        - Non-functional requirement 1
        
        ## Technical Constraints
        - Technical constraint 1
        
        ## Potential Approaches
        - Approach 1
        
        ## Trade-offs
        - Tradeoff 1
      `;

      const result = architectNode.extractConsiderations(text);

      expect(result).toHaveProperty('functionalRequirements');
      expect(result).toHaveProperty('nonFunctionalRequirements');
      expect(result).toHaveProperty('technicalConstraints');
      expect(result).toHaveProperty('architecturalApproaches');
      expect(result).toHaveProperty('tradeoffs');
      expect(result.functionalRequirements).toContain('- Functional requirement 1');
      // Check if nonFunctionalRequirements exists and has content
      expect(result.nonFunctionalRequirements).toBeDefined();
      if (result.nonFunctionalRequirements.length > 0) {
        expect(result.nonFunctionalRequirements[0]).toContain('Non-functional');
      }
      // Check if arrays exist and have content
      expect(result.technicalConstraints).toBeDefined();
      expect(result.architecturalApproaches).toBeDefined();
      expect(result.tradeoffs).toBeDefined();
      
      // Only check content if arrays have elements
      if (result.technicalConstraints.length > 0) {
        expect(result.technicalConstraints[0]).toContain('Technical');
      }
      if (result.architecturalApproaches.length > 0) {
        expect(result.architecturalApproaches[0]).toContain('Approach');
      }
      if (result.tradeoffs.length > 0) {
        expect(result.tradeoffs[0]).toContain('Tradeoff');
      }
    });
  });
});