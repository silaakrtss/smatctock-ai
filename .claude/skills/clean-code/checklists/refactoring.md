# Refactoring Checklist

Based on Robert C. Martin's "Clean Code" — Chapter 14 (Successive Refinement) and Chapter 17 (Smells).

## Before Refactoring

- [ ] Tests exist and pass (Ch14 Golden Rule: NO refactoring without tests)
- [ ] I understand what the code does
- [ ] I've identified the specific smell (Ch17 reference code)
- [ ] I have a clear goal for this refactoring

## Identifying Smells

### Quick Smell Scan

| Smell | Check | Ch17 Code |
|-------|-------|-----------|
| Long function | >20 lines? | Ch3, G30 |
| Too many params | >3 parameters? | F1 |
| Duplication | Same logic in multiple places? | G5 |
| Magic numbers | Literal values in logic? | G25 |
| God class | >200 lines? Multiple responsibilities? | Ch10 |
| Train wreck | `a.b().c().d()`? | G36 |
| Feature envy | Using others' data more than own? | G14 |
| Flag argument | Boolean parameter? | F3 |
| Dead code | Never called? | G9, F4 |
| Negative condition | `if (!notFound)`? | G29 |

## Refactoring Techniques

### Extract Method (for G30, long functions)
1. Identify a coherent block of code
2. Extract into a new method with descriptive name
3. Run tests

### Introduce Parameter Object (for F1)
1. Group related parameters into an object/record
2. Replace parameter list with object
3. Run tests

### Replace Conditional with Polymorphism (for G23)
1. Identify if/else or switch on type
2. Create interface/abstract class
3. Create implementations for each case
4. Replace conditional with polymorphic call
5. Run tests

### Extract Class (for God Class)
1. Identify groups of fields used by different methods
2. Move related fields and methods to new class
3. Inject new class where needed
4. Run tests

### Replace Magic Number (for G25)
1. Identify literal values
2. Create named constants
3. Replace literals with constants
4. Run tests

### Encapsulate Conditional (for G28)
1. Identify complex boolean expression
2. Extract into descriptively named method
3. Run tests

## During Refactoring (Ch14 Process)

- [ ] Making ONE change at a time
- [ ] Running tests after EACH change
- [ ] Not adding new features while refactoring
- [ ] Keeping changes small and reversible
- [ ] Committing after each successful step

## After Refactoring

- [ ] All tests still pass
- [ ] No new tests needed? (add if behavior changed)
- [ ] Code is more readable
- [ ] Specific smell is eliminated
- [ ] No new smells introduced
- [ ] Changes are committed

## Emergency Rollback

If tests fail after a refactoring step:
1. Undo the last change
2. Re-run tests to confirm they pass
3. Try a smaller step
4. If still stuck, reconsider the approach

## Common Refactoring Sequences

### Long Method → Clean Methods
```
1. Extract validation → test
2. Extract core logic → test
3. Extract side effects → test
4. Rename for clarity → test
```

### God Class → Focused Classes
```
1. Identify responsibility groups
2. Extract first group to new class → test
3. Extract second group → test
4. Repeat until original class has single responsibility
```

### if/else Chain → Polymorphism
```
1. Create interface → test
2. Extract first case to implementation → test
3. Extract second case → test
4. Remove original if/else → test
5. Use DI to wire implementations → test
```
