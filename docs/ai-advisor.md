# SHREA AI Advisor (Phase 8)

> SHREA AI explains application results. It does not replace the deterministic
> renewable-energy calculation engines and is never the source of a number.

## Architecture

```
Browser (GitHub Pages)                      no AI key, no provider URL
   |  POST /api/v1/advisor/chat {assessment_id, message, history}
   v
SHREA API (FastAPI, Render)
   AdvisorService  -> checks the assessment exists and belongs to the caller
                   -> builds context through the EXISTING services:
                        Solar (Phase 4) | Wind (Phase 7) | Tariff (Phase 5) | Incentives (Phase 6)
                   -> system prompt + compact JSON context + last N turns + the new message
   |  one request per user message
   v
ChatProvider (interface)  ->  NvidiaNimProvider  ->  NVIDIA NIM (OpenAI-compatible /chat/completions)
```

| Piece | File |
| --- | --- |
| Provider interface + NVIDIA NIM adapter | `backend/app/services/ai/provider.py` |
| System instructions | `backend/app/services/ai/prompt.py` |
| Context builder (pure) | `backend/app/services/ai/context.py` |
| Rate limiter | `backend/app/services/ai/rate_limit.py` |
| Orchestration | `backend/app/services/advisor_service.py` |
| Routes | `backend/app/api/v1/routes/advisor.py` |
| Chat UI | `frontend/src/components/advisor/AdvisorChat.tsx`, `hooks/useAdvisorChat.ts` |

The older `AIAdvisorService` abstract class (`ai_advisor_service.py`, tool-execution
oriented) was an unused placeholder and is left untouched; a plain chat adapter was
the smallest thing that works. Swapping providers means one new `ChatProvider`
subclass and one branch in `build_provider()`.

## Configuration (backend only)

| Variable | Default | Purpose |
| --- | --- | --- |
| `NVIDIA_API_KEY` | unset | API key. **Backend/Render only.** Never in the frontend, GitHub Pages variables or Git |
| `AI_PROVIDER` | `nvidia_nim` | Only adapter available |
| `AI_MODEL` | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | A small (30B total, ~3B active) Nemotron that answered on the hosted API with the key used for verification. `nvidia/nemotron-nano-3-30b-a3b` appears in the public model list but returned 404 "Not found for account", so a model being listed does not mean it is invocable; the reasoning text it returns separately is ignored |
| `AI_BASE_URL` | `https://integrate.api.nvidia.com/v1` | NIM endpoint |
| `AI_TIMEOUT_SECONDS` | 30 | Provider timeout |
| `AI_MAX_OUTPUT_TOKENS` | 800 | Output bound |
| `AI_HISTORY_LIMIT` | 6 | Prior turns sent |
| `AI_RATE_LIMIT_PER_MINUTE` | 10 | Per assessment |
| `AI_GLOBAL_RATE_LIMIT_PER_MINUTE` | 30 | All callers |

`render.yaml` declares `NVIDIA_API_KEY` with `sync: false`, so the value is entered in
the Render dashboard and never stored in the repository. Without it the advisor
returns `ai_not_configured` and the UI says "SHREA AI isn't connected yet."

## API

- `POST /api/v1/advisor/chat` -> `{status: ok | ai_not_configured | ai_error, message, error_code, assessment_id, provider, model}`.
  Provider failures are HTTP 200 with `ai_error` and a safe `error_code`
  (`timeout`, `rate_limited`, `auth_failed`, `provider_error`, `network_error`, `invalid_response`).
  404 = unknown (or not the caller's) assessment; 422 = invalid message; 429 = our own rate limit.
- `GET /api/v1/advisor/overview/{assessment_id}` -> location label, building, consumption,
  which result sections have verified data, suggested questions, whether AI is configured.
  **Makes no AI call**, so opening the chat costs nothing.

## Verified-data authority

The context contains only assessment fields and the existing engines' outputs. The system prompt
tells the model those numbers are authoritative, that it must not recalculate them, and that a
section with `status` other than `ok` means "the application has no verified data" - never an
estimate. Sections that fail are marked `unavailable` instead of being dropped or defaulted.
The model is told the application has no recommendation, cost/savings/payback/ROI, or live
monitoring, so "which should I install?", "what is my payback?" and "what is my turbine
producing?" are answered honestly rather than invented.

The incentive section is evaluated for a 3 kW solar system, the same default the dashboard uses.
That is not a recommendation and the context says so.

## Security

- **Key**: backend environment only; never in a prompt, response or log. A provider reply that
  contains the key is rejected.
- **Assessment access**: the backend loads the assessment itself (the frontend supplies only the
  id) and checks `assessment.building.user_id`. There is no authentication yet, so the current user
  is the prototype user (`get_current_user_id`) and an assessment is reachable only by its
  unguessable id, exactly like `GET /assessments/{id}`. Real auth replaces that one function.
  Foreign or missing assessments both return 404.
- **Not sent to the model**: credentials, database URL, street address, coordinates, or any
  unrelated assessment.
- **Prompt injection**: user text and prior turns are untrusted. They are only ever `user` /
  `assistant` messages after the system prompt; a `system` role in history is rejected (422); the
  prompt states that user text cannot change the rules or the data. Forged assistant turns can
  still appear in history, which is why the prompt tells the model only the application data
  block is authoritative. The model has no tools, no internet, no code execution.
- **Response validation**: text only, non-empty, at most 4,000 characters, reasoning blocks
  stripped, rendered by React as escaped text (no HTML, no Markdown).
- **Errors**: only a code is returned; provider bodies, headers and stack traces are never exposed.
- **Logging**: `provider, model, assessment id, outcome, latency`. No message text, context or key.

## Cost control

One provider request per submitted message; no call on page load, while typing or on retry;
compact context (~1-2k tokens); last 6 turns; 800-token output cap; 30-second timeout; in-memory
rate limits (10/min per assessment, 30/min overall - per process, assumes one API instance);
mocked tests; only a handful of real verification requests.

## Limitations

- The chat history lives in the browser only and is lost when the panel closes.
- Each chat or overview request re-runs the four engines through their normal services (the
  location profile is cached for 24 h, but each engine also writes its usual best-effort snapshot).
- Rate limiting is per process and not per user, because there are no users yet.
- Quality depends on the configured model; the prompt reduces but cannot eliminate mistakes, and
  the chat is not a recommendation, financial advice or engineering approval.
