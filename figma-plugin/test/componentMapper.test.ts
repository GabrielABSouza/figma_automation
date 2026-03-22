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

  it("rejects all leaf types", () => {
    for (const t of [
      "text",
      "card",
      "button",
      "input",
      "navbar",
      "table",
      "avatar",
      "badge",
      "divider",
    ]) {
      expect(isLayoutType(t)).toBe(false);
    }
  });
});

describe("isSupported", () => {
  it("supports all design system types", () => {
    for (const t of [
      "section",
      "row",
      "column",
      "stack",
      "text",
      "card",
      "button",
      "input",
      "navbar",
      "table",
      "avatar",
      "badge",
      "divider",
    ]) {
      expect(isSupported(t)).toBe(true);
    }
  });

  it("does not support unknown types", () => {
    expect(isSupported("modal")).toBe(false);
    expect(isSupported("dropdown")).toBe(false);
    expect(isSupported("tooltip")).toBe(false);
  });
});
