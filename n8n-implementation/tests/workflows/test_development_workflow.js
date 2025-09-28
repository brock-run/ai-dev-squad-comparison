/**
 * Tests for the development workflow.
 * 
 * This module contains tests for the development workflow JSON structure,
 * including node connections and configurations.
 */

// Import required modules
const fs = require('fs');
const path = require('path');

// Load the workflow JSON
const workflowPath = path.join(__dirname, '../../workflows/development_workflow.json');
const workflow = JSON.parse(fs.readFileSync(workflowPath, 'utf8'));

describe('Development Workflow', () => {
  describe('structure', () => {
    it('should have a valid workflow structure', () => {
      expect(workflow).toBeDefined();
      expect(workflow.name).toBeDefined();
      expect(workflow.nodes).toBeInstanceOf(Array);
      expect(workflow.connections).toBeDefined();
      expect(workflow.active).toBe(true);
    });

    it('should have the correct name', () => {
      expect(workflow.name).toContain('AI Development Squad');
    });

    it('should have all required nodes', () => {
      const nodeNames = workflow.nodes.map(node => node.name);
      
      // Check for required nodes
      expect(nodeNames).toContain('Webhook');
      expect(nodeNames).toContain('Architect - Analyze Requirements');
      expect(nodeNames).toContain('Architect - Create Design');
      expect(nodeNames).toContain('Developer - Implement Code');
      expect(nodeNames).toContain('Tester - Create Test Cases');
      expect(nodeNames).toContain('Tester - Run Tests');
      expect(nodeNames).toContain('Tester - Evaluate Code');
      expect(nodeNames).toContain('IF - Needs Refinement');
      expect(nodeNames).toContain('Developer - Refine Code');
      expect(nodeNames).toContain('Tester - Run Tests (Refined)');
      expect(nodeNames).toContain('Tester - Evaluate Code (Refined)');
      expect(nodeNames).toContain('Prepare Final Output');
      expect(nodeNames).toContain('Respond to Webhook');
    });
  });

  describe('node configurations', () => {
    it('should have correct Webhook configuration', () => {
      const webhookNode = workflow.nodes.find(node => node.name === 'Webhook');
      expect(webhookNode).toBeDefined();
      expect(webhookNode.type).toBe('n8n-nodes-base.webhook');
      expect(webhookNode.parameters.path).toBe('development-task');
    });

    it('should have correct Architect nodes configuration', () => {
      const analyzeNode = workflow.nodes.find(node => node.name === 'Architect - Analyze Requirements');
      expect(analyzeNode).toBeDefined();
      expect(analyzeNode.type).toBe('n8n-nodes-base.architect');
      expect(analyzeNode.parameters.operation).toBe('analyzeRequirements');

      const designNode = workflow.nodes.find(node => node.name === 'Architect - Create Design');
      expect(designNode).toBeDefined();
      expect(designNode.type).toBe('n8n-nodes-base.architect');
      expect(designNode.parameters.operation).toBe('createDesign');
    });

    it('should have correct Developer nodes configuration', () => {
      const implementNode = workflow.nodes.find(node => node.name === 'Developer - Implement Code');
      expect(implementNode).toBeDefined();
      expect(implementNode.type).toBe('n8n-nodes-base.developer');
      expect(implementNode.parameters.operation).toBe('implementCode');

      const refineNode = workflow.nodes.find(node => node.name === 'Developer - Refine Code');
      expect(refineNode).toBeDefined();
      expect(refineNode.type).toBe('n8n-nodes-base.developer');
      expect(refineNode.parameters.operation).toBe('refineCode');
    });

    it('should have correct Tester nodes configuration', () => {
      const createTestsNode = workflow.nodes.find(node => node.name === 'Tester - Create Test Cases');
      expect(createTestsNode).toBeDefined();
      expect(createTestsNode.type).toBe('n8n-nodes-base.tester');
      expect(createTestsNode.parameters.operation).toBe('createTestCases');

      const runTestsNode = workflow.nodes.find(node => node.name === 'Tester - Run Tests');
      expect(runTestsNode).toBeDefined();
      expect(runTestsNode.type).toBe('n8n-nodes-base.tester');
      expect(runTestsNode.parameters.operation).toBe('runTests');

      const evaluateNode = workflow.nodes.find(node => node.name === 'Tester - Evaluate Code');
      expect(evaluateNode).toBeDefined();
      expect(evaluateNode.type).toBe('n8n-nodes-base.tester');
      expect(evaluateNode.parameters.operation).toBe('evaluateCode');
    });

    it('should have correct conditional node configuration', () => {
      const ifNode = workflow.nodes.find(node => node.name === 'IF - Needs Refinement');
      expect(ifNode).toBeDefined();
      expect(ifNode.type).toBe('n8n-nodes-base.if');
      expect(ifNode.parameters.conditions.string).toBeInstanceOf(Array);
      expect(ifNode.parameters.conditions.string[0].operation).toBe('equal');
    });
  });

  describe('connections', () => {
    it('should have correct workflow sequence', () => {
      // Check main workflow sequence
      expect(workflow.connections['Webhook'].main[0][0].node).toBe('Architect - Analyze Requirements');
      expect(workflow.connections['Architect - Analyze Requirements'].main[0][0].node).toBe('Architect - Create Design');
      expect(workflow.connections['Architect - Create Design'].main[0][0].node).toBe('Developer - Implement Code');
      expect(workflow.connections['Developer - Implement Code'].main[0][0].node).toBe('Tester - Create Test Cases');
      expect(workflow.connections['Tester - Create Test Cases'].main[0][0].node).toBe('Tester - Run Tests');
      expect(workflow.connections['Tester - Run Tests'].main[0][0].node).toBe('Tester - Evaluate Code');
      expect(workflow.connections['Tester - Evaluate Code'].main[0][0].node).toBe('IF - Needs Refinement');
    });

    it('should have correct conditional branches', () => {
      // Check true branch (needs refinement)
      expect(workflow.connections['IF - Needs Refinement'].main[0][0].node).toBe('Developer - Refine Code');
      expect(workflow.connections['Developer - Refine Code'].main[0][0].node).toBe('Tester - Run Tests (Refined)');
      expect(workflow.connections['Tester - Run Tests (Refined)'].main[0][0].node).toBe('Tester - Evaluate Code (Refined)');
      expect(workflow.connections['Tester - Evaluate Code (Refined)'].main[0][0].node).toBe('Prepare Final Output');
      
      // Check false branch (no refinement needed)
      expect(workflow.connections['IF - Needs Refinement'].main[1][0].node).toBe('Prepare Final Output');
    });

    it('should have correct final output and response', () => {
      expect(workflow.connections['Prepare Final Output'].main[0][0].node).toBe('Respond to Webhook');
    });
  });

  describe('data flow', () => {
    it('should pass task and requirements through the workflow', () => {
      const designNode = workflow.nodes.find(node => node.name === 'Architect - Create Design');
      expect(designNode.parameters.taskDescription).toContain('$json.task');
      expect(designNode.parameters.requirements).toContain('$json.requirements');
      
      const implementNode = workflow.nodes.find(node => node.name === 'Developer - Implement Code');
      expect(implementNode.parameters.taskDescription).toContain('$json.task');
      expect(implementNode.parameters.design).toContain('$node[\'Architect - Create Design\']');
    });

    it('should pass code and test results through the workflow', () => {
      const createTestsNode = workflow.nodes.find(node => node.name === 'Tester - Create Test Cases');
      expect(createTestsNode.parameters.code).toContain('$node[\'Developer - Implement Code\']');
      
      const runTestsNode = workflow.nodes.find(node => node.name === 'Tester - Run Tests');
      expect(runTestsNode.parameters.code).toContain('$node[\'Developer - Implement Code\']');
      expect(runTestsNode.parameters.testCases).toContain('$node[\'Tester - Create Test Cases\']');
      
      const evaluateNode = workflow.nodes.find(node => node.name === 'Tester - Evaluate Code');
      expect(evaluateNode.parameters.code).toContain('$node[\'Developer - Implement Code\']');
      expect(evaluateNode.parameters.testResults).toContain('$node[\'Tester - Run Tests\']');
    });

    it('should handle refinement flow correctly', () => {
      const refineNode = workflow.nodes.find(node => node.name === 'Developer - Refine Code');
      expect(refineNode.parameters.code).toContain('$node[\'Developer - Implement Code\']');
      expect(refineNode.parameters.feedback).toContain('$node[\'Tester - Evaluate Code\']');
      
      const runRefinedNode = workflow.nodes.find(node => node.name === 'Tester - Run Tests (Refined)');
      expect(runRefinedNode.parameters.code).toContain('$node[\'Developer - Refine Code\']');
      
      const evaluateRefinedNode = workflow.nodes.find(node => node.name === 'Tester - Evaluate Code (Refined)');
      expect(evaluateRefinedNode.parameters.code).toContain('$node[\'Developer - Refine Code\']');
    });

    it('should prepare final output correctly', () => {
      const finalOutputNode = workflow.nodes.find(node => node.name === 'Prepare Final Output');
      expect(finalOutputNode.parameters.content).toContain('$json.task');
      expect(finalOutputNode.parameters.content).toContain('$json.requirements');
      expect(finalOutputNode.parameters.content).toContain('$node[\'Architect - Create Design\']');
      expect(finalOutputNode.parameters.content).toContain('$node[\'IF - Needs Refinement\'].json.true');
      expect(finalOutputNode.parameters.content).toContain('$node[\'Developer - Implement Code\']');
      expect(finalOutputNode.parameters.content).toContain('$node[\'Developer - Refine Code\']');
    });
  });
});