---
name: brainstorm
description: "This skill should be used when the user asks to 'brainstorm', 'design this', 'think through', 'plan this out', 'what should we build', 'how should this work', 'let's think about', 'explore approaches', or 'before we start'. Also appropriate when beginning tasks with genuine ambiguity: multiple reasonable approaches, unclear requirements, or cross-cutting changes spanning multiple subsystems."
---

# Brainstorm

Understand what to build before building it. Scale the process to match the problem.

## Core Principle

Implementation without understanding is the most common source of wasted work. But process without proportion is the second most common. Match the depth of exploration to the complexity of the task.

## Sizing the Conversation

Before anything else, assess scope. Not every task needs the same treatment.

**Quick (1-2 exchanges):** The task is clear and constrained. A config change, a single function, a well-specified bug fix. Ask one clarifying question if needed, confirm approach, move on.

**Medium (3-6 exchanges):** Genuine ambiguity exists. Multiple reasonable approaches, unclear requirements, or unfamiliar domain. Explore approaches, propose a recommendation, get alignment.

**Deep (7+ exchanges):** Large scope, multiple subsystems, or novel territory. Full collaborative design: explore context, ask questions one at a time, propose approaches with trade-offs, present design in sections, get approval before proceeding.

The sizing decision is a judgment call, not a checklist. Err toward doing less process, not more. A 30-second clarification that prevents a wrong turn is valuable. A 10-minute design review for a one-line change is not.

## The Process

### 1. Check Context

Read relevant files, docs, recent commits. Understand the current state before asking questions. Asking "what framework are you using?" when package.json is right there wastes everyone's time.

### 2. Clarify Intent

Ask questions to understand what the user actually wants — not just what they said. Focus on:

- **Purpose**: What problem does this solve? Who is it for?
- **Constraints**: What must it work with? What can't change?
- **Success**: How will we know it's right?

One question per message. Prefer multiple choice when the option space is known. Open-ended when it isn't.

Stop asking when the path forward is clear. Not every dimension needs to be explored — only the ones where a wrong assumption would waste significant work.

### 3. Explore Approaches (When Warranted)

When there are genuinely different ways to solve the problem, present 2-3 approaches with trade-offs. Lead with the recommended approach and explain why.

Skip this step when:
- There's an obvious right answer given the codebase and constraints
- The user has already specified their preferred approach
- The task is small enough that exploring alternatives costs more than just doing it

### 4. Present Design (For Deep Tasks Only)

For larger tasks, present the design in sections scaled to their complexity. A few sentences for straightforward parts, more detail for nuanced parts. Check alignment after each section.

Cover what matters: architecture, data flow, error handling, testing approach. Skip sections that are obvious from context.

### 5. Transition to Implementation

When alignment is reached, move to implementation. For deep tasks, consider writing the design to a file if it would help the implementation phase (especially across context windows). For quick and medium tasks, just start building.

Do not force a specific file path, spec format, or downstream skill invocation. The transition to implementation is a natural continuation, not a handoff to another process.

## Anti-Patterns to Avoid

- **Ceremony for its own sake.** A todo list doesn't need 2-3 approaches and a design doc.
- **Asking questions with knowable answers.** Read the codebase first.
- **Restating what the user said.** "So you want me to..." — just do it, or ask the real question.
- **Blocking on approval for obvious next steps.** If the user said "add a dark mode toggle" and there's one reasonable place to put it, don't present three options.
- **Over-decomposition.** Not every feature needs to be broken into sub-projects with their own spec cycles.

## When Implementation Is Already Clear

Sometimes the user's request is specific enough that no brainstorming is needed. "Rename `foo` to `bar` in utils.py" doesn't need a design phase. Recognize when the task is already well-specified and skip straight to doing it. The goal is understanding before implementation — if understanding is already there, proceed.
