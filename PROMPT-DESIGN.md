# HORSE Prompt Design

How prompts in this library are built: what a prompt file is, what makes a good HORSE prompt, and where the teaching lives. If you're writing or adapting a prompt for this library, start here.

## What a prompt file is

A prompt file has one job: hold the text a visitor copies. The companion site reads the file, draws a card from the frontmatter, and puts the prompt text behind a copy button. Nobody reads the file itself. Nothing in it teaches, explains, or gives an example. If a reader needs to know something before using the prompt, the prompt says it.

Every prompt lives in `<element>/prompts/<name>.md`:

```markdown
---
title:
element: objective      # harness | objective | role | scope | evaluate
level: beginner         # beginner | intermediate | advanced | expert
style: interview        # interview | instruction
summary:                # one line for cards and search
use_when:               # 1–2 situations this is for
---

## The prompt

<the text a visitor copies, and nothing else>
```

The frontmatter is what the site knows about a prompt, so keep the six fields and their values. `style` says what kind of prompt it is. An `interview` prompt has the AI question the reader before doing anything; an `instruction` prompt tells the AI how to behave and the reader carries on. New styles get added here as they appear. `start-here.md` in each element's `prompts/` folder is that element's first prompt. The body has exactly one heading, `## The prompt`, because the site finds the copyable text by that heading. Everything under it is what gets copied, so it must be clean, final text. Structure inside the prompt is welcome when it helps the AI follow it: bold step labels, numbered steps, bulleted rules. Just never use a `##` heading inside the prompt, or the site will cut the text there.

## What makes a good HORSE prompt

**It teaches a technique, not a task.** Every prompt helps you do one of the HORSE elements better: sharpen an objective, set a role, bound a scope, evaluate an output. None of them are "write me a marketing email." Task recipes go stale and teach nothing. Techniques transfer to any work.

**It assumes nothing about the reader or the tool.** No industry, no job, no particular AI. Assume a chat window. Prompts may lean on web search, file uploads, and memory, since nearly every tool has them now.

**It works copy-pasted, as is.** No placeholders to fill in, no setup outside the text, no reliance on anything the reader was supposed to read first.

**It picks up where the last element left off.** HORSE is walked in order, so a prompt asks whether the reader has already done the earlier elements and takes their output as given. The Role and Scope prompts take the objective if the reader pastes it. The Evaluate prompt asks for the objective and scope. If the reader has nothing, the prompt carries on without it.

**It isn't verbose, and it is structured.** Say what the AI must do and stop. A sentence can be a prompt. When a prompt has several steps or rules, lay them out as steps and rules. Dense paragraphs save words and lose the reader and the AI both.

**It ends with something the reader can carry.** Almost always, the prompt should leave the reader holding a written result: an objective in a sentence, a role definition, a set of criteria. A result they can paste into the next session beats one they have to remember. The rare prompt that doesn't produce anything is fine, but it should be the exception.

## Where the teaching lives

The element `README.md`. It explains what the letter means and gives a feel for the stage. The site takes its first paragraph as the on-page intro, so that paragraph should stand alone at around 50 to 60 words, with the deeper teaching below it. Anything about why a prompt works, or what to watch for when using it, belongs in the README if it belongs anywhere.

## If the prompt is an interview

Some prompts have the AI interview the reader. These rules apply to those prompts and no others.

- **One question at a time.** Ask, wait for the answer, then ask the next. A batch of questions in a chat window is where beginners bail.
- **Size the interview.** Two questions for an email, twenty for a business decision. A prompt can do this by telling the AI to scale its questions to the task, or by having it reflect the answer back as soon as it can and letting a correction restart the questioning. The second works better on weaker models, because guessing early is mechanical and guessing the size is a judgment.
- **Ask openly first, suggest later.** When a question draws something out of the reader, their objective, their context, what good looks like, the AI asks without proposing an answer, because only the reader has that material. Once it has listened enough, it may suggest. "Enough" should be something the AI can observe, not judge: it has already reflected the answer back in the reader's words at least once, or the reader has said they don't know. A suggestion is a question ("is it something like X?"), never the answer, and the AI asks the reader to say it back in their own words. The reader's words go in the result. The AI's phrasing gets in only if the reader adopts it. For genuine decisions with a sensible default ("email or memo?"), the AI may recommend freely.
- **Take notes, quietly.** The AI keeps track of what the reader has said, especially the asides about how they'd do it, and uses it in the final result. It doesn't recite the notes back mid-interview. Reading the reader their own answers is padding, and weak models do it badly.
- **Don't accept thin answers.** A label, a single word, or "better" isn't an answer. Ask what kind, or what else.
- **Facts are the AI's job. Decisions are the reader's.** The AI never asks the reader to look up something it could find or reason out itself.
- **Don't produce until the reader confirms.** The AI will want to start drafting mid-interview. It doesn't. It summarizes what it heard, and the work begins only after the reader says yes.
- **Say how it ends.** The reader should know what "done" looks like before the interview starts.

The known failure is passivity: the reader says "agreed, agreed, agreed" and ends up with a plan the AI wrote and they nodded at. A good interview prompt makes the reader correct something.
