/**
 * Figma Tree Renderer — renders a Figma node tree (from the backend converter)
 * directly into Figma nodes. Uses layoutSizing* API for reliable layout.
 */

import { loadFonts } from "./nodeFactory";
import { getIconSvg } from "./icons";

// ─── Types for the Figma node tree format ───

interface FigmaColor {
  r: number;
  g: number;
  b: number;
}

interface FigmaFill {
  type: "SOLID";
  color: FigmaColor;
  opacity?: number;
}

interface FigmaStroke {
  type: "SOLID";
  color: FigmaColor;
}

interface FigmaShadow {
  type: "DROP_SHADOW";
  color: { r: number; g: number; b: number; a: number };
  offset: { x: number; y: number };
  radius: number;
  spread?: number;
  visible?: boolean;
  blendMode?: string;
}

export interface FigmaNodeTree {
  type: "FRAME" | "TEXT" | "ICON";
  name?: string;
  children?: FigmaNodeTree[];

  // Icon-specific
  icon?: string;

  // Layout
  layoutMode?: "HORIZONTAL" | "VERTICAL" | "NONE";
  primaryAxisSizingMode?: "AUTO" | "FIXED";
  counterAxisSizingMode?: "AUTO" | "FIXED";
  primaryAxisAlignItems?: "MIN" | "CENTER" | "MAX" | "SPACE_BETWEEN";
  counterAxisAlignItems?: "MIN" | "CENTER" | "MAX";
  layoutAlign?: "STRETCH" | "INHERIT";
  layoutGrow?: number;
  itemSpacing?: number;

  // Size
  width?: number;
  height?: number;

  // Padding
  paddingTop?: number;
  paddingRight?: number;
  paddingBottom?: number;
  paddingLeft?: number;

  // Visual
  fills?: FigmaFill[];
  strokes?: FigmaStroke[];
  strokeWeight?: number;
  strokeAlign?: "INSIDE" | "OUTSIDE" | "CENTER";
  cornerRadius?: number;
  effects?: FigmaShadow[];
  clipsContent?: boolean;
  opacity?: number;

  // Text-specific
  characters?: string;
  fontSize?: number;
  fontWeight?: number;
  lineHeight?: number;
  textAlignHorizontal?: "LEFT" | "CENTER" | "RIGHT";
  letterSpacing?: number;
  textColor?: FigmaColor;
  textDecoration?: "UNDERLINE" | "STRIKETHROUGH";
  textAutoResize?: "NONE" | "WIDTH_AND_HEIGHT" | "HEIGHT";

  // Icon-specific color (same shape as textColor)
  color?: FigmaColor;
}

// ─── Font weight mapping ───

function fontWeightToStyle(weight: number): string {
  if (weight >= 700) return "Bold";
  if (weight >= 600) return "Semi Bold";
  if (weight >= 500) return "Medium";
  return "Regular";
}

// ─── Apply layout sizing AFTER a child is appended to an auto-layout parent ───

function applyChildLayout(
  child: SceneNode,
  childData: FigmaNodeTree,
  parentLayoutMode: string
): void {
  var isHorizontalParent = parentLayoutMode === "HORIZONTAL";

  // ── Primary axis (parent's flow direction) ──
  if (childData.layoutGrow === 1) {
    // layoutGrow → FILL on parent's primary axis
    if (isHorizontalParent) {
      (child as any).layoutSizingHorizontal = "FILL";
    } else {
      (child as any).layoutSizingVertical = "FILL";
    }
  } else {
    // No grow — if child has explicit dimension on primary axis, lock it to FIXED
    // Otherwise Figma defaults to HUG which may override the resize() call
    if (isHorizontalParent && childData.width) {
      (child as any).layoutSizingHorizontal = "FIXED";
    } else if (!isHorizontalParent && childData.height) {
      (child as any).layoutSizingVertical = "FIXED";
    }
  }

  // ── Counter axis (perpendicular to parent's flow) ──
  if (childData.layoutAlign === "STRETCH") {
    // STRETCH → FILL on parent's counter axis
    if (isHorizontalParent) {
      (child as any).layoutSizingVertical = "FILL";
    } else {
      (child as any).layoutSizingHorizontal = "FILL";
    }
  } else {
    // No stretch — if child has explicit dimension on counter axis, lock it to FIXED
    if (isHorizontalParent && childData.height) {
      (child as any).layoutSizingVertical = "FIXED";
    } else if (!isHorizontalParent && childData.width) {
      (child as any).layoutSizingHorizontal = "FIXED";
    }
  }
}

// ─── Render a TEXT node ───

function renderTextNode(node: FigmaNodeTree): TextNode {
  var textNode = figma.createText();
  textNode.name = node.name || "text";

  var weight = node.fontWeight || 400;
  var style = fontWeightToStyle(weight);
  textNode.fontName = { family: "Inter", style: style };

  if (node.fontSize) textNode.fontSize = node.fontSize;
  if (node.lineHeight) {
    textNode.lineHeight = { value: node.lineHeight, unit: "PIXELS" };
  }

  textNode.characters = node.characters || "";

  if (node.textColor) {
    textNode.fills = [{ type: "SOLID", color: node.textColor }];
  }

  if (node.textAlignHorizontal) {
    textNode.textAlignHorizontal = node.textAlignHorizontal;
  }

  if (node.letterSpacing) {
    textNode.letterSpacing = { value: node.letterSpacing, unit: "PIXELS" };
  }

  if (node.textDecoration) {
    textNode.textDecoration = node.textDecoration;
  }

  // textAutoResize — set before any layout properties
  if (node.textAutoResize) {
    textNode.textAutoResize = node.textAutoResize;
  } else if (node.layoutGrow || node.layoutAlign === "STRETCH") {
    textNode.textAutoResize = "HEIGHT";
  }

  // NOTE: layoutAlign/layoutGrow are applied AFTER appendChild
  // via applyChildLayout() — not set here.

  return textNode;
}

// ─── Render a FRAME node ───

function renderFrameNode(node: FigmaNodeTree): FrameNode {
  var frame = figma.createFrame();
  frame.name = node.name || "frame";

  // Layout mode
  if (node.layoutMode && node.layoutMode !== "NONE") {
    frame.layoutMode = node.layoutMode;
  } else if (node.layoutMode !== "NONE") {
    frame.layoutMode = "VERTICAL";
  }

  // Sizing mode
  if (node.primaryAxisSizingMode) {
    frame.primaryAxisSizingMode = node.primaryAxisSizingMode;
  } else {
    frame.primaryAxisSizingMode = "AUTO";
  }
  if (node.counterAxisSizingMode) {
    frame.counterAxisSizingMode = node.counterAxisSizingMode;
  } else {
    frame.counterAxisSizingMode = "AUTO";
  }

  // Alignment
  if (node.primaryAxisAlignItems) {
    frame.primaryAxisAlignItems = node.primaryAxisAlignItems;
  }
  if (node.counterAxisAlignItems) {
    frame.counterAxisAlignItems = node.counterAxisAlignItems;
  }

  // Item spacing
  if (node.itemSpacing !== undefined && node.itemSpacing !== null) {
    frame.itemSpacing = node.itemSpacing;
  }

  // Size — apply explicit dimensions
  var w = node.width || 0;
  var h = node.height || 0;
  if (w > 0 && h > 0) {
    frame.resize(w, h);
  } else if (w > 0) {
    frame.resize(w, frame.height);
  } else if (h > 0) {
    frame.resize(frame.width, h);
  }

  // NOTE: layoutAlign/layoutGrow are applied AFTER appendChild
  // via applyChildLayout() — not set here on the frame itself.

  // Padding
  if (node.paddingTop !== undefined) frame.paddingTop = node.paddingTop;
  if (node.paddingRight !== undefined) frame.paddingRight = node.paddingRight;
  if (node.paddingBottom !== undefined) frame.paddingBottom = node.paddingBottom;
  if (node.paddingLeft !== undefined) frame.paddingLeft = node.paddingLeft;

  // Fills
  if (node.fills && node.fills.length > 0) {
    var figmaFills: SolidPaint[] = [];
    for (var i = 0; i < node.fills.length; i++) {
      var fill = node.fills[i];
      var paint: SolidPaint = {
        type: "SOLID",
        color: fill.color,
      };
      if (fill.opacity !== undefined && fill.opacity < 1) {
        (paint as any).opacity = fill.opacity;
      }
      figmaFills.push(paint);
    }
    frame.fills = figmaFills;
  } else {
    frame.fills = [];
  }

  // Strokes
  if (node.strokes && node.strokes.length > 0) {
    var figmaStrokes: SolidPaint[] = [];
    for (var j = 0; j < node.strokes.length; j++) {
      figmaStrokes.push({
        type: "SOLID",
        color: node.strokes[j].color,
      });
    }
    frame.strokes = figmaStrokes;
    if (node.strokeWeight) frame.strokeWeight = node.strokeWeight;
    if (node.strokeAlign) frame.strokeAlign = node.strokeAlign;
  }

  // Corner radius
  if (node.cornerRadius !== undefined) {
    frame.cornerRadius = node.cornerRadius;
  }

  // Effects (shadows)
  if (node.effects && node.effects.length > 0) {
    var figmaEffects: DropShadowEffect[] = [];
    for (var k = 0; k < node.effects.length; k++) {
      var eff = node.effects[k];
      figmaEffects.push({
        type: "DROP_SHADOW",
        color: {
          r: eff.color.r,
          g: eff.color.g,
          b: eff.color.b,
          a: eff.color.a,
        },
        offset: { x: eff.offset.x, y: eff.offset.y },
        radius: eff.radius,
        spread: eff.spread || 0,
        visible: eff.visible !== false,
        blendMode: "NORMAL",
      });
    }
    frame.effects = figmaEffects;
  }

  // Clips content
  if (node.clipsContent) {
    frame.clipsContent = true;
  }

  // Opacity
  if (node.opacity !== undefined && node.opacity < 1) {
    frame.opacity = node.opacity;
  }

  // Render children — append FIRST, then apply layout sizing
  var children = node.children || [];
  var parentLayoutMode = node.layoutMode || "VERTICAL";
  for (var ci = 0; ci < children.length; ci++) {
    var childData = children[ci];
    var childNode = renderNode(childData);
    if (childNode) {
      frame.appendChild(childNode);
      // Apply layout sizing AFTER child is in the auto-layout parent
      applyChildLayout(childNode, childData, parentLayoutMode);
    }
  }

  return frame;
}

// ─── Render an ICON node (Lucide SVG) ───

function renderIconNode(node: FigmaNodeTree): SceneNode | null {
  var iconName = node.icon || "";
  var size = node.width || 24;

  // Convert FigmaColor {r,g,b} (0-1) to hex string
  var color = node.textColor || node.color || { r: 0.39, g: 0.45, b: 0.53 };
  var hexR = Math.round((color as any).r * 255)
    .toString(16)
    .padStart(2, "0");
  var hexG = Math.round((color as any).g * 255)
    .toString(16)
    .padStart(2, "0");
  var hexB = Math.round((color as any).b * 255)
    .toString(16)
    .padStart(2, "0");
  var hexColor = "#" + hexR + hexG + hexB;

  var svgStr = getIconSvg(iconName, hexColor, size);
  if (!svgStr) {
    // Unknown icon — create a small placeholder
    var ph = figma.createFrame();
    ph.name = "icon_" + iconName;
    ph.resize(size, size);
    ph.fills = [
      { type: "SOLID", color: { r: 0.88, g: 0.91, b: 0.94 } },
    ];
    ph.cornerRadius = 4;
    return ph;
  }

  try {
    var svgNode = figma.createNodeFromSvg(svgStr);
    svgNode.name = "icon_" + iconName;
    // Resize to desired size (SVG might be 24x24 already)
    if (svgNode.width !== size || svgNode.height !== size) {
      svgNode.resize(size, size);
    }
    return svgNode;
  } catch (e) {
    console.error("Failed to create SVG icon:", iconName, e);
    var ph2 = figma.createFrame();
    ph2.name = "icon_" + iconName;
    ph2.resize(size, size);
    ph2.fills = [
      { type: "SOLID", color: { r: 0.88, g: 0.91, b: 0.94 } },
    ];
    ph2.cornerRadius = 4;
    return ph2;
  }
}

// ─── Main render function ───

function renderNode(node: FigmaNodeTree): SceneNode | null {
  if (!node) return null;

  try {
    if (node.type === "ICON") {
      return renderIconNode(node);
    }
    if (node.type === "TEXT") {
      return renderTextNode(node);
    }
    return renderFrameNode(node);
  } catch (e) {
    console.error("Failed to render node:", node.name, e);
    // Create a red placeholder so the rest of the design still renders
    var placeholder = figma.createFrame();
    placeholder.name = "ERROR: " + (node.name || "unknown");
    placeholder.fills = [{ type: "SOLID", color: { r: 1, g: 0, b: 0 } }];
    placeholder.resize(100, 30);
    return placeholder;
  }
}

// ─── Public API ───

export interface DesignScreen {
  screen_name: string;
  tree: FigmaNodeTree;
}

export interface GenerateDesignResponse {
  success: boolean;
  screens: DesignScreen[];
  errors: string[];
  metadata: Record<string, unknown>;
}

/** Render a complete design screen from a Figma node tree. */
export async function renderDesignScreen(screen: DesignScreen): Promise<FrameNode> {
  await loadFonts();

  var tree = screen.tree;

  // Ensure root is a proper frame
  tree.type = "FRAME";
  tree.name = screen.screen_name;
  if (!tree.width) tree.width = 1440;

  var rootFrame = renderFrameNode(tree);

  // Root frame: force fixed dimensions
  rootFrame.primaryAxisSizingMode = "FIXED";
  rootFrame.counterAxisSizingMode = "FIXED";

  // Safety cap: if height exceeds viewport, clip it
  var MAX_HEIGHT = 1440;
  if (rootFrame.height > MAX_HEIGHT) {
    rootFrame.resize(rootFrame.width, MAX_HEIGHT);
    rootFrame.clipsContent = true;
  }

  return rootFrame;
}

/** Render all design screens, placing them side by side. */
export async function renderAllDesignScreens(
  screens: DesignScreen[]
): Promise<FrameNode[]> {
  var SCREEN_GAP = 100;
  var frames: FrameNode[] = [];
  var xOffset = 0;

  for (var i = 0; i < screens.length; i++) {
    var frame = await renderDesignScreen(screens[i]);
    frame.x = xOffset;
    frame.y = 0;

    figma.currentPage.appendChild(frame);
    frames.push(frame);

    xOffset += frame.width + SCREEN_GAP;
  }

  // Scroll viewport to show all rendered frames
  if (frames.length > 0) {
    figma.viewport.scrollAndZoomIntoView(frames);
  }

  return frames;
}
