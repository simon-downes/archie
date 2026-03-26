---
name: policy-general-coding
description: Core principles and practices for writing maintainable, high-quality code across all languages. Use when writing code, reviewing implementations, or making architectural decisions.
---

# General Coding Standards

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, MAY, and OPTIONAL in this document are to be interpreted as described in RFC 2119.

## Scope

This document defines language-agnostic principles, code quality standards, and implementation guidelines that apply across all programming languages.

Language-specific standards (tooling, syntax, idioms) are defined in separate language skills.

## Principles

### SOLID

**Single Responsibility**
- Functions/classes SHOULD have one primary purpose
- Each component should have one reason to change

**Open/Closed**
- SHOULD extend functionality through new code rather than modifying existing code
- Design for extension, not modification

**Liskov Substitution**
- Child classes MUST work wherever parent classes are expected
- Subtypes must be substitutable for their base types

**Interface Segregation**
- SHOULD create focused interfaces rather than large general ones
- Clients should not depend on interfaces they don't use

**Dependency Inversion**
- SHOULD depend on interfaces/abstractions when practical
- High-level modules should not depend on low-level modules

### DRY (Don't Repeat Yourself)

**SHOULD extract common logic when duplication creates maintenance burden**

- MUST NOT copy-paste code without considering abstraction
- SHOULD allow minor duplication if it improves code clarity
- MUST NOT extract code just to reduce line count if it hurts readability

**Balance:** Prefer clarity over strict adherence to DRY. Some duplication is acceptable if it makes code more understandable.

### YAGNI (You Aren't Gonna Need It)

**MUST implement only explicitly requested features**

- SHOULD NOT add configuration options, parameters or extension points "just in case"
- MUST resist building generic solutions for specific problems
- Wait for actual requirements before adding flexibility

**This principle directly supports the workflow constraint: questions get answers, not implementations.**

### KISS (Keep It Simple, Stupid)

**SHOULD prefer simple, understandable approaches at all levels of design**

- SHOULD avoid unnecessary complexity that doesn't reflect problem complexity
- SHOULD break complex problems into smaller, simpler parts when it improves overall system clarity
- SHOULD NOT artificially reduce complexity metrics at the expense of readability or maintainability

**Balance:** Simple doesn't mean simplistic. Match solution complexity to problem complexity.

## Code Quality

### Documentation

**MUST add docstrings to all functions and classes**

- MUST include argument and type details in docstrings only if not supported by the language
- SHOULD add comments when code intent isn't clear from reading
- MUST keep comments synchronized with code changes

**Good comments explain WHY, not WHAT:**
```
# Good - explains reasoning
# Use exponential backoff to avoid overwhelming the API during outages
retry_delay = base_delay * (2 ** attempt)

# Bad - restates the code
# Multiply base_delay by 2 to the power of attempt
retry_delay = base_delay * (2 ** attempt)
```

### Type Safety

**MUST use type hints for all function parameters and return values if the language supports types**

- MUST add variable type annotations if the language supports types
- MUST utilize type checking and linting tools when available

Type hints improve:
- Code clarity and self-documentation
- IDE support and autocomplete
- Early error detection
- Refactoring safety

### Structure

**MUST use descriptive names that communicate purpose**

- Variables, functions, classes should reveal intent
- Avoid abbreviations unless universally understood
- Use domain language that matches the problem space

**SHOULD keep functions reasonably small and focused**

- Each function should do one thing well
- If a function is hard to name, it probably does too much

**SHOULD group related functionality into modules**

- Organize code by feature or domain concept
- Keep related code together for easier understanding and maintenance

## Implementation

### Error Handling

**SHOULD handle the expected case first, then handle exceptions**

Rather than checking for every possible failure upfront, write code for the happy path and handle exceptions as they arise.

```
# Good - optimistic approach
try:
    result = process_data(input)
    return result
except ValueError as e:
    logger.error(f"Invalid input: {e}")
    return default_value

# Avoid - defensive approach
if input is None:
    return default_value
if not isinstance(input, dict):
    return default_value
if "required_field" not in input:
    return default_value
# ... finally process
```

**MUST handle expected and unexpected errors appropriately**

- Catch specific exceptions, not broad catches
- Provide context in error messages
- Log errors with appropriate severity

**MUST provide error messages appropriate to the audience/context**

- User-facing: Clear, actionable messages
- Developer-facing: Include technical details, stack traces
- Logs: Include context for debugging

### Logging

**SHOULD implement logging that aids troubleshooting without overwhelming with routine operations**

- Log significant events, state changes, errors
- Don't log every function call or routine operation
- Use appropriate log levels

**MUST use appropriate log levels based on severity and audience**

- ERROR: Something failed, requires attention
- WARN: Something unexpected, but handled
- INFO: Significant events, state changes
- DEBUG: Detailed information for troubleshooting

**MUST follow existing logging patterns in the project**

- If none exist, establish context-appropriate logging
- Be consistent with format, structure, and level usage

### Security

**MUST validate all external inputs**

- Never trust user input, API responses, file contents
- Validate type, format, range, and business rules
- Sanitize before use in queries, commands, or output

**MUST NOT hardcode secrets or credentials**

- Use environment variables, secret managers, or configuration files
- Never commit secrets to version control
- Rotate secrets regularly

**SHOULD use secure defaults**

- Fail closed, not open
- Require explicit opt-in for insecure options
- Use strong encryption, secure protocols by default

**MUST NOT place secrets or credentials in logs unless suitably masked**

- Redact sensitive data before logging
- Be careful with structured logging that might capture secrets
- Review logs for accidental exposure

### General Guidelines

**SHOULD favor readable and explicit code over compact or abstract code that reduces clarity**

- Clever code is hard to maintain
- Explicit is better than implicit
- Code is read more often than written

**SHOULD avoid premature optimization but MUST NOT ignore obvious inefficiencies**

- Profile before optimizing
- Focus on algorithmic efficiency first
- Don't sacrifice clarity for micro-optimizations
- But don't use O(n²) when O(n) is obvious

**SHOULD prefer composition over inheritance**

- Inheritance creates tight coupling
- Composition is more flexible
- Use inheritance only for true "is-a" relationships

**MUST follow consistent formatting and naming patterns**

- Consistency within a project is more important than personal preference
- Follow existing conventions
- Use automated formatters when available

**SHOULD test important business logic and edge cases**

- Focus tests on behavior, not implementation
- Test edge cases, error conditions, and boundaries
- Don't test framework code or trivial getters/setters

**MUST separate configuration from code**

- Use configuration files, environment variables, or feature flags
- Don't hardcode environment-specific values
- Make configuration explicit and discoverable
