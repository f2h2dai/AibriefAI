# Frontend design contract

Read `DESIGN.md` before making any frontend change. `DESIGN.md` is the canonical visual design
contract, and its `x-project.operatingMode` controls the scope of visual change.

Audit the affected interface against `DESIGN.md` before editing. For redesign work, classify each
existing pattern as KEEP, REFINE, REPLACE, or REMOVE. Work from global primitives to navigation and
layout, then reusable components, then pages.

Do not introduce colors, typography, spacing, shapes, components, gradients, shadows, animation,
imagery, or generic AI-interface patterns that conflict with `DESIGN.md`. When a permanent design
decision changes, update `DESIGN.md` in the same commit.

Preserve application functionality, accessibility, source links, evidence semantics, and data
behavior unless the task explicitly requires a functional change. Run the evidence UI tests and
desktop/mobile browser QA for frontend changes.
