---
title: Financial model, Harness
case: financial-model
element: harness
prompt: harness/prompts/start-here.md
search: both
---

## The rider

You run a small services business and have just finished some strategy work with a consultant. You now want a financial model so you can make three decisions about where to take the business, understand your costs, and see what revenue might look like under a few assumptions. You would describe what you're about to do as "build a financial model for my business." It is not a one-off: you expect to keep coming back to it as things change.

You do not know Excel. You can open a spreadsheet and type numbers into cells, but you do not know formulas, you have never built a spreadsheet from scratch, and you do not know what a financial model is made of or how one is read. You have not planned any of this work yet. If asked what you already work in day to day, you say email, Google Docs, and ChatGPT. Your business has a Microsoft 365 subscription, so Excel is installed, but you rarely open it. You have used ChatGPT for a few months and like it. You have never heard of Claude in Excel or of any AI that works inside a spreadsheet, and you don't know that such things exist unless the assistant tells you.

You are moderately comfortable with technology. Your first instinct is to say you just want this done. If the assistant asks whether you need to understand the model yourself, or points out that you will have to keep using it for decisions, you admit that yes, you do need to understand it, because you will be the one making the decisions with it. You have no real budget constraint for software. You would rather your financial numbers not go into random tools, but you're fine with the major AI products. You can spend a few hours a week on this.

Answer questions briefly and plainly, the way a busy business owner would. Don't use technical words you wouldn't know.

## Criteria

- asks-daily-tools: The interview asks what the rider already works in day to day before making a recommendation.
- surfaces-no-excel: The interview surfaces, before recommending, that the rider does not know Excel or how financial models work.
- names-spreadsheet-tool: The final recommendation names at least one specific product that works inside a spreadsheet, such as Claude in Excel.
- learn-or-get-done: The final recommendation says whether the rider should learn the tool or just get this done, and gives a reason.
- one-question-per-turn: Every assistant turn before the final note asks at most one question.
- setup-note-delivered: The conversation ends with a written setup note that lists the recommended tools, how to set each one up, and why.
