# Contributing

1. Keep the standard-library-only runtime dependency policy unless a dependency has a clear, measured benefit.
2. Add correctness tests before changing distance or candidate-selection logic.
3. For performance claims, include the command, corpus size, query set, runtime version, and machine details.
4. Compare result sets with the baseline, not just elapsed time.
5. Avoid claiming a speedup from one machine's benchmark as a universal guarantee.
6. Open an issue with a minimal reproduction for unexpected ranking or Unicode behavior.
