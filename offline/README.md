# Running an agent like me offline, on your own computer

Three levels, from "use it today" to "build it yourself". Each works without sending your code anywhere.

| Level | What you get | Effort | Hardware |
|---|---|---|---|
| 1. Claude Code on a local model | This exact agent setup (CLAUDE.md, skills, hooks, the evolving-agent mod), with an open model doing the thinking | 15 minutes | 16 GB+ RAM/VRAM |
| 2. Your own agent loop | `offline/local_agent.py`: ~200 lines you can read and change, wired to this repo's memory and guard | 5 minutes after level 1's model server | same |
| 3. Your own model | Train a small GPT from scratch, then a tiny chat model | days to weeks | a GPU helps; level-3a runs on a laptop |

A local model is much weaker than me at long, multi-step agent work. Expect to keep tasks smaller and check its work more.

---

## 1. Claude Code on a local model (Ollama)

Verified against Ollama's own docs (`docs/integrations/claude-code.mdx`, `docs/api/anthropic-compatibility.mdx`).

1. Install [Ollama](https://ollama.com/download) (v0.14+ speaks the Anthropic Messages API that Claude Code uses).
2. Pull a tool-capable model that fits your memory (see the table below), for example `ollama pull qwen3-coder:30b`.
3. Raise the context window. Ollama recommends 64k+ for real repos: `OLLAMA_CONTEXT_LENGTH=64000 ollama serve`
4. Start Claude Code against it, either way:
   - one command: `ollama launch claude`
   - or by hand:
     ```
     export ANTHROPIC_BASE_URL=http://localhost:11434
     export ANTHROPIC_AUTH_TOKEN=ollama      # required but ignored
     export ANTHROPIC_API_KEY=""
     claude --model qwen3-coder:30b
     ```
5. Inside this repo, everything here loads as usual: rules, lessons, skills, hooks. Install the mod in other projects with
   `/plugin install evolving-agent --marketplace rydermetcalfx4-commits/agent` (that step needs the internet once).

Limits (from Ollama's docs): `tool_choice`, deferred tools and hosted web search aren't fully supported. Models tagged
`:cloud` run on Ollama's servers, so don't use those if you need fully offline. Claude Code itself may still want the
network for sign-in and updates; the model and your code stay local.

Other servers that work the same way: LM Studio, llama.cpp's `llama-server`, and LiteLLM as a bridge.

### Which model (consumer hardware, Q4 quantised, mid-2026 guides; verify on the model card)

| Memory | Good first picks |
|---|---|
| 8 GB | `qwen3:8b` (simple tasks only) |
| 16 GB | Devstral Small 2 (24B), `gpt-oss:20b` |
| 24 GB (RTX 3090/4090) | Qwen3-Coder 30B-A3B (fast MoE), Devstral Small 2 |
| 64–128 GB unified memory (Apple Silicon) | larger Qwen3-Coder / GLM Air variants |

## 2. Your own agent loop: `offline/local_agent.py`

The same loop Claude Code runs, stripped to the bone and readable in one sitting: send messages and tool schemas →
run the tools the model asks for → append the results → repeat until it answers in text.

```
ollama serve                                  # or llama-server / LM Studio on an OpenAI-compatible port
python3 offline/local_agent.py "summarise scripts/doctor.py"
AGENT_MODEL=qwen3-coder:30b python3 offline/local_agent.py      # interactive
```

- Tools: `read_file`, `write_file`, `list_files`, `run_shell` (asks before each command unless `AGENT_YES=1`).
- Stays inside the project directory, and refuses what `scripts/guard.py` refuses (secrets files, `rm -rf ~`, force-push to main).
- Loads lessons at confidence ≥ 0.7 from `memory/learnings.md` (or `.evolving-agent/learnings.md`) into its prompt,
  and logs failed tool calls to the matching `failures.log`, so `/evolve` learns from the offline agent's mistakes too.
- Standard library only. `python3 offline/test_local_agent.py` runs 6 tests against a fake model server.

Ideas for growing it (good first projects): an `edit_file` tool that replaces one exact string, streaming output,
a `/evolve` command that runs the evolve skill's steps, and a reflection pass (draft → critique → revise).

## 3. Your own model

Work through these in order. Each is open source and runs locally.

| Step | Resource | What you learn | License |
|---|---|---|---|
| 3a | [karpathy/nanoGPT](https://github.com/karpathy/nanoGPT), plus Karpathy's "Let's build GPT" video | a GPT in ~300 lines; trains on a laptop CPU on Shakespeare | MIT |
| 3b | [rasbt/LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) (book + code, ch01–ch07) | tokenizer → attention → GPT → pretraining → fine-tuning for classification and instructions | Apache-2.0 |
| 3c | [Lightning-AI/pytorch-lightning](https://github.com/Lightning-AI/pytorch-lightning) `examples/fabric/language_model/train.py` | the same transformer training loop with Lightning Fabric: mixed precision, multi-GPU, checkpoints, with no code changes | Apache-2.0 |
| 3d | [karpathy/nanochat](https://github.com/karpathy/nanochat) | the full pipeline in ~8k lines: tokenizer, pretraining, SFT, RL, inference, and a web chat UI. Designed for one 8×GPU node; a CPU/MPS mode exists for tiny runs | MIT |
| 3e | Fine-tune an open model on your own data (LoRA via Hugging Face PEFT, or Unsloth), then serve it with Ollama/llama.cpp | make a model that knows your projects | varies |

Being realistic: a from-scratch model you can train at home will chat, but it won't approach the open coding models in
level 1. The practical path to "an AI like you, offline" is level 1 or 2 with a strong open model, plus 3e to specialise it.

## Background learning

- [AMAI-GmbH/AI-Expert-Roadmap](https://github.com/AMAI-GmbH/AI-Expert-Roadmap) (MIT): a topic map from fundamentals
  to deep learning. The checklist distilled from it is in `research/offline-ai-2026-10.md`.
- [500 AI/ML/DL/CV/NLP projects](https://github.com/ashishpatel26/500-AI-Machine-learning-Deep-learning-Computer-vision-NLP-Projects-with-code):
  a link list of project collections, indexed in `catalog/external/ai-projects.md`.

Tutorial sources (third-party, quality varies): [Ollama + Claude Code guide (morphllm)](https://www.morphllm.com/ollama-claude-code),
[KDnuggets: pairing Claude Code with local models](https://www.kdnuggets.com/pairing-claude-code-with-local-models),
[Build an AI coding agent from scratch in Python](https://youcanbuildthings.com/articles/build-ai-coding-agent-from-scratch-python/),
[tool-agent-lab (from-scratch loop + tests)](https://github.com/yassineldieb2-hrd/tool-agent-lab),
[Ollama tool calling guide](https://localaimaster.com/blog/ollama-tool-calling-guide),
[KDnuggets: top coding models to run locally](https://www.kdnuggets.com/top-7-coding-models-you-can-run-locally-in-2026).
