# LLM Evals

Snippets for evaluating LLM and VLM output quality, prompt templates, and rubric compliance.

## Core ideas
- **Deterministic Assertions**: Fast, exact checks (`icontains`, `not-icontains`, regex, length/format validation).
- **LLM-as-a-Judge (`llm-rubric`)**: Grading whether open-ended model outputs satisfy a natural-language description or constraint rubric.
- **Ephemeral GPU Lifecycle**: Spinning up a serverless GPU container only for the duration of the eval suite, storing results locally, and immediately tearing down the GPU.

## Implementations
| Folder | Framework | Description | Status |
|---|---|---|---|
| [promptfoo](promptfoo/) | Promptfoo | Config-driven prompt matrix & LLM-as-a-Judge evaluation suites | Working |
