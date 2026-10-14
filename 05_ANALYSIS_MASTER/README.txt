MAIZE ANALYSIS MASTER

This is the analytical layer created from the normalized observations.
The raw master and validated master are not modified.

MAIZE_ANALYSIS_MASTER.csv:
- one row per candidate genotype x experiment;
- experiment metadata joined from the experiment registry;
- canonical traits pivoted to columns;
- source pages/record IDs retained;
- review flags retained.

MAIZE_ANALYSIS_MASTER_LONG.csv:
- one row per observation and is the preferred audit-friendly form.

ANALYSIS_MASTER_CONFLICTS.csv:
- contains non-unique genotype x experiment x trait observations;
- conflicting cells in the wide master are left blank rather than averaged or guessed.

ML_*_CANDIDATE.csv files are starting pools, NOT final training datasets.
The next stage should build target-specific features, remove/handle target leakage, and define group-aware train/validation/test splits.
Weather has not been joined to experiments in this stage because temporal linkage requires a verified experiment date/location mapping.
