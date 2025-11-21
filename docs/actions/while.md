# while - While Loops

Execute a block of steps repeatedly while a condition remains true.

## Syntax

```yaml
- while: condition_expression
  loop:
    - step1
    - step2
    # ... more steps
```

## Parameters

- `condition_expression`: A boolean expression evaluated before each iteration
- `loop`: Array of steps to execute in each iteration

## Examples

### Basic Counter Loop

```yaml
entity: Counter
actions:
  - name: countdown
    steps:
      - declare:
          name: counter
          type: integer
          default: 10
      - while: counter > 0
        loop:
          - query: counter = counter - 1
          - if: counter = 5
            then:
              - return_early: "Halfway done"
      - return: "Done"
```

### Processing with Complex Condition

```yaml
entity: Processor
actions:
  - name: process_until_complete
    steps:
      - declare:
          name: status
          type: text
          default: 'pending'
      - declare:
          name: attempts
          type: integer
          default: 0
      - while: status != 'complete' AND attempts < 5
        loop:
          - call_function:
              function: process_batch
              returns: batch_result
          - query: status = batch_result.status
          - query: attempts = attempts + 1
```

## Notes

- The condition is evaluated before each iteration
- If the condition is false initially, the loop body never executes
- Use `return_early` to exit the loop prematurely
- Variables declared outside the loop are accessible inside
- Be careful to avoid infinite loops
