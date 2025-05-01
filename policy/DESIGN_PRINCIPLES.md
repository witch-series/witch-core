# Design Principles

This document explains the specific design principles and technical guidelines for witch-core.

## Code Structure and Naming Conventions

1. **Package Structure**
   - `src/` - Main source code
   - `examples/` - Usage examples and sample code
   - `tools/` - Utility tools and scripts
   - `tests/` - Test code (to be added in the future)
   - `docs/` - Documentation (to be added in the future)
   - `policy/` - Development policies and design principles

2. **Naming Conventions**
   - Module names: snake_case (`file_utils.py`)
   - Class names: PascalCase (`ServerRegistry`)
   - Function and variable names: snake_case (`calculate_hash`)
   - Constants: UPPER_CASE with underscores (`MAX_CONNECTIONS`)
   - Private methods/variables: begin with underscore (`_private_method`)

3. **File Structure**
   - Document string describing the module overview at the beginning of the file
   - Import order: standard library → third-party packages → custom modules
   - Class/function definitions
   - `if __name__ == "__main__"` block (if needed)

## Module Design

1. **File Size Limitations**
   - Target approximately 500 lines per file
   - Split complex modules into multiple files by functionality

2. **Dependency Management**
   - Avoid circular dependencies
   - Depend on interfaces rather than concrete implementations
   - Ensure submodules do not depend on parent modules

3. **Interface Design**
   - Clearly document public interfaces
   - Hide internal implementation details
   - Maintain consistent API design

## Error Handling

1. **Exception Handling Guidelines**
   - Catch exceptions at appropriate granularity
   - Use specific exception types when possible
   - After catching an exception, properly handle or propagate it
   - Make user-facing error messages clear and practical

2. **Logging Strategy**
   - `DEBUG`: Detailed information for developers
   - `INFO`: General operational information
   - `WARNING`: Situations that might cause problems
   - `ERROR`: When processing has failed
   - `CRITICAL`: Serious problems affecting the entire system

## Performance and Optimization

1. **Resource Usage Considerations**
   - Implementation conscious of memory usage
   - Be careful of memory leaks in long-running processes
   - Pay attention to thread usage and resource sharing

2. **Avoiding Premature Optimization**
   - First create "working code" and optimize as needed
   - Perform optimization based on profiling
   - Be careful not to sacrifice readability and maintainability

## Guidelines for LLM-Compatible Code

1. **Code Splitting**
   - Split code appropriately so it can be fully understood within an LLM's context window
   - Group related functionalities and ensure traceability

2. **Clear Documentation**
   - Explain the "why" behind implementations
   - Write comments that clearly convey the code's intent
   - Explain design decisions and trade-offs

3. **Consistent Structure**
   - Implement similar functionality in similar ways
   - Use consistent patterns and naming conventions
   - Maintain a unified structure throughout the project

## Source Code Integrity and Hash Calculation

1. **Source Directory Hash Verification**
   - The integrity of the `src/` directory is verified using hash values
   - These hash calculations are used to ensure compatibility between nodes
   - Consistent hash values across different environments are critical for proper communication

2. **Excluded Files and Directories**
   - `__pycache__` directories must not be included in the source tree
   - `.pyc` and other bytecode files must not be generated or committed
   - Temporary files (`.tmp`, `.bak`, etc.) should be excluded
   - Environment-specific files should not affect hash calculations

3. **Python Bytecode Prevention**
   - Set `PYTHONDONTWRITEBYTECODE=1` in your development environment
   - Use the `-B` flag when running Python scripts
   - Projects should implement `sys.dont_write_bytecode = True` at import time
   - Use the provided cleanup tools to remove any existing bytecode files

4. **Hash Calculation Consistency**
   - All hash calculations must be deterministic across different platforms
   - File paths must be normalized before hashing
   - Line endings should be normalized to ensure cross-platform compatibility
   - File modification timestamps should not affect hash calculations

## File Formatting and Language

1. **End of File Formatting**
   - All code files must end with a newline character
   - This includes Python files, markdown files, and configuration files

2. **Language Requirements**
   - All files must be written in English
   - This includes code, comments, documentation, and README files
   - No mixed-language content should be used in the codebase