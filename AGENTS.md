# Frontend design contract

## Approved UI baseline — locked

The visible Aibrief interface at Git commit `4fb5958` is the permanently approved UI baseline.
Do not change its navigation, information architecture, section order, layout, proportions,
responsive behavior, typography, palette, spacing, borders, cards, tables, controls, labels,
logo, signal bar, or interaction patterns.

Future visible work is restricted to these three surfaces only:

1. the news types or categories supplied by real data;
2. the editorial images displayed in the existing image slots;
3. the content and behavior of the existing pointer/focus popup.

An instruction that does not explicitly name one of those three surfaces is not authorization to
edit the UI. Preserve all other rendered output byte-for-byte where practical. Never interpret a
data, backend, maintenance, dependency, accessibility, or content task as permission to restyle or
recompose the interface. The exact approved baseline can be restored from the Git tag
`approved-ui-2026-09-29`.

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
