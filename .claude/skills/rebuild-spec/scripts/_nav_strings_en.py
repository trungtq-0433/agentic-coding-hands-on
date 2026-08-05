"""English prose for the docs reading-order index. Data only (locale module).

Numbers, links, and role reading-paths come from _nav_strings (structure); this
file carries ONLY translatable prose. role_labels is keyed by the role keys in
_nav_strings.ROLES so the number sequences stay single-sourced.
"""
from __future__ import annotations

STRINGS = {
    "title": "Documentation Index — Reading Order",
    "intro": (
        "This index lists the generated documentation in recommended reading "
        "order. Read top-down: orientation before detail. The numbers are a "
        "suggested path, not a strict dependency."
    ),
    "quick_path_label": "Minimum fast read",
    "col_headers": ("#", "Document", "What it answers"),
    "roles_heading": "Read by role",
    "role_labels": {
        "new_dev": "New developer — get productive fast",
        "reviewer": "Reviewer — rules, permissions, contracts",
        "pm": "PM / BA — scope and behavior",
    },
    "layer_labels": {
        1: "Orientation — what the system is and why",
        2: "Domain model — entities, features, and stories",
        3: "Interfaces & behavior — screens, APIs, rules, permissions",
        4: "Deep dives — flows, per-feature, and per-screen specs",
    },
    "layer_intros": {
        1: ("Start here if you are new. This layer answers what the system is "
            "and how it is shaped, before any detail."),
        2: ("The domain vocabulary — the entities, the feature catalogue, and "
            "the user stories that everything else refers back to."),
        3: ("How the system behaves at its edges: the screens users touch, the "
            "API surface, the business rules it enforces, and who may do what."),
        4: ("Drill-downs for when you need depth on one specific flow, feature, "
            "or screen — read after the layers above give you the map."),
    },
    "principles_label": "Principles",
    "principles": [
        "Read top-down: orientation (Layer 1) before deep dives (Layer 4).",
        "The numbered order is a recommended path, not a hard dependency.",
        "Absent artifacts are omitted — run the relevant pass to populate them.",
    ],
    "footnote": "Rows for passes that have not run are omitted from this index.",
    # Multi-line "how to read a feature" traversal block, rendered (presence-pruned
    # on the features/*/ entry) as a blockquote under the layer-4 table. Superseded
    # the single feature_reading_note line in A2. List length is the skeleton — the
    # parity test asserts equal len() across locales. Line 2 documents the CURRENT
    # manual screen-name → SCR### lookup (pre-Phase-B); Phase B upgrades it to a link.
    "feature_traversal": [
        "How to read a feature: open its folder and read the 4 files in order — "
        "business-context (why) → screens (what the user sees) → technical-spec "
        "(how) → edge-cases (what breaks).",
        "To go deeper on a screen listed in screens.md, follow the SCR### code in "
        "its row to docs/screens/SCR###/spec.md (the spec links back via its "
        "**Feature** header).",
        "See generated/screen-flow.md for how this feature's screens connect — its "
        "entry, owned, and exit screens.",
    ],
    # Causal "why read this here" clauses for the single-component reading-order
    # tables (layers 1-3 only). Keyed by the READING_ORDER entry "key" — no parallel
    # map, the entry key IS the lookup. Appended to the "what it answers" cell as
    # " — <clause>" (mirrors aggregate reading_order_rows). Layer-4 entries
    # (flows/features/screens) carry no clause here — A2/A3 prose covers them.
    "reading_why": {
        "system_overview": (
            "Read first — establishes the product's purpose, scope, and primary "
            "actors before any structural or behavioral detail."
        ),
        "architecture": (
            "Read after the overview because the layer diagram, tech stack, and "
            "data flow only make sense once you know what the system is for."
        ),
        "glossary": (
            "Read after the overview so the shared and ambiguous terms are pinned "
            "down before the deeper docs lean on them."
        ),
        "entities": (
            "Read after orientation — the core data entities are the vocabulary the "
            "feature list, stories, and APIs all refer back to."
        ),
        "feature_list": (
            "Read after the entities because each feature is described by the data "
            "it touches; this is the catalogue everything else indexes into."
        ),
        "user_stories": (
            "Read after the feature list — the stories expand each F### into "
            "concrete actor goals and acceptance intent."
        ),
        "screen_list": (
            "Read after the stories because screens are where those user goals "
            "become something the user can see and touch."
        ),
        "screen_flow": (
            "Read after the screen list so you know the screens before tracing how "
            "navigation and state move between them."
        ),
        "route_list": (
            "Read after the screens because the routes are the backend surface "
            "those screens call into."
        ),
        "api_map": (
            "Read after the route list — it groups the raw routes by resource and "
            "adds background jobs, giving the API its shape."
        ),
        "api_contracts": (
            "Read after the API map when you need the exact request and response "
            "shapes behind each grouped endpoint."
        ),
        "behavior_logic": (
            "Read after the API surface because the BL### units describe the async "
            "and background logic those endpoints and jobs trigger."
        ),
        "business_rules": (
            "Read after behavior because the invariants here are the constraints "
            "all that behavior must always satisfy."
        ),
        "permissions_matrix": (
            "Read after the rules — it pins down which role may perform each action "
            "the rest of the system exposes."
        ),
    },
    # Static orientation legend (A3): explains the cross-reference graph between the
    # ID systems and WHERE each linkage is recorded. NOT a generated per-repo table —
    # the live F### → SCR### table is generated/screen-flow.md § Feature Entry Points.
    # Rendered (as a bullet list under the heading) only when feature-list or
    # screen-list is present. List length is the skeleton (parity test).
    "relationship_map_heading": "How the ID systems relate",
    "relationship_map": [
        "**F###** (feature) — a unit of product behavior; catalogued in "
        "generated/feature-list.md.",
        "**SCR###** (screen) — a UI surface a feature owns; inventoried in "
        "generated/screen-list.md, detailed in docs/screens/SCR###/spec.md.",
        "**ROUTE###** (route) — a backend endpoint a feature owns; inventoried in "
        "generated/route-list.md via its Owner F### column (api-map.md and "
        "api-contracts.md are separate, unbound views — not cross-checked here).",
        "**US###** (user story) — an actor goal a feature satisfies; in "
        "generated/user-stories.md.",
        "The live per-feature map (entry / owned / exit screens) lives in "
        "generated/screen-flow.md § Feature Entry Points.",
    ],
    # A6 — per-role trailing notes, keyed by ROLES key. Appended to a role's reading
    # line only when its gating entry (the features glob, entry 16) survives pruning,
    # so it never points new_dev at an absent feature folder.
    "role_notes": {
        "new_dev": (
            "after the features entry, pick one feature and read it end-to-end — see "
            "“How to read a feature” below"
        ),
    },
    # A4 — per-feature README (docs/features/F###_Slug/README.md). file_purposes keys
    # are the 4 satellite filenames (skeleton identity asserted across locales).
    "feature_readme": {
        "title": "Feature {feature} — Reading Guide",
        "intro": (
            "Read this feature's files in order, then open any screen's full spec "
            "from the table below."
        ),
        "order_heading": "Reading order",
        "screens_heading": "Screens in this feature",
        "col_screen": "Screen",
        "col_scr": "SCR",
        "col_spec": "Spec",
        "unresolved": "—",
        # Route/API table (v25.0.0) — mirrors the Screens table shape above, but
        # every row's Spec link points at the single shared route-list.md (routes
        # have no per-route spec file the way screens have spec.md).
        "routes_heading": "Routes used by this feature",
        "col_route": "Route",
        "col_route_owner": "Method + Path",
        "col_route_spec": "Spec",
        "file_purposes": {
            "business-context.md": "why this feature exists",
            "screens.md": "what the user sees",
            "technical-spec.md": "how it works",
            "edge-cases.md": "what breaks",
            "test-cases.md": "how it's tested (UT/IT/UAT — optional)",
        },
    },
    # A5 — docs/features/README.md feature index.
    "features_index": {
        "title": "Features — Index",
        "intro": (
            "Every feature in this product. Open one and read it end-to-end via "
            "its reading guide."
        ),
    },
    "components_index": {
        "title": "Components Index — Reading Order",
        "intro": (
            "Lists every component module in recommended reading order: "
            "entry-point / gateway first, then domain services, frontend, fullstack, "
            "and reused nodes last."
        ),
        "col_num": "#",
        "col_module": "Module",
        "col_role": "Role",
        "role_labels": {
            "gateway": "Gateway",
            "api-gateway": "API Gateway",
            "api_gateway": "API Gateway",
            "backend": "Backend service",
            "service": "Service",
            "frontend": "Frontend",
            "fullstack": "Fullstack",
        },
        "reused_marker": "(reused)",
        "system_readme_title": "System Documentation — Reading Order",
    },
    "aggregate_index": {
        "title": "System of Systems — Reading Order",
        "intro": (
            "This index covers the multi-service aggregate documentation. "
            "Read top-down: system overview first, then catalog, architecture, "
            "ownership, flows, glossary, and confidence."
        ),
        "components_pointer_label": "All components",
        "components_pointer_desc": (
            "Per-component documentation index — each component's own docs, "
            "in suggested reading order"
        ),
        "roles_heading": "Read by role",
        "parent_pointer": "Full reading order: [system/README.md](system/README.md).",
        "read_first_heading": "Which service to read first",
        "read_first_intro": (
            "Suggested order across services — read the entry point and the most "
            "depended-on services first, reused components last."
        ),
        "rationale_gateway": "Entry point — start here; {n} service(s) depend on it.",
        "rationale_backend": "Backend service — called by {n} other service(s).",
        "rationale_frontend": "Frontend / client — read after its backend services.",
        "rationale_reused": "Reused component — read after the services that consume it.",
        "read_first_intro_no_deps": (
            "Cross-service dependencies were not statically detected{stack_hint}. "
            "Services are listed alphabetically — reading order is not significant."
        ),
    },
    "aggregate_why": {
        "overview": (
            "Read first — establishes the system's purpose, scope, and actors "
            "before any structural detail is introduced."
        ),
        "component_catalog": (
            "Read after the overview — lists every component with its role and "
            "responsibilities, giving you the vocabulary that architecture and "
            "ownership docs build on."
        ),
        "architecture": (
            "Read after the catalog — the layer diagram and topology reference "
            "the components catalogued there; context is needed to interpret "
            "service boundaries and data flows."
        ),
        "data_ownership_map": (
            "Read after architecture — maps entity ownership and correlation "
            "candidates across the services whose boundaries were just drawn."
        ),
        "cross_service_flows": (
            "Read after data ownership — end-to-end sagas and handoff sequences "
            "span the services and entities already introduced in the prior docs."
        ),
        "glossary": (
            "Read after the flows — shared and ambiguous terms now have the "
            "full system context needed to disambiguate them across services."
        ),
        "per_component_confidence": (
            "Read last — confidence scores and coverage gaps make sense only "
            "after you know the components, their roles, and what was authored."
        ),
    },
    "artifact_descriptions": {
        "system_overview": "Product goals, scope, primary actors, and the big picture — read first",
        "architecture": "Layer diagram, tech stack, service boundaries, and the main data flow",
        "glossary": "Shared and ambiguous domain terms, each defined once",
        "entities": "Core data entities, their key fields, and how they relate",
        "feature_list": "The full F### feature catalogue, each with a one-line summary",
        "user_stories": "US### user stories grouped by feature and actor",
        "screen_list": "Inventory of every SCR### screen in the product",
        "screen_flow": "How screens connect — navigation paths and state transitions",
        "route_list": "Every API route the backend exposes, with method and path",
        "api_map": "API surface grouped by resource, plus background jobs",
        "api_contracts": "Request/response shapes for REST/GraphQL/gRPC endpoints",
        "behavior_logic": "BL### background/async logic units and what triggers them",
        "business_rules": "Invariants and constraints the system must always enforce",
        "permissions_matrix": "Which role may perform which action (RBAC matrix)",
        "flows": "Cross-cutting process flows that span more than one feature",
        "features": "Per-feature deep specs — 4 files per feature (see note below)",
        "screens": "Per-screen detailed UI and behavior specifications",
        "job_list": "JOB### batch/background-job inventory with schedule and retry detail",
        "design_intent": "EXPERIMENTAL — inferred rationale for why the system was built this way",
    },
}
