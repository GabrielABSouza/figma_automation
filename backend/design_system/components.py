"""shadcn/ui Component Catalog — production-quality HTML templates.

These templates are injected into the LLM prompt so it composes screens
from real component patterns instead of generating from scratch.

Each component follows shadcn/ui visual language:
- Precise spacing on 4/8px grid
- Consistent border-radius (8px buttons, 12px cards)
- Subtle shadows (0 1px 3px for cards)
- Lucide icons via data-icon attribute
- Inter font family exclusively
"""

COMPONENT_CATALOG: dict[str, dict[str, str]] = {
    # ── Navigation ──
    "sidebar": {
        "description": "Dark sidebar with logo, nav groups, and user section",
        "html": (
            "<div style='width: 260px; display: flex; flex-direction: column; "
            "background-color: #0F172A; padding: 0px; gap: 0px; height: 900px; "
            "overflow: hidden'>"
            "  <div style='display: flex; flex-direction: row; gap: 12px; "
            "align-items: center; padding: 24px 20px 20px 20px'>"
            "    <div style='width: 32px; height: 32px; background-color: #2563EB; "
            "border-radius: 8px; display: flex; align-items: center; "
            "justify-content: center'>"
            "      <span style='color: #FFFFFF; font-size: 14px; font-weight: 700'>A</span>"
            "    </div>"
            "    <span style='color: #FFFFFF; font-size: 16px; font-weight: 600'>Acme Inc</span>"
            "  </div>"
            "  <div style='display: flex; flex-direction: column; gap: 2px; "
            "padding: 0px 12px; flex: 1'>"
            "    <span style='font-size: 11px; font-weight: 500; color: #64748B; "
            "padding: 8px 8px 4px 8px; letter-spacing: 0.05em; "
            "text-transform: uppercase'>Main</span>"
            "    <div style='display: flex; flex-direction: row; gap: 12px; "
            "align-items: center; padding: 8px 12px; border-radius: 8px; "
            "background-color: #2563EB'>"
            "      <div data-icon='home' style='width: 18px; height: 18px; "
            "color: #FFFFFF'></div>"
            "      <span style='font-size: 14px; font-weight: 500; "
            "color: #FFFFFF'>Dashboard</span>"
            "    </div>"
            "    <div style='display: flex; flex-direction: row; gap: 12px; "
            "align-items: center; padding: 8px 12px; border-radius: 8px'>"
            "      <div data-icon='bar-chart' style='width: 18px; height: 18px; "
            "color: #94A3B8'></div>"
            "      <span style='font-size: 14px; font-weight: 400; "
            "color: #94A3B8'>Analytics</span>"
            "    </div>"
            "    <div style='display: flex; flex-direction: row; gap: 12px; "
            "align-items: center; padding: 8px 12px; border-radius: 8px'>"
            "      <div data-icon='users' style='width: 18px; height: 18px; "
            "color: #94A3B8'></div>"
            "      <span style='font-size: 14px; font-weight: 400; "
            "color: #94A3B8'>Customers</span>"
            "    </div>"
            "    <div style='display: flex; flex-direction: row; gap: 12px; "
            "align-items: center; padding: 8px 12px; border-radius: 8px'>"
            "      <div data-icon='package' style='width: 18px; height: 18px; "
            "color: #94A3B8'></div>"
            "      <span style='font-size: 14px; font-weight: 400; "
            "color: #94A3B8'>Products</span>"
            "    </div>"
            "    <span style='font-size: 11px; font-weight: 500; color: #64748B; "
            "padding: 16px 8px 4px 8px; letter-spacing: 0.05em; "
            "text-transform: uppercase'>Settings</span>"
            "    <div style='display: flex; flex-direction: row; gap: 12px; "
            "align-items: center; padding: 8px 12px; border-radius: 8px'>"
            "      <div data-icon='settings' style='width: 18px; height: 18px; "
            "color: #94A3B8'></div>"
            "      <span style='font-size: 14px; font-weight: 400; "
            "color: #94A3B8'>Settings</span>"
            "    </div>"
            "    <div style='display: flex; flex-direction: row; gap: 12px; "
            "align-items: center; padding: 8px 12px; border-radius: 8px'>"
            "      <div data-icon='help-circle' style='width: 18px; height: 18px; "
            "color: #94A3B8'></div>"
            "      <span style='font-size: 14px; font-weight: 400; "
            "color: #94A3B8'>Help</span>"
            "    </div>"
            "  </div>"
            "  <div style='display: flex; flex-direction: row; gap: 12px; "
            "align-items: center; padding: 16px 20px; "
            "border-top: 1px solid #1E293B'>"
            "    <div style='width: 32px; height: 32px; background-color: #334155; "
            "border-radius: 9999px; display: flex; align-items: center; "
            "justify-content: center'>"
            "      <span style='color: #FFFFFF; font-size: 12px; font-weight: 600'>JD</span>"
            "    </div>"
            "    <div style='display: flex; flex-direction: column; gap: 0px; flex: 1'>"
            "      <span style='font-size: 13px; font-weight: 500; color: #F1F5F9'>John Doe</span>"
            "      <span style='font-size: 11px; color: #64748B'>john@acme.com</span>"
            "    </div>"
            "    <div data-icon='log-out' style='width: 16px; height: 16px; "
            "color: #64748B'></div>"
            "  </div>"
            "</div>"
        ),
    },
    "top-nav": {
        "description": "White top navigation bar with breadcrumb and actions",
        "html": (
            "<div style='width: 100%; display: flex; flex-direction: row; "
            "align-items: center; justify-content: space-between; "
            "padding: 12px 32px; background-color: #FFFFFF; "
            "border-bottom: 1px solid #E2E8F0'>"
            "  <div style='display: flex; flex-direction: row; gap: 8px; "
            "align-items: center'>"
            "    <span style='font-size: 14px; color: #94A3B8'>Dashboard</span>"
            "    <div data-icon='chevron-right' style='width: 14px; height: 14px; "
            "color: #CBD5E1'></div>"
            "    <span style='font-size: 14px; font-weight: 500; "
            "color: #0F172A'>Overview</span>"
            "  </div>"
            "  <div style='display: flex; flex-direction: row; gap: 16px; "
            "align-items: center'>"
            "    <div style='display: flex; flex-direction: row; gap: 8px; "
            "align-items: center; padding: 8px 14px; border: 1px solid #E2E8F0; "
            "border-radius: 8px; background-color: #FFFFFF'>"
            "      <div data-icon='search' style='width: 16px; height: 16px; "
            "color: #94A3B8'></div>"
            "      <span style='font-size: 14px; color: #94A3B8'>Search...</span>"
            "    </div>"
            "    <div data-icon='bell' style='width: 20px; height: 20px; "
            "color: #64748B'></div>"
            "    <div style='width: 32px; height: 32px; background-color: #2563EB; "
            "border-radius: 9999px; display: flex; align-items: center; "
            "justify-content: center'>"
            "      <span style='color: #FFFFFF; font-size: 12px; "
            "font-weight: 600'>JD</span>"
            "    </div>"
            "  </div>"
            "</div>"
        ),
    },
    # ── Metric Cards ──
    "metric-card": {
        "description": "KPI metric card with icon, label, value, and trend",
        "html": (
            "<div style='flex: 1; display: flex; flex-direction: column; gap: 12px; "
            "padding: 24px; background-color: #FFFFFF; border-radius: 12px; "
            "box-shadow: 0 1px 3px rgba(0,0,0,0.1)'>"
            "  <div style='display: flex; flex-direction: row; "
            "align-items: center; justify-content: space-between'>"
            "    <span style='font-size: 14px; font-weight: 500; "
            "color: #64748B'>Total Revenue</span>"
            "    <div data-icon='dollar-sign' style='width: 18px; height: 18px; "
            "color: #94A3B8'></div>"
            "  </div>"
            "  <span style='font-size: 32px; font-weight: 700; "
            "color: #0F172A'>$45,231.89</span>"
            "  <div style='display: flex; flex-direction: row; gap: 6px; "
            "align-items: center'>"
            "    <div data-icon='trending-up' style='width: 14px; height: 14px; "
            "color: #16A34A'></div>"
            "    <span style='font-size: 12px; font-weight: 600; "
            "color: #16A34A'>+20.1%</span>"
            "    <span style='font-size: 12px; color: #94A3B8'>from last month</span>"
            "  </div>"
            "</div>"
        ),
    },
    # ── Table ──
    "data-table": {
        "description": "Data table with header, sortable columns, status badges",
        "html": (
            "<div style='display: flex; flex-direction: column; "
            "background-color: #FFFFFF; border-radius: 12px; "
            "border: 1px solid #E2E8F0; overflow: hidden'>"
            "  <div style='display: flex; flex-direction: row; "
            "padding: 12px 24px; background-color: #F8FAFC; "
            "border-bottom: 1px solid #E2E8F0'>"
            "    <span style='flex: 1; font-size: 13px; font-weight: 600; "
            "color: #64748B'>Customer</span>"
            "    <span style='flex: 1; font-size: 13px; font-weight: 600; "
            "color: #64748B'>Status</span>"
            "    <span style='flex: 1; font-size: 13px; font-weight: 600; "
            "color: #64748B'>Amount</span>"
            "    <span style='flex: 1; font-size: 13px; font-weight: 600; "
            "color: #64748B'>Date</span>"
            "  </div>"
            "  <div style='display: flex; flex-direction: row; "
            "padding: 14px 24px; align-items: center; "
            "border-bottom: 1px solid #F1F5F9'>"
            "    <div style='flex: 1; display: flex; flex-direction: row; "
            "gap: 12px; align-items: center'>"
            "      <div style='width: 32px; height: 32px; "
            "background-color: #DBEAFE; border-radius: 9999px; "
            "display: flex; align-items: center; justify-content: center'>"
            "        <span style='font-size: 12px; font-weight: 600; "
            "color: #2563EB'>OC</span>"
            "      </div>"
            "      <div style='display: flex; flex-direction: column; gap: 0px'>"
            "        <span style='font-size: 14px; font-weight: 500; "
            "color: #0F172A'>Olivia Chen</span>"
            "        <span style='font-size: 12px; color: #94A3B8'>olivia@email.com</span>"
            "      </div>"
            "    </div>"
            "    <div style='flex: 1; display: flex; flex-direction: row'>"
            "      <div style='display: flex; padding: 2px 10px; "
            "border-radius: 9999px; background-color: #DCFCE7'>"
            "        <span style='font-size: 12px; font-weight: 500; "
            "color: #16A34A'>Completed</span>"
            "      </div>"
            "    </div>"
            "    <span style='flex: 1; font-size: 14px; "
            "color: #0F172A'>$1,250.00</span>"
            "    <span style='flex: 1; font-size: 14px; "
            "color: #64748B'>Jan 15, 2024</span>"
            "  </div>"
            "  <div style='display: flex; flex-direction: row; "
            "padding: 14px 24px; align-items: center; "
            "border-bottom: 1px solid #F1F5F9'>"
            "    <div style='flex: 1; display: flex; flex-direction: row; "
            "gap: 12px; align-items: center'>"
            "      <div style='width: 32px; height: 32px; "
            "background-color: #FEF3C7; border-radius: 9999px; "
            "display: flex; align-items: center; justify-content: center'>"
            "        <span style='font-size: 12px; font-weight: 600; "
            "color: #D97706'>MJ</span>"
            "      </div>"
            "      <div style='display: flex; flex-direction: column; gap: 0px'>"
            "        <span style='font-size: 14px; font-weight: 500; "
            "color: #0F172A'>Michael Johnson</span>"
            "        <span style='font-size: 12px; color: #94A3B8'>michael@email.com</span>"
            "      </div>"
            "    </div>"
            "    <div style='flex: 1; display: flex; flex-direction: row'>"
            "      <div style='display: flex; padding: 2px 10px; "
            "border-radius: 9999px; background-color: #FEF3C7'>"
            "        <span style='font-size: 12px; font-weight: 500; "
            "color: #D97706'>Pending</span>"
            "      </div>"
            "    </div>"
            "    <span style='flex: 1; font-size: 14px; "
            "color: #0F172A'>$890.00</span>"
            "    <span style='flex: 1; font-size: 14px; "
            "color: #64748B'>Jan 14, 2024</span>"
            "  </div>"
            "</div>"
        ),
    },
    # ── Buttons ──
    "button-primary": {
        "description": "Primary action button with icon",
        "html": (
            "<button style='display: flex; flex-direction: row; gap: 8px; "
            "align-items: center; padding: 10px 20px; "
            "background-color: #2563EB; border-radius: 8px'>"
            "  <div data-icon='plus' style='width: 16px; height: 16px; "
            "color: #FFFFFF'></div>"
            "  <span style='font-size: 14px; font-weight: 500; "
            "color: #FFFFFF'>Add New</span>"
            "</button>"
        ),
    },
    "button-secondary": {
        "description": "Secondary/outline button",
        "html": (
            "<button style='display: flex; flex-direction: row; gap: 8px; "
            "align-items: center; padding: 10px 20px; "
            "background-color: #FFFFFF; border: 1px solid #E2E8F0; "
            "border-radius: 8px'>"
            "  <span style='font-size: 14px; font-weight: 500; "
            "color: #0F172A'>Cancel</span>"
            "</button>"
        ),
    },
    "button-ghost": {
        "description": "Ghost button for subtle actions",
        "html": (
            "<button style='display: flex; flex-direction: row; gap: 8px; "
            "align-items: center; padding: 8px 14px; border-radius: 8px'>"
            "  <div data-icon='more-horizontal' style='width: 16px; "
            "height: 16px; color: #64748B'></div>"
            "</button>"
        ),
    },
    "button-destructive": {
        "description": "Destructive/danger button",
        "html": (
            "<button style='display: flex; flex-direction: row; gap: 8px; "
            "align-items: center; padding: 10px 20px; "
            "background-color: #DC2626; border-radius: 8px'>"
            "  <div data-icon='trash' style='width: 16px; height: 16px; "
            "color: #FFFFFF'></div>"
            "  <span style='font-size: 14px; font-weight: 500; "
            "color: #FFFFFF'>Delete</span>"
            "</button>"
        ),
    },
    # ── Badges ──
    "badge-success": {
        "description": "Green success badge",
        "html": (
            "<div style='display: flex; flex-direction: row; gap: 4px; "
            "padding: 2px 10px; border-radius: 9999px; "
            "background-color: #DCFCE7; align-items: center'>"
            "  <div data-icon='check-circle' style='width: 12px; "
            "height: 12px; color: #16A34A'></div>"
            "  <span style='font-size: 12px; font-weight: 500; "
            "color: #16A34A'>Active</span>"
            "</div>"
        ),
    },
    "badge-warning": {
        "description": "Yellow warning badge",
        "html": (
            "<div style='display: flex; flex-direction: row; gap: 4px; "
            "padding: 2px 10px; border-radius: 9999px; "
            "background-color: #FEF3C7; align-items: center'>"
            "  <div data-icon='alert-circle' style='width: 12px; "
            "height: 12px; color: #D97706'></div>"
            "  <span style='font-size: 12px; font-weight: 500; "
            "color: #D97706'>Pending</span>"
            "</div>"
        ),
    },
    "badge-error": {
        "description": "Red error badge",
        "html": (
            "<div style='display: flex; flex-direction: row; gap: 4px; "
            "padding: 2px 10px; border-radius: 9999px; "
            "background-color: #FEE2E2; align-items: center'>"
            "  <div data-icon='x-circle' style='width: 12px; "
            "height: 12px; color: #DC2626'></div>"
            "  <span style='font-size: 12px; font-weight: 500; "
            "color: #DC2626'>Failed</span>"
            "</div>"
        ),
    },
    "badge-neutral": {
        "description": "Neutral/default badge",
        "html": (
            "<div style='display: flex; flex-direction: row; "
            "padding: 2px 10px; border-radius: 9999px; "
            "background-color: #F1F5F9'>"
            "  <span style='font-size: 12px; font-weight: 500; "
            "color: #64748B'>Draft</span>"
            "</div>"
        ),
    },
    # ── Form Elements ──
    "input-with-label": {
        "description": "Input field with label above",
        "html": (
            "<div style='display: flex; flex-direction: column; gap: 6px; "
            "width: 100%'>"
            "  <label style='font-size: 14px; font-weight: 500; "
            "color: #0F172A'>Email address</label>"
            "  <input placeholder='john@example.com' "
            "style='width: 100%; padding: 10px 14px; "
            "border: 1px solid #E2E8F0; border-radius: 8px; "
            "font-size: 14px' />"
            "</div>"
        ),
    },
    "search-input": {
        "description": "Search bar with icon",
        "html": (
            "<div style='display: flex; flex-direction: row; gap: 8px; "
            "align-items: center; padding: 10px 14px; "
            "border: 1px solid #E2E8F0; border-radius: 8px; "
            "background-color: #FFFFFF; width: 320px'>"
            "  <div data-icon='search' style='width: 18px; height: 18px; "
            "color: #94A3B8'></div>"
            "  <span style='font-size: 14px; color: #94A3B8'>Search...</span>"
            "</div>"
        ),
    },
    "toggle-switch": {
        "description": "Toggle switch (on state)",
        "html": (
            "<div style='display: flex; flex-direction: row; gap: 12px; "
            "align-items: center'>"
            "  <div style='width: 44px; height: 24px; "
            "background-color: #2563EB; border-radius: 9999px; "
            "display: flex; flex-direction: row; align-items: center; "
            "padding: 2px; justify-content: flex-end'>"
            "    <div style='width: 20px; height: 20px; "
            "background-color: #FFFFFF; border-radius: 9999px'></div>"
            "  </div>"
            "  <span style='font-size: 14px; color: #0F172A'>Enable notifications</span>"
            "</div>"
        ),
    },
    # ── Cards ──
    "card-simple": {
        "description": "Simple content card with title and description",
        "html": (
            "<div style='display: flex; flex-direction: column; gap: 16px; "
            "padding: 24px; background-color: #FFFFFF; border-radius: 12px; "
            "box-shadow: 0 1px 3px rgba(0,0,0,0.1)'>"
            "  <div style='display: flex; flex-direction: column; gap: 4px'>"
            "    <span style='font-size: 16px; font-weight: 600; "
            "color: #0F172A'>Card Title</span>"
            "    <span style='font-size: 14px; color: #64748B'>"
            "Card description with supporting text</span>"
            "  </div>"
            "  <div style='display: flex; flex-direction: column; gap: 12px'>"
            "    <span style='font-size: 14px; color: #475569'>Card content goes here.</span>"
            "  </div>"
            "</div>"
        ),
    },
    "card-with-header": {
        "description": "Card with distinct header, content area, and footer actions",
        "html": (
            "<div style='display: flex; flex-direction: column; "
            "background-color: #FFFFFF; border-radius: 12px; "
            "box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden'>"
            "  <div style='display: flex; flex-direction: row; "
            "align-items: center; justify-content: space-between; "
            "padding: 20px 24px; border-bottom: 1px solid #F1F5F9'>"
            "    <div style='display: flex; flex-direction: column; gap: 2px'>"
            "      <span style='font-size: 16px; font-weight: 600; "
            "color: #0F172A'>Recent Orders</span>"
            "      <span style='font-size: 13px; color: #94A3B8'>Last 30 days</span>"
            "    </div>"
            "    <button style='display: flex; flex-direction: row; gap: 6px; "
            "align-items: center; padding: 6px 12px; border-radius: 8px; "
            "border: 1px solid #E2E8F0; background-color: #FFFFFF'>"
            "      <div data-icon='download' style='width: 14px; height: 14px; "
            "color: #64748B'></div>"
            "      <span style='font-size: 13px; font-weight: 500; "
            "color: #0F172A'>Export</span>"
            "    </button>"
            "  </div>"
            "  <div style='display: flex; flex-direction: column; padding: 24px'>"
            "    <span style='font-size: 14px; color: #475569'>Content area</span>"
            "  </div>"
            "</div>"
        ),
    },
    # ── Avatar ──
    "avatar": {
        "description": "User avatar with initials and colored background",
        "html": (
            "<div style='width: 40px; height: 40px; background-color: #2563EB; "
            "border-radius: 9999px; display: flex; align-items: center; "
            "justify-content: center'>"
            "  <span style='color: #FFFFFF; font-size: 14px; "
            "font-weight: 600'>JD</span>"
            "</div>"
        ),
    },
    "avatar-group": {
        "description": "Stack of overlapping avatars",
        "html": (
            "<div style='display: flex; flex-direction: row; gap: -8px'>"
            "  <div style='width: 36px; height: 36px; background-color: #2563EB; "
            "border-radius: 9999px; display: flex; align-items: center; "
            "justify-content: center; border: 2px solid #FFFFFF'>"
            "    <span style='color: #FFFFFF; font-size: 11px; font-weight: 600'>AB</span>"
            "  </div>"
            "  <div style='width: 36px; height: 36px; background-color: #16A34A; "
            "border-radius: 9999px; display: flex; align-items: center; "
            "justify-content: center; border: 2px solid #FFFFFF'>"
            "    <span style='color: #FFFFFF; font-size: 11px; font-weight: 600'>CD</span>"
            "  </div>"
            "  <div style='width: 36px; height: 36px; background-color: #F59E0B; "
            "border-radius: 9999px; display: flex; align-items: center; "
            "justify-content: center; border: 2px solid #FFFFFF'>"
            "    <span style='color: #FFFFFF; font-size: 11px; font-weight: 600'>EF</span>"
            "  </div>"
            "</div>"
        ),
    },
    # ── Alerts ──
    "alert-info": {
        "description": "Blue informational alert",
        "html": (
            "<div style='display: flex; flex-direction: row; gap: 12px; "
            "padding: 16px; border-radius: 12px; "
            "background-color: #EFF6FF; border: 1px solid #BFDBFE'>"
            "  <div data-icon='info' style='width: 20px; height: 20px; "
            "color: #2563EB'></div>"
            "  <div style='display: flex; flex-direction: column; gap: 4px; flex: 1'>"
            "    <span style='font-size: 14px; font-weight: 600; "
            "color: #1E40AF'>Information</span>"
            "    <span style='font-size: 13px; color: #1E40AF'>"
            "Your trial ends in 7 days. Upgrade to continue.</span>"
            "  </div>"
            "</div>"
        ),
    },
    "alert-success": {
        "description": "Green success alert",
        "html": (
            "<div style='display: flex; flex-direction: row; gap: 12px; "
            "padding: 16px; border-radius: 12px; "
            "background-color: #F0FDF4; border: 1px solid #BBF7D0'>"
            "  <div data-icon='check-circle' style='width: 20px; height: 20px; "
            "color: #16A34A'></div>"
            "  <div style='display: flex; flex-direction: column; gap: 4px; flex: 1'>"
            "    <span style='font-size: 14px; font-weight: 600; "
            "color: #166534'>Success</span>"
            "    <span style='font-size: 13px; color: #166534'>"
            "Your changes have been saved successfully.</span>"
            "  </div>"
            "</div>"
        ),
    },
    # ── Progress ──
    "progress-bar": {
        "description": "Progress bar with label and percentage",
        "html": (
            "<div style='display: flex; flex-direction: column; gap: 8px; "
            "width: 100%'>"
            "  <div style='display: flex; flex-direction: row; "
            "justify-content: space-between'>"
            "    <span style='font-size: 13px; font-weight: 500; "
            "color: #0F172A'>Storage</span>"
            "    <span style='font-size: 13px; color: #64748B'>75%</span>"
            "  </div>"
            "  <div style='width: 100%; height: 8px; "
            "background-color: #E2E8F0; border-radius: 9999px; "
            "display: flex; flex-direction: row; overflow: hidden'>"
            "    <div style='width: 75%; height: 8px; "
            "background-color: #2563EB; border-radius: 9999px'></div>"
            "  </div>"
            "</div>"
        ),
    },
    # ── Tabs ──
    "tab-bar": {
        "description": "Horizontal tab navigation",
        "html": (
            "<div style='display: flex; flex-direction: row; gap: 0px; "
            "border-bottom: 1px solid #E2E8F0'>"
            "  <div style='display: flex; flex-direction: row; "
            "padding: 10px 20px; border-bottom: 2px solid #2563EB'>"
            "    <span style='font-size: 14px; font-weight: 500; "
            "color: #2563EB'>Overview</span>"
            "  </div>"
            "  <div style='display: flex; flex-direction: row; "
            "padding: 10px 20px'>"
            "    <span style='font-size: 14px; font-weight: 500; "
            "color: #64748B'>Analytics</span>"
            "  </div>"
            "  <div style='display: flex; flex-direction: row; "
            "padding: 10px 20px'>"
            "    <span style='font-size: 14px; font-weight: 500; "
            "color: #64748B'>Reports</span>"
            "  </div>"
            "  <div style='display: flex; flex-direction: row; "
            "padding: 10px 20px'>"
            "    <span style='font-size: 14px; font-weight: 500; "
            "color: #64748B'>Settings</span>"
            "  </div>"
            "</div>"
        ),
    },
    # ── Empty State ──
    "empty-state": {
        "description": "Empty state placeholder with icon and CTA",
        "html": (
            "<div style='display: flex; flex-direction: column; gap: 16px; "
            "align-items: center; justify-content: center; padding: 64px 32px'>"
            "  <div style='width: 56px; height: 56px; "
            "background-color: #F1F5F9; border-radius: 12px; "
            "display: flex; align-items: center; justify-content: center'>"
            "    <div data-icon='inbox' style='width: 28px; height: 28px; "
            "color: #94A3B8'></div>"
            "  </div>"
            "  <div style='display: flex; flex-direction: column; gap: 4px; "
            "align-items: center'>"
            "    <span style='font-size: 16px; font-weight: 600; "
            "color: #0F172A'>No data yet</span>"
            "    <span style='font-size: 14px; color: #94A3B8'>"
            "Get started by creating your first item.</span>"
            "  </div>"
            "  <button style='display: flex; flex-direction: row; gap: 8px; "
            "align-items: center; padding: 10px 20px; "
            "background-color: #2563EB; border-radius: 8px'>"
            "    <div data-icon='plus' style='width: 16px; height: 16px; "
            "color: #FFFFFF'></div>"
            "    <span style='font-size: 14px; font-weight: 500; "
            "color: #FFFFFF'>Create First Item</span>"
            "  </button>"
            "</div>"
        ),
    },
    # ── List Item ──
    "list-item": {
        "description": "List item with icon, text, and action",
        "html": (
            "<div style='display: flex; flex-direction: row; gap: 16px; "
            "align-items: center; padding: 16px 24px; "
            "border-bottom: 1px solid #F1F5F9'>"
            "  <div style='width: 40px; height: 40px; "
            "background-color: #F1F5F9; border-radius: 10px; "
            "display: flex; align-items: center; justify-content: center'>"
            "    <div data-icon='file-text' style='width: 20px; height: 20px; "
            "color: #64748B'></div>"
            "  </div>"
            "  <div style='display: flex; flex-direction: column; gap: 2px; flex: 1'>"
            "    <span style='font-size: 14px; font-weight: 500; "
            "color: #0F172A'>Document Title</span>"
            "    <span style='font-size: 13px; color: #94A3B8'>Updated 2 hours ago</span>"
            "  </div>"
            "  <div data-icon='more-horizontal' style='width: 18px; height: 18px; "
            "color: #94A3B8'></div>"
            "</div>"
        ),
    },
    # ── Section Header ──
    "section-header": {
        "description": "Section title with description and action button",
        "html": (
            "<div style='display: flex; flex-direction: row; "
            "align-items: flex-start; justify-content: space-between; "
            "width: 100%'>"
            "  <div style='display: flex; flex-direction: column; gap: 4px'>"
            "    <span style='font-size: 20px; font-weight: 600; "
            "color: #0F172A'>Team Members</span>"
            "    <span style='font-size: 14px; color: #64748B'>"
            "Manage your team and their account permissions.</span>"
            "  </div>"
            "  <button style='display: flex; flex-direction: row; gap: 8px; "
            "align-items: center; padding: 10px 20px; "
            "background-color: #2563EB; border-radius: 8px'>"
            "    <div data-icon='plus' style='width: 16px; height: 16px; "
            "color: #FFFFFF'></div>"
            "    <span style='font-size: 14px; font-weight: 500; "
            "color: #FFFFFF'>Invite Member</span>"
            "  </button>"
            "</div>"
        ),
    },
    # ── Stats Row ──
    "stats-row": {
        "description": "Row of mini stats with icons",
        "html": (
            "<div style='display: flex; flex-direction: row; gap: 24px'>"
            "  <div style='flex: 1; display: flex; flex-direction: row; gap: 16px; "
            "padding: 20px; background-color: #FFFFFF; border-radius: 12px; "
            "border: 1px solid #E2E8F0; align-items: center'>"
            "    <div style='width: 44px; height: 44px; "
            "background-color: #EFF6FF; border-radius: 10px; "
            "display: flex; align-items: center; justify-content: center'>"
            "      <div data-icon='users' style='width: 22px; height: 22px; "
            "color: #2563EB'></div>"
            "    </div>"
            "    <div style='display: flex; flex-direction: column; gap: 2px'>"
            "      <span style='font-size: 12px; font-weight: 500; "
            "color: #64748B'>Total Users</span>"
            "      <span style='font-size: 24px; font-weight: 700; "
            "color: #0F172A'>2,543</span>"
            "    </div>"
            "  </div>"
            "  <div style='flex: 1; display: flex; flex-direction: row; gap: 16px; "
            "padding: 20px; background-color: #FFFFFF; border-radius: 12px; "
            "border: 1px solid #E2E8F0; align-items: center'>"
            "    <div style='width: 44px; height: 44px; "
            "background-color: #F0FDF4; border-radius: 10px; "
            "display: flex; align-items: center; justify-content: center'>"
            "      <div data-icon='dollar-sign' style='width: 22px; height: 22px; "
            "color: #16A34A'></div>"
            "    </div>"
            "    <div style='display: flex; flex-direction: column; gap: 2px'>"
            "      <span style='font-size: 12px; font-weight: 500; "
            "color: #64748B'>Revenue</span>"
            "      <span style='font-size: 24px; font-weight: 700; "
            "color: #0F172A'>$48.2K</span>"
            "    </div>"
            "  </div>"
            "</div>"
        ),
    },
    # ── Chart Placeholder ──
    "chart-placeholder": {
        "description": "Chart area placeholder with title (actual chart is visual only)",
        "html": (
            "<div style='display: flex; flex-direction: column; gap: 20px; "
            "padding: 24px; background-color: #FFFFFF; border-radius: 12px; "
            "box-shadow: 0 1px 3px rgba(0,0,0,0.1)'>"
            "  <div style='display: flex; flex-direction: row; "
            "align-items: center; justify-content: space-between'>"
            "    <div style='display: flex; flex-direction: column; gap: 2px'>"
            "      <span style='font-size: 16px; font-weight: 600; "
            "color: #0F172A'>Revenue Overview</span>"
            "      <span style='font-size: 13px; color: #94A3B8'>Monthly revenue trend</span>"
            "    </div>"
            "    <div style='display: flex; flex-direction: row; gap: 8px'>"
            "      <div style='display: flex; flex-direction: row; "
            "padding: 6px 14px; border-radius: 8px; "
            "background-color: #0F172A'>"
            "        <span style='font-size: 12px; font-weight: 500; "
            "color: #FFFFFF'>12M</span>"
            "      </div>"
            "      <div style='display: flex; flex-direction: row; "
            "padding: 6px 14px; border-radius: 8px'>"
            "        <span style='font-size: 12px; font-weight: 500; "
            "color: #64748B'>6M</span>"
            "      </div>"
            "      <div style='display: flex; flex-direction: row; "
            "padding: 6px 14px; border-radius: 8px'>"
            "        <span style='font-size: 12px; font-weight: 500; "
            "color: #64748B'>30D</span>"
            "      </div>"
            "    </div>"
            "  </div>"
            "  <div style='width: 100%; height: 240px; "
            "background-color: #F8FAFC; border-radius: 8px; "
            "display: flex; align-items: center; justify-content: center'>"
            "    <div data-icon='line-chart' style='width: 48px; height: 48px; "
            "color: #CBD5E1'></div>"
            "  </div>"
            "</div>"
        ),
    },
}


def get_component_catalog_for_prompt() -> str:
    """Generate a formatted component catalog section for the LLM prompt."""
    lines = ["## Component Library (shadcn/ui patterns)\n"]
    lines.append(
        "Use these EXACT component patterns when building screens. "
        "Compose full layouts by combining these building blocks. "
        "Adapt the content (text, colors, icons) but keep the structural "
        "pattern identical.\n"
    )

    for name, component in COMPONENT_CATALOG.items():
        lines.append(f"### {name}")
        lines.append(f"_{component['description']}_")
        lines.append("```html")
        lines.append(component["html"])
        lines.append("```\n")

    return "\n".join(lines)
