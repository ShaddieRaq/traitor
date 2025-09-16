# User Working Style Guide

## Core Philosophy
- **Fix root causes, never mask symptoms**
- **Challenge quick fixes that reduce capability**
- **Question solutions that disable rather than improve**

## Problem-Solving Approach
- Always investigate underlying causes, not just surface issues
- Scaling back functionality is avoidance, not problem-solving
- If a system can't handle its intended load, fix the system

## Anti-Patterns to Avoid
### ❌ **Symptom Masking**
- Turning off features to "fix" problems
- Reducing concurrent operations instead of optimizing them
- Accepting artificial limitations as solutions
- Working around issues instead of through them

### ✅ **Root Cause Solutions**
- Engineer proper technical solutions
- Implement correct architectural patterns
- Fix performance through optimization, not reduction
- Address concurrency with proper design

## Communication Style
- Always explain the technical reasoning behind approaches
- If suggesting a temporary fix, explicitly label it as such with a proper solution plan
- Challenge me if I seem to accept suboptimal solutions
- Don't assume "working around" problems is acceptable

## Technical Standards
- Systems should handle their designed capacity
- Performance issues require engineering solutions
- Concurrent operations are features, not problems to eliminate
- Technical debt should be temporary with clear resolution paths

## Red Flags for Solutions
- "Just turn off X" approaches
- Reducing system capability instead of improving it
- Quick fixes without addressing root causes
- Permanent workarounds instead of proper fixes

## Preferred Response Pattern
1. **Acknowledge the immediate problem**
2. **Identify the actual root cause**
3. **Propose proper engineering solution**
4. **Provide temporary workaround only if needed** (clearly labeled)
5. **Create implementation plan for real fix**
