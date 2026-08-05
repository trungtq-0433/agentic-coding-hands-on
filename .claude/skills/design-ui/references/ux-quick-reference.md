# UX Quick Reference

Ten rule categories ordered by priority. Work 1→10 to decide which category deserves attention first; use `--domain <Domain>` to pull details when needed.

| Priority | Category | Impact | Domain | Key Checks (Must Have) | Anti-Patterns (Avoid) |
|----------|----------|--------|--------|------------------------|------------------------|
| 1 | Accessibility | CRITICAL | `ux` | Contrast 4.5:1, Alt text, Keyboard nav, Aria-labels | Removing focus rings, Icon-only buttons without labels |
| 2 | Touch & Interaction | CRITICAL | `ux` | Min size 44×44px, 8px+ spacing, Loading feedback | Reliance on hover only, Instant state changes (0ms) |
| 3 | Performance | HIGH | `ux` | WebP/AVIF, Lazy loading, Reserve space (CLS &lt; 0.1) | Layout thrashing, Cumulative Layout Shift |
| 4 | Style Selection | HIGH | `style`, `product` | Match product type, Consistency, SVG icons (no emoji) | Mixing flat & skeuomorphic randomly, Emoji as icons |
| 5 | Layout & Responsive | HIGH | `ux` | Mobile-first breakpoints, Viewport meta, No horizontal scroll | Horizontal scroll, Fixed px container widths, Disable zoom |
| 6 | Typography & Color | MEDIUM | `typography`, `color` | Base 16px, Line-height 1.5, Semantic color tokens | Text &lt; 12px body, Gray-on-gray, Raw hex in components |
| 7 | Animation | MEDIUM | `ux` | Duration 150–300ms, Motion conveys meaning, Spatial continuity | Decorative-only animation, Animating width/height, No reduced-motion |
| 8 | Forms & Feedback | MEDIUM | `ux` | Visible labels, Error near field, Helper text, Progressive disclosure | Placeholder-only label, Errors only at top, Overwhelm upfront |
| 9 | Navigation Patterns | HIGH | `ux` | Predictable back, Bottom nav ≤5, Deep linking | Overloaded nav, Broken back behavior, No deep links |
| 10 | Charts & Data | LOW | `chart` | Legends, Tooltips, Accessible colors | Relying on color alone to convey meaning |

---

### 1. Accessibility (CRITICAL)

- `color-contrast` - Hold normal text at 4.5:1 or better (large text 3:1); Material Design
- `focus-states` - Keep focus rings visible on anything interactive (2–4px; Apple HIG, MD)
- `alt-text` - Give meaningful images descriptive alt text
- `aria-labels` - aria-label on icon-only buttons; accessibilityLabel on native (Apple HIG)
- `keyboard-nav` - Tab order tracks visual order; the whole UI works from the keyboard (Apple HIG)
- `form-labels` - Pair every label with its input via the for attribute
- `skip-links` - Offer a skip-to-main-content jump for keyboard users
- `heading-hierarchy` - Step h1→h6 in order; never skip a level
- `color-not-only` - Color can't carry meaning by itself — back it with an icon or text
- `dynamic-type` - Honor system text scaling; don't let growing text get truncated (Apple Dynamic Type, MD)
- `reduced-motion` - Obey prefers-reduced-motion; cut or kill animation when it's asked for (Apple Reduced Motion API, MD)
- `voiceover-sr` - Meaningful accessibilityLabel/accessibilityHint; keep reading order logical for VoiceOver/screen readers (Apple HIG, MD)
- `escape-routes` - Always leave a cancel/back path out of modals and multi-step flows (Apple HIG)
- `keyboard-shortcuts` - Don't clobber system or a11y shortcuts; give keyboard alternatives to drag-and-drop (Apple HIG)

### 2. Touch & Interaction (CRITICAL)

- `touch-target-size` - Floor of 44×44pt (Apple) / 48×48dp (Material); stretch the hit area past the visual bounds when the glyph is small
- `touch-spacing` - Leave at least 8px/8dp between touch targets (Apple HIG, MD)
- `hover-vs-tap` - Drive primary interactions from click/tap; hover alone isn't enough
- `loading-buttons` - Disable the button while async runs; surface a spinner or progress
- `error-feedback` - Put clear error messages right next to the problem
- `cursor-pointer` - Give clickable elements cursor-pointer (Web)
- `gesture-conflicts` - Keep horizontal swipe off the main content; lean on vertical scroll
- `tap-delay` - Reach for touch-action: manipulation to shave the 300ms delay (Web)
- `standard-gestures` - Stick to the platform's standard gestures; don't redefine them (e.g. swipe-back, pinch-zoom) (Apple HIG)
- `system-gestures` - Leave system gestures alone (Control Center, back swipe, and the like) (Apple HIG)
- `press-feedback` - Show something on press — ripple or highlight (MD state layers)
- `haptic-feedback` - Save haptics for confirmations and weighty actions; don't wear them out (Apple HIG)
- `gesture-alternative` - Never make a gesture the only way in; critical actions always need a visible control
- `safe-area-awareness` - Keep primary touch targets clear of the notch, Dynamic Island, gesture bar, and screen edges
- `no-precision-required` - Don't demand pixel-perfect taps on tiny icons or thin edges
- `swipe-clarity` - A swipe action needs a clear affordance or hint — chevron, label, tutorial
- `drag-threshold` - Require a bit of movement before a drag starts, so it doesn't fire by accident

### 3. Performance (HIGH)

- `image-optimization` - Ship WebP/AVIF, responsive images (srcset/sizes), and lazy-load anything non-critical
- `image-dimension` - Set width/height or aspect-ratio up front so the layout doesn't jump (Core Web Vitals: CLS)
- `font-loading` - font-display: swap/optional keeps text from going invisible (FOIT); reserve space to hold layout steady (MD)
- `font-preload` - Preload only the fonts that matter; don't preload every variant
- `critical-css` - Get above-the-fold CSS out first (inline the critical CSS or load that stylesheet early)
- `lazy-loading` - Defer non-hero components with dynamic import / route-level splitting
- `bundle-splitting` - Carve code up by route/feature (React Suspense / Next.js dynamic) to lighten initial load and TTI
- `third-party-scripts` - Load third-party scripts async/defer; audit them and drop the dead weight (MD)
- `reduce-reflows` - Don't ping-pong layout reads and writes; batch the reads, then the writes
- `content-jumping` - Hold space for async content so the layout doesn't lurch (Core Web Vitals: CLS)
- `lazy-load-below-fold` - loading="lazy" for below-the-fold images and heavy media
- `virtualize-lists` - Virtualize any list past 50 items for memory and scroll performance
- `main-thread-budget` - Stay under ~16ms of per-frame work for 60fps; push heavy work off the main thread (HIG, MD)
- `progressive-loading` - For anything over 1s, prefer skeleton/shimmer over a long blocking spinner (Apple HIG)
- `input-latency` - Hold input latency under ~100ms on taps/scrolls (Material responsiveness standard)
- `tap-feedback-speed` - Answer a tap with something visible inside 100ms (Apple HIG)
- `debounce-throttle` - Debounce or throttle the high-frequency events (scroll, resize, input)
- `offline-support` - Say something when offline and provide a basic fallback (PWA / mobile)
- `network-fallback` - Degrade gracefully on slow networks — lower-res images, fewer animations

### 4. Style Selection (HIGH)

- `style-match` - Fit the style to the product type (`--design-system` will recommend one)
- `consistency` - Hold one style across every page
- `no-emoji-icons` - SVG icons (Heroicons, Lucide), never emojis
- `color-palette-from-product` - Pull the palette from the product/industry (search `--domain color`)
- `effects-match-style` - Keep shadows, blur, and radius in step with the chosen style (glass / flat / clay etc.)
- `platform-adaptive` - Speak the platform's idiom (iOS HIG vs Material): navigation, controls, typography, motion
- `state-clarity` - Make hover/pressed/disabled read as distinct without leaving the style (Material state layers)
- `elevation-consistent` - Run one elevation/shadow scale across cards, sheets, modals; no one-off shadow values
- `dark-mode-pairing` - Design the light and dark variants side by side so brand, contrast, and style stay aligned
- `icon-style-consistent` - One icon set and visual language (stroke width, corner radius) for the whole product
- `system-controls` - Favor native/system controls over fully custom ones; customize only when branding demands it (Apple HIG)
- `blur-purpose` - Blur signals a dismissible background (modals, sheets) — it's not decoration (Apple HIG)
- `primary-action` - One primary CTA per screen; everything secondary reads as subordinate (Apple HIG)

### 5. Layout & Responsive (HIGH)

- `viewport-meta` - width=device-width initial-scale=1 (never disable zoom)
- `mobile-first` - Start at mobile, then scale up through tablet and desktop
- `breakpoint-consistency` - Pick a systematic breakpoint set (e.g. 375 / 768 / 1024 / 1440)
- `readable-font-size` - Body text no smaller than 16px on mobile (dodges iOS auto-zoom)
- `line-length-control` - 35–60 chars per line on mobile; 60–75 on desktop
- `horizontal-scroll` - Kill horizontal scroll on mobile; content fits the viewport width
- `spacing-scale` - Step spacing on a 4pt/8dp system (Material Design)
- `touch-density` - Space components comfortably for fingers — not cramped, no mis-taps
- `container-width` - One consistent max-width on desktop (max-w-6xl / 7xl)
- `z-index-management` - Lay out a deliberate z-index scale (e.g. 0 / 10 / 20 / 40 / 100 / 1000)
- `fixed-element-offset` - A fixed navbar/bottom bar must reserve safe padding for the content beneath it
- `scroll-behavior` - Steer clear of nested scroll regions that fight the main scroll
- `viewport-units` - Reach for min-h-dvh over 100vh on mobile
- `orientation-support` - Keep the layout readable and usable in landscape
- `content-priority` - Lead with core content on mobile; fold or hide the secondary
- `visual-hierarchy` - Build hierarchy from size, spacing, and contrast — not color alone

### 6. Typography & Color (MEDIUM)

- `line-height` - Body text sits best at 1.5-1.75
- `line-length` - Cap lines at 65-75 characters
- `font-pairing` - Match the personalities of heading and body fonts
- `font-scale` - One consistent type scale (e.g. 12 14 16 18 24 32)
- `contrast-readability` - Darker text on light grounds (e.g. slate-900 on white)
- `text-styles-system` - Lean on the platform type system: iOS 11 Dynamic Type styles / Material 5 type roles (display, headline, title, body, label) (HIG, MD)
- `weight-hierarchy` - Let font-weight carry hierarchy: bold headings (600–700), regular body (400), medium labels (500) (MD)
- `color-semantic` - Name semantic color tokens (primary, secondary, error, surface, on-surface) — never raw hex in components (Material color system)
- `color-dark-mode` - Dark mode means desaturated/lighter tonal variants, not inverted colors; verify its contrast on its own (HIG, MD)
- `color-accessible-pairs` - Every foreground/background pair clears 4.5:1 (AA) or 7:1 (AAA); confirm it with a tool (WCAG, MD)
- `color-not-decorative-only` - Functional color (error red, success green) carries an icon/text too; color alone never means anything (HIG, MD)
- `truncation-strategy` - Wrap before you truncate; when you must, use an ellipsis and expose the full text via tooltip/expand (Apple HIG)
- `letter-spacing` - Keep the platform's default tracking; don't tighten body text (HIG, MD)
- `number-tabular` - Tabular/monospaced figures for data columns, prices, and timers, so widths don't shift
- `whitespace-balance` - Spend whitespace on purpose — group what belongs together, separate the sections, skip the clutter (Apple HIG)

### 7. Animation (MEDIUM)

- `duration-timing` - Micro-interactions land at 150–300ms; complex transitions ≤400ms; nothing over 500ms (MD)
- `transform-performance` - Animate transform/opacity only; leave width/height/top/left alone
- `loading-states` - Past 300ms of loading, show a skeleton or progress indicator
- `excessive-motion` - At most 1-2 key elements move per view
- `easing` - ease-out on the way in, ease-in on the way out; linear has no place in UI transitions
- `motion-meaning` - Every animation states a cause and effect — decoration alone doesn't earn the motion (Apple HIG)
- `state-transition` - State changes (hover / active / expanded / collapsed / modal) glide, they don't snap
- `continuity` - Page/screen transitions hold spatial continuity (shared element, directional slide) (Apple HIG)
- `parallax-subtle` - Parallax in small doses only; it must honor reduced-motion and never disorient (Apple HIG)
- `spring-physics` - Spring/physics curves over linear or cubic-bezier for a natural feel (Apple HIG fluid animations)
- `exit-faster-than-enter` - Exits run shorter than entrances (~60–70% of the enter duration) to feel snappy (MD motion)
- `stagger-sequence` - Stagger list/grid entrances by 30–50ms each; not all at once, not painfully slow (MD)
- `shared-element-transition` - Carry a shared element / hero transition across screens for continuity (MD, HIG)
- `interruptible` - Animations stay interruptible; a tap or gesture cancels one mid-flight at once (Apple HIG)
- `no-blocking-animation` - Input is never blocked by an animation; the UI stays live throughout (Apple HIG)
- `fade-crossfade` - Crossfade when swapping content inside the same container (MD)
- `scale-feedback` - A small scale (0.95–1.05) on press for tappable cards/buttons; spring back on release (HIG, MD)
- `gesture-feedback` - Drag, swipe, and pinch answer in real time, tracking the finger (MD Motion)
- `hierarchy-motion` - Direction encodes hierarchy: enter from below = deeper, exit upward = back (MD)
- `motion-consistency` - Share one set of duration/easing tokens everywhere so all motion keeps the same rhythm
- `opacity-threshold` - Don't let a fading element hang below opacity 0.2 — fade it out fully or keep it visible
- `modal-motion` - Modals/sheets grow from their trigger (scale+fade or slide-in) for spatial context (HIG, MD)
- `navigation-direction` - Forward animates left/up, back animates right/down — keep the direction logical (HIG)
- `layout-shift-avoid` - No animation may trigger reflow or CLS; move things with transform (MD)

### 8. Forms & Feedback (MEDIUM)

- `input-labels` - A visible label on every input (placeholders don't count)
- `error-placement` - The error sits below the field it belongs to
- `submit-feedback` - Submit moves through loading, then success or error
- `required-indicators` - Flag required fields (an asterisk, say)
- `empty-states` - When there's no content, offer a helpful message and an action
- `toast-dismiss` - Toasts clear themselves in 3-5s
- `confirmation-dialogs` - Ask before anything destructive
- `input-helper-text` - Park persistent helper text below complex inputs — not just a placeholder (Material Design)
- `disabled-states` - Disabled means reduced opacity (0.38–0.5) + a cursor change + the semantic attribute (MD)
- `progressive-disclosure` - Unfold complex options as needed; don't dump them on the user at once (Apple HIG)
- `inline-validation` - Validate on blur, not per keystroke; only show the error once they're done typing (MD)
- `input-type-keyboard` - Semantic input types (email, tel, number) summon the right mobile keyboard (HIG, MD)
- `password-toggle` - Give password fields a show/hide toggle (MD)
- `autofill-support` - Set autocomplete / textContentType so the system can autofill (HIG, MD)
- `undo-support` - Let users undo destructive or bulk actions (e.g. an "Undo delete" toast) (Apple HIG)
- `success-feedback` - Close the loop on a finished action with brief feedback — checkmark, toast, color flash (MD)
- `error-recovery` - An error message carries a way out (retry, edit, help link) (HIG, MD)
- `multi-step-progress` - Multi-step flows show a step indicator or progress bar and let you go back (MD)
- `form-autosave` - Long forms auto-save drafts so an accidental dismissal doesn't lose the work (Apple HIG)
- `sheet-dismiss-confirm` - Confirm before dismissing a sheet/modal that holds unsaved changes (Apple HIG)
- `error-clarity` - Error text names the cause and the fix — not a bare "Invalid input" (HIG, MD)
- `field-grouping` - Group related fields logically (fieldset/legend or a visual grouping) (MD)
- `read-only-distinction` - Read-only must look and read differently from disabled (MD)
- `focus-management` - On a submit error, send focus straight to the first invalid field (WCAG, MD)
- `error-summary` - With several errors, top the form with a summary that links down to each field (WCAG)
- `touch-friendly-input` - Mobile inputs stand ≥44px tall to satisfy the touch-target rule (Apple HIG)
- `destructive-emphasis` - Destructive actions wear the semantic danger color (red) and sit apart from the primary ones (HIG, MD)
- `toast-accessibility` - Toasts don't grab focus; announce them with aria-live="polite" (WCAG)
- `aria-live-errors` - Form errors live in an aria-live region or role="alert" so screen readers catch them (WCAG)
- `contrast-feedback` - Error and success colors hold a 4.5:1 contrast ratio (WCAG, MD)
- `timeout-feedback` - A request timeout shows clear feedback with a retry (MD)

### 9. Navigation Patterns (HIGH)

- `bottom-nav-limit` - Bottom nav tops out at 5 items, each with a label and icon (Material Design)
- `drawer-usage` - The drawer/sidebar is for secondary navigation, not primary actions (Material Design)
- `back-behavior` - Back must be predictable and consistent, and it keeps scroll/state (Apple HIG, MD)
- `deep-linking` - Every key screen is reachable by deep link / URL for sharing and notifications (Apple HIG, MD)
- `tab-bar-ios` - iOS: a bottom Tab Bar drives top-level navigation (Apple HIG)
- `top-app-bar-android` - Android: a Top App Bar with a navigation icon anchors the primary structure (Material Design)
- `nav-label-icon` - Nav items carry both icon and text label; icon-only nav hurts discoverability (MD)
- `nav-state-active` - The current location is highlighted (color, weight, indicator) in the nav (HIG, MD)
- `nav-hierarchy` - Keep primary nav (tabs/bottom bar) plainly separate from secondary nav (drawer/settings) (MD)
- `modal-escape` - Modals and sheets need an obvious close/dismiss; swipe-down to dismiss on mobile (Apple HIG)
- `search-accessible` - Search stays within easy reach (top bar or tab) and offers recent/suggested queries (MD)
- `breadcrumb-web` - Web: breadcrumbs help orient anyone 3+ levels deep (MD)
- `state-preservation` - Going back restores the prior scroll position, filter state, and input (HIG, MD)
- `gesture-nav-support` - Support system gesture nav (iOS swipe-back, Android predictive back) without conflict (HIG, MD)
- `tab-badge` - Badge nav items sparingly for unread/pending, and clear them once visited (HIG, MD)
- `overflow-menu` - When actions outrun the space, move them to an overflow/more menu instead of cramming (MD)
- `bottom-nav-top-level` - Bottom nav holds top-level screens only; never nest sub-navigation in it (MD)
- `adaptive-navigation` - Large screens (≥1024px) favor a sidebar; small ones use bottom/top nav (Material Adaptive)
- `back-stack-integrity` - Don't silently reset the nav stack or jump to home out of nowhere (HIG, MD)
- `navigation-consistency` - Nav stays in the same place on every page; it doesn't shift by page type
- `avoid-mixed-patterns` - Don't run Tab + Sidebar + Bottom Nav at the same hierarchy level
- `modal-vs-navigation` - Modals aren't for primary navigation flows — they snap the user's path (HIG)
- `focus-on-route-change` - After a page transition, move focus to the main content for screen-reader users (WCAG)
- `persistent-nav` - Core navigation stays reachable from deep pages; don't bury it in sub-flows (HIG, MD)
- `destructive-nav-separation` - Dangerous actions (delete account, logout) sit apart, visually and spatially, from ordinary nav items (HIG, MD)
- `empty-nav-state` - When a destination is unavailable, say why rather than quietly hiding it (MD)

### 10. Charts & Data (LOW)

- `chart-type` - Fit the chart to the data (trend → line, comparison → bar, proportion → pie/donut)
- `color-guidance` - Use accessible palettes; steer clear of red/green-only pairs for colorblind users (WCAG, MD)
- `data-table` - Pair the chart with a table for accessibility — charts alone don't read to a screen reader (WCAG)
- `pattern-texture` - Back color with patterns, textures, or shapes so data reads even without color (WCAG, MD)
- `legend-visible` - Always show the legend, near the chart, not stranded below a scroll fold (MD)
- `tooltip-on-interact` - Surface exact values via tooltips/data labels on hover (Web) or tap (mobile) (HIG, MD)
- `axis-labels` - Label axes with units and a readable scale; no truncated or rotated labels on mobile
- `responsive-chart` - Charts reflow or simplify on small screens (horizontal bar over vertical, fewer ticks)
- `empty-data-state` - With no data, show a real empty state ("No data yet" + guidance), not a blank chart (MD)
- `loading-chart` - Hold the space with a skeleton/shimmer while data loads; never show a bare axis frame
- `animation-optional` - Entrance animations honor prefers-reduced-motion; the data reads immediately regardless (HIG)
- `large-dataset` - Past 1000 points, aggregate or sample and offer drill-down rather than drawing it all (MD)
- `number-formatting` - Format numbers, dates, and currencies locale-aware on axes and labels (HIG, MD)
- `touch-target-chart` - Interactive chart elements (points, segments) get a ≥44pt tap area or grow on touch (Apple HIG)
- `no-pie-overuse` - Don't push pie/donut past 5 categories; switch to a bar chart for clarity
- `contrast-data` - Lines/bars clear ≥3:1 against the ground; data text labels clear ≥4.5:1 (WCAG)
- `legend-interactive` - Make legends clickable to toggle series visibility (MD)
- `direct-labeling` - On small datasets, label values right on the chart to cut eye travel
- `tooltip-keyboard` - Tooltip content is keyboard-reachable and doesn't lean on hover alone (WCAG)
- `sortable-table` - Data tables sort, with aria-sort calling out the current sort state (WCAG)
- `axis-readability` - Keep axis ticks from crowding; hold readable spacing and auto-skip on small screens
- `data-density` - Cap how much one chart carries to avoid overload; split into several when it's too dense
- `trend-emphasis` - Put the trend first, not the decoration; skip heavy gradients/shadows that bury the data
- `gridline-subtle` - Keep grid lines low-contrast (e.g. gray-200) so they don't fight the data
- `focusable-elements` - Interactive chart elements (points, bars, slices) are keyboard-navigable (WCAG)
- `screen-reader-summary` - Offer a text summary or aria-label that states the chart's key insight for screen readers (WCAG)
- `error-state-chart` - A load failure shows an error with a retry, not a broken or empty chart
- `export-option` - On data-heavy products, let users export the chart data as CSV/image
- `drill-down-consistency` - Drill-downs keep a clear back-path and a hierarchy breadcrumb
- `time-scale-clarity` - Time-series charts label the time granularity (day/week/month) and let you switch it
