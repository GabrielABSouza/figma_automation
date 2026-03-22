# Figma Plugin API — Learnings & Pitfalls

Documento de referencia com aprendizados sobre a Figma Plugin API,
especialmente auto-layout, TextNode e ordem de operacoes.

---

## 1. textAutoResize (TextNode) — A Propriedade Mais Importante

Controla como o text node redimensiona para caber o conteudo.

| Valor | Width | Height | Compativel com Fill Width? | Compativel com Fill Height? |
|---|---|---|---|---|
| `"WIDTH_AND_HEIGHT"` (default) | Auto (hug) | Auto (hug) | **NAO** — conflita | **NAO** — conflita |
| `"HEIGHT"` | **Fixo** (controlado externamente) | Auto (hug) | **SIM** | **NAO** |
| `"NONE"` | Fixo | Fixo | SIM | SIM |
| `"TRUNCATE"` (deprecated) | Fixo | Fixo | SIM | SIM |

### Regra Critica

**Quando um TextNode tem `layoutGrow = 1` ou `layoutAlign = "STRETCH"`,
DEVE ter `textAutoResize = "HEIGHT"`.**

O default `"WIDTH_AND_HEIGHT"` significa "o texto determina sua propria largura",
o que conflita com "o parent determina a largura do texto" (layoutGrow/STRETCH).

Sem isso, o texto nao reflow dentro do espaco alocado pelo auto-layout,
causando texto vertical (1 caractere por linha) ou texto invisivel.

### Padrao Correto

```typescript
// Texto que preenche a largura do parent
textNode.textAutoResize = "HEIGHT";  // DEVE vir antes de layoutGrow
textNode.layoutGrow = 1;             // Ou layoutSizingHorizontal = "FILL"
```

### Padrao Incorreto (causa texto vertical)

```typescript
// textAutoResize nao definido → default "WIDTH_AND_HEIGHT"
textNode.layoutGrow = 1;  // Conflito! Texto tenta auto-width E fill ao mesmo tempo
```

**Fonte:** https://developers.figma.com/docs/plugins/api/properties/TextNode-textautoresize/

---

## 2. Sizing Modes — primaryAxisSizingMode & counterAxisSizingMode

### Eixos por layoutMode

| layoutMode | Primary Axis (controlado por primaryAxisSizingMode) | Counter Axis (controlado por counterAxisSizingMode) |
|---|---|---|
| `"VERTICAL"` | Vertical (height) | Horizontal (width) |
| `"HORIZONTAL"` | Horizontal (width) | Vertical (height) |

### Valores

| Valor | Significado |
|---|---|
| `"FIXED"` | Tamanho fixo, definido por resize() |
| `"AUTO"` | Hug contents — tamanho determinado pelos filhos |

### Regra Critica: AUTO vs layoutGrow

**Um parent com `primaryAxisSizingMode = "AUTO"` NAO PODE ter filhos com `layoutGrow = 1`
no mesmo eixo.** O parent nao pode simultaneamente "abracar" (hug) o conteudo
E ter um filho que "preenche" (fill) o espaco.

Isto causa comportamento imprevisivel — o Figma ignora silenciosamente um dos dois.

### Exemplo Problematico

```
FRAME (VERTICAL, primaryAxisSizingMode = "AUTO") ← Hug height
  └── CHILD (layoutGrow = 1) ← Fill height
  // CONFLITO: parent quer hug, child quer fill
```

### Exemplo Correto

```
FRAME (VERTICAL, primaryAxisSizingMode = "FIXED", height = 900)
  └── CHILD (layoutGrow = 1) ← Fill: preenche os 900px disponíveis
```

**Fonte:** https://developers.figma.com/docs/plugins/api/properties/nodes-primaryaxissizingmode/

---

## 3. layoutGrow vs layoutAlign — Eixos Diferentes

| Propriedade | Eixo que controla | Valores |
|---|---|---|
| `layoutGrow` | **Primary axis** do parent | `0` (fixo) ou `1` (fill) |
| `layoutAlign` | **Counter axis** do parent | `"INHERIT"` ou `"STRETCH"` |

### Para TextNode

- `layoutGrow = 1` em parent HORIZONTAL → texto preenche largura → **precisa `textAutoResize = "HEIGHT"`**
- `layoutAlign = "STRETCH"` em parent VERTICAL → texto preenche largura → **precisa `textAutoResize = "HEIGHT"`**

---

## 4. layoutSizingHorizontal / layoutSizingVertical (Shorthands)

Atalhos que configuram multiplas propriedades de uma vez. Recomendados por serem mais claros.

```typescript
// Equivalentes:
node.layoutSizingHorizontal = "FILL";
// É o mesmo que:
node.layoutGrow = 1;  // (em parent HORIZONTAL)
// Ou:
node.layoutAlign = "STRETCH";  // (em parent VERTICAL)
```

| Valor | Significado | Restricoes |
|---|---|---|
| `"FIXED"` | Tamanho fixo | Funciona em qualquer node |
| `"HUG"` | Abraca conteudo | Apenas auto-layout frames e text nodes |
| `"FILL"` | Preenche parent | Apenas filhos de auto-layout |

**Fonte:** https://developers.figma.com/docs/plugins/api/properties/nodes-layoutsizinghorizontal/

---

## 5. Ordem de Operacoes — CRITICO

A ordem em que voce configura propriedades no Figma Plugin API IMPORTA.

### Ordem Recomendada

```
1. Criar frame (figma.createFrame())
2. Criar filhos e appendar (frame.appendChild)
3. Carregar fontes (figma.loadFontAsync) — ANTES de modificar texto
4. Definir conteudo do texto e textAutoResize
5. Definir layoutMode no parent ("HORIZONTAL" ou "VERTICAL")
6. Definir auto-layout props no parent (sizing modes, padding, itemSpacing)
7. Definir props de layout nos filhos (layoutGrow, layoutAlign)
8. Definir min/max constraints (DEPOIS do layoutMode)
```

### Armadilhas

1. **`layoutMode` eh destrutivo**: Mudar de "VERTICAL" para "NONE" NAO restaura posicoes dos filhos
2. **`resize()` antes de sizing mode**: Setar `primaryAxisSizingMode = "AUTO"` e depois `resize()`
   faz o Figma ignorar o resize (o frame recalcula baseado nos filhos)
3. **`textAutoResize` precisa de fontes carregadas**: Setar antes de `loadFontAsync` lanca erro
4. **min/max ANTES de layoutMode**: Constraints sao ignoradas se setadas antes do auto-layout

---

## 6. Bug do Frame 1px — resize(1, h)

No nosso renderer, havia este codigo:

```typescript
if (w > 0 && h > 0) {
  frame.resize(w, h);
} else if (w > 0) {
  frame.resize(w, 1);      // OK: height temporario
} else if (h > 0) {
  frame.resize(1, h);      // BUG: width = 1px! Texto fica vertical!
}
```

**O terceiro branch cria um frame de 1px de largura**, fazendo qualquer texto
dentro dele renderizar vertical (1 caractere por linha).

**Fix**: Nao setar width=1 arbitrariamente. Se nao ha width, deixar o auto-layout
determinar a largura, ou usar um fallback seguro.

---

## 7. Dependencia Circular: STRETCH + counterAxisSizingMode=AUTO

Quando um parent VERTICAL tem `counterAxisSizingMode = "AUTO"` (width hug)
e TODOS os filhos tem `layoutAlign = "STRETCH"`:

```
FRAME (VERTICAL, counterAxisSizingMode = "AUTO") ← width = max(children widths)
  └── TEXT (layoutAlign = "STRETCH") ← width = parent width
  └── TEXT (layoutAlign = "STRETCH") ← width = parent width
  // CIRCULAR: parent precisa dos filhos pra saber width,
  // filhos precisam do parent pra saber width
```

Figma resolve usando a largura intrinseca dos filhos (ignorando STRETCH para calculo),
mas o resultado pode ser inesperado — especialmente com TEXT nodes.

**Solucao**: Garantir que o parent tem width fixo ou `layoutGrow = 1`
antes de aplicar STRETCH nos filhos.

---

## 8. Padrao Correto: Tabela com Auto-Layout

```
FRAME "table" (VERTICAL, width=100%, border-radius, clipsContent)
  ├── FRAME "header-row" (HORIZONTAL, counterAxisSizingMode=FIXED, height=44)
  │     ├── TEXT "Name"   (layoutGrow=1, textAutoResize="HEIGHT")
  │     ├── TEXT "Status" (layoutGrow=1, textAutoResize="HEIGHT")
  │     └── TEXT "Date"   (layoutGrow=1, textAutoResize="HEIGHT")
  └── FRAME "data-row" (HORIZONTAL, counterAxisSizingMode=FIXED, height=52)
        ├── TEXT "John"   (layoutGrow=1, textAutoResize="HEIGHT")
        ├── TEXT "Active" (layoutGrow=1, textAutoResize="HEIGHT")
        └── TEXT "Jan 1"  (layoutGrow=1, textAutoResize="HEIGHT")
```

**Chave**: Cada TEXT cell tem `layoutGrow=1` (distribui largura igual)
E `textAutoResize="HEIGHT"` (largura controlada pelo parent, altura auto).

---

## 9. Padrao Correto: Sidebar + Content

```
FRAME "root" (HORIZONTAL, width=1440, primaryAxisSizingMode=FIXED)
  ├── FRAME "sidebar" (VERTICAL, width=260, counterAxisSizingMode=FIXED)
  │     └── ...nav items...
  └── FRAME "content" (VERTICAL, layoutGrow=1, counterAxisSizingMode=FIXED)
        └── ...main content...
```

**Chave**: Sidebar tem width fixo. Content tem `layoutGrow=1`.
Root tem `primaryAxisSizingMode=FIXED` para que layoutGrow funcione.

---

## Fontes

- [textAutoResize](https://developers.figma.com/docs/plugins/api/properties/TextNode-textautoresize/)
- [layoutGrow](https://developers.figma.com/docs/plugins/api/properties/nodes-layoutgrow/)
- [layoutAlign](https://developers.figma.com/docs/plugins/api/properties/nodes-layoutalign/)
- [layoutSizingHorizontal](https://developers.figma.com/docs/plugins/api/properties/nodes-layoutsizinghorizontal/)
- [primaryAxisSizingMode](https://developers.figma.com/docs/plugins/api/properties/nodes-primaryaxissizingmode/)
- [counterAxisSizingMode](https://developers.figma.com/docs/plugins/api/properties/nodes-counteraxissizingmode/)
- [layoutMode](https://developers.figma.com/docs/plugins/api/properties/nodes-layoutmode/)
- [Working with Text](https://developers.figma.com/docs/plugins/working-with-text/)
- [Guide to auto layout](https://help.figma.com/hc/en-us/articles/360040451373-Guide-to-auto-layout)
- [Figma Text AutoResize (Grida)](https://grida.co/docs/@designto-code/figma-text-autoresize)
