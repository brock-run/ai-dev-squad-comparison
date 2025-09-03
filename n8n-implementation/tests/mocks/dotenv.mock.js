/**
 * Mock implementation of dotenv for testing.
 * 
 * This module provides mock implementations of dotenv functions used in the code,
 * allowing tests to run without depending on the actual dotenv implementation.
 */

// Mock environment variables
const mockEnv = {
  OLLAMA_BASE_URL: 'http://localhost:11434',
  OLLAMA_MODEL_ARCHITECT: 'llama3.1:8b',
  OLLAMA_MODEL_DEVELOPER: 'codellama:13b',
  OLLAMA_MODEL_TESTER: 'llama3.1:8b',
  TEMPERATURE: '0.7',
  ENABLE_HUMAN_FEEDBACK: 'false',
  CODE_EXECUTION_ALLOWED: 'false'
};

// Mock implementation of dotenv.config
const config = jest.fn(() => {
  // Set environment variables
  Object.keys(mockEnv).forEach(key => {
    process.env[key] = mockEnv[key];
  });
  
  return { parsed: mockEnv };
});

// Export the mock dotenv module
module.exports = {
  config,
  parse: jest.fn(() => mockEnv)
};