"""Lucide icon catalog — icon names available for the HTML generator.

This module provides the list of supported Lucide icon names that the LLM
can reference via data-icon="name" in the generated HTML. The actual SVG
data is bundled in the Figma plugin (figma-plugin/src/icons.ts).
"""

# All available Lucide icon names, organized by category.
# Keep in sync with figma-plugin/src/icons.ts.

ICON_CATEGORIES: dict[str, list[str]] = {
    "navigation": [
        "home",
        "menu",
        "x",
        "chevron-down",
        "chevron-right",
        "chevron-left",
        "chevron-up",
        "arrow-left",
        "arrow-right",
        "arrow-up",
        "arrow-down",
        "external-link",
        "log-out",
        "log-in",
    ],
    "actions": [
        "search",
        "plus",
        "minus",
        "edit",
        "trash",
        "copy",
        "filter",
        "more-horizontal",
        "more-vertical",
        "download",
        "upload",
        "refresh",
    ],
    "user": [
        "user",
        "users",
        "shield",
        "lock",
        "key",
    ],
    "communication": [
        "bell",
        "mail",
        "message-square",
        "phone",
        "globe",
    ],
    "charts": [
        "bar-chart",
        "line-chart",
        "pie-chart",
        "trending-up",
        "trending-down",
        "activity",
        "zap",
        "target",
    ],
    "commerce": [
        "dollar-sign",
        "credit-card",
        "shopping-cart",
        "shopping-bag",
        "package",
        "wallet",
        "receipt",
    ],
    "files": [
        "file",
        "file-text",
        "folder",
        "image",
        "paperclip",
        "link",
    ],
    "status": [
        "check",
        "check-circle",
        "alert-circle",
        "alert-triangle",
        "info",
        "x-circle",
    ],
    "ui": [
        "settings",
        "eye",
        "eye-off",
        "bookmark",
        "star",
        "heart",
    ],
    "time": [
        "calendar",
        "clock",
    ],
    "misc": [
        "map-pin",
        "layers",
        "layout",
        "grid",
        "sliders",
        "inbox",
        "cloud",
        "database",
        "help-circle",
        "share",
        "printer",
        "circle-dot",
        "rocket",
        "sparkles",
    ],
}

# Flat list of all available icon names
ALL_ICON_NAMES: list[str] = [
    name for names in ICON_CATEGORIES.values() for name in names
]


def get_icon_reference_for_prompt() -> str:
    """Generate a formatted icon reference section for the LLM prompt."""
    lines = ["## Available Icons (Lucide)\n"]
    lines.append(
        "Use `data-icon='icon-name'` on a `<div>` to render a Lucide icon. "
        "Set width/height for size and color for stroke color.\n"
    )
    lines.append("```html")
    lines.append(
        "<div data-icon='home' "
        "style='width: 20px; height: 20px; color: #64748B'></div>"
    )
    lines.append("```\n")

    for category, names in ICON_CATEGORIES.items():
        lines.append(f"**{category.title()}**: {', '.join(names)}")

    return "\n".join(lines)
