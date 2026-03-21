---
id: gene_panel_selection
name: Gene Panel Selection Workflow
description: |
  End-to-end workflow for gene panel design in scRNA-seq and spatial transcriptomics, that should be **STRICTLY** followed:
  dataset understanding + smart downsampling + train/test splits,
  algorithmic selection (HVG/DE/RF/scGeneFit/SpaPROS),
  optimal sub-panel discovery (ARI vs size),
  biological completion with a stability gate (Completion Rule), consensus scoring and completion (only if there is still room),
  and benchmarking on test splits (ARI/NMI/Silhouette + UMAP similarity).
tags: [gene-panel, selection, scrna-seq, spatial, scanpy, scverse, benchmarking, spapros, scgenefit, random-forest]
---

# Gene Panel Selection Workflow

This skill is used when you need to construct **biologically meaningful** and **algorithmically robust** gene panels. You will receive context from the `leader`agent , use this context and **STRICLTY** follow this **Gene Panel Selection Workflow** 

## Workflow Enforcement (MANDATORY)

Determine which stage of the workflow (Steps 1–5) is required for the current task,
and **STRICTLY** follow the corresponding step(s).

Once a step is entered, all its mandatory sub-steps must be executed.
No partial execution or silent degradation is allowed.



## Workdir
Always work in the workdir provided by the leader agent.

## Calling other agents
You can call other agents by using the `call_agent(agent_name, instruction)` function.

- **Call the `browser_use` agent** for information collection:
  When you encounter software or biological knowledge you are not familiar with, call `browser_use` to search the web and collect the necessary information.

- **Call the `system_manager` agent** for software environment installation:
  When you need to install software packages, call `system_manager` to install them.

- **Call the `biologist` agent** for results interpretation:
  When you plot figures, compute a panel, or have intermediate results, call `biologist` to ask for interpretations and include them in your report.

- **Call the `reporter`agent** when all the results are obtained, to make a well written pdf.

## Visual understanding
Use the `observe_images` function in the `file_manager` toolset to examine images and figures.
If a figure is not publication-quality, replot it.

## Reporting
At the end of the task, write a markdown report named:

`report_analysis.md`

The report **must** include:
- Summary
- Data (inputs, key parameters, outputs)
- Results (figures + tables)
- Key findings
- Next steps

## Large datasets
If the dataset is large, perform **smart downsampling** while preserving **all cell types**.

---

# Workflow (IMPORTANT : STRICLY FOLLOW NEEDED STEPS)

## 0. Dataset
If the user did not provide an AnnData object, retrieve and download relevant
single-cell or spatial omics datasets and to the context provided by the user from well-established public databases such as:

- Gene Expression Omnibus (GEO)
- ArrayExpress
- Human Cell Atlas (HCA)
- Single Cell Expression Atlas
- CELLxGENE Discover
- Tabula Sapiens
- Broad Institute Single Cell Portal

Prefer datasets that already provide processed count matrices
(e.g., h5ad, loom, mtx format) and associated metadata.
Convert the dataset into an AnnData object if needed.

**Else use the provided dataset of the user** 

## 1) Dataset Understanding and Splitting

Start with exploratory inspection using an **integrated notebook**.

### 1.1 Basic structure
Inspect:
- file format (h5ad or other)
- number of cells / genes
- batches / conditions
- `.obs`, `.var`, `.obsm`, `.uns`
- whether dataset has spatial or multimodal components

Checklist:
- [ ] Identify `label_key` (true cell type recommended if present)
- [ ] Identify batch/condition columns
- [ ] Confirm whether `adata.X` is raw counts or normalized/log1p

---

### 1.2 Downsampling (CRITICAL)
Rules:
- Downsample to **< 500k cells**, **preserving all cell types**
- If genes > **30000**, reduce to **<=30000** via QC/HVG for compute-heavy steps
- Save downsampled `adata` to a new file in workdir via `file_manager`

> [!IMPORTANT]
> Prefer stratified downsampling by `label_key` if available; otherwise stratify by clustering labels.

---

### 1.3 Splitting
If provided one dataset, split to preserve all cell type distribution across all datasets:
- 1 training dataset (diversified)
- several test batches (**at least 5**)
- constraint: each split **< 50k cells**
- make splits as non-redundant as possible and represent **all cell types**

---

### 1.4 Preprocessing status
Check:
- normalization
- PCA
- UMAP
- clustering

Recompute only if missing or invalid.

---

### 1.5 Preprocessing (if needed)
- QC (follow the QC skill if available)
- Normalize / log1p / scale
- PCA / neighbors / UMAP
- Batch correction (if needed)
- Leiden clustering
- DEG & marker detection
- Cell type annotation
- Marker plots (dotplots, heatmaps)

> [!IMPORTANT]
> If heavy steps are slow or unstable on notebook use python code

---

## 2) Algorithmic Gene Panel Selection 

### 2.1 Pre-established methods
Algorithmic Methods = `{HVG, DE, Random Forest, scGeneFit, SpaPROS}`

- Use true cell type as `label_key` whenever available
- Implement HVG / DE via Scanpy on code
- for more advaced methods **always Use** `gene_panel_selection_tool` toolset :
```python
from pantheon.toolsets.gene_panel_selection_tool import GenePanelToolSet

selection_tool = GenePanelToolSet(
    name="gene_panel_selection",
    default_adata_path="adapath",
    default_workdir="workdir",
)

# Advanced methods (tool calls)
# - select_scgenefit   (ALWAYS: max_constraints <= 1000)
# - select_spapros     (ALWAYS: n_hvg < 3000)
# - select_random_forest
#
# Example calls (adjust args as needed):
await selection_tool.select_scgenefit(label_key="cell_type", n_top_genes="200", max_constraints="1000")
await selection_tool.select_spapros(label_key="cell_type", num_markers="200", n_hvg="2500")
await selection_tool.select_random_forest(label_key="cell_type", n_top_genes="1000")
  ```

- Always request **gene scores**
- Save each method score table to disk (CSV)

---

## 3) Optimal SEED panel Discovery 

For **each method independently (HVG, DE, Scgenefit, RF, SpapROS)**:

Let N be the target final panel size requested by the leader 

1. Load the method-specific gene score CSV and rank genes (descending score).
2. Build candidate sub-panels of sizes K ∈ {100, 200, …, N} by taking the top-K ranked genes.
3. For each method and each K:
   - Subset the dataset to panel genes only: adata_K = adata[:, panel_genes]
   - Recompute neighbors + Leiden on adata_K (same preprocessing policy across K)
   - Compute ARI between Leiden clusters and true cell types (label_key).
4. Plot ARI vs K for each method.
5. Pick the **seed panel** = (method, K*) with the best ARI

**Note**: **SEED STEP** is performed using the training `adata`. It is **IMPORTANT** you investigate ARI vs panel size for all methods (HVG, DE, Scgenefit, RF, SpapROS) when possible, to make sure you take the best one! 

---

## 4) Curation Logic

### 4.1 Curation pipeline (STRICT ORDER)

Final panel is built in **two phases**:

#### Phase 1 — Seed-panel (algorithmic)
- Use the optimal Seed-panel identified in Step 3 as seed subpanel
- Do **not** change genes in the seed

#### Phase 2 — Completion (biological lookup is the PRIMARY mechanism)

> **CRITICAL**: Biological curation is the MAIN completion mechanism, NOT consensus fill.
> The purpose of completion is to add biologically meaningful genes that algorithmic methods may have missed.
> Consensus fill is ONLY a small last-resort gap filler. If you find yourself adding more consensus-fill genes
> than biological genes, you have NOT done enough biological lookup.

**0) Completion Rule**
Before adding a batch of genes:
- test whether it makes ARI drop considerably or become less stable (training)
- If completing the panel up to size **N** degrades performance substantially (eg ARI drop >5%), propose:
  - an optimal stable panel (< N)
  - a supplemental gene list to reach N if required
- a modest ARI drop is acceptable if it adds important biological coverage
Check this on the training dataset.

**1) Assess Seed Coverage First**
Before biological lookup, inspect genes in the seed panel:
- Map seed gene IDs to symbols
- Identify which biological categories from the leader's context are already covered
- Note which categories are MISSING or under-represented

**2) Exhaustive Biological Lookup (CRITICAL — MUST BE THOROUGH)**
Derive the relevant biological categories from the **leader-provided context** (e.g., cell type markers, signaling pathways, functional states, disease-specific genes — whatever the user's goal requires).

Call `browser_use` **MULTIPLE times**, once per major biological category identified.
For **each category**, collect **all** well-established marker genes (typically 10-30+ per category, not just 3-5).
Sources: GeneCards, GO, UniProt, KEGG, Reactome, MSigDB, published marker gene lists, review articles.

> A single browser_use call returning a handful of genes for an entire panel is INSUFFICIENT.
> The number of biologically curated genes should scale with the gap between seed size and target N.
> Do multiple rounds of lookup — breadth across ALL relevant categories AND depth within each.

**3) Add Biologically Relevant Genes**
For each candidate gene:
   - check not already in seed panel
   - ensure no redundancy
   - maintain balanced biological coverage across categories
   - categorize into a relevant biological category (from leader context, or inferred)
   - after each batch of additions, check Completion Rule (ARI stability on training)
   - if ARI drops sharply, try a different set; a modest drop for strong biological coverage is acceptable
   - continue until all important biological genes are added or panel reaches size N

**4) Consensus Fill (LAST RESORT ONLY — small gap filler)**
Only if after exhaustive biological lookup, `{seed + biological genes} < N`:
   - normalize scores per method (same scale, no method dominates)
   - aggregate into a consensus table
   - fill the small remaining gap by score priority, excluding genes already present

**Deliverable: a gene × {method where it comes from, biological category, biological function, source/reference} table.**

**Note**: Every accepted gene must be **justified**, assigned a **biological category**, and referenced with a source (seed/method score or website/literature) and a gene function description.

---

## 5) Benchmarking (MANDATORY)

### 5.0 Panel genes comparison
Create an **UpSet plot** for all **N-size** algorithmic panels to see overlap.

Use the **full original dataset** for evaluation.

### 5.1 Dataset
Benchmarking is performed on **test datasets**.

### 5.2 Metrics
For each subset compute (across test splits):
1. all algorithmic **N** size panels
2. final curated **N** size panel
3. if curated **N** was not optimal per **Completion Rule**, also benchmark the optimal stable (<N) panel
4. full gene set baseline

Compute:
- Leiden over-clustering on panel genes
- **ARI, NMI** between Leiden and true labels
- **Silhouette Index** using Leiden assignments

Plots:
- one figure per metric
- boxplots
- high-quality formatting

### 5.3 UMAP comparison
Compute UMAPs for:
- full genes (reference)
- each algorithmic **N** size panel
- final curated **N** size panel
- if needed, the optimal stable panel

Compare vs reference:
- qualitative
- quantitative (distance correlation / Procrustes-like metrics)

---

## 6) Summarizing

Report must include the full workflow (Steps 0 → 5) and at minimum, in a very well written **pdf** (ask `reporter` to make the pdf):

- **Objective & context**
- **Dataset description** (structure, labels, preprocessing status)
- **Algorithmic methods run** (HVG/DE/RF/scGeneFit/SpaPROS): what each optimizes (detailed)
- **Sub-panel selection**:
  - ARI vs size curves per method
  - UpSet plot of different panels (overlaps)
  - selection decision (method + size) and why
- **Consensus table construction**:
  - normalization choice
  - aggregation rule
  - resulting ranked list
- **Curation & completion reasoning (step-by-step)**:
  - per added gene: lookup → match to context → accept/reject
  - redundancy checks + category balance
  - **all biological references**
- **Benchmarking results**:
  - UpSet plot comparing algorithmic panels and curated panel
  - ARI/NMI/SI boxplots across test subsets
  - UMAP comparisons + quantitative similarity metric
  - interpretation of performance differences

### Tables (MANDATORY)
1) Recap table of final panel (all N genes):

| Gene | Methods where it appears | Biological Function | Relevance score |
|------|--------------------------|----------------------|-----------------|

2) Per-category count recap table based on leader context.

### Figures (MANDATORY)
The report should contain at **least** all of the following figures , and any other figures that you consider relevant:
  - ARI vs size curves per method (See above **Sub-panel selection**)
  - UpSet plot comparing algorithmic panels and curated panel (See above **Benchmarking results**)
  - ARI/NMI/SI boxplots across test subsets (See above **Benchmarking results**)
  - UMAP comparisons + quantitative similarity metric (See above **Benchmarking results**)
---

# Guidelines for integrated notebook usage

Use the `integrated_notebook` toolset to create/manage/execute notebooks.

- Keep all related code in the same notebook
- Each notebook handles one specific analysis task
- Start each notebook with a markdown cell:
  - background
  - objective
- After each code cell producing results, add a markdown cell explaining the result
- Save figures and also display them in notebook outputs

If memory becomes insufficient:
- close kernels using `manage_kernel`
- reduce compute via **stratified downsampling** (preserve all cell types) and/or split heavy operations into separate cells
- document decisions explicitly (what was checked, what was changed, why)

---

# Visualization quality gate

We expect **high-quality, publication-level figures**.

After generating a figure:
- inspect via `observe_images`
- if not good → replot

High-quality means:
- clear, readable
- labeled axes
- good color/contrast
- informative title (not too long)

If figure is not satisfactory → **replot**