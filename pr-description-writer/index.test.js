const { buildPrompt, fileExists, calculateLLMSimilarity } = require('./test-utils');

// Test buildPrompt function
describe('buildPrompt', () => {
    test('builds basic prompt with file changes only', () => {
        const fileChanges = [
            { filename: 'test.js', status: 'modified', content: 'test content' }
        ];
        const prTemplate = '';
        const customPrompt = '';
        const prExamples = [];
        const currentBody = '';

        const result = buildPrompt(fileChanges, prTemplate, customPrompt, prExamples, currentBody);

        expect(result).toContain('CODE CHANGES:');
        expect(result).toContain('test.js');
        expect(result).not.toContain('PR TEMPLATE TO FILL:');
        expect(result).not.toContain('CUSTOM INSTRUCTIONS:');
        expect(result).not.toContain('EXAMPLE PRS:');
    });

    test('includes PR template when provided', () => {
        const fileChanges = [
            { filename: 'test.js', status: 'modified', content: 'test content' }
        ];
        const prTemplate = '## What changed\n\n## Why';
        const customPrompt = '';
        const prExamples = [];
        const currentBody = '';

        const result = buildPrompt(fileChanges, prTemplate, customPrompt, prExamples, currentBody);

        expect(result).toContain('PR TEMPLATE TO FILL:');
        expect(result).toContain('## What changed');
    });

    test('includes custom prompt when provided', () => {
        const fileChanges = [
            { filename: 'test.js', status: 'modified', content: 'test content' }
        ];
        const prTemplate = '';
        const customPrompt = 'Use bullet points for changes';
        const prExamples = [];
        const currentBody = '';

        const result = buildPrompt(fileChanges, prTemplate, customPrompt, prExamples, currentBody);

        expect(result).toContain('CUSTOM INSTRUCTIONS:');
        expect(result).toContain('Use bullet points for changes');
    });

    test('includes PR examples when provided', () => {
        const fileChanges = [
            { filename: 'test.js', status: 'modified', content: 'test content' }
        ];
        const prTemplate = '';
        const customPrompt = '';
        const prExamples = [
            { title: 'Example PR', body: 'Example description', url: 'https://github.com/example/repo/pull/1' }
        ];
        const currentBody = '';

        const result = buildPrompt(fileChanges, prTemplate, customPrompt, prExamples, currentBody);

        expect(result).toContain('EXAMPLE PRS:');
        expect(result).toContain('Example PR');
        expect(result).toContain('Example description');
    });

    test('includes current PR description when provided', () => {
        const fileChanges = [
            { filename: 'test.js', status: 'modified', content: 'test content' }
        ];
        const prTemplate = '';
        const customPrompt = '';
        const prExamples = [];
        const currentBody = 'This is the current PR description.';

        const result = buildPrompt(fileChanges, prTemplate, customPrompt, prExamples, currentBody);

        expect(result).toContain('CURRENT PR DESCRIPTION:');
        expect(result).toContain('This is the current PR description.');
    });

    test('does not include current PR description section when empty', () => {
        const fileChanges = [
            { filename: 'test.js', status: 'modified', content: 'test content' }
        ];
        const prTemplate = '';
        const customPrompt = '';
        const prExamples = [];
        const currentBody = '';

        const result = buildPrompt(fileChanges, prTemplate, customPrompt, prExamples, currentBody);

        expect(result).not.toContain('CURRENT PR DESCRIPTION:');
    });
});

// Test fileExists function
describe('fileExists', () => {
    test('returns true for existing file', async () => {
        // Mock fs.access to resolve for existing file
        jest.spyOn(require('fs').promises, 'access').mockResolvedValueOnce();

        const result = await fileExists('existing-file.md');
        expect(result).toBe(true);
    });

    test('returns false for non-existing file', async () => {
        // Mock fs.access to reject for non-existing file
        jest.spyOn(require('fs').promises, 'access').mockRejectedValueOnce(new Error('ENOENT'));

        const result = await fileExists('non-existing-file.md');
        expect(result).toBe(false);
    });
});

// Test calculateLLMSimilarity function
describe('calculateLLMSimilarity', () => {
    test('returns 1.0 when title and description are identical', async () => {
        const existingTitle = 'Fix login bug';
        const existingBody = 'This PR fixes the login bug that was causing users to be logged out randomly.';
        const newTitle = 'Fix login bug';
        const newBody = 'This PR fixes the login bug that was causing users to be logged out randomly.';
        
        const similarity = await calculateLLMSimilarity(
            existingTitle, 
            existingBody, 
            newTitle, 
            newBody, 
            'openai', 
            'fake_api_key', 
            'fake_model'
        );
        
        expect(similarity).toBe(1.0);
    });
    
    test('returns 0.7 when titles are the same but descriptions differ', async () => {
        const existingTitle = 'Fix login bug';
        const existingBody = 'This PR fixes the login bug that was causing users to be logged out randomly.';
        const newTitle = 'Fix login bug';
        const newBody = 'This PR adds a fix for the login issue where sessions were being terminated unexpectedly.';
        
        const similarity = await calculateLLMSimilarity(
            existingTitle, 
            existingBody, 
            newTitle, 
            newBody, 
            'openai', 
            'fake_api_key', 
            'fake_model'
        );
        
        expect(similarity).toBe(0.7);
    });
    
    test('returns 0.6 when descriptions are the same but titles differ', async () => {
        const existingTitle = 'Fix login bug';
        const existingBody = 'This PR fixes the login bug that was causing users to be logged out randomly.';
        const newTitle = 'Resolve authentication issue';
        const newBody = 'This PR fixes the login bug that was causing users to be logged out randomly.';
        
        const similarity = await calculateLLMSimilarity(
            existingTitle, 
            existingBody, 
            newTitle, 
            newBody, 
            'openai', 
            'fake_api_key', 
            'fake_model'
        );
        
        expect(similarity).toBe(0.6);
    });
    
    test('calculates basic word-based similarity when both title and description differ', async () => {
        const existingTitle = 'Fix login bug';
        const existingBody = 'This PR fixes the login bug that was causing users to be logged out randomly.';
        const newTitle = 'Resolve authentication issue';
        const newBody = 'This pull request resolves the authentication problem where users were unexpectedly logged out.';
        
        const similarity = await calculateLLMSimilarity(
            existingTitle, 
            existingBody, 
            newTitle, 
            newBody, 
            'openai', 
            'fake_api_key', 
            'fake_model'
        );
        
        // Some similarity should be detected (actual value depends on our implementation)
        expect(similarity).toBeGreaterThan(0.2);
        expect(similarity).toBeLessThan(0.6);
    });
    
    test('returns low similarity when content is completely different', async () => {
        const existingTitle = 'Fix login bug';
        const existingBody = 'This PR fixes the login bug that was causing users to be logged out randomly.';
        const newTitle = 'Add dark mode support';
        const newBody = 'This PR implements a new dark mode theme for the application.';
        
        const similarity = await calculateLLMSimilarity(
            existingTitle, 
            existingBody, 
            newTitle, 
            newBody, 
            'openai', 
            'fake_api_key', 
            'fake_model'
        );
        
        // Expect low similarity
        expect(similarity).toBeLessThan(0.3);
    });
    
    test('handles empty or null inputs gracefully', async () => {
        // Empty existing content
        let similarity = await calculateLLMSimilarity(
            '', 
            '', 
            'New Title', 
            'New Description', 
            'openai', 
            'fake_api_key', 
            'fake_model'
        );
        expect(similarity).toBe(0.2); // Default for very different content
        
        // Empty new content
        similarity = await calculateLLMSimilarity(
            'Existing Title', 
            'Existing Description', 
            '', 
            '', 
            'openai', 
            'fake_api_key', 
            'fake_model'
        );
        expect(similarity).toBe(0.2); // Default for very different content
    });
});
