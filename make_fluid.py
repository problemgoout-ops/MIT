from pathlib import Path
import re

html = Path('index.html').read_text()

# === 1. REPLACE the entire second <style> block (the scale hack + mobile switch)
# with a comprehensive fluid override stylesheet.
second_style_start = html.find('<style>', html.find('<style>') + 1)
second_style_end = html.find('</style>', second_style_start) + len('</style>')

# We keep the third style block for mobile animations/form status, but merge them.
third_style_start = html.find('<style>', second_style_end)
third_style_end = html.find('</style>', third_style_start) + len('</style>')

# Extract existing mobile animation + form status rules from third block
third_content = html[third_style_start:third_style_end]
mobile_anim = """
/* Mobile version entrance animations */
.mobile-version .animate-in {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity .6s ease, transform .6s ease;
}
.mobile-version .animate-in.visible {
  opacity: 1;
  transform: translateY(0);
}

/* Mobile form status messages */
#form-status-mobile {
  font-size: 13px;
  margin-top: 10px;
  text-align: center;
  min-height: 18px;
}
#form-status-mobile.success { color: #22c55e; }
#form-status-mobile.error { color: #dc2626; }
"""

fluid_css = """<style>
/* === FLUID RESPONSIVE OVERRIDES v4 === */

/* Base: make the Framer desktop layout fluid, not fixed */
.framer-4isWX.framer-72rtr7 {
  width: 100% !important;
  max-width: 1200px !important;
  margin: 0 auto !important;
  overflow-x: hidden !important;
}

/* Remove the scale hack entirely; instead rely on fluid max-width */
@media (max-width: 1199px) and (min-width: 769px) {
  html, body { overflow-x: hidden; margin: 0; padding: 0; }
  #main { transform: none !important; width: 100% !important; max-width: 1200px !important; margin: 0 auto !important; }
}

/* Global fluid helpers */
html, body { overflow-x: hidden; }
img, svg, video { max-width: 100%; height: auto; }

/* --- Fluid desktop (≥769px) --- */
@media (min-width: 769px) {
  .mobile-version { display: none !important; }

  /* Hero row */
  .framer-4isWX .framer-1blo7nt {
    gap: clamp(24px, 4vw, 44px) !important;
    padding: clamp(28px, 4vw, 40px) clamp(16px, 3vw, 24px) clamp(24px, 3vw, 30px) !important;
  }
  .framer-4isWX .framer-ricdt9 { flex: 1 1 45% !important; width: auto !important; }
  .framer-4isWX .framer-5dfrwx {
    flex: 1 1 55% !important;
    width: auto !important;
    min-width: 0 !important;
    height: auto !important;
    min-height: clamp(420px, 50vw, 590px) !important;
  }
  .framer-4isWX .framer-p9ydro {
    width: clamp(280px, 40vw, 310px) !important;
    height: auto !important;
  }

  /* Headings scale */
  .framer-4isWX .framer-15gpk13,
  .framer-4isWX .framer-vid4l6,
  .framer-4isWX .framer-xn89c1,
  .framer-4isWX .framer-rs30in {
    font-size: clamp(28px, 4vw, 52px) !important;
  }

  /* Section wrappers */
  .framer-4isWX .framer-1etxs3x,
  .framer-4isWX .framer-1bmxqmy,
  .framer-4isWX .framer-1ry2qut,
  .framer-4isWX .framer-u0ra1u,
  .framer-4isWX .framer-wxi2f4,
  .framer-4isWX .framer-z4ncfl {
    max-width: 1200px !important;
    padding-left: clamp(16px, 3vw, 24px) !important;
    padding-right: clamp(16px, 3vw, 24px) !important;
  }

  /* 4-col grids become auto-fit */
  .framer-4isWX .framer-1h4gf12,
  .framer-4isWX .framer-1q2f5ic {
    grid-template-columns: repeat(auto-fit, minmax(clamp(220px, 22vw, 260px), 1fr)) !important;
  }
  .framer-4isWX .framer-1fy3nmw {
    grid-template-columns: repeat(auto-fit, minmax(clamp(220px, 22vw, 280px), 1fr)) !important;
  }
  .framer-4isWX .framer-1e81p67 {
    grid-template-columns: repeat(auto-fit, minmax(clamp(140px, 15vw, 180px), 1fr)) !important;
  }

  /* Integration diagram */
  .framer-4isWX .framer-4ko2b9 {
    height: auto !important;
    min-height: clamp(360px, 38vw, 440px) !important;
    padding: clamp(16px, 3vw, 28px) !important;
    gap: clamp(12px, 2vw, 18px) !important;
  }
  .framer-4isWX .framer-xbunyb {
    width: clamp(220px, 28vw, 300px) !important;
    height: clamp(220px, 28vw, 300px) !important;
  }
  .framer-4isWX .framer-hgje79 {
    width: clamp(120px, 16vw, 180px) !important;
    height: clamp(120px, 16vw, 180px) !important;
  }

  /* Center cluster badge widths */
  .framer-4isWX .framer-1fe218z { width: auto !important; max-width: 230px !important; }
  .framer-4isWX .framer-h1tjuw { width: auto !important; max-width: 270px !important; }

  /* CTA banner */
  .framer-4isWX .framer-1wzjap8 {
    padding: clamp(24px, 3vw, 38px) !important;
    gap: clamp(16px, 2.5vw, 24px) !important;
    flex-flow: row wrap !important;
  }

  /* Pricing / big cards */
  .framer-4isWX .framer-1a7afvb {
    padding: clamp(24px, 3vw, 34px) !important;
  }

  /* FAQ / form widths */
  .framer-4isWX .framer-4r1i58,
  .framer-4isWX .framer-6tctj2,
  .framer-4isWX .framer-17tev6p,
  .framer-4isWX .framer-1pp9zve,
  .framer-4isWX .framer-1bpwhiz {
    width: 100% !important;
    max-width: 760px !important;
  }
}

/* --- Tablet tweaks ( tighten gaps, hide long nav links if needed ) --- */
@media (max-width: 1024px) and (min-width: 769px) {
  .framer-4isWX .framer-y3d47h {
    gap: clamp(12px, 2vw, 22px) !important;
  }
  .framer-4isWX .framer-1762gwr {
    padding: 10px 14px !important;
  }
}

/* --- Mobile layout becomes the single source below 768px --- */
@media (max-width: 768px) {
  #main { display: none !important; }
  .mobile-version { display: block !important; }
}

""" + mobile_anim + """
</style>"""

new_html = html[:second_style_start] + fluid_css + html[third_style_end:]

# === 2. FLUIDIFY inline styles inside mobile-version div ===
# We'll do targeted replacements of the worst fixed values.
mobile_start = new_html.find('<div class="mobile-version"')
mobile_end = new_html.find('</body>', mobile_start)
mobile = new_html[mobile_start:mobile_end]

replacements = [
    # Hero section fluid typography & spacing
    ('font-size:30px;', 'font-size:clamp(24px, 7vw, 34px);'),
    ('font-size:15px;', 'font-size:clamp(14px, 4vw, 16px);'),
    ('padding:36px 16px 28px;', 'padding:clamp(28px, 8vw, 48px) clamp(14px, 4vw, 22px) clamp(24px, 6vw, 32px);'),
    # Telegram mock
    ('max-width:380px;', 'max-width:min(92vw, 420px);'),
    # Section wrappers
    ('padding:0 16px 40px;', 'padding:0 clamp(14px, 4vw, 22px) clamp(32px, 8vw, 48px);'),
    ('padding:48px 16px 24px;', 'padding:clamp(36px, 8vw, 56px) clamp(14px, 4vw, 22px) clamp(20px, 5vw, 28px);'),
    ('padding:0 16px 64px;', 'padding:0 clamp(14px, 4vw, 22px) clamp(48px, 12vw, 72px);'),
    ('padding:40px 16px 60px;', 'padding:clamp(32px, 8vw, 48px) clamp(14px, 4vw, 22px) clamp(48px, 12vw, 72px);'),
    ('padding:0 16px 88px;', 'padding:0 clamp(14px, 4vw, 22px) clamp(64px, 16vw, 96px);'),
    ('padding:54px 16px 44px;', 'padding:clamp(40px, 8vw, 60px) clamp(14px, 4vw, 22px) clamp(36px, 8vw, 48px);'),
    # Advantage cards 2-col
    ('grid-template-columns:repeat(2,1fr);', 'grid-template-columns:repeat(auto-fit, minmax(140px, 1fr));'),
    # Capabilities grid -> stack on very small
    ('grid-template-columns:repeat(2,1fr);gap:12px;', 'grid-template-columns:repeat(auto-fit, minmax(140px, 1fr));gap:12px;'),
    # Skills / integration 3-col
    ('grid-template-columns:repeat(3,1fr);gap:12px;', 'grid-template-columns:repeat(auto-fit, minmax(90px, 1fr));gap:12px;'),
    # Security cards
    ('grid-template-columns:repeat(2,1fr);gap:14px;', 'grid-template-columns:repeat(auto-fit, minmax(140px, 1fr));gap:14px;'),
    # Pricing / launch card
    ('padding:28px 20px;', 'padding:clamp(22px, 6vw, 32px) clamp(16px, 5vw, 28px);'),
    # FAQ
    ('padding:16px 18px;', 'padding:clamp(14px, 4vw, 18px) clamp(14px, 5vw, 22px);'),
]

for old, new in replacements:
    mobile = mobile.replace(old, new)

new_html = new_html[:mobile_start] + mobile + new_html[mobile_end:]

Path('index.html').write_text(new_html)
print('Done. New length:', len(new_html))
print('Diff:', len(new_html) - len(html))
