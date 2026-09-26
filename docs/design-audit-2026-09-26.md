# AibriefAI design audit — 26 September 2026

## Scope

This audit compares the current static public interface in `web/` with `DESIGN.md`. It does not
change data loading, evidence policy, source links, filters, language behavior, or publishing.

## Decision hierarchy

The current page opens with a marketing-style hero and aggregate counts. The canonical task begins
with material changes, review needs, evidence, relationships, and action. The redesign should make
the intelligence queue and evidence state the first working surface; geography and brand context
support that work rather than lead it.

## Classification

| Surface or pattern | Decision | Evidence | Required direction |
| --- | --- | --- | --- |
| Evidence policy and fail-closed labels | KEEP | Verified/corroborated/unverified state is normalized in shared policy code. | Preserve semantics and direct source URLs. |
| Search, source filter, status filter | KEEP | Controls support investigation and update real local state. | Move into the primary queue toolbar with consistent control typography. |
| English/Arabic toggle | KEEP | Working interaction with native RTL text. | Apply RTL to content regions without shifting the page shell. |
| Direct source links | KEEP | Records retain canonical source destinations. | Visually separate source evidence from related reading. |
| Editorial serif plus operational sans | REFINE | Current CSS applies Georgia to many controls and dense tables. | Keep serif for judgment/headlines; move controls and tables to the sans token. |
| Hero headline and three aggregate metrics | REPLACE | The first viewport prioritizes branding and totals over actionable intelligence. | Replace with a working intelligence queue plus evidence/detail region. |
| Hero gradient overlays | REMOVE | `editorial.css` uses multiple white-to-transparent gradients over imagery. | Use natural imagery in a bounded context module or no image. |
| Uppercase hero pretitle | REMOVE | The pretitle behaves as a decorative eyebrow. | Put geography/topic context in real filters or record metadata. |
| Three equal regional columns | REPLACE | Saudi, research, and X are arranged as a generic three-column dashboard. | Use one queue with source/type facets and connected detail views. |
| Metric tiles | REPLACE | Rounded count boxes resemble generic dashboard summary cards. | Use a compact operational summary line only where counts affect action. |
| Status pills | REFINE | Status is meaningful, but pill treatment is repeated. | Use text plus a structural marker; reserve pills for compact status only. |
| Radar graphic | REPLACE | Decorative radar metaphor adds little evidence value. | Replace with provenance, relationship, or timeline information. |
| Place photography | REFINE | Riyadh/Miami imagery gives context but currently competes with analysis. | Keep one restrained, naturally colored context image below the working surface. |
| Multiple CSS layers and copied HTML pages | REPLACE | Core rules are duplicated across `index.html`, `brief.html`, and template CSS. | Establish tokens and reusable primitives before page-level redesign. |
| Glass, glow, robot/brain imagery | KEEP ABSENT | No dominant use in the inspected surface. | Continue to prohibit them. |

## Global primitive gaps

- Current CSS values are split between inline styles and `assets/editorial.css`; no single token
  source controls color, type, spacing, radius, or evidence states.
- Teal is used for interaction and editorial decoration without a consistently documented role.
- Controls inherit mixed serif and browser-adjacent typography.
- Radius and spacing values are repeated ad hoc.
- Evidence colors are not yet mapped to canonical design tokens.

## Proposed redesign sequence

1. Export `DESIGN.md` tokens and map them to CSS custom properties.
2. Rebuild the page shell and navigation without changing routes or data contracts.
3. Build reusable queue row, evidence state, provenance rail, filter, empty-state, and source-link
   primitives.
4. Replace the hero with the primary queue/detail working surface.
5. Consolidate Saudi, research, and X into facets and relationship views.
6. Move geographic imagery into one restrained context module.
7. Apply the same primitives to `index.html`, `brief.html`, and `landing-template.html`.
8. Verify English and Arabic at desktop and mobile sizes, then rerun evidence UI tests.

## Functional invariants

- Model-provided labels cannot mark a record verified.
- URL deduplication and evidence counts remain unchanged.
- Search, source/status filters, language toggle, and missing-X state remain functional.
- Direct source URLs remain accessible.
- No new production claims or fabricated metrics may be introduced.

## Acceptance gates for the redesign

- `DESIGN.md` lint reports no errors.
- Above-the-fold content starts with actionable intelligence and evidence state.
- No gradients, glass, glow, decorative pills, generic three-card grid, or AI stock imagery.
- Desktop and mobile screenshots match the accepted concept and have no horizontal overflow.
- English and Arabic flows pass visual and interaction QA.
- Existing evidence-policy tests remain green; known unrelated baseline failures are documented.
