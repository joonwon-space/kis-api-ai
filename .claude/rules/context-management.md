# Context Management

## The Core Constraint

Context window is your fundamental constraint. As context fills:
- Claude may "forget" earlier instructions
- Response quality degrades
- Performance decreases
- More mistakes occur

**Strategy**: Actively manage context to maintain peak performance.

## When to Use /compact

Use `/compact` command to compress conversation history:

- **Context usage >50%**: Before it becomes a problem
- **Before starting new feature**: Clean slate for complex work
- **After completing milestone**: Compress completed work
- **When switching contexts**: Moving between different parts of codebase
- **After 15+ exchanges**: Long conversations accumulate cruft

### How to Check Context

Watch for these signs:
- Responses becoming less precise
- Claude forgetting earlier decisions
- Repeated questions about same topics
- Performance slowdown

## When to Use /clear

Use `/clear` command to start fresh conversation:

- **Starting new issue**: Each GitHub issue = new conversation
- **Switching to different area**: Moving from backend to frontend
- **After major completion**: Feature shipped and merged
- **Context >75%**: When /compact isn't enough
- **After 20+ exchanges**: Very long sessions

**Rule of thumb**: Issues that are unrelated = separate conversations

## Subagent Strategy

Delegate to subagents instead of doing research directly:

### Explore Agent
- **When**: Open-ended codebase exploration
- **Example**: "Where are errors handled?" "What's the architecture?"
- Use `subagent_type=Explore` with Task tool

### Planner Agent
- **When**: Complex features requiring design decisions
- **Example**: "Plan implementation of X feature"
- Use `subagent_type=Plan` or `/plan` skill

### Code Reviewer Agent
- **When**: After writing/modifying code
- **Example**: Automatic after significant changes
- Use `subagent_type=code-reviewer`

### TDD Guide Agent
- **When**: Writing new features with tests first
- **Example**: "Implement feature X with TDD approach"
- Use `/tdd` skill or `subagent_type=tdd-guide`

### Benefits of Subagents
- Work in isolated context (don't pollute main conversation)
- Can be run in parallel
- Return only relevant results
- Specialized for specific tasks

## Parallel Task Execution

When tasks are independent, use parallel execution:

```python
# GOOD: Parallel agents
Task 1: Security review of auth.py
Task 2: Performance review of cache.py
Task 3: Type check of utils.py

# BAD: Sequential when not needed
First Task 1, then Task 2, then Task 3
```

## Context Optimization Tips

### DO:
- Use subagents for research and exploration
- Keep main conversation focused on implementation
- Use /compact regularly
- Start new conversations for new issues
- Run parallel agents for independent tasks

### DON'T:
- Let context grow to >75% without action
- Mix unrelated features in one conversation
- Do extensive codebase searches in main thread
- Keep old completed work in active context

## Workflow Example

```bash
# Starting new issue
/clear
gh issue view 14

# Exploring codebase (use subagent, not direct grep)
[Use Task tool with Explore agent]

# Planning (use subagent)
/plan

# Implementing (main thread)
[Write code]

# Review (use subagent)
/code-review

# After 10-15 exchanges
/compact

# After completing and merging
/clear
```

## Session Hygiene

Good session hygiene = better results:
- One issue = one conversation
- Clean up with /compact every ~10 exchanges
- Start fresh with /clear for new issues
- Delegate research to subagents
- Keep main thread focused on implementation

Remember: Context is your most valuable resource. Manage it actively.
