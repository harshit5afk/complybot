import os
import sys
import pptx
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def build_presentation_v3():
    template_path = os.path.expanduser(r'~\Downloads\6aa7f1b39e957_infothon_7_0_template.pptx')
    prs = pptx.Presentation(template_path)
    
    # Color Palette matching the cyber HUD theme
    C_LIME = RGBColor(193, 255, 114)       # #C1FF72 (Primary Accent & Highlights)
    C_NEON = RGBColor(34, 197, 94)        # #22C55E (Neon Green Border)
    C_CYAN = RGBColor(45, 212, 191)       # #2DD4BF (Teal / Cyan Header Pills like reference image)
    C_BRIGHT = RGBColor(74, 222, 128)     # #4ADE80 (Accents & Keys)
    C_WHITE = RGBColor(255, 255, 255)     # #FFFFFF (Headings & Pure White)
    C_OFFWHITE = RGBColor(235, 245, 238)   # #EBF5EE (Body Text)
    C_MUTED = RGBColor(160, 185, 170)     # #A0B9AA (Secondary Text)
    C_CARD_BG = RGBColor(7, 20, 13)       # Deep dark cyber green card
    C_CARD_BG2 = RGBColor(10, 26, 17)     # Slightly lighter dark card
    C_PILL_BG = RGBColor(13, 38, 25)      # Header pill background
    
    FONT_TITLE = 'Anton'
    FONT_HEADING = 'Arial'
    FONT_BODY = 'Segoe UI'

    def remove_shapes_by_name(slide, names):
        for name in names:
            for s in list(slide.shapes):
                if s.name == name:
                    sp = s._element
                    sp.getparent().remove(sp)

    def add_hud_card(slide, left, top, width, height, title, items, border_color=C_NEON, bg_color=C_CARD_BG, title_color=C_LIME, font_size_pt=12.5, space_after_pt=8):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)
        
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.25)
        tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.22)
        tf.margin_bottom = Inches(0.2)
        tf.vertical_anchor = MSO_ANCHOR.TOP
        
        p_title = tf.paragraphs[0]
        p_title.text = title.upper()
        p_title.font.name = FONT_HEADING
        p_title.font.bold = True
        p_title.font.size = Pt(15.5)
        p_title.font.color.rgb = title_color
        p_title.space_after = Pt(10)
        
        for item in items:
            p = tf.add_paragraph()
            p.font.name = FONT_BODY
            p.font.size = Pt(font_size_pt)
            p.space_after = Pt(space_after_pt)
            
            if isinstance(item, tuple):
                r_head = p.add_run()
                r_head.text = "• " + item[0] + ": "
                r_head.font.bold = True
                r_head.font.color.rgb = C_BRIGHT
                
                r_body = p.add_run()
                r_body.text = item[1]
                r_body.font.color.rgb = C_OFFWHITE
            else:
                p.text = "• " + item
                p.font.color.rgb = C_OFFWHITE

        return card

    # =========================================================================
    # SLIDE 1: TITLE SLIDE (Team: STAR WARS, Domain: CLEARED)
    # =========================================================================
    s1 = prs.slides[0]
    
    # Center Project Pill / Banner
    banner = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(2500000), Emu(5900000), Emu(13288000), Emu(680000))
    banner.fill.solid()
    banner.fill.fore_color.rgb = C_CARD_BG2
    banner.line.color.rgb = C_BRIGHT
    banner.line.width = Pt(1.5)
    tf_b = banner.text_frame
    tf_b.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_b.word_wrap = True
    p_b = tf_b.paragraphs[0]
    p_b.alignment = PP_ALIGN.CENTER
    
    r1 = p_b.add_run()
    r1.text = "COMPLYBOT : "
    r1.font.name = FONT_TITLE
    r1.font.size = Pt(17)
    r1.font.color.rgb = C_LIME
    r1.font.bold = True
    
    r2 = p_b.add_run()
    r2.text = "AI-Powered Multi-Agent Assistant for Indian Standards & BIS Services  |  "
    r2.font.name = FONT_HEADING
    r2.font.size = Pt(13)
    r2.font.bold = True
    r2.font.color.rgb = C_WHITE
    
    r3 = p_b.add_run()
    r3.text = "PS #04 (SIH26107)"
    r3.font.name = FONT_HEADING
    r3.font.size = Pt(13)
    r3.font.bold = True
    r3.font.color.rgb = C_LIME

    # In Group 20: Team Name = "STAR WARS"
    team_val = s1.shapes.add_textbox(Emu(5300000), Emu(7080000), Emu(4800000), Emu(550000))
    tf_tv = team_val.text_frame
    tf_tv.margin_left = tf_tv.margin_right = tf_tv.margin_top = tf_tv.margin_bottom = 0
    tf_tv.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_tv = tf_tv.paragraphs[0]
    r_tv = p_tv.add_run()
    r_tv.text = "STAR WARS"
    r_tv.font.name = FONT_TITLE
    r_tv.font.size = Pt(22)
    r_tv.font.bold = True
    r_tv.font.color.rgb = C_LIME

    # Domain: CLEARED (Left completely blank as requested by user)
    # We do NOT add domain_val shape, leaving the cyber bracket empty for the user to fill!

    # Sub-detail bar at bottom
    sub_foot = s1.shapes.add_textbox(Emu(2000000), Emu(8650000), Emu(14288000), Emu(500000))
    tf_sf = sub_foot.text_frame
    tf_sf.margin_left = tf_sf.margin_right = tf_sf.margin_top = tf_sf.margin_bottom = 0
    p_sf = tf_sf.paragraphs[0]
    p_sf.alignment = PP_ALIGN.CENTER
    r_sf = p_sf.add_run()
    r_sf.text = "Team: STAR WARS  •  Lead: Harshit Vishwakarma  •  100% Offline GPU Inference via Ollama  •  PS #04"
    r_sf.font.name = FONT_BODY
    r_sf.font.size = Pt(11.5)
    r_sf.font.color.rgb = C_MUTED

    # =========================================================================
    # SLIDE 2: PROBLEM IDENTIFICATION
    # =========================================================================
    s2 = prs.slides[1]
    remove_shapes_by_name(s2, ['TextBox 8'])
    
    col_width = Emu(4900000)
    col_height = Emu(4500000)
    top_pos = Emu(2000000)
    
    add_hud_card(
        s2, Emu(1400000), top_pos, col_width, col_height,
        "WHO IS AFFECTED",
        [
            ("Indian MSMEs", "Over 63 million small manufacturers struggling with mandatory BIS compliance."),
            ("Consumers & Buyers", "Citizens purchasing gold jewellery and electronic appliances needing authenticity proof."),
            ("Innovators & Students", "Engineers and researchers seeking exact standard clauses for R&D."),
            ("BIS Service Seekers", "Enterprises looking for accredited testing labs and licensing application flows."),
            ("Regulatory Bodies", "Officials seeking transparent, verifiable tools to curb non-compliant goods.")
        ],
        font_size_pt=12.5, space_after_pt=9
    )
    
    add_hud_card(
        s2, Emu(6694000), top_pos, col_width, col_height,
        "CORE PAIN POINT",
        [
            ("Information Dispersion", "Critical data is scattered across disjointed BIS PDFs and multiple portals."),
            ("Complex Certification", "Heavy confusion regarding scheme differences (ISI Mark vs. CRS vs. FMCS)."),
            ("Hallmarking Ambiguity", "Lack of instant consumer tools to verify 6-digit HUID and karat purity."),
            ("Testing Lab Friction", "Painstaking manual search for nearest accredited laboratories by product type."),
            ("High Consultancy Cost", "Small businesses forced to pay hefty agent fees for basic compliance guidance.")
        ],
        font_size_pt=12.5, space_after_pt=9
    )
    
    add_hud_card(
        s2, Emu(11988000), top_pos, col_width, col_height,
        "CURRENT GAP",
        [
            ("Keyword Search Failures", "Existing government portals rely on rigid keywords rather than natural language."),
            ("Zero Centralized Reasoning", "No unified conversational AI layer connecting standards, labs & schemes."),
            ("Lack of Traceable Sources", "General LLMs (ChatGPT) hallucinate rules and cannot cite official clauses."),
            ("Language Barriers", "Over 70% of MSME owners prefer Hindi, but compliance documentation is in complex English."),
            ("Data Privacy Concerns", "Commercial APIs expose enterprise product secrets to public cloud servers.")
        ],
        font_size_pt=12.5, space_after_pt=9
    )
    
    bottom_bar = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(1400000), Emu(6800000), Emu(15488000), Emu(2200000))
    bottom_bar.fill.solid()
    bottom_bar.fill.fore_color.rgb = C_CARD_BG2
    bottom_bar.line.color.rgb = C_BRIGHT
    bottom_bar.line.width = Pt(1.5)
    tf_bb = bottom_bar.text_frame
    tf_bb.word_wrap = True
    tf_bb.margin_left = Inches(0.35)
    tf_bb.margin_top = Inches(0.22)
    tf_bb.margin_right = Inches(0.35)
    
    p_bb_title = tf_bb.paragraphs[0]
    p_bb_title.text = "Problem Statement Focus"
    p_bb_title.font.name = FONT_HEADING
    p_bb_title.font.bold = True
    p_bb_title.font.size = Pt(17)
    p_bb_title.font.color.rgb = C_LIME
    p_bb_title.space_after = Pt(6)
    
    p_bb_body = tf_bb.add_paragraph()
    p_bb_body.text = (
        "Create an NLP assistant that answers standards and certification queries for Indian MSMEs with "
        "referenced, evidence-backed responses. The broader concept also serves consumers through product, "
        "hallmarking and complaint guidance — running entirely locally with 0 API costs and guaranteed source citations."
    )
    p_bb_body.font.name = FONT_BODY
    p_bb_body.font.size = Pt(13.5)
    p_bb_body.font.color.rgb = C_WHITE

    # =========================================================================
    # SLIDE 3: PROPOSED SOLUTION
    # =========================================================================
    s3 = prs.slides[2]
    remove_shapes_by_name(s3, ['TextBox 7'])
    
    step_width = Emu(2700000)
    step_height = Emu(2250000)
    step_gap = Emu(450000)
    step_top = Emu(2000000)
    start_left = Emu(1400000)
    
    steps = [
        ("ASK 💬", "Natural Language Query", "User inputs plain query in English or हिन्दी via chat UI."),
        ("ROUTE 🧭", "Deterministic Routing", "Router Agent classifies domain & intent in 0ms (LLM fallback)."),
        ("RETRIEVE 🔍", "Vector RAG & Rules", "Searches ChromaDB vector store + structured JSON rule engines."),
        ("VERIFY 🛡️", "Evidence Validation", "Cross-checks official BIS clauses, testing lab data & purity formulas."),
        ("RESPOND ⚡", "Cited Synthesis", "Plain-language answer with Agent Transparency Badge & citations.")
    ]
    
    for i, (title, sub, desc) in enumerate(steps):
        s_left = start_left + i * (step_width + step_gap)
        box = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, s_left, step_top, step_width, step_height)
        box.fill.solid()
        box.fill.fore_color.rgb = C_CARD_BG
        box.line.color.rgb = C_NEON
        box.line.width = Pt(1.5)
        
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.12)
        tf.margin_right = Inches(0.12)
        tf.margin_top = Inches(0.18)
        tf.vertical_anchor = MSO_ANCHOR.TOP
        
        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.name = FONT_HEADING
        p_t.font.bold = True
        p_t.font.size = Pt(14.5)
        p_t.font.color.rgb = C_LIME
        p_t.alignment = PP_ALIGN.CENTER
        
        p_s = tf.add_paragraph()
        p_s.text = sub
        p_s.font.name = FONT_BODY
        p_s.font.bold = True
        p_s.font.size = Pt(11)
        p_s.font.color.rgb = C_BRIGHT
        p_s.alignment = PP_ALIGN.CENTER
        p_s.space_after = Pt(5)
        
        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.name = FONT_BODY
        p_d.font.size = Pt(10.5)
        p_d.font.color.rgb = C_OFFWHITE
        p_d.alignment = PP_ALIGN.CENTER
        
        if i < 4:
            arr_left = s_left + step_width + Emu(40000)
            arr = s3.shapes.add_textbox(arr_left, step_top + Emu(750000), step_gap - Emu(80000), Emu(600000))
            tf_a = arr.text_frame
            tf_a.margin_left = tf_a.margin_right = tf_a.margin_top = tf_a.margin_bottom = 0
            p_a = tf_a.paragraphs[0]
            p_a.text = "➔"
            p_a.font.name = 'Segoe UI Symbol'
            p_a.font.size = Pt(22)
            p_a.font.color.rgb = C_BRIGHT
            p_a.alignment = PP_ALIGN.CENTER

    lower_top = Emu(4550000)
    lower_width = Emu(7500000)
    lower_height = Emu(4450000)
    
    add_hud_card(
        s3, Emu(1400000), lower_top, lower_width, lower_height,
        "Key Capabilities",
        [
            ("Standards Q&A", "Semantic RAG search over BIS standards (IS 16102 for LEDs, IS 14543 for water, IS 9873 for toys)."),
            ("Certification Schemes", "Clear walkthroughs for ISI Mark, Compulsory Registration Scheme (CRS), and FMCS."),
            ("Instant Hallmarking", "0ms rule-based verification of gold purity (24K/22K/18K/14K) and 6-digit alphanumeric HUID format."),
            ("Lab Finder Agent", "Locates nearest BIS-recognized testing laboratories filtered by product type and state."),
            ("Bilingual Engine", "Native English and Hindi translation layer powered by Qwen2.5 for inclusive nationwide reach.")
        ],
        font_size_pt=12.5, space_after_pt=8
    )
    
    add_hud_card(
        s3, Emu(9388000), lower_top, lower_width, lower_height,
        "Innovation Edge",
        [
            ("Zero Hallucinations", "Every response is strictly grounded with exact BIS standard & clause citations."),
            ("Transparent Agent Badges", "Live 'Answered by: [Agent Name]' badges verify multi-agent orchestration for judges."),
            ("100% Offline Local AI", "Runs entirely on consumer GPUs via Ollama — zero cloud bills, zero internet risk during demo."),
            ("Deterministic Hybrid Routing", "Keyword-first dispatch eliminates LLM routing latency for maximum demo reliability."),
            ("Flagged Uncertainty", "Uncertain or out-of-scope queries are explicitly flagged rather than guessed.")
        ],
        font_size_pt=12.5, space_after_pt=8
    )

    # =========================================================================
    # SLIDE 4: TECHNOLOGY STACK (Modeled like user's reference diagram + REAL LOGOS!)
    # =========================================================================
    s4 = prs.slides[3]
    remove_shapes_by_name(s4, ['TextBox 8', 'AutoShape 9', 'AutoShape 10', 'TextBox 11', 'AutoShape 12', 'AutoShape 13'])
    
    # Left / Architecture Block Flow: width = 11,800,000 EMU
    # Right / Tech Stack Sidebar: width = 3,700,000 EMU
    
    def add_arch_block(left, top, width, height, pill_title, bullets, pill_color=C_CYAN):
        # Base card
        card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD_BG
        card.line.color.rgb = C_NEON
        card.line.width = Pt(1.2)
        
        # Pill header on top of the card
        pill_w = min(width - Emu(300000), Emu(3400000) if width > Emu(4000000) else width - Emu(200000))
        pill_h = Emu(380000)
        pill = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left + Emu(150000), top - Emu(180000), pill_w, pill_h)
        pill.fill.solid()
        pill.fill.fore_color.rgb = pill_color
        pill.line.color.rgb = C_WHITE
        pill.line.width = Pt(1)
        tf_p = pill.text_frame
        tf_p.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_pt = tf_p.paragraphs[0]
        p_pt.text = pill_title.upper()
        p_pt.font.name = FONT_HEADING
        p_pt.font.bold = True
        p_pt.font.size = Pt(11)
        p_pt.font.color.rgb = RGBColor(6, 20, 12) # Dark text on bright pill
        p_pt.alignment = PP_ALIGN.CENTER
        
        # Text inside the card
        tf_c = card.text_frame
        tf_c.word_wrap = True
        tf_c.margin_left = Inches(0.18)
        tf_c.margin_right = Inches(0.18)
        tf_c.margin_top = Inches(0.28) # Margin to clear pill
        tf_c.margin_bottom = Inches(0.15)
        tf_c.vertical_anchor = MSO_ANCHOR.TOP
        
        for idx, item in enumerate(bullets):
            p = tf_c.paragraphs[0] if idx == 0 else tf_c.add_paragraph()
            p.font.name = FONT_BODY
            p.font.size = Pt(11)
            p.space_after = Pt(4)
            
            if isinstance(item, tuple):
                r_head = p.add_run()
                r_head.text = item[0] + ": "
                r_head.font.bold = True
                r_head.font.color.rgb = C_BRIGHT
                
                r_body = p.add_run()
                r_body.text = item[1]
                r_body.font.color.rgb = C_OFFWHITE
            else:
                p.text = "• " + item
                p.font.color.rgb = C_OFFWHITE

    # 1. Users Block (Top-Left)
    add_arch_block(
        Emu(1400000), Emu(2000000), Emu(3400000), Emu(1500000),
        "Users & Stakeholders",
        [
            ("MSMEs & Industries", "Factory owners & quality managers"),
            ("Consumers & Buyers", "Citizens verifying hallmarked jewellery")
        ],
        pill_color=C_CYAN
    )

    # 2. Access & Router Gateway (Top-Center)
    add_arch_block(
        Emu(5100000), Emu(2000000), Emu(8000000), Emu(1500000),
        "API Gateway & Hybrid Router",
        [
            ("FastAPI Async Endpoint", "Session handling with <15ms response latency"),
            ("0ms Deterministic Router", "Keyword dispatcher with LLM intent fallback classifier"),
            ("Multilingual Support", "Native query routing for English & हिन्दी")
        ],
        pill_color=C_CYAN
    )

    # 3. Industry Compliance Agents (Middle-Left)
    add_arch_block(
        Emu(1400000), Emu(3800000), Emu(5700000), Emu(2650000),
        "Industry & MSME Agents",
        [
            ("Retriever Agent (RAG)", "Cosine similarity search over BIS standards (IS 16102, IS 14543)"),
            ("Certification Agent", "Detailed steps for ISI Mark, CRS & FMCS schemes with timelines"),
            ("Lab Finder Agent", "Locates nearest testing labs by product & state directory"),
            ("Clause Citations", "Exact clause-level citations with zero hallucination")
        ],
        pill_color=C_LIME
    )

    # 4. Consumer Protection Agents (Middle-Right)
    add_arch_block(
        Emu(7400000), Emu(3800000), Emu(5700000), Emu(2650000),
        "Consumer & Verification Agents",
        [
            ("Hallmarking Agent", "0-latency rule checks for 24K/22K/18K purity & 6-digit HUID"),
            ("Consumer Rights Agent", "Plain-language guidance with BIS CARE app & 1915 helpline"),
            ("Agent Badging Layer", "Live visual 'Answered by: [Agent]' badge for explainability"),
            ("Hindi Engine", "Real-time natural language synthesis in Hindi")
        ],
        pill_color=C_LIME
    )

    # 5. Data & Retrieval Layer (Bottom-Left)
    add_arch_block(
        Emu(1400000), Emu(6750000), Emu(5700000), Emu(2400000),
        "Data & Retrieval Layer",
        [
            ("ChromaDB Vector Store", "Persistent embeddings via nomic-embed-text (768-dim)"),
            ("Structured Rule Stores", "JSON catalogs for schemes, labs & gold hallmarking"),
            ("Standards Catalog", "Markdown chunking with metadata clause indices")
        ],
        pill_color=C_CYAN
    )

    # 6. Local AI Inference Layer (Bottom-Right)
    add_arch_block(
        Emu(7400000), Emu(6750000), Emu(5700000), Emu(2400000),
        "Local AI Inference Engine",
        [
            ("Ollama GPU Server", "Runs locally on consumer GPU with NVIDIA CUDA"),
            ("Qwen2.5 7B Instruct", "Grounded synthesis & English ↔ Hindi translation"),
            ("100% Offline & Private", "Zero cloud API calls, zero data leaks, $0 token bills")
        ],
        pill_color=C_CYAN
    )

    # =========================================================================
    # RIGHT SIDEBAR: "TECH STACK" WITH REAL LOGOS / SYMBOLS
    # =========================================================================
    sb_left = Emu(13400000)
    sb_top = Emu(1900000)
    sb_width = Emu(3800000)
    sb_height = Emu(7250000)
    
    # Outer sidebar card
    sb_card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sb_left, sb_top, sb_width, sb_height)
    sb_card.fill.solid()
    sb_card.fill.fore_color.rgb = C_CARD_BG2
    sb_card.line.color.rgb = C_CYAN
    sb_card.line.width = Pt(1.8)
    
    # Sidebar Header Pill
    sb_pill = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sb_left + Emu(400000), sb_top - Emu(180000), sb_width - Emu(800000), Emu(450000))
    sb_pill.fill.solid()
    sb_pill.fill.fore_color.rgb = C_CYAN
    sb_pill.line.color.rgb = C_WHITE
    sb_pill.line.width = Pt(1.2)
    tf_sp = sb_pill.text_frame
    tf_sp.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_sp = tf_sp.paragraphs[0]
    p_sp.text = "TECH STACK"
    p_sp.font.name = FONT_TITLE
    p_sp.font.size = Pt(15)
    p_sp.font.color.rgb = RGBColor(6, 20, 12)
    p_sp.alignment = PP_ALIGN.CENTER
    
    # 7 Tech Items with Real Logos
    tech_items = [
        ("python.png", "Python 3.10+", "Core Runtime & Logic"),
        ("fastapi.png", "FastAPI", "High-Throughput REST API"),
        ("ollama.png", "Ollama", "Local GPU Model Server"),
        ("qwen.png", "Qwen2.5 7B", "Multilingual Reasoning LLM"),
        ("chroma.png", "ChromaDB", "Persistent Vector Store"),
        ("javascript.png", "JavaScript", "Responsive Web Chat UI"),
        ("nvidia.png", "NVIDIA CUDA", "Local GPU Acceleration"),
    ]
    
    icon_dir = r'c:\STAR WARS\complybot\template_assets\icons'
    row_start_top = sb_top + Emu(480000)
    row_height = Emu(920000)
    
    for idx, (icon_file, name, role) in enumerate(tech_items):
        r_top = row_start_top + idx * row_height
        
        # Subtle separator / row background
        row_bg = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sb_left + Emu(150000), r_top, sb_width - Emu(300000), Emu(820000))
        row_bg.fill.solid()
        row_bg.fill.fore_color.rgb = C_PILL_BG
        row_bg.line.color.rgb = RGBColor(25, 65, 42)
        row_bg.line.width = Pt(0.8)
        
        # Add Real Logo Picture
        icon_path = os.path.join(icon_dir, icon_file)
        if os.path.exists(icon_path):
            s4.shapes.add_picture(
                icon_path,
                sb_left + Emu(280000),
                r_top + Emu(100000),
                width=Emu(620000),
                height=Emu(620000)
            )
        
        # Text block
        tb = s4.shapes.add_textbox(
            sb_left + Emu(1020000),
            r_top + Emu(80000),
            sb_width - Emu(1150000),
            Emu(660000)
        )
        tf_t = tb.text_frame
        tf_t.word_wrap = True
        tf_t.margin_left = tf_t.margin_right = tf_t.margin_top = tf_t.margin_bottom = 0
        
        p1 = tf_t.paragraphs[0]
        p1.text = name
        p1.font.name = FONT_HEADING
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = C_WHITE
        
        p2 = tf_t.add_paragraph()
        p2.text = role
        p2.font.name = FONT_BODY
        p2.font.size = Pt(10)
        p2.font.color.rgb = C_LIME

    # =========================================================================
    # SLIDE 5: FEASIBILITY & IMPACT
    # =========================================================================
    s5 = prs.slides[4]
    remove_shapes_by_name(s5, ['TextBox 7'])
    
    card_w = Emu(7500000)
    card_h = Emu(3350000)
    r1_top = Emu(2000000)
    r2_top = Emu(5650000)
    c1_left = Emu(1400000)
    c2_left = Emu(9388000)
    
    add_hud_card(
        s5, c1_left, r1_top, card_w, card_h,
        "Implementation Viability (Demo-Ready)",
        [
            ("Fully Operational MVP", "Complete end-to-end working software ready and demonstrated live today."),
            ("Commodity Hardware", "Runs comfortably on standard 6–8GB VRAM consumer GPUs (RTX 3050/3060)."),
            ("Zero Operational Cost", "100% local inference eliminates expensive API token billing ($0 deployment cost)."),
            ("Guaranteed Demo Uptime", "Zero reliance on external internet connections or third-party cloud availability.")
        ],
        font_size_pt=12.5, space_after_pt=8
    )
    
    add_hud_card(
        s5, c2_left, r1_top, card_w, card_h,
        "Technical Foundation & Scalability",
        [
            ("Modular Micro-Agents", "Decoupled architecture enables hot-plugging new standards and agent services."),
            ("Grounded RAG Pipeline", "Strict citation anchoring eliminates hallucinations and prevents legal misinformation."),
            ("Sub-Second Latency", "Deterministic rule engines deliver instantaneous responses for hallmarking & labs."),
            ("Production-Ready Schema", "Pydantic validated data structures ensure seamless future BIS CARE API sync.")
        ],
        font_size_pt=12.5, space_after_pt=8
    )
    
    add_hud_card(
        s5, c1_left, r2_top, card_w, card_h,
        "Measurable Outcomes & Impact",
        [
            ("98% Time Reduction", "Compresses compliance research from 3–5 hours across portals to <5 seconds."),
            ("Empowering 63M+ MSMEs", "Democratizes complex regulatory access, saving lakhs in third-party consultancy."),
            ("Consumer Fraud Protection", "Instant 6-digit HUID format checks shield buyers from counterfeit jewellery."),
            ("Linguistic Inclusion", "Hindi support empowers Tier-2 and rural artisans to achieve formal BIS certification.")
        ],
        font_size_pt=12.5, space_after_pt=8
    )
    
    add_hud_card(
        s5, c2_left, r2_top, card_w, card_h,
        "Conclusion & Novelty (Infothon 7.0)",
        [
            ("Full Spectrum Coverage", "The only platform unifying all 8 core BIS capabilities into one conversational interface."),
            ("Transparent & Auditable", "Every synthesized answer includes auditable source standard clauses and agent badges."),
            ("National Scalability", "Extensible to all 20,000+ Indian Standards covering 15 core national industry sectors."),
            ("Autonomous Vision", "Directly fulfills the theme: 'Architecting an Autonomous Tomorrow' for Indian regulatory compliance.")
        ],
        font_size_pt=12.5, space_after_pt=8
    )

    # =========================================================================
    # SLIDE 6: SYSTEM ARCHITECTURE & DEMO WORKFLOW
    # =========================================================================
    s6 = prs.slides[5]
    remove_shapes_by_name(s6, ['TextBox 7'])
    
    for s in s6.shapes:
        if s.name == 'TextBox 5' and s.has_text_frame:
            s.text_frame.text = "SYSTEM ARCHITECTURE & DEMO"
            s.text_frame.paragraphs[0].font.name = FONT_TITLE
            s.text_frame.paragraphs[0].font.size = Pt(36)
            s.text_frame.paragraphs[0].font.color.rgb = C_LIME
            s.left = Emu(2900000)
            s.top = Emu(360000)
            s.width = Emu(14000000)
    
    arch_w = Emu(7600000)
    arch_h = Emu(7000000)
    
    add_hud_card(
        s6, Emu(1400000), Emu(1900000), arch_w, arch_h,
        "Multi-Agent Swarm Architecture",
        [
            ("User Layer", "Responsive Web Chat Interface with English & हिन्दी toggles."),
            ("API Gateway", "FastAPI async server managing conversation context & session routing."),
            ("Router Agent", "Deterministic keyword classifier (0ms) + LLM intent fallback:"),
            ("  • Retriever Agent (RAG)", "Cosine similarity search over ChromaDB + nomic-embed-text."),
            ("  • Certification Agent", "Maps products to ISI / CRS / FMCS schemes & application timelines."),
            ("  • Consumer Agent", "Plain-language explanations linked with BIS CARE app & 1915 helpline."),
            ("  • Hallmarking Agent", "0-latency rule checks for 24K/22K/18K gold purity & 6-digit HUID."),
            ("  • Lab Finder Agent", "Geo-directory filtering recognized testing laboratories by domain."),
            ("Local AI Synthesis", "Qwen2.5-7B Instruct synthesizes grounded answers on local GPU."),
            ("Explainable Response", "Delivers verified standard citations & live Agent Transparency Badge.")
        ],
        font_size_pt=12.5, space_after_pt=8
    )
    
    demo_w = Emu(7588000)
    demo_h = Emu(7000000)
    
    add_hud_card(
        s6, Emu(9300000), Emu(1900000), demo_w, demo_h,
        "Live Demo Validation Scenarios",
        [
            ("Scenario 1: MSME Industry Guidance", "LED Bulb manufacturer asks: 'How do I certify my LED lights?'\n➔ Certification Agent explains CRS scheme with IS 16102 standard citation."),
            ("Scenario 2: Consumer Protection in Hindi", "User asks: '22 कैरेट सोने पर क्या हॉलमार्क होना चाहिए?'\n➔ Hallmarking Agent responds in Hindi with 916 purity mark and HUID verification."),
            ("Scenario 3: Testing Lab Locator", "User asks: 'Where can I test packaged drinking water in Karnataka?'\n➔ Lab Finder Agent returns accredited labs for IS 14543 with contact data."),
            ("Scenario 4: Visual Agent Attribution", "Every answer displays a live badge: 'Answered by: [Agent Name]'\n➔ Proves autonomous routing live to hackathon judges with zero fake mockups."),
            ("Future Roadmap", "Direct BIS CARE API sync, voice telephony for rural artisans, & cataloging 20,000+ national standards.")
        ],
        font_size_pt=12.5, space_after_pt=8
    )

    out_file = r'c:\STAR WARS\complybot\ComplyBot_Infothon_7.0_Final.pptx'
    prs.save(out_file)
    print(f'Successfully saved presentation to: {out_file}')

    downloads_out = os.path.expanduser(r'~\Downloads\ComplyBot_Infothon_7.0_Final.pptx')
    prs.save(downloads_out)
    print(f'Successfully copied presentation to: {downloads_out}')

if __name__ == '__main__':
    build_presentation_v3()
