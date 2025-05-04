const core = require('@actions/core');
const github = require('@actions/github');
const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');

// Helper function to check if a file exists
async function fileExists(filePath) {
    try {
        await fs.access(filePath);
        return true;
    } catch {
        return false;
    }
}

async function run() {
    try {
        // Get inputs
        const prs = core.getInput('prs');
        const prTemplatePath = core.getInput('pull_request_template_path');
        const promptPath = core.getInput('prompt_path');
        const githubToken = core.getInput('github_token');
        const llmProvider = core.getInput('llm_provider');
        const openaiApiKey = core.getInput('openai_api_key');
        const openaiModel = core.getInput('openai_model');
        const anthropicApiKey = core.getInput('anthropic_api_key');
        const anthropicModel = core.getInput('anthropic_model');

        // Initialize Octokit client
        const octokit = github.getOctokit(githubToken);
        const context = github.context;
        const { owner, repo } = context.repo;

        // Get current PR number from context
        const prNumber = context.payload.pull_request?.number;
        if (!prNumber) {
            throw new Error('This action must be run in the context of a pull request');
        }

        // Fetch changed files in the PR
        const { data: changedFiles } = await octokit.rest.pulls.listFiles({
            owner,
            repo,
            pull_number: prNumber,
        });

        // Build a collection of file changes
        const fileChanges = [];
        for (const file of changedFiles) {
            if (file.status === 'removed') {
                // For removed files, just note that they were removed
                fileChanges.push({
                    filename: file.filename,
                    status: 'removed'
                });
            } else {
                // For added/modified files, fetch the content
                let fileContent;
                try {
                    const { data: fileData } = await octokit.rest.repos.getContent({
                        owner,
                        repo,
                        path: file.filename,
                        ref: context.payload.pull_request.head.ref
                    });

                    // GitHub API returns content as base64
                    fileContent = Buffer.from(fileData.content, 'base64').toString();

                    // Only include reasonable sized files (to avoid token limits)
                    if (fileContent.length > 10000) {
                        fileContent = fileContent.substring(0, 10000) + "\n... (content truncated)";
                    }
                } catch (error) {
                    core.warning(`Could not fetch content for ${file.filename}: ${error.message}`);
                    fileContent = null;
                }

                fileChanges.push({
                    filename: file.filename,
                    status: file.status,
                    content: fileContent,
                    additions: file.additions,
                    deletions: file.deletions,
                    changes: file.changes
                });
            }
        }

        // Read PR template if available
        let prTemplate = '';
        if (prTemplatePath) {
            try {
                const templateExists = await fileExists(prTemplatePath);
                if (templateExists) {
                    prTemplate = await fs.readFile(prTemplatePath, 'utf8');
                } else {
                    core.info(`PR template file not found at ${prTemplatePath}. Continuing without template.`);
                }
            } catch (error) {
                core.warning(`Could not read PR template: ${error.message}`);
            }
        }

        // Read custom prompt if available
        let customPrompt = '';
        if (promptPath) {
            try {
                const promptExists = await fileExists(promptPath);
                if (promptExists) {
                    customPrompt = await fs.readFile(promptPath, 'utf8');
                } else {
                    core.info(`Custom prompt file not found at ${promptPath}. Continuing without custom prompt.`);
                }
            } catch (error) {
                core.warning(`Could not read custom prompt: ${error.message}`);
            }
        }

        // Fetch examples from past PRs if provided
        const prExamples = [];
        if (prs) {
            const prLinks = prs.split(',').map(link => link.trim());
            for (const link of prLinks) {
                try {
                    // Extract owner, repo, and PR number from link
                    const match = link.match(/github\.com\/([^\/]+)\/([^\/]+)\/pull\/(\d+)/);
                    if (match) {
                        const [_, exOwner, exRepo, exPrNumber] = match;
                        const { data: pr } = await octokit.rest.pulls.get({
                            owner: exOwner,
                            repo: exRepo,
                            pull_number: parseInt(exPrNumber)
                        });

                        prExamples.push({
                            title: pr.title,
                            body: pr.body,
                            url: link
                        });
                    }
                } catch (error) {
                    core.warning(`Could not fetch example PR: ${link} - ${error.message}`);
                }
            }
        }

        // Build prompt for the LLM
        const prompt = buildPrompt(fileChanges, prTemplate, customPrompt, prExamples);

        // Update the PR with the generated title and description
        let result;
        try {
            if (llmProvider === 'openai') {
                result = await callOpenAI(prompt, openaiApiKey, openaiModel);
            } else if (llmProvider === 'anthropic') {
                result = await callAnthropic(prompt, anthropicApiKey, anthropicModel);
            } else {
                throw new Error(`Unsupported LLM provider: ${llmProvider}`);
            }

            // No need to parse further, the API functions now always return
            // an object with title and description properties
            const title = result.title;
            const body = result.description;

            // Update the PR with the generated title and description
            await octokit.rest.pulls.update({
                owner,
                repo,
                pull_number: prNumber,
                title,
                body
            });

            core.info('Successfully updated PR title and description');
        } catch (error) {
            core.setFailed(`Failed to generate or update PR description: ${error.message}`);
        }

    } catch (error) {
        core.setFailed(`Action failed: ${error.message}`);
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
If a PR template is provided, use it to structure your description.

Your response should be in the following format:
TITLE: [generated title]

DESCRIPTION:
[generated description]`;

    return prompt;
}

async function callOpenAI(prompt, apiKey, model) {
    try {
        const response = await axios.post(
            'https://api.openai.com/v1/chat/completions',
            {
                model: model,
                messages: [{
                    role: 'user',
                    content: prompt + "\n\nReturn your response as a JSON object with 'title' and 'description' fields. Do not include any other text."
                }],
                response_format: { type: "json_object" },
                temperature: 0.7,
                max_tokens: 2000,
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                }
            }
        );

        // Parse the JSON response
        const content = response.data.choices[0].message.content;
        try {
            const parsed = JSON.parse(content);
            return {
                title: parsed.title || 'Automated PR Description',
                description: parsed.description || parsed.body || ''
            };
        } catch (error) {
            core.warning(`Failed to parse OpenAI response as JSON: ${error.message}`);
            return {
                title: 'Automated PR Description',
                description: 'The PR description could not be generated correctly. The API did not return valid JSON.'
            };
        }
    } catch (error) {
        core.error(`OpenAI API error: ${error.message}`);
        return {
            title: 'Automated PR Description',
            description: `The PR description could not be generated due to an API error: ${error.message}`
        };
    }
}

async function callAnthropic(prompt, apiKey, model) {
    try {
        const response = await axios.post(
            'https://api.anthropic.com/v1/messages',
            {
                model: model,
                messages: [{
                    role: 'user',
                    content: prompt + "\n\nReturn your response as a JSON object with 'title' and 'description' fields. The JSON object should be valid and parseable. Do not include any other text outside of the JSON object."
                }],
                max_tokens: 2000,
                system: "Return your response as a valid, parseable JSON object with 'title' and 'description' fields. Include only the JSON object in your response, with no additional explanations or text."
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Anthropic-Version': '2023-06-01',
                    'x-api-key': apiKey
                }
            }
        );

        const content = response.data.content[0].text;

        // Try to extract JSON from the response
        let jsonMatch = content.match(/\{[\s\S]*\}/);
        try {
            const jsonStr = jsonMatch ? jsonMatch[0] : content;
            const parsed = JSON.parse(jsonStr);
            return {
                title: parsed.title || 'Automated PR Description',
                description: parsed.description || parsed.body || ''
            };
        } catch (error) {
            core.warning(`Failed to parse Anthropic response as JSON: ${error.message}`);
            return {
                title: 'Automated PR Description',
                description: 'The PR description could not be generated correctly. The API did not return valid JSON.'
            };
        }
    } catch (error) {
        core.error(`Anthropic API error: ${error.message}`);
        return {
            title: 'Automated PR Description',
            description: `The PR description could not be generated due to an API error: ${error.message}`
        };
    }
}

function parseGeneratedContent(content) {
    // If we already have a parsed JSON object with title and description/body
    if (content && typeof content === 'object') {
        if (content.title) {
            // If we have a direct JSON response
            return {
                title: content.title,
                body: content.description || content.body || ''
            };
        } else if (content.rawContent) {
            // Fall back to parsing text if JSON parsing failed earlier
            const textContent = content.rawContent;
            let title = '';
            let body = '';

            // Extract title
            const titleMatch = textContent.match(/TITLE:\s*(.*?)(?:\n\n|\n|$)/);
            if (titleMatch) {
                title = titleMatch[1].trim();
            }

            // Extract description
            const bodyMatch = textContent.match(/DESCRIPTION:\s*([\s\S]*?)$/);
            if (bodyMatch) {
                body = bodyMatch[1].trim();
            }

            return { title, body };
        }
    }

    // If we have a string, try to parse it as text
    if (typeof content === 'string') {
        let title = '';
        let body = '';

        // Extract title
        const titleMatch = content.match(/TITLE:\s*(.*?)(?:\n\n|\n|$)/);
        if (titleMatch) {
            title = titleMatch[1].trim();
        }

        // Extract description
        const bodyMatch = content.match(/DESCRIPTION:\s*([\s\S]*?)$/);
        if (bodyMatch) {
            body = bodyMatch[1].trim();
        }

        return { title, body };
    }

    // Default fallback
    return {
        title: 'Automated PR Description',
        body: 'This PR description was automatically generated, but the format could not be parsed correctly.'
    };
}

run().catch(error => {
    core.setFailed(`Unhandled error: ${error.message}`);
});

// Export functions for testing
if (process.env.NODE_ENV === 'test') {
    module.exports = {
        buildPrompt,
        fileExists
    };
}
