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

// ─── Leaf Component Factories ───

export function createInput(component: UIComponent): FrameNode {
  const frame = figma.createFrame();
  frame.name = component.id;
  frame.layoutMode = "VERTICAL";
  frame.primaryAxisSizingMode = "AUTO";
  frame.counterAxisSizingMode = "AUTO";
  frame.itemSpacing = 6;
  frame.fills = [];

  const label = (component.props["label"] as string) ?? "Label";
  const labelNode = figma.createText();
  labelNode.name = `${component.id}_label`;
  labelNode.fontName = { family: "Inter", style: "Medium" };
  labelNode.fontSize = 14;
  labelNode.lineHeight = { value: 20, unit: "PIXELS" };
  labelNode.characters = label;
  const labelColor = resolveColor("text-primary");
  if (labelColor) labelNode.fills = [{ type: "SOLID", color: labelColor }];
  frame.appendChild(labelNode);

  const inputFrame = figma.createFrame();
  inputFrame.name = `${component.id}_field`;
  inputFrame.layoutMode = "HORIZONTAL";
  inputFrame.primaryAxisAlignItems = "CENTER";
  inputFrame.counterAxisAlignItems = "CENTER";
  inputFrame.resize(320, 44);
  inputFrame.primaryAxisSizingMode = "AUTO";
  inputFrame.counterAxisSizingMode = "FIXED";
  inputFrame.layoutAlign = "STRETCH";
  inputFrame.paddingLeft = 12;
  inputFrame.paddingRight = 12;
  inputFrame.paddingTop = 10;
  inputFrame.paddingBottom = 10;
  inputFrame.cornerRadius = resolveBorderRadius("sm") ?? 4;

  const borderColor = resolveColor(component.tokens["border"] ?? "border");
  if (borderColor) {
    inputFrame.strokes = [{ type: "SOLID", color: borderColor }];
    inputFrame.strokeWeight = 1;
  }
  const bgColor = resolveColor(component.tokens["background"] ?? "background");
  if (bgColor) inputFrame.fills = [{ type: "SOLID", color: bgColor }];

  const placeholder =
    (component.props["placeholder"] as string) ?? "Enter text...";
  const placeholderNode = figma.createText();
  placeholderNode.name = `${component.id}_placeholder`;
  placeholderNode.fontName = { family: "Inter", style: "Regular" };
  placeholderNode.fontSize = 16;
  placeholderNode.lineHeight = { value: 24, unit: "PIXELS" };
  placeholderNode.characters = placeholder;
  const mutedColor = resolveColor("text-muted");
  if (mutedColor)
    placeholderNode.fills = [{ type: "SOLID", color: mutedColor }];
  inputFrame.appendChild(placeholderNode);

  frame.appendChild(inputFrame);
  applyFrameTokens(frame, component.tokens);
  return frame;
}

export function createNavbar(component: UIComponent): FrameNode {
  const frame = figma.createFrame();
  frame.name = component.id;
  frame.layoutMode = "HORIZONTAL";
  frame.primaryAxisSizingMode = "AUTO";
  frame.counterAxisSizingMode = "AUTO";
  frame.primaryAxisAlignItems = "CENTER";
  frame.counterAxisAlignItems = "CENTER";
  frame.itemSpacing = resolveSpacing("lg") ?? 24;

  const padding = resolveSpacing(component.tokens["spacing"] ?? "md") ?? 16;
  frame.paddingTop = padding;
  frame.paddingBottom = padding;
  frame.paddingLeft = resolveSpacing("xl") ?? 32;
  frame.paddingRight = resolveSpacing("xl") ?? 32;

  const navBg = resolveColor(component.tokens["background"] ?? "surface");
  if (navBg) frame.fills = [{ type: "SOLID", color: navBg }];

  const navBorder = resolveColor(component.tokens["border"] ?? "border");
  if (navBorder) {
    frame.strokes = [{ type: "SOLID", color: navBorder }];
    frame.strokeWeight = 1;
  }

  const logo = (component.props["logo"] as string) ?? "Logo";
  const logoNode = figma.createText();
  logoNode.name = `${component.id}_logo`;
  logoNode.fontName = { family: "Inter", style: "Bold" };
  logoNode.fontSize = 20;
  logoNode.lineHeight = { value: 28, unit: "PIXELS" };
  logoNode.characters = logo;
  const logoColor = resolveColor("text-primary");
  if (logoColor) logoNode.fills = [{ type: "SOLID", color: logoColor }];
  frame.appendChild(logoNode);

  const items = (component.props["items"] as unknown[]) ?? [];
  for (var idx = 0; idx < items.length; idx++) {
    var item = items[idx];
    var itemLabel =
      typeof item === "string"
        ? item
        : (item as { label?: string }).label ?? "Item";
    const itemNode = figma.createText();
    itemNode.name = `${component.id}_item`;
    itemNode.fontName = { family: "Inter", style: "Medium" };
    itemNode.fontSize = 16;
    itemNode.lineHeight = { value: 24, unit: "PIXELS" };
    itemNode.characters = itemLabel;
    const textColor = resolveColor("text-secondary");
    if (textColor) itemNode.fills = [{ type: "SOLID", color: textColor }];
    frame.appendChild(itemNode);
  }

  return frame;
}

export function createTable(component: UIComponent): FrameNode {
  const frame = figma.createFrame();
  frame.name = component.id;
  frame.layoutMode = "VERTICAL";
  frame.primaryAxisSizingMode = "AUTO";
  frame.counterAxisSizingMode = "AUTO";
  frame.itemSpacing = 0;
  frame.cornerRadius = resolveBorderRadius("md") ?? 8;
  frame.clipsContent = true;
  frame.fills = [];

  const borderRgb = resolveColor(component.tokens["border"] ?? "border");
  if (borderRgb) {
    frame.strokes = [{ type: "SOLID", color: borderRgb }];
    frame.strokeWeight = 1;
  }

  const columns = (component.props["columns"] as unknown[]) ?? [
    { header: "Column 1" },
    { header: "Column 2" },
    { header: "Column 3" },
  ];
  const rowCount = (component.props["rows"] as number) ?? 3;

  function createTableRow(cells: string[], isHeader: boolean): FrameNode {
    const row = figma.createFrame();
    row.name = component.id + "_" + (isHeader ? "header" : "row");
    row.layoutMode = "HORIZONTAL";
    row.primaryAxisSizingMode = "AUTO";
    row.counterAxisSizingMode = "AUTO";
    row.itemSpacing = 0;

    const bg = resolveColor(isHeader ? "surface" : "background");
    if (bg) row.fills = [{ type: "SOLID", color: bg }];

    if (borderRgb) {
      row.strokes = [{ type: "SOLID", color: borderRgb }];
      row.strokeWeight = 1;
    }

    for (var ci = 0; ci < cells.length; ci++) {
      const cell = figma.createFrame();
      cell.name = "cell";
      cell.layoutMode = "HORIZONTAL";
      cell.primaryAxisSizingMode = "AUTO";
      cell.counterAxisSizingMode = "AUTO";
      cell.primaryAxisAlignItems = "MIN";
      cell.counterAxisAlignItems = "CENTER";
      cell.paddingLeft = 12;
      cell.paddingRight = 12;
      cell.paddingTop = 10;
      cell.paddingBottom = 10;
      cell.fills = [];
      cell.layoutGrow = 1;

      const text = figma.createText();
      text.fontName = {
        family: "Inter",
        style: isHeader ? "Semi Bold" : "Regular",
      };
      text.fontSize = 14;
      text.lineHeight = { value: 20, unit: "PIXELS" };
      text.characters = cells[ci];
      const color = resolveColor(
        isHeader ? "text-primary" : "text-secondary"
      );
      if (color) text.fills = [{ type: "SOLID", color: color }];

      cell.appendChild(text);
      row.appendChild(cell);
    }

    return row;
  }

  var headers: string[] = [];
  for (var hi = 0; hi < columns.length; hi++) {
    var col = columns[hi];
    if (typeof col === "string") {
      headers.push(col);
    } else {
      headers.push(
        (col as { header?: string; name?: string }).header ??
          (col as { header?: string; name?: string }).name ??
          "Column"
      );
    }
  }
  var headerRow = createTableRow(headers, true);
  headerRow.layoutAlign = "STRETCH";
  frame.appendChild(headerRow);

  for (var ri = 0; ri < rowCount; ri++) {
    var cells: string[] = [];
    for (var cj = 0; cj < columns.length; cj++) {
      cells.push("Row " + (ri + 1) + ", Col " + (cj + 1));
    }
    var dataRow = createTableRow(cells, false);
    dataRow.layoutAlign = "STRETCH";
    frame.appendChild(dataRow);
  }

  applyFrameTokens(frame, component.tokens);
  return frame;
}

export function createAvatar(component: UIComponent): FrameNode {
  const frame = figma.createFrame();
  frame.name = component.id;

  const size = (component.props["size"] as string) ?? "md";
  const dimension = size === "sm" ? 32 : size === "lg" ? 48 : 40;
  frame.resize(dimension, dimension);

  frame.layoutMode = "HORIZONTAL";
  frame.primaryAxisSizingMode = "FIXED";
  frame.counterAxisSizingMode = "FIXED";
  frame.primaryAxisAlignItems = "CENTER";
  frame.counterAxisAlignItems = "CENTER";

  const variant = (component.props["variant"] as string) ?? "circle";
  frame.cornerRadius =
    variant === "square" ? resolveBorderRadius("md") ?? 8 : dimension / 2;

  const avatarBg = resolveColor(component.tokens["background"] ?? "primary");
  if (avatarBg) frame.fills = [{ type: "SOLID", color: avatarBg }];

  const initials = (component.props["initials"] as string) ?? "AB";
  const textNode = figma.createText();
  textNode.name = `${component.id}_initials`;
  textNode.fontName = { family: "Inter", style: "Semi Bold" };
  textNode.fontSize = size === "sm" ? 12 : size === "lg" ? 18 : 14;
  textNode.lineHeight = { value: textNode.fontSize + 4, unit: "PIXELS" };
  textNode.characters = initials.substring(0, 2).toUpperCase();
  const avatarTextColor = resolveColor("background");
  if (avatarTextColor)
    textNode.fills = [{ type: "SOLID", color: avatarTextColor }];

  frame.appendChild(textNode);
  return frame;
}

export function createBadge(component: UIComponent): FrameNode {
  const frame = figma.createFrame();
  frame.name = component.id;
  frame.layoutMode = "HORIZONTAL";
  frame.primaryAxisSizingMode = "AUTO";
  frame.counterAxisSizingMode = "AUTO";
  frame.primaryAxisAlignItems = "CENTER";
  frame.counterAxisAlignItems = "CENTER";
  frame.paddingLeft = 8;
  frame.paddingRight = 8;
  frame.paddingTop = 2;
  frame.paddingBottom = 2;
  frame.cornerRadius = resolveBorderRadius("full") ?? 9999;

  const badgeVariant = (component.props["variant"] as string) ?? "default";
  var bgTokenName: string;
  var textTokenName: string;

  switch (badgeVariant) {
    case "success":
      bgTokenName = "success";
      textTokenName = "background";
      break;
    case "warning":
      bgTokenName = "warning";
      textTokenName = "text-primary";
      break;
    case "error":
      bgTokenName = "error";
      textTokenName = "background";
      break;
    default:
      bgTokenName = "secondary";
      textTokenName = "background";
      break;
  }

  const badgeBg = resolveColor(component.tokens["background"] ?? bgTokenName);
  if (badgeBg) frame.fills = [{ type: "SOLID", color: badgeBg }];

  const badgeLabel = (component.props["label"] as string) ?? "Badge";
  const badgeText = figma.createText();
  badgeText.name = `${component.id}_label`;
  badgeText.fontName = { family: "Inter", style: "Medium" };
  badgeText.fontSize = 12;
  badgeText.lineHeight = { value: 16, unit: "PIXELS" };
  badgeText.characters = badgeLabel;
  const badgeTextColor = resolveColor(
    component.tokens["color"] ?? textTokenName
  );
  if (badgeTextColor)
    badgeText.fills = [{ type: "SOLID", color: badgeTextColor }];

  frame.appendChild(badgeText);
  return frame;
}

export function createDivider(component: UIComponent): FrameNode {
  const frame = figma.createFrame();
  frame.name = component.id;

  const divVariant = (component.props["variant"] as string) || "horizontal";
  if (divVariant === "vertical") {
    frame.resize(1, 24);
  } else {
    frame.resize(100, 1);
    frame.layoutAlign = "STRETCH";
  }

  const divColor = resolveColor(component.tokens["color"] ?? "border");
  if (divColor) frame.fills = [{ type: "SOLID", color: divColor }];

  return frame;
}

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
