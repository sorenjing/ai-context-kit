# Agent Skills integration

AI coding environments often combine three complementary inputs:

| Layer | Responsibility |
|---|---|
| Project rules | Repository-specific constraints, contribution guidance, commands, architecture, and ownership. These commonly live in `AGENTS.md`, `CONTRIBUTING.md`, or equivalent files. |
| AI Context Kit | Shared workspace context: project discovery, deterministic facts, freshness checks, and thin adapters for coding tools. |
| Agent Skills | Reusable behaviors and workflows that apply across projects, such as review procedures, release checks, or safety practices. |

At runtime, the coding agent combines these layers with the task prompt:

```text
task prompt + project rules + shared context + reusable skills
  -> coding agent
```

AI Context Kit owns neither repository policy nor reusable behavior. It provides the context that lets those layers operate with current workspace facts.

## Composition, not a dependency

Agent Skills are optional. AI Context Kit has no dependency on a particular Skill repository, Skill manager, remote service, or personal configuration. It remains useful with project rules alone, and it can coexist with any compatible skill-discovery mechanism.

Likewise, Agent Skills should not duplicate the context store. A skill can instruct an agent to read the workspace context and run `aictx` when relevant, while AI Context Kit continues to own discovery, freshness, and managed context files.

## Recommended workflow

1. Start from the repository's own instructions and the current task.
2. Read the shared workspace context; run `aictx status` when the workspace may have changed.
3. Apply any relevant reusable skill for the task's workflow or risk profile.
4. Make and verify the project change according to repository rules.
5. Refresh shared context only when project facts became stale, and record concise semantic decisions in the managed manual block when needed.

This keeps project constraints close to the code, shared facts in one workspace-level context store, and reusable behavior portable across repositories and agents.
