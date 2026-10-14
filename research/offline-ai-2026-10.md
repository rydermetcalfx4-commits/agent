# Research: AI learning repos + running an agent offline (2026-10-14)

Asked to scrape three repos and find solid tutorials for building and running "an AI like me" offline, on the user's computer.
Deliverables: `offline/README.md` (the guide), `offline/local_agent.py` (a working local agent), `catalog/external/ai-projects.md`.

## The three repos

| Repo | License | What's actually in it | Taken |
|---|---|---|---|
| AMAI-GmbH/AI-Expert-Roadmap (a4c66c2, 2025-09) | MIT | Roadmap diagrams (SVG/draw.io); the README is only images and links | the topic checklist below, extracted from the diagram text |
| Lightning-AI/pytorch-lightning (84df182, 2026-09) | Apache-2.0 | Training framework: LightningModule/Trainer, Fabric, and examples including a small transformer language model on WikiText-2 | `examples/fabric/language_model/train.py` as level 3c of the guide; no code vendored |
| ashishpatel26/500-AI-…-Projects-with-code (5f10445, 2025-08) | none | A single README table of 103 links (63 GitHub collections, 40 articles); no code | names and links indexed in `catalog/external/ai-projects.md` |

None of them is about agents. They're learning material for building and training models, which is level 3 of the guide.

## Roadmap checklist (distilled from the AI-Expert-Roadmap diagrams)
- **Fundamentals**: linear algebra and matrices; databases (SQL joins, NoSQL); data formats (JSON, XML, CSV); regex;
  Python (venvs, data structures, PEP 8, NumPy, Pandas); data munging, EDA, PCA, missing values; Jupyter; web scraping.
- **Machine learning**: concepts (gradient descent, cost functions, over/underfitting, train/val/test, precision vs
  recall, bias vs variance); supervised (linear/logistic regression, trees, naïve Bayes, KNN, SVM); unsupervised
  (k-means, DBSCAN, hierarchical, GMM, PCA, t-SNE, UMAP); ensembles (bagging, boosting, stacking); RL (Q-learning); scikit-learn.
- **Deep learning**: feedforward nets, CNNs, RNN/LSTM/GRU, autoencoders, GANs, **Transformers (attention, encoder, decoder)**,
  residual connections; training (optimizers SGD→Adam, LR schedules, batch norm, dropout, early stopping, augmentation);
  transfer and multitask learning; distillation and quantization; PyTorch, Hugging Face Transformers, TensorBoard, MLflow.
- For building an LLM, the critical path is Python → linear algebra → gradient descent → feedforward nets →
  attention/Transformers → training tricks → quantization (to run it locally).

## Running an agent offline: what's verified
- **Claude Code + Ollama**: confirmed in Ollama's repo docs (`docs/integrations/claude-code.mdx`,
  `docs/api/anthropic-compatibility.mdx`). The commands are `ollama launch claude`, or `ANTHROPIC_BASE_URL=http://localhost:11434`
  with `ANTHROPIC_AUTH_TOKEN=ollama`, plus a 64k+ context. Supported: messages, streaming, tools, thinking.
  Not supported: `tool_choice` and hosted web search.
- **From-scratch training**: karpathy/nanochat (MIT, updated 2026-07; tokenizer→pretrain→SFT→RL→chat UI, `uv sync --extra cpu`
  for CPU/MPS), karpathy/nanoGPT (MIT), rasbt/LLMs-from-scratch (Apache-2.0, ch01–ch07 + appendices, updated 2026-10).
- **Model picks** come from third-party 2026 guides, which disagree and sometimes cite unverifiable model names. They're
  treated as starting points in the guide, with "verify on the model card".

## What couldn't be verified here
ollama.com, huggingface.co and GitHub release downloads are blocked in this container, so no real model was run.
`offline/local_agent.py` is tested end-to-end against a scripted fake OpenAI-compatible server (6 tests: tool loop,
lesson injection, guard, path containment, shell errors, the runaway-loop cap), not against a real model.
