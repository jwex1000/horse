# HORSE Prompt Design

How prompts in this library are built. This is the architecture behind every prompt file — what a prompt must do, the file format the site consumes, and the mechanics we use on purpose. If you're writing or adapting a prompt for this library, start here.

## Design principles

**Technique prompts, not task recipes.** Every prompt here helps you do one of the HORSE elements better — sharpen an objective, set a role, bound a scope, evaluate an output. None of them are "write me a marketing email." Task recipes go stale and teach nothing; techniques transfer to any work.

**Domain-agnostic, tool-agnostic.** Assume nothing about the reader's industry or job. Assume only a chat interface — ChatGPT, Copilot, Claude, Gemini, or anything like them. Prompts may freely lean on web search, file uploads, and memory, since nearly every tool has them now.

**Prompts work copy-pasted, as-is.** Many readers will copy the prompt without reading anything around it. Every prompt must be self-contained: no placeholders that break it, no setup steps hidden in the surrounding prose. The teaching around a prompt is for the minority who read it.

**No naked prompts.** Every prompt is reachable only through something that told you why you'd want it. That context travels in the file itself: the `summary` and `use_when` frontmatter get the prompt picked correctly, and the body sections teach it once you're inside. When an element fans out into sub-topics (like the five roles), each sub-topic gets a short intro before its prompts.

**A sentence can be a prompt.** Length is earned by rules, not padding. Some of the best technique prompts are one line ("Confirm your understanding before you start."); long prompts are fine when the length is behavioral rules the AI must follow.

## The file contract

Every prompt lives in `<element>/prompts/<name>.md`:

```markdown
---
title:
element: objective      # harness | objective | role | scope | evaluate
level: beginner         # beginner | intermediate
summary:                # one line for cards/search
use_when:               # 1–2 situations this is for
---

## The prompt
## Why it works
## Example
## It's working if
## Watch out for
```

The first three sections are required. The last two are optional but encouraged:

- **It's working if** — success signals for a fuzzy technique. A conversation doesn't have a test suite, so tell the reader what good feels like ("it's working if you disagree with something the AI proposed").
- **Watch out for** — the technique's named limits and failure modes. Every technique has a boundary; naming it is part of teaching it ("this stalls when the question needs a prototype, not more talking").

The companion site renders only `## The prompt` on its surface pages. Everything else is for the GitHub reader and deeper site views — so the extra sections cost the casual visitor nothing.

## How the site consumes this repo

The site fetches `index.json` for the catalog, then prompt bodies on demand. Each element page shows one short intro paragraph, then the start-here prompt with a copy button. That means:

- Each element `README.md` leads with one tight paragraph (~50–60 words) — the site takes the first paragraph as the on-page intro. Deeper teaching follows below it.
- The prompt body under `## The prompt` must be clean, final text — exactly what a reader should paste, nothing else.

## Interview prompts

The library's flagship move is flipped interaction: the AI interviews you. Most good sessions open with some version of it — a co-creative session starts as an interview, and even "write this email" starts with a question or two — because interviewing is simply how the AI acquires your objective, scope, and context instead of guessing them. But not everything needs one, and nothing needs a maximal one. Any interview-style prompt in this library follows these mechanics:

- **One question at a time. Always.** Never a wall of questions. Ask, wait for the answer, then ask the next. This is a hard rule of the library — a batch of eight questions in a chat window is where beginners bail.
- **Right-size the interview.** The depth of questioning scales with the stakes and novelty of the task: two questions for an email, twenty for a business decision. Interview prompts instruct the AI to size its questioning to the task — thoroughness is not the goal; sufficiency is.
- **Recommend answers for decisions, never for elicitation.** When a question is a genuine decision with a sensible default ("email or memo?"), the AI may propose its recommendation for the user to accept or push back on. When the question is drawing something out of the user — their objective, their context, what good looks like — the AI asks openly and never suggests the answer. Only the user has that material.
- **Document as you go.** A good interviewer takes notes. The AI keeps a running bulleted record of what's been settled, visible to the user — so nothing gets lost, and the wrap-up artifact is trustworthy instead of reconstructed.
- **Probe thin answers.** A good interviewer doesn't accept the first answer — "can you give me more context on that?" is always available. First answers are often labels for things the user hasn't unpacked yet.
- **Facts are the AI's job; decisions are the user's.** The AI never asks the user to go look something up it could find or reason out itself.
- **There is an explicit end condition.** The interview ends when nothing is left silently assumed.
- **No producing until the user confirms.** Mid-interview, the AI will be tempted to jump ahead and start drafting the deliverable. It doesn't. The interview ends with the AI summarizing what it heard; only when the user confirms the summary does the actual work begin.
- **End with an artifact.** Close by producing something portable — "write up what we decided in one paragraph I can reuse." A conversation the user keeps beats a conversation the user remembers.

The known failure mode is passivity: answering "agreed, agreed, agreed" and ending up with a plan the AI wrote and you nodded at. "I don't know" is a real answer. It's working if you disagree with something.

## Reusing what interviews learn

Interviews have a cost: without somewhere to put what they learn, they repeat themselves — every session re-asks who you are, how you work, what you're building. The library has two answers now, and one later:

- **The artifact.** Every interview ends with a reusable brief. Paste it into the next session instead of re-answering.
- **Install-once prompts.** Nearly every tool has memory now, so some prompts are run once and persist: "Remember: whenever I bring you a task, start by interviewing me — one question at a time, sized to the task." Use once, benefit in every future session. This is a distinct prompt genre in the library, and part of the Harness element: shaping the tool, not just the conversation.
- **Later: the rider profile.** A standing document about how you work — produced by an interview, pasted anywhere. Not built yet; noted so the design leaves room for it.

## Role prompts

A role prompt works through behavioral rules, not a costume. "Act as a tutor" does nothing; the rules do everything:

- One question at a time. Wait for the answer.
- Never ask "do you understand?" — make the user explain it or apply it instead.
- State what the role won't do ("don't do the work for me — make me plan the next step").

When writing a role prompt, spend the words on the rules of engagement, not on describing the character.
