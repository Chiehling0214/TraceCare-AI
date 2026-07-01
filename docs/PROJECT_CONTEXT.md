# TraceCare AI Project Context

## Project Purpose

TraceCare AI is a local clinical data integration and decision-support
competition prototype.

The system converts synthetic clinical data into traceable events,
runs deterministic rules, displays supporting evidence, and tracks
whether an event has been acknowledged or resolved.

## Core Principles

1. Evidence first
2. Deterministic calculations before LLM generation
3. Every event must be traceable to source data
4. Human confirmation is required
5. Local processing only
6. Synthetic data only during the prototype stage

## Current Scope

- Synthetic patients
- Structured laboratory results
- Clinical events
- Evidence links
- Deterministic trend analysis
- Event acknowledgement and resolution
- Simulated device state

## Out of Scope

- Medical diagnosis
- Treatment recommendations
- Real patient data
- Real hospital integration
- FHIR implementation
- Local LLM
- RAG
- Vector database
- Real ESP32 connection
- ECG or PPG processing

## Safety Statement

This project is a competition prototype and is not a medical device.
It must not be used for diagnosis or treatment decisions.