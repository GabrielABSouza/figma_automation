import { UIComponent, LAYOUT_TYPES } from "./types";
import {
  createSection,
  createRow,
  createColumn,
  createStack,
  createText,
  createCard,
  createButton,
  createInput,
  createNavbar,
  createTable,
  createAvatar,
  createBadge,
  createDivider,
} from "./nodeFactory";

/** Factory function signature: takes a UIComponent, returns a SceneNode. */
export type ComponentFactory = (component: UIComponent) => SceneNode;

/** Registry of component type -> factory function. */
const FACTORY_MAP: Record<string, ComponentFactory> = {
  section: createSection,
  row: createRow,
  column: createColumn,
  stack: createStack,
  text: createText,
  card: createCard,
  button: createButton,
  input: createInput,
  navbar: createNavbar,
  table: createTable,
  avatar: createAvatar,
  badge: createBadge,
  divider: createDivider,
};

/** Check if a component type is a layout (container) type. */
export function isLayoutType(type: string): boolean {
  return LAYOUT_TYPES.has(type);
}

/** Check if a component type has a registered factory. */
export function isSupported(type: string): boolean {
  return type in FACTORY_MAP;
}

/** Get the factory function for a component type. Returns null if unsupported. */
export function getFactory(type: string): ComponentFactory | null {
  return FACTORY_MAP[type] ?? null;
}

/** Create a Figma node from a UIComponent. Returns null if unsupported. */
export function createNode(component: UIComponent): SceneNode | null {
  const factory = getFactory(component.type);
  if (!factory) {
    console.warn(
      `[componentMapper] Unsupported type "${component.type}" (id: ${component.id}). Skipping.`
    );
    return null;
  }
  return factory(component);
}

/** Register a new factory (for post-MVP extension). */
export function registerFactory(
  type: string,
  factory: ComponentFactory
): void {
  FACTORY_MAP[type] = factory;
}
