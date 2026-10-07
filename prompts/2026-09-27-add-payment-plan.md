# Add Payment Plan ? September 27, 2026

User request: implement Add Payment Plan in the existing DueMap React/TypeScript/
Vite and FastAPI branch, preserving profile and card flows. References: Stitch
project 6921387155947892246, screens 394c5bab3c614a038accd189cd42ba9c and
3b5a1980095f4b8c8b0602532e94ea0d.

Requirements and outcomes are recorded in docs/payment-plan-flow.md and
its local verification checklist. Support five fixed providers, profile-owned
card IDs, CAD/USD, existing biweekly Python calculations, paid counts, structured
validation, editable controlled form reuse, no-card guidance, immediate overview,
and an ephemeral accessible success notice. Extend JSON import/export and run
frontend/backend regression checks. No account credentials or conversion.

Decision: use existing transactional SQLite profile documents and shared Python
validation/application pipeline; do not add a second schedule calculator.
