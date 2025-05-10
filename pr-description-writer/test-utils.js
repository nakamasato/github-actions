const fs = require('fs').promises;

// Export the functions from index.js for testing
async function fileExists(filePath) {
    try {
        await fs.access(filePath);
        return true;
    } catch {
        return false;
    }
}

function buildPrompt(fileChanges, prTemplate, customPrompt, prExamples, currentBody) {
    let prompt = `You are a GitHub PR description writer. Your task is to generate a title and description for a pull request based on the code changes.

CODE CHANGES:
${JSON.stringify(fileChanges, null, 2)}

`;

    if (currentBody && currentBody.trim() !== '') {
        prompt += `CURRENT PR DESCRIPTION:
${currentBody}

`;
    }

    if (prTemplate) {
        prompt += `PR TEMPLATE TO FILL:
${prTemplate}

`;
    }

    if (customPrompt) {
        prompt += `CUSTOM INSTRUCTIONS:
${customPrompt}

`;
    }

    if (prExamples.length > 0) {
        prompt += 'EXAMPLE PRS:\n';
        prExamples.forEach((example, index) => {
            prompt += `Example ${index + 1}:\n`;
            prompt += `Title: ${example.title}\n`;
            prompt += `Body: ${example.body}\n\n`;
        });
    }

    prompt += `
Please generate a concise, informative PR description that summarizes the changes and their purpose.
The description should explain the purpose of the changes and any relevant details.
If a PR template is provided, use it to structure your description.
If a current PR description is provided, use it as a starting point and enhance it based on the code changes.
Please keep links, images, and any other references in the current body if exists.

Your response should be in the following format:
DESCRIPTION:
[generated description]`;

    return prompt;
}

// Mock implementation of calculateLLMSimilarity for testing
async function calculateLLMSimilarity(existingTitle, existingBody, newTitle, newBody, llmProvider, apiKey, model) {
    // For test purposes, implement a simple rule-based similarity metric
    
    // If both titles and descriptions are exactly the same, return 1.0 (maximum similarity)
    if (existingTitle === newTitle && existingBody === newBody) {
        return 1.0;
    }
    
    // If titles are the same but bodies are different, return 0.7
    if (existingTitle === newTitle && existingBody !== newBody) {
        return 0.7;
    }
    
    // If bodies are the same but titles are different, return 0.6
    if (existingTitle !== newTitle && existingBody === newBody) {
        return 0.6;
    }
    
    // If both are different but have some content, do a basic word-based similarity
    if (existingTitle && existingBody && newTitle && newBody) {
        // Very basic similarity calculation for testing
        // Count how many words are shared between titles and descriptions
        const existingWords = (existingTitle + " " + existingBody).toLowerCase().split(/\s+/);
        const newWords = (newTitle + " " + newBody).toLowerCase().split(/\s+/);
        
        const existingSet = new Set(existingWords);
        const newSet = new Set(newWords);
        
        let commonCount = 0;
        for (const word of existingSet) {
            if (newSet.has(word)) {
                commonCount++;
            }
        }
        
        // Basic similarity formula
        return commonCount / Math.max(existingSet.size, newSet.size);
    }
    
    // Default: low similarity (different content)
    return 0.2;
}

module.exports = {
    buildPrompt,
    fileExists,
    calculateLLMSimilarity
};
