---
name: clean-code
description: Clean Code principles for writing readable, maintainable code. Use when writing new code, reviewing, or refactoring.
allowed-tools: Read, Grep, Glob, Bash
user-invocable: true
---

# Clean Code - Pragmatic Standards

> "Any fool can write code that a computer can understand. Good programmers write code that humans can understand." — Martin Fowler

## Core Principles (Quick Reference)

| Principle | Description | Key Question |
|-----------|-------------|--------------|
| **SRP** | Single Responsibility | "Does this have only one reason to change?" |
| **DRY** | Don't Repeat Yourself | "Is this logic duplicated elsewhere?" |
| **KISS** | Keep It Simple, Stupid | "Is this the simplest solution?" |
| **YAGNI** | You Aren't Gonna Need It | "Do I need this right now?" |
| **Boy Scout** | Leave code cleaner than you found it | "Did I improve something?" |

## Naming Rules (Critical)

| Rule | Bad | Good |
|------|-----|------|
| Reveal Intent | `d` | `elapsedDays` |
| No Misinformation | `accountList` (if Set) | `accounts` |
| Meaningful Distinction | `a1, a2` | `source, destination` |
| Pronounceable | `genymdhms` | `generationTimestamp` |
| Boolean as Question | `flag` | `isActive`, `hasPermission` |
| Class = Noun | `Process` | `ConflictDetector` |
| Method = Verb | `conflict()` | `detectConflict()` |

## Function Rules

| Rule | Guideline |
|------|-----------|
| Size | Max 20 lines, ideal 4-5 |
| Arguments | Max 3, ideal 0-1 (use objects) |
| Side Effects | Name must reveal ALL actions |
| Single Purpose | "and" in description = split needed |
| No Flag Args | Boolean parameter → split into two functions |

## Class Rules

| Rule | Guideline |
|------|-----------|
| SRP | Single reason to change |
| Cohesion | Methods should use the same fields |
| Max Size | ~200 lines |
| No Train Wreck | `a.getB().getC()` → delegate |
| Law of Demeter | Only talk to immediate friends |

## Error Handling

| Don't | Do |
|-------|-----|
| Return null | Return `Optional.empty()` |
| Return error code | Throw specific exception |
| Swallow exceptions | Log or rethrow |
| Catch generic `Exception` | Catch specific types |

## Comment Philosophy

> "Comments are, at best, a necessary evil." — Robert C. Martin

Before writing a comment → **Can the code be clearer?**

| Allowed | Prohibited |
|---------|-----------|
| Legal/copyright | WHAT explanation (`// increment i`) |
| Consequence warning | Commented-out code |
| `TODO` with ticket | TODO without ticket |
| WHY explanation | Javadoc for internal methods |
| 3rd party behavior note | Redundant comments |

## Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Train Wreck | `a.getB().getC().getD()` | Delegate through methods |
| Primitive Obsession | Many raw params | Parameter Object |
| God Class | Class does everything | Split by responsibility |
| Feature Envy | Using others' data | Move method to right class |
| Magic Numbers | `if (status == 4)` | Named constants |
| Flag Arguments | `render(boolean)` | `renderSuite()`, `renderSingle()` |

## Deep Dive Chapters (MANDATORY Loading)

Each chapter maps to Robert C. Martin's "Clean Code" book. AI Agents MUST load the appropriate chapter.

### Group 1: Foundation — Philosophy, Names, Comments, Formatting

| Chapter | Topic | Importance | Trigger |
|---------|-------|------------|---------|
| [Ch1](stages/ch01-clean-code.md) | Clean Code Philosophy | **HIGH** | Understanding WHY clean code matters |
| [Ch2](stages/ch02-meaningful-names.md) | Meaningful Names | **CRITICAL** | ANY naming decision |
| [Ch4](stages/ch04-comments.md) | Comments | **CRITICAL** | BEFORE writing any comment |
| [Ch5](stages/ch05-formatting.md) | Formatting | **HIGH** | Code organization decisions |

### Group 2: Functions

| Chapter | Topic | Importance | Trigger |
|---------|-------|------------|---------|
| [Ch3](stages/ch03-functions.md) | Functions | **CRITICAL** | Writing or refactoring functions |

### Group 3: Data, Errors, Boundaries

| Chapter | Topic | Importance | Trigger |
|---------|-------|------------|---------|
| [Ch6](stages/ch06-objects-and-data-structures.md) | Objects & Data Structures | **HIGH** | Class/struct design, DTO decisions |
| [Ch7](stages/ch07-error-handling.md) | Error Handling | **HIGH** | Exception/error strategies |
| [Ch8](stages/ch08-boundaries.md) | Boundaries | **MEDIUM** | 3rd party library integration |

### Group 4: Tests, Classes, Emergence

| Chapter | Topic | Importance | Trigger |
|---------|-------|------------|---------|
| [Ch9](stages/ch09-unit-tests.md) | Unit Tests | **CRITICAL** | Writing or reviewing tests |
| [Ch10](stages/ch10-classes.md) | Classes | **HIGH** | Class design, SRP, OCP, DIP |
| [Ch12](stages/ch12-emergence.md) | Emergence | **MEDIUM** | Architectural decisions, simplicity |

### Group 5: Systems, Concurrency, Case Study, Smells

| Chapter | Topic | Importance | Trigger |
|---------|-------|------------|---------|
| [Ch11](stages/ch11-systems.md) | Systems | **MEDIUM** | DI, AOP, construction vs use |
| [Ch13](stages/ch13-concurrency.md) | Concurrency | **MEDIUM** | Multi-threading, async code |
| [Ch14](stages/ch14-successive-refinement.md) | Successive Refinement | **MEDIUM** | Refactoring strategy, case study |
| [Ch17](stages/ch17-smells-heuristics.md) | Smells & Heuristics | **HIGH** | Code review, smell detection |

## Checklists

| Checklist | Use Case |
|-----------|----------|
| [Code Review](checklists/code-review.md) | Before PR submission or code review |
| [Refactoring](checklists/refactoring.md) | Before and during refactoring |

## Validation Scripts

```bash
# Check function/method lengths
~/.claude/skills/clean-code/scripts/function-length-check.sh <source-path>

# General code quality check
~/.claude/skills/clean-code/scripts/code-quality-check.sh <source-path>
```

## Self-Check (MANDATORY)

Before completing any task, verify:

| Check | Question |
|-------|----------|
| Goal met? | Did I do exactly what was asked? |
| Names clear? | Would another developer understand? |
| Functions small? | All functions ≤20 lines? |
| No unnecessary comments? | If comment needed → refactor code first |
| Tests written? | New behavior has tests? |
| Tests pass? | All existing tests still pass? |
| No over-engineering? | Only changes that were requested? |
| DRY? | No duplicated logic? |

## Related Agents

| Agent | Purpose |
|-------|---------|
| [clean-code-reviewer](../../agents/clean-code-reviewer.md) | Read-only code review |
| [refactoring-assistant](../../agents/refactoring-assistant.md) | Guided refactoring |
