# Legacy API Builder Lab

The original provider lab remains available at the repository root:

- `run_lab.py`
- `labs/`
- `providers.md`
- `workflow.md`
- `SKILL.md`

APIForgeKit Studio V1 does not use LLMs, provider SDKs, agents, voice, or vision. The legacy lab can still be used separately when validating OpenAI, Gemini, Anthropic, or xAI provider behavior.

Install legacy provider dependencies only when needed:

```bash
python -m pip install -r requirements-legacy.txt
python run_lab.py --status
```
