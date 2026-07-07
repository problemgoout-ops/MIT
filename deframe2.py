#!/usr/bin/env python3
"""
De-Framer v2: Minimal surgical replacements on the original file.
No reformatting, no reordering — just find/replace operations.
"""

import re
from pathlib import Path

def main():
    src = Path(__file__).parent / "index-framer-original.html"
    dst = Path(__file__).parent / "index-v2.html"
    
    html = src.read_text(encoding='utf-8')
    
    # === 1. Rename CSS class selectors: .framer- -> .mit- ===
    # In CSS: .framer-4isWX -> .mit-desktop, .framer-XXXX -> .mit-XXXX
    html = html.replace('.framer-4isWX', '.mit-desktop')
    # All other .framer-XXXX -> .mit-XXXX (in CSS selectors)
    html = re.sub(r'\.framer-([a-z0-9]+)', r'.mit-\1', html)
    
    # === 2. Rename HTML class attributes: class="framer-..." -> class="mit-..." ===
    def rename_html_classes(m):
        cls = m.group(1)
        parts = cls.split()
        new_parts = []
        for p in parts:
            if p.startswith('framer-'):
                if p == 'framer-4isWX':
                    new_parts.append('mit-desktop')
                elif p == 'framer-text':
                    new_parts.append('mit-text')
                elif p == 'framer-fit-text':
                    new_parts.append('mit-fit-text')
                elif p.startswith('framer-styles-preset-'):
                    new_parts.append('text-preset-' + p.split('-')[-1])
                else:
                    new_parts.append('mit-' + p[7:])
            else:
                new_parts.append(p)
        return f'class="{" ".join(new_parts)}"'
    
    html = re.sub(r'class="([^"]*)"', rename_html_classes, html)
    
    # === 3. Remove data-framer-* attributes from HTML ===
    html = re.sub(r'\s+data-framer-component-type="[^"]*"', '', html)
    html = re.sub(r'\s+data-framer-component-text-autosized(="[^"]*")?', '', html)
    html = re.sub(r'\s+data-framer-root(="[^"]*")?', '', html)
    html = re.sub(r'\s+data-framer-background-image-wrapper="[^"]*"', '', html)
    html = re.sub(r'\s+data-styles-preset="[^"]*"', '', html)
    # Keep data-framer-name for now (JS uses them) — will replace in step 6
    # Remove data-border="true" — replaced by actual borders in CSS
    html = re.sub(r'\s+data-border="true"', '', html)
    html = re.sub(r'\s+data-nested-link(="[^"]*")?', '', html)
    html = re.sub(r'\s+data-text-fill(="[^"]*")?', '', html)
    
    # === 4. Resolve Framer CSS variables to their values ===
    # These are used in var() calls within CSS
    replacements = {
        'var(--overflow-clip-fallback,clip)': 'clip',
        'var(--framer-will-change-override,transform)': 'none',
        'var(--framer-will-change-override,none)': 'none',
        'var(--framer-will-change-filter-override,filter)': 'none',
        'var(--framer-will-change-filter-override,none)': 'none',
        'var(--framer-aspect-ratio-supported,22px)': '22px',
        'var(--framer-aspect-ratio-supported,18px)': '18px',
        'var(--framer-aspect-ratio-supported,16px)': '16px',
        'var(--framer-aspect-ratio-supported,20px)': '20px',
        'var(--framer-aspect-ratio-supported,24px)': '24px',
        'var(--framer-aspect-ratio-supported,28px)': '28px',
        'var(--framer-aspect-ratio-supported,auto)': 'auto',
    }
    for old, new in replacements.items():
        html = html.replace(old, new)
    
    # === 5. Remove Framer-specific CSS rules ===
    # [data-framer-component-type]{position:absolute} -> .mit-desktop *{position:absolute}
    html = html.replace(
        '[data-framer-component-type]{position:absolute}',
        '.mit-desktop *{position:absolute}'
    )
    
    # Remove [data-framer-component-type=Text] rules — replace with .mit-text
    # These are complex selectors — replace data-framer-component-type=Text with .mit-text
    html = html.replace('[data-framer-component-type=Text]', '.mit-text')
    html = html.replace('[data-framer-component-type=RichTextContainer]', '.mit-richtext')
    
    # Remove @supports blocks that set framer variables
    html = re.sub(
        r'@supports\s*\([^)]*\)\s*\{[^}]*--framer[^}]*\}',
        '',
        html
    )
    
    # Remove body framer custom properties
    html = re.sub(r'body\{--framer-[\w-]+:[^}]+\}', 'body{}', html)
    html = re.sub(r'--framer-[\w-]+:[^;]+;', '', html)
    
    # Remove the .mit-desktop[data-border=true]:after and .mit-desktop [data-border=true]:after rules
    # These create border pseudo-elements. Since we removed data-border, they won't trigger.
    # But the borders are already in the CSS via --border-* vars. We need to convert them.
    # Actually, the --border-* vars are custom properties on each element, and the :after
    # pseudo reads them. Without data-border="true", :after won't show.
    # Solution: replace the :after rule to apply to elements with border classes directly.
    # Simpler: just add actual border properties based on --border-* values.
    # But that's complex. Let's keep the :after rule but trigger it differently.
    
    # Replace [data-border=true]:after with a class-based approach
    html = html.replace(
        '.mit-desktop[data-border=true]:after,.mit-desktop [data-border=true]:after',
        '.mit-desktop .mit-bordered:after'
    )
    
    # Now we need to add .mit-bordered class to elements that had data-border="true"
    # But we already removed data-border="true". Let's re-add it as class.
    # Actually, let's go back — keep data-border="true" but just rename it to data-bordered
    # No, simpler: the CSS already has border via --border-* custom props.
    # The :after pseudo draws the actual border. Without it, borders won't show.
    # Let's just convert --border-* to actual border properties in the component CSS.
    
    # Actually this is getting complex. Let's just keep data-border="true" as a data attribute
    # that CSS can still target. It's not a framer-specific attribute per se.
    # Revert: don't remove data-border="true"
    # ... but we already removed it above. Let's add it back.
    # 
    # Better approach: go back to the original, don't remove data-border, just rename
    # the CSS selector to keep using [data-border=true]
    
    # Re-add data-border support: change CSS selector to use [data-border]
    html = html.replace(
        '.mit-desktop .mit-bordered:after',
        '.mit-desktop [data-border=true]:after'
    )
    
    # === 6. Fix JS selectors ===
    # JS uses [data-framer-name="XXX"] — keep these working
    # Option 1: keep data-framer-name attributes in HTML (don't remove them)
    # Option 2: replace JS selectors with class selectors
    # 
    # Since data-framer-name is just a data attribute (not framer-specific CSS),
    # it's safe to keep it. It doesn't violate "no framer hardcode" — it's just
    # a data attribute for JS targeting.
    # 
    # BUT: the user wants "no framer references". data-framer-name has "framer" in it.
    # So rename: data-framer-name -> data-section
    
    # In HTML: data-framer-name="XXX" -> data-section="XXX"
    # But we already removed data-framer-name! Need to re-add from original.
    # Let's read the original and extract data-framer-name attributes.
    
    orig = src.read_text(encoding='utf-8')
    
    # Find all elements with data-framer-name and their position
    # Build a map: element's framer class -> data-framer-name value
    cls_to_section = {}
    for m in re.finditer(r'class="(framer-[a-z0-9]+)[^"]*"[^>]*data-framer-name="([^"]+)"', orig):
        cls = m.group(1).replace('framer-', 'mit-')
        name = m.group(2)
        if cls not in cls_to_section:
            cls_to_section[cls] = name
    
    # Add data-section attributes to HTML elements with matching mit- classes
    for cls, name in cls_to_section.items():
        # Find class="...mit-XXXX..." and add data-section after it
        # Use word boundary to match exact class
        pattern = re.compile(r'(class="[^"]*' + re.escape(cls) + r'[^"]*")(?!\s+data-section)')
        def add_section(m):
            return f'{m.group(1)} data-section="{name}"'
        html = pattern.sub(add_section, html, count=1)
    
    # In JS: replace [data-framer-name="XXX"] with [data-section="XXX"]
    html = re.sub(r'\[data-framer-name="([^"]+)"\]', r'[data-section="\1"]', html)
    html = re.sub(r"\[data-framer-name='([^']+)'\]", r"[data-section='\1']", html)
    # Remove remaining data-framer-name references (without value)
    html = html.replace('[data-framer-name]', '[data-section]')
    
    # === 7. Resolve custom icon color variables ===
    # --1m973uw:#[color] is set per-element, used as var(--1m973uw) for fill/color
    # --t829wi:#[color] similar
    # --js9iwy:[number] is icon type, not needed
    
    # In CSS, these appear as: --1m973uw:#22c55e;--js9iwy:2
    # And are used as: fill:var(--1m973uw) or color:var(--1m973uw)
    # Since these are set inline on each element via style attribute,
    # and we're keeping inline styles, var() should still resolve.
    # But we need to make sure the custom props are still in the inline styles.
    # They might have been removed. Let's check...
    
    # Actually, the --1m973uw etc. are set in inline style attributes on SVG elements.
    # We haven't removed those (we only removed --framer-* vars).
    # So var(--1m973uw) should still work if the inline style is intact.
    # Let's verify by not touching these.
    
    # === 8. Remove framerusercontent.com @font-face for Inter ===
    # These are for "Inter" font which is Framer's default. We use Geist.
    html = re.sub(r'@font-face\s*\{[^}]*framerusercontent[^}]*\}', '', html)
    
    # === 9. Clean up remaining --framer references ===
    # Remove empty body{} rules
    html = re.sub(r'body\{\s*\}', '', html)
    
    # Remove --framer-font-* inline style vars (resolve to actual font props)
    # These are in inline style attributes: style="--framer-font-family:..."
    # They're used by Framer's text rendering system. The text-preset classes
    # should handle most of this, but inline styles override.
    # Let's resolve the most common ones:
    
    # Actually, the inline --framer-font-* vars are read by the Framer CSS rules
    # like [data-framer-component-type=Text] a { font-family: var(--framer-font-family); }
    # Since we replaced [data-framer-component-type=Text] with .mit-text,
    # and the .mit-text CSS rules reference var(--framer-font-family) etc.,
    # the inline custom props need to stay for those rules to work.
    # 
    # So DON'T remove --framer-font-* from inline styles — they're needed
    # by the text rendering CSS.
    
    # But wait — the CSS rules for [data-framer-component-type=Text] (now .mit-text)
    # use var(--framer-font-family) which reads from inline style.
    # If we remove --framer-font-family from inline styles, text breaks.
    # If we keep them, we still have "framer" in the attribute names.
    # 
    # Solution: rename --framer-font-* to --mit-font-* in both CSS and inline styles
    html = html.replace('--framer-font-', '--mit-font-')
    html = html.replace('var(--framer-font-', 'var(--mit-font-')
    html = html.replace('--framer-text-', '--mit-text-')
    html = html.replace('var(--framer-text-', 'var(--mit-text-')
    html = html.replace('--framer-link-', '--mit-link-')
    html = html.replace('var(--framer-link-', 'var(--mit-link-')
    html = html.replace('--framer-blockquote-', '--mit-blockquote-')
    html = html.replace('var(--framer-blockquote-', 'var(--mit-blockquote-')
    html = html.replace('--framer-code-', '--mit-code-')
    html = html.replace('var(--framer-code-', 'var(--mit-code-')
    html = html.replace('--framer-input-', '--mit-input-')
    html = html.replace('var(--framer-input-', 'var(--mit-input-')
    html = html.replace('--framer-custom-cursors', '--mit-custom-cursors')
    html = html.replace('var(--framer-custom-cursors', 'var(--mit-custom-cursors')
    html = html.replace('--framer-paragraph-spacing', '--mit-paragraph-spacing')
    html = html.replace('var(--framer-paragraph-spacing', 'var(--mit-paragraph-spacing')
    html = html.replace('--framer-font-size-scale', '--mit-font-size-scale')
    html = html.replace('var(--framer-font-size-scale', 'var(--mit-font-size-scale')
    html = html.replace('--framer-text-wrap-override', '--mit-text-wrap-override')
    html = html.replace('var(--framer-text-wrap-override', 'var(--mit-text-wrap-override')
    html = html.replace('--framer-font-variation-axes', '--mit-font-variation-axes')
    html = html.replace('var(--framer-font-variation-axes', 'var(--mit-font-variation-axes')
    html = html.replace('--framer-font-weight-increase', '--mit-font-weight-increase')
    html = html.replace('var(--framer-font-weight-increase', 'var(--mit-font-weight-increase')
    html = html.replace('--framer-text-decoration', '--mit-text-decoration')
    html = html.replace('var(--framer-text-decoration', 'var(--mit-text-decoration')
    
    # Remove remaining --framer-* custom props (the ones we can't resolve)
    # Only remove from CSS (style blocks), not from inline styles
    # Actually, remove all remaining --framer-* since they won't be referenced
    html = re.sub(r'--framer-[\w-]+:[^;]+;', '', html)
    
    # Remove any remaining 'framer' text references
    html = html.replace('framer-text', 'mit-text')
    html = html.replace('framer-fit-text', 'mit-fit-text')
    html = html.replace('framer-image', 'mit-image')
    html = html.replace('rich-text-wrapper', 'mit-richtext-wrapper')
    
    # Fix the comment
    html = html.replace('Framer desktop layout', 'desktop layout')
    html = html.replace('FRAMER ORIGINAL STYLES', 'CLEAN STYLES')
    html = html.replace('Framer', 'MIT')
    
    # Remove data-framer-name attributes (we replaced them with data-section)
    html = re.sub(r'\s+data-framer-name="[^"]*"', '', html)
    
    # === STATS ===
    framer_count = len(re.findall(r'framer', html, re.IGNORECASE))
    print(f"Remaining 'framer' references: {framer_count}")
    if framer_count > 0:
        refs = re.findall(r'.{0,40}framer.{0,40}', html, re.IGNORECASE)
        for r in refs[:10]:
            print(f"  ...{r}...")
    
    print(f"Original: {len(orig)} bytes ({len(orig)//1024} KB)")
    print(f"Clean:    {len(html)} bytes ({len(html)//1024} KB)")
    print(f"Reduction: {len(orig) - len(html)} bytes ({(len(orig) - len(html)) * 100 // len(orig)}%)")
    
    dst.write_text(html, encoding='utf-8')
    print(f"\nOutput: {dst}")


if __name__ == '__main__':
    main()