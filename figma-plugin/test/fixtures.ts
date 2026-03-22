import { GenerateUIResponse, Screen, UIComponent } from "../src/types";

export const SIMPLE_TEXT: UIComponent = {
  id: "Dashboard_text_1",
  type: "text",
  props: { content: "Dashboard Overview", variant: "heading-1" },
  tokens: { color: "text-primary" },
  children: [],
};

export const SIMPLE_CARD: UIComponent = {
  id: "Dashboard_card_1",
  type: "card",
  props: { title: "Revenue", padding: "md" },
  tokens: { background: "surface", shadow: "md" },
  children: [
    {
      id: "Dashboard_text_2",
      type: "text",
      props: { content: "$12,345", variant: "heading-2" },
      tokens: { color: "text-primary" },
      children: [],
    },
  ],
};

export const DASHBOARD_SCREEN: Screen = {
  screen_name: "Dashboard",
  components: [
    {
      id: "Dashboard_section_1",
      type: "section",
      props: {},
      tokens: { spacing: "md" },
      children: [
        SIMPLE_TEXT,
        {
          id: "Dashboard_row_1",
          type: "row",
          props: {},
          tokens: {},
          children: [SIMPLE_CARD],
        },
      ],
    },
  ],
  tokens: { background: "background" },
  metadata: {},
  validation: { is_valid: true, errors: [], warnings: [] },
};

export const SIMPLE_INPUT: UIComponent = {
  id: "Form_input_1",
  type: "input",
  props: { label: "Email Address", placeholder: "you@example.com" },
  tokens: { border: "border", background: "background" },
  children: [],
};

export const SIMPLE_NAVBAR: UIComponent = {
  id: "Dashboard_navbar_1",
  type: "navbar",
  props: { logo: "Acme Inc", items: ["Dashboard", "Reports", "Settings"] },
  tokens: { background: "surface", border: "border" },
  children: [],
};

export const SIMPLE_TABLE: UIComponent = {
  id: "Dashboard_table_1",
  type: "table",
  props: {
    columns: [{ header: "Name" }, { header: "Status" }, { header: "Date" }],
    rows: 3,
  },
  tokens: { border: "border" },
  children: [],
};

export const SIMPLE_AVATAR: UIComponent = {
  id: "Profile_avatar_1",
  type: "avatar",
  props: { initials: "JD", size: "md", variant: "circle" },
  tokens: { background: "primary" },
  children: [],
};

export const SIMPLE_BADGE: UIComponent = {
  id: "Dashboard_badge_1",
  type: "badge",
  props: { label: "Active", variant: "success" },
  tokens: {},
  children: [],
};

export const SIMPLE_DIVIDER: UIComponent = {
  id: "Dashboard_divider_1",
  type: "divider",
  props: { variant: "horizontal" },
  tokens: { color: "border" },
  children: [],
};

export const SAMPLE_RESPONSE: GenerateUIResponse = {
  success: true,
  screens: [DASHBOARD_SCREEN],
  errors: [],
  metadata: {
    prompt: "Build a SaaS dashboard",
    screen_count: 1,
    schema_version: "1.0.0",
  },
};
