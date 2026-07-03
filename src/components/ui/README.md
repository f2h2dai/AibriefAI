# Shared UI Wrappers

Place shared React UI wrappers in this directory when AIbrief adds or migrates React interfaces.

Rules for this layer:

1. Use `@base-ui/react` primitives.
2. Import through component-specific entry points.
3. Keep Base UI primitives unstyled.
4. Apply project styling through Tailwind CSS, CSS Modules, or the chosen CSS-in-JS layer.
5. Preserve Base UI keyboard navigation, focus management, ARIA attributes, and semantic roles.

Do not add wrappers around `@base-ui-components/react`; that package is deprecated.
