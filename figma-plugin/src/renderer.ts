import { Screen, UIComponent } from "./types";
import { createNode, isLayoutType } from "./componentMapper";
import { loadFonts } from "./nodeFactory";
import { resolveColor, LAYOUT } from "./tokens";

/** Recursively render a UIComponent tree into Figma nodes. */
function renderComponent(
  component: UIComponent,
  parentType?: string
): SceneNode | null {
  const node = createNode(component);
  if (!node) return null;

  const isContainer =
    isLayoutType(component.type) || component.type === "card";

  if (isContainer && component.children.length > 0 && "appendChild" in node) {
    const parentFrame = node as FrameNode;

    // Section with title prop: inject heading before children
    if (component.type === "section" && component.props["title"]) {
      const titleText = figma.createText();
      titleText.name = `${component.id}_title`;
      titleText.fontName = { family: "Inter", style: "Semi Bold" };
      titleText.fontSize = 20;
      titleText.lineHeight = { value: 28, unit: "PIXELS" };
      titleText.characters = component.props["title"] as string;

      const titleColor = resolveColor("text-primary");
      if (titleColor) {
        titleText.fills = [{ type: "SOLID", color: titleColor }];
      }
      parentFrame.appendChild(titleText);
    }

    // Card with title prop: inject title text before children
    if (component.type === "card" && component.props["title"]) {
      const titleText = figma.createText();
      titleText.name = `${component.id}_title`;
      titleText.fontName = { family: "Inter", style: "Semi Bold" };
      titleText.fontSize = 16;
      titleText.lineHeight = { value: 24, unit: "PIXELS" };
      titleText.characters = component.props["title"] as string;

      const titleColor = resolveColor("text-primary");
      if (titleColor) {
        titleText.fills = [{ type: "SOLID", color: titleColor }];
      }
      parentFrame.appendChild(titleText);
    }

    for (const child of component.children) {
      const childNode = renderComponent(child, component.type);
      if (childNode) {
        parentFrame.appendChild(childNode);

        // Cards and columns inside rows grow equally
        if (
          component.type === "row" &&
          (child.type === "card" || child.type === "column") &&
          "layoutGrow" in childNode
        ) {
          (childNode as FrameNode).layoutGrow = 1;
        }

        // Horizontal dividers stretch to fill parent width
        if (
          child.type === "divider" &&
          ((child.props["variant"] as string) ?? "horizontal") ===
            "horizontal" &&
          "layoutAlign" in childNode
        ) {
          (childNode as FrameNode).layoutAlign = "STRETCH";
        }
      }
    }
  }

  return node;
}

/** Render a complete screen as a top-level Figma frame. */
export async function renderScreen(screen: Screen): Promise<FrameNode> {
  await loadFonts();

  const root = figma.createFrame();
  root.name = screen.screen_name;
  root.resize(LAYOUT.maxWidth, 900);
  root.layoutMode = "VERTICAL";
  root.primaryAxisSizingMode = "AUTO";
  root.counterAxisSizingMode = "FIXED";
  root.itemSpacing = 0;

  root.paddingLeft = LAYOUT.margin;
  root.paddingRight = LAYOUT.margin;
  root.paddingTop = LAYOUT.margin;
  root.paddingBottom = LAYOUT.margin;

  const bgToken = screen.tokens["background"] ?? "background";
  const bgColor = resolveColor(bgToken);
  if (bgColor) root.fills = [{ type: "SOLID", color: bgColor }];

  for (const component of screen.components) {
    const node = renderComponent(component);
    if (node) {
      root.appendChild(node);
      // Direct children stretch to fill root frame width
      if ("layoutAlign" in node) {
        (node as FrameNode).layoutAlign = "STRETCH";
      }
    }
  }

  return root;
}

/** Render all screens, placing them side by side on the canvas. */
export async function renderAllScreens(
  screens: Screen[]
): Promise<FrameNode[]> {
  const SCREEN_GAP = 100;
  const frames: FrameNode[] = [];
  let xOffset = 0;

  for (const screen of screens) {
    if (!screen.validation.is_valid) {
      console.warn(
        `[renderer] Skipping "${screen.screen_name}" — validation failed: ` +
          screen.validation.errors.join(", ")
      );
      continue;
    }

    const frame = await renderScreen(screen);
    frame.x = xOffset;
    frame.y = 0;

    figma.currentPage.appendChild(frame);
    frames.push(frame);

    xOffset += frame.width + SCREEN_GAP;
  }

  return frames;
}
