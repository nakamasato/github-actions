const core = require('@actions/core');
const github = require('@actions/github');
const { run, processInput } = require('../src/index');

// Mock the GitHub Actions core library
jest.mock('@actions/core');
jest.mock('@actions/github');

describe('Action Name', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Reset environment
    process.env.GITHUB_REPOSITORY = 'owner/repo';
    process.env.GITHUB_EVENT_NAME = 'push';
    
    // Setup default mocks
    github.context = {
      eventName: 'push',
      repo: {
        owner: 'owner',
        repo: 'repo'
      }
    };
  });

  describe('run', () => {
    test('should complete successfully with valid input', async () => {
      // Arrange
      core.getInput.mockImplementation((name) => {
        switch (name) {
          case 'example-input':
            return 'test-value';
          case 'github-token':
            return 'fake-token';
          default:
            return '';
        }
      });

      // Act
      await run();

      // Assert
      expect(core.setOutput).toHaveBeenCalledWith('result', 'Processed: test-value');
      expect(core.setOutput).toHaveBeenCalledWith('status', 'success');
      expect(core.setFailed).not.toHaveBeenCalled();
    });

    test('should fail when required input is missing', async () => {
      // Arrange
      core.getInput.mockImplementation((name, options) => {
        if (name === 'example-input' && options?.required) {
          throw new Error('Input required and not supplied: example-input');
        }
        return '';
      });

      // Act
      await run();

      // Assert
      expect(core.setFailed).toHaveBeenCalledWith(
        expect.stringContaining('Input required and not supplied: example-input')
      );
    });

    test('should handle errors gracefully', async () => {
      // Arrange
      core.getInput.mockReturnValue('test-value');
      core.isDebug.mockReturnValue(true);
      
      // Mock processInput to throw
      const error = new Error('Processing failed');
      error.stack = 'Error stack trace';
      jest.spyOn(global, 'processInput').mockRejectedValue(error);

      // Act
      await run();

      // Assert
      expect(core.setFailed).toHaveBeenCalledWith('Action failed: Processing failed');
      expect(core.debug).toHaveBeenCalledWith('Error stack trace');
    });
  });

  describe('processInput', () => {
    test('should process input correctly', async () => {
      // Act
      const result = await processInput('test-input');

      // Assert
      expect(result).toBe('Processed: test-input');
    });
  });
});