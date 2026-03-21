import { describe, it, expect } from "vitest";
import {
  hexToFigmaRGB,
  resolveColor,
  resolveSpacing,
  resolveTypography,
  resolveBorderRadius,
  fontWeightToStyle,
  parseShadow,
} from "../src/tokens";

describe("hexToFigmaRGB", () => {
  it("converts white", () => {
    expect(hexToFigmaRGB("#FFFFFF")).toEqual({ r: 1, g: 1, b: 1 });
  });

  it("converts black", () => {
    expect(hexToFigmaRGB("#000000")).toEqual({ r: 0, g: 0, b: 0 });
  });

  it("converts primary blue", () => {
    const rgb = hexToFigmaRGB("#2563EB");
    expect(rgb.r).toBeCloseTo(0.145, 2);
    expect(rgb.g).toBeCloseTo(0.388, 2);
    expect(rgb.b).toBeCloseTo(0.922, 2);
  });
});

describe("resolveColor", () => {
  it("resolves known token", () => {
    expect(resolveColor("primary")).not.toBeNull();
  });

  it("resolves background to white", () => {
    expect(resolveColor("background")).toEqual({ r: 1, g: 1, b: 1 });
  });

  it("returns null for unknown token", () => {
    expect(resolveColor("nonexistent")).toBeNull();
  });
});

describe("resolveSpacing", () => {
  it("resolves md to 16", () => {
    expect(resolveSpacing("md")).toBe(16);
  });

  it("resolves xs to 4", () => {
    expect(resolveSpacing("xs")).toBe(4);
  });

  it("returns null for unknown", () => {
    expect(resolveSpacing("xxx")).toBeNull();
  });
});

describe("resolveTypography", () => {
  it("resolves heading-1", () => {
    const t = resolveTypography("heading-1");
    expect(t.fontSize).toBe(32);
    expect(t.fontWeight).toBe(700);
    expect(t.lineHeight).toBe(40);
  });

  it("falls back to body for unknown", () => {
    const t = resolveTypography("unknown");
    expect(t.fontSize).toBe(16);
    expect(t.fontWeight).toBe(400);
  });
});

describe("resolveBorderRadius", () => {
  it("resolves md to 8", () => {
    expect(resolveBorderRadius("md")).toBe(8);
  });

  it("returns null for unknown", () => {
    expect(resolveBorderRadius("xxx")).toBeNull();
  });
});

describe("fontWeightToStyle", () => {
  it("maps 400 to Regular", () => {
    expect(fontWeightToStyle(400)).toBe("Regular");
  });

  it("maps 600 to Semi Bold", () => {
    expect(fontWeightToStyle(600)).toBe("Semi Bold");
  });

  it("maps 700 to Bold", () => {
    expect(fontWeightToStyle(700)).toBe("Bold");
  });

  it("maps 500 to Medium", () => {
    expect(fontWeightToStyle(500)).toBe("Medium");
  });
});

describe("parseShadow", () => {
  it("parses md shadow", () => {
    const result = parseShadow("0 4px 6px rgba(0,0,0,0.07)");
    expect(result).not.toBeNull();
    expect(result!.blur).toBe(6);
    expect(result!.offsetY).toBe(4);
    expect(result!.a).toBeCloseTo(0.07);
  });

  it("returns null for invalid input", () => {
    expect(parseShadow("invalid")).toBeNull();
  });

  it("returns null for empty string", () => {
    expect(parseShadow("")).toBeNull();
  });
});
