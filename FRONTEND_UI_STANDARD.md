# Frontend UI Standard

This standard applies to all new React web interface work in AIbrief. The current public site is static generated HTML, but any future React surface must follow these rules.

Architecture decision record: `docs/adr/0001-frontend-ui-foundation.md`.

## Component Foundation

1. Use `@base-ui/react` as the default component foundation for React web interfaces.
2. Do not install the deprecated `@base-ui-components/react` package.
3. Import components through component-specific entry points.
4. Keep Base UI unstyled and apply the project's existing Tailwind CSS, CSS Modules, or CSS-in-JS layer.
5. Build shared wrappers under `src/components/ui/`.

## Accessibility And Behavior

1. Preserve Base UI keyboard navigation, focus management, ARIA attributes, and semantic roles.
2. Do not replace Base UI behavior with custom implementations unless a documented requirement cannot be met.
3. Do not mix Radix UI, Headless UI, Material UI, or another primitive library into new code without an architecture decision record.
4. Existing components may be migrated incrementally when modified.

## Handoff Checks

Run the relevant checks before handoff for React UI changes:

1. Accessibility checks.
2. Keyboard-navigation checks.
3. Type-checking.
4. UI regression tests.

If a check cannot run in the current environment, document the exact blocker in the handoff.
