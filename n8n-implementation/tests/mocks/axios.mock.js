/**
 * Mock implementation of axios for testing.
 * 
 * This module provides mock implementations of axios functions used in the code,
 * allowing tests to run without depending on the actual axios implementation.
 */

// Mock response data for different API calls
const mockResponses = {
  // Mock response for Ollama API calls
  ollama: {
    // Response for generating text
    generate: {
      model: "llama3.1:8b",
      created_at: "2025-08-17T19:44:00.000Z",
      response: "This is a mock response from the Ollama API.",
      done: true
    },
    // Response for creating a design
    design: {
      model: "llama3.1:8b",
      created_at: "2025-08-17T19:44:00.000Z",
      response: `
# Design

## Components
- Component 1
- Component 2

## Interfaces
- Interface 1
- Interface 2

## Data Flow
- Data flows from Component 1 to Component 2

## Design Patterns
- Factory Pattern
- Observer Pattern

## Challenges
- Challenge 1
- Challenge 2
      `,
      done: true
    },
    // Response for analyzing requirements
    analyze: {
      model: "llama3.1:8b",
      created_at: "2025-08-17T19:44:00.000Z",
      response: `
# Architectural Considerations

Based on the requirements, here are the key architectural considerations:

## Functional Requirements
- Must handle negative numbers
- Should include proper error handling
- Should have clear documentation

## Non-functional Requirements
- Should be optimized for performance

## Technical Constraints
- None specified

## Potential Approaches
- Iterative approach for better performance
- Recursive approach for clarity
- Memoization for optimization

## Trade-offs
- Performance vs. readability
- Simplicity vs. robustness
      `,
      done: true
    }
  }
};

// Mock implementation of axios.post
const post = jest.fn((url, data) => {
  // Check if this is an Ollama API call
  if (url.includes('ollama') || url.includes('11434')) {
    // Determine the type of response based on the prompt
    const prompt = data.prompt || '';
    
    if (prompt.includes('design') || prompt.includes('Design')) {
      return Promise.resolve({ data: mockResponses.ollama.design });
    } else if (prompt.includes('analyze') || prompt.includes('Analyze')) {
      return Promise.resolve({ data: mockResponses.ollama.analyze });
    } else {
      return Promise.resolve({ data: mockResponses.ollama.generate });
    }
  }
  
  // Default response for unknown URLs
  return Promise.resolve({
    data: {
      message: "Mock response for unknown URL",
      url: url,
      data: data
    }
  });
});

// Export the mock axios module
module.exports = {
  post,
  get: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  patch: jest.fn()
};