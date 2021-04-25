# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestLayout::test_layer_init_polygon_with_polygon 1'] = '<g><path fill-rule="evenodd" fill="#66cc99" stroke="#555555" stroke-width="2.0" opacity="0.6" d="M 0.0,0.0 L 30.0,30.0 L 0.0,30.0 L 0.0,0.0 z" /></g>'

snapshots['TestLayout::test_layer_init_polygon_without_polygon 1'] = '<g><path fill-rule="evenodd" fill="#66cc99" stroke="#555555" stroke-width="2.0" opacity="0.6" d="M 0.0,0.0 L 100.0,0.0 L 100.0,200.0 L 0.0,200.0 L 0.0,0.0 z" /></g>'

snapshots['TestLayout::test_layout_init 1'] = {
    0: set([
        1,
        2
    ]),
    1: set([
        0,
        2
    ]),
    2: set([
        0,
        1
    ])
}

snapshots['TestLayout::test_layout_init 2'] = [
    '<g><path fill-rule="evenodd" fill="#66cc99" stroke="#555555" stroke-width="2.0" opacity="0.6" d="M 0.0,30.0 L 0.0,200.0 L 100.0,200.0 L 100.0,0.0 L 30.0,0.0 L 30.0,20.0 L 40.0,20.0 L 40.0,30.0 L 30.0,30.0 L 10.0,30.0 L 0.0,30.0 z" /></g>',
    '<g><path fill-rule="evenodd" fill="#66cc99" stroke="#555555" stroke-width="2.0" opacity="0.6" d="M 30.0,20.0 L 30.0,0.0 L 0.0,0.0 L 0.0,30.0 L 10.0,30.0 L 10.0,20.0 L 30.0,20.0 z" /></g>',
    '<g><path fill-rule="evenodd" fill="#66cc99" stroke="#555555" stroke-width="2.0" opacity="0.6" d="M 10.0,20.0 L 40.0,20.0 L 40.0,30.0 L 10.0,30.0 L 10.0,20.0 z" /></g>'
]
