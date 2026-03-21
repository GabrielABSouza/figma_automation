import { UIComponent } from "./types";
import {
  resolveColor,
  resolveSpacing,
  resolveTypography,
  resolveBorderRadius,
  parseShadow,
  fontWeightToStyle,
  SHADOWS,
} from "./tokens";

// ─── Font Loading ───

const REQUIRED_FONTS: Array<FontName> = [
  { family: "Inter", style: "Regular" },
  { family: "Inter", style: "Medium" },
  { family: "Inter", style: "Semi Bold" },
  { family: "Inter", style: "Bold" },
];

/** Load all required fonts. MUST be called once before any text creation. */
export async function loadFonts(): Promise<void> {
  await Promise.all(REQUIRED_FONTS.map((font) => figma.loadFontAsync(font)));
}

// ─── Helper: Apply common tokens to a FrameNode ───

function applyFrameTokens(
  frame: FrameNode,
  tokens: Record<string, string>
): void {
  if (tokens["background"]) {
    const rgb = resolveColor(tokens["background"]);
    if (rgb) frame.fills = [{ type: "SOLID", color: rgb }];
  }

  if (tokens["border"]) {
    const rgb = resolveColor(tokens["border"]);
    if (rgb) {
      frame.strokes = [{ type: "SOLID", color: rgb }];
      frame.strokeWeight = 1;
    }
  }

  if (tokens["borderRadius"]) {
    const radius = resolveBorderRadius(tokens["borderRadius"]);
    if (radius !== null) frame.cornerRadius = radius;
  }

  if (tokens["shadow"]) {
    const cssStr = SHADOWS[tokens["shadow"]];
    if (cssStr) {
      const parsed = parseShadow(cssStr);
      if (parsed) {
        frame.effects = [
          {
            type: "DROP_SHADOW",
            color: {
              r: parsed.r / 255,
              g: parsed.g / 255,
              b: parsed.b / 255,
              a: parsed.a,
            },
            offset: { x: parsed.offsetX, y: parsed.offsetY },
            radius: parsed.blur,
            spread: 0,
            visible: true,
            blendMode: "NORMAL",
          },
        ];
      }
    }
  }

  if (tokens["spacing"]) {
    const px = resolveSpacing(tokens["spacing"]);
    if (px !== null) {
      frame.paddingTop = px;
      frame.paddingBottom = px;
      frame.paddingLeft = px;
      frame.paddingRight = px;
    }
  }
}

// ─── Layout Node Factories ───

export function createSection(component: UIComponent): FrameNode {
  const frame = figma.createFrame();
  frame.name = component.id;
  frame.layoutMode = "VERTICAL";
  frame.primaryAxisSizingMode = "AUTO";
  frame.counterAxisSizingMode = "AUTO";
  frame.itemSpacing = resolveSpacing("md") ?? 16;

  const padding = resolveSpacing(component.tokens["spacing"] ?? "md") ?? 16;
  frame.paddingTop = padding;
  frame.paddingBottom = padding;
  frame.paddingLeft = padding;
  frame.paddingRight = padding;

  frame.fills = [];
  applyFrameTokens(frame, component.tokens);
  return frame;
}

export function createRow(component: UIComponent): FrameNode {
  const frame = figma.createFrame();
  frame.name = component.id;
  frame.layoutMode = "HORIZONTAL";
  frame.primaryAxisSizingMode = "AUTO";
  frame.counterAxisSizingMode = "AUTO";
  frame.itemSpacing = resolveSpacing(component.tokens["spacing"] ?? "md") ?? 16;

  frame.fills = [];
  applyFrameTokens(frame, component.tokens);
  return frame;
}

export function createColumn(component: UIComponent): FrameNode {
  const frame = figma.createFrame();
  frame.name = component.id;
  frame.layoutMode = "VERTICAL";
  frame.primaryAxisSizingMode = "AUTO";
  frame.counterAxisSizingMode = "AUTO";
  frame.layoutGrow = 1;
  frame.itemSpacing = resolveSpacing(component.tokens["spacing"] ?? "sm") ?? 8;

  frame.fills = [];
  applyFrameTokens(frame, component.tokens);
  return frame;
}

export function createStack(component: UIComponent): FrameNode {
  const frame = figma.createFrame();
  frame.name = component.id;
  frame.layoutMode = "VERTICAL";
  frame.primaryAxisSizingMode = "AUTO";
  frame.counterAxisSizingMode = "AUTO";
  frame.itemSpacing = resolveSpacing(component.tokens["spacing"] ?? "sm") ?? 8;

  frame.fills = [];
  applyFrameTokens(frame, component.tokens);
  return frame;
}

// ─── MVP Leaf Component Factories ───

export function createText(component: UIComponent): TextNode {
  const node = figma.createText();
  node.name = component.id;

  const variant = (component.props["variant"] as string) ?? "body";
  const typo = resolveTypography(variant);
  const style = fontWeightToStyle(typo.fontWeight);

  node.fontName = { family: "Inter", style };
  node.fontSize = typo.fontSize;
  node.lineHeight = { value: typo.lineHeight, unit: "PIXELS" };

  const content = (component.props["content"] as string) ?? "";
  node.characters = content;

  const colorToken =
    component.tokens["color"] ?? (component.props["color"] as string);
  if (colorToken) {
    const rgb = resolveColor(colorToken);
    if (rgb) node.fills = [{ type: "SOLID", color: rgb }];
  }

  return node;
}

export function createCard(component: UIComponent): FrameNode {
  const frame = figma.createFrame();
  frame.name = component.id;
  frame.layoutMode = "VERTICAL";
  frame.primaryAxisSizingMode = "AUTO";
  frame.counterAxisSizingMode = "AUTO";
  frame.itemSpacing = resolveSpacing("sm") ?? 8;

  frame.cornerRadius =
    resolveBorderRadius(component.tokens["borderRadius"] ?? "md") ?? 8;

  const paddingToken =
    (component.props["padding"] as string) ??
    component.tokens["spacing"] ??
    "md";
  const padding = resolveSpacing(paddingToken) ?? 16;
  frame.paddingTop = padding;
  frame.paddingBottom = padding;
  frame.paddingLeft = padding;
  frame.paddingRight = padding;

  const bgToken = component.tokens["background"] ?? "surface";
  const bgColor = resolveColor(bgToken);
  if (bgColor) frame.fills = [{ type: "SOLID", color: bgColor }];

  const shadowToken = component.tokens["shadow"] ?? "sm";
  const cssStr = SHADOWS[shadowToken];
  if (cssStr) {
    const parsed = parseShadow(cssStr);
    if (parsed) {
      frame.effects = [
        {
          type: "DROP_SHADOW",
          color: {
            r: parsed.r / 255,
            g: parsed.g / 255,
            b: parsed.b / 255,
            a: parsed.a,
          },
          offset: { x: parsed.offsetX, y: parsed.offsetY },
          radius: parsed.blur,
          spread: 0,
          visible: true,
          blendMode: "NORMAL",
        },
      ];
    }
  }

  if (component.tokens["border"]) {
    const borderColor = resolveColor(component.tokens["border"]);
    if (borderColor) {
      frame.strokes = [{ type: "SOLID", color: borderColor }];
      frame.strokeWeight = 1;
    }
  }

  return frame;
}

export function createButton(component: UIComponent): FrameNode {
  const frame = figma.createFrame();
  frame.name = component.id;
  frame.layoutMode = "HORIZONTAL";
  frame.primaryAxisSizingMode = "AUTO";
  frame.counterAxisSizingMode = "AUTO";
  frame.primaryAxisAlignItems = "CENTER";
  frame.counterAxisAlignItems = "CENTER";

  const size = (component.props["size"] as string) ?? "md";
  const hPad = size === "sm" ? 12 : size === "lg" ? 24 : 16;
  const vPad = size === "sm" ? 6 : size === "lg" ? 14 : 10;
  frame.paddingLeft = hPad;
  frame.paddingRight = hPad;
  frame.paddingTop = vPad;
  frame.paddingBottom = vPad;

  frame.cornerRadius = resolveBorderRadius("md") ?? 8;

  const variant = (component.props["variant"] as string) ?? "primary";
  let bgTokenName: string;
  let textColorToken: string;

  switch (variant) {
    case "secondary":
      bgTokenName = "secondary";
      textColorToken = "background";
      break;
    case "ghost":
      bgTokenName = "";
      textColorToken = "primary";
      break;
    case "danger":
      bgTokenName = "error";
      textColorToken = "background";
      break;
    default:
      bgTokenName = "primary";
      textColorToken = "background";
      break;
  }

  const effectiveBg = component.tokens["background"] ?? bgTokenName;
  if (effectiveBg) {
    const rgb = resolveColor(effectiveBg);
    if (rgb) frame.fills = [{ type: "SOLID", color: rgb }];
  } else {
    frame.fills = [];
  }

  const label = (component.props["label"] as string) ?? "Button";
  const textNode = figma.createText();
  textNode.name = `${component.id}_label`;
  textNode.fontName = { family: "Inter", style: "Semi Bold" };
  textNode.fontSize = size === "sm" ? 14 : size === "lg" ? 18 : 16;
  textNode.lineHeight = {
    value: size === "sm" ? 20 : size === "lg" ? 28 : 24,
    unit: "PIXELS",
  };
  textNode.characters = label;

  const textColor = resolveColor(component.tokens["color"] ?? textColorToken);
  if (textColor) textNode.fills = [{ type: "SOLID", color: textColor }];

  frame.appendChild(textNode);
  return frame;
}
