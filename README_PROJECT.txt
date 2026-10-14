MAIZE AI/ML DIGITALIZATION PROJECT
=================================

Purpose
-------
This project folder consolidates the work completed so far for digitizing maize research PDFs and preparing the data for downstream analysis and ML/AI work.

Folder order / pipeline
-----------------------
00_SOURCE_DOCUMENTS
    The four source PDFs used for this project, renamed descriptively, plus a mapping manifest to their original runtime filenames.

01_DIGITIZATION
    Document-specific digitization outputs and intermediate/source-extraction artifacts:
    - TLB_Rabi_2022_23
    - SDM_Rabi_2022_23
    - Rabi_Yield_2022_23
    - Annual_Report_2023_24
    - Working_Renders

02_MASTER_DATA
    Consolidated master datasets combining the source material into structured CSVs, including master observations, experiments, genotypes, annual-report facts, weather, Karnataka maize history, drought districts, staffing, budget/program utilization, source text and data dictionary.

03_VALIDATION
    Validation outputs, exact duplicate candidates, duplicate review, genotype-name match candidates, validation issues, summary and ML filter recommendations.

04_NORMALIZATION
    Standardized genotype/trait masters, aliases, unit conversion rules, standardized observations, normalization summary and review queue.

05_ANALYSIS_MASTER
    Analysis-ready master tables, long format, conflicts, domain-specific ML candidate datasets, inventory and summary.

06_ML_DATASETS
    ML-ready yield, TLB and SDM datasets; grouped train/validation/test splits; classification variants; multi-trait exploratory dataset; feature dictionary; leakage check; dataset summary and README.

07_STAGE_ARCHIVES
    ZIP archives generated for the individual completed stages. These are included for convenience; the folders above contain the expanded files.

Current status
-------------
Completed through ML dataset preparation.
The current ML datasets are prepared for model training, evaluation and feature engineering. Imputation/scaling/encoding should be fit on training data only. The disease datasets include exploratory linkage to pre-harvest phenotype features for the same candidate genotype and should be interpreted as exploratory unless independently validated.

Important data-quality notes
----------------------------
- The master dataset contains source-preserved values and validation flags.
- Genotype/trait alias mappings include review queues; these should be checked before treating all aliases as confirmed identical biological entries.
- Group-aware train/validation/test splits were created using candidate genotype groups to reduce genotype leakage across splits.
- Weather was not automatically joined to experiment-day records because a verified experiment-day linkage was not established.
- The source PDFs are retained in 00_SOURCE_DOCUMENTS for traceability.

================ MODELING UPDATE — 2026-09-29 ================

The modeling phase has now been added under 07_MODELING.

Important readiness finding:
The first yield-modeling run exposed a target-unit inconsistency in the prior
analysis-ready dataset. The source material uses both t/ha and kg/ha yield
formats. The corrected modeling branch therefore rebuilds grain yield directly
from raw source observations and standardizes the target to kg/ha before model
training. Statistical summary rows (C.V, C.D, General Mean, Location Mean) are
excluded from the genotype-level prediction target.

Current modeling folders:
07_MODELING/00_MODEL_READINESS_AUDIT
07_MODELING/01_YIELD_BASELINE_DIAGNOSTIC
07_MODELING/02_YIELD_BASELINE_CORRECTED

The diagnostic folder is preserved for auditability; its metrics are NOT final
project results. The corrected baseline is the active yield modeling branch.

Pending modeling stages are documented in:
07_MODELING/00_MODEL_READINESS_AUDIT/MODELING_ROADMAP.txt

High-level order:
07.0 Readiness audit -> 07.1 Yield diagnostic -> 07.2 Corrected yield baseline
-> 07.3 Disease modeling -> 07.4 PCA/clustering -> 07.5 Weather-driven disease
risk (data-dependent) -> 07.6 Explainability -> 07.7 Tuning/robust validation
-> 07.8 Model packaging/API -> 07.9 Dashboard/AI assistant.

================ AUTOMATED MODEL PIPELINE — ADDED ================

The project now contains an executable pipeline under:
08_AUTOMATED_PIPELINE

Windows entry point:
08_AUTOMATED_PIPELINE\run_pipeline.ps1

The interactive menu supports:
1 = next step
2 = previous step
3 = redo current/failed step
4 = run all remaining steps
5 = run selected step
6 = retry failed step
7 = status
8 = exit

The same stages are available from the command line with -Action next/prev/redo/all/run/retry/status.

The pipeline has nine stages: readiness, yield baseline, disease models, PCA/clustering,
weather-risk readiness, group-aware tuning, explainability, packaging, and final verification.
Each stage has its own Python file. The pipeline preserves stage outputs and writes logs.

A weather input template is supplied at:
08_AUTOMATED_PIPELINE\config\WEATHER_DISEASE_LINKED_TEMPLATE.csv

Copy/fill it as WEATHER_DISEASE_LINKED.csv only after date/location aligned disease observations are available. Step 5 will then attempt time-aware weather/disease modeling.

See 09_FINAL_PROJECT_STATUS.md for the final project state and remaining data-dependent work.
