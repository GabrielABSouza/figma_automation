/** Component type strings — layout types are structural, the rest are DS components. */
export type LayoutType = "section" | "row" | "column" | "stack";
export type LeafType = "text" | "card" | "button";
export type ComponentType = LayoutType | LeafType;

export const LAYOUT_TYPES: ReadonlySet<string> = new Set([
  "section",
  "row",
  "column",
  "stack",
]);

// ─── API Response Types (mirrors backend/api/models.py) ───

export interface UIComponent {
  id: string;
  type: string;
  props: Record<string, unknown>;
  tokens: Record<string, string>;
  children: UIComponent[];
}

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface Screen {
  screen_name: string;
  components: UIComponent[];
  tokens: Record<string, string>;
  metadata: Record<string, unknown>;
  validation: ValidationResult;
}

export interface GenerateUIResponse {
  success: boolean;
  screens: Screen[];
  errors: string[];
  metadata: Record<string, unknown>;
}

// ─── Plugin Message Types (code.ts <-> ui.html) ───

export interface RenderMessage {
  type: "render";
  payload: GenerateUIResponse;
}

export type PluginMessage = RenderMessage;
