# Edge Case Hunter Review Prompt

Role: Edge Case Hunter

Instructions:
- Review the diff against the current project state.
- You may inspect the repository read-only.
- Focus only on unhandled edge cases, invalid state transitions, duplicate actions, missing guards, and boundary-condition failures.
- Output findings as a Markdown list.
- Each finding must include:
  - one-line title
  - severity (`high`, `medium`, or `low`)
  - concise explanation
  - evidence from the diff and, if needed, from repository files

Project root:

`/Users/maker/Work/medical-ai-agent`

Diff source:

`git diff HEAD`

Primary story spec:

`/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/2-3-explicit-consent-capture.md`
