#!/usr/bin/env python3
"""
De-Framer: removes Framer-specific code from the MIT landing page HTML.
Strategy: Replace Framer CSS variables with their resolved values,
strip Framer-specific data attributes and classes, and clean up
Framer-only CSS rules. The visual output must remain identical.

Approach:
1. Parse the HTML file
2. In the CSS: resolve all --framer-* CSS variables to their actual values
3. Remove Framer-specific CSS rules (data-framer-component-type selectors, etc.)
4. Keep all .framer-* class rules but rename them to .mit-* 
5. In the HTML: remove data-framer-* attributes, rename classes
6. Keep mobile version, JS, fonts intact
"""

import re
import sys
from pathlib import Path
from html.parser import HTMLParser

def main():
    input_file = Path(__file__).parent / "index-framer-original.html"
    output_file = Path(__file__).parent / "index-clean.html"
    
    content = input_file.read_text(encoding='utf-8')
    
    # === STEP 1: Separate sections ===
    # Find all <style> blocks
    style_blocks = []
    html_parts = []
    last_end = 0
    
    style_pattern = re.compile(r'<style[^>]*>(.*?)</style>', re.DOTALL)
    
    for m in style_pattern.finditer(content):
        html_parts.append(content[last_end:m.start()])
        style_blocks.append(m.group(0))
        last_end = m.end()
    html_parts.append(content[last_end:])
    
    # === STEP 2: Process CSS ===
    # The first style block contains @font-face + Framer component styles
    # We need to:
    # a) Keep @font-face rules
    # b) Keep body/base styles but resolve framer variables
    # c) Rename .framer-* classes to .mit-* 
    # d) Resolve --framer-* var() references to their values
    # e) Remove pure Framer infrastructure rules ([data-framer-component-type]...)
    # f) Keep .framer-styles-preset-* but inline their values
    
    processed_styles = []
    
    for i, block in enumerate(style_blocks):
        # Extract the CSS content
        css_match = re.match(r'<style[^>]*>(.*?)</style>', block, re.DOTALL)
        if not css_match:
            processed_styles.append(block)
            continue
        
        css = css_match.group(1)
        
        if i == 0:
            # === MAIN FRAMER CSS BLOCK ===
            # This is the big one with all the Framer styles
            
            # 1. Keep @font-face rules as-is
            font_face_rules = re.findall(r'@font-face\s*\{[^}]+\}', css)
            
            # 2. Extract all .framer-4isWX .framer-XXXX rules and resolve them
            # Pattern: .framer-4isWX .framer-NAME{props}
            # Also: .framer-4isWX .framer-A, .framer-4isWX .framer-B{props}
            
            # First, resolve the Framer CSS custom properties
            # --framer-aspect-ratio-supported -> we need to find where it's defined
            # --overflow-clip-fallback -> clip
            # --framer-will-change-override -> none (set in body)
            # --framer-will-change-filter-override -> none (set in body)
            
            # Global framer variable resolutions
            framer_var_map = {
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
            }
            
            # Resolve --1m973uw and --t829wi custom props (icon colors)
            # These are set per-element, we need to handle them in context
            # --1m973uw: color for icon, --js9iwy: type (2=icon)
            # --t829wi: color for another icon type
            
            # Extract all component rules
            # Pattern: .framer-4isWX .framer-NAME{...} or .framer-4isWX .framer-A,.framer-4isWX .framer-B{...}
            component_rules = []
            
            # Find rules with .framer-4isWX prefix
            rule_pattern = re.compile(r'\.framer-4isWX\s+([^{}]+)\{([^}]*)\}')
            for m in rule_pattern.finditer(css):
                selectors = m.group(1).strip()
                props = m.group(2)
                
                # Skip if selector contains data-border (framer-specific)
                if 'data-border' in selectors:
                    continue
                
                # Resolve framer vars in props
                for var, val in framer_var_map.items():
                    props = props.replace(var, val)
                
                # Resolve --1m973uw color variables (icon colors)
                # These are custom props set on the element itself: --1m973uw:#22c55e;--js9iwy:2
                # In context they're used as: var(--1m973uw) for color
                # We need to extract the color from the props themselves
                color_match = re.search(r'--1m973uw:(#[0-9a-fA-F]+)', props)
                if color_match:
                    color = color_match.group(1)
                    props = props.replace('var(--1m973uw)', color)
                    # Remove the custom prop definition
                    props = re.sub(r'--1m973uw:#[0-9a-fA-F]+;', '', props)
                    props = re.sub(r'--1m973uw:#[0-9a-fA-F]+\s*;', '', props)
                
                color_match2 = re.search(r'--t829wi:(#[0-9a-fA-F]+)', props)
                if color_match2:
                    color = color_match2.group(1)
                    props = props.replace('var(--t829wi)', color)
                    props = re.sub(r'--t829wi:#[0-9a-fA-F]+;', '', props)
                
                # Remove --js9iwy:2 (framer icon type)
                props = re.sub(r'--js9iwy:\d+;', '', props)
                props = re.sub(r'--js9iwy:\d+\s*;', '', props)
                
                # Resolve --border-* vars
                # --border-bottom-width:1px etc -> used in [data-border=true]:after
                # But since we're removing data-border rules, we can extract border info
                border_match = re.search(r'--border-bottom-width:(\d+px)', props)
                if border_match:
                    # These are used for borders on the element itself via :after pseudo
                    # We need to convert to actual border property
                    bw = '1px'
                    bc_match = re.search(r'--border-color:(#[0-9a-fA-F]+)', props)
                    bc = bc_match.group(1) if bc_match else '#e1e8f2'
                    bs_match = re.search(r'--border-style:(\w+)', props)
                    bs = bs_match.group(1) if bs_match else 'solid'
                    
                    # Check if border-width vars exist
                    btw = re.search(r'--border-top-width:(\d+px)', props)
                    bbw = re.search(r'--border-bottom-width:(\d+px)', props)
                    blw = re.search(r'--border-left-width:(\d+px)', props)
                    brw = re.search(r'--border-right-width:(\d+px)', props)
                    
                    if btw and bbw and blw and brw:
                        # All borders same width
                        if btw.group(1) == bbw.group(1) == blw.group(1) == brw.group(1):
                            if btw.group(1) == '0px':
                                pass  # No border
                            else:
                                # Add border if not already present
                                if 'border:' not in props and 'border-' not in props.split(';')[0]:
                                    props = f"border:{btw.group(1)} {bs} {bc};{props}"
                        else:
                            # Different widths per side
                            props = f"border-top:{btw.group(1)} {bs} {bc};border-bottom:{bbw.group(1)} {bs} {bc};border-left:{blw.group(1)} {bs} {bc};border-right:{brw.group(1)} {bs} {bc};{props}"
                    
                    # Remove the custom prop definitions
                    props = re.sub(r'--border-\w+:\d+px;', '', props)
                    props = re.sub(r'--border-color:#[0-9a-fA-F]+;', '', props)
                    props = re.sub(r'--border-style:\w+;', '', props)
                
                # Rename selector classes: .framer-NAME -> .mit-NAME
                # But we need to keep the .framer-4isWX parent -> .mit-main
                selectors = selectors.replace('.framer-4isWX', '.mit-desktop')
                # Don't rename individual classes yet - we'll do it in HTML
                
                component_rules.append((selectors, props))
            
            # Also handle body rules
            body_rules = re.findall(r'body\s*\{([^}]*)\}', css)
            body_css = ''
            for br in body_rules:
                # Resolve framer vars
                for var, val in framer_var_map.items():
                    br = br.replace(var, val)
                # Remove framer-specific custom props
                br = re.sub(r'--framer-[\w-]+:[^;]+;', '', br)
                body_css += f"body{{{br}}}\n"
            
            # Handle @supports rules - resolve to non-framer equivalents
            # These set --framer-will-change-override and --framer-will-change-filter-override
            # We already resolved those to 'none', so we can skip @supports blocks
            
            # Handle .framer-4isWX[data-border=true]:after rules
            # These create borders via pseudo-elements
            # We've already converted borders to actual border properties
            
            # Handle [data-framer-component-type] rules - REMOVE entirely
            # These are Framer infrastructure for positioning
            
            # Handle .framer-styles-preset-* rules
            # These define text styles via CSS variables
            # We need to resolve them to actual CSS properties
            
            # Extract text style presets
            preset_pattern = re.compile(r'\.framer-(\w+)\s+\.framer-styles-preset-(\w+):not\([^)]+\)[^{]*\{([^}]*)\}')
            preset_rules = []
            for m in preset_pattern.finditer(css):
                parent = m.group(1)
                preset_name = m.group(2)
                props = m.group(3)
                
                # Resolve --framer-font-* to actual font properties
                font_family = re.search(r'--framer-font-family:\s*([^;]+)', props)
                font_size = re.search(r'--framer-font-size:\s*(\d+px)', props)
                font_weight = re.search(r'--framer-font-weight:\s*(\d+)', props)
                font_style = re.search(r'--framer-font-style:\s*(\w+)', props)
                line_height = re.search(r'--framer-line-height:\s*([\d.]+em)', props)
                letter_spacing = re.search(r'--framer-letter-spacing:\s*([-\d.]+em)', props)
                text_color = re.search(r'--framer-text-color:\s*(#[0-9a-fA-F]+)', props)
                text_align = re.search(r'--framer-text-alignment:\s*(\w+)', props)
                text_wrap = re.search(r'--framer-text-wrap:\s*(\w+)', props)
                
                resolved = ""
                if font_family:
                    ff = font_family.group(1).strip()
                    # Clean up "Geist","Geist Placeholder",sans-serif -> 'Geist', sans-serif
                    ff = re.sub(r'"([^"]+)","[^"]+",sans-serif', r'"\1",sans-serif', ff)
                    resolved += f"font-family:{ff};"
                if font_size:
                    resolved += f"font-size:{font_size.group(1)};"
                if font_weight:
                    resolved += f"font-weight:{font_weight.group(1)};"
                if font_style:
                    resolved += f"font-style:{font_style.group(1)};"
                if line_height:
                    resolved += f"line-height:{line_height.group(1)};"
                if letter_spacing:
                    resolved += f"letter-spacing:{letter_spacing.group(1)};"
                if text_color:
                    resolved += f"color:{text_color.group(1)};"
                if text_align:
                    resolved += f"text-align:{text_align.group(1)};"
                if text_wrap:
                    resolved += f"text-wrap:{text_wrap.group(1)};"
                
                preset_rules.append((parent, preset_name, resolved))
            
            # Now build the new CSS
            new_css = "/* === CLEAN STYLES (de-Framed) === */\n\n"
            
            # 1. Font faces
            for ff in font_face_rules:
                new_css += ff + "\n\n"
            
            # 2. Body styles (cleaned)
            new_css += body_css + "\n"
            
            # 3. Component styles with resolved vars
            for selectors, props in component_rules:
                new_css += f".mit-desktop {selectors.replace('.mit-desktop ', '')}{{{props}}}\n"
            
            # 4. Text presets as utility classes
            new_css += "\n/* === TEXT PRESETS === */\n"
            for parent, name, resolved in preset_rules:
                new_css += f".text-preset-{name}{{{resolved}}}\n"
            
            # 5. Framer text base styles (simplified)
            new_css += """
/* === TEXT BASE === */
p, div, h1, h2, h3, h4, h5, h6, ol, ul, li, span, a, mark, code, blockquote {
  margin: 0;
  padding: 0;
}
p, div, h1, h2, h3, h4, h5, h6, li, ol, ul, span, mark {
  font-family: 'Geist', -apple-system, BlinkMacSystemFont, sans-serif;
  font-style: normal;
  font-weight: 400;
  color: #1a1f2b;
  font-size: 16px;
  letter-spacing: 0;
  text-transform: none;
  text-decoration: none;
  line-height: 1.2em;
  text-align: start;
}
strong { font-weight: 700; }
em { font-style: italic; }
a { cursor: pointer; text-decoration: none; color: inherit; }
a:hover { color: inherit; }
"""
            
            processed_styles.append(f'<style>\n{new_css}\n</style>')
            
        else:
            # Other style blocks (responsive, adaptive) - keep as-is
            # but rename .framer-4isWX references
            css = css.replace('.framer-4isWX', '.mit-desktop')
            processed_styles.append(f'<style>\n{css}\n</style>')
    
    # === STEP 3: Reassemble HTML ===
    result = ""
    part_idx = 0
    style_idx = 0
    
    for m in style_pattern.finditer(content):
        result += html_parts[part_idx]
        part_idx += 1
        if style_idx < len(processed_styles):
            result += processed_styles[style_idx]
            style_idx += 1
    result += html_parts[part_idx]
    
    # === STEP 4: Clean HTML attributes ===
    # Remove data-framer-component-type="..."
    result = re.sub(r'\s+data-framer-component-type="[^"]*"', '', result)
    # Remove data-framer-component-text-autosized
    result = re.sub(r'\s+data-framer-component-text-autosized(="[^"]*")?', '', result)
    # Remove data-border="true"
    result = re.sub(r'\s+data-border="true"', '', result)
    # Remove data-text-fill
    result = re.sub(r'\s+data-text-fill(="[^"]*")?', '', result)
    # Remove data-nested-link
    result = re.sub(r'\s+data-nested-link(="[^"]*")?', '', result)
    # Remove any remaining data-framer-* attributes
    result = re.sub(r'\s+data-framer-\w+(="[^"]*")?', '', result)
    
    # === STEP 5: Rename classes ===
    # .framer-4isWX -> .mit-desktop (already done in CSS)
    # .framer-XXXX -> .mit-XXXX (keep unique names)
    # In HTML: class="framer-XXXX" -> class="mit-XXXX"
    # Also handle multiple classes: class="framer-XXX framer-text" etc
    
    # Rename framer classes in HTML
    def rename_framer_class(match):
        cls = match.group(1)
        # Rename framer-XXX to mit-XXX, keep framer-text as mit-text
        parts = cls.split()
        new_parts = []
        for p in parts:
            if p.startswith('framer-'):
                if p == 'framer-text':
                    new_parts.append('mit-text')
                elif p == 'framer-styles-preset-1wu8czi':
                    new_parts.append('text-preset-link')
                elif p == 'framer-styles-preset-1t75fkg':
                    new_parts.append('text-preset-h1')
                elif p == 'framer-styles-preset-5mwvuw':
                    new_parts.append('text-preset-body')
                elif p == 'framer-styles-preset-aqyig4':
                    new_parts.append('text-preset-h2')
                elif p.startswith('framer-styles-preset-'):
                    new_parts.append('text-preset-' + p.split('-')[-1])
                elif p == 'framer-4isWX':
                    new_parts.append('mit-desktop')
                elif p == 'framer-fit-text':
                    new_parts.append('mit-fit-text')
                elif p == 'rich-text-wrapper':
                    new_parts.append('rich-text-wrapper')
                elif p == 'isCurrent':
                    new_parts.append('isCurrent')
                else:
                    # framer-XXXX -> mit-XXXX
                    new_parts.append('mit-' + p[7:])
            else:
                new_parts.append(p)
        return f'class="{" ".join(new_parts)}"'
    
    result = re.sub(r'class="([^"]*)"', rename_framer_class, result)
    
    # === STEP 6: Clean up remaining framer artifacts ===
    # Remove --framer-* inline custom properties
    # These appear as style="--framer-xxx:yyy;..."
    def clean_framer_inline_style(match):
        style = match.group(1)
        # Remove --framer-* custom properties
        style = re.sub(r'--framer-[\w-]+:[^;]+;?', '', style)
        # Remove --1m973uw, --js9iwy, --t829wi custom props
        style = re.sub(r'--1m973uw:[^;]+;?', '', style)
        style = re.sub(r'--js9iwy:[^;]+;?', '', style)
        style = re.sub(r'--t829wi:[^;]+;?', '', style)
        # Remove --border-* custom props (already resolved)
        style = re.sub(r'--border-[\w-]+:[^;]+;?', '', style)
        # Clean up multiple semicolons and leading/trailing
        style = re.sub(r';+', ';', style).strip(';').strip()
        if style:
            return f'style="{style}"'
        return ''
    
    result = re.sub(r'style="([^"]*)"', clean_framer_inline_style, result)
    
    # Remove empty class attributes
    result = re.sub(r'class="\s*"', '', result)
    # Remove empty style attributes
    result = re.sub(r'style="\s*"', '', result)
    
    # === STEP 7: Handle Framer text CSS rules ===
    # The CSS still has [data-framer-component-type=Text] rules
    # We need to add equivalent rules for .mit-text class
    
    # Actually, let's check - did we already handle this in the CSS step?
    # The text base styles section should cover most cases.
    
    # Write output
    output_file.write_text(result, encoding='utf-8')
    
    # Stats
    orig_size = len(content)
    new_size = len(result)
    print(f"Original: {orig_size} bytes ({orig_size//1024} KB)")
    print(f"Clean:     {new_size} bytes ({new_size//1024} KB)")
    print(f"Reduction: {orig_size - new_size} bytes ({(orig_size - new_size) * 100 // orig_size}%)")
    
    # Check for remaining framer references
    framer_refs = len(re.findall(r'framer', result, re.IGNORECASE))
    print(f"Remaining 'framer' references: {framer_refs}")
    
    # List remaining framer refs
    if framer_refs > 0:
        remaining = re.findall(r'.{0,40}framer.{0,40}', result, re.IGNORECASE)
        for r in remaining[:20]:
            print(f"  ...{r}...")
    
    print(f"\nOutput: {output_file}")

if __name__ == '__main__':
    main()