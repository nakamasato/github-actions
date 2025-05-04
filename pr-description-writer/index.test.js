const { buildPrompt, fileExists } = require('./test-utils');

// Test buildPrompt function
describe('buildPrompt', () => {
    test('builds basic prompt with file changes only', () => {
        const fileChanges = [
            { filename: 'test.js', status: 'modified', content: 'test content' }
        ];
        const prTemplate = '';
        const customPrompt = '';
        const prExamples = [];

        const result = buildPrompt(fileChanges, prTemplate, customPrompt, prExamples);

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

        const result = buildPrompt(fileChanges, prTemplate, customPrompt, prExamples);

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

        const result = buildPrompt(fileChanges, prTemplate, customPrompt, prExamples);

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

        const result = buildPrompt(fileChanges, prTemplate, customPrompt, prExamples);

        expect(result).toContain('EXAMPLE PRS:');
        expect(result).toContain('Example PR');
        expect(result).toContain('Example description');
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
