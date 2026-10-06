import os
import sys
import copy
import pptx
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def build_presentation():
    template_path = os.path.expanduser(r'~\Downloads\6aa7f1b39e957_infothon_7_0_template.pptx')
    prs = pptx.Presentation(template_path)
    
    # Palette
    C_LIME = RGBColor(193, 255, 114)     # #C1FF72
    C_NEON = RGBColor(34, 197, 94)      # #22C55E
    C_BRIGHT = RGBColor(74, 222, 128)   # #4ADE80
    C_WHITE = RGBColor(255, 255, 255)   # #FFFFFF
    C_OFFWHITE = RGBColor(235, 245, 238) # #EBF5EE
    C_MUTED = RGBColor(156, 175, 163)   # #9CAFA3
    C_CARD_BG = RGBColor(9, 23, 15)     # Very dark cyber green
    C_CARD_BG2 = RGBColor(12, 30, 20)
    C_BADGE_BG = RGBColor(16, 42, 28)
    C_ACCENT_ORANGE = RGBColor(251, 191, 36) # Amber for highlights
    
    FONT_TITLE = 'Anton'
    FONT_HEADING = 'Arial'
    FONT_BODY = 'Segoe UI'
    FONT_CODE = 'Consolas'

    def remove_shapes_by_name(slide, names):
        for name in names:
            for s in list(slide.shapes):
                if s.name == name:
                    sp = s._element
                    sp.getparent().remove(sp)

    def add_hud_card(slide, left, top, width, height, title, items, badge=None, border_color=C_NEON, bg_color=C_CARD_BG, title_color=C_LIME):
        # Background card shape
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)
        
        # Add text
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.2)
        tf.margin_right = Inches(0.2)
        tf.margin_top = Inches(0.2)
        tf.margin_bottom = Inches(0.2)
        tf.vertical_anchor = MSO_ANCHOR.TOP
        
        # Title paragraph
        p_title = tf.paragraphs[0]
        p_title.text = title.upper()
        p_title.font.name = FONT_HEADING
        p_title.font.bold = True
        p_title.font.size = Pt(15)
        p_title.font.color.rgb = title_color
        p_title.space_after = Pt(8)
        
        # Items / bullets
        for item in items:
            p = tf.add_paragraph()
            p.font.name = FONT_BODY
            p.font.size = Pt(11.5)
            p.space_after = Pt(5)
            
            if isinstance(item, tuple):
                # (heading, text)
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

        return card

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    s1 = prs.slides[0]
    # Check what's in slide 1
    # Add Project title / banner in the center
    # Center bounds: left=2,600,000, top=5,900,000, width=13,000,000, height=2,000,000
    
    # Project Showcase Card
    title_card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(3000000), Emu(6100000), Emu(12288000), Emu(1500000))
    title_card.fill.solid()
    title_card.fill.fore_color.rgb = C_CARD_BG2
    title_card.line.color.rgb = C_NEON
    title_card.line.width = Pt(1.8)
    tf_tc = title_card.text_frame
    tf_tc.word_wrap = True
    tf_tc.vertical_anchor = MSO_ANCHOR.MIDDLE
    
    p1 = tf_tc.paragraphs[0]
    p1.text = "COMPLYBOT"
    p1.font.name = FONT_TITLE
    p1.font.size = Pt(36)
    p1.font.color.rgb = C_LIME
    p1.alignment = PP_ALIGN.CENTER
    
    p2 = tf_tc.add_paragraph()
    p2.text = "AI-Powered Multi-Agent Assistant for Indian Standards & BIS Services"
    p2.font.name = FONT_HEADING
    p2.font.bold = True
    p2.font.size = Pt(15)
    p2.font.color.rgb = C_WHITE
    p2.alignment = PP_ALIGN.CENTER
    
    p3 = tf_tc.add_paragraph()
    p3.text = "Problem Statement: SIH26107 / PS #04  •  100% Offline Local Inference via Ollama"
    p3.font.name = FONT_BODY
    p3.font.size = Pt(12)
    p3.font.color.rgb = C_BRIGHT
    p3.alignment = PP_ALIGN.CENTER

    # Fill Team Name & Domain boxes at the bottom
    # Group 20 has boxes around top=7,800,000
    team_box = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(1200000), Emu(8000000), Emu(7600000), Emu(850000))
    team_box.fill.solid()
    team_box.fill.fore_color.rgb = C_BADGE_BG
    team_box.line.color.rgb = C_BRIGHT
    team_box.line.width = Pt(1.2)
    tf_tb = team_box.text_frame
    tf_tb.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_tb = tf_tb.paragraphs[0]
    r_tb_l = p_tb.add_run()
    r_tb_l.text = "TEAM: "
    r_tb_l.font.bold = True
    r_tb_l.font.color.rgb = C_LIME
    r_tb_l.font.size = Pt(13)
    r_tb_v = p_tb.add_run()
    r_tb_v.text = "COMPLYBOT (Harshit Vishwakarma & Team)"
    r_tb_v.font.color.rgb = C_WHITE
    r_tb_v.font.size = Pt(13)

    domain_box = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(9488000), Emu(8000000), Emu(7600000), Emu(850000))
    domain_box.fill.solid()
    domain_box.fill.fore_color.rgb = C_BADGE_BG
    domain_box.line.color.rgb = C_BRIGHT
    domain_box.line.width = Pt(1.2)
    tf_db = domain_box.text_frame
    tf_db.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_db = tf_db.paragraphs[0]
    r_db_l = p_db.add_run()
    r_db_l.text = "DOMAIN: "
    r_db_l.font.bold = True
    r_db_l.font.color.rgb = C_LIME
    r_db_l.font.size = Pt(13)
    r_db_v = p_db.add_run()
    r_db_v.text = "Artificial Intelligence & Autonomous Systems (PS #04)"
    r_db_v.font.color.rgb = C_WHITE
    r_db_v.font.size = Pt(13)

    # =========================================================================
    # SLIDE 2: PROBLEM IDENTIFICATION
    # =========================================================================
    s2 = prs.slides[1]
    remove_shapes_by_name(s2, ['TextBox 8'])
    
    col_width = Emu(4900000)
    col_height = Emu(4500000)
    top_pos = Emu(2000000)
    
    # 3 Columns
    # Col 1: WHO IS AFFECTED
    add_hud_card(
        s2, Emu(1400000), top_pos, col_width, col_height,
        "WHO IS AFFECTED",
        [
            "MSMEs and small manufacturers seeking product compliance",
            "Consumers and jewellery buyers needing hallmark verification",
            "Students, innovators, and academic researchers",
            "BIS-related service seekers & testing laboratory clients",
            "Startups navigating mandatory quality control orders (QCOs)"
        ]
    )
    
    # Col 2: CORE PAIN POINT
    add_hud_card(
        s2, Emu(6694000), top_pos, col_width, col_height,
        "CORE PAIN POINT",
        [
            "Difficulty discovering the correct BIS standard among 20,000+ files",
            "Confusion regarding certification procedures (ISI Mark, CRS, FMCS)",
            "Lack of instant, transparent gold hallmarking & 6-digit HUID guidance",
            "Time-consuming search for nearest BIS-recognized testing laboratories",
            "Information fragmented across dozens of disconnected web portals"
        ]
    )
    
    # Col 3: CURRENT GAP
    add_hud_card(
        s2, Emu(11988000), top_pos, col_width, col_height,
        "CURRENT GAP",
        [
            "Keyword-only search engines that fail on natural language questions",
            "No conversational cross-service reasoning or intent routing",
            "Scattered service portals with zero unified conversational layer",
            "Complex regulatory jargon without verified clause-level citations",
            "Absence of offline-capable, local AI solutions for data privacy"
        ]
    )
    
    # Bottom Bar: Problem Statement Focus
    bottom_bar = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(1400000), Emu(6800000), Emu(15488000), Emu(2200000))
    bottom_bar.fill.solid()
    bottom_bar.fill.fore_color.rgb = C_CARD_BG2
    bottom_bar.line.color.rgb = C_BRIGHT
    bottom_bar.line.width = Pt(1.5)
    tf_bb = bottom_bar.text_frame
    tf_bb.word_wrap = True
    tf_bb.margin_left = Inches(0.3)
    tf_bb.margin_top = Inches(0.2)
    tf_bb.margin_right = Inches(0.3)
    
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
        "hallmarking, and complaint guidance — running entirely locally with 0 API costs and guaranteed source citations."
    )
    p_bb_body.font.name = FONT_BODY
    p_bb_body.font.size = Pt(13)
    p_bb_body.font.color.rgb = C_WHITE

    # =========================================================================
    # SLIDE 3: PROPOSED SOLUTION
    # =========================================================================
    s3 = prs.slides[2]
    remove_shapes_by_name(s3, ['TextBox 7'])
    
    # 5 Process Steps Flow
    step_width = Emu(2700000)
    step_height = Emu(2300000)
    step_gap = Emu(450000)
    step_top = Emu(2000000)
    start_left = Emu(1400000)
    
    steps = [
        ("ASK 💬", "Natural Language Query", "User asks query in plain English or Hindi via chat UI."),
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
        tf.margin_top = Inches(0.15)
        tf.vertical_anchor = MSO_ANCHOR.TOP
        
        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.name = FONT_HEADING
        p_t.font.bold = True
        p_t.font.size = Pt(14)
        p_t.font.color.rgb = C_LIME
        p_t.alignment = PP_ALIGN.CENTER
        
        p_s = tf.add_paragraph()
        p_s.text = sub
        p_s.font.name = FONT_BODY
        p_s.font.bold = True
        p_s.font.size = Pt(10.5)
        p_s.font.color.rgb = C_BRIGHT
        p_s.alignment = PP_ALIGN.CENTER
        p_s.space_after = Pt(4)
        
        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.name = FONT_BODY
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_OFFWHITE
        p_d.alignment = PP_ALIGN.CENTER
        
        # Add connecting arrow if not last
        if i < 4:
            arr_left = s_left + step_width + Emu(60000)
            arr = s3.shapes.add_textbox(arr_left, step_top + Emu(800000), step_gap - Emu(120000), Emu(600000))
            tf_a = arr.text_frame
            tf_a.margin_left = tf_a.margin_right = tf_a.margin_top = tf_a.margin_bottom = 0
            p_a = tf_a.paragraphs[0]
            p_a.text = "➔"
            p_a.font.name = 'Segoe UI Symbol'
            p_a.font.size = Pt(22)
            p_a.font.color.rgb = C_BRIGHT
            p_a.alignment = PP_ALIGN.CENTER

    # Two Lower Cards
    lower_top = Emu(4600000)
    lower_width = Emu(7500000)
    lower_height = Emu(4400000)
    
    add_hud_card(
        s3, Emu(1400000), lower_top, lower_width, lower_height,
        "Key Capabilities",
        [
            ("Standards Q&A", "Semantic RAG search over BIS standards (IS 16102, IS 14543, IS 9873)."),
            ("Certification Schemes", "Step-by-step guidance for ISI Mark, CRS, and FMCS schemes & timelines."),
            ("Instant Hallmarking", "0ms rule-based verification of gold purity (24K, 22K, 18K, 14K) and 6-digit HUID."),
            ("Lab Finder Agent", "Locates nearest BIS-recognized testing laboratories with product & state filters."),
            ("Bilingual Engine", "Native English and Hindi translation layer powered by Qwen2.5.")
        ]
    )
    
    add_hud_card(
        s3, Emu(9388000), lower_top, lower_width, lower_height,
        "Innovation Edge",
        [
            ("Zero Hallucinations", "Every response is strictly grounded with exact BIS standard & clause citations."),
            ("Transparent Agent Badges", "Live 'Answered by: [Agent]' badges verify multi-agent orchestration for judges."),
            ("100% Offline Local AI", "Runs entirely on consumer GPUs via Ollama — zero cloud bills, zero internet risk."),
            ("Deterministic Hybrid Routing", "Keyword-first dispatch eliminates LLM routing latency for maximum demo reliability."),
            ("Flagged Uncertainty", "Uncertain or out-of-scope queries are explicitly flagged rather than guessed.")
        ]
    )

    # =========================================================================
    # SLIDE 4: TECHNOLOGY STACK
    # =========================================================================
    s4 = prs.slides[3]
    remove_shapes_by_name(s4, ['TextBox 8', 'AutoShape 9', 'AutoShape 10', 'TextBox 11', 'AutoShape 12', 'AutoShape 13'])
    
    # Grid of 4 Tech Cards (2 x 2)
    card_w = Emu(7500000)
    card_h = Emu(3300000)
    r1_top = Emu(2000000)
    r2_top = Emu(5600000)
    c1_left = Emu(1400000)
    c2_left = Emu(9388000)
    
    add_hud_card(
        s4, c1_left, r1_top, card_w, card_h,
        "Core AI & Generation Engine",
        [
            ("Local LLM Runtime", "Ollama serving local models with full GPU acceleration (NVIDIA CUDA)."),
            ("Generative Model", "Qwen2.5 (7B/3B Instruct) for nuanced offline reasoning & English ↔ Hindi translation."),
            ("Embedding Model", "Nomic-Embed-Text generating 768-dimensional dense semantic embeddings."),
            ("Execution Mode", "100% offline, zero cloud API dependencies, zero recurring tokens cost.")
        ]
    )
    
    add_hud_card(
        s4, c2_left, r1_top, card_w, card_h,
        "Backend & Agentic Pipeline",
        [
            ("Web Framework", "FastAPI (Python 3.10+) serving asynchronous REST endpoints with <15ms latency."),
            ("Multi-Agent Swarm", "Modular agent pipeline (Router, Retriever, Certification, Hallmarking, Lab Finder)."),
            ("Hybrid Router", "Deterministic keyword routing for 0ms classification with LLM intent fallback."),
            ("Error Resilience", "Automatic retry handling with exponential backoff against GPU engine timeouts.")
        ]
    )
    
    add_hud_card(
        s4, c1_left, r2_top, card_w, card_h,
        "Data Architecture & Retrieval (RAG)",
        [
            ("Vector Database", "ChromaDB persistent vector store utilizing cosine similarity search."),
            ("Document Ingestion", "Custom chunking pipeline parsing markdown standards with clause metadata."),
            ("Structured Knowledge", "Optimized JSON rule stores for certification schemes, labs & gold purity."),
            ("Deterministic Rule Engine", "Zero-latency pure Python rules for HUID regex & Karat validation.")
        ]
    )
    
    add_hud_card(
        s4, c2_left, r2_top, card_w, card_h,
        "Frontend & User Experience",
        [
            ("Chat Interface", "Modern cyberpunk HUD aesthetic with responsive sidebar & conversation history."),
            ("Explainability Badges", "Dynamic visual badges proving which specialized micro-agent answered."),
            ("Standard Citations", "Interactive citation blocks linking verbatim standard clauses and scheme circulars."),
            ("Multilingual Switch", "Instant 1-click toggle between English and हिन्दी with auto-detection.")
        ]
    )

    # =========================================================================
    # SLIDE 5: FEASIBILITY & IMPACT
    # =========================================================================
    s5 = prs.slides[4]
    remove_shapes_by_name(s5, ['TextBox 7'])
    
    # 4 High Impact Cards (2 x 2)
    add_hud_card(
        s5, c1_left, r1_top, card_w, card_h,
        "Implementation Viability (Demo-Ready)",
        [
            ("Fully Operational MVP", "Complete end-to-end working software ready and demonstrated in real-time today."),
            ("Commodity Hardware", "Runs comfortably on standard 6–8GB VRAM consumer GPUs (RTX 3050/3060)."),
            ("Zero Operational Cost", "100% local inference eliminates expensive API token billing ($0 deployment cost)."),
            ("Guaranteed Demo Uptime", "Zero reliance on external internet connections or third-party cloud availability.")
        ]
    )
    
    add_hud_card(
        s5, c2_left, r1_top, card_w, card_h,
        "Technical Foundation & Scalability",
        [
            ("Modular Micro-Agents", "Decoupled architecture enables hot-plugging new standards and agent services."),
            ("Grounded RAG Pipeline", "Strict citation anchoring eliminates hallucinations and prevents legal misinformation."),
            ("Sub-Second Latency", "Deterministic rule engines deliver instantaneous responses for hallmarking & labs."),
            ("Production-Ready Schema", "Pydantic validated data structures ensure seamless future BIS CARE API sync.")
        ]
    )
    
    add_hud_card(
        s5, c1_left, r2_top, card_w, card_h,
        "Measurable Outcomes & Impact",
        [
            ("98% Time Reduction", "Compresses compliance research from 3–5 hours across portals to <5 seconds."),
            ("Empowering 63M+ MSMEs", "Democratizes complex regulatory access, saving lakhs in third-party consultancy."),
            ("Consumer Fraud Protection", "Instant 6-digit HUID format checks shield buyers from counterfeit jewellery."),
            ("Linguistic Inclusion", "Hindi support empowers Tier-2 and rural artisans to achieve formal BIS certification.")
        ]
    )
    
    add_hud_card(
        s5, c2_left, r2_top, card_w, card_h,
        "Conclusion & Novelty (Infothon 7.0)",
        [
            ("Full Spectrum Coverage", "The only platform unifying all 8 core BIS capabilities into one conversational interface."),
            ("Transparent & Auditable", "Every synthesized answer includes auditable source standard clauses and agent badges."),
            ("National Scalability", "Extensible to all 20,000+ Indian Standards covering 15 core national industry sectors."),
            ("Autonomous Vision", "Directly fulfills the theme: 'Architecting an Autonomous Tomorrow' for Indian regulatory compliance.")
        ]
    )

    # =========================================================================
    # SLIDE 6: SYSTEM ARCHITECTURE & DEMO WORKFLOW
    # =========================================================================
    s6 = prs.slides[5]
    remove_shapes_by_name(s6, ['TextBox 7'])
    
    # Update title from "SUBMISSION GUIDELINES" to "SYSTEM ARCHITECTURE & DEMO WORKFLOW"
    for s in s6.shapes:
        if s.name == 'TextBox 5' and s.has_text_frame:
            s.text_frame.text = "SYSTEM ARCHITECTURE & DEMO WORKFLOW"
            s.text_frame.paragraphs[0].font.name = FONT_TITLE
            s.text_frame.paragraphs[0].font.size = Pt(45)
            s.text_frame.paragraphs[0].font.color.rgb = C_LIME
    
    # Left Box: Multi-Agent Architecture Diagram Box
    arch_w = Emu(7800000)
    arch_h = Emu(6800000)
    
    add_hud_card(
        s6, Emu(1400000), Emu(2000000), arch_w, arch_h,
        "Multi-Agent Swarm Architecture",
        [
            ("User Layer", "Web Browser Chat Interface (English / हिन्दी toggles)."),
            ("API Gateway", "FastAPI asynchronous server managing sessions & requests."),
            ("Intelligent Router", "Analyzes query syntax & dispatches to specialized agent:"),
            ("  • Retriever Agent (RAG)", "Cosine similarity search over ChromaDB + nomic-embed-text."),
            ("  • Certification Agent", "Maps products to ISI / CRS / FMCS schemes & application timelines."),
            ("  • Consumer Agent", "Plain-language explanations linked with BIS CARE app & 1915 helpline."),
            ("  • Hallmarking Agent", "0-latency rule checks for 24K/22K/18K gold purity & 6-digit HUID."),
            ("  • Lab Finder Agent", "Geo-directory filtering recognized testing laboratories by domain."),
            ("Local AI Synthesis", "Qwen2.5-7B Instruct synthesizes final grounded answer on GPU."),
            ("Explainable Response", "Formatted response delivered with Agent Badge & verified citations.")
        ]
    )
    
    # Right Box: Live Demo Highlights & Hackathon Scenarios
    demo_w = Emu(7388000)
    demo_h = Emu(6800000)
    
    add_hud_card(
        s6, Emu(9500000), Emu(2000000), demo_w, demo_h,
        "Live Demo Validation Scenarios",
        [
            ("Scenario 1: MSME Industry Query", "LED Bulb manufacturer asks: 'How do I certify my LED lights?'\n➔ Certification Agent explains CRS scheme with IS 16102 standard citation."),
            ("Scenario 2: Consumer Protection in Hindi", "User asks: '22 कैरेट सोने पर क्या हॉलमार्क होना चाहिए?'\n➔ Hallmarking Agent responds in Hindi with 916 purity mark and HUID verification."),
            ("Scenario 3: Testing Lab Locator", "User asks: 'Where can I test packaged drinking water in Karnataka?'\n➔ Lab Finder Agent returns accredited labs for IS 14543 with contact data."),
            ("Scenario 4: Visual Agent Attribution", "Every answer displays a live badge: 'Answered by: [Agent Name]'\n➔ Proves autonomous routing live to hackathon judges with zero fake mockups."),
            ("Future Roadmap", "Direct BIS CARE API sync, voice interface for rural artisans, & expansion to 20,000+ national standards.")
        ]
    )

    out_file = r'c:\STAR WARS\complybot\ComplyBot_Infothon_7.0_Final.pptx'
    prs.save(out_file)
    print(f'Successfully saved presentation to: {out_file}')

    # Also save to user's Downloads
    downloads_out = os.path.expanduser(r'~\Downloads\ComplyBot_Infothon_7.0_Final.pptx')
    prs.save(downloads_out)
    print(f'Successfully copied presentation to: {downloads_out}')

if __name__ == '__main__':
    build_presentation()
