# Component Guidelines

> How components are built in this project.

---

## Overview

<!--
Document your project's component conventions here.

Questions to answer:
- What component patterns do you use?
- How are props defined?
- How do you handle composition?
- What accessibility standards apply?
-->

UI uses composable React components with strict typed props.
Container components stay in feature folders; shared UI primitives stay in `components/common`.

---

## Component Structure

<!-- Standard structure of a component file -->

- One component per file with colocated subcomponents only when tightly coupled.
- Prefer presentational + container split for complex pages.
- Keep business logic in hooks/services, not in JSX trees.

---

## Props Conventions

<!-- How props should be defined and typed -->

- Define explicit `Props` interface/type for every exported component.
- Prefer narrow prop contracts over passing large model objects.
- Use callback props for side effects (`onSubmit`, `onRetry`, `onDelete`).

---

## Styling Patterns

<!-- How styles are applied (CSS modules, styled-components, Tailwind, etc.) -->

- Preferred baseline: Ant Design component system for data-heavy pages.
- Keep custom styling token-driven (theme variables) to support dark mode.
- Avoid hardcoded spacing/color values repeated across pages.

---

## Accessibility

<!-- A11y requirements and patterns -->

- Use semantic HTML and accessible labels for form fields.
- Interactive controls must be keyboard reachable.
- Tables and charts need textual fallback summaries where practical.
- Error and empty states must be visible and screen-reader friendly.

---

## Common Mistakes

<!-- Component-related mistakes your team has made -->

- Fetching data directly in deeply nested presentational components.
- Passing `any`-typed props to bypass compile checks.
- Re-implementing existing common table/form wrappers per feature.
- Hiding actionable failures behind generic "something went wrong" text.
