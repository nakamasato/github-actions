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

function buildPrompt(fileChanges, prTemplate, customPrompt, prExamples) {
    let prompt = `You are a GitHub PR description writer. Your task is to generate a title and description for a pull request based on the code changes.

CODE CHANGES:
${JSON.stringify(fileChanges, null, 2)}

`;

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
Please generate a concise, informative PR title and description that summarizes the changes and their purpose.
The title should be clear and descriptive.
The description should explain the purpose of the changes and any relevant details.
If a PR template is provided, use it to structure your description.`;

    return prompt;
}

module.exports = {
    buildPrompt,
    fileExists
};
