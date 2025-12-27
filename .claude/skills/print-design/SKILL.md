---
name: print-design
description: Create print-ready designs (posters, flyers, business cards, resumes, brochures) using HTML/WeasyPrint or SVG/Inkscape. Use this skill when the user asks to design materials intended for print or PDF output.
---

This skill guides creation of print-ready designs that render correctly when converted to PDF or PNG. It covers posters, flyers, business cards, resumes, brochures, invitations, certificates, and other print materials.

## Aesthetic Guidelines

**If the frontend-design skill is installed**, invoke it alongside this skill to get comprehensive aesthetic guidance. The frontend-design skill provides essential direction on typography, color, composition, and avoiding generic "AI slop" aesthetics. Use both skills together.

**If the frontend-design skill is not installed**, aim for:
- A clear conceptual direction executed with precision
- Typography that matches the tone (elegant, bold, playful, etc.)
- Color choices that create visual hierarchy
- Designs that feel intentionally crafted, not templated

## Default Behavior: PDF First

When the user doesn't specify an output format, **default to HTML + WeasyPrint for PDF output**. This is the most common expectation for print materials. Only switch to SVG/Inkscape if:
- The design requires effects that WeasyPrint can't render (glows, shadows)
- You've attempted HTML and the PDF output has rendering issues
- The user explicitly requests PNG output

## Critical: Text Must Be Vector, Not Raster

**NEVER bake text into generated images.** All text must be rendered as proper vector text in the final PDF.

**Wrong approach:**
- Asking Gemini/image AI to generate a "complete poster" with text included
- Using a PNG that contains the title/headline text
- Mixing: some text in the image, some text in HTML

**Correct approach:**
1. Generate an image that is **decorative/background only** - no text
2. Create HTML with that image as background
3. Add **all text in HTML** - titles, dates, locations, descriptions
4. Convert to PDF - text will be proper vector/searchable

**Why this matters:**
- Vector text is sharp at any print size
- Text is searchable and selectable in the PDF
- Text can be easily modified without regenerating images
- Proper typographic control (kerning, leading, font choice)

**When generating images for print designs, prompt for:**
- "Background image with [theme] - no text"
- "Decorative [subject] illustration - leave space for text overlay"
- "Abstract [style] pattern for poster background"

## Typography Sizing for Posters

**Headlines must be BIG** - but must also fit on the page.

**Font size depends on text length.** For letter-size (8.5×11") posters:
- Short names (1-2 words like "KISS"): 96-144pt
- Medium names (3-4 words): 60-84pt
- Long names (5+ words like "The Dark Night Cowboys"): 48-60pt

**Other elements:**
- Venue/location: 24-36pt
- Date/time: 20-28pt
- Price/details: 18-24pt
- Fine print/taglines: 12-16pt

**CRITICAL: Always verify text fits within the page bounds.** If text runs off the edge, reduce font size. Never let text overflow.

## Image Composition for Text Overlay

**Never place text over the subject's face or focal point.**

### If Grok Vision is Available (Recommended)

Before laying out text, use `mcp__grok__analyze_image` to analyze the background image with this specific prompt:

"Analyze this image for text overlay placement. Answer precisely:
1. What percentage from the TOP of the image does the subject's head/face START? (e.g., '15%' means head starts 15% down from top)
2. What percentage from the TOP does the subject's head/face END? (e.g., '45%' means head ends 45% down from top)
3. What percentage from the BOTTOM is clearly empty/dark/suitable for text? (e.g., '25%' means bottom 25% is clear)
4. Are there any clear zones on the LEFT or RIGHT sides suitable for text?"

Use these percentages to calculate exact CSS positioning. For example, if head starts at 10% and ends at 50%, only place text below 55% (with 5% buffer).

**CRITICAL: The vision analysis must drive your layout decisions.**

Do not follow default poster conventions (band name at top, details at bottom). Instead, design the layout AROUND the subject based on what Grok tells you. If Grok says the face occupies the upper portion, you cannot put ANY text there - not even the band name. Find a creative solution that keeps text in the clear areas only.

Common mistake: Acknowledging "face is in upper area" then putting the band name at top anyway because "that's where band names go." This is wrong. The image composition dictates the layout, not convention.

### When Generating New Background Images

Request composition with the subject positioned to leave text zones:
- "...subject positioned in lower half, empty sky/background in upper portion for text"
- "...character on the right side, negative space on left for text overlay"
- "...figure in bottom third, dramatic sky/atmosphere in upper two-thirds"

### When Using Existing Images Without Vision Analysis

If you cannot analyze the image, use conservative assumptions:
- **Assume the face is in the center-upper area** (most common portrait composition)
- Place headline text at the very top edge (above where heads typically are)
- Place details at the very bottom edge (below where bodies typically are)
- Use semi-transparent dark overlays to ensure text readability regardless of what's behind it

**Text placement zones (for portrait-orientation posters):**
- **Top edge (0-15%)**: Safest for headlines - usually above the subject's head
- **Middle (15-70%)**: DANGER ZONE - assume face/body is here
- **Bottom edge (70-100%)**: Safe for details - usually below the subject

**If the subject fills the frame**, use a semi-transparent gradient overlay (dark at top and bottom, transparent in middle) to create text contrast zones.

## Choose Your Approach

You have two primary approaches for print design. Choose based on the requirements:

### Approach 1: HTML + WeasyPrint (for PDF output)

**Best for**: Text-heavy designs, documents, simple layouts, when PDF is required.

**WeasyPrint CSS Limitations** - these properties are IGNORED:
- `box-shadow` - will not render
- `text-shadow` - will not render
- `filter` (blur, contrast, brightness) - will not render
- `@keyframes` / CSS animations - will not render
- `backdrop-filter` - will not render
- `background-clip: text` - **DANGER: causes gray boxes behind text** (see below)

**CRITICAL: Avoid `background-clip: text` for gradient text effects.**
This CSS technique clips a gradient/image background to the text shape. When WeasyPrint ignores it, the gradient renders as a full rectangle BEHIND the text instead of being clipped to it - creating an ugly colored box. Use solid colors for text in PDF output, or switch to SVG if gradient text is essential.

**What DOES work in WeasyPrint**:
- `linear-gradient`, `radial-gradient` for backgrounds
- `border`, `border-radius`
- `opacity`
- `transform` (rotate, scale) - static only
- Google Fonts via `@import` (with internet connection)
- Flexbox and Grid layouts
- `@page` rules for print control

### Approach 2: SVG + Inkscape (for PNG output)

**Best for**: Designs requiring glows, shadows, complex effects, or when PNG output is acceptable.

**SVG advantages**:
- `<filter>` elements for glow, shadow, blur effects actually render
- More predictable output across all renderers
- Can embed raster images with `<image xlink:href="...">`
- Export to PNG at any resolution via Inkscape

**SVG filter example for glow effects**:
```xml
<filter id="glow">
  <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
  <feMerge>
    <feMergeNode in="coloredBlur"/>
    <feMergeNode in="SourceGraphic"/>
  </feMerge>
</filter>
<text filter="url(#glow)" ...>Text with glow</text>
```

## Full Bleed and Margins (MANDATORY for HTML/WeasyPrint)

**This is the #1 source of errors. Follow this exactly:**

### Required CSS - Copy This Template:
```css
@page {
  margin: 0;  /* CRITICAL: removes print margins */
  size: 8.5in 11in;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  width: 8.5in;
  height: 11in;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

.poster {
  width: 100%;
  height: 100%;
  padding: 0.5in; /* safe area for text - adjust as needed */
  position: relative;
}

.background-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: -1;
}
```

### Full Bleed Checklist - Verify Before Converting:
- [ ] `@page { margin: 0; }` is present
- [ ] Body has explicit `width` and `height` in inches
- [ ] Body has `margin: 0` and `padding: 0`
- [ ] Body has `overflow: hidden`
- [ ] Background image uses `position: absolute` with `top/left: 0`
- [ ] Text content has internal padding (not body padding)

**Do NOT use:**
- `height: 100vh` - WeasyPrint ignores this
- `margin: auto` for centering - use flexbox or explicit positioning
- Percentage-based dimensions without a fixed parent

## Common Print Dimensions

| Format | Size (inches) | Size (pixels @ 300dpi) |
|--------|---------------|------------------------|
| Letter | 8.5 × 11 | 2550 × 3300 |
| Tabloid/Ledger | 11 × 17 | 3300 × 5100 |
| Poster (small) | 18 × 24 | 5400 × 7200 |
| Business Card | 3.5 × 2 | 1050 × 600 |
| A4 | 8.27 × 11.69 | 2480 × 3508 |
| A3 | 11.69 × 16.54 | 3508 × 4961 |

## Pre-Conversion Checklist

Before converting HTML to PDF or SVG to PNG, verify:

1. **All text is in HTML/SVG**: No text baked into PNG images
2. **Generated image is referenced**: The image you created is actually used in the HTML (check the filename matches exactly)
3. **Full bleed CSS is correct**: Review the Full Bleed Checklist above
4. **Text fits on page**: All text is within bounds - no overflow or clipping
5. **Images positioned correctly**: Background uses `position: absolute; top: 0; left: 0`
6. **No forbidden CSS**: No `100vh`, `text-shadow`, `box-shadow`, `filter`, `background-clip: text`
7. **Test BOTH outputs**: Open HTML in browser AND generate PDF - they can differ significantly

**After generating the PDF:**
- DO NOT use the Read tool on PDF files - they're binary and will crash the session if large
- The PDF will auto-open for the user to verify
- You cannot verify PDF output yourself - trust that your HTML layout will render correctly
- If the user reports issues, fix the HTML and regenerate

## Image Handling

**For HTML/WeasyPrint**:
```css
.image-container {
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.image-container img {
  width: 100%;
  height: auto;
  object-fit: contain;
}
```

**For SVG**:
```xml
<image x="76" y="175" width="460" height="420"
       xlink:href="image.png"
       preserveAspectRatio="xMidYMid meet"/>
```

## When to Switch Approaches

**Start with HTML/WeasyPrint** if:
- User specifically requests PDF output
- Design is primarily text and simple shapes
- No glow/shadow effects needed

**Switch to SVG/Inkscape** if:
- WeasyPrint output looks wrong (missing effects)
- Design requires glows, shadows, or complex filters
- PNG output is acceptable
- You've iterated twice on HTML and still have rendering issues

## Workflow Summary

### For HTML/WeasyPrint (PDF output):

1. **Understand requirements**: Dimensions, theme, text content needed
2. **Generate decorative image**: Use AI image generation for background ONLY - no text in image
3. **Create HTML from template**: Start with the Full Bleed CSS template above
4. **Add background image**: Use `position: absolute` positioning
5. **Add ALL text in HTML**: Titles, dates, locations, descriptions - everything
6. **Apply aesthetic principles**: Bold typography, cohesive colors, proper hierarchy
7. **Run Full Bleed Checklist**: Verify all CSS requirements before converting
8. **Convert to PDF**: Use WeasyPrint
9. **Visually verify PDF**: Check for cutoff text, white edges, image coverage
10. **Iterate if needed**: Fix issues and regenerate

### For SVG/Inkscape (PNG output):

1. **Understand requirements**: Dimensions, theme, effects needed
2. **Generate decorative image**: Background/elements only - no text
3. **Create SVG**: With proper viewBox dimensions
4. **Add background**: Embed image or create SVG patterns
5. **Add ALL text in SVG**: Using `<text>` elements with filters for effects
6. **Export to PNG**: Via Inkscape at target resolution

**Never one-shot a complete design with AI image generation** - always build the design with proper vector text.
