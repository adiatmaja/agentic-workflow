---
paths:
  - "**/README.md"
---

# Documentation

## README.md — Root Project

When creating or updating a root-level `README.md`, always include **ASCII art diagrams**
for workflow and architecture visualization. Do not use Mermaid or image links — ASCII
renders everywhere (terminal, GitHub, editors) without external dependencies.

### Workflow Diagrams

Use box-and-arrow ASCII art to visualize data flows, pipelines, and system architecture:

```
Single flow (linear):

  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │  PDF Input  │────▶│  Generator  │────▶│ Training DB │
  └─────────────┘     └─────────────┘     └─────────────┘

Multi-zone architecture:

  ┌──────────────────────────────────────────────────────────┐
  │  LAPTOP                                                  │
  │  ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
  │  │  PDFs    │───▶│ generate │───▶│  training data   │   │
  │  └──────────┘    └──────────┘    └────────┬─────────┘   │
  └────────────────────────────────────────────┼─────────────┘
                                               │
  ┌────────────────────────────────────────────▼─────────────┐
  │  DOCKER (GPU)                                            │
  │  ┌──────────────┐    ┌──────────────┐                    │
  │  │  Unsloth     │───▶│  Fine-tuned  │                    │
  │  │  Training    │    │  Model       │                    │
  │  └──────────────┘    └──────────────┘                    │
  └──────────────────────────────────────────────────────────┘

Decision / branching flow:

                    ┌─────────────┐
                    │  Validate   │
                    └──────┬──────┘
                           │
               ┌───────────┴───────────┐
               ▼                       ▼
          ┌─────────┐            ┌──────────┐
          │  Valid  │            │ Invalid  │
          └────┬────┘            └────┬─────┘
               │                     │
               ▼                     ▼
          ┌─────────┐          ┌───────────┐
          │  Save   │          │  Log Err  │
          └─────────┘          └───────────┘
```

### Box Characters

Use Unicode box-drawing characters for clean diagrams:

```
Corners : ┌ ┐ └ ┘
Sides   : │ ─
Joins   : ├ ┤ ┬ ┴ ┼
Arrows  : ─▶  ◀─  │▼  ▲│
Double  : ╔ ╗ ╚ ╝ ║ ═ (for highlighted zones)
```

### README Structure

Every root README.md should follow this structure:

```markdown
# Project Name

> One-line description of what this project does.

## Overview

Brief paragraph (3-5 sentences) explaining the problem and solution.

## Architecture / Workflow

ASCII diagram showing the high-level system or data flow.

## Quick Start

Minimal steps to get running (< 10 lines).

## Configuration

Key environment variables and config files.

## Project Structure

Directory tree with brief descriptions.

## Documentation

Links to detailed docs (if docs/ directory exists).
```

### Example

```
## Workflow

  ┌──────────────────────────────────────────────────────────────┐
  │  DATA GENERATION  (Laptop)                                   │
  │                                                              │
  │  PDFs / FAQs ──▶ pdf_loader ──▶ generator ──▶ data.jsonl    │
  │                                    ▲                         │
  │                              LM Studio API                   │
  └──────────────────────────────────────────────────────────────┘
                                    │
                              data.jsonl
                                    │
  ┌─────────────────────────────────▼────────────────────────────┐
  │  TRAINING  (Docker + GPU)                                    │
  │                                                              │
  │  data.jsonl ──▶ Unsloth ──▶ LoRA ──▶ merged model ──▶ GGUF │
  └──────────────────────────────────────────────────────────────┘
```
