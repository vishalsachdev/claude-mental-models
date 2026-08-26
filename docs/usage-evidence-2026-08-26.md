# Which Claude Code mental models show up in Vishal's own usage?

**Evidence snapshot: 2026-08-26**

## Headline summary

Vishal shows direct evidence of **11 of the project's 13 mental models** in his
own Claude Code prompts. Four are embedded habits, five are recurring practices,
two appear only as traces, and two have no direct evidence.

- **Embedded (score 3):** external connectivity, extensibility, permission and
  security boundaries, and session identity/persistence.
- **Recurring (score 2):** multi-agent orchestration, resource monitoring,
  layered configuration, workspace isolation, and context management.
- **Trace (score 1):** UI/command navigation and model/inference controls.
- **Absent (score 0):** terminal rendering/display and terminal input/interaction.

Every observed first-use date is later than the model's changelog emergence
date, by 283–357 days. That is an **observed lag, not a measured adoption delay**:
the usage database begins on 2026-03-01, after all 13 models had already emerged.
There is therefore no period in this corpus in which Vishal could be observed
leading the changelog.

## What was counted

The live database was opened with `sqlite3 -readonly`; it was never modified.
The pinned snapshot's `user_prompts` table contains 19,070 rows across 7,456 content-session
identifiers from 2026-03-01 through 2026-08-26. A May 21 spike includes 5,985
imported changelog prompts and other headless analysis traffic. Counting those
would falsely make product-release text look like Vishal's behavior.

The adoption analysis therefore uses a conservative **direct-prompt set**:

- the prompt belongs to an interactive session with a non-null
  `memory_session_id`;
- it is at most 2,000 characters, reducing matches inside pasted reports and
  large generated payloads; and
- it does not begin with a known source/template prefix (`Source:`, `You are`,
  `<task-notification>`, `Themes:`, or `Open codes:`).

This leaves **8,106 prompts in 680 recorded sessions**. Counts below are distinct
matching prompts. Session share is the number of the 680 sessions containing at
least one match. FTS5 was used for all signature searches. `observations` and
`session_summaries` were used as corroborating spot checks, not as Vishal's own
words. One surviving raw transcript was sampled rather than bulk-loaded; it
contained the exact context-limit prompt at line 4000.

Examples are verbatim, at most 200 characters, and omit student names and email
addresses. Spelling and punctuation are preserved.

## Adoption score

The score is rule-based and deliberately conservative:

| Score | Rule |
|---:|---|
| **0 — absent** | No direct-prompt match. |
| **1 — trace** | Some evidence, but it does not meet the recurring threshold. |
| **2 — recurring** | At least 3 active months, at least 2% of sessions, and at least 2 signature families. |
| **3 — embedded** | At least 5 active months, at least 10% of sessions, and at least 3 signature families. |

An active month has at least one matching prompt. A model must satisfy every
condition at its score; high volume alone cannot make a narrow signature look
embedded.

## Results at a glance

Monthly columns are March through August 2026.

| Mental model | Emerged | First seen | Comparison | Mar | Apr | May | Jun | Jul | Aug | Sessions | Score |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| External Connectivity | 2025-04-02† | 2026-03-01 | lagging 333d | 60 | 20 | 1 | 33 | 62 | 68 | 23.24% | **3** |
| Extensibility Ecosystem | 2025-04-02† | 2026-03-01 | lagging 333d | 96 | 31 | 0 | 26 | 18 | 70 | 20.59% | **3** |
| UI Navigation & Command Surfaces | 2025-04-02† | 2026-03-05 | lagging 337d | 4 | 0 | 0 | 0 | 4 | 5 | 1.91% | **1** |
| Terminal Rendering & Display | 2025-04-02† | — | absent | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% | **0** |
| Terminal Input & Interaction | 2025-04-02† | — | absent | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% | **0** |
| Multi-Agent Orchestration | 2025-04-18 | 2026-03-01 | lagging 317d | 20 | 2 | 1 | 4 | 10 | 75 | 9.41% | **2** |
| Permission & Security Boundaries | 2025-04-02† | 2026-03-04 | lagging 336d | 22 | 10 | 4 | 15 | 22 | 76 | 13.38% | **3** |
| Resource Monitoring & Performance | 2025-04-02† | 2026-03-05 | lagging 337d | 8 | 3 | 0 | 3 | 0 | 23 | 3.38% | **2** |
| Session Identity & Persistence | 2025-04-02† | 2026-03-02 | lagging 334d | 152 | 72 | 4 | 74 | 155 | 175 | 69.85% | **3** |
| Layered Configuration Policy | 2025-04-02† | 2026-03-04 | lagging 336d | 19 | 5 | 1 | 10 | 18 | 20 | 8.38% | **2** |
| Model Behavior & Inference Controls | 2025-04-02† | 2026-03-25 | lagging 357d | 1 | 0 | 0 | 0 | 7 | 11 | 1.76% | **1** |
| Workspace Isolation & File Operations | 2025-06-02 | 2026-03-12 | lagging 283d | 5 | 2 | 0 | 0 | 1 | 28 | 4.12% | **2** |
| Context Window as Managed Resource | 2025-04-02† | 2026-03-04 | lagging 336d | 4 | 1 | 0 | 2 | 4 | 7 | 2.50% | **2** |

† The source project warns that 2025-04-02 is a lower bound: upstream seeded
17 versions in its first public changelog commit that day.

## Per-model evidence

### 1. External Connectivity: MCP Servers, Providers & Network Reliability — 3/3

**Signatures:** MCP / Model Context Protocol; connectors; webhooks, network
errors/access, or remote servers. **244 prompts, 158 sessions (23.24%), 6 active
months, 3/3 signature families.** First seen 2026-03-01, 333 days after the
changelog lower bound. This is embedded: Vishal repeatedly asks Claude Code to
test, configure, restrict, and troubleshoot external connections.

> “kill canvas mcp servers bg processes” — 2026-03-13

> “did i tell you that ms teams connector is enabled for chatgpt edu?” — 2026-07-26

> “do users who are logged in to remote server , need to do anything. restart codex or similar?” — 2026-03-13

### 2. Extensibility Ecosystem: Plugins, Skills & Hooks — 3/3

**Signatures:** skills; hooks; plugins; slash/custom commands. **241 prompts,
140 sessions (20.59%), 5 active months, 4/4 families.** First seen 2026-03-01,
333 days after emergence. This is embedded: the prompts do not merely discover
extensions; they revise, evaluate, globalize, and debug them.

> “lets update the /skill-creator skill” — 2026-03-05

> “what is this hook that failed. fix it” — 2026-03-24

> “explain how the cli-anything plugin helps me draw in blender” — 2026-03-08

### 3. UI Navigation & Command Surfaces — 1/3

**Signatures:** command palette/slash commands; status line/bar; sidebar, file
picker, or permission mode. **13 prompts, 13 sessions (1.91%), 3 active months,
3/3 families.** First seen 2026-03-05, 337 days after emergence. The vocabulary
is real but sparse, so this is a trace rather than a recurring practice.

> “i think it was inside the claude code session and i saw a slash command notigication” — 2026-03-10

> “why do i see :(codex/monday-outreach-dynamic-roster) in the status bar below” — 2026-08-11

> “no, ill do it manually when needed. if you need to make it a skill or slash command, do that” — 2026-07-14

### 4. Terminal Rendering & Display — 0/3

**Signatures:** terminal/console output or terminal rendering; ANSI, wrapping,
or syntax highlighting; terminal/screen flicker or terminal spinner. **No direct
matches.** Seventeen apparent matches before filtering were all long generated
or pasted payloads, not direct requests. Corroborating observations and session
summaries also returned zero. No prompt examples exist by definition.

**Zero positive control:** on the same filtered `user_prompts_fts` path,
`MATCH 'Claude'` returned **221** rows. The zero is not a broken FTS join; the
signature may still be too narrow for ordinary phrases such as “looks wrong.”

### 5. Terminal Input & Interaction — 0/3

**Signatures:** Vim mode/keybindings; multiline input/Shift+Enter; keyboard
shortcuts/hotkeys; bracketed paste/paste mode. **No direct matches.** The
unfiltered hits were imported changelog items, exactly the contamination the
direct-prompt filter was designed to remove. Observations and session summaries
also returned zero. No prompt examples exist by definition.

**Zero positive control:** the same filtered `MATCH 'Claude'` query returned
**221** rows. The signature is intentionally narrow and may miss interaction
habits that Vishal performs without asking Claude Code about them.

### 6. Multi-Agent Orchestration & Task Lifecycle — 2/3

**Signatures:** sub-agents; agent teams/fleets; dispatch/delegation; parallel
agents. **112 prompts, 64 sessions (9.41%), 6 active months, 4/4 families.**
First seen 2026-03-01, 317 days after emergence. It is recurring and accelerating,
but misses the 10% session-share threshold for “embedded” by 0.59 percentage
points.

> “sure , use agent team to get it done faster” — 2026-03-02

> “yes, fix those and run the M4I7 test with parallel agents” — 2026-07-27

> “i think i dispatched devin to phase 2 manually” — 2026-08-05

### 7. Permission & Security Boundaries — 3/3

**Signatures:** permission/authorization; sandbox/allowlist/denylist; read-only
boundaries; approval gates and no-push/no-publish instructions. **149 prompts,
91 sessions (13.38%), 6 active months, 4/4 families.** First seen 2026-03-04,
336 days after emergence. This is embedded and often expressed as an explicit
authorization boundary.

> “wire this into Claude Code in readonly mode” — 2026-06-14

> “creating fine grained pat. what permissions does it need” — 2026-03-15

> “yes, make it approval-gated and fix both dates” — 2026-08-01

### 8. Resource Monitoring, Observability & Performance — 2/3

**Signatures:** token accounting; performance/latency/timeouts/resource usage;
monitoring/observability; log files/tracing/telemetry. **37 prompts, 23 sessions
(3.38%), 4 active months, 4/4 families.** First seen 2026-03-05, 337 days after
emergence. This is recurring, with evidence spanning both system health and the
design of monitoring surfaces.

> “i just saw an alert abhout high memory usage. what was that” — 2026-03-10

> “live fetch of data from formbuilder is high latency and an overkill. The data barely changes once or twice a day” — 2026-03-16

> “pull and tell me if we discussed any admin screen for me to monitor platform usage and such” — 2026-06-19

### 9. Session Identity & Persistence — 3/3

**Signatures:** resume/continue session; session/conversation identifiers;
conversation or usage history; wrap-up and “where were we” handoffs. **632
prompts, 475 sessions (69.85%), 6 active months, 3/4 families.** First seen
2026-03-02, 334 days after emergence. This is the most pervasive model, driven
largely by a highly routinized wrap-up practice.

> “wrap up sessions in both repositories” — 2026-03-09

> “wrap up session and commit everything” — 2026-07-28

> “/wrap-up-session  and move back to main” — 2026-08-10

### 10. Configuration as a Layered Policy Hierarchy — 2/3

**Signatures:** CLAUDE.md/AGENTS.md/project instructions; settings/configuration
files; hierarchy or precedence; environment variables. **73 prompts, 57 sessions
(8.38%), 6 active months, 3/4 families.** First seen 2026-03-04, 336 days after
emergence. Repeated editing of instruction files shows a recurring policy-layer
practice, but its session share stays below the embedded threshold.

> “commit the CLAUDE.md auth-split note too” — 2026-07-06

> “add a positive control rule for canvas checks to CLAUDE.md” — 2026-08-23

> “dont know the difference between putting in claude.md global or auto memory” — 2026-06-28

### 11. Model Behavior & Inference Controls — 1/3

**Signatures:** Opus/Sonnet/Haiku; model selection; reasoning/thinking controls;
plan/fast modes. **19 prompts, 12 sessions (1.76%), 3 active months, 4/4
families.** First seen 2026-03-25, 357 days after emergence. The examples are
substantive, but the behavior is too sparse for the recurring threshold.

> “rerun workflows with opus or sonnet?  why use fable?” — 2026-07-14

> “Let's do opus for control and sonnet maybe on uh high reasoning for the fleet?” — 2026-08-15

> “why not open another pane for yourself with opus as the model (use dsp alias if needed) and start on the article?” — 2026-08-05

### 12. Workspace Isolation & File-System Operations — 2/3

**Signatures:** worktrees; dirty/uncommitted/unrelated changes; working directory
or cwd; separate/isolated branches. **36 prompts, 28 sessions (4.12%), 4 active
months, 3/4 families.** First seen 2026-03-12, 283 days after emergence—the
shortest observed lag. This is recurring, with a sharp rise to 28 prompts in
August.

> “just do the markdown cleanup in a separate branch” — 2026-04-10

> “open another session for badm554-online and pick the right cwd” — 2026-08-23

> “do dedicated worktrees, can you drive panes or tabs in herdr here to do this” — 2026-08-08

### 13. Context Window as a Finite, Managed Resource — 2/3

**Signatures:** context capacity; compact/compaction; clear/fresh/new context;
memory and session handoff. **18 prompts, 17 sessions (2.50%), 5 active months,
4/4 families.** First seen 2026-03-04, 336 days after emergence. This is
recurring: Vishal explicitly diagnoses context capacity and chooses between
compaction, a clean context, and durable memory.

> “coming close to the context limit. what do you recommend” — 2026-07-31

> “create a plan for the rest. and compact” — 2026-03-04

> “lets wrap up and clear context and then start” — 2026-03-22

## Timeline interpretation

The changelog timeline and usage timeline do not overlap: the final canonical
theme emerged by 2025-06-02, while the personal corpus begins 2026-03-01. The
observed lags therefore mainly measure the **left-censoring boundary** of the
personal archive. The useful comparison is relative: workspace isolation has
the shortest observed lag (283 days), model controls the longest (357 days),
and both terminal-surface models remain absent through 2026-08-26.

The monthly profiles add more information than the first dates. Multi-agent use
climbs from 20 prompts in March to 75 in August; permissions rise from 22 to 76;
workspace isolation rises from 5 to 28. Session persistence is already strong
at the corpus boundary and stays high. The May trough reflects only four
eligible interactive sessions after synthetic traffic is removed, not a real
month-long behavioral collapse.

## Gaps and cautions

1. **No evidence is not proof of no behavior.** Terminal display and input can
   be used tacitly without generating a prompt. Their signatures are narrower
   than those for policy or orchestration.
2. **The archive starts late.** All leading/lagging labels are relative to a
   March 2026 observation floor. “Lagging” cannot establish when adoption truly
   began.
3. **Session share is a recorded-session measure.** The denominator is the 680
   sessions surviving the direct-prompt filter, not every shell invocation.
4. **Signatures overlap conceptually.** Slash commands touch UI and
   extensibility; memory touches sessions, configuration, and context. Counts
   are per model and are not meant to sum.
5. **FTS measures language, then judgment narrows it.** Examples were manually
   reviewed, observations/summaries were used as corroboration, and imported or
   generated false positives were removed. This is stronger than raw keyword
   counting but remains an interpretive measurement.

## Appendix A — exact SQL used

The following is the final SQL used for the reported counts. It was run with
`sqlite3 -readonly ~/.claude-mem/claude-mem.db`. The observation/summary spot
check and zero positive control follow it.

```sql
SELECT COUNT(*) AS raw_prompts,
       COUNT(DISTINCT content_session_id) AS raw_sessions,
       MIN(substr(created_at,1,10)) AS first_date,
       MAX(substr(created_at,1,10)) AS last_date,
       SUM(prompt_text LIKE 'Source: changelog%') AS imported_changelog_prompts
FROM user_prompts;

SELECT COUNT(*) AS eligible_prompts,
       COUNT(DISTINCT p.content_session_id) AS eligible_sessions
FROM user_prompts p
JOIN sdk_sessions sdk USING(content_session_id)
WHERE sdk.memory_session_id IS NOT NULL
  AND length(p.prompt_text) <= 2000
  AND p.prompt_text NOT LIKE 'Source:%'
  AND p.prompt_text NOT LIKE 'You are %'
  AND p.prompt_text NOT LIKE '<task-notification>%'
  AND p.prompt_text NOT LIKE 'Themes:%'
  AND p.prompt_text NOT LIKE 'Open codes:%';

CREATE TEMP TABLE signatures (
  model_id TEXT, model_name TEXT, emergence_date TEXT,
  family TEXT, fts_query TEXT
);

INSERT INTO signatures VALUES
('external','External Connectivity','2025-04-02','MCP','mcp OR "model context protocol"'),
('external','External Connectivity','2025-04-02','connectors','connector OR connectors'),
('external','External Connectivity','2025-04-02','network integration','webhook OR webhooks OR "network error" OR "network access" OR "remote server"'),
('extensibility','Extensibility Ecosystem','2025-04-02','skills','skill OR skills'),
('extensibility','Extensibility Ecosystem','2025-04-02','hooks','hook OR hooks'),
('extensibility','Extensibility Ecosystem','2025-04-02','plugins','plugin OR plugins'),
('extensibility','Extensibility Ecosystem','2025-04-02','custom commands','"slash command" OR "slash commands" OR "custom command" OR "custom commands"'),
('ui_navigation','UI Navigation','2025-04-02','command discovery','"command palette" OR "slash command" OR "slash commands"'),
('ui_navigation','UI Navigation','2025-04-02','status surface','"status line" OR statusline OR "status bar"'),
('ui_navigation','UI Navigation','2025-04-02','navigation surface','sidebar OR "file picker" OR "permission mode"'),
('terminal_rendering','Terminal Rendering','2025-04-02','terminal output','"terminal output" OR "console output" OR "terminal rendering"'),
('terminal_rendering','Terminal Rendering','2025-04-02','display mechanics','ansi OR "line wrap" OR "line wrapping" OR "syntax highlighting"'),
('terminal_rendering','Terminal Rendering','2025-04-02','render stability','"terminal flicker" OR "screen flicker" OR "terminal spinner"'),
('terminal_input','Terminal Input','2025-04-02','editing mode','"vim mode" OR keybinding OR keybindings'),
('terminal_input','Terminal Input','2025-04-02','multiline entry','"multiline input" OR "multi line input" OR "shift enter"'),
('terminal_input','Terminal Input','2025-04-02','keyboard control','"keyboard shortcut" OR "keyboard shortcuts" OR hotkey OR hotkeys'),
('terminal_input','Terminal Input','2025-04-02','paste handling','"bracketed paste" OR "paste mode" OR "pasted input"'),
('multi_agent','Multi-Agent Orchestration','2025-04-18','sub-agents','subagent OR subagents OR "sub agent" OR "sub agents"'),
('multi_agent','Multi-Agent Orchestration','2025-04-18','teams and fleets','"agent team" OR "agent teams" OR teammate OR teammates OR fleet'),
('multi_agent','Multi-Agent Orchestration','2025-04-18','delegation','dispatch OR dispatched OR delegate OR delegated OR delegation'),
('multi_agent','Multi-Agent Orchestration','2025-04-18','parallel agents','"parallel agent" OR "parallel agents" OR "parallelize agents"'),
('permissions','Permission Boundaries','2025-04-02','permission and authority','permission OR permissions OR authorization OR authorized'),
('permissions','Permission Boundaries','2025-04-02','sandbox and lists','sandbox OR allowlist OR denylist'),
('permissions','Permission Boundaries','2025-04-02','read-only boundaries','"read only" OR readonly OR "do not write" OR "no edits"'),
('permissions','Permission Boundaries','2025-04-02','approval gates','approval OR approve OR "do not push" OR "do not publish"'),
('observability','Resource Monitoring','2025-04-02','token accounting','"token budget" OR "token usage" OR "usage limit"'),
('observability','Resource Monitoring','2025-04-02','runtime resources','performance OR latency OR timeout OR "memory usage" OR "cpu usage"'),
('observability','Resource Monitoring','2025-04-02','monitoring','monitor OR monitoring OR observability'),
('observability','Resource Monitoring','2025-04-02','logs and traces','"log file" OR "log files" OR tracing OR telemetry'),
('session_identity','Session Identity','2025-04-02','resume','"resume session" OR "resume this" OR "continue session"'),
('session_identity','Session Identity','2025-04-02','session identity','"session id" OR "session identifier" OR "conversation id"'),
('session_identity','Session Identity','2025-04-02','history','"conversation history" OR "usage history" OR "previous session"'),
('session_identity','Session Identity','2025-04-02','handoff','"wrap up" OR "where were we" OR "pick up where"'),
('configuration','Layered Configuration','2025-04-02','instruction files','"CLAUDE md" OR "AGENTS md" OR "project instructions"'),
('configuration','Layered Configuration','2025-04-02','settings','"settings json" OR "config file" OR "configuration file"'),
('configuration','Layered Configuration','2025-04-02','precedence','"instruction hierarchy" OR "configuration precedence" OR "project level" OR "user level"'),
('configuration','Layered Configuration','2025-04-02','environment','"environment variable" OR "environment variables"'),
('model_controls','Model Controls','2025-04-02','model families','opus OR sonnet OR haiku'),
('model_controls','Model Controls','2025-04-02','model selection','"model selection" OR "choose model" OR "switch model" OR "model choice"'),
('model_controls','Model Controls','2025-04-02','reasoning controls','"reasoning effort" OR "thinking mode" OR "extended thinking"'),
('model_controls','Model Controls','2025-04-02','interaction modes','"plan mode" OR "fast mode"'),
('workspace','Workspace Isolation','2025-06-02','worktrees','worktree OR worktrees'),
('workspace','Workspace Isolation','2025-06-02','dirty-state care','"dirty worktree" OR "uncommitted changes" OR "unrelated changes"'),
('workspace','Workspace Isolation','2025-06-02','working directory','"current working directory" OR "working directory" OR cwd'),
('workspace','Workspace Isolation','2025-06-02','branch isolation','"separate branch" OR "isolated branch" OR "workspace isolation"'),
('context','Managed Context','2025-04-02','context capacity','"context window" OR "context limit" OR "context budget"'),
('context','Managed Context','2025-04-02','compaction','compact OR compaction'),
('context','Managed Context','2025-04-02','context reset','"clear context" OR "fresh context" OR "new context"'),
('context','Managed Context','2025-04-02','memory and handoff','"memory file" OR "update memory" OR "remember this" OR "session handoff"');

CREATE TEMP VIEW matched_family AS
SELECT DISTINCT s.model_id, s.model_name, s.emergence_date, s.family,
       p.id AS prompt_id, p.content_session_id, p.created_at, p.prompt_text
FROM signatures AS s
JOIN user_prompts_fts ON user_prompts_fts MATCH s.fts_query
JOIN user_prompts AS p ON p.id = user_prompts_fts.rowid
JOIN sdk_sessions AS sdk ON sdk.content_session_id = p.content_session_id
WHERE sdk.memory_session_id IS NOT NULL
  AND length(p.prompt_text) <= 2000
  AND p.prompt_text NOT LIKE 'Source:%'
  AND p.prompt_text NOT LIKE 'You are %'
  AND p.prompt_text NOT LIKE '<task-notification>%'
  AND p.prompt_text NOT LIKE 'Themes:%'
  AND p.prompt_text NOT LIKE 'Open codes:%';

CREATE TEMP VIEW matched_model AS
SELECT DISTINCT model_id, model_name, emergence_date, prompt_id,
                content_session_id, created_at, prompt_text
FROM matched_family;

SELECT s.model_id, s.model_name, s.emergence_date,
       MIN(substr(m.created_at,1,10)) AS first_seen,
       COUNT(DISTINCT m.prompt_id) AS matching_prompts,
       COUNT(DISTINCT m.content_session_id) AS matching_sessions,
       ROUND(100.0 * COUNT(DISTINCT m.content_session_id) /
         (SELECT COUNT(DISTINCT p.content_session_id)
          FROM user_prompts p JOIN sdk_sessions sdk USING(content_session_id)
          WHERE sdk.memory_session_id IS NOT NULL
            AND length(p.prompt_text) <= 2000
            AND p.prompt_text NOT LIKE 'Source:%'
            AND p.prompt_text NOT LIKE 'You are %'
            AND p.prompt_text NOT LIKE '<task-notification>%'
            AND p.prompt_text NOT LIKE 'Themes:%'
            AND p.prompt_text NOT LIKE 'Open codes:%'), 2) AS session_share_pct,
       COUNT(DISTINCT mf.family) AS signature_families_hit
FROM (SELECT DISTINCT model_id,model_name,emergence_date FROM signatures) s
LEFT JOIN matched_model m USING(model_id,model_name,emergence_date)
LEFT JOIN matched_family mf
  ON mf.model_id=m.model_id AND mf.prompt_id=m.prompt_id
GROUP BY s.model_id,s.model_name,s.emergence_date;

WITH months(month) AS (
  VALUES ('2026-03'),('2026-04'),('2026-05'),
         ('2026-06'),('2026-07'),('2026-08')
)
SELECT s.model_id, months.month, COUNT(DISTINCT m.prompt_id) matching_prompts
FROM (SELECT DISTINCT model_id FROM signatures) s
CROSS JOIN months
LEFT JOIN matched_model m
  ON m.model_id=s.model_id AND substr(m.created_at,1,7)=months.month
GROUP BY s.model_id,months.month;

SELECT model_id,family,COUNT(DISTINCT prompt_id) AS matching_prompts
FROM matched_family
GROUP BY model_id,family;

-- Corroborating machine summaries, restricted to sessions already matched by
-- direct prompts. These counts support spot checks; they are not adoption counts.
WITH matched_mem AS (
  SELECT DISTINCT m.model_id,sdk.memory_session_id
  FROM matched_model m JOIN sdk_sessions sdk USING(content_session_id)
),
obs_hits AS (
  SELECT DISTINCT sig.model_id,o.id
  FROM signatures sig
  JOIN observations_fts ON observations_fts MATCH sig.fts_query
  JOIN observations o ON o.id=observations_fts.rowid
  JOIN matched_mem mm
    ON mm.model_id=sig.model_id AND mm.memory_session_id=o.memory_session_id
),
summary_hits AS (
  SELECT DISTINCT sig.model_id,ss.id
  FROM signatures sig
  JOIN session_summaries_fts ON session_summaries_fts MATCH sig.fts_query
  JOIN session_summaries ss ON ss.id=session_summaries_fts.rowid
  JOIN matched_mem mm
    ON mm.model_id=sig.model_id AND mm.memory_session_id=ss.memory_session_id
)
SELECT x.model_id,COUNT(DISTINCT o.id) observation_hits,
       COUNT(DISTINCT sh.id) summary_hits
FROM (SELECT DISTINCT model_id FROM signatures) x
LEFT JOIN obs_hits o USING(model_id)
LEFT JOIN summary_hits sh USING(model_id)
GROUP BY x.model_id;

-- Positive control, run separately for each zero-result model.
SELECT COUNT(*) AS positive_control_claude
FROM user_prompts_fts f
JOIN user_prompts p ON p.id=f.rowid
JOIN sdk_sessions sdk USING(content_session_id)
WHERE user_prompts_fts MATCH 'Claude'
  AND sdk.memory_session_id IS NOT NULL
  AND length(p.prompt_text) <= 2000
  AND p.prompt_text NOT LIKE 'Source:%'
  AND p.prompt_text NOT LIKE 'You are %'
  AND p.prompt_text NOT LIKE '<task-notification>%'
  AND p.prompt_text NOT LIKE 'Themes:%'
  AND p.prompt_text NOT LIKE 'Open codes:%';
-- Result for Terminal Rendering: 221
-- Result for Terminal Input: 221
```

## Appendix B — canonical source themes

The names and emergence dates come from `docs/findings.md`. The source project
labels seven themes high-confidence, three provisional, and three
bottom-up-only; its median coherence is 0.30. This usage overlay does not
upgrade those source-theme confidence levels. It asks a different question:
whether Vishal's own prompts contain observable behaviors consistent with each
canonical theme.
