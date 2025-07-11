## Coding Guidelines

- Do not send mock data on error. Only send mock data when the mock flag is true
- do not return mock data on errors
- use python3 all the time, do not run commands with python
- make sure we do dev on branches, never master

## Testing Strategy

- Unit tests for each integration module
- Integration tests with mocked external APIs
- End-to-end tests for complete workflows
- Use pytest fixtures for test data
- Mock external API calls using `responses` or `unittest.mock`
- All new features should have 80% test coverage

## Error Handling

- All external API calls wrapped in try/except blocks
- Retry logic for transient failures
- Dead letter queue for failed processing
- Comprehensive logging with structured logs
- Alert on critical failures

## Security Considerations

- Store API credentials in environment variables
- Validate all incoming data
- Sanitize PDF content before processing
- Use HTTPS for all external communications
- Implement rate limiting on API endpoints

## Development Guidance

- Use python3 not python

## Your Role
Don't be shy to ask questions -- I'm here to help you!

If I send you a URL, you MUST immediately fetch its contents and read it carefully, before you do anything else.

# Git Commit and Pull Request Guidelines

## Conventional Commits Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types
- `feat`: New features (correlates with MINOR in semantic versioning)
- `fix`: Bug fixes (correlates with PATCH in semantic versioning)
- `docs`: Documentation only changes
- `refactor`: Code changes that neither fix bugs nor add features
- `perf`: Performance improvements
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks, dependency updates, etc.
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `build`: Changes to build system or dependencies
- `ci`: Changes to CI configuration files and scripts

### Scope Guidelines
- **Scope is OPTIONAL**: only add when it provides clarity
- Use lowercase, placed in parentheses after type: `feat(transcription):`
- Prefer specific component/module names over generic terms
- Your current practice is good: component names (`EditRecordingDialog`), feature areas (`transcription`, `sound`)
- Avoid overly generic scopes like `ui` or `backend` unless truly appropriate

### When to Use Scope
- When the change is localized to a specific component/module
- When it helps distinguish between similar changes
- When working in a large codebase with distinct areas

### When NOT to Use Scope
- When the change affects multiple areas equally
- When the type alone is sufficiently descriptive
- For small, obvious changes

### Description Rules
- Start with lowercase immediately after the colon and space
- Use imperative mood ("add" not "added" or "adds")
- No period at the end
- Keep under 50-72 characters on first line

### Breaking Changes
- Add `!` after type/scope, before colon: `feat(api)!: change endpoint structure`
- Include `BREAKING CHANGE:` in the footer with details
- These trigger MAJOR version bumps in semantic versioning

### Examples Following Your Style:
- `feat(transcription): add model selection for OpenAI providers`
- `fix(sound): resolve audio import paths in assets module`
- `refactor(EditRecordingDialog): implement working copy pattern`
- `docs(README): clarify cost comparison section`
- `chore: update dependencies to latest versions`
- `fix!: change default transcription API endpoint`

## Commit Messages Best Practices
- NEVER include Claude Code watermarks or attribution
- Each commit should represent a single, atomic change
- Write commits for future developers (including yourself)
- If you need more than one line to describe what you did, consider splitting the commit

## Pull Request Guidelines
- NEVER include Claude Code watermarks or attribution in PR titles/descriptions
- PR title should follow same conventional commit format as commits
- Focus on the "why" and "what" of changes, not the "how it was created"
- Include any breaking changes prominently
- Link to relevant issues

## What NOT to Include:
- `🤖 Generated with [Claude Code](https://claude.ai/code)`
- `Co-Authored-By: Claude <noreply@anthropic.com>`
- Any references to AI assistance
- Tool attribution or watermarks

# Punctuation Guidelines

## Avoiding AI Artifacts
The pattern " - " (space-hyphen-space) is a common AI writing artifact that should be replaced with proper punctuation.

### Replacement Priority
1. **Semicolon (;)** - Use to connect closely related independent clauses
   - Before: `The code works - the tests pass`
   - After: `The code works; the tests pass`

2. **Colon (:)** - Use when introducing an explanation, list, or example
   - Before: `**Bold text** - This explains what it means`
   - After: `**Bold text**: This explains what it means`

3. **Em dash (—)** - Use for dramatic pauses or parenthetical statements where semicolon and colon don't work
   - Before: `The app is fast - really fast`
   - After: `The app is fast—really fast`

### Common Patterns
- **Definitions/Explanations**: Use colon
  - `**Feature name**: Description of the feature`
- **Examples/Lists**: Use colon
  - `**Examples**: item1, item2, item3`
- **Dramatic emphasis**: Use em dash
  - `It's more than fast—it's instant`
- **Related statements**: Use semicolon
  - `The API is simple; the documentation is clear`

# Writing Style Examples

## Good Example (Natural, Human)
"I was paying $30/month for a transcription app. Then I did the math: the actual API calls cost about $0.36/hour. At my usage (3-4 hours/day), I was paying $30 for what should cost $3.

So I built Whispering to cut out the middleman. You bring your own API key, your audio goes directly to the provider, and you pay actual costs. No subscription, no data collection, no lock-in."

## Bad Example (AI-Generated Feel)
"**Introducing Whispering** - A revolutionary transcription solution that empowers users with unprecedented control.

**Key Benefits:**
- **Cost-Effective**: Save up to 90% on transcription costs
- **Privacy-First**: Your data never leaves your control
- **Flexible**: Multiple provider options available

**Why Whispering?** We believe transcription should be accessible to everyone..."

## The Difference
- Good: Tells a story, uses specific numbers, flows naturally
- Bad: Structured sections, bold headers, marketing language
- Good: "I built this because..." (personal)
- Bad: "This was built to..." (corporate)
- Good: "$0.02/hour" (specific)
- Bad: "affordable pricing" (vague)

# Documentation & README Writing Guidelines

## Authentic Communication Style
- Avoid emojis in headings and formal content unless explicitly requested
- Use direct, factual language over marketing speak or hyperbole
- Lead with genuine value propositions, not sales tactics
- Mirror the straightforward tone of established sections when editing
- Prefer "We built this because..." over "Revolutionary new..."

## Avoiding AI-Generated Feel

### The Dead Giveaways
- **Bold formatting everywhere**: Biggest red flag. Never bold section headers in post content
- **Excessive bullet lists**: Convert to flowing paragraphs
- **Marketing language**: "game-changing", "revolutionary", "unleash", "empower"
- **Structured sections**: "Key Features:", "Benefits:", "Why This Matters:"
- **Vague superlatives**: "incredibly powerful", "seamlessly integrates", "robust solution"

### Writing Natural Prose
- **Start with a story or problem**: "I was paying $30/month..." not "Introducing..."
- **Use specific numbers**: "$0.02/hour" not "affordable pricing"
- **Personal voice**: "I built this because..." not "This was built to..."
- **Conversational flow**: Ideas connect naturally, not in rigid sections
- **Concrete examples**: "I use it 3-4 hours daily" not "heavy usage"