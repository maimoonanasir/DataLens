# Final Project Report — DataLens

**Course:** Generative AI for Business — Spring 2026
**Dataset:** Online Retail II (UK Gift Retailer 2009–2011), ~1M rows
**Submitted by:** Haider Ahmad

---

## 1. What the Agent Did Well

The agent's most impressive capability was generating correct, idiomatic FastAPI code with proper Pydantic models on the first attempt — without any back-and-forth corrections. When asked to "build the CSV upload endpoint with validation," the agent:

- Correctly structured the Pydantic response model with all required fields
- Added the `python-multipart` dependency unprompted (required for `UploadFile`)
- Applied a chunked `df.to_sql()` call with `chunksize=5000` without being asked — a performance detail most junior developers would miss
- Wrote defensive error handling that distinguished between encoding errors (UTF-8 vs Latin-1 fallback) and structural CSV errors

This was genuinely impressive. A developer writing this from scratch would typically write a basic version, run it, discover the encoding issue only when testing against real datasets, then fix it. The agent wrote the robust version first.

The second strong area was React component architecture. When asked to build the `FilterPanel`, the agent correctly chose to compose a `FilterControl` sub-component rather than writing a monolithic conditional render. The resulting code was clean and testable — the `FilterControl` component renders correctly in unit tests because it has no side effects and accepts only props.

The agent's SPEC.md output was also excellent. When directed to "write a spec covering the six core areas," it automatically added an "Assumptions" section (which the template asked for but didn't emphasise) and populated it with genuinely non-obvious assumptions, such as: "InvoiceDate in the Online Retail II dataset requires datetime parsing with mixed formats." This showed the agent had actually explored the dataset profile before speccing, not just followed the template mechanically.

---

## 2. Where We Had to Intervene

**Intervention 1: SQL injection in query_engine.py**

In the first version of `_query_grouped()`, the agent generated SQL with f-string column name interpolation for the WHERE clause values:

```python
# What the agent wrote first:
f'WHERE "{safe_x}" = "{filter_value}"'
```

This is a SQL injection vulnerability. We intervened and directed the agent to use parameterised queries with `:param` placeholders and a `params` dict, which is the correct SQLAlchemy pattern. The agent correctly refactored this in the next iteration. This was a clear case of the agent taking the "easy" path — it knew the right pattern but defaulted to the simpler interpolation because we hadn't explicitly required parameterised queries in the initial prompt.

**Lesson:** The spec's "Always Do" boundary must explicitly say "use parameterised SQL queries" — agents will default to string interpolation without this constraint.

**Intervention 2: Agent tried to skip Vitest setup**

When directed to "write frontend tests," the agent initially produced a `test_upload.test.tsx` that imported directly from the source file without mocking the `api` module:

```tsx
// Agent's first attempt:
import { api } from "../src/lib/api";
// ...then called api.uploadCsv() directly in tests
```

This would make every frontend test dependent on a running backend — defeating the purpose of unit tests. We pushed back: "These tests must mock the API layer. The component should be tested in isolation." The agent then correctly added `vi.mock("../src/lib/api", ...)` and rewrote the tests with proper mock implementations.

**Lesson:** The agent understands test isolation conceptually but defaults to integration-style tests when left unprompted. This is the "skip tests to ship faster" rationalisation flagged in the spec's Boundaries section.

**Intervention 3: Chart histogram binning produced unusable output**

The first histogram implementation used `pd.cut()` bin labels that Recharts could not render (they contained parentheses and brackets: `(-80.0, 10.0]`). The chart appeared blank in the browser. We traced the issue, diagnosed it, and directed the agent to: "Use simple string labels like '−80 to 10' without special characters." The agent correctly regenerated the histogram bucketing logic with human-readable labels.

**Lesson:** Agents cannot see their own browser output. Visual verification of chart rendering requires manual testing — this cannot be fully delegated.

---

## 3. What We Would Do Differently

If we had another week, three changes would have the highest impact:

**Add proper database indexes.** The current SQLite tables have no indexes. For the 1M-row Online Retail II dataset, a `WHERE Country = 'United Kingdom'` query takes ~1.5 seconds. Adding `CREATE INDEX idx_country ON data_<id> ("Country")` would drop this to under 100ms. We'd add this as part of the upload flow, creating indexes on all categorical and datetime columns automatically.

**Add streaming to the LLM chat.** Currently, the chat UI waits for the full response before displaying anything. For queries that require 3–4 tool-call rounds, this can take 8–10 seconds with a blank loading state. Server-Sent Events (SSE) streaming would show partial text as it streams from the Anthropic API, dramatically improving perceived responsiveness.

**Make chart selection user-editable.** The auto-selection algorithm produces good defaults, but users sometimes want a different chart. A "swap chart type" control on each ChartCard would let users change from a bar to a line without reloading, using the already-fetched data.

---

## 4. Which Skills Activated When

**spec-driven-development:** Activated in the first interaction — "let's write the spec for DataLens." The agent immediately began populating SPEC.md's six core areas in order, surfaced assumptions explicitly ("I'm assuming the Online Retail II CSV has these specific column names..."), and wrote testable success criteria (e.g., "dashboard renders within 3 seconds" rather than "dashboard renders quickly"). Without this skill, the agent would have started writing FastAPI code on Day 1.

**planning-and-task-breakdown:** Activated when asked to "break the spec into an implementation plan." The agent produced `plan.md` with eight phases ordered by dependency (upload before profiling, profiling before charts, charts before filters). It correctly identified that "LLM tool definitions depend on query_engine.py being in place" — a non-obvious dependency. The task list in `todo.md` had every task bounded to ≤5 files, which proved accurate during implementation.

**incremental-implementation:** Visible in how the agent structured its work when coding began. It consistently built the backend endpoint before the frontend component that calls it, and tested each piece before moving on. When the chart endpoint was complete, it ran `curl` to verify the JSON shape before writing the React component that consumed it. This thin-slice discipline prevented integration surprises at Week 2's end.

**test-driven-development:** Most visible at the moments of intervention described above. When we pushed back on the integration-style frontend tests, the agent knew exactly what we meant by "mock the API layer" and did it correctly. The skill was also evident in the conftest.py fixture design — the agent used an in-memory SQLite database for all tests, which prevented test contamination of the production database without being asked.

**documentation-and-adrs:** Activated when decisions were made. When we decided to use Anthropic over OpenAI, the agent immediately asked: "Should I record this in an ADR?" This was the skill working as intended — it primed the agent to recognise decision moments and capture them before they were forgotten. The three ADRs in `docs/adrs/` each include concrete trade-offs, not generic justifications.

**git-workflow-and-versioning:** The most subtle skill — it changed the agent's commit behavior from big-bang dumps to atomic commits. Each feature received its own commit with a descriptive message ("feat(upload): add CSV validation and Pandas ingestion with Latin-1 fallback"). By Week 3, the git log told the story of the project's development in chronological order, which the spec required.
