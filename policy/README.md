# Development Policy

This document explains the development policy for the witch-core project. This framework is designed as a common foundation for other AI-powered projects.

## Basic Principles

1. **Balanced Approach to Dependencies**
   - Prefer Python standard library for core functionality to minimize external dependencies
   - Use well-established external packages when they significantly simplify code or improve performance
   - Selection of third-party libraries requires consideration of maintenance, security, and long-term support

2. **Emphasis on Readability**
   - Write code that is readable for both humans and LLMs (Large Language Models)
   - Maintain sufficient comments, clear variable names, and logical structure
   - Describe the purpose and main functions of the module at the beginning of each file

3. **Module Division**
   - Appropriately divide modules by functionality and follow the single responsibility principle
   - Split long files into multiple smaller files
   - Include a README in each directory explaining the role of the files

4. **Design as a Common Foundation**
   - Design generically so that it can be reused in other AI projects
   - Implement features that depend on specific use cases in an extensible form

## Coding Conventions

1. **Documentation**
   - Include docstrings for all functions and classes
   - Specify arguments, return values, and exceptions
   - Add line comments for complex logic

2. **Type Hints**
   - Use type hints for function parameters and return values
   - Provide type information for complex data structures

3. **Error Handling**
   - Implement appropriate exception handling and provide clear error messages
   - Provide information so users and client code can address issues

4. **Logging**
   - Use log levels appropriately (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - Do not record sensitive information in logs

## Architecture Design

1. **Layer Separation**
   - Clearly separate network layer, protocol layer, utility layer, etc.
   - Define the scope of responsibility for each layer and manage dependencies appropriately

2. **Interface Stability**
   - Prioritize stability in public APIs and maintain compatibility
   - Design so that changes to internal implementations do not affect external usage

3. **Separation of Configuration and Code**
   - Avoid hardcoding and externalize configuration
   - Provide default settings while making customization easy

## Testing and Documentation

1. **Test Coverage**
   - Create unit tests for key functionality
   - Write tests that consider edge cases

2. **Documentation**
   - Provide user manuals
   - Enhance examples and tutorials
   - Place READMEs in each directory explaining the role of the files

## Compatibility with LLMs

1. **LLM-Friendly Code**
   - Avoid complex abbreviations and specialized terms, use clear naming conventions
   - Structure and divide appropriately so that context is easy to understand
   - Use consistent patterns to increase predictability

2. **AI Development Support**
   - Structure code so that AI tools can understand it easily
   - Strive for designs that are receptive to AI suggestions and extensions

## Security Considerations

1. **Data Validation**
   - Always validate data received from external sources
   - Safely process untrusted input

2. **Secure Default Settings**
   - Use the most secure settings by default
   - Clearly indicate security risks when changing settings
