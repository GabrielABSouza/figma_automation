import { describe, it, expect, vi, beforeEach } from "vitest";

// Minimal mock of Figma node objects
function mockFrameNode(): Record<string, unknown> {
  var children: unknown[] = [];
  return {
    name: "",
    layoutMode: "NONE",
    primaryAxisSizingMode: "AUTO",
    counterAxisSizingMode: "AUTO",
    primaryAxisAlignItems: "MIN",
    counterAxisAlignItems: "MIN",
    itemSpacing: 0,
    paddingTop: 0,
    paddingBottom: 0,
    paddingLeft: 0,
    paddingRight: 0,
    cornerRadius: 0,
    fills: [],
    strokes: [],
    strokeWeight: 0,
    strokeAlign: "CENTER",
    effects: [],
    clipsContent: false,
    layoutGrow: 0,
    layoutAlign: "INHERIT",
    children: children,
    appendChild: vi.fn(function (child: unknown) {
      children.push(child);
    }),
    resize: vi.fn(function (
      this: Record<string, unknown>,
      w: number,
      h: number
    ) {
      this.width = w;
      this.height = h;
    }),
    width: 0,
    height: 0,
  };
}

function mockTextNode(): Record<string, unknown> {
  return {
    name: "",
    fontName: { family: "Inter", style: "Regular" },
    fontSize: 16,
    lineHeight: { value: 24, unit: "PIXELS" },
    characters: "",
    fills: [],
  };
}

var figmaMock = {
  createFrame: vi.fn(function () {
    return mockFrameNode();
  }),
  createText: vi.fn(function () {
    return mockTextNode();
  }),
};

vi.stubGlobal("figma", figmaMock);

import {
  createInput,
  createNavbar,
  createTable,
  createAvatar,
  createBadge,
  createDivider,
} from "../src/nodeFactory";

beforeEach(function () {
  vi.clearAllMocks();
  figmaMock.createFrame.mockImplementation(function () {
    return mockFrameNode();
  });
  figmaMock.createText.mockImplementation(function () {
    return mockTextNode();
  });
});

describe("createInput", function () {
  it("creates frame with label and input field", function () {
    var node = createInput({
      id: "test_input_1",
      type: "input",
      props: { label: "Email", placeholder: "you@example.com" },
      tokens: {},
      children: [],
    }) as unknown as Record<string, unknown>;
    expect(node.name).toBe("test_input_1");
    expect(node.layoutMode).toBe("VERTICAL");
    expect(node.appendChild).toHaveBeenCalledTimes(2);
  });
});

describe("createNavbar", function () {
  it("creates horizontal frame with logo and items", function () {
    var node = createNavbar({
      id: "test_navbar_1",
      type: "navbar",
      props: { logo: "Acme", items: ["Home", "About"] },
      tokens: {},
      children: [],
    }) as unknown as Record<string, unknown>;
    expect(node.name).toBe("test_navbar_1");
    expect(node.layoutMode).toBe("HORIZONTAL");
    expect(node.appendChild).toHaveBeenCalledTimes(3);
  });

  it("handles object items with label property", function () {
    var node = createNavbar({
      id: "test_navbar_2",
      type: "navbar",
      props: { logo: "App", items: [{ label: "Dashboard" }] },
      tokens: {},
      children: [],
    }) as unknown as Record<string, unknown>;
    expect(node.appendChild).toHaveBeenCalledTimes(2);
  });
});

describe("createTable", function () {
  it("creates table with header and data rows", function () {
    var node = createTable({
      id: "test_table_1",
      type: "table",
      props: { columns: [{ header: "A" }, { header: "B" }], rows: 2 },
      tokens: {},
      children: [],
    }) as unknown as Record<string, unknown>;
    expect(node.name).toBe("test_table_1");
    expect(node.layoutMode).toBe("VERTICAL");
    expect(node.appendChild).toHaveBeenCalledTimes(3);
  });
});

describe("createAvatar", function () {
  it("creates circle avatar with correct size", function () {
    var node = createAvatar({
      id: "test_avatar_1",
      type: "avatar",
      props: { initials: "JD", size: "md" },
      tokens: {},
      children: [],
    }) as unknown as Record<string, unknown>;
    expect(node.name).toBe("test_avatar_1");
    expect(node.resize).toHaveBeenCalledWith(40, 40);
    expect(node.cornerRadius).toBe(20);
  });

  it("uses larger dimension for lg size", function () {
    var node = createAvatar({
      id: "test_avatar_2",
      type: "avatar",
      props: { initials: "AB", size: "lg" },
      tokens: {},
      children: [],
    }) as unknown as Record<string, unknown>;
    expect(node.resize).toHaveBeenCalledWith(48, 48);
    expect(node.cornerRadius).toBe(24);
  });

  it("uses square radius for square variant", function () {
    var node = createAvatar({
      id: "test_avatar_3",
      type: "avatar",
      props: { initials: "XY", variant: "square" },
      tokens: {},
      children: [],
    }) as unknown as Record<string, unknown>;
    expect(node.cornerRadius).toBe(8);
  });
});

describe("createBadge", function () {
  it("uses full border radius for pill shape", function () {
    var node = createBadge({
      id: "test_badge_1",
      type: "badge",
      props: { label: "Active", variant: "success" },
      tokens: {},
      children: [],
    }) as unknown as Record<string, unknown>;
    expect(node.name).toBe("test_badge_1");
    expect(node.cornerRadius).toBe(9999);
  });
});

describe("createDivider", function () {
  it("creates horizontal divider", function () {
    var node = createDivider({
      id: "test_divider_1",
      type: "divider",
      props: { variant: "horizontal" },
      tokens: {},
      children: [],
    }) as unknown as Record<string, unknown>;
    expect(node.resize).toHaveBeenCalledWith(100, 1);
    expect(node.layoutAlign).toBe("STRETCH");
  });

  it("creates vertical divider", function () {
    var node = createDivider({
      id: "test_divider_2",
      type: "divider",
      props: { variant: "vertical" },
      tokens: {},
      children: [],
    }) as unknown as Record<string, unknown>;
    expect(node.resize).toHaveBeenCalledWith(1, 24);
  });
});
