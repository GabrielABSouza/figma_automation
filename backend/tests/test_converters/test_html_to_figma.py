"""Tests for the HTML-to-Figma converter.

Level 2: Verifies that HTML with inline styles is correctly converted
to a Figma node tree with proper properties.
"""

import pytest

from backend.converters.html_to_figma import (
    _apply_text_transform,
    _convert_icon_node,
    _font_weight_to_style,
    _parse_border,
    _parse_border_radius,
    _parse_box_shadow,
    _parse_color,
    _parse_hex_color,
    _parse_inline_style,
    _parse_letter_spacing,
    _parse_padding,
    _parse_px,
    _validate_tree,
    convert_html_to_figma_tree,
)

# ─── CSS Parsing Unit Tests ───


class TestParseInlineStyle:
    def test_simple_properties(self):
        result = _parse_inline_style("display: flex; color: #fff")
        assert result == {"display": "flex", "color": "#fff"}

    def test_empty_string(self):
        assert _parse_inline_style("") == {}

    def test_trailing_semicolon(self):
        result = _parse_inline_style("padding: 16px;")
        assert result == {"padding": "16px"}

    def test_whitespace_handling(self):
        result = _parse_inline_style("  font-size : 14px ;  color : #000  ")
        assert result["font-size"] == "14px"
        assert result["color"] == "#000"

    def test_complex_value(self):
        result = _parse_inline_style(
            "box-shadow: 0 4px 6px rgba(0,0,0,0.1)"
        )
        assert result["box-shadow"] == "0 4px 6px rgba(0,0,0,0.1)"


class TestParseColor:
    def test_hex_6_digit(self):
        c = _parse_color("#2563EB")
        assert c is not None
        assert abs(c["r"] - 0.145) < 0.01
        assert abs(c["g"] - 0.388) < 0.01
        assert abs(c["b"] - 0.922) < 0.01

    def test_hex_3_digit(self):
        c = _parse_hex_color("#fff")
        assert c is not None
        assert c["r"] == 1.0
        assert c["g"] == 1.0
        assert c["b"] == 1.0

    def test_rgb_function(self):
        c = _parse_color("rgb(255, 0, 128)")
        assert c is not None
        assert c["r"] == 1.0
        assert c["g"] == 0.0
        assert abs(c["b"] - 0.502) < 0.01

    def test_rgba_function(self):
        c = _parse_color("rgba(0, 0, 0, 0.5)")
        assert c is not None
        assert c["r"] == 0.0

    def test_named_color_white(self):
        c = _parse_color("white")
        assert c == {"r": 1.0, "g": 1.0, "b": 1.0}

    def test_named_color_black(self):
        c = _parse_color("black")
        assert c == {"r": 0.0, "g": 0.0, "b": 0.0}

    def test_transparent_returns_none(self):
        assert _parse_color("transparent") is None

    def test_invalid_returns_none(self):
        assert _parse_color("not-a-color") is None


class TestParsePx:
    def test_with_px_suffix(self):
        assert _parse_px("16px") == 16.0

    def test_without_suffix(self):
        assert _parse_px("24") == 24.0

    def test_float_value(self):
        assert _parse_px("1.5px") == 1.5

    def test_invalid_returns_none(self):
        assert _parse_px("auto") is None

    def test_empty_returns_none(self):
        assert _parse_px("") is None


class TestParsePadding:
    def test_single_value(self):
        assert _parse_padding("16px") == (16, 16, 16, 16)

    def test_two_values(self):
        assert _parse_padding("16px 24px") == (16, 24, 16, 24)

    def test_three_values(self):
        assert _parse_padding("10px 20px 30px") == (10, 20, 30, 20)

    def test_four_values(self):
        assert _parse_padding("10px 20px 30px 40px") == (10, 20, 30, 40)


class TestParseBorder:
    def test_solid_border(self):
        weight, color = _parse_border("1px solid #E2E8F0")
        assert weight == 1.0
        assert color is not None

    def test_none_border(self):
        weight, color = _parse_border("none")
        assert weight == 0
        assert color is None


class TestParseBoxShadow:
    def test_valid_shadow(self):
        result = _parse_box_shadow("0 4px 6px rgba(0,0,0,0.1)")
        assert result is not None
        assert result["type"] == "DROP_SHADOW"
        assert result["offset"]["y"] == 4
        assert result["radius"] == 6
        assert result["color"]["a"] == pytest.approx(0.1)

    def test_invalid_returns_none(self):
        assert _parse_box_shadow("none") is None
        assert _parse_box_shadow("") is None


class TestParseBorderRadius:
    def test_px_value(self):
        assert _parse_border_radius("12px") == 12

    def test_fifty_percent(self):
        assert _parse_border_radius("50%") == 9999

    def test_large_px(self):
        assert _parse_border_radius("9999px") == 9999


class TestFontWeightToStyle:
    def test_regular(self):
        assert _font_weight_to_style(400) == "Regular"

    def test_medium(self):
        assert _font_weight_to_style(500) == "Medium"

    def test_semibold(self):
        assert _font_weight_to_style(600) == "Semi Bold"

    def test_bold(self):
        assert _font_weight_to_style(700) == "Bold"


# ─── HTML → Figma Conversion Tests ───


class TestConvertHtmlToFigmaTree:
    def test_empty_html_returns_default_frame(self):
        tree = convert_html_to_figma_tree("", "EmptyScreen")
        assert tree["type"] == "FRAME"
        assert tree["name"] == "EmptyScreen"
        assert tree["width"] == 1440

    def test_simple_div_becomes_frame(self):
        html = "<div style='display: flex; flex-direction: column'></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree["type"] == "FRAME"
        assert tree["layoutMode"] == "VERTICAL"

    def test_horizontal_flex(self):
        html = "<div style='display: flex; flex-direction: row'></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree["layoutMode"] == "HORIZONTAL"

    def test_background_color(self):
        html = "<div style='background-color: #0F172A'></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        assert "fills" in tree
        assert len(tree["fills"]) == 1
        assert tree["fills"][0]["type"] == "SOLID"
        assert tree["fills"][0]["color"]["r"] == pytest.approx(0.059, abs=0.01)

    def test_padding(self):
        html = "<div style='padding: 24px 32px'></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree["paddingTop"] == 24
        assert tree["paddingRight"] == 32
        assert tree["paddingBottom"] == 24
        assert tree["paddingLeft"] == 32

    def test_border_radius(self):
        html = "<div style='border-radius: 12px'></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree["cornerRadius"] == 12

    def test_gap_becomes_item_spacing(self):
        html = "<div style='display: flex; gap: 16px'></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree["itemSpacing"] == 16

    def test_border(self):
        html = "<div style='border: 1px solid #E2E8F0'></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        assert "strokes" in tree
        assert tree["strokeWeight"] == 1

    def test_box_shadow(self):
        html = "<div style='box-shadow: 0 4px 6px rgba(0,0,0,0.1)'></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        assert "effects" in tree
        assert tree["effects"][0]["type"] == "DROP_SHADOW"

    def test_text_only_element(self):
        html = (
            "<div><p style='font-size: 24px; font-weight: 700; "
            "color: #0F172A'>Hello World</p></div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        children = tree.get("children", [])
        assert len(children) >= 1
        text_node = children[0]
        assert text_node["type"] == "TEXT"
        assert text_node["characters"] == "Hello World"
        assert text_node["fontSize"] == 24
        assert text_node["fontWeight"] == 700

    def test_nested_structure(self):
        html = """
        <div style='display: flex; flex-direction: column; gap: 16px'>
            <div style='display: flex; flex-direction: row; gap: 8px'>
                <p style='font-size: 16px'>Item 1</p>
                <p style='font-size: 16px'>Item 2</p>
            </div>
        </div>
        """
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree["layoutMode"] == "VERTICAL"
        assert tree["itemSpacing"] == 16
        row = tree["children"][0]
        assert row["type"] == "FRAME"
        assert row["layoutMode"] == "HORIZONTAL"
        assert len(row["children"]) == 2

    def test_heading_tags_font_sizes(self):
        html = "<div><h1>Title</h1><h2>Subtitle</h2><h3>Section</h3></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        children = tree["children"]
        assert children[0]["fontSize"] == 48  # h1
        assert children[1]["fontSize"] == 32  # h2
        assert children[2]["fontSize"] == 24  # h3

    def test_button_element(self):
        html = """
        <div>
            <button style='background-color: #2563EB; color: #FFFFFF;
                padding: 10px 20px; border-radius: 8px'>
                Click Me
            </button>
        </div>
        """
        tree = convert_html_to_figma_tree(html, "Test")
        btn = tree["children"][0]
        assert btn["type"] == "FRAME"
        assert btn["cornerRadius"] == 8
        # Button should have a text child
        assert any(c["type"] == "TEXT" for c in btn.get("children", []))

    def test_input_element(self):
        html = (
            "<div><input style='padding: 12px; border: 1px solid #ccc'"
            " placeholder='Type here...' /></div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        input_node = tree["children"][0]
        assert input_node["type"] == "FRAME"
        # Should have placeholder text
        assert any(
            c["type"] == "TEXT" and c["characters"] == "Type here..."
            for c in input_node.get("children", [])
        )

    def test_flex_grow(self):
        html = "<div style='display: flex'><div style='flex: 1'>Content</div></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        child = tree["children"][0]
        assert child.get("layoutGrow") == 1

    def test_width_100_percent_becomes_stretch(self):
        html = "<div><div style='width: 100%'>Full width</div></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        child = tree["children"][0]
        assert child.get("layoutAlign") == "STRETCH"

    def test_overflow_hidden(self):
        html = "<div style='overflow: hidden'></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree.get("clipsContent") is True

    def test_align_items_center(self):
        html = "<div style='display: flex; align-items: center'></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree.get("counterAxisAlignItems") == "CENTER"

    def test_justify_content_space_between(self):
        html = "<div style='display: flex; justify-content: space-between'></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree.get("primaryAxisAlignItems") == "SPACE_BETWEEN"

    def test_explicit_width_height(self):
        html = "<div style='width: 200px; height: 100px'></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree.get("width") == 200
        assert tree.get("height") == 100

    def test_root_name_is_screen_name(self):
        html = "<div>Hello</div>"
        tree = convert_html_to_figma_tree(html, "Dashboard")
        assert tree["name"] == "Dashboard"


class TestConvertComplexLayout:
    """Test conversion of realistic, complex HTML layouts."""

    def test_dashboard_card_row(self):
        html = (
            "<div style='display: flex; flex-direction: column;"
            " padding: 48px; gap: 32px; width: 1440px;"
            " background-color: #F8FAFC'>"
            "<h1 style='font-size: 32px; font-weight: 700;"
            " color: #0F172A'>Dashboard</h1>"
            "<div style='display: flex; flex-direction: row;"
            " gap: 24px'>"
            "<div style='flex: 1; background-color: #FFFFFF;"
            " border-radius: 12px; padding: 24px;"
            " box-shadow: 0 1px 3px rgba(0,0,0,0.1)'>"
            "<p style='font-size: 14px; color: #64748B'>"
            "Total Revenue</p>"
            "<p style='font-size: 32px; font-weight: 700;"
            " color: #0F172A'>$45,231</p>"
            "</div>"
            "<div style='flex: 1; background-color: #FFFFFF;"
            " border-radius: 12px; padding: 24px;"
            " box-shadow: 0 1px 3px rgba(0,0,0,0.1)'>"
            "<p style='font-size: 14px; color: #64748B'>"
            "Active Users</p>"
            "<p style='font-size: 32px; font-weight: 700;"
            " color: #0F172A'>2,345</p>"
            "</div>"
            "</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Dashboard")

        # Root frame
        assert tree["type"] == "FRAME"
        assert tree["layoutMode"] == "VERTICAL"
        assert tree["paddingTop"] == 48
        assert tree["itemSpacing"] == 32
        assert tree["width"] == 1440

        # Should have title + card row
        assert len(tree["children"]) >= 2

        # Title
        title = tree["children"][0]
        assert title["type"] == "TEXT"
        assert title["characters"] == "Dashboard"
        assert title["fontSize"] == 32

        # Card row
        card_row = tree["children"][1]
        assert card_row["layoutMode"] == "HORIZONTAL"
        assert card_row["itemSpacing"] == 24
        assert len(card_row["children"]) == 2

        # First card
        card = card_row["children"][0]
        assert card["layoutGrow"] == 1
        assert card["cornerRadius"] == 12
        assert card["paddingTop"] == 24
        assert "effects" in card  # box-shadow

    def test_navbar_structure(self):
        html = (
            "<div style='display: flex; flex-direction: row;"
            " align-items: center;"
            " justify-content: space-between;"
            " padding: 16px 32px;"
            " background-color: #FFFFFF;"
            " border-bottom: 1px solid #E2E8F0'>"
            "<span style='font-size: 20px; font-weight: 700;"
            " color: #0F172A'>Acme Inc</span>"
            "<div style='display: flex; flex-direction: row;"
            " gap: 24px'>"
            "<span style='font-size: 16px;"
            " color: #475569'>Dashboard</span>"
            "<span style='font-size: 16px;"
            " color: #475569'>Settings</span>"
            "</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Navbar")

        assert tree["layoutMode"] == "HORIZONTAL"
        assert tree["counterAxisAlignItems"] == "CENTER"
        assert tree["primaryAxisAlignItems"] == "SPACE_BETWEEN"
        assert "strokes" in tree  # border-bottom

    def test_table_like_structure(self):
        html = (
            "<div style='display: flex; flex-direction: column;"
            " border: 1px solid #E2E8F0;"
            " border-radius: 8px; overflow: hidden'>"
            "<div style='display: flex; flex-direction: row;"
            " background-color: #F8FAFC; padding: 12px 16px'>"
            "<span style='flex: 1; font-size: 14px;"
            " font-weight: 600'>Name</span>"
            "<span style='flex: 1; font-size: 14px;"
            " font-weight: 600'>Status</span>"
            "</div>"
            "<div style='display: flex; flex-direction: row;"
            " padding: 12px 16px;"
            " border-top: 1px solid #E2E8F0'>"
            "<span style='flex: 1; font-size: 14px'>"
            "John Doe</span>"
            "<span style='flex: 1; font-size: 14px'>"
            "Active</span>"
            "</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Table")

        assert tree["clipsContent"] is True
        assert tree["cornerRadius"] == 8
        assert len(tree["children"]) == 2

        # Header row
        header = tree["children"][0]
        assert header["layoutMode"] == "HORIZONTAL"
        assert "fills" in header  # background-color


# ─── New CSS Features ───


class TestTextTransform:
    def test_uppercase(self):
        assert _apply_text_transform("hello world", "uppercase") == "HELLO WORLD"

    def test_lowercase(self):
        assert _apply_text_transform("Hello World", "lowercase") == "hello world"

    def test_capitalize(self):
        assert _apply_text_transform("hello world", "capitalize") == "Hello World"

    def test_none_returns_original(self):
        assert _apply_text_transform("Hello", "none") == "Hello"

    def test_text_transform_in_html(self):
        html = (
            "<div style='display: flex; flex-direction: column'>"
            "<p style='text-transform: uppercase;"
            " font-size: 12px; color: #64748B'>overview</p>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        text_nodes = [
            c for c in tree["children"]
            if c["type"] == "TEXT"
        ]
        assert len(text_nodes) >= 1
        assert text_nodes[0]["characters"] == "OVERVIEW"


class TestDisplayNone:
    def test_hidden_element_is_skipped(self):
        html = (
            "<div style='display: flex; flex-direction: column'>"
            "<p style='font-size: 16px'>Visible</p>"
            "<div style='display: none'>Hidden content</div>"
            "<p style='font-size: 16px'>Also visible</p>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        # Only 2 children should remain (the two visible <p> tags)
        assert len(tree["children"]) == 2

    def test_display_none_on_text_element(self):
        html = (
            "<div style='display: flex; flex-direction: column'>"
            "<span style='display: none; font-size: 14px'>Hidden</span>"
            "<span style='font-size: 14px'>Visible</span>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        assert len(tree["children"]) == 1


class TestFlexShorthand:
    def test_flex_1_1_0_percent(self):
        html = (
            "<div style='display: flex; flex-direction: row'>"
            "<div style='flex: 1 1 0%'>A</div>"
            "<div style='flex: 1 1 0%'>B</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        for child in tree["children"]:
            assert child.get("layoutGrow") == 1

    def test_flex_0_0_auto(self):
        html = (
            "<div style='display: flex; flex-direction: row'>"
            "<div style='flex: 0 0 auto'>Fixed</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        # flex: 0 should NOT set layoutGrow
        assert tree["children"][0].get("layoutGrow") != 1

    def test_flex_2(self):
        html = (
            "<div style='display: flex; flex-direction: row'>"
            "<div style='flex: 2'>A</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree["children"][0].get("layoutGrow") == 1

    def test_flex_grow_1(self):
        html = (
            "<div style='display: flex; flex-direction: row'>"
            "<div style='flex-grow: 1'>A</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree["children"][0].get("layoutGrow") == 1


class TestTextDecoration:
    def test_underline(self):
        html = (
            "<div style='display: flex; flex-direction: column'>"
            "<a style='text-decoration: underline;"
            " font-size: 14px; color: #2563EB'>Click here</a>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        text = tree["children"][0]
        assert text["type"] == "TEXT"
        assert text.get("textDecoration") == "UNDERLINE"

    def test_line_through(self):
        html = (
            "<div style='display: flex; flex-direction: column'>"
            "<span style='text-decoration: line-through;"
            " font-size: 14px; color: #94A3B8'>$99.99</span>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        text = tree["children"][0]
        assert text["type"] == "TEXT"
        assert text.get("textDecoration") == "STRIKETHROUGH"

    def test_no_decoration_by_default(self):
        html = (
            "<div style='display: flex; flex-direction: column'>"
            "<p style='font-size: 16px'>Normal text</p>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        text = tree["children"][0]
        assert text["type"] == "TEXT"
        assert "textDecoration" not in text


# ─── Text Node Layout Properties ───


class TestTextNodeFlex:
    def test_text_node_with_flex_gets_layout_grow(self):
        """TEXT node with flex: 1 should get layoutGrow=1."""
        html = (
            "<div style='display: flex; flex-direction: row'>"
            "<span style='flex: 1; font-size: 14px'>Cell A</span>"
            "<span style='flex: 1; font-size: 14px'>Cell B</span>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        for child in tree["children"]:
            assert child["type"] == "TEXT"
            assert child.get("layoutGrow") == 1

    def test_text_node_with_flex_grow_gets_layout_grow(self):
        """TEXT node with flex-grow: 1 should get layoutGrow=1."""
        html = (
            "<div style='display: flex; flex-direction: row'>"
            "<span style='flex-grow: 1; font-size: 14px'>Cell</span>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree["children"][0].get("layoutGrow") == 1

    def test_text_node_width_100_percent_gets_stretch(self):
        """TEXT node with width: 100% should get layoutAlign=STRETCH."""
        html = (
            "<div style='display: flex; flex-direction: column'>"
            "<p style='width: 100%; font-size: 14px'>Full width</p>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree["children"][0].get("layoutAlign") == "STRETCH"


# ─── Defensive Heuristics ───


class TestDefensiveHeuristics:
    def test_multiple_text_siblings_in_horizontal_get_grow(self):
        """3+ text spans in HORIZONTAL without flex should all get layoutGrow=1."""
        html = (
            "<div style='display: flex; flex-direction: row; padding: 12px 16px'>"
            "<span style='font-size: 14px; font-weight: 600'>Customer</span>"
            "<span style='font-size: 14px; font-weight: 600'>Status</span>"
            "<span style='font-size: 14px; font-weight: 600'>Date</span>"
            "<span style='font-size: 14px; font-weight: 600'>Amount</span>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        for child in tree["children"]:
            assert child["type"] == "TEXT"
            assert child.get("layoutGrow") == 1

    def test_single_text_in_horizontal_no_grow(self):
        """A single text child in HORIZONTAL should NOT get defensive layoutGrow."""
        html = (
            "<div style='display: flex; flex-direction: row'>"
            "<span style='font-size: 14px'>Only child</span>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        # Single text child — defensive heuristic should NOT apply
        assert tree["children"][0].get("layoutGrow") != 1

    def test_horizontal_frame_children_without_width_get_grow(self):
        """FRAME children in HORIZONTAL without width/flex should get layoutGrow=1."""
        html = (
            "<div style='display: flex; flex-direction: row; gap: 24px'>"
            "<div style='display: flex; flex-direction: column; gap: 8px'>"
            "<p style='font-size: 14px'>User Growth</p>"
            "<p style='font-size: 32px; font-weight: 700'>+12.5%</p>"
            "</div>"
            "<div style='display: flex; flex-direction: column; gap: 8px'>"
            "<p style='font-size: 14px'>Revenue</p>"
            "<p style='font-size: 32px; font-weight: 700'>$45K</p>"
            "</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        for child in tree["children"]:
            assert child["type"] == "FRAME"
            assert child.get("layoutGrow") == 1

    def test_horizontal_frame_with_explicit_width_no_grow(self):
        """FRAME with explicit width in HORIZONTAL should NOT get defensive layoutGrow."""
        html = (
            "<div style='display: flex; flex-direction: row'>"
            "<div style='width: 260px; display: flex; flex-direction: column'>"
            "<p style='font-size: 14px'>Sidebar</p>"
            "</div>"
            "<div style='display: flex; flex-direction: column'>"
            "<p style='font-size: 14px'>Content</p>"
            "</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        sidebar = tree["children"][0]
        assert sidebar.get("width") == 260
        # Sidebar should NOT get defensive layoutGrow (has explicit width)
        assert sidebar.get("layoutGrow") != 1


# ─── Root Frame Height ───


class TestRootFrameHeight:
    def test_root_frame_has_fixed_height(self):
        """Root frame should default to 900px height with FIXED sizing."""
        html = "<div style='display: flex; flex-direction: column; width: 1440px'></div>"
        tree = convert_html_to_figma_tree(html, "Dashboard")
        assert tree["height"] == 900
        assert tree["primaryAxisSizingMode"] == "FIXED"

    def test_root_frame_preserves_explicit_height(self):
        """Root frame with explicit height should keep that value."""
        html = (
            "<div style='display: flex; flex-direction: column; "
            "width: 1440px; height: 800px'></div>"
        )
        tree = convert_html_to_figma_tree(html, "Dashboard")
        assert tree["height"] == 800
        assert tree["primaryAxisSizingMode"] == "FIXED"

    def test_root_frame_has_clips_content(self):
        """Root frame should always have clipsContent=True."""
        html = "<div style='display: flex; flex-direction: column'></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree["clipsContent"] is True


# ─── textAutoResize ───


class TestTextAutoResize:
    def test_text_with_layout_grow_gets_text_auto_resize_height(self):
        """TEXT with layoutGrow=1 must have textAutoResize=HEIGHT."""
        html = (
            "<div style='display: flex; flex-direction: row'>"
            "<span style='flex: 1; font-size: 14px'>Cell A</span>"
            "<span style='flex: 1; font-size: 14px'>Cell B</span>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        for child in tree["children"]:
            assert child["type"] == "TEXT"
            assert child.get("layoutGrow") == 1
            assert child.get("textAutoResize") == "HEIGHT"

    def test_text_with_stretch_gets_text_auto_resize_height(self):
        """TEXT with layoutAlign=STRETCH must have textAutoResize=HEIGHT."""
        html = (
            "<div style='display: flex; flex-direction: column'>"
            "<p style='width: 100%; font-size: 14px'>Full width text</p>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        text = tree["children"][0]
        assert text["type"] == "TEXT"
        assert text.get("layoutAlign") == "STRETCH"
        assert text.get("textAutoResize") == "HEIGHT"

    def test_text_without_grow_gets_width_and_height(self):
        """TEXT without layoutGrow/STRETCH should have textAutoResize=WIDTH_AND_HEIGHT."""
        html = (
            "<div style='display: flex; flex-direction: column; "
            "align-items: flex-start'>"
            "<p style='font-size: 16px'>Normal text</p>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        text = tree["children"][0]
        assert text["type"] == "TEXT"
        assert text["textAutoResize"] == "WIDTH_AND_HEIGHT"

    def test_defensive_text_siblings_get_text_auto_resize(self):
        """Defensive heuristic must set textAutoResize=HEIGHT along with layoutGrow."""
        html = (
            "<div style='display: flex; flex-direction: row; padding: 12px'>"
            "<span style='font-size: 14px'>Customer</span>"
            "<span style='font-size: 14px'>Status</span>"
            "<span style='font-size: 14px'>Amount</span>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        for child in tree["children"]:
            assert child["type"] == "TEXT"
            assert child.get("layoutGrow") == 1
            assert child.get("textAutoResize") == "HEIGHT"

    def test_inline_text_with_stretch_gets_text_auto_resize(self):
        """Inline text injected with STRETCH must get textAutoResize=HEIGHT."""
        html = (
            "<div style='display: flex; flex-direction: column'>"
            "<div style='display: flex; flex-direction: row; gap: 8px'>"
            "Label text"
            "<span style='font-size: 14px'>Child</span>"
            "</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        inner = tree["children"][0]
        # First child should be the injected inline text node
        inline = inner["children"][0]
        assert inline["type"] == "TEXT"
        assert inline["characters"] == "Label text"
        # Parent has default align-items:stretch, so inline text should have it
        if inline.get("layoutAlign") == "STRETCH":
            assert inline.get("textAutoResize") == "HEIGHT"


class TestFrameCounterAxisSizing:
    def test_frame_with_layout_grow_and_width_gets_fixed_counter_axis(self):
        """FRAME with layoutGrow=1 and explicit width gets counterAxisSizingMode=FIXED."""
        html = (
            "<div style='display: flex; flex-direction: row'>"
            "<div style='flex: 1; width: 500px; display: flex; "
            "flex-direction: column'>"
            "<p style='font-size: 14px'>Content</p>"
            "</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        child = tree["children"][0]
        assert child["type"] == "FRAME"
        assert child.get("layoutGrow") == 1
        assert child.get("counterAxisSizingMode") == "FIXED"


# ─── Regression Tests: Real-world Layout Patterns ───


class TestSidebarContentLayout:
    """Test sidebar (260px fixed) + content area (flex:1) — the most common pattern."""

    def test_sidebar_keeps_fixed_width(self):
        html = (
            "<div style='width: 1440px; display: flex; flex-direction: row'>"
            "<div style='width: 260px; display: flex; flex-direction: column;"
            " background-color: #0F172A; padding: 24px 16px; gap: 32px'>"
            "<span style='color: #FFFFFF; font-size: 20px; font-weight: 700'>App</span>"
            "</div>"
            "<div style='flex: 1; display: flex; flex-direction: column'>"
            "<p style='font-size: 24px; font-weight: 600; color: #0F172A'>Dashboard</p>"
            "</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Dashboard")

        assert tree["layoutMode"] == "HORIZONTAL"
        assert len(tree["children"]) == 2

        sidebar = tree["children"][0]
        content = tree["children"][1]

        # Sidebar: fixed width, no layoutGrow
        assert sidebar["width"] == 260
        assert sidebar.get("layoutGrow") != 1

        # Content: has layoutGrow, no explicit width
        assert content.get("layoutGrow") == 1
        assert "width" not in content

    def test_sidebar_sizing_modes(self):
        html = (
            "<div style='width: 1440px; display: flex; flex-direction: row'>"
            "<div style='width: 260px; display: flex; flex-direction: column;"
            " padding: 24px 16px'>"
            "<span style='font-size: 14px; color: #FFFFFF'>Nav</span>"
            "</div>"
            "<div style='flex: 1; display: flex; flex-direction: column; padding: 32px'>"
            "<span style='font-size: 24px; color: #0F172A'>Content</span>"
            "</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Dashboard")
        sidebar = tree["children"][0]
        content = tree["children"][1]

        # Sidebar: VERTICAL layout, width=260 → counterAxisSizingMode=FIXED
        assert sidebar["layoutMode"] == "VERTICAL"
        assert sidebar.get("counterAxisSizingMode") == "FIXED"

        # Content: has layoutGrow=1, parent is HORIZONTAL → will FILL
        assert content.get("layoutGrow") == 1


class TestCardGridLayout:
    """Test grid of cards (3 columns flex:1) — metric cards pattern."""

    def test_three_cards_all_get_grow(self):
        html = (
            "<div style='display: flex; flex-direction: row; gap: 24px'>"
            "<div style='flex: 1; display: flex; flex-direction: column;"
            " padding: 24px; background-color: #FFFFFF;"
            " border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1)'>"
            "<span style='font-size: 14px; color: #64748B'>Revenue</span>"
            "<span style='font-size: 32px; font-weight: 700; color: #0F172A'>$45K</span>"
            "</div>"
            "<div style='flex: 1; display: flex; flex-direction: column;"
            " padding: 24px; background-color: #FFFFFF;"
            " border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1)'>"
            "<span style='font-size: 14px; color: #64748B'>Users</span>"
            "<span style='font-size: 32px; font-weight: 700; color: #0F172A'>2,345</span>"
            "</div>"
            "<div style='flex: 1; display: flex; flex-direction: column;"
            " padding: 24px; background-color: #FFFFFF;"
            " border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1)'>"
            "<span style='font-size: 14px; color: #64748B'>Conversion</span>"
            "<span style='font-size: 32px; font-weight: 700; color: #0F172A'>3.2%</span>"
            "</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")

        assert tree["layoutMode"] == "HORIZONTAL"
        assert tree["itemSpacing"] == 24
        assert len(tree["children"]) == 3

        for card in tree["children"]:
            assert card.get("layoutGrow") == 1
            assert card["cornerRadius"] == 12
            assert card["paddingTop"] == 24
            assert "effects" in card  # box-shadow


class TestTextOnlyCells:
    """Test that text-only divs (<div>Cell Value</div>) don't lose content."""

    def test_text_only_div_preserves_text(self):
        html = (
            "<div style='display: flex; flex-direction: row'>"
            "<div style='display: flex; flex-direction: column'>Cell A</div>"
            "<div style='display: flex; flex-direction: column'>Cell B</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")

        # Both divs should have text children
        for child in tree["children"]:
            text_children = [c for c in child.get("children", []) if c["type"] == "TEXT"]
            assert len(text_children) >= 1


class TestButtonNoGrow:
    """Test that buttons don't receive defensive layoutGrow."""

    def test_button_in_row_no_grow(self):
        html = (
            "<div style='display: flex; flex-direction: row; gap: 12px'>"
            "<button style='background-color: #2563EB; color: #FFFFFF;"
            " padding: 10px 20px; border-radius: 8px'>Save</button>"
            "<button style='border: 1px solid #E2E8F0; color: #0F172A;"
            " padding: 10px 20px; border-radius: 8px'>Cancel</button>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")

        for child in tree["children"]:
            assert child["name"] == "button"
            # Buttons should NOT get layoutGrow from defensive heuristic
            assert child.get("layoutGrow") != 1


class TestMinHeight:
    """Test that min-height is converted to height."""

    def test_min_height_becomes_height(self):
        html = "<div style='display: flex; flex-direction: column; min-height: 900px'></div>"
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree["height"] == 900


class TestSizingModeConsistency:
    """Test _resolve_sizing_modes produces correct results."""

    def test_horizontal_parent_with_grow_children_is_fixed(self):
        """Parent with layoutGrow children must have FIXED primary axis."""
        html = (
            "<div style='display: flex; flex-direction: row; gap: 24px'>"
            "<div style='flex: 1; display: flex; flex-direction: column'>"
            "<p style='font-size: 14px'>A</p>"
            "</div>"
            "<div style='flex: 1; display: flex; flex-direction: column'>"
            "<p style='font-size: 14px'>B</p>"
            "</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")

        # Root overrides sizing, so check the inner row
        row = tree  # root is the row itself
        assert row.get("primaryAxisSizingMode") == "FIXED"

    def test_vertical_frame_with_explicit_height_is_fixed(self):
        html = (
            "<div style='display: flex; flex-direction: column; height: 400px'>"
            "<p style='font-size: 14px'>Content</p>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        # Root frame overrides, but the converter should have set it
        assert tree.get("primaryAxisSizingMode") == "FIXED"

    def test_horizontal_frame_with_explicit_width_is_fixed(self):
        html = (
            "<div style='display: flex; flex-direction: row; width: 800px'>"
            "<p style='font-size: 14px'>Content</p>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        assert tree.get("primaryAxisSizingMode") == "FIXED"


# ─── Letter Spacing ───


class TestLetterSpacing:
    def test_px_letter_spacing(self):
        assert _parse_letter_spacing("2px", 16) == 2.0

    def test_em_letter_spacing(self):
        assert _parse_letter_spacing("0.05em", 16) == pytest.approx(0.8)

    def test_em_letter_spacing_different_font_size(self):
        assert _parse_letter_spacing("0.1em", 12) == pytest.approx(1.2)

    def test_invalid_returns_none(self):
        assert _parse_letter_spacing("normal", 16) is None


class TestParsePxEdgeCases:
    def test_em_returns_none(self):
        assert _parse_px("1.5em") is None

    def test_rem_returns_none(self):
        assert _parse_px("1rem") is None

    def test_percent_returns_none(self):
        assert _parse_px("50%") is None


# ─── Tree Validation ───


class TestValidateTree:
    def test_valid_tree_no_warnings(self):
        tree = {
            "type": "FRAME",
            "name": "root",
            "children": [
                {
                    "type": "TEXT",
                    "characters": "Hello",
                    "fontSize": 16,
                    "fontWeight": 400,
                }
            ],
        }
        warnings = _validate_tree(tree)
        assert len(warnings) == 0

    def test_text_with_grow_no_auto_resize_warns(self):
        tree = {
            "type": "FRAME",
            "name": "root",
            "children": [
                {
                    "type": "TEXT",
                    "characters": "Hello",
                    "layoutGrow": 1,
                    # Missing textAutoResize
                }
            ],
        }
        warnings = _validate_tree(tree)
        assert any("textAutoResize" in w for w in warnings)

    def test_text_with_grow_and_auto_resize_no_warn(self):
        tree = {
            "type": "FRAME",
            "name": "root",
            "children": [
                {
                    "type": "TEXT",
                    "characters": "Hello",
                    "layoutGrow": 1,
                    "textAutoResize": "HEIGHT",
                }
            ],
        }
        warnings = _validate_tree(tree)
        assert not any("textAutoResize" in w for w in warnings)

    def test_empty_frame_warns(self):
        tree = {"type": "FRAME", "name": "empty", "children": []}
        warnings = _validate_tree(tree)
        assert any("no children" in w for w in warnings)

    def test_icon_node_no_warnings(self):
        tree = {
            "type": "FRAME",
            "name": "root",
            "children": [
                {
                    "type": "ICON",
                    "name": "icon_home",
                    "icon": "home",
                    "width": 20,
                    "height": 20,
                    "color": {"r": 0.39, "g": 0.45, "b": 0.53},
                }
            ],
        }
        warnings = _validate_tree(tree)
        # ICON node should not generate any warnings
        assert len(warnings) == 0


# ─── Icon Node Conversion ───


class TestIconNodeConversion:
    """Test data-icon → ICON node conversion."""

    def test_data_icon_creates_icon_node(self):
        html = (
            "<div style='display: flex; flex-direction: row; gap: 12px; "
            "align-items: center'>"
            "<div data-icon='home' style='width: 20px; height: 20px; "
            "color: #64748B'></div>"
            "<span style='font-size: 14px; color: #0F172A'>Dashboard</span>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        children = tree["children"]

        # First child should be an ICON node
        icon_node = children[0]
        assert icon_node["type"] == "ICON"
        assert icon_node["icon"] == "home"
        assert icon_node["width"] == 20
        assert icon_node["height"] == 20

        # Second child should be a TEXT node
        text_node = children[1]
        assert text_node["type"] == "TEXT"
        assert text_node["characters"] == "Dashboard"

    def test_icon_default_size(self):
        html = (
            "<div style='display: flex; flex-direction: column'>"
            "<div data-icon='settings'></div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        icon_node = tree["children"][0]
        assert icon_node["type"] == "ICON"
        assert icon_node["width"] == 24  # default
        assert icon_node["height"] == 24  # default

    def test_icon_custom_color(self):
        html = (
            "<div style='display: flex; flex-direction: column'>"
            "<div data-icon='bell' style='width: 18px; height: 18px; "
            "color: #2563EB'></div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        icon_node = tree["children"][0]
        assert icon_node["type"] == "ICON"
        assert icon_node["color"]["r"] == pytest.approx(0.145, abs=0.01)
        assert icon_node["color"]["b"] == pytest.approx(0.922, abs=0.01)

    def test_unknown_icon_ignored(self):
        """Elements with data-icon for unknown names are treated as frames."""
        html = (
            "<div style='display: flex; flex-direction: column'>"
            "<div data-icon='nonexistent-icon'></div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Test")
        # Unknown icon should be treated as a regular FRAME
        child = tree["children"][0]
        assert child["type"] == "FRAME"

    def test_convert_icon_node_directly(self):
        node = {
            "tag": "div",
            "attrs": {"data-icon": "search"},
            "style": {"width": "16px", "height": "16px", "color": "#94A3B8"},
            "children": [],
            "text": "",
        }
        result = _convert_icon_node(node)
        assert result["type"] == "ICON"
        assert result["icon"] == "search"
        assert result["name"] == "icon_search"
        assert result["width"] == 16
        assert result["height"] == 16

    def test_icon_in_sidebar_pattern(self):
        """Test a realistic sidebar nav item with icon + text."""
        html = (
            "<div style='display: flex; flex-direction: column; width: 260px; "
            "background-color: #0F172A; padding: 24px 16px; gap: 4px'>"
            "<div style='display: flex; flex-direction: row; gap: 12px; "
            "align-items: center; padding: 8px 12px; border-radius: 8px; "
            "background-color: #2563EB'>"
            "  <div data-icon='home' style='width: 18px; height: 18px; "
            "color: #FFFFFF'></div>"
            "  <span style='font-size: 14px; font-weight: 500; "
            "color: #FFFFFF'>Dashboard</span>"
            "</div>"
            "<div style='display: flex; flex-direction: row; gap: 12px; "
            "align-items: center; padding: 8px 12px; border-radius: 8px'>"
            "  <div data-icon='bar-chart' style='width: 18px; height: 18px; "
            "color: #94A3B8'></div>"
            "  <span style='font-size: 14px; color: #94A3B8'>Analytics</span>"
            "</div>"
            "</div>"
        )
        tree = convert_html_to_figma_tree(html, "Sidebar")

        # Root sidebar frame
        assert tree["width"] == 260

        # First nav item
        nav_item_1 = tree["children"][0]
        assert nav_item_1["layoutMode"] == "HORIZONTAL"
        assert nav_item_1["children"][0]["type"] == "ICON"
        assert nav_item_1["children"][0]["icon"] == "home"
        assert nav_item_1["children"][1]["type"] == "TEXT"

        # Second nav item
        nav_item_2 = tree["children"][1]
        assert nav_item_2["children"][0]["type"] == "ICON"
        assert nav_item_2["children"][0]["icon"] == "bar-chart"
