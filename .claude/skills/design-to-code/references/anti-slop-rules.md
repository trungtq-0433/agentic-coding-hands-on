# Anti-Slop Rules: Avoiding AI Design Fingerprints

These are the moves LLMs make on autopilot. Read them as "worn-out defaults," not hard bans — context decides. A SaaS dashboard and a personal blog don't play by the same rules.

## Typography

**Reach for an alternative to:**
- `Inter` — so common it's gone invisible. Try `Geist`, `Outfit`, `Cabinet Grotesk`, `Satoshi`, `Plus Jakarta Sans`
- `Roboto` / `Arial` / `Open Sans` — browser defaults with no voice
- `Space Grotesk` — done to death in "tech startup" work

**Alternatives:** variable fonts, display serifs (editorial), tight grotesks (minimal SaaS), humanist sans (consumer apps)

**Steer off:**
- Serif fonts on dashboards/data UIs — keep them for creative or editorial work
- Only Regular (400) + Bold (700) — bring in 500/600 for a softer hierarchy
- Orphaned words — `text-wrap: balance` or `text-wrap: pretty`
- All-caps subheaders everywhere — try lowercase italic, sentence case, small-caps

## Color

**Reach for an alternative to:**
- The AI purple/blue gradient — the single most recognizable LLM fingerprint
- Pure `#000000` — go off-black: `#0a0a0a`, `#111`, Zinc-950, or a tinted dark
- Oversaturated accents (saturation > 80%) — desaturate so they sit elegantly
- Gradient text on large headers — sparingly, never on body copy

**Principles:**
- One accent color per project, tops. Cut the rest.
- One gray family — never warm and cool grays in the same design
- Tint shadows toward the background hue (navy shadow on a navy bg), not flat black
- Flat design with zero texture reads sterile — lay in a little noise/grain

## Layout

**Reach for an alternative to:**
- 3-column equal card rows as the feature section — the most generic AI layout. Use 2-col zig-zag, asymmetric grid, horizontal scroll, or masonry
- Centered hero with a centered H1 at high variance — try split-screen, left-aligned, or asymmetric whitespace
- `h-screen` for full-height sections — always `min-h-[100dvh]` (the iOS Safari viewport bug)
- Flexbox grinding through grid math in `calc()` — hand it to CSS Grid

**Steer off:**
- Everything centered and symmetrical — break it with offset margins or mixed aspect ratios
- Equal card heights forced by flexbox — let heights vary or go masonry
- One border-radius value everywhere — vary it: tighter inside, softer on containers
- No max-width — always cap around ~1200-1440px with auto margins

## Content (The "Jane Doe" Effect)

**Steer off:**
- Cookie-cutter names: "John Doe", "Jane Smith", "Sarah Chan" — use realistic, diverse ones
- Round fake numbers: `99.99%`, `50%`, `$100.00` — use organic data: `47.2%`, `$99.00`
- Startup slop names: "Acme", "Nexus", "SmartFlow" — invent something that fits the context
- AI copy tics: "Elevate", "Seamless", "Unleash", "Next-Gen", "Game-changer", "Delve", "Tapestry" — write plain, specific language
- Lorem Ipsum — write real draft copy, rough is fine
- Exclamation marks in success messages — be confident, not loud
- "Oops!" error messages — say it straight: "Connection failed. Try again."
- Title Case On Every Single Header — sentence case

## Visual Effects

**Reach for an alternative to:**
- Neon/outer glows (`box-shadow` glows) — use inner borders or subtle tinted shadows
- Custom mouse cursors — dated, and they cost performance and accessibility
- Stock `ease-in-out` / `linear` transitions — spring physics or custom cubic-beziers

**Allowed with care:**
- Gradient text — sparingly, on accent elements, never on body or large headers
- Glassmorphism — only when it goes past `backdrop-blur` (add an inner border + refraction shadow)

## Components

**Reach for an alternative to:**
- Unstyled/default shadcn components — always tune the radii, colors, and shadows
- Generic card (border + shadow + white bg) at high density — use spacing/dividers
- Only the stock Lucide/Feather set — try Phosphor, Heroicons, or custom SVG to differentiate
- Rocketship for "Launch", shield for "Security" — drop the cliché metaphors
- 3-card carousel testimonials with dots — masonry wall, embedded posts, or one rotating quote
- Pill-shaped "New"/"Beta" badges everywhere — try square badges or plain text labels
- Avatar circles only — try squircles or rounded squares

## External Resources

**Steer off:**
- Direct Unsplash links — use `https://picsum.photos/seed/{name}/800/600` or SVG UI Avatars
- One avatar image reused across users — give each a unique asset
- Stock "diverse team" photos — use real photos, candid shots, or one consistent illustration style

## AI Tells: Quick Self-Check

Before it ships, sweep for the instant giveaways:
- [ ] Inter anywhere in the project?
- [ ] Purple or blue gradient as the main look?
- [ ] Three equal-width cards in a row?
- [ ] Centered hero text over a dark gradient image?
- [ ] "John Doe" or "Acme Corp" in the copy?
- [ ] Round placeholder numbers (50%, $100)?
- [ ] "Elevate your workflow" or similar AI copy?
- [ ] Pure `#000000` as a background?
- [ ] A generic spinner instead of a skeleton loader?
- [ ] No hover/active states on buttons?

Any box ticked and the design reads as machine-made. Fix it before handing over.
