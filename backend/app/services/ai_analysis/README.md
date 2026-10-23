# AI analysis module

This package owns scam and suspicious-investment text analysis. It is designed
to plug into the shared FastAPI backend without owning application routes,
authentication, database persistence, or FSCA verification.

## Module responsibilities

- `schemas.py`: validated inputs and the assessment response contract.
- `baseline.py`: simple phrase checks and baseline risk categorisation. These
  checks are clues for further review, not a final decision about fraud.
- `prompts.py`: instructions that treat submitted content as untrusted evidence.
- `nvidia_client.py`: backend-only NVIDIA API integration and configuration.
- `service.py`: combines the baseline with optional AI explanations.
- `backend/tests/services/ai_analysis/`: tests for the baseline, validation,
  prompt-injection resistance, and AI service failure behavior.

The baseline must remain usable when the NVIDIA service is unavailable. AI
output is explanatory evidence, not proof of fraud or a legal finding. API
credentials belong in an untracked local `.env` file, never in frontend code
or source control.
