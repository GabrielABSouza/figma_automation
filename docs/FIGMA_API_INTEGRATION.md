# Figma API Integration Guide

> Reference document for integrating with the Figma REST API in the automation pipeline.
> This document captures the essential API details needed for our backend and plugin.

---

## Table of Contents

- [1. Authentication](#1-authentication)
- [2. Files API](#2-files-api)
- [3. Components API](#3-components-api)
- [4. Variables API](#4-variables-api)
- [5. Errors](#5-errors)
- [6. Webhooks (Post-MVP)](#6-webhooks-post-mvp)
- [7. Implementation Notes](#7-implementation-notes)

---

## 1. Authentication

### Base URL

```
https://api.figma.com
```

### Auth Strategy for This Project

| Phase | Method | Reason |
|-------|--------|--------|
| **MVP** | Personal Access Token | Simple, no OAuth server needed, one user |
| **Post-MVP** | OAuth 2.0 | Multi-user, token refresh, delegated access |

---

### 1.1 Personal Access Token (MVP)

**How to generate:**
1. Login to Figma → Account menu → **Settings**
2. **Security** tab → **Personal access tokens** → **Generate new token**
3. Set scopes (see below) and copy the token immediately

**Required scopes for MVP:**

| Scope | Purpose |
|-------|---------|
| `file_content:read` | Read file structure, nodes, layers |
| `files:read` | Access file metadata |

**Usage — `X-Figma-Token` header:**

```bash
curl -sH 'X-Figma-Token: <PERSONAL_ACCESS_TOKEN>' \
  'https://api.figma.com/v1/files/:file_key'
```

**Backend implementation:**

```python
# backend/config.py — already configured
figma_access_token: str = ""  # loaded from .env

# Usage in requests
headers = {
    "X-Figma-Token": settings.figma_access_token
}
```

**Environment variable:**
```
FIGMA_ACCESS_TOKEN=figd_...
```

---

### 1.2 OAuth 2.0 (Post-MVP)

For multi-user support. Flow:

```
User clicks "Connect Figma"
        ↓
Redirect to Figma OAuth URL
        ↓
User authorizes scopes
        ↓
Figma redirects to our callback with `code`
        ↓
Exchange `code` for `access_token` + `refresh_token`
        ↓
Store tokens, use access_token for API calls
```

#### OAuth URL (Authorization)

```
GET https://www.figma.com/oauth?
  client_id=:client_id&
  redirect_uri=:callback&
  scope=:scope&
  state=:state&
  response_type=code&
  code_challenge=:challenge   # recommended (PKCE, S256 only)
```

| Parameter | Value |
|-----------|-------|
| `client_id` | From OAuth app registration |
| `redirect_uri` | Must match registered callback URL |
| `scope` | Comma-separated: `file_content:read,files:read` |
| `state` | Random value, validate on callback |
| `response_type` | `code` (only supported value) |
| `code_challenge` | PKCE S256 challenge (recommended) |

#### Token Exchange

```
POST https://api.figma.com/v1/oauth/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic <BASE64(client_id:client_secret)>

Body: redirect_uri=:callback&code=:code&grant_type=authorization_code
```

**Response:**

```json
{
  "user_id_string": "<USER_ID>",
  "access_token": "<TOKEN>",
  "token_type": "bearer",
  "expires_in": 7776000,
  "refresh_token": "<REFRESH_TOKEN>"
}
```

> **Note:** `expires_in` = 90 days (7776000 seconds). Must implement refresh before expiry.

> **Note:** Auth codes expire in **30 seconds**. Exchange must happen immediately.

> **Note:** `user_id` (numeric) is deprecated. Use `user_id_string`.

#### Token Refresh

```
POST https://api.figma.com/v1/oauth/refresh
Content-Type: application/x-www-form-urlencoded
Authorization: Basic <BASE64(client_id:client_secret)>

Body: refresh_token=:refresh_token
```

**Response:**

```json
{
  "access_token": "<NEW_TOKEN>",
  "token_type": "bearer",
  "expires_in": 7776000
}
```

> **Important:** Refreshing invalidates the previous access token. Only one active token per user per app.

#### OAuth Usage (Bearer token)

```bash
curl -sH 'Authorization: Bearer <TOKEN>' \
  'https://api.figma.com/v1/files/:file_key'
```

#### Scopes Needed (Full Platform)

| Scope | Purpose | Phase |
|-------|---------|-------|
| `file_content:read` | Read files, nodes, layers | MVP |
| `files:read` | File metadata | MVP |
| `file_comments:read` | Read comments (feedback loop) | Post-MVP |
| `file_comments:write` | Post comments | Post-MVP |

#### OAuth App Registration

1. Go to `figma.com/developers/apps`
2. **Create a new app** → associate with team/org
3. Copy **Client ID** and **Client Secret** (shown only once)
4. Configure redirect URLs, scopes, publish (private for internal use)

**App states:** Draft → Private (team/org only, no Figma review) → Public (requires Figma review)

---

### 1.3 Auth Abstraction in Backend

```python
# Planned: backend/figma/auth.py

class FigmaAuth:
    """Unified auth — uses PAT in MVP, OAuth in production."""

    def get_headers(self, user_id: str | None = None) -> dict[str, str]:
        if user_id and self._has_oauth_token(user_id):
            return {"Authorization": f"Bearer {self._get_oauth_token(user_id)}"}
        return {"X-Figma-Token": settings.figma_access_token}
```

---

## 2. Files API — Node Structure & Types

### 2.1 Figma File Tree Model

Every Figma file is a tree of nodes:

```
DOCUMENT (root)
  └── CANVAS (page)
        ├── FRAME (container / auto-layout)
        │     ├── TEXT
        │     ├── RECTANGLE
        │     ├── INSTANCE (component instance)
        │     └── FRAME (nested)
        ├── COMPONENT (reusable component definition)
        ├── COMPONENT_SET (variant group)
        ├── SECTION (organizational)
        └── GROUP
```

### 2.2 Global Node Properties

Every node in the tree has these properties:

| Property | Type | Description |
|----------|------|-------------|
| `id` | String | Unique ID within document |
| `name` | String | User-given name in Figma |
| `visible` | Boolean (default: true) | Visibility on canvas |
| `type` | String | Node type enum (see below) |
| `rotation` | Number | Rotation if not 0 |
| `boundVariables` | Map | Variables applied to fields (links to Variables API) |
| `componentPropertyReferences` | Map | Links to component property definitions |

### 2.3 Node Types — Relevance for Our Pipeline

#### Critical for Renderer (MVP)

| Node Type | What It Is | Our Use |
|-----------|------------|---------|
| `DOCUMENT` | Root of every file | Entry point when reading files |
| `CANVAS` | A page in Figma | Each screen → one canvas or frame on canvas |
| `FRAME` | Container with layout | **Primary building block** — screens, sections, rows |
| `TEXT` | Text layer | Labels, headings, body text |
| `RECTANGLE` | Rectangle shape | Backgrounds, dividers, placeholders |
| `COMPONENT` | Reusable component def | Design system components |
| `COMPONENT_SET` | Variant group | Component with variants (e.g. Button/primary, Button/ghost) |
| `INSTANCE` | Instance of a component | Placed components on screen |

#### Secondary (Post-MVP)

| Node Type | What It Is | Our Use |
|-----------|------------|---------|
| `SECTION` | Organization container | Screen sections in Figma |
| `GROUP` | Grouped layers | Same properties as FRAME |
| `VECTOR` | Vector shape | Icons, custom shapes |
| `ELLIPSE` | Ellipse/circle | Avatars, indicators |
| `LINE` | Line | Dividers |

#### Not Needed

`STICKY`, `SHAPE_WITH_TEXT`, `CONNECTOR`, `WASHI_TAPE`, `TABLE`, `TABLE_CELL` — FigJam only, irrelevant for UI generation.

---

### 2.4 FRAME — The Key Node Type

Frames are the backbone of our renderer. Every screen, section, and layout container maps to a FRAME.

#### Auto-Layout Properties (Critical)

Our renderer must set these when creating layout:

| Property | Type | Values | Purpose |
|----------|------|--------|---------|
| `layoutMode` | String | `NONE`, `HORIZONTAL`, `VERTICAL`, `GRID` | **Direction of auto-layout** |
| `layoutSizingHorizontal` | String | `FIXED`, `HUG`, `FILL` | Horizontal sizing behavior |
| `layoutSizingVertical` | String | `FIXED`, `HUG`, `FILL` | Vertical sizing behavior |
| `primaryAxisAlignItems` | String | `MIN`, `CENTER`, `MAX`, `SPACE_BETWEEN` | Main axis alignment (like `justify-content`) |
| `counterAxisAlignItems` | String | `MIN`, `CENTER`, `MAX`, `BASELINE` | Cross axis alignment (like `align-items`) |
| `itemSpacing` | Number | default: 0 | Gap between children (like `gap`) |
| `paddingTop/Right/Bottom/Left` | Number | default: 0 | Padding inside frame |
| `layoutWrap` | String | `NO_WRAP`, `WRAP` | Wrapping (like `flex-wrap`) |
| `counterAxisSpacing` | Number | default: 0 | Gap between wrapped rows |
| `clipsContent` | Boolean | | Overflow hidden |

#### Grid Layout Properties (for complex layouts)

| Property | Type | Purpose |
|----------|------|---------|
| `gridRowCount` | Number | Rows in grid |
| `gridColumnCount` | Number | Columns in grid |
| `gridRowGap` | Number | Row gap |
| `gridColumnGap` | Number | Column gap |
| `gridColumnsSizing` | String | CSS `grid-template-columns` equivalent |
| `gridRowsSizing` | String | CSS `grid-template-rows` equivalent |

#### Visual Properties

| Property | Type | Purpose |
|----------|------|---------|
| `fills` | Paint[] | Background fills (replaces deprecated `backgroundColor`) |
| `strokes` | Paint[] | Border strokes |
| `strokeWeight` | Number | Border width |
| `strokeAlign` | String | `INSIDE`, `OUTSIDE`, `CENTER` |
| `cornerRadius` | Number | Border radius (all corners) |
| `rectangleCornerRadii` | Number[4] | Per-corner radius `[TL, TR, BR, BL]` |
| `cornerSmoothing` | Number | 0–1, where 0.6 = iOS squircle |
| `effects` | Effect[] | Shadows, blurs |
| `opacity` | Number | 0–1 |
| `blendMode` | BlendMode | Layer blending |

#### Size & Position

| Property | Type | Purpose |
|----------|------|---------|
| `absoluteBoundingBox` | Rectangle | Position & size in absolute coordinates |
| `absoluteRenderBounds` | Rectangle\|null | Actual visual bounds (incl. shadows) |
| `minWidth/maxWidth` | Number\|null | Size constraints |
| `minHeight/maxHeight` | Number\|null | Size constraints |

#### Children Properties (for children of auto-layout frames)

| Property | Type | Purpose |
|----------|------|---------|
| `layoutAlign` | String | `INHERIT`, `STRETCH` — stretch along cross axis |
| `layoutPositioning` | String | `AUTO`, `ABSOLUTE` — opt out of auto-layout |

---

### 2.5 TEXT Node

All properties of VECTOR, plus:

| Property | Type | Purpose |
|----------|------|---------|
| `characters` | String | The actual text content |
| `style` | TypeStyle | Font family, weight, size, line height, etc. |
| `characterStyleOverrides` | Number[] | Per-character style references |
| `styleOverrideTable` | Map | Style override definitions |
| `lineTypes` | LineType[] | `ORDERED`, `UNORDERED`, `NONE` per line |
| `lineIndentations` | Number[] | Indentation per line |

---

### 2.6 COMPONENT & INSTANCE

#### COMPONENT (definition)

Same as FRAME, plus:

| Property | Type | Purpose |
|----------|------|---------|
| `componentPropertyDefinitions` | Map | Property definitions (name → type, defaultValue) |

#### COMPONENT_SET (variant group)

Same as FRAME, plus:

| Property | Type | Purpose |
|----------|------|---------|
| `componentPropertyDefinitions` | Map | Shared properties across variants |

#### INSTANCE (placed component)

Same as FRAME, plus:

| Property | Type | Purpose |
|----------|------|---------|
| `componentId` | String | ID of source component |
| `componentProperties` | Map | Property values set on this instance |
| `overrides` | Overrides[] | Fields overridden from component |
| `isExposedInstance` | Boolean | If exposed to parent component |

> **Key insight for our pipeline:** When we render a UI, we create INSTANCE nodes that reference COMPONENT definitions from the design system. The `componentId` links them. The `componentProperties` map lets us set props (label, variant, etc).

---

### 2.7 SECTION

Lightweight organizational container:

| Property | Type | Purpose |
|----------|------|---------|
| `sectionContentsHidden` | Boolean | Contents visibility |
| `devStatus` | Object\|null | "Ready for dev" or "Completed" |
| `fills` | Paint[] | Background |
| `children` | Node[] | Contained nodes |

---

### 2.8 API Endpoints — Full Reference

All endpoints require `file_content:read` scope.

#### GET /v1/files/:key — Get Full File

Returns the entire file as a JSON tree. This is our primary read endpoint.

```
GET /v1/files/:key?ids=1:2,1:3&depth=2&branch_data=false
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | path | yes | File key (from URL: `figma.com/:type/:key/:name`) |
| `version` | query | no | Specific version ID |
| `ids` | query | no | Comma-separated node IDs (returns subset + ancestors) |
| `depth` | query | no | Tree depth limit (1=pages only, 2=pages+top-level) |
| `geometry` | query | no | Set to `paths` for vector data |
| `branch_data` | query | no | Include branch metadata (default: false) |
| `plugin_data` | query | no | Comma-separated plugin IDs to include data from |

**Response:**

```json
{
  "name": "My Design File",
  "lastModified": "2024-01-15T10:30:00Z",
  "version": "123456",
  "editorType": "figma",
  "document": { "type": "DOCUMENT", "children": [...] },
  "components": { "node_id": { "key": "...", "name": "Button", ... } },
  "componentSets": { "node_id": { "key": "...", "name": "Button", ... } },
  "styles": { "style_id": { "key": "...", "name": "Primary", "styleType": "FILL" } },
  "schemaVersion": 0
}
```

> **Key for our pipeline:** The `components` and `componentSets` maps at the top level give us component metadata without traversing the tree. The `styles` map gives us all published styles.

**Error codes:** 403 (invalid/expired token), 404 (file not found)

---

#### GET /v1/files/:key/nodes — Get Specific Nodes

Returns only the requested nodes and their subtrees. More efficient than full file fetch.

```
GET /v1/files/:key/nodes?ids=1:2,1:3&depth=1
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | path | yes | File key |
| `ids` | query | yes | Comma-separated node IDs |
| `depth` | query | no | Subtree depth limit |
| `version` | query | no | Specific version ID |

**Response:**

```json
{
  "name": "My Design File",
  "nodes": {
    "1:2": {
      "document": { "id": "1:2", "type": "FRAME", ... },
      "components": { ... },
      "styles": { ... }
    },
    "1:3": null
  }
}
```

> **Important:** Node values can be `null` (node doesn't exist). Always handle this.

**Error codes:** 400 (invalid parameter), 403, 404

---

#### GET /v1/images/:key — Render Nodes as Images

Renders specific nodes as PNG/SVG/JPG/PDF. Images expire after **30 days**. Max **32 megapixels**.

```
GET /v1/images/:key?ids=1:2,1:3&format=png&scale=2
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | path | yes | File key |
| `ids` | query | yes | Comma-separated node IDs to render |
| `scale` | query | no | 0.01–4, image scale factor |
| `format` | query | no | `jpg`, `png`, `svg`, `pdf` |
| `svg_outline_text` | query | no | Outline text in SVGs (default: true) |
| `svg_include_id` | query | no | Include layer names as SVG `id` attrs |
| `contents_only` | query | no | Exclude overlapping content (default: true) |
| `use_absolute_bounds` | query | no | Export with full bounds (useful for text) |

**Response:**

```json
{
  "images": {
    "1:2": "https://figma-alpha-api.s3.us-west-2.amazonaws.com/images/...",
    "1:3": null
  }
}
```

> **Note:** `null` in the images map = render failed (node invisible, 0% opacity, or invalid).

**Error codes:** 400, 403, 404, 500 (render error)

---

#### GET /v1/files/:key/images — Get Image Fills

Returns download URLs for all user-uploaded images in the file (image fills). URLs expire after **14 days**.

```
GET /v1/files/:key/images
```

**Response:**

```json
{
  "images": {
    "image_ref_hash": "https://s3-alpha.figma.com/img/..."
  }
}
```

> Maps `imageRef` (from Paint objects) → download URL. Useful for extracting assets.

---

#### GET /v1/files/:key/meta — File Metadata Only

Lightweight endpoint — returns file metadata without the node tree. Requires `file_metadata:read` scope (separate from `file_content:read`).

```
GET /v1/files/:key/meta
```

**Response:**

```json
{
  "file": {
    "name": "My File",
    "folder_name": "Project X",
    "creator": { ... },
    "version": "123456",
    "editorType": "figma",
    "url": "https://www.figma.com/file/..."
  }
}
```

---

#### Endpoint Tier & Phase Summary

| Endpoint | Tier | Scope | Our Phase |
|----------|------|-------|-----------|
| `GET /v1/files/:key` | Tier 1 | `file_content:read` | **MVP** |
| `GET /v1/files/:key/nodes` | Tier 1 | `file_content:read` | **MVP** |
| `GET /v1/images/:key` | Tier 1 | `file_content:read` | Post-MVP |
| `GET /v1/files/:key/images` | Tier 2 | `file_content:read` | Post-MVP |
| `GET /v1/files/:key/meta` | Tier 3 | `file_metadata:read` | Post-MVP |

---

### 2.9 Mapping: Our UI Schema → Figma Nodes

This is the critical translation table for our **renderer** and **Design System Mapper**:

| Our Schema `type` | Figma Node Type | Key Properties to Set |
|--------------------|-----------------|----------------------|
| `section` | FRAME | `layoutMode: VERTICAL`, padding, fills |
| `row` | FRAME | `layoutMode: HORIZONTAL`, `itemSpacing` |
| `column` | FRAME | `layoutMode: VERTICAL`, `itemSpacing` |
| `stack` | FRAME | `layoutMode: NONE` (absolute positioning) |
| `card` | FRAME | `fills`, `cornerRadius`, `effects` (shadow), padding |
| `button` | INSTANCE | `componentId` → Button component, `componentProperties` |
| `input` | INSTANCE | `componentId` → Input component, `componentProperties` |
| `text` | TEXT | `characters`, `style` (TypeStyle) |
| `navbar` | INSTANCE or FRAME | Component if in DS, else composed FRAME |
| `table` | FRAME (grid) | `layoutMode: GRID`, `gridRowCount`, `gridColumnCount` |
| `avatar` | INSTANCE | `componentId` → Avatar component |
| `badge` | INSTANCE | `componentId` → Badge component |
| `divider` | RECTANGLE or LINE | `fills`, `strokeWeight` |

---

### 2.10 Deprecated Properties to Avoid

| Deprecated | Use Instead |
|------------|-------------|
| `background` (FRAME) | `fills` |
| `backgroundColor` (FRAME) | `fills` |
| `horizontalPadding` | `paddingLeft` + `paddingRight` |
| `verticalPadding` | `paddingTop` + `paddingBottom` |
| `preserveRatio` | `targetAspectRatio` |
| `isMaskOutline` | `maskType` |
| `prototypeStartNodeID` | `flowStartingPoints` |
| `lineHeightPercent` (TypeStyle) | `lineHeightPercentFontSize` |

---

### 2.11 Property Types Reference (Renderer-Critical)

These are the Figma property types our renderer and mapper need to construct when creating nodes.

#### Color (RGBA)

```json
{ "r": 0.15, "g": 0.38, "b": 0.92, "a": 1.0 }
```

All channels 0–1 (not 0–255). To convert hex `#2563EB`:
```python
r, g, b = 0x25/255, 0x63/255, 0xEB/255  # → 0.145, 0.388, 0.922
```

#### Paint (fills and strokes)

Every `fills` and `strokes` array contains Paint objects:

| Property | Type | Notes |
|----------|------|-------|
| `type` | String | `SOLID`, `GRADIENT_LINEAR`, `GRADIENT_RADIAL`, `IMAGE` |
| `visible` | Boolean | default: true |
| `opacity` | Number | default: 1 |
| `color` | Color | For SOLID paints |
| `gradientStops` | ColorStop[] | For gradient paints |
| `scaleMode` | String | For IMAGE paints: `FILL`, `FIT`, `TILE`, `STRETCH` |
| `imageRef` | String | For IMAGE paints: reference to download via Images API |
| `boundVariables` | Map | Variable bindings (links to Variables API) |

**Solid fill example (our primary color):**
```json
{
  "type": "SOLID",
  "visible": true,
  "opacity": 1,
  "color": { "r": 0.145, "g": 0.388, "b": 0.922, "a": 1.0 }
}
```

**Gradient fill example:**
```json
{
  "type": "GRADIENT_LINEAR",
  "gradientHandlePositions": [
    { "x": 0.5, "y": 0 },
    { "x": 0.5, "y": 1 },
    { "x": 0, "y": 0 }
  ],
  "gradientStops": [
    { "position": 0, "color": { "r": 1, "g": 1, "b": 1, "a": 1 } },
    { "position": 1, "color": { "r": 0, "g": 0, "b": 0, "a": 1 } }
  ]
}
```

#### Effect (shadows and blurs)

| Property | Type | Notes |
|----------|------|-------|
| `type` | String | `DROP_SHADOW`, `INNER_SHADOW`, `LAYER_BLUR`, `BACKGROUND_BLUR` |
| `visible` | Boolean | Is active? |
| `radius` | Number | Blur/shadow radius |
| `color` | Color | Shadow color (shadows only) |
| `offset` | Vector | Shadow x/y offset (shadows only) |
| `spread` | Number | Shadow spread (default: 0) |
| `blendMode` | BlendMode | Blend mode |

**Drop shadow example (our `md` shadow token):**
```json
{
  "type": "DROP_SHADOW",
  "visible": true,
  "radius": 6,
  "color": { "r": 0, "g": 0, "b": 0, "a": 0.07 },
  "offset": { "x": 0, "y": 4 },
  "spread": 0,
  "blendMode": "NORMAL"
}
```

#### TypeStyle (text formatting)

Critical properties for our TEXT nodes:

| Property | Type | Notes |
|----------|------|-------|
| `fontFamily` | String | e.g. "Inter", "Roboto" |
| `fontWeight` | Number | 400 (regular), 600 (semibold), 700 (bold) |
| `fontSize` | Number | In px |
| `lineHeightPx` | Number | Line height in px |
| `letterSpacing` | Number | In px |
| `textAlignHorizontal` | String | `LEFT`, `RIGHT`, `CENTER`, `JUSTIFIED` |
| `textAlignVertical` | String | `TOP`, `CENTER`, `BOTTOM` |
| `textCase` | String | `ORIGINAL`, `UPPER`, `LOWER`, `TITLE` |
| `textDecoration` | String | `NONE`, `UNDERLINE`, `STRIKETHROUGH` |
| `textAutoResize` | String | `NONE`, `HEIGHT`, `WIDTH_AND_HEIGHT` |
| `fills` | Paint[] | Text color (array of paints, not a simple color) |
| `italic` | Boolean | Italic flag |

**TypeStyle for our `heading-2` token:**
```json
{
  "fontFamily": "Inter",
  "fontWeight": 600,
  "fontSize": 24,
  "lineHeightPx": 32,
  "letterSpacing": 0,
  "textAlignHorizontal": "LEFT",
  "textAlignVertical": "TOP",
  "textAutoResize": "HEIGHT",
  "fills": [{ "type": "SOLID", "color": { "r": 0.059, "g": 0.09, "b": 0.165, "a": 1 } }]
}
```

#### Component Property Types

Properties that components expose for customization:

| ComponentPropertyType | Description | Example |
|-----------------------|-------------|---------|
| `BOOLEAN` | Show/hide toggle | `{ "type": "BOOLEAN", "defaultValue": true }` |
| `TEXT` | Editable text content | `{ "type": "TEXT", "defaultValue": "Button" }` |
| `INSTANCE_SWAP` | Swap nested instance | `{ "type": "INSTANCE_SWAP", "preferredValues": [...] }` |
| `VARIANT` | Select variant | `{ "type": "VARIANT", "defaultValue": "primary", "variantOptions": ["primary", "secondary"] }` |

**ComponentPropertyDefinition** (on COMPONENT/COMPONENT_SET):
```json
{
  "Label#123": { "type": "TEXT", "defaultValue": "Click me" },
  "Variant": { "type": "VARIANT", "defaultValue": "primary", "variantOptions": ["primary", "secondary", "ghost"] },
  "Show Icon": { "type": "BOOLEAN", "defaultValue": false }
}
```

**ComponentProperty** (on INSTANCE — values set on placed component):
```json
{
  "Label#123": { "type": "TEXT", "value": "Submit" },
  "Variant": { "type": "VARIANT", "value": "primary" },
  "Show Icon": { "type": "BOOLEAN", "value": true }
}
```

> **Key for our pipeline:** The Design System Mapper agent maps our schema props to ComponentProperty values. The renderer uses these to configure INSTANCE nodes.

#### VariableAlias (links to Variables)

```json
{ "type": "VARIABLE_ALIAS", "id": "VariableID:123:456" }
```

Found in `boundVariables` on nodes and paints. Links a property to a Figma Variable (design token). The `id` is used with the Variables API to resolve the actual value.

#### Rectangle (bounding box)

```json
{ "x": 100, "y": 200, "width": 400, "height": 300 }
```

#### Vector (2D point)

```json
{ "x": 10, "y": 20 }
```

#### Style (published style reference)

| Property | Type | Notes |
|----------|------|-------|
| `key` | String | Global style key |
| `name` | String | e.g. "Primary/Default", "Heading 1" |
| `description` | String | User-entered description |
| `styleType` | String | `FILL`, `TEXT`, `EFFECT`, `GRID` |
| `remote` | Boolean | Whether it's from an external library |

Styles are referenced via the `styles` map on nodes: `{ "fill": "style_id_123", "text": "style_id_456" }`

#### Component & ComponentSet (metadata)

| Property | Type | Notes |
|----------|------|-------|
| `key` | String | Global component key |
| `name` | String | Component name |
| `description` | String | User-entered description |
| `componentSetId` | String? | Parent variant group (COMPONENT only) |
| `documentationLinks` | DocLink[] | External docs |
| `remote` | Boolean | From external library? |

---

### 2.12 Property Types — Not Needed for MVP

These types are related to prototyping, interactions, and FigJam — skip for now:

- **Interaction, Trigger, Action** — prototype interactions
- **Navigation, SimpleTransition, DirectionTransition** — prototype transitions
- **Easing, EasingFunctionCubicBezier, EasingFunctionSpring** — animation curves
- **ConnectorEndpoint, ConnectorLineType, ConnectorTextBackground** — FigJam connectors
- **ShapeType** — FigJam shapes
- **Expression, ConditionalAction, SetVariableAction** — prototype variables/logic
- **TransformModifier** — transform groups (beta)
- **Measurement, Annotation** — Dev Mode features

---

## 3. Components & Styles API

These endpoints are for **published** components and styles in team/file libraries. For local (unpublished) components, use `GET /v1/files/:key` (the `components` map in the response — see section 2.8).

### 3.1 Data Types

#### Component (published metadata)

| Property | Type | Description |
|----------|------|-------------|
| `key` | String | **Global unique component key** (used to fetch by key) |
| `file_key` | String | File that contains this component |
| `node_id` | String | Node ID within the file |
| `thumbnail_url` | String | Thumbnail image URL |
| `name` | String | Component name |
| `description` | String | Publisher-entered description |
| `created_at` | String | ISO 8601 UTC |
| `updated_at` | String | ISO 8601 UTC |
| `user` | User | Last updater |
| `containing_frame` | FrameInfo | Parent frame info |

#### ComponentSet (published variant group)

Same fields as Component. Represents a group of variant components.

#### Style (published style)

Same as Component, plus:

| Property | Type | Description |
|----------|------|-------------|
| `style_type` | String | `FILL`, `TEXT`, `EFFECT`, `GRID` |

#### FrameInfo (containing frame metadata)

| Property | Type | Description |
|----------|------|-------------|
| `node_id` | String | Frame node ID |
| `name` | String | Frame name |
| `backgroundColor` | String | Frame background color |
| `pageId` | String | Page ID |
| `pageName` | String | Page name |
| `containingComponentSet` | String | Parent component set (if any) |

---

### 3.2 Endpoints

#### Component Endpoints

| Endpoint | Scope | Description |
|----------|-------|-------------|
| `GET /v1/teams/:team_id/components` | `team_library_content:read` | Paginated list of all published components in team |
| `GET /v1/files/:file_key/components` | `library_content:read` | All published components in a file library |
| `GET /v1/components/:key` | `library_assets:read` | Single component by global key |

#### Component Set Endpoints

| Endpoint | Scope | Description |
|----------|-------|-------------|
| `GET /v1/teams/:team_id/component_sets` | `team_library_content:read` | Paginated list of all component sets in team |
| `GET /v1/files/:file_key/component_sets` | `library_content:read` | All component sets in a file library |
| `GET /v1/component_sets/:key` | `library_assets:read` | Single component set by global key |

#### Style Endpoints

| Endpoint | Scope | Description |
|----------|-------|-------------|
| `GET /v1/teams/:team_id/styles` | `team_library_content:read` | Paginated list of all published styles in team |
| `GET /v1/files/:file_key/styles` | `library_content:read` | All published styles in a file library |
| `GET /v1/styles/:key` | `library_assets:read` | Single style by global key |

> All component/style library endpoints are **Tier 3**.

---

### 3.3 Pagination (Team Endpoints)

Team endpoints return paginated results:

```json
{
  "meta": {
    "components": [...],
    "cursor": {
      "before": 12345,
      "after": 67890
    }
  }
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page_size` | Number | 30 | Items per page (max 1000) |
| `after` | Number | — | Cursor: fetch items after this ID |
| `before` | Number | — | Cursor: fetch items before this ID |

> `after` and `before` are mutually exclusive. Cursor values are internal integers, not node IDs.

---

### 3.4 Response Examples

**GET /v1/files/:file_key/components:**

```json
{
  "status": 200,
  "error": false,
  "meta": {
    "components": [
      {
        "key": "abc123def456",
        "file_key": "xYzFile789",
        "node_id": "1:42",
        "thumbnail_url": "https://figma-alpha-api.s3.../img/...",
        "name": "Button",
        "description": "Primary action button with variants",
        "created_at": "2024-01-10T10:00:00Z",
        "updated_at": "2024-03-15T14:30:00Z",
        "containing_frame": {
          "node_id": "1:40",
          "name": "Components",
          "pageId": "0:1",
          "pageName": "Design System",
          "containingComponentSet": "ButtonSet"
        }
      }
    ]
  }
}
```

**GET /v1/components/:key:**

```json
{
  "status": 200,
  "error": false,
  "meta": {
    "key": "abc123def456",
    "file_key": "xYzFile789",
    "node_id": "1:42",
    "name": "Button",
    "description": "Primary action button",
    "thumbnail_url": "https://..."
  }
}
```

---

### 3.5 Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid request (message in response) |
| 403 | Insufficient permission or invalid/expired token |
| 404 | Resource not found |

---

### 3.6 Strategy for Our Pipeline

#### Two Approaches to Get Design System Components

| Approach | Endpoint | Scope | When to Use |
|----------|----------|-------|-------------|
| **A: File-based (MVP)** | `GET /v1/files/:key` | `file_content:read` | We know the DS file key. Returns `components` map with node structure + property definitions |
| **B: Library-based** | `GET /v1/files/:file_key/components` | `library_content:read` | We want published metadata (thumbnails, descriptions) without full file tree |

**MVP Recommendation: Approach A**

```
1. GET /v1/files/:ds_file_key → full design system file
2. Extract `components` + `componentSets` maps from response
3. For each component, traverse node tree to get `componentPropertyDefinitions`
4. Build our internal `components.json` from this data
```

**Why:** Approach A gives us everything in one call — component structure, property definitions, variants, and the node tree. Approach B only gives metadata (name, key, thumbnail) without the actual component structure.

#### Mapping Flow: Figma DS → Our Design System

```
GET /v1/files/:ds_file_key
        ↓
Extract COMPONENT_SET nodes (variant groups)
        ↓
For each: read componentPropertyDefinitions
        ↓
Map to our components.json format:
  - type → component name
  - variantOptions → variants array
  - property definitions → props schema
        ↓
Extract styles map
        ↓
Map to our tokens.json format:
  - FILL styles → color tokens
  - TEXT styles → typography tokens
  - EFFECT styles → shadow tokens
```

#### Required Scopes Summary

| Phase | Scopes Needed |
|-------|---------------|
| MVP | `file_content:read` (covers file-based component reading) |
| Post-MVP | + `library_content:read`, `library_assets:read` (for library browsing) |
| Team-wide | + `team_library_content:read` (for team-level component listing) |

---

## 4. Variables API (Design Tokens)

Variables in Figma = **design tokens**. Colors, spacing, typography values, booleans — organized in collections with modes (light/dark, brand A/B).

### 4.1 Critical Limitation

> **Enterprise only.** The Variables API requires a Full seat in an Enterprise org. This impacts our MVP strategy — see section 4.6.

| Action | Plan | Account | File Permission | Scope |
|--------|------|---------|-----------------|-------|
| GET | Enterprise | Any org member | View access | `file_variables:read` |
| POST | Enterprise | Full seats, admins | Edit access | `file_variables:write` |

---

### 4.2 Core Concepts

#### Variable

A single design token with values per mode:

| Property | Type | Description |
|----------|------|-------------|
| `id` | String | Unique ID (e.g. `VariableID:1:3`) |
| `name` | String | Token name (e.g. `colors/primary`) |
| `key` | String | Stable key |
| `variableCollectionId` | String | Parent collection |
| `resolvedType` | String | `BOOLEAN`, `FLOAT`, `STRING`, `COLOR` |
| `valuesByMode` | Map | `{ modeId: value }` — different value per mode |
| `description` | String | Description |
| `scopes` | VariableScope[] | UI picker visibility |
| `codeSyntax` | Map | Platform code names: `{ WEB: "var(--primary)", iOS: "primaryColor" }` |
| `hiddenFromPublishing` | Boolean | Hidden from library consumers |

#### VariableCollection

A grouping of related variables sharing the same modes:

| Property | Type | Description |
|----------|------|-------------|
| `id` | String | Unique ID |
| `name` | String | Collection name (e.g. "Colors", "Spacing") |
| `modes` | Mode[] | `[{ modeId, name }]` — e.g. "Light", "Dark" |
| `defaultModeId` | String | Default mode |
| `variableIds` | String[] | All variables in this collection |
| `remote` | Boolean | From external library? |

#### Extended Collections (Theming)

Extended collections inherit from a parent and override specific values — ideal for theme variants:

```
Colors (root collection)
  ├── Light mode: primary = #2563EB
  └── Dark mode: primary = #60A5FA
        ↓ extends
Brand B Colors (extended)
  ├── Light mode: primary = #DC2626 (override)
  └── Dark mode: primary = #F87171 (override)
```

---

### 4.3 Variable Types & Scopes

| resolvedType | Value Format | Our Use |
|--------------|-------------|---------|
| `COLOR` | `{ r, g, b, a }` (0-1) | Color tokens |
| `FLOAT` | Number | Spacing, border radius, font size, opacity |
| `STRING` | String | Font family, font style, text content |
| `BOOLEAN` | Boolean | Feature flags, visibility toggles |

#### Scopes (UI picker visibility)

**COLOR scopes:** `ALL_SCOPES`, `ALL_FILLS`, `FRAME_FILL`, `SHAPE_FILL`, `TEXT_FILL`, `STROKE_COLOR`, `EFFECT_COLOR`

**FLOAT scopes:** `ALL_SCOPES`, `CORNER_RADIUS`, `WIDTH_HEIGHT`, `GAP`, `STROKE_FLOAT`, `OPACITY`, `FONT_SIZE`, `LINE_HEIGHT`, `LETTER_SPACING`, etc.

**STRING scopes:** `ALL_SCOPES`, `TEXT_CONTENT`, `FONT_FAMILY`, `FONT_STYLE`

---

### 4.4 Endpoints

#### GET /v1/files/:file_key/variables/local — Local + Remote Variables

Returns all local variables AND remote variables used in the file, with full mode values.

```
GET /v1/files/:file_key/variables/local
```

**Scope:** `file_variables:read` | **Tier:** 2

**Response:**

```json
{
  "status": 200,
  "meta": {
    "variables": {
      "VariableID:1:3": {
        "id": "VariableID:1:3",
        "name": "colors/primary",
        "key": "abc123",
        "variableCollectionId": "VariableCollectionId:1:2",
        "resolvedType": "COLOR",
        "valuesByMode": {
          "1:0": { "r": 0.145, "g": 0.388, "b": 0.922, "a": 1.0 },
          "1:1": { "r": 0.376, "g": 0.647, "b": 0.980, "a": 1.0 }
        },
        "remote": false,
        "description": "Primary brand color",
        "scopes": ["ALL_FILLS"],
        "codeSyntax": { "WEB": "--color-primary", "iOS": "colorPrimary" }
      },
      "VariableID:1:5": {
        "id": "VariableID:1:5",
        "name": "spacing/md",
        "resolvedType": "FLOAT",
        "valuesByMode": {
          "1:0": 16
        },
        "scopes": ["GAP", "WIDTH_HEIGHT"]
      }
    },
    "variableCollections": {
      "VariableCollectionId:1:2": {
        "id": "VariableCollectionId:1:2",
        "name": "Design Tokens",
        "modes": [
          { "modeId": "1:0", "name": "Light" },
          { "modeId": "1:1", "name": "Dark" }
        ],
        "defaultModeId": "1:0",
        "variableIds": ["VariableID:1:3", "VariableID:1:5"]
      }
    }
  }
}
```

---

#### GET /v1/files/:file_key/variables/published — Published Variables

Returns published variables **without mode values** (metadata only).

```
GET /v1/files/:file_key/variables/published
```

**Scope:** `file_variables:read` | **Tier:** 2

**Response:**

```json
{
  "meta": {
    "variables": {
      "VariableID:1:3": {
        "id": "VariableID:1:3",
        "subscribed_id": "VariableID:5:6",
        "name": "colors/primary",
        "key": "abc123",
        "resolvedType": "COLOR",
        "updatedAt": "2024-03-15T10:00:00Z"
      }
    },
    "variableCollections": {
      "VariableCollectionId:1:2": {
        "id": "VariableCollectionId:1:2",
        "subscribed_id": "VariableCollectionId:7:8",
        "name": "Design Tokens",
        "key": "def456"
      }
    }
  }
}
```

> **Note:** No `valuesByMode` or `modes` in published response. Use `/variables/local` on the same file to get actual values.

> **Note:** `subscribed_id` changes every time the variable is modified and published. `id` and `key` are stable.

---

#### POST /v1/files/:file_key/variables — Bulk Create/Update/Delete

Atomic bulk operations on variables, collections, modes, and values.

```
POST /v1/files/:file_key/variables
Content-Type: application/json
```

**Scope:** `file_variables:write` | **Tier:** 3 | **Max body:** 4MB

**Request body (4 arrays, processed in order):**

```json
{
  "variableCollections": [
    { "action": "CREATE", "id": "temp_coll", "name": "New Tokens", "initialModeId": "temp_mode" }
  ],
  "variableModes": [
    { "action": "UPDATE", "id": "temp_mode", "name": "Default", "variableCollectionId": "temp_coll" }
  ],
  "variables": [
    { "action": "CREATE", "id": "temp_var", "name": "primary", "resolvedType": "COLOR", "variableCollectionId": "temp_coll" }
  ],
  "variableModeValues": [
    { "variableId": "temp_var", "modeId": "temp_mode", "value": { "r": 0.145, "g": 0.388, "b": 0.922, "a": 1 } }
  ]
}
```

**Response:**

```json
{
  "status": 200,
  "meta": {
    "tempIdToRealId": {
      "temp_coll": "VariableCollectionId:1:2",
      "temp_mode": "1:0",
      "temp_var": "VariableID:1:3"
    }
  }
}
```

**Key behaviors:**
- All operations are **atomic** — any validation failure rolls back everything
- **Temporary IDs** can reference objects created in the same request
- Max 40 modes per collection, max 5000 variables per collection
- Variable names must be unique within a collection
- Aliases cannot form cycles

**Error codes:** 400, 403, 404, 413 (body > 4MB)

---

### 4.5 Mapping: Figma Variables → Our tokens.json

```
GET /v1/files/:ds_file_key/variables/local
        ↓
Group variables by collection name
        ↓
For each variable:
  resolvedType=COLOR  → tokens.colors[name] = valuesByMode[defaultMode]
  resolvedType=FLOAT  → tokens.spacing[name] or tokens.borderRadius[name]
                        (based on scopes or name convention)
  resolvedType=STRING → tokens.typography[name].fontFamily
        ↓
Map modes → theme variants:
  mode "Light" → tokens.json (default)
  mode "Dark"  → tokens-dark.json
```

**Variable name → token category mapping:**

| Variable Name Pattern | Token Category | resolvedType |
|-----------------------|---------------|--------------|
| `colors/*` or scope `*_FILL` | `tokens.colors` | COLOR |
| `spacing/*` or scope `GAP` | `tokens.spacing` | FLOAT |
| `radius/*` or scope `CORNER_RADIUS` | `tokens.borderRadius` | FLOAT |
| `font-size/*` or scope `FONT_SIZE` | `tokens.typography.*.fontSize` | FLOAT |
| `font-family/*` or scope `FONT_FAMILY` | `tokens.typography.*.fontFamily` | STRING |
| `shadow/*` or scope `EFFECT_*` | `tokens.shadows` | (via Effect styles, not variables) |

---

### 4.6 Strategy: Enterprise vs Non-Enterprise

| Scenario | Token Source | Approach |
|----------|-------------|----------|
| **Enterprise plan** | Variables API | `GET /variables/local` → auto-populate `tokens.json` |
| **Non-Enterprise** | Manual / Styles API | Parse styles from `GET /v1/files/:key` (`styles` map) + manual `tokens.json` |
| **Either** | Static config | Hand-craft `tokens.json` (our current default) |

**MVP Decision:** Start with static `tokens.json` (already created). Add Variables API integration as optional enhancement for Enterprise users.

```python
# backend/figma/variables.py (planned)
async def sync_tokens_from_figma(file_key: str) -> DesignTokens:
    """Fetch variables from Figma and convert to our token format.
    Falls back to static tokens.json if Variables API unavailable."""
```

#### Scopes Update

| Phase | Scopes Needed |
|-------|---------------|
| MVP | `file_content:read` |
| With Variables | + `file_variables:read` |
| Write-back | + `file_variables:write` |

---

## 5. Errors & Rate Limits

### 5.1 HTTP Error Codes

| Code | Name | Description | Our Handling |
|------|------|-------------|--------------|
| **400** | Bad Request | Invalid/malformed params, or request too large (timeout) | Validate params before sending. Reduce `ids` or `depth` if payload too big |
| **403** | Forbidden | Invalid token, expired token, insufficient permissions, or HTTP instead of HTTPS | Refresh OAuth token or re-check PAT. Always use HTTPS |
| **404** | Not Found | File or resource doesn't exist | Validate file key before pipeline run |
| **429** | Rate Limited | Too many requests (per-user for OAuth) | Implement exponential backoff. Wait ~60s before retry |
| **500** | Internal Server Error | Usually large image render timeouts | Reduce image render batch size. Retry with fewer nodes |

### 5.2 Error Handling Strategy for Backend

```python
# backend/figma/client.py (planned)

class FigmaAPIError(Exception):
    def __init__(self, status: int, message: str): ...

class FigmaRateLimitError(FigmaAPIError): ...
class FigmaAuthError(FigmaAPIError): ...

async def _handle_response(response: httpx.Response) -> dict:
    match response.status_code:
        case 200:
            return response.json()
        case 400:
            raise FigmaAPIError(400, f"Bad request: {response.text}")
        case 403:
            raise FigmaAuthError(403, "Auth failed — check token/permissions")
        case 404:
            raise FigmaAPIError(404, "Resource not found")
        case 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise FigmaRateLimitError(429, f"Rate limited, retry after {retry_after}s")
        case 500:
            raise FigmaAPIError(500, "Figma server error — reduce request size")
```

### 5.3 Rate Limit Strategy

- Rate limits are **per-user** (per OAuth token or PAT)
- No specific limit numbers published by Figma
- **Our approach:**
  - Cache `GET /v1/files/:key` responses (design system file rarely changes)
  - Batch node requests with `ids` param instead of multiple calls
  - Implement retry with exponential backoff: 1s → 2s → 4s → max 60s
  - For 429 errors, respect `Retry-After` header if present

---

## 6. Webhooks (Post-MVP)

> **Waiting for documentation page.**

---

## 7. Implementation Notes

### Client Architecture

```
backend/
  ├── figma/                    # Figma integration module
  │   ├── __init__.py
  │   ├── auth.py              # Auth abstraction (PAT + OAuth)
  │   ├── client.py            # HTTP client (httpx async) + error handling + retry
  │   ├── files.py             # Files API wrapper (GET file, GET nodes, GET images)
  │   ├── components.py        # Components API wrapper (file + team + single)
  │   └── variables.py         # Variables API wrapper (local, published, POST)
```

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| `httpx` async client | Non-blocking, fits FastAPI async pattern |
| PAT for MVP | No OAuth server needed, single-user scenario |
| Auth abstraction layer | Swap PAT → OAuth without changing API wrappers |
| PKCE for OAuth | Security best practice, required for public apps |
| File-based DS reading (Approach A) | One call gets components + structure + property definitions |
| Static tokens.json for MVP | Variables API is Enterprise-only; fallback to manual config |
| Cache DS file responses | DS file changes rarely; avoids rate limits |

### Environment Variables

```env
# MVP
FIGMA_ACCESS_TOKEN=figd_...

# Post-MVP (OAuth)
FIGMA_CLIENT_ID=...
FIGMA_CLIENT_SECRET=...
FIGMA_REDIRECT_URI=https://...
```

### Consolidated Scope Requirements

| Phase | Scopes | Endpoints Unlocked |
|-------|--------|--------------------|
| **MVP** | `file_content:read` | Files, Nodes, Images, file-level Components/Styles |
| + Variables | `file_variables:read` | Variables local + published (Enterprise only) |
| + Library browsing | `library_content:read`, `library_assets:read` | File/single component + style library endpoints |
| + Team library | `team_library_content:read` | Team-level component/style listing |
| + Variable write | `file_variables:write` | POST variables (Enterprise only) |
| + OAuth | `file_content:read` (+ above) | Same endpoints, multi-user |
| + Feedback loop | `file_comments:read`, `file_comments:write` | Comments API |

### Full API Endpoint Map

| # | Endpoint | Tier | MVP? | Purpose |
|---|----------|------|------|---------|
| 1 | `GET /v1/files/:key` | 1 | Yes | Read file tree + components + styles |
| 2 | `GET /v1/files/:key/nodes` | 1 | Yes | Read specific nodes |
| 3 | `GET /v1/images/:key` | 1 | No | Render nodes as images |
| 4 | `GET /v1/files/:key/images` | 2 | No | Download image fills |
| 5 | `GET /v1/files/:key/meta` | 3 | No | File metadata only |
| 6 | `GET /v1/files/:key/components` | 3 | No | Published file components |
| 7 | `GET /v1/teams/:id/components` | 3 | No | Published team components |
| 8 | `GET /v1/components/:key` | 3 | No | Single component by key |
| 9 | `GET /v1/files/:key/component_sets` | 3 | No | Published file component sets |
| 10 | `GET /v1/teams/:id/component_sets` | 3 | No | Published team component sets |
| 11 | `GET /v1/component_sets/:key` | 3 | No | Single component set by key |
| 12 | `GET /v1/files/:key/styles` | 3 | No | Published file styles |
| 13 | `GET /v1/teams/:id/styles` | 3 | No | Published team styles |
| 14 | `GET /v1/styles/:key` | 3 | No | Single style by key |
| 15 | `GET /v1/files/:key/variables/local` | 2 | No | Local variables (Enterprise) |
| 16 | `GET /v1/files/:key/variables/published` | 2 | No | Published variables (Enterprise) |
| 17 | `POST /v1/files/:key/variables` | 3 | No | Bulk variable CRUD (Enterprise) |
