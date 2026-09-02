# Architecture

The V1 architecture is frozen in the [Software Design Document](SOFTWARE_DESIGN_DOCUMENT.md) and [final freeze review](ARCHITECTURE_FREEZE_REVIEW.md). Milestone 0 implements only dependency boundaries: web, API, worker, contracts, policy, document core, and AI provider abstractions.

The API is a modular FastAPI service, long-running work belongs to the worker, and all future AI calls must cross the provider-neutral `AIProvider` interface after Privacy Engine gating.
