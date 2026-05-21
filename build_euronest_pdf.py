"""Build the Euronest business plan as a PDF using reportlab.

Same content as build_euronest_plan.py but rendered directly to PDF
because LibreOffice writer is not installed in this environment.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, ListFlowable, ListItem,
)
from reportlab.platypus.flowables import HRFlowable

NAVY = HexColor("#102A54")
ACCENT = HexColor("#3E63A6")
LIGHTBG = HexColor("#EEF2F8")
RULE = HexColor("#C9D2E3")

styles = getSampleStyleSheet()

body = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=10.5,
    leading=15,
    alignment=TA_JUSTIFY,
    spaceAfter=8,
    textColor=HexColor("#1c1c1c"),
)

bullet = ParagraphStyle(
    "Bullet",
    parent=body,
    leftIndent=14,
    bulletIndent=2,
    spaceAfter=4,
)

h1 = ParagraphStyle(
    "H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=20, leading=24, textColor=NAVY, spaceBefore=4, spaceAfter=10,
)
h2 = ParagraphStyle(
    "H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=14, leading=18, textColor=NAVY, spaceBefore=10, spaceAfter=6,
)
h3 = ParagraphStyle(
    "H3", parent=styles["Heading3"], fontName="Helvetica-Bold",
    fontSize=11.5, leading=15, textColor=ACCENT, spaceBefore=6, spaceAfter=4,
)

cover_title_style = ParagraphStyle(
    "CT", parent=body, fontName="Helvetica-Bold", fontSize=42,
    leading=48, textColor=NAVY, alignment=TA_CENTER, spaceAfter=10,
)
cover_sub_style = ParagraphStyle(
    "CS", parent=body, fontName="Helvetica-Oblique", fontSize=16,
    leading=22, textColor=HexColor("#444"), alignment=TA_CENTER, spaceAfter=24,
)
cover_label_style = ParagraphStyle(
    "CL", parent=body, fontName="Helvetica-Bold", fontSize=18,
    leading=22, textColor=NAVY, alignment=TA_CENTER, spaceAfter=8,
)
cover_meta_style = ParagraphStyle(
    "CM", parent=body, fontName="Helvetica", fontSize=11,
    leading=16, textColor=HexColor("#333"), alignment=TA_CENTER,
)

italic = ParagraphStyle("I", parent=body, fontName="Helvetica-Oblique")

story = []


def P(text, st=body):
    story.append(Paragraph(text, st))


def H1(text):
    story.append(Paragraph(text, h1))
    story.append(HRFlowable(width="100%", thickness=0.7, color=RULE,
                            spaceBefore=0, spaceAfter=8))


def H2(text):
    story.append(Paragraph(text, h2))


def H3(text):
    story.append(Paragraph(text, h3))


def BULLETS(items):
    flow = ListFlowable(
        [ListItem(Paragraph(t, body), leftIndent=10) for t in items],
        bulletType="bullet", start="circle", leftIndent=18,
    )
    story.append(flow)
    story.append(Spacer(1, 4))


def NUMS(items):
    flow = ListFlowable(
        [ListItem(Paragraph(t, body), leftIndent=10) for t in items],
        bulletType="1", leftIndent=20,
    )
    story.append(flow)
    story.append(Spacer(1, 4))


def TBL(headers, rows, col_widths=None):
    data = [[Paragraph(f"<b>{h}</b>", body) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), body) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.3, RULE),
        ("BOX", (0, 0), (-1, -1), 0.6, NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHTBG]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    # Override header text colour after Paragraph render
    story.append(t)
    story.append(Spacer(1, 6))


def PBR():
    story.append(PageBreak())


# Fix: header cells need white text in the Paragraph, not the table style
def TBL2(headers, rows, col_widths=None):
    header_style = ParagraphStyle(
        "Hdr", parent=body, textColor=white, fontName="Helvetica-Bold",
        fontSize=10.5, leading=14,
    )
    data = [[Paragraph(str(h), header_style) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c).replace("\n", "<br/>"), body) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.3, RULE),
        ("BOX", (0, 0), (-1, -1), 0.6, NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHTBG]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))


# =====================================================================
# COVER PAGE
# =====================================================================
story.append(Spacer(1, 4 * cm))
P("EURONEST", cover_title_style)
P("Student Housing &amp; Lifestyle Subscription Service", cover_sub_style)
story.append(HRFlowable(width="50%", thickness=1.2, color=NAVY,
                        spaceBefore=10, spaceAfter=20, hAlign="CENTER"))
P("Business Plan", cover_label_style)
story.append(Spacer(1, 3 * cm))
P("Prepared by the founding team", cover_meta_style)
P("ISTEC, Paris &middot; April 2026", cover_meta_style)
story.append(Spacer(1, 1.4 * cm))
P("Mansoor Ali &middot; Fidha Fathima Panankavil &middot; Leo Joy",
  cover_meta_style)
P("Nithin Stanley George &middot; Minhaj Eswaramangalam",
  cover_meta_style)
P("Gopinath Dasan &middot; Nithin Pallampetti Velayudhan", cover_meta_style)
story.append(Spacer(1, 1.4 * cm))
P("<i>Contact: founders@euronest.eu</i>", cover_meta_style)
PBR()

# =====================================================================
# CONTENTS
# =====================================================================
H1("Contents")
toc = [
    ("1.", "Cover page and contents", "1"),
    ("2.", "Executive summary", "3"),
    ("3.", "Problem analysis and value proposition", "4"),
    ("4.", "Market research and strategy", "6"),
    ("5.", "Business model (incl. service standards)", "10"),
    ("6.", "Human resources, risks and mitigation", "14"),
    ("7.", "Financial forecasts", "16"),
    ("8.", "Legal and organisational structure", "18"),
    ("9.", "Roadmap", "20"),
    ("10.", "Appendix (glossary, sources, community,"
            " sustainability, waste, fire safety)", "21"),
]
TBL2(["#", "Section", "Page"], toc, col_widths=[1.5 * cm, 12 * cm, 2 * cm])
P(
    "<i>This document describes how Euronest will operate in France during "
    "its first three years: who it is for, what it costs to run, and how "
    "the founding team plans to reach break-even.</i>"
)
PBR()

# =====================================================================
# 2. EXECUTIVE SUMMARY
# =====================================================================
H1("2. Executive summary")
P(
    "Euronest is a student housing and lifestyle subscription platform for "
    "international students arriving in France. We verify the apartment "
    "before the student lands, bundle the essentials (rent, internet, gym, "
    "streaming and optional meal plans) into a single monthly payment, and "
    "give every subscriber one point of contact, in their own language, "
    "for the first six months of their stay."
)
P(
    "The idea came out of our own arrival experience. Between the seven of "
    "us we lost deposits on fake listings, spent weeks chasing a French "
    "guarantor, and moved twice before settling in. Talking to other "
    "international students at ISTEC made it clear this was not bad luck. "
    "It was the default."
)
H2("What we are building")
P(
    "A website and mobile app where a student can pick a verified apartment "
    "in Paris, Lyon, Lille, Toulouse or Marseille, choose a service tier, "
    "and pay either monthly or as a single six-month upfront amount. The "
    "tier decides what is bundled in: basic gives you the apartment and "
    "internet; standard adds gym and streaming; premium adds meal plans, "
    "visa paperwork support, and one return-home flight credit for the "
    "academic year."
)
H2("Who it is for")
P(
    "Our first customer is the non-EU master's student who is moving to "
    "France for the first time, has limited French, and whose parents are "
    "paying the deposit. We also serve Erasmus students on shorter stays, "
    "interns on six-month contracts, and young professionals who want a "
    "ready apartment without the usual paperwork."
)
H2("Why this works financially")
P(
    "A pilot cohort of twenty students on the standard tier already covers "
    "most fixed costs. Break-even sits between 35 and 45 subscribers "
    "depending on the city mix. Above that, every premium subscription is "
    "high margin because the underlying services (gym, streaming, food) "
    "are bought on volume contracts. The plan in this document gets us "
    "from twenty students in year one to roughly 320 by the end of year "
    "three."
)
H2("What we need")
P(
    "An initial investment of EUR 180,000 to cover platform development, "
    "the first batch of furnished apartments, marketing for the September "
    "intake, and six months of operating costs. Half of that is going into "
    "deposits and furniture which we recover when leases turn over. The "
    "remainder funds the team and the app."
)
PBR()

# =====================================================================
# 3. PROBLEM ANALYSIS AND VALUE PROPOSITION
# =====================================================================
H1("3. Problem analysis and value proposition")
H2("3.1 The problem")
P(
    "Finding housing in France as an international student is harder than "
    "it should be. The friction is not in the listings. There are plenty "
    "of listings. The friction is in everything that surrounds them."
)
P(
    "We interviewed 42 international students at ISTEC and three other "
    "Paris schools between January and March 2026. The patterns were "
    "consistent enough to summarise:"
)
BULLETS([
    "Fake or misleading listings. Roughly one in three students we spoke "
    "to had sent money to a landlord who either did not own the apartment "
    "or had already let it to someone else.",
    "The guarantor wall. French landlords typically demand a French "
    "guarantor earning three times the rent. Students arriving without "
    "family in France either pay six months upfront or get rejected.",
    "Language. Lease contracts run twelve to twenty pages in French legal "
    "vocabulary. Most students sign without fully understanding the "
    "early-exit clauses or the deposit conditions.",
    "Fragmented setup. Internet, electricity, home insurance, gym, food "
    "and transit each require a separate sign-up with different paperwork "
    "and different cancellation rules.",
    "No safety net. When something goes wrong (broken boiler, missing "
    "deposit, dispute with the landlord) the student has no one to call "
    "who is on their side and speaks their language.",
])
H2("3.2 Why now")
P(
    "France hosted around 430,000 international students in the 2024-2025 "
    "academic year, with a stated government target of 500,000 by 2027. "
    "Most of that growth is coming from outside the EU, which is exactly "
    "the cohort that struggles most with the guarantor and language "
    "issues above. At the same time, students arriving in 2026 are the "
    "first cohort who grew up booking everything (flights, food, rides) "
    "through an app. They expect housing to work the same way. It does "
    "not."
)
P(
    "Parents are also part of this. The students we interviewed who paid "
    "six months upfront were almost always doing it because their family "
    "wanted certainty. A platform that gives parents a verified booking "
    "and a contract they can read is worth a measurable premium."
)
H2("3.3 Our value proposition")
P("Euronest gives a student three things that are missing from the current market:")
NUMS([
    "A verified apartment. Every property is visited by a team member or "
    "a vetted local partner before it is listed. We refuse roughly a "
    "third of the apartments offered to us.",
    "A single price. Rent, utilities, internet and the chosen lifestyle "
    "services come in one monthly invoice. No separate bills, no surprise "
    "deposits, no guarantor required for the standard and premium tiers "
    "because Euronest itself acts as the guarantor.",
    "One human contact. Each subscriber gets a named coordinator who "
    "speaks at least English plus one of French, Hindi, Arabic or "
    "Mandarin. They handle paperwork in the first month and stay "
    "reachable for the rest of the stay.",
])
H2("3.4 What makes the offer hard to copy")
P(
    "Airbnb has scale but treats students like any other short-stay guest. "
    "The big French agencies (Studapart, Lokaviz, ImmoJeune) publish "
    "listings but stop at the booking. Local agencies handle paperwork "
    "but charge agency fees that match or exceed our monthly premium, and "
    "they do not bundle anything beyond the apartment itself."
)
P(
    "What is hard to copy is the combination: a curated inventory, a "
    "guarantor function backed by our own balance sheet, and a service "
    "layer that only makes sense if you are willing to specialise in "
    "students. We are, because that is the only market we want."
)
PBR()

# =====================================================================
# 4. MARKET RESEARCH AND STRATEGY
# =====================================================================
H1("4. Market research and strategy")
H2("4.1 Market size and target cities")
P(
    "We are starting in five cities that together host more than 60% of "
    "international students in France. The order below also reflects the "
    "order we plan to enter them."
)
TBL2(
    ["City", "Intl. students (est.)", "Avg. monthly rent (studio)", "Priority"],
    [
        ["Paris", "115,000", "EUR 950", "Year 1 launch"],
        ["Lyon", "32,000", "EUR 620", "Year 1 launch"],
        ["Lille", "21,000", "EUR 540", "Year 2"],
        ["Toulouse", "19,000", "EUR 560", "Year 2"],
        ["Marseille", "17,000", "EUR 600", "Year 3"],
    ],
    col_widths=[3 * cm, 4 * cm, 5 * cm, 4 * cm],
)
P(
    "Rents in the table are city averages for an unfurnished studio. Our "
    "furnished, all-inclusive price will sit above the headline average "
    "but below what students currently pay once you add furniture, "
    "internet, gym and insurance separately."
)
P(
    "Two structural facts about the French student housing market frame "
    "everything else in this plan. First, the public operator CROUS "
    "(Centre Regional des Oeuvres Universitaires et Scolaires) manages "
    "roughly 175,000 publicly owned rooms across France, but waiting "
    "lists are long and allocation favours French and EU students on "
    "scholarship. Second, the privately operated stock is fragmented "
    "across small landlords. Of an estimated 350,000 rooms in the "
    "broader French student market, fewer than 15% are professionally "
    "managed. That gap, between public scarcity and private fragmentation, "
    "is where Euronest sits."
)
H2("4.2 Customer segments")
BULLETS([
    "Non-EU master's students. Our primary segment. High willingness to "
    "pay for certainty, parents involved in the decision, average stay of "
    "16 to 24 months.",
    "Erasmus students. Shorter stays of 5 to 10 months, lower price "
    "tolerance, but they bring strong word of mouth across European "
    "universities.",
    "Interns on six-month contracts. The cleanest fit for our six-month "
    "prepay product. Often arriving for a fixed start date.",
    "Young professionals new to France. Smaller volume, higher price "
    "tolerance, useful for filling apartments in the summer gap.",
])
H2("4.3 Competitor map")
TBL2(
    ["Competitor", "Inventory", "Service depth", "Price vs Euronest"],
    [
        ["Airbnb", "Very large", "None (listings only)", "Higher per night, no contract"],
        ["Studapart", "Large", "Booking only", "Similar rent, fewer extras"],
        ["Uniplaces", "Pan-European", "Booking + verified listings",
         "Similar headline rent, no service bundle"],
        ["HousingAnywhere", "Pan-European, peer-to-peer",
         "Free for both sides, paid premium add-ons",
         "Lower, but no guarantor and no support"],
        ["Student.com", "Global, mostly PBSA partners",
         "Booking + concierge for international students",
         "Variable, depends on partner property"],
        ["Lokaviz / ImmoJeune", "Medium", "Listings + filters", "Lower, but DIY"],
        ["Local rental agencies", "Medium", "Paperwork", "Higher once fees are added"],
        ["CROUS residences", "~175,000 rooms nationally",
         "Basic public housing", "Lower, but allocation favours French / EU"],
    ],
    col_widths=[4.2 * cm, 3.8 * cm, 4.5 * cm, 4 * cm],
)
P(
    "The honest read on this table: nobody is doing what we want to do, "
    "but pieces of it exist everywhere. Our risk is not that a competitor "
    "blocks us. It is that students do not yet trust a new brand enough "
    "to prepay six months. We address that in Section 6 under risk."
)
H2("4.4 Commercial strategy")
P(
    "Positioning. We are not the cheapest housing site and we will not "
    "pretend to be. We are the safest one for a student who has never "
    "lived in France. Every piece of marketing copy is written to that "
    "person."
)
P(
    "Pricing. Three tiers (basic, standard, premium) covered in detail in "
    "Section 5. A six-month prepay option carries a 5% discount and "
    "doubles as our cash-flow buffer for the first year."
)
P(
    "Channels. Year one is mostly digital and word of mouth: Instagram "
    "and TikTok content in English with local-language subtitles, a "
    "referral programme that pays the referring student EUR 80 per "
    "completed booking, and partnerships with five Paris schools where "
    "we already have student contacts. YouTube long-form (city guides, "
    "lease explainers) is the slow-burn channel that should mature by "
    "year two."
)
P(
    "Customer experience. Easy booking is the table-stakes claim. What "
    "we are actually building is the boring part: a clear lease in two "
    "languages, a deposit held in escrow, a 48-hour move-in checklist, "
    "and one named coordinator the student can reach on WhatsApp."
)

H3("Year 1 marketing budget")
TBL2(
    ["Channel", "Spend (EUR)", "What we are paying for"],
    [
        ["Instagram and TikTok ads", "12,000",
         "Targeted at students in India, Morocco, Senegal, Vietnam, Brazil "
         "two to four months before the September intake."],
        ["YouTube content production", "6,000",
         "Eight long-form videos: city guides, lease walkthroughs, FAQ in "
         "English, French and Hindi."],
        ["Referral payouts", "9,000",
         "EUR 80 per completed booking. Funded only when revenue is "
         "received."],
        ["Campus partnerships", "5,000",
         "Stand at student associations, welcome events, leaflet print "
         "runs at five Paris schools."],
        ["Influencer collaborations", "7,000",
         "Three micro-influencers per target country, fee plus one free "
         "month of standard tier."],
        ["SEO and content writing", "3,000",
         "Articles aimed at the long tail (CAF, visa, social security "
         "registration)."],
        ["<b>Total</b>", "<b>42,000</b>", ""],
    ],
    col_widths=[4.5 * cm, 3 * cm, 9 * cm],
)

H3("Customer journey")
P(
    "We map our subscriber across five stages. The point of the map is "
    "to make sure no stage is left to luck."
)
NUMS([
    "Discover. Student sees a TikTok or hears from a friend. They land "
    "on the website, watch a 90-second explainer, and read three real "
    "subscriber stories.",
    "Compare. They put Euronest next to two or three alternatives. We "
    "win or lose on the bundled price and on the guarantor question.",
    "Book. They pick a city, a tier and a move-in date. The lease is "
    "signed digitally in two languages. Deposit and first month (or "
    "six-month prepay) are paid into escrow.",
    "Arrive. A coordinator meets the student at the apartment, walks "
    "through the inventory, sets up internet credentials, and answers "
    "the first wave of paperwork questions.",
    "Live and renew. The student stays in WhatsApp contact with their "
    "coordinator. Two months before the lease ends we offer a renewal, "
    "a swap to a different city, or a roommate match for the next year.",
])
PBR()

H2("4.5 SWOT analysis")
TBL2(
    ["Strengths", "Weaknesses"],
    [[
        "Niche focus on international students.<br/>"
        "Bundled offer is hard to assemble piecemeal.<br/>"
        "Recurring annual demand from each university intake.<br/>"
        "Multilingual team with first-hand experience of the problem.",
        "New brand with no trust history.<br/>"
        "Capital-intensive: deposits and furniture tie up cash.<br/>"
        "Small inventory in year one limits choice for students.<br/>"
        "Founder team is full-time studying for the first six months."
    ]],
    col_widths=[8 * cm, 8 * cm],
)
TBL2(
    ["Opportunities", "Threats"],
    [[
        "French target of 500,000 international students by 2027.<br/>"
        "Expansion via Erasmus network into Spain, Italy, Germany.<br/>"
        "Landlords who want stable tenants and one professional counterparty.<br/>"
        "AI roommate matching as a low-cost differentiator.",
        "Regulation on short-term lets and sub-letting.<br/>"
        "Seasonal demand: a quiet July and August reduce occupancy.<br/>"
        "Currency risk for students paying from outside the eurozone.<br/>"
        "A large player (Airbnb, Booking) copying the bundle."
    ]],
    col_widths=[8 * cm, 8 * cm],
)
H2("4.6 PESTEL summary")
BULLETS([
    "Political. France actively recruits international students. Visa "
    "policy is the main variable to watch; a tightening would hit us "
    "directly.",
    "Economic. Inflation in rents has slowed since 2024 but utility "
    "costs remain volatile. We protect our margin by indexing the "
    "premium tier to a published utility index, reviewed every six "
    "months.",
    "Social. Students are used to subscription models for everything "
    "else in their life. Selling housing as a subscription is more "
    "familiar to them than to their parents.",
    "Technological. Booking, payments and roommate matching are "
    "off-the-shelf problems. Our differentiation is in the curation and "
    "the service, not the code.",
    "Environmental. Furnished apartments give us control over energy "
    "ratings. We will only sign with properties at DPE class D or "
    "better, which also reduces utility bills.",
    "Legal. The Alur law and the loi ELAN govern most of what we do. We "
    "have engaged a French housing lawyer for the contract templates "
    "(see Section 8).",
])
PBR()

# =====================================================================
# 5. BUSINESS MODEL
# =====================================================================
H1("5. Business model")
H2("5.1 Value created and for whom")
P(
    "We create value on three sides. Students get a verified place to "
    "live and a single bill. Landlords get a professional tenant, on-time "
    "payments, and no vacancy management. Service partners (gyms, ISPs, "
    "meal providers, insurers) get a steady, pre-segmented stream of "
    "subscribers with negligible churn during the academic year."
)
H2("5.2 Customer segments")
P(
    "Already covered in Section 4.2. The mix we plan for in year one is "
    "roughly 60% master's students, 25% Erasmus and interns, 15% young "
    "professionals."
)
H2("5.3 The offer (tiers)")
TBL2(
    ["Tier", "Monthly price", "What is included", "Best for"],
    [
        ["Basic", "EUR 690",
         "Furnished apartment, fibre internet, utilities, contents insurance.",
         "Short stays, budget-sensitive Erasmus students."],
        ["Standard", "EUR 890",
         "Everything in Basic + gym pass, Netflix or Amazon Prime, Euronest acts as guarantor.",
         "Master's students for a full academic year."],
        ["Premium", "EUR 1,190",
         "Everything in Standard + meal plan (15 meals/week), visa &amp; paperwork support, "
         "swimming pool / sports turf access, one annual return-home flight credit "
         "(capped at EUR 450).",
         "Students whose families want the full setup."],
    ],
    col_widths=[2.5 * cm, 2.5 * cm, 7.5 * cm, 4 * cm],
)
P(
    "Prices above are Paris pricing. Lyon and the other cities are 15 to "
    "25% lower because the underlying rent is lower. The six-month "
    "prepay option carries a 5% discount on top of these prices."
)
H2("5.4 Revenue streams")
BULLETS([
    "Subscription revenue (about 90% of total). Monthly or six-month prepay.",
    "Landlord commission. On apartments we list but do not head-lease "
    "ourselves, we take a 6% commission on the first month of rent.",
    "Service partner share. Gyms, ISPs and meal providers pay us a "
    "fixed margin on each subscriber we route to them.",
    "Gift vouchers and family top-ups. Parents buy credit that students "
    "spend inside the platform.",
    "Optional add-ons. Airport pickup, French SIM card, additional "
    "language coaching. Small in revenue, high in customer satisfaction.",
])
H2("5.5 Cost structure")
TBL2(
    ["Cost item", "Type", "Year 1 estimate (EUR)"],
    [
        ["Apartment rent paid to landlords", "Variable", "240,000"],
        ["Furniture and setup (recoverable)", "One-off", "55,000"],
        ["Platform and mobile app development", "One-off", "35,000"],
        ["Staff salaries (4 FTE by month 6)", "Fixed", "110,000"],
        ["Cleaning and maintenance", "Variable", "18,000"],
        ["Marketing and advertising", "Variable", "42,000"],
        ["Office rent and utilities", "Fixed", "9,000"],
        ["Insurance, legal, accounting", "Fixed", "14,000"],
        ["Bank fees and payment processing", "Variable", "6,000"],
        ["<b>Total year 1</b>", "", "<b>529,000</b>"],
    ],
    col_widths=[8 * cm, 3.5 * cm, 5 * cm],
)
P(
    "The largest line is rent we pay to landlords, which is matched by "
    "the rent we collect from subscribers. The number that actually needs "
    "to come from investment is the gap between cumulative costs and "
    "cumulative revenue during the first nine months. We size that gap "
    "at around EUR 180,000 in Section 7."
)
H2("5.6 Key activities")
BULLETS([
    "Sourcing and verifying apartments.",
    "Furnishing and setting up each unit before the academic year.",
    "Onboarding students, including paperwork and arrival logistics.",
    "Running the website, app and payment infrastructure.",
    "Managing service partners and renewing volume contracts.",
])
H2("5.7 Key resources")
BULLETS([
    "Verified apartment inventory (the moat that compounds over years).",
    "Brand and reputation among university communities.",
    "The platform itself: bookings, payments, escrow, roommate matching.",
    "Working capital to pre-pay landlord deposits.",
    "The founding team's network across student associations.",
])
H2("5.8 Key partners")
BULLETS([
    "Landlords and small property managers in our five target cities.",
    "ISPs (Orange, Free, SFR) for the internet bundle.",
    "Gym chains (Basic-Fit, Fitness Park, On Air Fitness) for the "
    "lifestyle bundle.",
    "Insurers for contents and civil liability cover.",
    "Banks for student-friendly account opening (Boursorama, Revolut, "
    "BNP Paribas).",
    "Universities and student associations for distribution.",
])
H2("5.9 Operational workflow")
NUMS([
    "Sourcing. The operations lead and one apartment scout visit each "
    "candidate unit, check it against a 38-point checklist, and "
    "negotiate a 12 to 24 month head-lease with the landlord.",
    "Setup. The apartment is furnished from a standard catalogue (bed, "
    "desk, chair, kitchenware) and fitted with fibre internet within "
    "two weeks of signing.",
    "Listing. Photos, floor plan and a short walk-through video go on "
    "the website and the app. Pricing follows the tier table in 5.3.",
    "Booking. The student selects a tier, signs the bilingual lease, "
    "and pays either the first month plus deposit or the six-month "
    "upfront amount.",
    "Move-in. The coordinator meets the student at the apartment, "
    "hands over keys, walks through the inventory, and registers the "
    "student with the local utilities where required.",
    "Support. Coordinator stays on WhatsApp for the duration of the "
    "stay. Maintenance issues are routed to vetted local handymen with "
    "a 48-hour response target.",
])

H2("5.10 Service standards")
P(
    "We publish the standards below in every lease. Students know what "
    "to expect; coordinators know what they are accountable for."
)

H3("Maintenance response")
TBL2(
    ["Priority", "Response", "Examples"],
    [
        ["Emergency", "Within 24 hours",
         "No power, water leak, lock failure, anything that affects "
         "safety or makes the unit unliveable."],
        ["Urgent", "Within 5 working days",
         "Broken appliance, faulty heater, internet outage longer than "
         "48 hours."],
        ["Non-urgent", "Within 28 days",
         "Single light fitting, sticking door or window, minor cosmetic "
         "repair."],
    ],
    col_widths=[3.2 * cm, 3.5 * cm, 9.3 * cm],
)

H3("Reception and on-call coverage")
BULLETS([
    "Coordinator availability on WhatsApp: Monday to Friday 09:00 to "
    "20:00, Saturday 10:00 to 17:00, with extended hours during the "
    "September and January intake weeks.",
    "Out-of-hours emergency line answered by a duty coordinator. "
    "Routed to the on-call manager if unanswered after five minutes.",
    "Each subscriber has a single named coordinator. We refuse the "
    "round-robin call centre pattern. The same person who onboards the "
    "student handles their tenancy until move-out.",
])

H3("Housekeeping and common areas")
P(
    "In a shared apartment, the residents clean their own kitchen, "
    "bathroom and bedrooms. Anything we manage (shared entrance, "
    "building-level laundry, our coordinator office) follows this "
    "schedule:"
)
TBL2(
    ["Area", "Frequency", "Owner"],
    [
        ["Building entrance and stairwell", "Weekly", "Building syndic"],
        ["Shared laundry room", "Twice weekly", "Euronest contractor"],
        ["Apartment deep-clean between tenants", "Once per turnover",
         "Specialist cleaning contractor"],
        ["Window cleaning", "Annual (June)", "Specialist contractor"],
    ],
    col_widths=[6 * cm, 4 * cm, 6 * cm],
)

H3("Quiet hours and neighbourhood relations")
P(
    "Quiet hours are 22:00 to 07:00 every night. Subscribers sign up to "
    "this in the lease. The first complaint from a neighbour is a "
    "conversation; the second is a written warning; the third is a "
    "EUR 100 charge against the deposit; the fourth ends the lease. "
    "We tell students this on day one so nobody is surprised."
)
PBR()

# =====================================================================
# 6. HUMAN RESOURCES, RISKS AND MITIGATION
# =====================================================================
H1("6. Human resources, risks and mitigation")
H2("6.1 The founding team")
P(
    "We are seven MBA students at ISTEC. None of us has run a housing "
    "business before, but between us we have worked in software, finance, "
    "marketing and hospitality, and we have all been on the wrong side "
    "of the problem we are now trying to solve."
)
TBL2(
    ["Member", "Role in Euronest", "Background"],
    [
        ["Mansoor Ali", "CEO, partnerships",
         "Hospitality operations; led a 40-room boutique hotel before MBA."],
        ["Fidha Fathima Panankavil", "COO, apartment operations",
         "Real estate analyst; handles inventory, setup, maintenance."],
        ["Leo Joy", "CFO",
         "Audit and corporate finance; runs the financial model and fundraising."],
        ["Nithin Stanley George", "CTO, platform",
         "Software engineer; owns the website, app and payments."],
        ["Minhaj Eswaramangalam", "Head of marketing",
         "Digital marketing; runs paid social, content and the referral programme."],
        ["Gopinath Dasan", "Head of student support",
         "Multilingual customer service background; coordinator team lead."],
        ["Nithin Pallampetti Velayudhan", "Head of legal &amp; compliance",
         "Law graduate; manages lease templates, GDPR, regulatory tracking."],
    ],
    col_widths=[4.5 * cm, 4 * cm, 8 * cm],
)
H2("6.2 Hiring plan")
P(
    "We stay at seven founders through the pilot. Once we cross 60 paid "
    "subscribers we add three roles: two student coordinators (one for "
    "Paris, one for Lyon) and one apartment scout. By the end of year "
    "two we expect twelve people on payroll. Salaries are modelled "
    "against the French market median for each role with a 10% discount "
    "compensated by equity for the first four hires."
)
H2("6.3 Culture and how we work")
P(
    "We are remote-first with a shared office at ISTEC for two days a "
    "week. Operations meet daily for 15 minutes. Everyone, including the "
    "engineers, spends at least one day a month visiting apartments or "
    "meeting students. This is a deliberate rule. The moment a Euronest "
    "employee stops talking to the customer is the moment we lose what "
    "made the product different in the first place."
)
H2("6.4 Risks")
P("Listing them honestly. No risk register is complete, but these are the ones we think about most.")
TBL2(
    ["Risk", "Likelihood", "Impact", "Mitigation"],
    [
        ["Low trust in a new brand slows year-1 sign-ups",
         "High", "High",
         "Money-back guarantee on the first month. Verified reviews. First-cohort discount of 10% for the September 2026 intake."],
        ["Landlord pulls a property mid-lease",
         "Medium", "Medium",
         "12-month head-leases with break clauses on our side only. Backup inventory of 10% spare units per city."],
        ["Regulatory change on furnished rentals",
         "Low", "High",
         "Quarterly review with French housing lawyer. Lobby through FNAIM membership."],
        ["Cash gap before break-even",
         "Medium", "High",
         "Six-month prepay option creates working capital. Reserve of EUR 40k held back from initial raise."],
        ["Key founder leaves before year-2",
         "Medium", "Medium",
         "Vesting on four-year schedule. Two-deep coverage for every function."],
        ["Apartment damage or non-payment by subscriber",
         "Medium", "Low to medium",
         "Two-month deposit held in escrow. Civil liability insurance bundled into the standard tier."],
        ["Currency volatility for non-EU parents paying in advance",
         "Low", "Medium",
         "Lock-in exchange rate via Wise Business at the time of booking."],
    ],
    col_widths=[5 * cm, 2 * cm, 2 * cm, 7.5 * cm],
)
H2("6.5 What would make us shut this down")
P(
    "If, by the end of month 18, we have fewer than 120 active subscribers "
    "and a customer acquisition cost above EUR 280, we stop. The platform "
    "either compounds on word of mouth or it does not, and pouring more "
    "marketing into a product students do not recommend would be the "
    "wrong call."
)
PBR()

# =====================================================================
# 7. FINANCIAL FORECASTS
# =====================================================================
H1("7. Financial forecasts")
H2("7.1 Initial investment")
TBL2(
    ["Use of funds", "Amount (EUR)"],
    [
        ["Platform and mobile app development", "35,000"],
        ["Furniture, deposits and setup for first 25 apartments", "55,000"],
        ["Marketing for September 2026 intake", "25,000"],
        ["Six months of fixed operating costs", "45,000"],
        ["Working capital reserve", "20,000"],
        ["<b>Total</b>", "<b>180,000</b>"],
    ],
    col_widths=[11 * cm, 5 * cm],
)
P(
    "We are raising the EUR 180,000 as a mix of founder contribution "
    "(EUR 40k), a Bpifrance student entrepreneur loan (EUR 60k applied "
    "for in March 2026) and an equity round from one French business "
    "angel network for the balance (EUR 80k for 12% equity)."
)
H2("7.2 Three-year projection")
TBL2(
    ["", "Year 1", "Year 2", "Year 3"],
    [
        ["Subscribers (avg.)", "55", "180", "320"],
        ["Mix (basic / std / prem)", "35/45/20%", "25/55/20%", "20/55/25%"],
        ["Revenue (EUR)", "540,000", "1,820,000", "3,360,000"],
        ["Cost of services (rent + bundles)", "385,000", "1,210,000", "2,180,000"],
        ["Gross margin (EUR)", "155,000", "610,000", "1,180,000"],
        ["Gross margin %", "29%", "34%", "35%"],
        ["Operating costs (team + ops)", "190,000", "395,000", "640,000"],
        ["EBITDA (EUR)", "-35,000", "215,000", "540,000"],
        ["EBITDA %", "-6%", "12%", "16%"],
    ],
    col_widths=[6.5 * cm, 3 * cm, 3 * cm, 3.5 * cm],
)
P(
    "Year 1 is intentionally loss-making. We are buying the first cohort "
    "with the September intake discount and we are paying a full team "
    "from month six. The model turns positive between month 13 and "
    "month 15 depending on how the June-August occupancy lands."
)
H2("7.3 Break-even analysis")
P(
    "Fixed monthly costs after the team is fully hired sit at around "
    "EUR 18,500 (salaries, office, software, accounting, marketing "
    "baseline). Average contribution per subscriber is EUR 480 per "
    "month at the year-1 tier mix. That puts break-even at 39 "
    "subscribers, which matches the 35 to 45 range we worked through "
    "in the financial overview meeting."
)
H2("7.4 Cash flow")
P(
    "The six-month prepay option is doing real work on the cash flow "
    "side. Even if only a quarter of standard and premium subscribers "
    "take it, that pulls forward roughly EUR 95,000 of cash in the "
    "first quarter of operation. That is the same money that would "
    "otherwise need to come from a larger raise."
)
P(
    "We model a worst-case scenario where uptake is 40% slower than "
    "planned. In that case the company still survives year one but "
    "needs an additional EUR 60,000 bridge in month 9. We have "
    "pre-agreed this bridge in principle with the angel investor."
)
H2("7.5 Sensitivities")
BULLETS([
    "If average rent paid to landlords rises by 8%, EBITDA in year 2 "
    "drops from EUR 215,000 to around EUR 130,000. Mitigation: longer "
    "head-leases with fixed rent.",
    "If gym partners pull their volume discount, the standard tier "
    "loses EUR 22 per subscriber per month. We have a backup partner "
    "agreement with On Air Fitness signed in February 2026.",
    "If churn between semesters rises from 12% to 25%, year-3 revenue "
    "drops by roughly EUR 480,000. Mitigation: annual prepay incentive "
    "and end-of-semester roommate matching for the next cohort.",
])
PBR()

# =====================================================================
# 8. LEGAL AND ORGANISATIONAL STRUCTURE
# =====================================================================
H1("8. Legal and organisational structure")
H2("8.1 Legal form")
P(
    "Euronest will be registered as a SAS (Societe par Actions Simplifiee) "
    "under French law. We picked SAS over SARL for three reasons: "
    "flexibility in shareholder agreements, easier issuance of founder "
    "shares and BSPCE (employee equity), and the option to bring in a "
    "venture investor later without restructuring."
)
H2("8.2 Shareholding at incorporation")
TBL2(
    ["Shareholder", "Shares", "Percentage"],
    [
        ["Mansoor Ali", "13,000", "13.0%"],
        ["Fidha Fathima Panankavil", "13,000", "13.0%"],
        ["Leo Joy", "13,000", "13.0%"],
        ["Nithin Stanley George", "13,000", "13.0%"],
        ["Minhaj Eswaramangalam", "13,000", "13.0%"],
        ["Gopinath Dasan", "13,000", "13.0%"],
        ["Nithin Pallampetti Velayudhan", "10,000", "10.0%"],
        ["Angel investor (post-seed)", "12,000", "12.0%"],
        ["<b>Total</b>", "<b>100,000</b>", "<b>100%</b>"],
    ],
    col_widths=[8 * cm, 4 * cm, 4 * cm],
)
P(
    "All founder shares vest over four years with a one-year cliff. The "
    "angel investor's stake is post-seed and reflects the EUR 80,000 "
    "investment described in Section 7."
)
H2("8.3 Governance")
P(
    "A president (Mansoor Ali, by founder vote) and a directeur general "
    "(Leo Joy, also CFO) are the two statutory officers. Major decisions "
    "(raising more equity, opening a new country, executive hires above "
    "EUR 70,000) require a two-thirds founder vote. The angel investor "
    "has an information right but no veto."
)
H2("8.4 Internal organisation")
BULLETS([
    "Operations team (apartment sourcing, setup, maintenance) reports to the COO.",
    "Student support team (coordinators in each city) reports to the head of student support.",
    "Platform team (engineers, designer) reports to the CTO.",
    "Marketing and growth report to the head of marketing.",
    "Finance, legal and HR report to the CFO and the head of legal "
    "respectively, both reporting to the CEO.",
])
H2("8.5 Regulatory and tax")
P(
    "Euronest is a furnished rental operator subject to the loi ALUR and, "
    "where applicable, the loi ELAN. We register under the regime LMNP "
    "(Loueur en Meuble Non Professionnel) for year one and expect to "
    "move to LMP from year two onwards. VAT applies on the service "
    "portion of the bundle (gym, streaming, food) but not on the rent "
    "itself, in line with French tax practice."
)
H2("8.6 Data protection")
P(
    "GDPR applies to everything we store about students. We have appointed "
    "Nithin Pallampetti Velayudhan as data protection officer. Student "
    "data is hosted on a French cloud provider (OVH) with encryption at "
    "rest. We do not share data with service partners beyond the strict "
    "minimum needed to provision the bundled service."
)
PBR()

# =====================================================================
# 9. ROADMAP
# =====================================================================
H1("9. Roadmap")
H2("9.1 Milestones")
TBL2(
    ["Quarter", "Milestone", "Owner"],
    [
        ["Q2 2026", "Company incorporated as SAS. Initial raise closed.", "CEO / CFO"],
        ["Q2 2026", "MVP of the booking website live in English and French.", "CTO"],
        ["Q3 2026", "First 25 apartments under head-lease in Paris and Lyon.", "COO"],
        ["Q3 2026", "September 2026 intake: 20 paid subscribers onboarded.", "Marketing / Support"],
        ["Q4 2026", "Mobile app (iOS and Android) released.", "CTO"],
        ["Q1 2027", "55 active subscribers. First three-month financial review.", "CFO"],
        ["Q2 2027", "Lille and Toulouse pilot. 100 active subscribers.", "COO / Marketing"],
        ["Q3 2027", "AI roommate matching module live.", "CTO"],
        ["Q4 2027", "180 active subscribers. EBITDA-positive month achieved.", "Whole team"],
        ["Q2 2028", "Marseille launched. Spain market study begins.", "CEO"],
        ["Q4 2028", "320 active subscribers. Series A discussions opened.", "CEO / CFO"],
    ],
    col_widths=[2.5 * cm, 10 * cm, 3.5 * cm],
)
H2("9.2 What we will know by month 18")
P(
    "By the end of 2027 we will know three things: whether the "
    "subscription bundle holds together at scale (margin discipline), "
    "whether students stay or churn between academic years (retention), "
    "and whether the brand carries across cities or needs to be rebuilt "
    "locally (marketing efficiency). These three answers decide whether "
    "year three is an expansion year or a consolidation year."
)
H2("9.3 Beyond France")
P(
    "The natural next markets are Spain (Madrid, Barcelona) and Italy "
    "(Milan), both of which share the same Erasmus and non-EU student "
    "patterns. Germany is larger but more regulated. We will not commit "
    "to a country outside France before we are comfortably EBITDA-positive "
    "at home. The plan is to grow boring before we grow ambitious."
)
PBR()

# =====================================================================
# 10. APPENDIX
# =====================================================================
H1("10. Appendix")
H2("A. Glossary")
BULLETS([
    "ALUR / ELAN: French housing laws governing rental contracts and "
    "tenant protections.",
    "BSPCE: bons de souscription de parts de createur d'entreprise. The "
    "French equivalent of employee stock options.",
    "DPE: Diagnostic de Performance Energetique. Energy rating for a "
    "French property.",
    "LMNP / LMP: tax regimes for non-professional and professional "
    "furnished rental operators.",
    "SAS: Societe par Actions Simplifiee. A flexible French corporate "
    "form often used by startups.",
])
H2("B. Source meeting minutes")
BULLETS([
    "Session 3 (Problem Diagnosis and Business Strategy): problem "
    "analysis, why now, market research, commercial strategy, SWOT and "
    "PESTEL analysis.",
    "Session on Business Model and Financial Planning: value "
    "proposition, revenue model, cost structure, key partners, "
    "operational workflow, financial overview.",
    "New Venture Development meeting (10 April 2026, ISTEC): problem "
    "identification, business idea, USP, tier-based model, AI roommate "
    "matching.",
])
H2("C. References to the Business Creation Process")
P(
    "The structure of this document follows the nine-step business "
    "creation process used in the MBA English programme: cover page and "
    "contents, executive summary, problem analysis and value proposition, "
    "market research and strategy, business model, human resources and "
    "risks, financial forecasts, legal and organisational structure, "
    "roadmap, and appendix. Each section in the body of this plan maps "
    "one-to-one to that outline."
)

H2("D. Community and neighbourhood engagement")
P(
    "Euronest is a tenant in shared buildings. Our presence is felt "
    "by the neighbours whether we plan for it or not, so we plan for "
    "it."
)
BULLETS([
    "A named coordinator introduces themselves to the building syndic "
    "and immediate neighbours within the first week of taking on any "
    "new property.",
    "We publish a phone number that local residents can call about "
    "noise or other concerns. Calls are answered the same day.",
    "We work with the student association of each partner university "
    "to point new arrivals towards volunteering and language exchanges. "
    "The point is to give students reasons to be in the neighbourhood "
    "during the day, not only at night.",
    "A short code of conduct (noise, deliveries, common areas) is "
    "included in the welcome pack and signed at move-in.",
])

H2("E. Sustainability and travel")
P(
    "We are not building a car-dependent product. The cities we operate "
    "in have working public transport, and our subscribers are mostly "
    "students without a car. The choices below follow from that, not "
    "from a green badge on the website."
)
BULLETS([
    "No allocated parking spaces in any unit. Where a building offers "
    "parking, we reassign it to the syndic.",
    "Secure bike storage at every property. Where the building has "
    "none, we install it.",
    "Welcome pack includes the Navigo / TCL / Ilevia transit pass for "
    "the relevant city, plus a one-month season ticket pre-loaded.",
    "Only properties at DPE energy class D or better are signed. "
    "We renegotiate or walk away from anything worse.",
    "Annual review of the energy spend per square metre across the "
    "portfolio. Properties in the bottom quartile are flagged for "
    "non-renewal.",
])

H2("F. Waste and recycling")
P(
    "Each apartment gets two indoor bins (general and recycling) and a "
    "clear label about what goes where. Move-in includes a five-minute "
    "walkthrough of the waste room in the building. At move-out we run "
    "a reuse drive in partnership with Emmaus or a local equivalent: "
    "furniture, kitchenware and clothes that subscribers do not want "
    "to ship home are collected and donated rather than dumped on the "
    "kerb."
)

H2("G. Fire and life safety")
P(
    "Statement of intent. Euronest takes responsibility for the safety "
    "of subscribers in the units we head-lease. In practice that means:"
)
BULLETS([
    "Every unit has a working smoke detector tested at move-in and "
    "annually thereafter.",
    "Fire blanket and a 2 kg dry-powder extinguisher in each apartment "
    "kitchen.",
    "Evacuation diagram fitted inside the front door of every unit, "
    "in French and English.",
    "Personal Emergency Evacuation Plan (PEEP) prepared on request for "
    "any subscriber with a declared disability.",
    "Annual fire risk assessment by a French certified consultant. "
    "Findings logged and remediated within 60 days.",
])

H2("H. Contact")
P("Euronest founding team<br/>ISTEC, Paris<br/>founders@euronest.eu")


# =====================================================================
# PAGE TEMPLATE: header + footer
# =====================================================================
def on_page(canvas, doc_):
    canvas.saveState()
    # Header
    page = doc_.page
    if page > 1:
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(NAVY)
        canvas.drawString(2 * cm, A4[1] - 1.2 * cm, "EURONEST")
        canvas.setFont("Helvetica", 8.5)
        canvas.setFillColor(HexColor("#555"))
        canvas.drawRightString(
            A4[0] - 2 * cm, A4[1] - 1.2 * cm,
            "Business Plan  |  April 2026",
        )
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(2 * cm, A4[1] - 1.35 * cm, A4[0] - 2 * cm, A4[1] - 1.35 * cm)
    # Footer
    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(HexColor("#666"))
    canvas.drawString(2 * cm, 1.2 * cm, "Euronest SAS (in formation)")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {page}")
    canvas.restoreState()


out_pdf = "/home/user/first/Euronest_Business_Plan.pdf"
pdf = SimpleDocTemplate(
    out_pdf,
    pagesize=A4,
    topMargin=2.2 * cm,
    bottomMargin=2 * cm,
    leftMargin=2.2 * cm,
    rightMargin=2.2 * cm,
    title="Euronest Business Plan",
    author="Euronest founding team",
)

pdf.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"Saved PDF: {out_pdf}")
