// ─── Token Data (from backend/design_system/tokens.json) ───

export const COLORS: Record<string, string> = {
  primary: "#2563EB",
  "primary-hover": "#1D4ED8",
  secondary: "#64748B",
  success: "#16A34A",
  warning: "#F59E0B",
  error: "#DC2626",
  background: "#FFFFFF",
  surface: "#F8FAFC",
  border: "#E2E8F0",
  "text-primary": "#0F172A",
  "text-secondary": "#475569",
  "text-muted": "#94A3B8",
};

export const SPACING: Record<string, number> = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  "2xl": 48,
};

export interface TypographyToken {
  fontSize: number;
  fontWeight: number;
  lineHeight: number;
}

export const TYPOGRAPHY: Record<string, TypographyToken> = {
  "heading-1": { fontSize: 32, fontWeight: 700, lineHeight: 40 },
  "heading-2": { fontSize: 24, fontWeight: 600, lineHeight: 32 },
  "heading-3": { fontSize: 20, fontWeight: 600, lineHeight: 28 },
  body: { fontSize: 16, fontWeight: 400, lineHeight: 24 },
  "body-small": { fontSize: 14, fontWeight: 400, lineHeight: 20 },
  caption: { fontSize: 12, fontWeight: 400, lineHeight: 16 },
};

export const BORDER_RADIUS: Record<string, number> = {
  sm: 4,
  md: 8,
  lg: 12,
  full: 9999,
};

export const SHADOWS: Record<string, string> = {
  sm: "0 1px 2px rgba(0,0,0,0.05)",
  md: "0 4px 6px rgba(0,0,0,0.07)",
  lg: "0 10px 15px rgba(0,0,0,0.1)",
};

// ─── Layout Rules (from backend/design_system/rules.json) ───

export const LAYOUT = {
  maxWidth: 1440,
  gridColumns: 12,
  gutter: 24,
  margin: 48,
} as const;

// ─── Resolver Functions ───

export interface FigmaRGB {
  r: number;
  g: number;
  b: number;
}

/** Parse hex color (#RRGGBB) to Figma's {r, g, b} format (0-1 range). */
export function hexToFigmaRGB(hex: string): FigmaRGB {
  const h = hex.replace("#", "");
  return {
    r: parseInt(h.substring(0, 2), 16) / 255,
    g: parseInt(h.substring(2, 4), 16) / 255,
    b: parseInt(h.substring(4, 6), 16) / 255,
  };
}

/** Resolve a bare color token name to Figma RGB. Returns null if not found. */
export function resolveColor(tokenName: string): FigmaRGB | null {
  const hex = COLORS[tokenName];
  if (!hex) return null;
  return hexToFigmaRGB(hex);
}

/** Resolve a spacing token name to pixel value. */
export function resolveSpacing(tokenName: string): number | null {
  return SPACING[tokenName] ?? null;
}

/** Resolve a typography variant name. Falls back to "body" if not found. */
export function resolveTypography(variant: string): TypographyToken {
  return TYPOGRAPHY[variant] ?? TYPOGRAPHY["body"];
}

/** Resolve border radius token to pixel value. */
export function resolveBorderRadius(tokenName: string): number | null {
  return BORDER_RADIUS[tokenName] ?? null;
}

/** Parse a CSS shadow string into components. Returns null on invalid input. */
export function parseShadow(
  shadowStr: string
): {
  offsetX: number;
  offsetY: number;
  blur: number;
  r: number;
  g: number;
  b: number;
  a: number;
} | null {
  const match = shadowStr.match(
    /^(\d+)\s+(\d+)px\s+(\d+)px\s+rgba\((\d+),(\d+),(\d+),([\d.]+)\)$/
  );
  if (!match) return null;
  const [, offsetX, offsetY, blur, r, g, b, a] = match;
  return {
    offsetX: parseInt(offsetX),
    offsetY: parseInt(offsetY),
    blur: parseInt(blur),
    r: parseInt(r),
    g: parseInt(g),
    b: parseInt(b),
    a: parseFloat(a),
  };
}

/** Map fontWeight number to Figma font style string. */
export function fontWeightToStyle(weight: number): string {
  if (weight >= 700) return "Bold";
  if (weight >= 600) return "Semi Bold";
  if (weight >= 500) return "Medium";
  return "Regular";
}
