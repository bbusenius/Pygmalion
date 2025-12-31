---
name: logo-design
description: Create distinctive, professional logos with proper color variations. Use this skill when the user asks to design logos, brand marks, wordmarks, or visual identity elements.
---

This skill guides creation of distinctive, professional logos that avoid generic aesthetics. All logos are created as pure SVG code - no AI image generation. Every logo delivery includes mandatory color variations and a presentation page for client review.

The user provides logo requirements: brand name, purpose, industry, tone, or other context about what they need.

## Design Thinking

Before creating, understand the context and commit to a clear direction:

- **Purpose**: What does this brand represent? What problem does it solve?
- **Tone**: Pick a direction: bold/powerful, refined/elegant, playful/friendly, tech/modern, organic/natural, minimalist/clean, vintage/classic, geometric/precise, hand-crafted/artisan, etc.
- **Constraints**: Where will it be used? (web, print, signage, favicon, embroidery)
- **Differentiation**: What makes this memorable? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. The logo must feel intentionally designed for this specific brand, not like a generic template.

## Logo Types

Support all logo types based on what best serves the brand:

- **Wordmark**: Brand name styled typographically (Google, Coca-Cola)
- **Lettermark**: Initials only (IBM, HBO, NASA)
- **Iconographic**: Symbol/icon only (Apple, Nike, Target)
- **Combination Mark**: Icon + wordmark together (Adidas, Burger King)
- **Emblem**: Text inside a symbol/badge (Starbucks, Harley-Davidson)

Choose the type that best fits the brand's needs, usage contexts, and name characteristics.

## Typography Guidelines

**BEFORE SELECTING FONTS: Check if the frontend-design skill exists using the Skill tool with skill="frontend-design"**
- If it exists: **MANDATORY** - invoke it to get expert typography guidance
- If it doesn't exist: proceed with the guidelines below

### Forbidden Fonts

**ABSOLUTELY NEVER use these fonts in logos - they are generic, overused, and unprofessional:**
- Arial, Arial Black, Arial Narrow
- Impact
- Helvetica, Helvetica Neue
- Times New Roman, Times
- Verdana, Tahoma
- Georgia
- Comic Sans (obviously)
- Default sans-serif, serif, or monospace

**Using any of these fonts is a critical failure.** Logos with these fonts look amateurish and forgettable.

### Font Discovery

Before selecting fonts, check what's available on the system:
```bash
fc-list : family | sort -u
```

Pick distinctive fonts from the results. Common good options on Linux:
- **Bold/display**: Oswald, Bebas Neue, Liberation Sans Bold, Noto Sans Black
- **Elegant**: Liberation Serif, Noto Serif, DejaVu Serif
- **Clean**: Ubuntu, Cantarell, Liberation Sans

### Font Selection

For logo typography specifically:

- **Font must be distinctive and intentional**: Choose typefaces that match brand personality
- **Use only fonts installed on the system**: Run `fc-list` to check availability
- **Match tone to brand**:
  - Bold/adventurous: Condensed sans with strong character
  - Elegant/refined: Serifs with finesse
  - Tech/modern: Geometric sans
  - Hand-crafted: Display fonts with personality
- **Consider custom letterforms**: Modify existing glyphs or create custom characters
- **Kerning matters**: Adjust letter spacing meticulously
- **Weight and proportion**: Choose weights that work at all sizes

**For wordmarks and lettermarks**, typography IS the logo. Every curve, terminal, and proportion must be intentional.

## Color Requirements

**Maximum 3 colors** in any logo design. Logos must work with fewer colors, not more.

### Mandatory 3 Versions Per Design

Every logo must be delivered in three color versions:

1. **Monotone**: Single color (works for embroidery, stamps, low-budget printing)
2. **Two-color**: Primary + one accent (versatile for most applications)
3. **Three-color**: Full color palette (maximum expression, hero usage)

All three versions must use the SAME design - only colors change. The monotone version proves the logo works without relying on color for meaning.

### Color Selection

- Choose colors that reinforce brand meaning (blue for trust, green for growth, etc.)
- Ensure sufficient contrast between colors
- Test that colors work on both light and dark backgrounds
- Consider print reproduction - some colors don't translate well to CMYK

## Layout Variations

When appropriate, provide multiple layout versions:

- **Horizontal**: Primary layout, icon left of text (or text only)
- **Vertical/Stacked**: Icon above text, for square spaces
- **Abbreviated**: Icon or initials only, for small spaces (favicons, app icons)

Not every logo needs all variations. Provide them when:
- The logo has both icon and text components
- The client will use it across different format requirements
- The abbreviated version is meaningfully different from the full logo

## Technical Requirements

### SVG Format

All logos must be created as clean SVG code:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 [width] [height]">
  <!-- Logo content -->
</svg>
```

### SVG Best Practices

- Use `viewBox` for scalability, not fixed width/height
- Group related elements with `<g>` tags
- Use meaningful IDs for color variations: `id="primary-color"`, `id="accent-color"`
- Convert text to paths for final delivery (ensures fonts render everywhere)
- Keep paths clean - minimize nodes, smooth curves
- Remove unnecessary attributes and whitespace

### Size Testing

Every logo must work at:
- **Favicon size**: 16x16px (recognizable silhouette)
- **Social icon**: 48x48px (clear detail)
- **Header size**: 200px wide (full detail visible)
- **Large format**: 1000px+ (no quality loss, clean edges)

**CRITICAL: Maintain Aspect Ratio**

Logos and icons must NEVER be distorted when resized. All resizing must maintain the original proportions:
- Never squash or stretch a logo to fit a space
- Scale proportionally only - if you reduce width by 50%, reduce height by 50%
- Use CSS/SVG `preserveAspectRatio` when embedding
- If a space requires different proportions, create a purpose-built layout variation instead of distorting the existing logo

## Generating Graphical Elements

**Two approaches for generating graphical elements:**

1. **AI-generated SVG** (`gemini_generate_svg`): Direct SVG code generation
2. **Bitmap tracing** (`trace_bitmap`): Convert raster images to SVG vectors

Choose based on the design requirements and available resources.

### Approach 1: AI-Generated SVG (Gemini)

**When the gemini_generate_svg tool is available**, it can generate SVG code directly from text descriptions.

**Use `gemini_generate_svg` for:**
- **Complex organic shapes**: Natural forms, flowing curves, illustrated elements
- **Intricate iconography**: Detailed symbols that are hard to code geometrically
- **Initial concepts**: Quick exploration of visual directions
- **One-off elements**: When you need a specific graphical component

**CRITICAL: Always request monotone (single color) SVGs from Gemini.** The tool produces ONE graphical element in a single color. You then manually create the three color variations.

**Example Gemini prompt:**
```
"A minimalist mountain icon with three peaks, clean geometric shapes,
single color black (#000000), suitable for a coffee company logo"
```

### Approach 2: Bitmap Tracing (Potrace)

**When the trace_bitmap tool is available**, it can convert raster images (PNG, JPG, BMP) to clean SVG vectors. This mirrors the traditional designer workflow of tracing bitmap references.

**Use `trace_bitmap` for:**
- **User-provided images**: When the user says "I have an image I want traced"
- **AI-generated bitmaps**: Generate image with Gemini, then trace to SVG
- **Hand-drawn sketches**: Scan or photograph sketches, then trace
- **Existing bitmap logos**: Convert legacy raster logos to scalable vectors
- **Complex illustrations**: When bitmap generation produces better results than direct SVG

**Workflow for bitmap tracing:**
1. **Option A - User provides image**: User says "trace this image for my logo"
2. **Option B - Generate then trace**: Use `gemini_generate_image` to create bitmap → `trace_bitmap` to vectorize
3. Adjust tracing parameters:
   - `turdsize`: Suppress speckles (default: 2, higher = cleaner)
   - `turnpolicy`: Path extraction (default: minority)
   - `alphamax`: Corner sharpness (default: 1.0, lower = sharper)
   - `opttolerance`: Curve smoothness (default: 0.2, higher = smoother)
4. Result is a single-color SVG
5. Manually create three color variations
6. Compose with typography and build presentation

**Example bitmap→trace workflow:**
```
User: Design a logo for Mountain Coffee Co. using this mountain photo I have.

1. Use trace_bitmap on user's mountain.jpg → get mountain-traced.svg (black paths)
2. Clean/simplify the traced SVG if needed
3. Create three color versions:
   - monotone: black mountain
   - two-color: navy mountain with brown accent
   - three-color: navy mountain, brown accent, cream highlight
4. Code the "Mountain Coffee Co." wordmark
5. Compose each color variation with the wordmark
6. Generate horizontal, vertical, and abbreviated layouts
7. Build presentation HTML showing all variations
```

**Example generate→trace workflow:**
```
User: Create a logo with an organic leaf illustration.

1. Use gemini_generate_image: "detailed organic leaf illustration, single leaf,
   black and white, high contrast, clean edges, 1024x1024px"
2. Use trace_bitmap on the generated image → get leaf-traced.svg
3. Refine the traced paths if needed
4. Create three color versions (monotone, two-color, three-color)
5. Compose with brand typography
6. Build complete presentation
```

**CRITICAL: Integrating Potrace Output**

After tracing with `trace_bitmap` (which includes automatic viewBox optimization), you'll have an SVG like this:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg viewBox="0 0 1291.5 724" width="1291.5pt" height="724pt" ...>
  <g transform="matrix(0.1,0,0,-0.1,-378.97,1370)" fill="#000000">
    <path d="m 10830,13684 c -158,-41..."/>
  </g>
</svg>
```

The traced SVG has viewBox dimensions (e.g., 1291.5 x 724) and a matrix transform on the `<g>` element.

**To compose this into a logo using `<g>` elements (allows Inkscape optimization):**

```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <!-- Traced icon wrapped in positioning transform -->
  <!-- Calculate scale: desired_size / viewBox_dimension -->
  <!-- Example: want 120px wide, viewBox is 1291.5, scale = 120/1291.5 = 0.0929 -->
  <g transform="translate(20, 40) scale(0.0929)">
    <!-- Copy the <g> and <path> EXACTLY from traced SVG -->
    <g transform="matrix(0.1,0,0,-0.1,-378.97,1370)" fill="#1a1a1a">
      <path d="m 10830,13684 c -158,-41..."/>
    </g>
  </g>

  <!-- Typography -->
  <text x="160" y="80" font-size="32">VOLCANO</text>
  <text x="160" y="115" font-size="16">ADVENTURES</text>
</svg>
```

**Key calculation steps:**
1. **Determine desired icon size** (e.g., 120px wide)
2. **Get traced viewBox width** from traced SVG (e.g., 1291.5)
3. **Calculate scale** = desired_size / viewBox_width (e.g., 120 / 1291.5 = 0.0929)
4. **Apply transform** = `translate(x_pos, y_pos) scale(calculated_scale)`
5. **Copy the inner `<g transform="matrix(...)">` and `<path>` exactly** - don't modify them

**After creating the logo, optimize viewBox with Inkscape:**
```bash
inkscape logo.svg --export-area-drawing --export-plain-svg --export-filename=logo.svg
```

This approach:
- ✅ Uses `<g>` elements throughout (no nested `<svg>`)
- ✅ Preserves Potrace matrix transform exactly
- ✅ Allows Inkscape to calculate tight bounding box correctly
- ✅ Removes lopsided whitespace automatically

**NEVER do these:**
- ❌ Don't copy just the `<path>` element - you lose the coordinate system
- ❌ Don't modify the inner matrix transform values - use them exactly as traced
- ❌ Don't use nested `<svg>` - it breaks Inkscape's bounding box detection

### When to Code SVG Directly

Generate SVG code directly (without AI tools) for:
- **Wordmarks and lettermarks**: Typography-only logos
- **Simple geometric icons**: Circles, triangles, squares, basic shapes
- **Precise technical logos**: When mathematical precision is required
- **Maximum control**: When you need exact control over every path and node

### Tool Responsibilities

**Both approaches produce a single graphical element** - not the complete logo or variations. You are always responsible for:
- Composing the icon with typography (for combination marks)
- Creating all three color variations (monotone, two-color, three-color) from the base element
- Generating layout variations (horizontal, vertical, abbreviated)
- Building the presentation page
- Testing at all sizes

## Anti-patterns

**NEVER create logos that:**

- Are too complex or detailed (won't work small)
- Rely on color for meaning (monotone must work)
- Use generic fonts (Arial, Helvetica, system fonts)
- Follow fleeting trends (will look dated quickly)
- Look like generic "AI slop" (gradient blobs, generic tech swooshes)
- Have poor kerning or typography
- Include too many colors (max 3)
- Can't be reproduced in single color

**AVOID common AI logo aesthetics:**
- Generic gradient orbs
- Swooshy abstract shapes with no meaning
- Overused tech/startup visual language
- Clip-art quality illustrations
- Overly complex geometric patterns

## Workflow

**Phase 1: Setup and Typography**
1. **Understand requirements**: Brand name, industry, tone, usage contexts
2. **Check for frontend-design skill**: Use Skill tool to see if it exists
3. **If frontend-design exists**: INVOKE IT for typography guidance (MANDATORY)
4. **Choose conceptual direction**: Pick a clear aesthetic approach based on typography guidance
5. **Select logo type**: Wordmark, icon, combination, etc.

**Phase 2: Create Editable Versions**
6. **Create base SVG design**: WITHOUT viewBox, using distinctive fonts (NO forbidden fonts)
7. **Generate all variations**: Monotone, two-color, three-color, horizontal, vertical, icon-only
8. **Save all as editable**: All files saved with `_editable.svg` suffix, text as text

**Phase 3: Convert to Delivery Versions**
9. **For EACH editable file**:
   - Run Inkscape to convert text to outlines
   - Run Inkscape to optimize viewBox
   - Save as final delivery version (without `_editable` suffix)

**Phase 4: Presentation**
10. **Build presentation page**: HTML showing final delivery versions
11. **Test at multiple sizes**: Verify legibility from favicon to large format

**CRITICAL: You must create BOTH versions:**
- **Editable versions** (`*_editable.svg`): Text as text, for future modifications
- **Delivery versions** (`*.svg`): Text converted to outlines, perfect rendering everywhere

**If you skip the text-to-outlines conversion, logos will have rendering issues in browsers.**

## Converting Text to Outlines

**CRITICAL**: Convert all text to paths before delivery to ensure consistent rendering across browsers and platforms.

### Workflow for Each Logo Variant

**Step 1: Create editable version with text**
```bash
# Write the SVG with text elements (no viewBox)
# Save as: logo_monotone_horizontal_editable.svg
```

**Step 2: Convert text to outlines**
```bash
inkscape logo_monotone_horizontal_editable.svg \
  --actions="select-all:text;object-to-path" \
  --export-plain-svg \
  --export-filename=logo_monotone_horizontal_temp.svg
```

**Step 3: Optimize viewBox**
```bash
inkscape logo_monotone_horizontal_temp.svg \
  --export-area-drawing \
  --export-plain-svg \
  --export-filename=logo_monotone_horizontal.svg
```

### Why Convert to Outlines?

- **Consistent rendering**: Browsers render text differently; paths render identically everywhere
- **No font dependencies**: Logo works without requiring fonts to be installed
- **Prevents clipping issues**: Eliminates browser text rendering quirks
- **Professional standard**: Industry best practice for logo delivery

### What to Deliver

**For presentation and use:**
- Logos with text converted to outlines
- Optimized viewBox
- Clean, browser-safe rendering

**For client's future edits:**
- Editable versions with text as text (`*_editable.svg`)
- Document which fonts were used

## ViewBox Optimization

**CRITICAL:** When creating composed logos with traced bitmaps, use `<g>` elements (NOT nested `<svg>`) so Inkscape can calculate bounds correctly.

After converting text to outlines, optimize the viewBox using Inkscape:

```bash
inkscape input.svg --export-area-drawing --export-plain-svg --export-filename=output.svg
```

This command:
- Calculates the tight bounding box around ALL content (icon + paths)
- Adds the correct viewBox attribute
- Removes excess whitespace
- Ensures consistent sizing

**Apply this to EVERY logo file** (monotone, two-color, three-color, horizontal, vertical, abbreviated) AFTER converting text to outlines.

## Presentation Format

Deliver logos in an HTML presentation page that shows:

### Color Variations Section
Display all three color versions side-by-side:
- Monotone | Two-color | Three-color
- Show on both light and dark backgrounds

### Layout Variations Section (when applicable)
Display horizontal, vertical, and abbreviated versions together

### Size Preview Section
Show the logo at multiple sizes:
- Favicon (16px)
- Small (48px)
- Medium (200px)
- Large (400px+)

### Example Presentation Structure

```html
<!DOCTYPE html>
<html>
<head>
  <title>[Brand] Logo Presentation</title>
  <style>
    /* Grid layout for variations */
    /* Light and dark background sections */
    /* Size comparison displays */
  </style>
</head>
<body>
  <h1>[Brand] Logo</h1>

  <section class="color-variations">
    <h2>Color Versions</h2>
    <!-- Monotone, Two-color, Three-color side by side -->
  </section>

  <section class="layout-variations">
    <h2>Layout Options</h2>
    <!-- Horizontal, Vertical, Abbreviated -->
  </section>

  <section class="size-tests">
    <h2>Size Testing</h2>
    <!-- Multiple sizes from small to large -->
  </section>

  <section class="background-tests">
    <h2>Background Compatibility</h2>
    <!-- Logo on light and dark backgrounds -->
  </section>
</body>
</html>
```

## Integration with Other Skills

**If the frontend-design skill is installed**, invoke it alongside this skill for comprehensive aesthetic guidance. The frontend-design skill provides direction on:
- Typography choices and pairings
- Color theory and palette creation
- Avoiding generic "AI slop" aesthetics
- Bold, intentional design decisions

Use both skills together for maximum design quality.
