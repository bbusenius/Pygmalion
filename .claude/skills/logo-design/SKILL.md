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

**If the frontend-design skill is installed**, reference it for comprehensive typography guidance.

For logo typography specifically:

- **Avoid generic fonts**: Never use Arial, Helvetica, Times New Roman, or overused display fonts
- **Match tone to brand**: Geometric sans for tech, serifs for elegance, hand-drawn for artisan
- **Consider custom letterforms**: Modify existing glyphs or create custom characters when it elevates the design
- **Kerning matters**: Adjust letter spacing meticulously - default kerning is rarely optimal
- **Weight and proportion**: Choose weights that work at all sizes; thin strokes may disappear at small sizes

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

## Generating Graphical Elements with AI

**When the gemini_generate_svg tool is available**, it can be used to generate complex graphical elements for logos. This is particularly useful for organic shapes, illustrations, or intricate iconography that would be tedious to code by hand.

### When to Use Gemini SVG Generation

Use `gemini_generate_svg` for:
- **Complex organic shapes**: Natural forms, flowing curves, illustrated elements
- **Intricate iconography**: Detailed symbols that are hard to code geometrically
- **Initial concepts**: Quick exploration of visual directions
- **One-off elements**: When you need a specific graphical component

**The tool generates a single graphical element** - not the complete logo or color variations. You are still responsible for:
- Composing the icon with typography (for combination marks)
- Creating all three color variations (monotone, two-color, three-color) from the base element
- Generating layout variations (horizontal, vertical, abbreviated)
- Building the presentation page
- Testing at all sizes

### When NOT to Use Gemini SVG Generation

Generate SVG code directly (without the tool) for:
- **Wordmarks and lettermarks**: Typography-only logos (the tool isn't needed)
- **Simple geometric icons**: Circles, triangles, squares, basic shapes
- **Precise technical logos**: When mathematical precision is required
- **Maximum control**: When you need exact control over every path and node

### Using the Tool

**CRITICAL: Always request monotone (single color) SVGs from Gemini.** The tool produces ONE graphical element in a single color. You will then manually create the three color variations by modifying the SVG colors.

When using `gemini_generate_svg`:
1. **Request monotone output**: Include "single color", "monotone", or "black only" in your prompt
2. Provide a specific, detailed prompt describing the icon/mark
3. Specify the style (minimal, geometric, organic, detailed, flat)
4. Use an appropriate viewBox size (100-200 for logos)
5. The tool returns a single SVG file with the graphical element in one color
6. You then create three copies with different color schemes (monotone, two-color, three-color)
7. Compose with typography, generate layout variations, and build the presentation

**Example prompt for Gemini:**
```
"A minimalist mountain icon with three peaks, clean geometric shapes,
single color black (#000000), suitable for a coffee company logo"
```

**Example workflow:**
```
User: Design a logo for Mountain Coffee Co.

1. Use gemini_generate_svg with monotone request → get mountain-icon.svg (black)
2. Create three color versions:
   - monotone: black mountain
   - two-color: navy mountain with brown accent
   - three-color: navy mountain, brown accent, cream highlight
3. Code the "Mountain Coffee Co." wordmark
4. Compose each color variation with the wordmark
5. Generate horizontal, vertical, and abbreviated layouts for each
6. Build presentation HTML showing all 9 versions (3 colors × 3 layouts)
```

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

1. **Understand requirements**: Brand name, industry, tone, usage contexts
2. **Choose conceptual direction**: Pick a clear aesthetic approach
3. **Select logo type**: Wordmark, icon, combination, etc.
4. **Create base SVG design**: The core logo in full color
5. **Generate color variations**: Monotone, two-color, three-color versions
6. **Create layout variations**: Horizontal, vertical, abbreviated (when appropriate)
7. **Build presentation page**: HTML showing all versions together
8. **Test at multiple sizes**: Verify legibility from favicon to large format

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
