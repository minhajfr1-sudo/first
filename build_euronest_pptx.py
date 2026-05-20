"""Build Euronest pitch deck as a PPTX.

Style: 16:9, navy + accent blue + warm sand background, Calibri, large
typography, one idea per slide. Copy written through the humanizer pass:
no em dashes, no "stands as / serves as", no rule-of-three by default,
no signposting, varied rhythm.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION

NAVY = RGBColor(0x10, 0x2A, 0x54)
ACCENT = RGBColor(0x3E, 0x63, 0xA6)
SAND = RGBColor(0xF5, 0xEF, 0xE6)
INK = RGBColor(0x1C, 0x1C, 0x1C)
MUTED = RGBColor(0x6B, 0x73, 0x80)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xEE, 0xF2, 0xF8)
GOLD = RGBColor(0xC9, 0x9A, 0x3C)
GREEN = RGBColor(0x4A, 0x7C, 0x59)
CORAL = RGBColor(0xD0, 0x6A, 0x5F)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

blank = prs.slide_layouts[6]


def add_bg(slide, color=SAND):
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height
    )
    bg.line.fill.background()
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.shadow.inherit = False
    return bg


def add_text(slide, text, left, top, width, height,
             size=18, bold=False, color=INK, align=PP_ALIGN.LEFT,
             font="Calibri", italic=False, anchor=MSO_ANCHOR.TOP,
             line_spacing=1.15):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0)
    tf.margin_right = Inches(0)
    tf.margin_top = Inches(0)
    tf.margin_bottom = Inches(0)
    tf.vertical_anchor = anchor
    if isinstance(text, str):
        lines = text.split("\n")
    else:
        lines = text
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        r = p.add_run()
        r.text = line
        r.font.name = font
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
    return tb


def add_rect(slide, left, top, width, height, fill, line=None, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, left, top, width, height)
    s.line.fill.background() if line is None else setattr(s.line.color, "rgb", line)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.shadow.inherit = False
    return s


def header_band(slide, title, eyebrow=None):
    add_rect(slide, 0, 0, prs.slide_width, Inches(0.18), NAVY)
    if eyebrow:
        add_text(slide, eyebrow.upper(), Inches(0.7), Inches(0.4),
                 Inches(11), Inches(0.4),
                 size=11, bold=True, color=ACCENT)
    add_text(slide, title, Inches(0.7), Inches(0.75),
             Inches(11.9), Inches(1.0),
             size=32, bold=True, color=NAVY)
    # accent rule
    add_rect(slide, Inches(0.7), Inches(1.6), Inches(0.6), Inches(0.04), ACCENT)


def footer(slide, page_no):
    add_text(slide, "Euronest  |  Business Plan  |  April 2026",
             Inches(0.7), Inches(7.05), Inches(8), Inches(0.3),
             size=9, color=MUTED)
    add_text(slide, str(page_no),
             Inches(12.3), Inches(7.05), Inches(0.6), Inches(0.3),
             size=9, color=MUTED, align=PP_ALIGN.RIGHT)


def bullet_box(slide, items, left, top, width, height,
               size=16, bullet="— ", color=INK):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0)
    tf.margin_right = Inches(0)
    tf.margin_top = Inches(0)
    tf.margin_bottom = Inches(0)
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = 1.25
        p.space_after = Pt(6)
        r = p.add_run()
        r.text = bullet + item
        r.font.name = "Calibri"
        r.font.size = Pt(size)
        r.font.color.rgb = color
    return tb


page = 1


# =====================================================================
# SLIDE 1 — Cover
# =====================================================================
s = prs.slides.add_slide(blank)
add_bg(s, NAVY)
# decorative shapes
add_rect(s, Inches(0), Inches(6.4), prs.slide_width, Inches(1.1), ACCENT)
add_rect(s, Inches(11.3), Inches(0), Inches(2), prs.slide_height, ACCENT)

add_text(s, "EURONEST", Inches(0.9), Inches(1.7), Inches(10),
         Inches(1.4), size=84, bold=True, color=WHITE)
add_text(s, "Student housing & lifestyle subscription, France first.",
         Inches(0.9), Inches(3.3), Inches(10), Inches(1),
         size=24, color=WHITE, italic=True)
add_rect(s, Inches(0.95), Inches(4.1), Inches(0.8), Inches(0.05), GOLD)
add_text(s, "Business Plan  |  April 2026", Inches(0.9),
         Inches(4.3), Inches(10), Inches(0.5),
         size=18, color=WHITE)
add_text(s, "ISTEC, Paris", Inches(0.9), Inches(4.75),
         Inches(10), Inches(0.5), size=14, color=LIGHT)
add_text(s,
         "Mansoor Ali  ·  Fidha Fathima Panankavil  ·  Leo Joy  ·  Nithin Stanley George\n"
         "Minhaj Eshwaramangalam  ·  Gopinath Dasan  ·  Pallampettivelayudhan Nithin",
         Inches(0.9), Inches(5.5), Inches(11), Inches(0.8),
         size=13, color=LIGHT)


# =====================================================================
# SLIDE 2 — Agenda
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "What we will cover today", eyebrow="Agenda")

agenda = [
    ("01", "The problem", "Why student housing in France is broken"),
    ("02", "Solution", "What Euronest actually does"),
    ("03", "Market", "Where we are starting and why"),
    ("04", "Business model", "Tiers, revenue, unit economics"),
    ("05", "Financials & ask", "Three-year plan and the EUR 180k raise"),
    ("06", "Team & roadmap", "Who is doing this and what comes next"),
]

x = Inches(0.7)
y = Inches(2.0)
w = Inches(6.0)
h = Inches(0.78)
for i, (num, title, sub) in enumerate(agenda):
    row = i // 2
    col = i % 2
    lx = x + col * (w + Inches(0.2))
    ly = y + row * (h + Inches(0.55))
    add_rect(s, lx, ly, Inches(0.7), h, ACCENT)
    add_text(s, num, lx, ly, Inches(0.7), h,
             size=22, bold=True, color=WHITE,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_rect(s, lx + Inches(0.7), ly, w - Inches(0.7), h, WHITE)
    add_text(s, title, lx + Inches(0.9), ly + Inches(0.05),
             w - Inches(0.9), Inches(0.4), size=17, bold=True, color=NAVY)
    add_text(s, sub, lx + Inches(0.9), ly + Inches(0.42),
             w - Inches(0.9), Inches(0.4), size=12, color=MUTED)

footer(s, page)


# =====================================================================
# SLIDE 3 — The problem
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "Finding student housing in France is broken",
            eyebrow="01 · Problem")

stats = [
    ("1 in 3", "students we interviewed had sent money to a fake or "
               "misleading listing."),
    ("12-20 pages", "of a French legal-vocabulary lease, usually signed "
                    "without full understanding."),
    ("3x rent", "the income a French guarantor must show. Most non-EU "
                "students cannot find one."),
    ("6 months", "rent demanded upfront by many landlords when the "
                 "guarantor wall blocks them."),
]
x = Inches(0.7)
y = Inches(2.0)
w = Inches(2.95)
h = Inches(2.2)
for i, (big, line) in enumerate(stats):
    lx = x + i * (w + Inches(0.15))
    add_rect(s, lx, y, w, h, WHITE)
    add_rect(s, lx, y, w, Inches(0.12), ACCENT)
    add_text(s, big, lx + Inches(0.25), y + Inches(0.35),
             w - Inches(0.5), Inches(0.9), size=34, bold=True, color=NAVY)
    add_text(s, line, lx + Inches(0.25), y + Inches(1.2),
             w - Inches(0.5), h - Inches(1.3), size=13, color=INK,
             line_spacing=1.3)

add_text(
    s,
    "Source: 42 interviews with international students at ISTEC and "
    "three other Paris schools, Jan-Mar 2026.",
    Inches(0.7), Inches(6.5), Inches(11), Inches(0.4),
    size=11, italic=True, color=MUTED,
)
footer(s, page)


# =====================================================================
# SLIDE 4 — Why now
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "The market is moving in our direction",
            eyebrow="01 · Why now")

# Left column: 3 key facts
y = Inches(2.0)
facts = [
    ("430,000",
     "international students in France in 2024-25.",
     "Stated government target: 500,000 by 2027."),
    ("~175,000",
     "publicly owned CROUS rooms.",
     "Waitlisted, allocation favours French and EU students."),
    ("<15%",
     "of the private student housing stock is professionally managed.",
     "The rest is fragmented across small landlords."),
]
for i, (big, line, sub) in enumerate(facts):
    ly = y + i * Inches(1.55)
    add_text(s, big, Inches(0.7), ly, Inches(2.5), Inches(0.7),
             size=36, bold=True, color=ACCENT)
    add_text(s, line, Inches(3.4), ly + Inches(0.05),
             Inches(5.5), Inches(0.6), size=15, bold=True, color=NAVY)
    add_text(s, sub, Inches(3.4), ly + Inches(0.5),
             Inches(5.5), Inches(0.6), size=12, color=MUTED)

# Right column: insight
add_rect(s, Inches(9.2), Inches(2.0), Inches(3.5), Inches(4.5), NAVY)
add_text(s, "Why now",
         Inches(9.4), Inches(2.15), Inches(3.2), Inches(0.5),
         size=14, bold=True, color=GOLD)
add_text(
    s,
    "The 2026 intake is the first cohort that grew up booking flights, "
    "food and rides from an app.\n\n"
    "They expect housing to work the same way.\n\n"
    "Right now it does not.",
    Inches(9.4), Inches(2.7), Inches(3.1), Inches(4),
    size=14, color=WHITE, line_spacing=1.35
)

footer(s, page)


# =====================================================================
# SLIDE 5 — Solution
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "Euronest in one frame", eyebrow="02 · Solution")

# Three pillars
y = Inches(2.1)
pillars = [
    ("Verified apartment",
     "Every property visited and checked against a 38-point list.\n"
     "We refuse roughly a third of what landlords offer us."),
    ("One bundled price",
     "Rent, utilities, internet, gym, streaming and optional meals "
     "in a single monthly invoice.\nEuronest acts as guarantor for "
     "standard and premium tiers."),
    ("One named coordinator",
     "Each subscriber gets one person, multilingual, reachable on "
     "WhatsApp from move-in to move-out."),
]
w = Inches(4.0)
for i, (t, body) in enumerate(pillars):
    lx = Inches(0.7) + i * (w + Inches(0.15))
    add_rect(s, lx, y, w, Inches(4.4), WHITE)
    add_rect(s, lx, y, w, Inches(0.65), ACCENT)
    add_text(s, str(i + 1), lx + Inches(0.3), y + Inches(0.1),
             Inches(0.5), Inches(0.5), size=20, bold=True, color=WHITE)
    add_text(s, t, lx + Inches(1.0), y + Inches(0.12),
             w - Inches(1.2), Inches(0.5), size=17, bold=True, color=WHITE)
    add_text(s, body, lx + Inches(0.3), y + Inches(0.95),
             w - Inches(0.6), Inches(3.3), size=13, color=INK,
             line_spacing=1.35)

footer(s, page)


# =====================================================================
# SLIDE 6 — How it works
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "How a student becomes a subscriber",
            eyebrow="02 · User journey")

steps = [
    ("01", "Discover",
     "TikTok, friend or YouTube city guide. Lands on the site, "
     "watches a 90-second explainer."),
    ("02", "Book",
     "Picks a city, a tier and a move-in date. Signs a bilingual "
     "lease. Pays into escrow."),
    ("03", "Arrive",
     "Coordinator meets the student at the door. Inventory walkthrough. "
     "Wi-Fi already on."),
    ("04", "Live",
     "WhatsApp contact stays open. Maintenance SLAs published. "
     "Quiet-hours code of conduct signed."),
    ("05", "Renew",
     "Two months before lease end: renew, swap city, or get matched "
     "with a roommate for next year."),
]
y = Inches(2.4)
step_w = Inches(2.40)
for i, (n, t, body) in enumerate(steps):
    lx = Inches(0.55) + i * (step_w + Inches(0.07))
    add_rect(s, lx, y + Inches(0.4), step_w, Inches(0.07), ACCENT)
    add_rect(s, lx + step_w / 2 - Inches(0.4), y, Inches(0.8),
             Inches(0.8), NAVY, shape=MSO_SHAPE.OVAL)
    add_text(s, n, lx + step_w / 2 - Inches(0.4), y,
             Inches(0.8), Inches(0.8), size=15, bold=True, color=WHITE,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, t, lx, y + Inches(1.0), step_w, Inches(0.5),
             size=16, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    add_text(s, body, lx + Inches(0.1), y + Inches(1.5),
             step_w - Inches(0.2), Inches(3.5), size=12, color=INK,
             align=PP_ALIGN.CENTER, line_spacing=1.35)

footer(s, page)


# =====================================================================
# SLIDE 7 — Tiers
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "Three tiers, one invoice", eyebrow="02 · Offer")

tiers = [
    ("Basic", "EUR 690", NAVY,
     ["Furnished apartment", "Fibre internet", "Utilities included",
      "Contents insurance"],
     "Short stays, budget-sensitive Erasmus students."),
    ("Standard", "EUR 890", ACCENT,
     ["Everything in Basic", "Gym pass (Basic-Fit / Fitness Park)",
      "Netflix or Amazon Prime", "Euronest acts as guarantor"],
     "Master's students for a full academic year."),
    ("Premium", "EUR 1,190", GOLD,
     ["Everything in Standard", "Meal plan, 15 meals/week",
      "Visa & paperwork support", "One return-home flight credit "
      "(up to EUR 450)"],
     "Students whose families want the full setup."),
]
y = Inches(1.9)
w = Inches(4.05)
for i, (name, price, color, lines, who) in enumerate(tiers):
    lx = Inches(0.7) + i * (w + Inches(0.1))
    add_rect(s, lx, y, w, Inches(4.9), WHITE)
    add_rect(s, lx, y, w, Inches(1.05), color)
    add_text(s, name, lx + Inches(0.3), y + Inches(0.1),
             w - Inches(0.6), Inches(0.5), size=20, bold=True, color=WHITE)
    add_text(s, price + " / month", lx + Inches(0.3), y + Inches(0.55),
             w - Inches(0.6), Inches(0.5), size=16, color=WHITE)
    # bullets
    by = y + Inches(1.25)
    for line in lines:
        add_text(s, "·  " + line, lx + Inches(0.3), by,
                 w - Inches(0.6), Inches(0.45), size=13.5, color=INK)
        by += Inches(0.45)
    # who
    add_rect(s, lx + Inches(0.25), y + Inches(4.0),
             w - Inches(0.5), Inches(0.04), color)
    add_text(s, who, lx + Inches(0.3), y + Inches(4.12),
             w - Inches(0.6), Inches(0.8), size=11.5, italic=True, color=MUTED,
             line_spacing=1.3)

add_text(s,
         "Paris pricing shown. Lyon and other cities 15-25% lower. "
         "Six-month prepay carries a 5% discount.",
         Inches(0.7), Inches(7.0), Inches(11.5), Inches(0.4),
         size=11, italic=True, color=MUTED)
footer(s, page)


# =====================================================================
# SLIDE 8 — Market & cities
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "Five cities, ~60% of France's international students",
            eyebrow="03 · Market")

# Left: city table
y = Inches(2.0)
add_rect(s, Inches(0.7), y, Inches(6.5), Inches(0.55), NAVY)
add_text(s, "City", Inches(0.85), y + Inches(0.1),
         Inches(2), Inches(0.4), size=13, bold=True, color=WHITE)
add_text(s, "Intl. students", Inches(2.7), y + Inches(0.1),
         Inches(2), Inches(0.4), size=13, bold=True, color=WHITE)
add_text(s, "Avg studio rent", Inches(4.5), y + Inches(0.1),
         Inches(1.7), Inches(0.4), size=13, bold=True, color=WHITE)
add_text(s, "Entry", Inches(6.1), y + Inches(0.1),
         Inches(1), Inches(0.4), size=13, bold=True, color=WHITE)
cities = [
    ("Paris", "115,000", "EUR 950", "Y1"),
    ("Lyon", "32,000", "EUR 620", "Y1"),
    ("Lille", "21,000", "EUR 540", "Y2"),
    ("Toulouse", "19,000", "EUR 560", "Y2"),
    ("Marseille", "17,000", "EUR 600", "Y3"),
]
ry = y + Inches(0.55)
for i, row in enumerate(cities):
    add_rect(s, Inches(0.7), ry, Inches(6.5), Inches(0.5),
             WHITE if i % 2 == 0 else LIGHT)
    add_text(s, row[0], Inches(0.85), ry + Inches(0.08),
             Inches(2), Inches(0.4), size=13, bold=True, color=NAVY)
    add_text(s, row[1], Inches(2.7), ry + Inches(0.08),
             Inches(2), Inches(0.4), size=13, color=INK)
    add_text(s, row[2], Inches(4.5), ry + Inches(0.08),
             Inches(1.7), Inches(0.4), size=13, color=INK)
    add_text(s, row[3], Inches(6.1), ry + Inches(0.08),
             Inches(1), Inches(0.4), size=13, bold=True, color=ACCENT)
    ry += Inches(0.5)

# Right: callout
add_rect(s, Inches(7.7), Inches(2.0), Inches(5.0), Inches(4.5), NAVY)
add_text(s, "What this means", Inches(7.9), Inches(2.15),
         Inches(4.5), Inches(0.5), size=14, bold=True, color=GOLD)
add_text(s,
         "Paris and Lyon at launch give us critical mass without "
         "spreading too thin.\n\n"
         "Lille and Toulouse in year two open the Erasmus corridor.\n\n"
         "Marseille closes the southern triangle in year three.",
         Inches(7.9), Inches(2.75), Inches(4.6), Inches(3.5),
         size=14, color=WHITE, line_spacing=1.4)

footer(s, page)


# =====================================================================
# SLIDE 9 — Competitor map
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "Where we sit against the alternatives",
            eyebrow="03 · Competition")

# 2x2 matrix
chart_l = Inches(0.7)
chart_t = Inches(2.0)
chart_w = Inches(7.5)
chart_h = Inches(4.6)
add_rect(s, chart_l, chart_t, chart_w, chart_h, WHITE)
# axes
add_rect(s, chart_l + chart_w / 2, chart_t, Inches(0.02), chart_h, MUTED)
add_rect(s, chart_l, chart_t + chart_h / 2, chart_w, Inches(0.02), MUTED)
add_text(s, "Service depth", chart_l + Inches(0.1), chart_t + Inches(0.1),
         Inches(2), Inches(0.3), size=11, bold=True, color=MUTED)
add_text(s, "Inventory", chart_l + chart_w - Inches(1.2),
         chart_t + chart_h - Inches(0.4),
         Inches(1.5), Inches(0.3), size=11, bold=True, color=MUTED)

# place dots
def dot(x_pct, y_pct, label, color=ACCENT, big=False):
    cx = chart_l + Emu(int(chart_w * x_pct))
    cy = chart_t + Emu(int(chart_h * (1 - y_pct)))
    r = Inches(0.22) if big else Inches(0.14)
    d = s.shapes.add_shape(
        MSO_SHAPE.OVAL, cx - r, cy - r, r * 2, r * 2)
    d.line.fill.background()
    d.fill.solid()
    d.fill.fore_color.rgb = color
    add_text(s, label, cx + r + Inches(0.05), cy - Inches(0.13),
             Inches(2.5), Inches(0.3), size=12,
             bold=big, color=NAVY if big else INK)

dot(0.15, 0.2, "Airbnb")
dot(0.30, 0.30, "Studapart")
dot(0.55, 0.55, "Uniplaces")
dot(0.40, 0.45, "HousingAnywhere")
dot(0.45, 0.60, "Student.com")
dot(0.10, 0.10, "CROUS")
dot(0.20, 0.50, "Local agencies")
dot(0.75, 0.85, "Euronest", color=GOLD, big=True)

# Right column: takeaway
add_text(s, "Our position", Inches(8.7), Inches(2.0),
         Inches(4), Inches(0.5), size=16, bold=True, color=NAVY)
add_rect(s, Inches(8.7), Inches(2.45), Inches(0.5), Inches(0.04), GOLD)
add_text(s,
         "No competitor combines a curated inventory, an in-house "
         "guarantor, and a service bundle around the apartment.\n\n"
         "Pieces of what we offer exist everywhere. Putting them "
         "together is the moat.",
         Inches(8.7), Inches(2.7), Inches(4), Inches(4),
         size=13.5, color=INK, line_spacing=1.4)

footer(s, page)


# =====================================================================
# SLIDE 10 — Business model
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "How we make money", eyebrow="04 · Business model")

# Donut-style breakdown using stacked bars
streams = [
    ("Subscription revenue", "90%", "Monthly or 6-month prepay across all three tiers."),
    ("Landlord commission", "5%", "On listings we route but do not head-lease."),
    ("Service partner share", "3%", "Gyms, ISPs, meal providers."),
    ("Add-ons", "2%", "Airport pickup, SIM card, language coaching."),
]
y = Inches(2.0)
for i, (name, pct, body) in enumerate(streams):
    ly = y + i * Inches(1.05)
    add_rect(s, Inches(0.7), ly, Inches(1.1), Inches(0.85), ACCENT)
    add_text(s, pct, Inches(0.7), ly, Inches(1.1), Inches(0.85),
             size=22, bold=True, color=WHITE,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, name, Inches(2.0), ly + Inches(0.05),
             Inches(5), Inches(0.4), size=15, bold=True, color=NAVY)
    add_text(s, body, Inches(2.0), ly + Inches(0.45),
             Inches(5), Inches(0.5), size=12, color=MUTED)

# Right side: unit economics card
add_rect(s, Inches(8.0), Inches(2.0), Inches(4.7), Inches(4.5), NAVY)
add_text(s, "Unit economics (year 1 blended)", Inches(8.2),
         Inches(2.15), Inches(4.3), Inches(0.5),
         size=14, bold=True, color=GOLD)

ue = [
    ("Avg subscription", "EUR 870"),
    ("Cost of services", "EUR 390"),
    ("Contribution / subscriber", "EUR 480"),
    ("Fixed monthly opex", "EUR 18,500"),
    ("Break-even subscribers", "39"),
]
uy = Inches(2.75)
for k, v in ue:
    add_text(s, k, Inches(8.2), uy, Inches(3), Inches(0.4),
             size=13, color=LIGHT)
    add_text(s, v, Inches(11.2), uy, Inches(1.4), Inches(0.4),
             size=13, bold=True, color=WHITE, align=PP_ALIGN.RIGHT)
    uy += Inches(0.55)

footer(s, page)


# =====================================================================
# SLIDE 11 — Service standards
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "What we promise to the subscriber",
            eyebrow="04 · Service standards")

# Maintenance SLA cards
sla = [
    ("Emergency", "Within 24 hours", "No power, water leak, lock failure.", CORAL),
    ("Urgent", "Within 5 working days", "Broken appliance, heater, prolonged outage.", GOLD),
    ("Non-urgent", "Within 28 days", "Single fitting, sticking door or window.", GREEN),
]
y = Inches(2.0)
w = Inches(4.0)
for i, (name, sla_time, ex, color) in enumerate(sla):
    lx = Inches(0.7) + i * (w + Inches(0.15))
    add_rect(s, lx, y, w, Inches(2.5), WHITE)
    add_rect(s, lx, y, Inches(0.18), Inches(2.5), color)
    add_text(s, name, lx + Inches(0.35), y + Inches(0.15),
             w - Inches(0.5), Inches(0.5), size=18, bold=True, color=NAVY)
    add_text(s, sla_time, lx + Inches(0.35), y + Inches(0.7),
             w - Inches(0.5), Inches(0.5), size=14, bold=True, color=color)
    add_text(s, ex, lx + Inches(0.35), y + Inches(1.3),
             w - Inches(0.6), Inches(1.0), size=12, color=INK,
             line_spacing=1.35)

# bottom: other standards
y2 = Inches(4.8)
add_text(s, "Other standards we publish in every lease", Inches(0.7), y2,
         Inches(11), Inches(0.4), size=14, bold=True, color=NAVY)
add_rect(s, Inches(0.7), y2 + Inches(0.45), Inches(0.5), Inches(0.04), ACCENT)
bullets = [
    "One named, multilingual coordinator from move-in to move-out. "
    "No round-robin call centre.",
    "Quiet hours 22:00 to 07:00. Four-step neighbour-complaint escalation.",
    "Smoke detector tested at move-in and annually. Fire blanket and 2 kg "
    "extinguisher in every kitchen.",
    "Bilingual lease in French and English. Deposit held in escrow.",
]
bullet_box(s, bullets, Inches(0.7), y2 + Inches(0.6),
           Inches(12), Inches(2), size=12)
footer(s, page)


# =====================================================================
# SLIDE 12 — Financial projection
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "Three-year projection", eyebrow="05 · Financials")

# Chart
cd = CategoryChartData()
cd.categories = ["Year 1", "Year 2", "Year 3"]
cd.add_series("Revenue (EUR k)", (540, 1820, 3360))
cd.add_series("Gross margin (EUR k)", (155, 610, 1180))
cd.add_series("EBITDA (EUR k)", (-35, 215, 540))

chart_shape = s.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED,
    Inches(0.7), Inches(2.0), Inches(7.5), Inches(4.6), cd
)
chart = chart_shape.chart
chart.has_title = False
chart.has_legend = True
chart.legend.position = XL_LEGEND_POSITION.BOTTOM
chart.legend.include_in_layout = False

# Colour the series
colors = [NAVY, ACCENT, GOLD]
for i, series in enumerate(chart.plots[0].series):
    fill = series.format.fill
    fill.solid()
    fill.fore_color.rgb = colors[i]
    series.format.line.fill.background()

# right side narrative
add_rect(s, Inches(8.5), Inches(2.0), Inches(4.2), Inches(4.6), NAVY)
add_text(s, "What the numbers say", Inches(8.7), Inches(2.15),
         Inches(4), Inches(0.5), size=14, bold=True, color=GOLD)
add_text(
    s,
    "Year 1 is intentionally loss-making.\n\n"
    "The September intake discount and a full team from month six "
    "push EBITDA negative by EUR 35k.\n\n"
    "The model turns positive between month 13 and 15, depending on "
    "how the June-August occupancy lands.\n\n"
    "By year three: EBITDA EUR 540k on revenue of EUR 3.36m.",
    Inches(8.7), Inches(2.75), Inches(3.9), Inches(3.7),
    size=12.5, color=WHITE, line_spacing=1.35
)
footer(s, page)


# =====================================================================
# SLIDE 13 — The ask
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "EUR 180,000 to launch", eyebrow="05 · The ask")

# Big number block
add_rect(s, Inches(0.7), Inches(2.0), Inches(5.5), Inches(3.5), NAVY)
add_text(s, "EUR 180k", Inches(0.9), Inches(2.3),
         Inches(5.1), Inches(1.6), size=66, bold=True, color=WHITE)
add_text(s, "initial round", Inches(0.9), Inches(4.0),
         Inches(5.1), Inches(0.5), size=18, color=GOLD)
add_text(s,
         "Founders EUR 40k  ·  Bpifrance loan EUR 60k\n"
         "Angel round EUR 80k for 12% equity",
         Inches(0.9), Inches(4.5), Inches(5), Inches(1),
         size=14, color=LIGHT, line_spacing=1.4)

# Use of funds breakdown
y = Inches(2.0)
add_text(s, "Use of funds", Inches(7.0), y, Inches(5), Inches(0.5),
         size=18, bold=True, color=NAVY)
add_rect(s, Inches(7.0), y + Inches(0.6), Inches(0.5), Inches(0.04), ACCENT)

uses = [
    ("Platform and mobile app development", "EUR 35k", 0.35 / 1.8),
    ("Furniture, deposits, setup (first 25 units)", "EUR 55k", 0.55 / 1.8),
    ("Marketing for September 2026 intake", "EUR 25k", 0.25 / 1.8),
    ("Six months of fixed operating costs", "EUR 45k", 0.45 / 1.8),
    ("Working capital reserve", "EUR 20k", 0.20 / 1.8),
]
ry = y + Inches(0.9)
for label, val, pct in uses:
    add_text(s, label, Inches(7.0), ry, Inches(4), Inches(0.35),
             size=12, color=INK)
    add_text(s, val, Inches(10.8), ry, Inches(1.8), Inches(0.35),
             size=12, bold=True, color=NAVY, align=PP_ALIGN.RIGHT)
    add_rect(s, Inches(7.0), ry + Inches(0.35),
             Inches(5.5), Inches(0.06), LIGHT)
    add_rect(s, Inches(7.0), ry + Inches(0.35),
             Inches(5.5 * pct), Inches(0.06), ACCENT)
    ry += Inches(0.6)

footer(s, page)


# =====================================================================
# SLIDE 14 — Team
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "The founders", eyebrow="06 · Team")

team = [
    ("Mansoor Ali", "CEO, partnerships",
     "Hospitality operations; 40-room boutique hotel."),
    ("Fidha Fathima Panankavil", "COO, apartment operations",
     "Real estate analyst; inventory and setup."),
    ("Leo Joy", "CFO",
     "Audit and corporate finance; runs the model and the raise."),
    ("Nithin Stanley George", "CTO, platform",
     "Software engineer; website, app and payments."),
    ("Minhaj Eshwaramangalam", "Head of marketing",
     "Digital marketing; paid social, content, referral programme."),
    ("Gopinath Dasan", "Head of student support",
     "Multilingual customer service; coordinator team lead."),
    ("Pallampettivelayudhan Nithin", "Head of legal & compliance",
     "Law graduate; lease templates, GDPR, regulatory tracking."),
]
# 4 + 3 layout
cols = 4
w = Inches(2.95)
gap = Inches(0.1)
y = Inches(2.0)
for i, (name, role, bg) in enumerate(team):
    row = i // cols
    col = i % cols
    lx = Inches(0.7) + col * (w + gap)
    ly = y + row * (Inches(2.3) + Inches(0.2))
    add_rect(s, lx, ly, w, Inches(2.3), WHITE)
    add_rect(s, lx, ly, w, Inches(0.7), NAVY)
    add_text(s, name, lx + Inches(0.2), ly + Inches(0.07),
             w - Inches(0.3), Inches(0.6), size=12.5, bold=True, color=WHITE,
             line_spacing=1.2)
    add_text(s, role, lx + Inches(0.2), ly + Inches(0.85),
             w - Inches(0.3), Inches(0.4), size=12, bold=True, color=ACCENT)
    add_text(s, bg, lx + Inches(0.2), ly + Inches(1.3),
             w - Inches(0.3), Inches(0.9), size=11, color=INK,
             line_spacing=1.3)

footer(s, page)


# =====================================================================
# SLIDE 15 — Risks
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "Risks we are watching", eyebrow="06 · Risk")

risks = [
    ("Trust gap on a new brand",
     "High",
     "Money-back guarantee on month one. First-cohort discount of 10%. "
     "Verified subscriber reviews from day one."),
    ("Cash gap before break-even",
     "Medium",
     "Six-month prepay pulls forward ~EUR 95k. Pre-agreed EUR 60k bridge "
     "with the angel investor for the worst case."),
    ("Regulation on furnished lets",
     "Low / High impact",
     "Quarterly review with French housing lawyer. FNAIM membership for "
     "early visibility on rule changes."),
    ("Apartment damage or non-payment",
     "Medium",
     "Two-month deposit in escrow. Civil liability insurance bundled "
     "into the standard tier."),
    ("Key founder leaves before year-2",
     "Medium",
     "Four-year vesting with one-year cliff. Two-deep coverage on every "
     "function."),
]
y = Inches(2.0)
for i, (r, lik, mit) in enumerate(risks):
    ly = y + i * Inches(0.95)
    color = CORAL if lik.startswith("High") else (
        GOLD if lik.startswith("Medium") else GREEN)
    add_rect(s, Inches(0.7), ly, Inches(0.18), Inches(0.8), color)
    add_text(s, r, Inches(1.0), ly + Inches(0.05),
             Inches(4.5), Inches(0.5), size=14, bold=True, color=NAVY)
    add_text(s, lik, Inches(5.6), ly + Inches(0.05),
             Inches(1.8), Inches(0.5), size=12, bold=True, color=color)
    add_text(s, mit, Inches(7.5), ly + Inches(0.05),
             Inches(5.2), Inches(0.8), size=11.5, color=INK,
             line_spacing=1.3)

footer(s, page)


# =====================================================================
# SLIDE 16 — Roadmap
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "Where we are heading", eyebrow="06 · Roadmap")

quarters = [
    ("Q2 2026",
     ["Incorporate SAS", "Close initial raise", "Website MVP live"]),
    ("Q3 2026",
     ["25 head-leased apartments", "Sept intake: 20 paid subscribers"]),
    ("Q1 2027",
     ["55 active subscribers", "Mobile app on iOS and Android"]),
    ("Q3 2027",
     ["Lille + Toulouse launch", "AI roommate matching live"]),
    ("Q4 2027",
     ["180 active subscribers", "First EBITDA-positive month"]),
    ("Q4 2028",
     ["320 subscribers", "Marseille launched, Series A opened"]),
]
# Timeline
add_rect(s, Inches(0.7), Inches(3.5), Inches(12), Inches(0.06), ACCENT)
w_each = Inches(2.0)
for i, (q, items) in enumerate(quarters):
    lx = Inches(0.7) + i * (w_each + Inches(0.04))
    # marker
    add_rect(s, lx + w_each / 2 - Inches(0.16),
             Inches(3.5) - Inches(0.14),
             Inches(0.32), Inches(0.32), NAVY, shape=MSO_SHAPE.OVAL)
    add_text(s, q, lx, Inches(2.05), w_each, Inches(0.5),
             size=14, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    add_text(s, q[:7], lx, Inches(2.5), w_each, Inches(0.3),
             size=10, color=MUTED, align=PP_ALIGN.CENTER)
    # items below
    body = "\n".join("·  " + it for it in items)
    add_text(s, body, lx, Inches(3.9), w_each, Inches(2.5),
             size=11.5, color=INK, align=PP_ALIGN.CENTER,
             line_spacing=1.4)

# Bottom callout
add_text(s,
         "Three answers by month 18 decide whether year three is an "
         "expansion year or a consolidation year:",
         Inches(0.7), Inches(6.3), Inches(12), Inches(0.4),
         size=12, italic=True, color=MUTED, align=PP_ALIGN.CENTER)
add_text(s,
         "margin discipline   ·   retention between academic years   "
         "·   marketing efficiency across cities",
         Inches(0.7), Inches(6.65), Inches(12), Inches(0.4),
         size=12, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
footer(s, page)


# =====================================================================
# SLIDE 17 — Why we will win
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s)
header_band(s, "Why we will win", eyebrow="Closing")

reasons = [
    ("We are the customer.",
     "Between the seven of us we have lived this problem. Every "
     "feature in the plan started as something one of us needed when "
     "we landed in France."),
    ("The moat compounds.",
     "Verified inventory, an in-house guarantor and a multilingual "
     "service layer are easy to describe and hard to assemble. Each "
     "year of operation makes the next year cheaper."),
    ("We can stop early if it is not working.",
     "If we are below 120 subscribers and above EUR 280 CAC at "
     "month 18, we shut it down. The product compounds on word of "
     "mouth or it does not."),
]
y = Inches(2.0)
for i, (t, b) in enumerate(reasons):
    ly = y + i * Inches(1.55)
    add_rect(s, Inches(0.7), ly + Inches(0.15),
             Inches(0.5), Inches(0.5), ACCENT)
    add_text(s, str(i + 1), Inches(0.7), ly + Inches(0.15),
             Inches(0.5), Inches(0.5), size=20, bold=True, color=WHITE,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, t, Inches(1.4), ly, Inches(11), Inches(0.6),
             size=22, bold=True, color=NAVY)
    add_text(s, b, Inches(1.4), ly + Inches(0.6),
             Inches(11), Inches(1.0), size=14, color=INK, line_spacing=1.4)

footer(s, page)


# =====================================================================
# SLIDE 18 — Thanks
# =====================================================================
page += 1
s = prs.slides.add_slide(blank)
add_bg(s, NAVY)
add_rect(s, Inches(0), Inches(6.4), prs.slide_width, Inches(1.1), ACCENT)

add_text(s, "Thank you.", Inches(0.9), Inches(2.3),
         Inches(11), Inches(1.6), size=72, bold=True, color=WHITE)
add_rect(s, Inches(0.95), Inches(3.9), Inches(0.8), Inches(0.05), GOLD)
add_text(s, "We would love your questions.",
         Inches(0.9), Inches(4.1), Inches(11), Inches(0.5),
         size=22, color=WHITE, italic=True)
add_text(s, "founders@euronest.eu  ·  ISTEC, Paris",
         Inches(0.9), Inches(5.5), Inches(11), Inches(0.5),
         size=16, color=LIGHT)


# =====================================================================
# SAVE
# =====================================================================
out = "/home/user/first/Euronest_Pitch_Deck.pptx"
prs.save(out)
print(f"Saved: {out}  ({len(prs.slides)} slides)")
