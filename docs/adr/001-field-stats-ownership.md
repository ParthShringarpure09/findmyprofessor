# ADR 001 — FieldStats ownership

## Question

How should FindMyProfessor divide FieldStats work between M0 and M3 when the build specification assigns FieldStats to M0 but describes the large-scale computation in M3?

## Decision

M0 owns the FieldStats domain schema, database representation, and computation interface.

The empirical computation using at least 5,000 authors per top-level field is performed during M3 before field-normalised ranking is accepted.

## Reason

This preserves the dependency direction M0 → M3 while ensuring M3 receives the empirical field statistics required for ranking evaluation.

## Alternatives

1. Compute the complete production FieldStats dataset during M0.
2. Move FieldStats entirely into M3.

## Why not

Option 1 makes M0 depend on substantial academic ingestion work that formally belongs downstream.

Option 2 conflicts with the specification's assignment of the FieldStats domain model and table to M0.

## Trade-off

M0 establishes structural readiness for FieldStats before the final empirical statistics are produced during M3.

## Affected modules

- M0 Foundation
- M3 Topic → People Search
- M4 Researcher Profile Builder
- M11 Evaluation
