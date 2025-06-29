const core = require('@actions/core');
const github = require('@actions/github');

async function run() {
  try {
    // Get inputs
    const exampleInput = core.getInput('example-input', { required: true });
    const token = core.getInput('github-token');
    
    core.info(`Processing with input: ${exampleInput}`);
    
    // Get the GitHub context
    const context = github.context;
    core.debug(`Event: ${context.eventName}`);
    core.debug(`Repository: ${context.repo.owner}/${context.repo.repo}`);
    
    // Initialize Octokit if token is provided
    let octokit;
    if (token) {
      octokit = github.getOctokit(token);
    }
    
    // Main logic here
    const result = await processInput(exampleInput);
    
    // Set outputs
    core.setOutput('result', result);
    core.setOutput('status', 'success');
    
    // Add to job summary
    core.summary
      .addHeading('Action Summary')
      .addTable([
        [{data: 'Input', header: true}, {data: 'Value', header: true}],
        ['Example Input', exampleInput],
        ['Result', result]
      ])
      .write();
    
  } catch (error) {
    core.setFailed(`Action failed: ${error.message}`);
    if (error.stack && core.isDebug()) {
      core.debug(error.stack);
    }
  }
}

async function processInput(input) {
  // Implement your main logic here
  return `Processed: ${input}`;
}

// Run the action
if (require.main === module) {
  run();
}

module.exports = { run, processInput };