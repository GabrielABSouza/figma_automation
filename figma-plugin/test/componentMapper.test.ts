import { describe, it, expect } from "vitest";
import { isLayoutType, isSupported } from "../src/componentMapper";

describe("isLayoutType", () => {
  it("recognizes section", () => {
    expect(isLayoutType("section")).toBe(true);
  });

  it("recognizes row", () => {
    expect(isLayoutType("row")).toBe(true);
  });

  it("recognizes column", () => {
    expect(isLayoutType("column")).toBe(true);
  });

  it("recognizes stack", () => {
    expect(isLayoutType("stack")).toBe(true);
  });

  it("rejects text", () => {
    expect(isLayoutType("text")).toBe(false);
  });

  it("rejects card", () => {
    expect(isLayoutType("card")).toBe(false);
  });

  it("rejects button", () => {
    expect(isLayoutType("button")).toBe(false);
  });
});

describe("isSupported", () => {
  it("supports all MVP types", () => {
    for (const t of [
      "section",
      "row",
      "column",
      "stack",
      "text",
      "card",
      "button",
    ]) {
      expect(isSupported(t)).toBe(true);
    }
  });

  it("does not support post-MVP types", () => {
    expect(isSupported("input")).toBe(false);
    expect(isSupported("navbar")).toBe(false);
    expect(isSupported("table")).toBe(false);
    expect(isSupported("avatar")).toBe(false);
    expect(isSupported("badge")).toBe(false);
    expect(isSupported("divider")).toBe(false);
  });
});
