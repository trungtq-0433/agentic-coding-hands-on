"""SVN Proposal template — role-based descriptors for 17 configured slides.

Each slide is described by ROLES (semantic groups of shapes) instead of
per-shape hardcoded targets. Roles bind to source paths in ProjectProfile,
so changing content (e.g. 6 before_steps instead of 8) just means fewer
shapes get filled — the renderer clears the excess.
"""
from __future__ import annotations

from lib.templates.base import (
    BaseSlideTemplate,
    ContentKind,
    ShapeFindStrategy,
    ShapeRole,
    SlideRoleConfig,
)


# ---------------------------------------------------------------------------
# Helper builders to keep slide configs compact
# ---------------------------------------------------------------------------

def _text_by_index(name: str, idx: int, source: str, desc: str = '') -> ShapeRole:
    return ShapeRole(
        name=name, cardinality=1, kind=ContentKind.TEXT, source_path=source,
        find_strategy=ShapeFindStrategy.BY_INDEX, find_params={'index': idx},
        description=desc,
    )


def _table_by_index(name: str, idx: int, source: str, fill_cols=None, desc: str = '') -> ShapeRole:
    return ShapeRole(
        name=name, cardinality=1, kind=ContentKind.TABLE, source_path=source,
        find_strategy=ShapeFindStrategy.BY_INDEX, find_params={'index': idx},
        fill_cols=fill_cols, description=desc,
    )


def _image_fit_slide(name: str, idx: int, source: str, desc: str = '') -> ShapeRole:
    return ShapeRole(
        name=name, cardinality=1, kind=ContentKind.IMAGE, source_path=source,
        find_strategy=ShapeFindStrategy.BY_INDEX, find_params={'index': idx},
        fit_to_slide=True, description=desc,
    )


def _image_by_index(name: str, idx: int, source: str, desc: str = '') -> ShapeRole:
    return ShapeRole(
        name=name, cardinality=1, kind=ContentKind.IMAGE, source_path=source,
        find_strategy=ShapeFindStrategy.BY_INDEX, find_params={'index': idx},
        description=desc,
    )


def _text_collection_by_names(name: str, names: list[str], source: str, desc: str = '') -> ShapeRole:
    """N-cardinality role: list of shapes, each looked up by exact name (recursive group search)."""
    return ShapeRole(
        name=name, cardinality=len(names), kind=ContentKind.TEXT, source_path=source,
        find_strategy=ShapeFindStrategy.BY_NAME, find_params={'names': names},
        description=desc,
    )


def _text_collection_by_indices(name: str, indices: list[int], source: str, desc: str = '') -> ShapeRole:
    """N-cardinality role: list of top-level shapes located by index."""
    return ShapeRole(
        name=name, cardinality=len(indices), kind=ContentKind.TEXT, source_path=source,
        find_strategy=ShapeFindStrategy.BY_INDEX, find_params={'indices': indices},
        description=desc,
    )


def _compound_by_names(name: str, source: str, title_names: list[str], body_names: list[str], desc: str = '') -> ShapeRole:
    """Compound role: list of (title, body) pairs. Each pair has its own shape names."""
    return ShapeRole(
        name=name, cardinality=len(title_names), kind=ContentKind.TEXT, source_path=source,
        find_strategy=ShapeFindStrategy.BY_NAME,
        find_params={'pair_names': list(zip(title_names, body_names))},
        sub_roles=[
            ShapeRole(name='title', cardinality=1, kind=ContentKind.TEXT, source_path='title',
                      find_strategy=ShapeFindStrategy.BY_NAME),
            ShapeRole(name='body', cardinality=1, kind=ContentKind.TEXT, source_path='body',
                      find_strategy=ShapeFindStrategy.BY_NAME),
        ],
        description=desc,
    )


def _compound_by_indices(name: str, source: str, title_indices: list[int], body_indices: list[int], desc: str = '') -> ShapeRole:
    """Compound role: list of (title, body) pairs located by top-level index."""
    return ShapeRole(
        name=name, cardinality=len(title_indices), kind=ContentKind.TEXT, source_path=source,
        find_strategy=ShapeFindStrategy.BY_INDEX,
        find_params={'pair_indices': list(zip(title_indices, body_indices))},
        sub_roles=[
            ShapeRole(name='title', cardinality=1, kind=ContentKind.TEXT, source_path='title',
                      find_strategy=ShapeFindStrategy.BY_INDEX),
            ShapeRole(name='body', cardinality=1, kind=ContentKind.TEXT, source_path='body',
                      find_strategy=ShapeFindStrategy.BY_INDEX),
        ],
        description=desc,
    )


# ---------------------------------------------------------------------------
# SVN template configuration
# ---------------------------------------------------------------------------

# Map profile section name → FULL list of slide numbers that section fills.
# Used by (a) extra-slide insertion to resolve `anchor_section` → insert position
# (the section's LAST slide, `SECTION_TO_SLIDES[key][-1]`), and (b) the
# prune+reorder pass to know exactly which template slides a section owns.
# Insertion order = canonical section order (also the fallback for
# `profile.section_order` when a profile predates section-order tracking).
SECTION_TO_SLIDES: dict[str, list[int]] = {
    'project_background': [4],
    'features': [5],
    'nfr_overview': [6],
    'screen_flow': [8],
    'business_process': [10, 11],
    'benefits': [12, 13],
    'approach_comparison': [21],
    'assumptions': [23, 24, 25],
    'infrastructure': [33],
    'software_stack': [34],
    'nfr_sections': [35],
    'nfr_detailed': [36],
    'schedule': [43],
}

# Map chapter divider slide → the content slide numbers it introduces.
# The prune+reorder pass keeps a divider iff at least one of its content
# slides survives (i.e. the owning section has content).
CHAPTER_DIVIDERS: dict[int, list[int]] = {
    3: [4, 5, 6, 8],
    9: [10, 11, 12, 13],
    17: [21],
    22: [23, 24, 25],
    27: [33, 34, 35, 36],
    41: [43],
}

# Slides kept unconditionally regardless of content (cover + agenda).
ALWAYS_KEEP_SLIDES = [1, 2]

# Slide 11 (business process, horizontal view) — bespoke shape indices for the
# before/after split fallback used when `after_blocks` overflows its 4 slots.
# A human editor wouldn't duplicate the whole slide (repeating the unrelated
# before_steps row); they'd split into a before-only slide and an after-only
# slide with the overflow laid out as a second row. Indices are 0-based
# top-level `slide.shapes` positions specific to this exact template file.
BUSINESS_PROCESS_SLIDE11_LAYOUT = {
    'before_bg': 3,
    'before_label': 4,
    'before_boxes': [8, 9, 10, 11, 12, 13, 15, 14],  # left→right visual order
    'before_connectors': [17, 18, 19, 20, 21, 22, 23],  # connector[i] is between box[i] and box[i+1]
    'after_bg': 2,
    'after_label': 35,
    'after_card_bg': [16, 7, 6, 5],  # per-column card backdrop, col1→col4 (behind title/body)
    'after_title_boxes': [24, 25, 26, 27],
    'after_body_boxes': [31, 32, 33, 34],
    'after_connectors': [28, 29, 30],
    'row_arrow': 36,  # connector between the before/after panels
}


class SVNProposalTemplate(BaseSlideTemplate):
    """72-slide SVN Proposal Menu template — 17 slides configured for filling."""

    def _initialize_configs(self):
        c = self.slide_role_configs

        # Slide 4: System Overview (current issues + objectives)
        c[4] = SlideRoleConfig(
            slide_number=4,
            content_types=['text'],
            roles=[
                _text_by_index('current_issues', 3, 'project_background.current_issues',
                               '現状の課題 - left column'),
                _text_by_index('objectives', 6, 'project_background.objectives',
                               '目的・実現したいこと - right column'),
            ],
            description='Current issues + objectives, 2-column layout',
        )

        # Slide 5: Feature list (description + table)
        c[5] = SlideRoleConfig(
            slide_number=5, content_types=['text', 'table'],
            roles=[
                _text_by_index('feature_description', 3, 'features.description',
                               '機能一覧表の説明文'),
                _table_by_index('function_table', 8, 'features.table',
                                desc='機能一覧テーブル (6 cols)'),
            ],
        )

        # Slide 6: NFR overview (description + table)
        c[6] = SlideRoleConfig(
            slide_number=6, content_types=['text', 'table'],
            roles=[
                _text_by_index('requirements_description', 2, 'nfr_overview.description',
                               '非機能要件の説明文'),
                _table_by_index('requirements_table', 4, 'nfr_overview.table',
                                desc='非機能要件テーブル (5 cols)'),
            ],
        )

        # Slide 8: Screen transition diagram (fill slide content area)
        c[8] = SlideRoleConfig(
            slide_number=8, content_types=['image'],
            roles=[_image_fit_slide('screen_flow_image', 3, 'screen_flow.image_path',
                                    '画面遷移図 PNG — fit to slide content area')],
        )

        # Slide 10: Vertical business process (4 category labels, 8 before_steps in GROUPs, 4 after_blocks)
        # Most editable shapes live in GROUP shapes — must be found by NAME (recursive).
        c[10] = SlideRoleConfig(
            slide_number=10, content_types=['text'],
            roles=[
                _text_collection_by_indices(
                    'category_labels', [5, 9, 7, 6], 'business_process.categories',
                    '4 process category labels (top-level)',
                ),
                _text_collection_by_names(
                    'before_steps',
                    [
                        'Google Shape;859;p10',  # step 1
                        'Google Shape;862;p10',  # step 2
                        'Google Shape;865;p10',  # step 3
                        'Google Shape;868;p10',  # step 4
                        'Google Shape;871;p10',  # step 5
                        'Google Shape;874;p10',  # step 6
                        'Google Shape;877;p10',  # step 7
                        'Google Shape;880;p10',  # step 8
                    ],
                    'business_process.before_steps',
                    '8 before-process step boxes (nested in GROUPs)',
                ),
                _compound_by_names(
                    'after_blocks', 'business_process.after_blocks',
                    title_names=['Google Shape;835;p10', 'Google Shape;839;p10',
                                 'Google Shape;843;p10', 'Google Shape;847;p10'],
                    body_names=['Google Shape;836;p10', 'Google Shape;840;p10',
                                'Google Shape;844;p10', 'Google Shape;848;p10'],
                    desc='4 after-process benefit blocks (title + body)',
                ),
            ],
        )

        # Slide 11: Horizontal business process (8 before_steps top-level, 4 after_blocks top-level)
        c[11] = SlideRoleConfig(
            slide_number=11, content_types=['text'],
            roles=[
                _text_collection_by_indices(
                    'before_steps', [8, 9, 10, 11, 12, 13, 15, 14],
                    'business_process.before_steps',
                    '8 before-step boxes, left → right',
                ),
                _compound_by_indices(
                    'after_blocks', 'business_process.after_blocks',
                    title_indices=[24, 25, 26, 27],
                    body_indices=[31, 32, 33, 34],
                    desc='4 after-block (title+body) pairs, left → right',
                ),
            ],
        )

        # Slides 12 & 13: System benefits (2 title+body pairs each)
        # Slide 12 takes benefits[0:2], slide 13 takes benefits[2:4]
        c[12] = SlideRoleConfig(
            slide_number=12, content_types=['text'],
            roles=[_compound_by_indices(
                'benefit_blocks', 'benefits[0:2]',
                title_indices=[2, 4], body_indices=[3, 5],
                desc='2 benefit title+body pairs (削減コスト / 業務効率)',
            )],
        )

        c[13] = SlideRoleConfig(
            slide_number=13, content_types=['text'],
            roles=[_compound_by_indices(
                'benefit_blocks', 'benefits[2:4]',
                title_indices=[2, 4], body_indices=[3, 5],
                desc='2 benefit title+body pairs (セキュリティ / システム連携)',
            )],
        )

        # Slide 21: Approach comparison table (3-4 columns)
        c[21] = SlideRoleConfig(
            slide_number=21, content_types=['table'],
            roles=[_table_by_index('approach_table', 2, 'approach_comparison',
                                   desc='アプローチ比較サマリ')],
        )

        # Slides 23, 24, 25: Assumptions (2-col table, fill col 1 only)
        # Each slide takes a slice of the assumptions list.
        c[23] = SlideRoleConfig(
            slide_number=23, content_types=['table'],
            roles=[_table_by_index('assumptions_table', 0, 'assumptions[0:5]',
                                   fill_cols=[1],
                                   desc='前提条件 part1 (5 rows: 開発方針/品質戦略/開発言語/機能要件/非機能要件)')],
        )

        c[24] = SlideRoleConfig(
            slide_number=24, content_types=['table'],
            roles=[_table_by_index('assumptions_table', 0, 'assumptions[5:8]',
                                   fill_cols=[1],
                                   desc='前提条件 part2 (3 rows: デザイン/外部API/その他)')],
        )

        c[25] = SlideRoleConfig(
            slide_number=25, content_types=['table'],
            roles=[_table_by_index('assumptions_table', 0, 'assumptions[8:9]',
                                   fill_cols=[1],
                                   desc='前提条件 part3 (1 row: インフラ)')],
        )

        # Slide 33: Infrastructure configuration table (3 cols)
        c[33] = SlideRoleConfig(
            slide_number=33, content_types=['table'],
            roles=[_table_by_index('infrastructure_table', 0, 'infrastructure',
                                   desc='インフラ構成テーブル')],
        )

        # Slide 34: Software stack table (3 cols)
        c[34] = SlideRoleConfig(
            slide_number=34, content_types=['table'],
            roles=[_table_by_index('software_table', 0, 'software_stack',
                                   desc='ソフトウェア構成テーブル')],
        )

        # Slide 35: NFR sections (4 title+body pairs)
        # Order in template: Performance, Maintainability, Scalability, Availability
        c[35] = SlideRoleConfig(
            slide_number=35, content_types=['text'],
            roles=[_compound_by_indices(
                'nfr_sections', 'nfr_sections',
                title_indices=[5, 18, 14, 10],
                body_indices=[6, 19, 15, 11],
                desc='4 NFR title+body sections (Performance/Maintainability/Scalability/Availability)',
            )],
        )

        # Slide 36: Detailed NFR table (5 cols, 12-18 rows)
        c[36] = SlideRoleConfig(
            slide_number=36, content_types=['table'],
            roles=[_table_by_index('nfr_detailed_table', 0, 'nfr_detailed',
                                   desc='非機能要件詳細版テーブル')],
        )

        # Slide 43: Development schedule (description text + Gantt image)
        c[43] = SlideRoleConfig(
            slide_number=43, content_types=['text', 'image'],
            roles=[
                _text_by_index('schedule_description', 0, 'schedule.description',
                               'スケジュール説明文'),
                _image_by_index('schedule_image', 15, 'schedule.image_path',
                                '開発スケジュール Gantt chart PNG'),
            ],
        )

    def get_template_info(self):
        return {
            'name': 'SVN Proposal Menu',
            'total_slides': 72,
            'configured_slides': len(self.slide_role_configs),
            'protected_slides': self.protected_slides,
            'version': '2.0.0',
        }


if __name__ == '__main__':
    t = SVNProposalTemplate()
    print(f'Configured slides: {sorted(t.slide_role_configs.keys())}')
    print(f'Total: {len(t.slide_role_configs)}')
    for sn in sorted(t.slide_role_configs.keys()):
        cfg = t.slide_role_configs[sn]
        print(f'  Slide {sn}: {len(cfg.roles)} role(s) — {[r.name for r in cfg.roles]}')
