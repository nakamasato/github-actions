const core = require('@actions/core');
const github = require('@actions/github');
const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');

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
        let prTemplate;
        try {
            prTemplate = await fs.readFile(prTemplatePath, 'utf8');
        } catch (error) {
            core.warning(`Could not read PR template: ${error.message}`);
            prTemplate = '';
        }

        // Read custom prompt if available
        let customPrompt = '';
        if (promptPath) {
            try {
                customPrompt = await fs.readFile(promptPath, 'utf8');
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

        // Call the appropriate LLM API
        let generatedContent;
        if (llmProvider === 'openai') {
            generatedContent = await callOpenAI(prompt, openaiApiKey, openaiModel);
        } else if (llmProvider === 'anthropic') {
            generatedContent = await callAnthropic(prompt, anthropicApiKey, anthropicModel);
        } else {
            throw new Error(`Unsupported LLM provider: ${llmProvider}`);
        }

        // Parse the generated content to extract title and description
        const { title, body } = parseGeneratedContent(generatedContent);

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
                messages: [{ role: 'user', content: prompt }],
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

        return response.data.choices[0].message.content;
    } catch (error) {
        throw new Error(`OpenAI API error: ${error.message}`);
    }
}

async function callAnthropic(prompt, apiKey, model) {
    try {
        const response = await axios.post(
            'https://api.anthropic.com/v1/messages',
            {
                model: model,
                messages: [{ role: 'user', content: prompt }],
                max_tokens: 2000,
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Anthropic-Version': '2023-06-01',
                    'x-api-key': apiKey
                }
            }
        );

        return response.data.content[0].text;
    } catch (error) {
        throw new Error(`Anthropic API error: ${error.message}`);
    }
}

function parseGeneratedContent(content) {
    // Default values
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

run().catch(error => {
    core.setFailed(`Unhandled error: ${error.message}`);
});
