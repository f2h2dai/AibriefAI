# ADR 0001: Frontend UI Foundation

## Status

Accepted

## Context

AIbrief currently ships a static generated command center from `web/`. If the project adds or migrates React interfaces, shared interactive components need one primitive foundation so keyboard behavior, focus management, ARIA attributes, and semantic roles remain consistent.

## Decision

Use `@base-ui/react` as the default primitive foundation for new React web interfaces.

Shared React UI wrappers must live under `src/components/ui/`, import Base UI through component-specific entry points, and keep Base UI unstyled. Project styling should remain in the existing Tailwind CSS, CSS Modules, or CSS-in-JS layer chosen for that React surface.

Do not install `@base-ui-components/react`; it is the deprecated package name.

Do not add Radix UI, Headless UI, Material UI, or another primitive component library to new code without a separate architecture decision record that explains why Base UI cannot meet the requirement.

## Consequences

New React UI work starts from the shared wrapper layer instead of importing primitives directly throughout feature code.

Accessibility behavior supplied by Base UI should be preserved unless a documented product requirement cannot be met by the primitive.

Existing static HTML output can remain unchanged until it is migrated or touched for React work.
