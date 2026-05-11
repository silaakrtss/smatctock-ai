# Code Review Checklist

Based on Robert C. Martin's "Clean Code" — Chapters 1-17.

## Before Starting Review

- [ ] Understand the purpose of the changes
- [ ] Run tests to confirm they pass

## Naming (Ch2, N1-N7)

- [ ] Names reveal intent (N1)
- [ ] No misleading names (Ch2)
- [ ] Meaningful distinctions — no `a1, a2` (Ch2)
- [ ] Pronounceable and searchable names (Ch2)
- [ ] Booleans read as questions: `isActive`, `hasPermission` (Ch2)
- [ ] Classes are nouns, methods are verbs (Ch2)
- [ ] Names at appropriate abstraction level (N2)
- [ ] Standard nomenclature used (Factory, Strategy, etc.) (N3)
- [ ] No encodings or type prefixes (N6)
- [ ] Side effects described in name (N7)

## Functions (Ch3, F1-F4)

- [ ] Functions ≤20 lines (Ch3)
- [ ] Functions do ONE thing (Ch3)
- [ ] ≤3 parameters (F1)
- [ ] No output arguments (F2)
- [ ] No flag (boolean) arguments (F3)
- [ ] No dead functions (F4)
- [ ] No side effects beyond what name says (Ch3)
- [ ] Command-Query Separation respected (Ch3)
- [ ] Newspaper metaphor: callers above, callees below (Ch5)

## Comments (Ch4, C1-C5)

- [ ] No redundant comments (C3)
- [ ] No obsolete comments (C2)
- [ ] No commented-out code (C5)
- [ ] Comments explain WHY, not WHAT (Ch4)
- [ ] TODOs have ticket numbers (Ch4)
- [ ] Could any comment be eliminated by better code? (Ch4)

## Formatting (Ch5)

- [ ] Vertical openness between concepts (Ch5)
- [ ] Related code is close together (Ch5)
- [ ] Consistent style throughout (G24)

## Objects & Data (Ch6)

- [ ] No train wrecks: `a.getB().getC()` (G36, Ch6)
- [ ] Law of Demeter respected (Ch6)
- [ ] Data structures vs objects distinction clear (Ch6)

## Error Handling (Ch7)

- [ ] No null returns — Optional/Result used (Ch7)
- [ ] Specific exceptions thrown (Ch7)
- [ ] No swallowed exceptions (Ch7)
- [ ] Special Case pattern where appropriate (Ch7)

## Boundaries (Ch8)

- [ ] 3rd party code wrapped/adapted (Ch8)
- [ ] Learning tests exist for external libraries (Ch8)

## Tests (Ch9, T1-T9)

- [ ] Tests exist for new behavior (T1)
- [ ] FIRST principles followed (Ch9)
- [ ] Given-When-Then structure (Ch9)
- [ ] One concept per test (Ch9)
- [ ] Boundary conditions tested (T5)
- [ ] Tests near recent bugs (T6)
- [ ] Tests are fast (T9)

## Classes (Ch10)

- [ ] Single Responsibility Principle (Ch10)
- [ ] Classes ≤200 lines (Ch10)
- [ ] High cohesion (Ch10)
- [ ] Open/Closed Principle (Ch10)

## General Smells (Ch17)

- [ ] No duplication (G5)
- [ ] No magic numbers (G25)
- [ ] No dead code (G9)
- [ ] No feature envy (G14)
- [ ] No artificial coupling (G13)
- [ ] Negative conditionals avoided (G29)
- [ ] Conditionals encapsulated (G28)
- [ ] Consistent conventions (G11)

## Final Check

- [ ] All tests pass
- [ ] No over-engineering (YAGNI)
- [ ] Code is simpler than before (Boy Scout Rule)
