---
version: "alpha"
name: "AibriefAI"
description: "Canonical design contract for an intelligence product. Copy this file to any AI-generated project and replace the project profile, tokens, and component rules before redesign work."
colors:
  primary: "#0B1520"
  secondary: "#44515C"
  tertiary: "#C94B3C"
  neutral: "#F3F0E8"
  surface: "#FFFFFF"
  surface-subtle: "#E9E6DE"
  text: "#0B1520"
  text-muted: "#5D6872"
  border: "#C9C4BA"
  accent: "#007C83"
  success: "#1E6B50"
  warning: "#8A5300"
  danger: "#B42318"
  on-primary: "#FFFFFF"
  on-tertiary: "#FFFFFF"
  on-accent: "#FFFFFF"
  on-status: "#FFFFFF"
typography:
  display:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "3.75rem"
    fontWeight: "600"
    lineHeight: "1.02"
    letterSpacing: "-0.03em"
  h1:
    fontFamily: "Source Sans 3, Segoe UI, sans-serif"
    fontSize: "2.5rem"
    fontWeight: "650"
    lineHeight: "1.08"
    letterSpacing: "-0.02em"
  h2:
    fontFamily: "Source Sans 3, Segoe UI, sans-serif"
    fontSize: "1.75rem"
    fontWeight: "650"
    lineHeight: "1.15"
    letterSpacing: "-0.015em"
  h3:
    fontFamily: "Source Sans 3, Segoe UI, sans-serif"
    fontSize: "1.25rem"
    fontWeight: "650"
    lineHeight: "1.2"
  body-lg:
    fontFamily: "Source Sans 3, Segoe UI, sans-serif"
    fontSize: "1.125rem"
    fontWeight: "400"
    lineHeight: "1.55"
  body-md:
    fontFamily: "Source Sans 3, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: "400"
    lineHeight: "1.5"
  body-sm:
    fontFamily: "Source Sans 3, Segoe UI, sans-serif"
    fontSize: "0.875rem"
    fontWeight: "400"
    lineHeight: "1.45"
  label:
    fontFamily: "Source Sans 3, Segoe UI, sans-serif"
    fontSize: "0.75rem"
    fontWeight: "650"
    lineHeight: "1.2"
    letterSpacing: "0.045em"
  data:
    fontFamily: "IBM Plex Mono, Consolas, monospace"
    fontSize: "0.8125rem"
    fontWeight: "500"
    lineHeight: "1.35"
    letterSpacing: "0em"
rounded:
  none: "0px"
  xs: "2px"
  sm: "4px"
  md: "8px"
  lg: "12px"
  pill: "999px"
spacing:
  0: "0px"
  1: "4px"
  2: "8px"
  3: "12px"
  4: "16px"
  5: "20px"
  6: "24px"
  8: "32px"
  10: "40px"
  12: "48px"
  16: "64px"
  20: "80px"
  24: "96px"
components:
  page:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.text}"
    typography: "{typography.body-md}"
    rounded: "{rounded.none}"
    padding: "0px"
  surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.body-md}"
    rounded: "{rounded.sm}"
    padding: "16px"
  surface-subtle:
    backgroundColor: "{colors.surface-subtle}"
    textColor: "{colors.text}"
    typography: "{typography.body-md}"
    rounded: "{rounded.sm}"
    padding: "16px"
  navigation:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "12px"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "12px"
    height: "40px"
  button-primary-hover:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "12px"
    height: "40px"
  button-accent:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "12px"
    height: "40px"
  alert-critical:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-status}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "8px"
  alert-warning:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.on-status}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "8px"
  status-success:
    backgroundColor: "{colors.success}"
    textColor: "{colors.on-status}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "8px"
  editorial-accent:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-tertiary}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "8px"
  metadata:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.text-muted}"
    typography: "{typography.data}"
    rounded: "{rounded.none}"
    padding: "4px"
  divider:
    backgroundColor: "{colors.border}"
    textColor: "{colors.secondary}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.none}"
    height: "1px"
    padding: "0px"
x-project:
  id: "aibriefai"
  productType: "intelligence-platform"
  operatingMode: "redesign"
  baseline: "existing-production-ui"
  visualWorld: "intelligence operations desk + investigative newsroom + restrained Miami context"
  primaryUserTask: "detect, understand, verify, connect, and act on signals"
  aiTemplatePolicy: "reject-generic-ai-patterns"
  implementationPolicy: "DESIGN.md-is-canonical"
x-governance:
  authority: "DESIGN.md controls visible design decisions unless an explicit product requirement overrides it."
  readBeforeUiWork: true
  updateDesignAndImplementationTogether: true
  requireDiffReview: true
  requireResponsiveReview: true
  requireAccessibilityReview: true
  requireVisualRegressionReview: true
---

## Overview

### Purpose

`DESIGN.md` is the canonical design contract for this project.

It exists to prevent coding agents from inventing a new visual language on every task, importing generic AI/SaaS patterns, or changing the interface without a product reason.

The YAML front matter contains exact design tokens. The Markdown body explains how those tokens must be applied. When they conflict, token values are exact; prose controls intent, hierarchy, composition, and usage.

### Reuse in another project

Copy this file to the root of the new project as `DESIGN.md`.

Before implementation, replace:

1. `name` and `description`.
2. `x-project` values.
3. Color tokens.
4. Typography tokens.
5. Radius and spacing scales if needed.
6. Component tokens.
7. The project profile below.
8. Product-specific component rules.
9. Do's and Don'ts.

Do not copy AibriefAI's visual world into an unrelated product. The structure is reusable; the identity is not.

### Design authority

For any UI task, an agent must use this order of authority:

1. Explicit user requirement for the current task.
2. Product behavior and accessibility requirements.
3. `DESIGN.md`.
4. Existing validated UI patterns.
5. Framework or component-library defaults.
6. Agent preference.

Agent preference is never sufficient reason to introduce a new visual pattern.

### Operating modes

The current mode is defined in `x-project.operatingMode`.

**preserve**

Use when the current design is approved. Change only what the task requires. New elements must reuse existing patterns and tokens.

**evolve**

Use when the structure is retained but the visual system is being improved. Replace inconsistencies gradually and document any new token or component rule here.

**redesign**

Use when the visible UI should converge to this file. Existing implementation is evidence, not authority. Preserve functionality and information architecture unless the task explicitly changes them.

A redesign does not permit arbitrary invention. Every visible decision must trace to this file or an explicit requirement.

### Project profile — AibriefAI

AibriefAI is an intelligence workspace, not an AI marketing site.

The interface should feel like a working environment for signals, events, entities, evidence, geography, chronology, confidence, and action.

The visual reference is:

**intelligence operations desk + investigative newsroom + restrained Miami context**

Miami is environmental context, not a decorative theme. Use it through light, climate, map/geographic references, imagery, or selected accent behavior when relevant. Do not turn the interface into a tourism motif.

AI operates behind the product. AI is not the visual theme.

### Primary user sequence

Design around this sequence:

**Signal → Context → Evidence → Relationship → Confidence → Action**

Every major screen should help the user move through one or more parts of that sequence.

### Information hierarchy

Use this order when multiple information types compete:

1. Threat, anomaly, change, or time-sensitive signal.
2. What happened.
3. Why it matters.
4. Evidence and source confidence.
5. Affected entity, asset, place, or topic.
6. Time and sequence.
7. Related signals and relationships.
8. Available action.
9. Secondary metadata.

Do not give all information equal visual weight.

### Anti-AI-template objective

The interface must not look like a generic site generated from a prompt such as "modern AI SaaS dashboard."

Do not use visual conventions merely because they are common in generated interfaces. Each pattern must have a product reason.

The following are warning signs when they appear without a documented reason:

- centered hero with large gradient headline;
- purple/blue glow as the default AI signal;
- glass panels;
- floating orbs, neural meshes, sparkles, robots, brains, or abstract AI waves;
- three identical feature cards;
- every section enclosed inside a rounded card;
- large empty whitespace used to imply value;
- repeated statistic tiles with no operational purpose;
- fake graphs, fake activity, fake customers, fake testimonials, or fake data;
- identical card layouts for unrelated information types;
- excessive pill controls;
- excessive rounded corners;
- generic "AI-powered" labels used as decoration;
- animation without state or information meaning;
- default use of Inter or a similar neutral UI font without an identity reason;
- decorative gradients where flat hierarchy would communicate more clearly.

### Product-derived design rule

Before designing a page, answer internally:

1. What is the user's primary task here?
2. What must be noticed first?
3. What information needs comparison?
4. What information needs chronology?
5. What information needs evidence?
6. What action follows?
7. Which existing component already expresses this role?
8. What should remain visually quiet?

If these questions do not change the composition, the page is probably being designed from a template rather than from the product.

### Design change protocol

A visible design change must follow this sequence:

1. Read `DESIGN.md`.
2. Inspect the current implementation.
3. Identify the product task and current inconsistency.
4. Reuse an existing token or component where possible.
5. If a new visual rule is required, add it to `DESIGN.md` first or in the same change.
6. Implement the change.
7. Review desktop and mobile behavior.
8. Check keyboard, focus, contrast, zoom, and reduced-motion behavior where applicable.
9. Compare the implementation against this file.
10. Review the Git diff before commit.

Never silently create a second design system inside component-level CSS.

## Colors

### Palette role

Color communicates hierarchy, state, confidence, or action. It is not used to make the interface look "AI-like."

For AibriefAI:

- `primary` is the main ink and navigation foundation.
- `neutral` is the page field.
- `surface` is used when a bounded information surface is needed.
- `tertiary` is an editorial/action accent, not a global decoration.
- `accent` is used for interaction, selection, links, and focused intelligence states.
- `danger`, `warning`, and `success` represent status only.
- `secondary` and `text-muted` carry supporting information.
- `border` separates information when spacing alone is insufficient.

### Color discipline

Use one accent role per local composition.

Do not combine `tertiary`, `accent`, and status colors merely to increase visual activity.

Do not color-code information unless the meaning remains understandable without color.

Do not invent one-off hex values in components. Add a token here if a new semantic color is required.

### Dark mode

Do not auto-generate a dark theme by inverting this palette.

If dark mode becomes a requirement, define a complete semantic dark palette and verify contrast and hierarchy independently.

## Typography

### Type system

AibriefAI uses three roles:

- **Editorial display:** `Source Serif 4` for selected high-level narrative moments, not routine controls.
- **Interface:** `Source Sans 3` for headings, body text, navigation, and actions.
- **Data:** `IBM Plex Mono` for timestamps, identifiers, confidence values, source labels, hashes, technical metadata, and compact data rows.

This separation helps distinguish narrative, interface, and evidence.

### Typography rules

Do not use display typography for routine dashboard content.

Do not use monospace merely to appear technical. Use it when the content behaves like data.

Do not use more than three font families.

Do not introduce a new font for a single component.

Do not reduce body text below readable interface sizes to force more content into a layout. Increase information density through structure first.

### Headline behavior

Operational screens should use short headings and information-first labels.

Marketing-sized headlines belong only on pages whose job is introduction or positioning.

Do not place oversized centered headings above every product view.

## Layout

### Layout principle

Composition follows information relationships, not a default card grid.

Use the page structure that best fits the task:

- timeline for sequence;
- table for comparison;
- split view for source + analysis;
- map for geography;
- graph for relationships;
- feed for incoming signals;
- detail rail for metadata;
- workspace for investigation;
- card only when information forms a bounded unit.

### Grid

Use a 12-column page grid for wide screens when a grid is useful. Do not force all pages into equal columns.

Preferred content behavior:

- primary work area: 7–9 columns;
- supporting rail: 3–5 columns;
- full-width evidence or timeline: 12 columns;
- reading width for prose: approximately 60–75 characters per line.

### Density

AibriefAI is allowed to be information-dense.

Density is controlled through grouping, alignment, typography, separators, and progressive disclosure rather than large empty zones.

Do not confuse whitespace with usability. Use enough space to separate meaning, not to simulate a marketing aesthetic.

### Spacing

Use the spacing scale in the front matter.

Use smaller steps inside components and larger steps between semantic regions.

Typical guidance:

- 4–8px: tightly related data;
- 12–16px: controls and component internals;
- 20–32px: component groups;
- 40–64px: page regions;
- 80px and above: only where the composition requires a major break.

Do not invent `13px`, `27px`, `37px`, or similar one-off spacing unless a rendering constraint requires it.

### Alignment

Prefer strong shared edges.

Metadata, timestamps, confidence labels, identifiers, and values should align predictably.

Intentional asymmetry is permitted when it expresses hierarchy. Accidental misalignment is not.

### Responsive behavior

Responsive design must preserve task priority, not merely stack desktop columns.

When reducing width:

1. Keep primary information visible.
2. Move secondary metadata into a disclosure or lower section.
3. Convert side rails into drawers or inline detail sections.
4. Preserve action access.
5. Preserve evidence/source context.
6. Avoid horizontal scrolling except for content that inherently requires it, such as wide data tables.

Mobile is a distinct composition, not a shrunken desktop.

## Elevation & Depth

### Depth principle

Depth represents interaction hierarchy or temporary layering.

Use shadows for:

- menus;
- popovers;
- modals;
- draggable/floating surfaces;
- elements physically layered above the work surface.

Do not add shadows to every card.

Static information regions should normally use spacing, border, tonal separation, or typography before shadow.

### Glass and glow

Glassmorphism and glow are prohibited by default.

They may be introduced only when the project profile explicitly requires them and their functional role is documented here.

A status should not glow merely because it is generated or analyzed by AI.

### Overlay behavior

Popovers must appear close to the initiating element, preserve context, and dismiss predictably.

Hover may reveal supplementary information on pointer devices, but essential information and actions must remain reachable without hover.

## Shapes

### Shape principle

Shape communicates component role.

A single radius must not be applied indiscriminately to navigation, cards, inputs, tags, dialogs, charts, and data regions.

### Radius usage

- `none`: structural regions, separators, full-width bars, data-heavy areas.
- `xs`: alerts, labels, data markers.
- `sm`: buttons, inputs, standard surfaces.
- `md`: dialogs or grouped surfaces that need stronger separation.
- `lg`: rare; reserved for a composition that explicitly calls for a softer container.
- `pill`: compact status or filter tokens only.

Do not convert large content regions into pills or heavily rounded containers.

### Borders

Use borders to communicate containment, selection, table structure, or state.

Do not add borders around every element. If spacing and background already establish the relationship, another box is unnecessary.

## Components

### Component governance

Before creating a component, search the project for an existing component serving the same semantic role.

Create a new component only if at least one is true:

- interaction is different;
- information hierarchy is different;
- state model is different;
- responsive behavior is different;
- accessibility behavior is different;
- repeated use justifies a reusable abstraction.

Visual variation alone is not enough reason to fork a component.

### Navigation

Navigation should communicate location and available transitions.

AibriefAI navigation should behave like a workspace, not a marketing header.

Avoid oversized logos, repeated call-to-action buttons, decorative gradients, or large empty header areas inside authenticated/operational views.

Selected navigation state must be distinguishable without relying only on color.

### Intelligence navigation / tabs

Tabs represent peer views of the same work context.

Use them when users need to switch between related views without losing context.

Do not use tabs as decorative category labels.

For many categories, prefer searchable navigation, grouped filters, or a secondary rail instead of a long tab strip.

### Signal row

A signal row should make these fields scannable where available:

- time;
- severity/importance;
- entity or topic;
- event summary;
- source/confidence;
- status;
- next action.

Do not wrap every signal in a large card. Dense feeds should primarily behave as rows or structured blocks.

### Alert

Alerts communicate change requiring attention.

Use status color sparingly and locally. The whole page should not become red/orange because one item is critical.

An alert should show:

- what changed;
- when;
- scope;
- confidence or verification state;
- available action.

### Evidence block

Evidence is visually distinct from generated analysis.

Evidence blocks should preserve source, timestamp, origin, and verification state when available.

Never style generated interpretation so that it can be mistaken for source evidence.

### Confidence indicator

Confidence must include text or a value, not only color.

If confidence derives from a model or heuristic, the UI should expose the meaning of the scale when needed.

Do not use confidence as decorative certainty.

### Entity panel

Entity panels organize identity, attributes, relationships, recent events, and actions.

Do not duplicate the same entity metadata across multiple cards on the same screen.

### Timeline

Timeline is preferred when sequence changes interpretation.

Show time at a consistent edge. Distinguish confirmed events, claims, analysis, and system actions when applicable.

### Relationship view

Relationship diagrams require a question. Do not render a network graph merely because the data has entities and edges.

Provide filters, labels, and a path to supporting evidence.

### Map

Map views are for spatial questions.

Do not use a map as background decoration.

Map overlays must have a legend and should not hide uncertainty.

### Cards

A card is a semantic container, not the default page primitive.

Use a card when its contents form an independent unit that can be understood, moved, compared, selected, or acted on as a unit.

Do not create card-inside-card-inside-card structures.

Do not use the same card template for alerts, evidence, profiles, metrics, and actions.

### Metrics

Metrics require context.

A number should have a label, unit where applicable, comparison or trend where useful, and timeframe when relevant.

Do not create decorative KPI tiles with invented values.

### Charts

A chart must answer a defined question better than text or a table.

Axes, units, timeframe, source, and state must remain interpretable.

Do not use smooth curves, gradients, or animated pulses only to make a chart appear advanced.

### Tables

Use tables for comparison and scanning across consistent fields.

Support sorting/filtering only when users need them.

Keep column labels explicit. Preserve identifiers and units. Use sticky headers for long tables where appropriate.

### Buttons

Primary action count should normally be one per local decision region.

Buttons describe actions with verbs.

Do not turn every link into a button.

Do not use pill buttons by default.

### Inputs

Inputs require visible labels unless the surrounding context makes the field purpose persistent and unambiguous.

Placeholder text does not replace a label.

Validation should explain the problem and recovery path.

### Search

Search is an operational control, not a decorative hero element.

For intelligence products, search may support entities, signals, sources, time ranges, identifiers, and natural-language queries, but the UI should clarify scope.

### Filters

Filters should reflect actual data dimensions.

Do not create a row of pills simply because a generated design expects filters.

Active filters must remain visible and removable.

### Badges and status

Badges represent compact state or category.

Do not badge ordinary text.

Avoid multiple adjacent badges that encode information better represented as a structured row.

### Popovers and hover panels

A hover panel may reveal supporting context before navigation.

For AibriefAI, hover can reveal source confidence, summary, entity context, or recent state without requiring a click.

Do not hide required actions behind hover.

Popover position must not cover the information the user is comparing unless no alternative exists.

### Modals

Use a modal for a bounded task requiring temporary focus.

Do not use a modal for ordinary navigation or large investigative workflows.

### Empty states

Empty states explain:

- what is absent;
- why it may be absent;
- what action is available.

Do not fill empty states with generic AI illustrations.

### Loading states

Use skeletons only when they mirror the final content structure.

Use progress text for operations with meaningful stages.

Do not create fake activity indicators that imply work when none is occurring.

### Errors

Errors state what failed, impact, and recovery action where known.

Do not blame the user.

Preserve technical details behind expandable diagnostics when they are useful to operators.

### Icons

Icons supplement text and state. They do not replace unclear language.

Use one icon system per project unless a documented exception exists.

Avoid sparkles, magic-wand icons, brains, robots, neural nodes, or stars as generic shorthand for AI.

### Imagery

Imagery must belong to the product world.

For AibriefAI, acceptable uses include geography, source imagery, event imagery, evidence, location context, and selected Miami environmental references.

Avoid generic stock images of servers, humanoid robots, glowing brains, matrix code, or abstract digital waves unless the content itself concerns them.

### Motion

Motion communicates:

- state transition;
- spatial relationship;
- confirmation;
- loading/progress;
- entry/exit of temporary surfaces.

Do not animate content to make the interface appear intelligent.

Respect `prefers-reduced-motion`.

### Focus

Every interactive element must expose a visible keyboard focus state.

Do not remove outlines unless an equivalent focus indicator is supplied.

### Content

Interface copy should name the object, state, evidence, and action directly.

Avoid generic phrases such as:

- Unlock the power of AI.
- Supercharge your workflow.
- Reimagine the future.
- AI-powered insights at your fingertips.
- Transform your business with intelligence.

Product copy should describe what the system actually does.

## Do's and Don'ts

### Do

- Read this file before changing visible UI.
- Design from the user's task and information structure.
- Reuse semantic tokens.
- Reuse components by role, not appearance alone.
- Keep evidence distinct from interpretation.
- Use typography to establish hierarchy before adding containers.
- Use separators and alignment for dense information.
- Use status colors only for states with defined meaning.
- Allow information density where the task requires comparison or monitoring.
- Use progressive disclosure for secondary detail.
- Preserve source, timestamp, confidence, and provenance when they affect interpretation.
- Make desktop and mobile deliberate compositions.
- Make hover behavior supplementary, never mandatory.
- Verify keyboard access.
- Verify focus states.
- Verify contrast.
- Verify zoom and text reflow.
- Review responsive breakpoints.
- Review the final UI against this file before commit.
- Update this file when a new permanent visual rule is introduced.

### Don't

- Do not start from a generic AI dashboard template.
- Do not use purple/blue gradients as shorthand for AI.
- Do not use gradient text by default.
- Do not use glassmorphism by default.
- Do not use glow by default.
- Do not use decorative particle backgrounds.
- Do not use AI sparkles as a universal icon.
- Do not use robot/brain/neural imagery as product identity.
- Do not create a centered marketing hero inside an operational workspace.
- Do not create a three-card feature grid by habit.
- Do not place every section in a rounded card.
- Do not nest cards without a semantic need.
- Do not round every corner with the same large radius.
- Do not turn every metadata item into a pill.
- Do not create fake metrics or charts.
- Do not invent user activity or customer logos.
- Do not add animation without state meaning.
- Do not use oversized whitespace to hide weak hierarchy.
- Do not introduce one-off colors.
- Do not introduce one-off spacing without reason.
- Do not introduce a new font for one component.
- Do not create duplicate components that serve the same semantic role.
- Do not hide essential information behind hover.
- Do not change information architecture merely to match a visual trend.
- Do not change approved product behavior during a design-only task.
- Do not redesign unrelated screens while implementing a local feature.
- Do not silently change this file to justify an implementation already made.

### AI-agent execution contract

When an agent receives a frontend task, it must follow this contract:

1. Read `DESIGN.md` before editing frontend files.
2. State internally which operating mode applies: preserve, evolve, or redesign.
3. Inspect existing components and tokens before creating new ones.
4. Identify any generic AI-template pattern affected by the task.
5. Implement using this file as the visual authority.
6. Do not change unrelated functionality.
7. Run available lint, tests, and build checks.
8. Review the diff.
9. Review responsive behavior.
10. Review accessibility behavior.
11. Compare the result to `DESIGN.md`.
12. If a permanent new design rule was introduced, update this file in the same change.

### Full redesign contract

When `x-project.operatingMode` is `redesign`, the agent must audit the current project before changing it.

Classify each existing pattern as:

- **KEEP** — consistent with product task and this file.
- **REFINE** — useful pattern with inconsistent execution.
- **REPLACE** — generic, duplicated, inaccessible, or inconsistent pattern.
- **REMOVE** — decoration or UI with no product function.

The redesign sequence is:

1. Inventory pages and components.
2. Inventory colors, typography, spacing, radius, shadows, icons, and motion.
3. Identify duplicate and one-off values.
4. Identify AI-template patterns.
5. Map existing UI to the target tokens and components in this file.
6. Correct global primitives first.
7. Correct navigation and layout second.
8. Correct reusable components third.
9. Correct page-specific compositions last.
10. Verify no functionality or data state was lost.
11. Verify responsive behavior.
12. Verify accessibility.
13. Remove obsolete CSS/components only after replacement is proven.

### New-project bootstrap contract

For a newly generated project:

1. Do not generate the final UI until the project profile in this file is filled.
2. Define the product type, primary user, primary task, information hierarchy, visual world, and prohibited patterns.
3. Replace the default tokens.
4. Define the minimum reusable components required by the product.
5. Generate one representative screen first.
6. Review whether it resembles a generic AI/SaaS template.
7. If it does, correct `DESIGN.md` before generating the rest of the product.
8. Expand the system only after the representative screen passes review.

### Validation

Use the Google DESIGN.md CLI to validate the file structure and token references.

Cross-platform:

```bash
npx -p @google/design.md designmd lint DESIGN.md
```

If installed as a development dependency:

```json
{
  "scripts": {
    "design:lint": "designmd lint DESIGN.md"
  }
}
```

Compare design-system changes:

```bash
npx -p @google/design.md designmd diff DESIGN-before.md DESIGN.md
```

Export tokens when needed:

```bash
npx -p @google/design.md designmd export --format css-tailwind DESIGN.md > theme.css
npx -p @google/design.md designmd export --format json-tailwind DESIGN.md > tailwind.theme.json
npx -p @google/design.md designmd export --format dtcg DESIGN.md > tokens.json
```

### Definition of done

A UI change is complete only when:

- the requested behavior works;
- the visible result follows `DESIGN.md`;
- no unsupported design token was introduced;
- no duplicate component was created without reason;
- desktop and mobile were reviewed;
- focus and keyboard behavior were reviewed where relevant;
- contrast was reviewed where relevant;
- loading, empty, error, and active states remain coherent where relevant;
- the design lint has no errors;
- the implementation diff was reviewed;
- permanent design changes are reflected in this file.
