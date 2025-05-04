const axios = require('axios');
const core = require('@actions/core');

// Import the actual function from index.js using NODE_ENV=test
process.env.NODE_ENV = 'test';
const { calculateLLMSimilarity } = require('./index');

// Mock axios
jest.mock('axios');

// Mock core.info and core.warning
jest.spyOn(core, 'info').mockImplementation(() => {});
jest.spyOn(core, 'warning').mockImplementation(() => {});

describe('calculateLLMSimilarity (actual implementation)', () => {
    beforeEach(() => {
        // Clear all mocks before each test
        jest.clearAllMocks();
    });

    test('calculates similarity using OpenAI', async () => {
        // Mock OpenAI response
        axios.post.mockResolvedValueOnce({
            data: {
                choices: [
                    {
                        message: {
                            content: '0.85'
                        }
                    }
                ]
            }
        });

        const similarity = await calculateLLMSimilarity(
            'Fix login bug',
            'This PR fixes the login bug',
            'Fix authentication issue',
            'This PR fixes an auth problem',
            'openai',
            'fake_api_key',
            'gpt-4'
        );

        // Check result
        expect(similarity).toBe(0.85);
        
        // Verify that axios was called correctly
        expect(axios.post).toHaveBeenCalledWith(
            'https://api.openai.com/v1/chat/completions',
            expect.objectContaining({
                model: 'gpt-4',
                temperature: 0.1,
                max_tokens: 10
            }),
            expect.objectContaining({
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer fake_api_key'
                }
            })
        );
    });

    test('calculates similarity using Anthropic', async () => {
        // Mock Anthropic response
        axios.post.mockResolvedValueOnce({
            data: {
                content: [
                    {
                        text: '0.72'
                    }
                ]
            }
        });

        const similarity = await calculateLLMSimilarity(
            'Fix login bug',
            'This PR fixes the login bug',
            'Fix authentication issue',
            'This PR fixes an auth problem',
            'anthropic',
            'fake_api_key',
            'claude-3'
        );

        // Check result
        expect(similarity).toBe(0.72);
        
        // Verify that axios was called correctly
        expect(axios.post).toHaveBeenCalledWith(
            'https://api.anthropic.com/v1/messages',
            expect.objectContaining({
                model: 'claude-3',
                temperature: 0.1,
                max_tokens: 10
            }),
            expect.objectContaining({
                headers: {
                    'Content-Type': 'application/json',
                    'Anthropic-Version': '2023-06-01',
                    'x-api-key': 'fake_api_key'
                }
            })
        );
    });

    test('handles OpenAI errors gracefully', async () => {
        // Mock OpenAI error
        axios.post.mockRejectedValueOnce(new Error('API error'));

        const similarity = await calculateLLMSimilarity(
            'Fix login bug',
            'This PR fixes the login bug',
            'Fix authentication issue',
            'This PR fixes an auth problem',
            'openai',
            'fake_api_key',
            'gpt-4'
        );

        // When there's an error, the function should return 0
        expect(similarity).toBe(0);
        expect(core.warning).toHaveBeenCalled();
    });

    test('handles Anthropic errors gracefully', async () => {
        // Mock Anthropic error
        axios.post.mockRejectedValueOnce(new Error('API error'));

        const similarity = await calculateLLMSimilarity(
            'Fix login bug',
            'This PR fixes the login bug',
            'Fix authentication issue',
            'This PR fixes an auth problem',
            'anthropic',
            'fake_api_key',
            'claude-3'
        );

        // When there's an error, the function should return 0
        expect(similarity).toBe(0);
        expect(core.warning).toHaveBeenCalled();
    });

    test('handles malformed OpenAI responses gracefully', async () => {
        // Mock malformed OpenAI response
        axios.post.mockResolvedValueOnce({
            data: {
                choices: [
                    {
                        message: {
                            content: 'not a number'
                        }
                    }
                ]
            }
        });

        const similarity = await calculateLLMSimilarity(
            'Fix login bug',
            'This PR fixes the login bug',
            'Fix authentication issue',
            'This PR fixes an auth problem',
            'openai',
            'fake_api_key',
            'gpt-4'
        );

        // When the response doesn't contain a valid number, it should default to 0
        expect(similarity).toBe(0);
    });

    test('handles malformed Anthropic responses gracefully', async () => {
        // Mock malformed Anthropic response
        axios.post.mockResolvedValueOnce({
            data: {
                content: [
                    {
                        text: 'not a number'
                    }
                ]
            }
        });

        const similarity = await calculateLLMSimilarity(
            'Fix login bug',
            'This PR fixes the login bug',
            'Fix authentication issue',
            'This PR fixes an auth problem',
            'anthropic',
            'fake_api_key',
            'claude-3'
        );

        // When the response doesn't contain a valid number, it should default to 0
        expect(similarity).toBe(0);
    });

    test('handles unsupported LLM provider', async () => {
        const similarity = await calculateLLMSimilarity(
            'Fix login bug',
            'This PR fixes the login bug',
            'Fix authentication issue',
            'This PR fixes an auth problem',
            'unknown_provider',
            'fake_api_key',
            'model'
        );
        
        // The function catches the error and returns 0
        expect(similarity).toBe(0);
        expect(core.warning).toHaveBeenCalled();
    });

    test('clamps similarity values to be between 0 and 1', async () => {
        // Mock response with value > 1
        axios.post.mockResolvedValueOnce({
            data: {
                choices: [
                    {
                        message: {
                            content: '1.5'
                        }
                    }
                ]
            }
        });

        let similarity = await calculateLLMSimilarity(
            'Fix login bug',
            'This PR fixes the login bug',
            'Fix authentication issue',
            'This PR fixes an auth problem',
            'openai',
            'fake_api_key',
            'gpt-4'
        );

        // Value should be clamped to 1.0
        expect(similarity).toBe(1.0);

        // Mock response with value < 0
        axios.post.mockResolvedValueOnce({
            data: {
                choices: [
                    {
                        message: {
                            content: '-0.5'
                        }
                    }
                ]
            }
        });

        similarity = await calculateLLMSimilarity(
            'Fix login bug',
            'This PR fixes the login bug',
            'Fix authentication issue',
            'This PR fixes an auth problem',
            'openai',
            'fake_api_key',
            'gpt-4'
        );

        // Value should be clamped to 0
        expect(similarity).toBeGreaterThanOrEqual(0);
    });
});