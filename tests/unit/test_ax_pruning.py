"""Unit tests and benchmarks for accessibility tree pruning."""

from unittest.mock import MagicMock, patch
import json
import pytest

from actra.mac import accessibility


def test_ax_pruning_filters_non_actionable_nodes():
    """Verify that pruning removes non-interactive layout containers and empty groups."""
    # Build a simulated complex AX hierarchy:
    # App -> Window -> SplitGroup (decorative) -> Group (decorative) -> Button "Search"
    #                                           -> Group (decorative empty)
    #               -> ScrollArea -> WebArea -> Heading "Welcome"
    #                                        -> GenericContainer (decorative)

    def mock_get_attr(elem, attr):
        attrs = getattr(elem, "_attrs", {})
        return attrs.get(attr)

    def mock_get_actions(elem):
        return getattr(elem, "_actions", [])

    btn = MagicMock(_attrs={"AXRole": "AXButton", "AXTitle": "Search", "AXPosition": MagicMock(x=10, y=20), "AXSize": MagicMock(width=80, height=30)}, _actions=["AXPress"])
    empty_grp = MagicMock(_attrs={"AXRole": "AXGroup"}, _actions=[])
    grp1 = MagicMock(_attrs={"AXRole": "AXGroup", "AXChildren": [btn, empty_grp]}, _actions=[])
    split = MagicMock(_attrs={"AXRole": "AXSplitGroup", "AXChildren": [grp1]}, _actions=[])

    heading = MagicMock(_attrs={"AXRole": "AXHeading", "AXTitle": "Welcome", "AXValue": "Welcome Header"}, _actions=[])
    empty_gen = MagicMock(_attrs={"AXRole": "AXGenericElement"}, _actions=[])
    web = MagicMock(_attrs={"AXRole": "AXScrollArea", "AXChildren": [heading, empty_gen]}, _actions=[])

    window = MagicMock(_attrs={"AXRole": "AXWindow", "AXTitle": "Safari Window", "AXChildren": [split, web]}, _actions=[])
    app = MagicMock(_attrs={"AXRole": "AXApplication", "AXTitle": "Safari", "AXChildren": [window]}, _actions=[])

    with patch("actra.mac.accessibility._get_attr", side_effect=mock_get_attr):
        with patch("actra.mac.accessibility._get_actions", side_effect=mock_get_actions):
            # 1. Full Tree
            full_tree = accessibility._element_to_dict(
                app, pid=123, path=[], depth=0, max_depth=5, id_counter=[0], full_tree=True
            )
            # 2. Pruned Tree
            pruned_tree = accessibility._element_to_dict(
                app, pid=123, path=[], depth=0, max_depth=5, id_counter=[0], full_tree=False
            )

    full_json = json.dumps(full_tree, indent=2)
    pruned_json = json.dumps(pruned_tree, indent=2)

    assert len(pruned_json) < len(full_json)
    assert "empty_gen" not in pruned_json
    assert "Search" in pruned_json
    assert "Welcome" in pruned_json

    print(f"\n[AX Tree Pruning Benchmark]")
    print(f"Full tree size:   {len(full_json)} chars (~{len(full_json)//4} tokens)")
    print(f"Pruned tree size: {len(pruned_json)} chars (~{len(pruned_json)//4} tokens)")
    reduction = (1 - (len(pruned_json) / len(full_json))) * 100
    print(f"Token reduction:  {reduction:.1f}%")
    assert reduction > 20.0
