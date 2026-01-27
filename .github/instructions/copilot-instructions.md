# GitHub Copilot Instructions for CITO Project

## Overview
This document provides essential guidelines for AI coding agents to effectively navigate and contribute to the CITO project. Understanding the architecture, workflows, and conventions is crucial for productivity.

## Project Structure
The CITO project is organized into several key directories:

- **docs/**: Contains general documentation, including functional and technical requirements, Copilot usage guides, and domain knowledge.
- **poc/**: Houses Proof of Concept (PoC) directories, where technical experiments and controlled versions are centralized.
  - **v-a33-240125/**: A specific version of the PoC, representing a complete snapshot of the ETL pipeline.
  - **config/**: External configuration files, including service account credentials for Google integration.

## Key Components
- **a_load_configs.py**: Loads and normalizes external configurations, centralizing pipeline parameters for easy adjustments.
- **b_search_save_html.py**: Handles HTML searching and saving processes.
- **c_extract_data.py**: Responsible for basic data extraction tasks.

## Developer Workflows
- **Building**: Ensure all dependencies are installed as specified in the `requirements.txt` file located in the PoC directories.
- **Testing**: Use the provided test scripts to validate functionality after making changes. Ensure tests cover all critical paths.
- **Debugging**: Utilize logging within the Python scripts to trace execution and identify issues. Familiarize yourself with the logging configuration in `config/`.

## Project-Specific Conventions
- Follow the naming conventions for Python files and functions as outlined in the documentation. Use snake_case for file names and function definitions.
- Maintain consistent indentation and code formatting as per PEP 8 guidelines.

## Integration Points
- The project integrates with Google Sheets via service account credentials stored in `config/service_account.json`. Ensure these credentials are correctly configured for successful API interactions.

## Communication Patterns
- Components communicate through function calls and shared configuration files. Ensure that any changes to the configuration are reflected across all relevant modules.

## Conclusion
By adhering to these guidelines, AI coding agents can effectively contribute to the CITO project, ensuring alignment with existing practices and enhancing overall productivity.