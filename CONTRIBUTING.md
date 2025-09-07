# Contributing to Ducky

First off, thank you for considering contributing to Ducky! It's people like you that make open-source software such a powerful tool. Ducky is a community-driven project, and we welcome any contribution, no matter how small.

This document provides guidelines for contributing to the project.

## How Can I Contribute?

There are many ways you can contribute to the Ducky project:

*   **Reporting Bugs:** If you find a bug, please let us know!
*   **Suggesting Enhancements:** Have a great idea for a new feature or an improvement to an existing one?
*   **Writing Documentation:** Good documentation is crucial. You can help improve the README, `docs.html`, or even add comments to the code.
*   **Submitting Code:** If you're a developer, you can contribute directly by fixing bugs or adding new features.

## Reporting Bugs

Before reporting a bug, please search the existing [GitHub Issues](https://github.com/thecmdguy/Ducky/issues) to see if someone has already reported it.

When filing a bug report, please provide as much detail as possible:

1.  **A clear and descriptive title.**
2.  **Steps to reproduce the bug.** Be as specific as possible.
3.  **What you expected to happen.**
4.  **What actually happened.** Include screenshots, error messages, and console output.
5.  **Your operating system and Ducky version.**

## Suggesting Enhancements

We'd love to hear your ideas for making Ducky better. Please open an issue on GitHub with the label `enhancement`. Describe your idea clearly, explaining the problem you're trying to solve and how your proposed feature would help.

## Code Contributions

If you'd like to contribute code, please follow these steps:

#### 1. Set Up Your Environment

1.  **Fork the repository:** Click the "Fork" button on the top right of the [Ducky GitHub page](https://github.com/thecmdguy/Ducky). This creates a copy of the project under your own GitHub account.
2.  **Clone your fork:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/Ducky.git
    cd Ducky
    ```
3.  **Set up for development:** Create a virtual environment and install the project in "editable" mode. This will also install all the development dependencies.
    ```powershell
    # Create and activate a virtual environment
    python -m venv venv
    .\venv\Scripts\activate

    # Install the project in editable mode
    pip install -e .
    ```

#### 2. Make Your Changes

*   Create a new branch for your feature or bug fix. This keeps your changes organized.
    ```bash
    git checkout -b my-awesome-new-feature
    ```
*   Write your code! Make your changes to the files in the `src/ducky_app` directory.
*   Try to follow the existing code style. We generally follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide.

#### 3. Submit a Pull Request

1.  Commit your changes with a clear and descriptive commit message.
    ```bash
    git add .
    git commit -m "feat: Add my awesome new feature"
    ```
2.  Push your changes to your fork on GitHub.
    ```bash
    git push origin my-awesome-new-feature
    ```
3.  Go to your fork on GitHub. You should see a new button prompting you to "Compare & pull request". Click it.
4.  Write a clear description of the changes you've made and why. If it fixes an existing issue, be sure to reference it (e.g., "Closes #123").
5.  Submit the pull request! We will review it as soon as we can.

Thank you again for your interest in contributing!
