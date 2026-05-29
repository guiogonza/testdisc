"""
Funciones de generación de reportes PDF para todas las pruebas psicométricas.
"""
import os
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime, timedelta, timezone as _tz_mod

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from constants import *
from analysis import (
    analyze_disc_aptitude,
    analyze_valanti_aptitude,
    analyze_wpi_aptitude,
    analyze_eri_aptitude,
    analyze_talent_map_match,
)

_GMT5 = _tz_mod(timedelta(hours=-5))


def _now_gmt5():
    return datetime.now(_GMT5)


def _build_hesego_header(codigo, version="02", fecha="30-01-24", titulo="EVALUACIÓN DESEMPEÑO"):
    """Construye el encabezado institucional HESEGO para los PDFs de desempeño."""
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    if os.path.exists(logo_path):
        logo_cell = Image(logo_path, width=110, height=55)
    else:
        logo_cell = Paragraph(
            "<b>HESEGO</b><br/>Ingeniería S.A.S",
            ParagraphStyle("_HLogo", fontName="Helvetica-Bold", fontSize=10, alignment=1, leading=14),
        )

    center_style = ParagraphStyle(
        "_HCenter", fontName="Helvetica-Bold", fontSize=11, alignment=1, leading=16
    )
    center_cell = Paragraph(f"FORMATO<br/><br/>{titulo}", center_style)

    right_data = [
        ["CÓDIGO:", codigo],
        ["VERSIÓN:", version],
        ["FECHA:", fecha],
    ]
    right_table = Table(right_data, colWidths=[62, 78])
    right_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    header_table = Table([[logo_cell, center_cell, right_table]], colWidths=[130, 252, 140])
    header_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
        ("LINEAFTER", (0, 0), (1, -1), 0.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    return [header_table, Spacer(1, 14)]


# =========================================================================
# DISC
# =========================================================================

def generate_disc_pdf(candidate, normalized, relative, fig, session_id, completed_at=None, analysis=None,
                      behavioral_styles=None, temperament=None, mega_summary=None, styles_fig=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Justify", alignment=4, leading=14))
    styles.add(ParagraphStyle(name="SmallBold", parent=styles["Normal"], fontSize=9, leading=12, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9, leading=12))
    story = []
    story.append(Paragraph("Evaluación de Personalidad DISC - Reporte", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>ID Evaluación:</b> {session_id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Candidato:</b> {candidate['name']} (Cédula: {candidate['cedula']})", styles["Normal"]))
    
    if completed_at:
        try:
            fecha_obj = datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
            fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
        except Exception:
            fecha_str = completed_at
    else:
        fecha_str = _now_gmt5().strftime('%d/%m/%Y %H:%M')
    
    story.append(Paragraph(f"<b>Cargo:</b> {candidate.get('position','N/A')} | <b>Fecha de Presentación:</b> {fecha_str}", styles["Normal"]))
    
    if analysis is None:
        analysis = analyze_disc_aptitude(normalized, relative)
    
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>RESULTADO DE APTITUD: {analysis['aptitude_level']} ({analysis['aptitude_score']}/100)</b>", styles["Heading2"]))
    story.append(Paragraph(f"{analysis['aptitude_desc']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Perfil:</b> {analysis['profile_name']} ({analysis['dominant_name']} + {analysis['secondary_name']})", styles["Normal"]))
    story.append(Spacer(1, 12))
    
    data = [["Estilo", "Puntaje Normalizado", "Porcentaje Relativo"]]
    for s in "DISC":
        data.append([s, f"{normalized[s]:.1f}%", f"{relative[s]:.1f}%"])
    t = Table(data, colWidths=[100, 150, 150])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))
    if fig:
        img_buf = BytesIO()
        fig.savefig(img_buf, format="png", dpi=150, bbox_inches="tight")
        img_buf.seek(0)
        story.append(Image(img_buf, width=280, height=280))
    
    story.append(PageBreak())
    story.append(Paragraph("Análisis y Recomendaciones", styles["Heading1"]))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("FORTALEZAS DEL CANDIDATO", styles["Heading2"]))
    for f in analysis.get('fortalezas', []):
        story.append(Paragraph(f"• {f}", styles["Small"]))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("ALERTAS Y ÁREAS DE ATENCIÓN", styles["Heading2"]))
    for a in analysis.get('alertas', []):
        story.append(Paragraph(f"• {a}", styles["Small"]))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("RECOMENDACIONES", styles["Heading2"]))
    for r in analysis.get('recomendaciones', []):
        story.append(Paragraph(f"• {r}", styles["Small"]))
    story.append(Spacer(1, 10))
    
    if analysis.get('ideal_para'):
        story.append(Paragraph("ROLES IDEALES", styles["Heading2"]))
        for r in analysis['ideal_para']:
            story.append(Paragraph(f"• {r}", styles["Small"]))
        story.append(Spacer(1, 10))
    
    if analysis.get('cuidado_en'):
        story.append(Paragraph("PRECAUCIÓN EN ROLES DE", styles["Heading2"]))
        for r in analysis['cuidado_en']:
            story.append(Paragraph(f"• {r}", styles["Small"]))

    if mega_summary:
        story.append(PageBreak())
        story.append(Paragraph("Resumen Conductual Detallado", styles["Heading1"]))
        story.append(Spacer(1, 8))
        temperament_style = ParagraphStyle(
            "TemperamentSummary",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            wordWrap="CJK",
        )
        if temperament:
            story.append(Paragraph(
                f"<b>Temperamento:</b><br/>{temperament['label'].capitalize()} - {temperament['description']}",
                temperament_style
            ))
            story.append(Spacer(1, 8))
        summary_label_style = ParagraphStyle(
            "SummaryLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#1e40af"),
        )
        summary_text_style = ParagraphStyle(
            "SummaryText",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
        )

        data_rows = [["Dimensión", "Descripción Conductual"]]
        for label, text in mega_summary.items():
            data_rows.append([
                Paragraph(label, summary_label_style),
                Paragraph(text, summary_text_style),
            ])
        t_sum = Table(data_rows, colWidths=[130, 360])
        t_sum.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t_sum)

    if behavioral_styles:
        story.append(PageBreak())
        story.append(Paragraph("9 Estilos Conductuales Derivados", styles["Heading1"]))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "Puntajes derivados matemáticamente del perfil DISC. Cada estilo presenta 4 sub-dimensiones "
            "mapeadas a Dominancia (D), Influencia (I), Estabilidad (S) y Cumplimiento (C).",
            styles["Small"]
        ))
        story.append(Spacer(1, 10))

        if styles_fig:
            try:
                styles_buf = BytesIO()
                styles_fig.savefig(styles_buf, format="png", dpi=130, bbox_inches="tight")
                styles_buf.seek(0)
                story.append(Image(styles_buf, width=480, height=len(behavioral_styles) * 55 + 30))
            except Exception:
                pass
        
        story.append(Spacer(1, 12))
        for style_name, style_data in behavioral_styles.items():
            story.append(Paragraph(f"<b>{style_name}</b>", styles["Heading3"]))
            sub_data = [["Sub-dimensión", "Puntaje", "Descripción"]]
            for sub_name, sub_val in style_data["subs"].items():
                sub_data.append([sub_name, str(sub_val), style_data["desc"][sub_name]])
            t_sub = Table(sub_data, colWidths=[110, 45, 335])
            t_sub.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F9FAFB"), colors.white]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(t_sub)
            story.append(Spacer(1, 8))

    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Este reporte es generado automáticamente como herramienta de apoyo para Recursos Humanos. Los resultados deben complementarse con entrevistas y otras evaluaciones.</i>", styles["Small"]))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


# =========================================================================
# VALANTI
# =========================================================================

def generate_valanti_pdf(candidate, direct, standard, radar_fig, session_id, completed_at=None, analysis=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Justify", alignment=4, leading=14))
    styles.add(ParagraphStyle(name="SmallBold", parent=styles["Normal"], fontSize=9, leading=12, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9, leading=12))
    story = []
    story.append(Paragraph("Cuestionario VALANTI - Reporte de Resultados", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>ID Evaluación:</b> {session_id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Candidato:</b> {candidate['name']} (Cédula: {candidate['cedula']})", styles["Normal"]))
    
    if completed_at:
        try:
            fecha_obj = datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
            fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
        except Exception:
            fecha_str = completed_at
    else:
        fecha_str = _now_gmt5().strftime('%d/%m/%Y %H:%M')
    
    story.append(Paragraph(f"<b>Cargo:</b> {candidate.get('position','N/A')} | <b>Fecha de Presentación:</b> {fecha_str}", styles["Normal"]))
    
    if analysis is None:
        analysis = analyze_valanti_aptitude(standard)
    
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>RESULTADO DE APTITUD: {analysis['aptitude_level']} ({analysis['aptitude_score']}/100)</b>", styles["Heading2"]))
    story.append(Paragraph(f"{analysis['aptitude_desc']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Valor más fuerte:</b> {analysis['strongest_value']} (T={analysis['strongest_score']}) | <b>Valor más bajo:</b> {analysis['weakest_value']} (T={analysis['weakest_score']})", styles["Normal"]))
    story.append(Spacer(1, 12))
    
    data = [["Valor", "Puntaje Directo", "Puntaje Estándar (T)"]]
    for trait in VALANTI_TRAITS:
        data.append([trait, str(direct[trait]), str(standard[trait])])
    t = Table(data, colWidths=[120, 120, 150])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))
    if radar_fig:
        img_buf = BytesIO()
        radar_fig.savefig(img_buf, format="png", dpi=150, bbox_inches="tight")
        img_buf.seek(0)
        story.append(Image(img_buf, width=300, height=300))
    
    story.append(PageBreak())
    story.append(Paragraph("Análisis y Recomendaciones", styles["Heading1"]))
    story.append(Spacer(1, 10))
    
    if analysis.get('fortalezas'):
        story.append(Paragraph("FORTALEZAS VALORALES", styles["Heading2"]))
        for f in analysis['fortalezas']:
            story.append(Paragraph(f"• {f}", styles["Small"]))
        story.append(Spacer(1, 10))
    
    if analysis.get('alertas'):
        story.append(Paragraph("ALERTAS Y ÁREAS DE ATENCIÓN", styles["Heading2"]))
        for a in analysis['alertas']:
            story.append(Paragraph(f"• {a}", styles["Small"]))
        story.append(Spacer(1, 10))
    
    if analysis.get('recomendaciones'):
        story.append(Paragraph("RECOMENDACIONES", styles["Heading2"]))
        for r in analysis['recomendaciones']:
            r_clean = r.replace("**", "")
            story.append(Paragraph(f"• {r_clean}", styles["Small"]))
        story.append(Spacer(1, 10))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Este reporte es generado automáticamente como herramienta de apoyo para Recursos Humanos. Los resultados deben complementarse con entrevistas y otras evaluaciones.</i>", styles["Small"]))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


# =========================================================================
# WPI
# =========================================================================

def generate_wpi_pdf(candidate, raw_scores, normalized, radar_fig, session_id, completed_at=None, analysis=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Justify", alignment=4, leading=14))
    styles.add(ParagraphStyle(name="SmallBold", parent=styles["Normal"], fontSize=9, leading=12, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9, leading=12))
    story = []
    
    story.append(Paragraph("WPI - Work Personality Index", styles["Title"]))
    story.append(Paragraph("Evaluación de Personalidad Laboral", styles["Heading2"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>ID Evaluación:</b> {session_id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Candidato:</b> {candidate['name']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Cédula:</b> {candidate['cedula']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Cargo:</b> {candidate.get('position', 'N/A')}", styles["Normal"]))
    
    if completed_at:
        try:
            fecha_obj = datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
            fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
        except Exception:
            fecha_str = completed_at
    else:
        fecha_str = _now_gmt5().strftime('%d/%m/%Y %H:%M')
    
    story.append(Paragraph(f"<b>Fecha de Presentación:</b> {fecha_str}", styles["Normal"]))
    story.append(Spacer(1, 16))
    
    if analysis is None:
        analysis = analyze_wpi_aptitude(normalized)
    
    story.append(Paragraph(
        f"<b>RESULTADO: {analysis['aptitude_level']} ({analysis['aptitude_score']}/100)</b>", 
        styles["Heading2"]
    ))
    story.append(Paragraph(f"{analysis['aptitude_desc']}", styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"<b>Dimensión más fuerte:</b> {analysis['strongest_dimension']} "
        f"({int(analysis['strongest_score'])}/100) | "
        f"<b>Dimensión a desarrollar:</b> {analysis['weakest_dimension']} "
        f"({int(analysis['weakest_score'])}/100)",
        styles["Normal"]
    ))
    story.append(Paragraph(f"<b>Promedio general:</b> {analysis['average_score']}/100", styles["Normal"]))
    story.append(Spacer(1, 16))
    
    story.append(Paragraph("Puntajes por Dimensión", styles["Heading2"]))
    story.append(Spacer(1, 8))
    
    data = [["Dimensión", "Puntaje Directo", "Puntaje Normalizado (0-100)", "Nivel"]]
    for dim in WPI_DIMENSIONS:
        nivel = "Alto" if normalized[dim] >= 70 else ("Medio" if normalized[dim] >= 45 else "Bajo")
        data.append([dim, str(int(raw_scores[dim])), f"{int(normalized[dim])}/100", nivel])
    
    t = Table(data, colWidths=[140, 80, 130, 60])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))
    
    if radar_fig:
        img_buf = BytesIO()
        radar_fig.savefig(img_buf, format="png", dpi=150, bbox_inches="tight")
        img_buf.seek(0)
        story.append(Image(img_buf, width=320, height=320))
    
    story.append(PageBreak())
    story.append(Paragraph("Análisis Detallado y Recomendaciones", styles["Heading1"]))
    story.append(Spacer(1, 12))
    
    if analysis.get('fortalezas'):
        story.append(Paragraph("✅ FORTALEZAS DESTACADAS", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for f in analysis['fortalezas']:
            story.append(Paragraph(f"• {f.replace('**', '')}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    if analysis.get('alertas'):
        story.append(Paragraph("⚠️ ÁREAS DE ATENCIÓN", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for a in analysis['alertas']:
            story.append(Paragraph(f"• {a.replace('**', '').replace('⚠️ ', '')}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    if analysis.get('ideal_para'):
        story.append(Paragraph("🎯 ROLES IDEALES PARA EL CANDIDATO", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for role in analysis['ideal_para']:
            story.append(Paragraph(f"• {role}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    if analysis.get('avoid_roles'):
        story.append(Paragraph("⛔ ROLES NO RECOMENDADOS", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for role in analysis['avoid_roles']:
            story.append(Paragraph(f"• {role}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    if analysis.get('recomendaciones'):
        story.append(Paragraph("💡 RECOMENDACIONES ESPECÍFICAS", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for r in analysis['recomendaciones']:
            story.append(Paragraph(f"• {r.replace('**', '')}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    story.append(PageBreak())
    story.append(Paragraph("Descripción de las Dimensiones del WPI", styles["Heading1"]))
    story.append(Spacer(1, 12))
    
    for dim in WPI_DIMENSIONS:
        score = normalized[dim]
        desc_info = WPI_DESCRIPTIONS[dim]
        if score >= 70:
            level_text, desc_text = "ALTO", desc_info["high"]
        elif score >= 45:
            level_text, desc_text = "MEDIO", desc_info["medium"]
        else:
            level_text, desc_text = "BAJO", desc_info["low"]
        
        story.append(Paragraph(
            f"<b>{desc_info['title']}</b> - Nivel: {level_text} ({int(score)}/100)",
            styles["Heading3"]
        ))
        story.append(Paragraph(desc_text, styles["Small"]))
        story.append(Spacer(1, 8))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<i>Este reporte es generado automáticamente como herramienta de apoyo para "
        "Recursos Humanos. Los resultados deben complementarse con entrevistas, "
        "referencias laborales y otras evaluaciones pertinentes.</i>",
        styles["Small"]
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


# =========================================================================
# ERI
# =========================================================================

def generate_eri_pdf(candidate, raw_scores, normalized, radar_fig, session_id, completed_at=None, analysis=None, validity_score=None, validity_flags=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Justify", alignment=4, leading=14))
    styles.add(ParagraphStyle(name="SmallBold", parent=styles["Normal"], fontSize=9, leading=12, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="AlertBold", parent=styles["Normal"], fontSize=11, leading=14, fontName="Helvetica-Bold", textColor=colors.HexColor("#DC2626")))
    story = []
    
    story.append(Paragraph("ERI - Evaluación de Riesgo e Integridad", styles["Title"]))
    story.append(Paragraph("Screening de Confiabilidad y Comportamiento Laboral", styles["Heading2"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>ID Evaluación:</b> {session_id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Candidato:</b> {candidate['name']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Cédula:</b> {candidate['cedula']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Cargo:</b> {candidate.get('position', 'N/A')}", styles["Normal"]))
    
    if completed_at:
        try:
            fecha_obj = datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
            fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
        except Exception:
            fecha_str = completed_at
    else:
        fecha_str = _now_gmt5().strftime('%d/%m/%Y %H:%M')
    
    story.append(Paragraph(f"<b>Fecha de Presentación:</b> {fecha_str}", styles["Normal"]))
    story.append(Spacer(1, 16))
    
    if analysis is None:
        if validity_score is None:
            validity_score = ERI_VALIDITY_QUESTIONS_COUNT
        if validity_flags is None:
            validity_flags = []
        analysis = analyze_eri_aptitude(normalized, validity_score, validity_flags)
    
    if analysis.get('validity_warning'):
        story.append(Paragraph("⚠️ ALERTA DE VALIDEZ DEL TEST", styles["AlertBold"]))
        story.append(Paragraph(analysis['validity_warning'], styles["Small"]))
        story.append(Spacer(1, 12))
    
    risk_color_map = {
        "#10B981": "✅ BAJO RIESGO",
        "#F59E0B": "⚠️ RIESGO MODERADO",
        "#EF4444": "🚫 ALTO RIESGO"
    }
    risk_banner = risk_color_map.get(analysis['risk_color'], analysis['risk_level'])
    
    story.append(Paragraph(
        f"<b>RESULTADO: {risk_banner} ({analysis['risk_score']:.1f}/100)</b>", 
        styles["Heading2"]
    ))
    story.append(Paragraph(f"{analysis['risk_desc']}", styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"<b>Dimensión de menor riesgo:</b> {analysis['safest_dimension']} "
        f"({int(analysis['safest_score'])}/100) | "
        f"<b>Dimensión de mayor riesgo:</b> {analysis['riskiest_dimension']} "
        f"({int(analysis['riskiest_score'])}/100)",
        styles["Normal"]
    ))
    story.append(Paragraph(
        f"<b>Promedio de riesgo:</b> {analysis['average_score']:.1f}/100 (Puntajes altos = BAJO riesgo)",
        styles["Normal"]
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>Decisión Recomendada:</b> {analysis['hiring_decision']}", styles["Heading3"]))
    story.append(Spacer(1, 16))
    
    story.append(Paragraph("Puntajes por Dimensión de Riesgo", styles["Heading2"]))
    story.append(Spacer(1, 8))
    
    data = [["Dimensión", "Puntaje", "Nivel de Riesgo", "Estado"]]
    for dim in ERI_DIMENSIONS:
        score = normalized[dim]
        if score >= ERI_RISK_THRESHOLDS["low_risk"]:
            nivel, estado = "Bajo Riesgo", "✅"
        elif score >= ERI_RISK_THRESHOLDS["medium_risk"]:
            nivel, estado = "Riesgo Moderado", "⚠️"
        else:
            nivel, estado = "Alto Riesgo", "🚨"
        data.append([dim, f"{int(score)}/100", nivel, estado])
    
    t = Table(data, colWidths=[140, 70, 110, 50])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DC2626")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))
    
    if radar_fig:
        img_buf = BytesIO()
        radar_fig.savefig(img_buf, format="png", dpi=150, bbox_inches="tight")
        img_buf.seek(0)
        story.append(Image(img_buf, width=350, height=350))
    
    story.append(PageBreak())
    story.append(Paragraph("Análisis Detallado y Recomendaciones de Contratación", styles["Heading1"]))
    story.append(Spacer(1, 12))
    
    if analysis.get('fortalezas'):
        story.append(Paragraph("✅ ASPECTOS POSITIVOS (Bajo Riesgo)", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for f in analysis['fortalezas']:
            story.append(Paragraph(f"• {f.replace('**', '')}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    if analysis.get('alertas'):
        story.append(Paragraph("🚨 SEÑALES DE ALERTA Y FACTORES DE RIESGO", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for a in analysis['alertas']:
            story.append(Paragraph(f"• {a.replace('**', '').replace('⚠️ ', '').replace('🚨 ', '')}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    if analysis.get('recomendaciones'):
        story.append(Paragraph("💼 RECOMENDACIONES DE CONTRATACIÓN", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for r in analysis['recomendaciones']:
            story.append(Paragraph(f"{r.replace('**', '')}", styles["Small"]))
        story.append(Spacer(1, 8))
    
    if validity_flags and len(validity_flags) > 0:
        story.append(PageBreak())
        story.append(Paragraph("⚠️ DETALLES DE VALIDEZ DEL TEST", styles["Heading2"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            f"Se detectaron {len(validity_flags)} respuestas poco realistas en preguntas de validez.",
            styles["Small"]
        ))
        story.append(Spacer(1, 8))
        story.append(Paragraph("Ejemplos de respuestas sospechosas:", styles["SmallBold"]))
        story.append(Spacer(1, 4))
        for flag in validity_flags[:5]:
            story.append(Paragraph(f"• {flag}", styles["Small"]))
        if len(validity_flags) > 5:
            story.append(Paragraph(f"... y {len(validity_flags) - 5} más.", styles["Small"]))
        story.append(Spacer(1, 12))
    
    story.append(PageBreak())
    story.append(Paragraph("Descripción de las Dimensiones del ERI", styles["Heading1"]))
    story.append(Spacer(1, 12))
    
    for dim in ERI_DIMENSIONS:
        score = normalized[dim]
        desc_info = ERI_DESCRIPTIONS[dim]
        if score >= ERI_RISK_THRESHOLDS["low_risk"]:
            level_text, desc_text = "BAJO RIESGO ✅", desc_info["low_risk"]
        elif score >= ERI_RISK_THRESHOLDS["medium_risk"]:
            level_text, desc_text = "RIESGO MODERADO ⚠️", desc_info["medium_risk"]
        else:
            level_text, desc_text = "ALTO RIESGO 🚨", desc_info["high_risk"]
        
        story.append(Paragraph(f"<b>{desc_info['title']}</b> - {level_text} ({int(score)}/100)", styles["Heading3"]))
        story.append(Paragraph(desc_text, styles["Small"]))
        story.append(Spacer(1, 8))
    
    story.append(PageBreak())
    story.append(Paragraph("Interpretación de Umbrales de Riesgo", styles["Heading1"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>✅ BAJO RIESGO (66-100 puntos):</b>", styles["Heading3"]))
    story.append(Paragraph("Sin indicadores significativos de riesgo. El candidato muestra actitudes y comportamientos compatibles con un desempeño confiable y ético en el entorno laboral.", styles["Small"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>⚠️ RIESGO MODERADO (41-65 puntos):</b>", styles["Heading3"]))
    story.append(Paragraph("Señales de alerta moderadas. Se recomienda profundizar con entrevistas enfocadas, referencias laborales exhaustivas y período de prueba con supervisión cercana.", styles["Small"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>🚨 ALTO RIESGO (0-40 puntos):</b>", styles["Heading3"]))
    story.append(Paragraph("Múltiples indicadores de riesgo significativo. La contratación representa riesgo elevado para la organización. Se recomienda NO CONTRATAR o requerir evaluación psicológica profesional adicional.", styles["Small"]))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Limitaciones y Consideraciones Importantes", styles["Heading2"]))
    story.append(Spacer(1, 8))
    for item in [
        "• Este test es una herramienta de SCREENING, no un diagnóstico psicológico definitivo.",
        "• Los resultados deben complementarse con: entrevistas conductuales (STAR), referencias laborales verificables, verificación de antecedentes penales y laborales.",
        "• Ningún test psicométrico predice el comportamiento futuro con 100% de certeza.",
        "• En casos de alto riesgo en dimensiones críticas, se recomienda evaluación por psicólogo organizacional certificado.",
        "• Este reporte es CONFIDENCIAL y debe manejarse según políticas de protección de datos.",
    ]:
        story.append(Paragraph(item, styles["Small"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<i>Este reporte es generado automáticamente como herramienta de apoyo para Recursos Humanos en procesos de selección. Los resultados deben ser interpretados por personal capacitado y complementados con otras fuentes de información.</i>",
        styles["Small"]
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


# =========================================================================
# TALENT MAP
# =========================================================================

def generate_talent_map_pdf(candidate, raw_scores, normalized, radar_fig, session_id, completed_at=None, analysis=None, job_profile_name=None, comparison_fig=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Justify", alignment=4, leading=14))
    styles.add(ParagraphStyle(name="SmallBold", parent=styles["Normal"], fontSize=9, leading=12, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="MatchHighlight", parent=styles["Normal"], fontSize=13, leading=16, fontName="Helvetica-Bold", textColor=colors.HexColor("#1E40AF")))
    story = []
    
    story.append(Paragraph("Talent Map - Mapeo de Competencias y Talentos", styles["Title"]))
    story.append(Paragraph("Evaluación de 8 Competencias Universales", styles["Heading2"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>ID Evaluación:</b> {session_id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Candidato:</b> {candidate['name']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Cédula:</b> {candidate['cedula']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Cargo Evaluado:</b> {candidate.get('position', 'N/A')}", styles["Normal"]))
    
    if completed_at:
        try:
            fecha_obj = datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
            fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
        except Exception:
            fecha_str = completed_at
    else:
        fecha_str = _now_gmt5().strftime('%d/%m/%Y %H:%M')
    
    story.append(Paragraph(f"<b>Fecha de Presentación:</b> {fecha_str}", styles["Normal"]))
    story.append(Spacer(1, 16))
    
    if analysis is None:
        analysis = analyze_talent_map_match(normalized, job_profile_name)
    
    story.append(Paragraph(
        f"<b>PERFIL DE COMPETENCIAS: Promedio {analysis['average_score']:.1f}/100</b>", 
        styles["Heading2"]
    ))
    story.append(Paragraph(
        f"<b>Competencia más fuerte:</b> {analysis['strongest_competency']} "
        f"({int(analysis['strongest_score'])}/100) | "
        f"<b>Área de mayor desarrollo:</b> {analysis['weakest_competency']} "
        f"({int(analysis['weakest_score'])}/100)",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))
    
    if analysis.get('match_analysis'):
        match = analysis['match_analysis']
        story.append(Paragraph(f"{match['match_label']}: {match['match_percentage']:.1f}%", styles["MatchHighlight"]))
        story.append(Paragraph(f"<b>Perfil de Puesto:</b> {match['job_emoji']} {match['job_profile']} - {match['job_description']}", styles["Normal"]))
        story.append(Paragraph(f"<b>Evaluación:</b> {match['match_desc']}", styles["Normal"]))
        story.append(Spacer(1, 16))
    else:
        story.append(Spacer(1, 12))
    
    story.append(Paragraph("Puntajes por Competencia", styles["Heading2"]))
    story.append(Spacer(1, 8))
    
    data = [["Competencia", "Puntaje", "Nivel", "Estado"]]
    for comp in TALENT_MAP_COMPETENCIES:
        score = normalized[comp]
        if score >= 75:
            nivel, estado = "Alto", "🌟"
        elif score >= 50:
            nivel, estado = "Medio", "👍"
        else:
            nivel, estado = "En Desarrollo", "📈"
        data.append([comp, f"{int(score)}/100", nivel, estado])
    
    t = Table(data, colWidths=[140, 70, 90, 50])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))
    
    if radar_fig:
        img_buf = BytesIO()
        radar_fig.savefig(img_buf, format="png", dpi=150, bbox_inches="tight")
        img_buf.seek(0)
        story.append(Image(img_buf, width=350, height=350))
    
    story.append(PageBreak())
    story.append(Paragraph("Análisis Detallado de Competencias", styles["Heading1"]))
    story.append(Spacer(1, 12))
    
    if analysis.get('fortalezas'):
        story.append(Paragraph("🌟 FORTALEZAS CLAVE", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for f in analysis['fortalezas']:
            story.append(Paragraph(f"• {f.replace('**', '')}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    if analysis.get('areas_desarrollo'):
        story.append(Paragraph("📈 ÁREAS DE DESARROLLO", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for a in analysis['areas_desarrollo']:
            story.append(Paragraph(f"• {a.replace('**', '')}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    if analysis.get('match_analysis'):
        match = analysis['match_analysis']
        story.append(Paragraph(f"🎯 ANÁLISIS DE MATCH CON {match['job_profile'].upper()}", styles["Heading2"]))
        story.append(Spacer(1, 8))
        if match.get('match_strengths'):
            story.append(Paragraph("<b>✅ Competencias que EXCEDEN el perfil:</b>", styles["SmallBold"]))
            story.append(Spacer(1, 4))
            for s in match['match_strengths']:
                story.append(Paragraph(f"• {s.replace('**', '')}", styles["Small"]))
            story.append(Spacer(1, 8))
        if match.get('match_gaps'):
            story.append(Paragraph("<b>⚠️ Brechas a cerrar:</b>", styles["SmallBold"]))
            story.append(Spacer(1, 4))
            for g in match['match_gaps']:
                story.append(Paragraph(f"• {g.replace('**', '')}", styles["Small"]))
            story.append(Spacer(1, 12))
    
    if comparison_fig:
        story.append(PageBreak())
        story.append(Paragraph("Análisis de Brechas de Competencia", styles["Heading1"]))
        story.append(Spacer(1, 12))
        img_buf = BytesIO()
        comparison_fig.savefig(img_buf, format="png", dpi=150, bbox_inches="tight")
        img_buf.seek(0)
        story.append(Image(img_buf, width=500, height=420))
    
    story.append(PageBreak())
    story.append(Paragraph("💼 Recomendaciones y Plan de Desarrollo", styles["Heading1"]))
    story.append(Spacer(1, 12))
    if analysis.get('recomendaciones'):
        for r in analysis['recomendaciones']:
            story.append(Paragraph(f"{r.replace('**', '')}", styles["Small"]))
            story.append(Spacer(1, 6))
    
    story.append(PageBreak())
    story.append(Paragraph("Descripción de las 8 Competencias Evaluadas", styles["Heading1"]))
    story.append(Spacer(1, 12))
    for comp in TALENT_MAP_COMPETENCIES:
        score = normalized[comp]
        desc_info = TALENT_MAP_DESCRIPTIONS[comp]
        if score >= 75:
            level_text, desc_text = "ALTO 🌟", desc_info["high"]
        elif score >= 50:
            level_text, desc_text = "MEDIO 👍", desc_info["medium"]
        else:
            level_text, desc_text = "EN DESARROLLO 📈", desc_info["low"]
        story.append(Paragraph(f"<b>{desc_info['title']}</b> - {level_text} ({int(score)}/100)", styles["Heading3"]))
        story.append(Paragraph(desc_text, styles["Small"]))
        story.append(Spacer(1, 8))
    
    story.append(PageBreak())
    story.append(Paragraph("Perfiles de Puestos de Referencia", styles["Heading1"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("El sistema incluye perfiles de referencia (benchmarks) para los siguientes puestos:", styles["Normal"]))
    story.append(Spacer(1, 8))
    for job_name, job_info in TALENT_MAP_JOB_PROFILES.items():
        story.append(Paragraph(f"<b>{job_info['emoji']} {job_name}:</b> {job_info['descripcion']}", styles["Small"]))
        story.append(Spacer(1, 4))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<i>Este reporte es generado automáticamente como herramienta de apoyo para Recursos Humanos en procesos de selección y desarrollo. Los resultados deben ser interpretados por personal capacitado y complementados con entrevistas, evaluaciones de desempeño y otras fuentes de información.</i>",
        styles["Small"]
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


# =========================================================================
# DESEMPEÑO
# =========================================================================

def generate_desempeno_pdf(candidate, rendimiento_scores, potencial_scores, radar_fig, bars_fig, 
                           session_id, completed_at=None, analysis=None, evaluador_nombre=None, iniciativas=None):
    """Genera PDF de Evaluación de Desempeño."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='DTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor("#1E40AF"), alignment=1, spaceAfter=14))
    styles.add(ParagraphStyle(name='SubTitle', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor("#374151"), spaceAfter=10))
    styles.add(ParagraphStyle(name='DSmall', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor("#6B7280")))
    styles.add(ParagraphStyle(name='ListItem', parent=styles['Normal'], fontSize=10, leftIndent=20, spaceAfter=6))
    
    story = []
    story.extend(_build_hesego_header("FO-GH-40", version="02", fecha="30-01-24"))
    story.append(Paragraph(f"<b>Colaborador Evaluado:</b> {candidate['name']}", styles['Normal']))
    story.append(Paragraph(f"<b>Cédula:</b> {candidate['cedula']}", styles['Normal']))
    story.append(Paragraph(f"<b>Cargo:</b> {candidate.get('position', 'N/A')}", styles['Normal']))
    if evaluador_nombre:
        story.append(Paragraph(f"<b>Evaluador:</b> {evaluador_nombre}", styles['Normal']))
    story.append(Paragraph(f"<b>Fecha de Evaluación:</b> {completed_at or 'N/A'}", styles['Normal']))
    story.append(Paragraph(f"<b>ID de Sesión:</b> {session_id}", styles['DSmall']))
    story.append(Spacer(1, 24))
    
    if analysis and analysis.get("clasificacion"):
        clasif = analysis["clasificacion"]
        banner_table = Table([[clasif["label"]]], colWidths=[450])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(clasif["color"])),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('TOPPADDING', (0, 0), (-1, -1), 16),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ]))
        story.append(banner_table)
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<i>{clasif['descripcion']}</i>", styles['DSmall']))
    
    story.append(Spacer(1, 24))
    
    if analysis:
        puntajes_data = [
            ["Componente", "Promedio", "Máximo"],
            ["Evaluación de Rendimiento (6 objetivos)", f"{analysis['promedio_rendimiento']:.2f}", "5.00"],
            ["Evaluación de Potencial (5 dimensiones)", f"{analysis['promedio_potencial']:.2f}", "3.00"],
            ["Puntaje Global Ponderado", f"<b>{analysis['puntaje_global']:.2f}</b>", "5.00"]
        ]
        puntajes_table = Table(puntajes_data, colWidths=[250, 100, 100])
        puntajes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#3B82F6")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor("#F3F4F6")),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#DBEAFE")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(puntajes_table)
    
    story.append(PageBreak())
    story.append(Paragraph("EVALUACIÓN DE RENDIMIENTO", styles['SubTitle']))
    story.append(Spacer(1, 12))
    
    if bars_fig:
        img_buffer = BytesIO()
        bars_fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        story.append(Image(img_buffer, width=480, height=320))
        plt.close(bars_fig)
    
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Detalle por Objetivo:</b>", styles['Normal']))
    story.append(Spacer(1, 6))
    for obj_id, score in rendimiento_scores.items():
        objetivo = DESEMPENO_OBJETIVOS[int(obj_id) - 1]
        nivel = DESEMPENO_ESCALA_RENDIMIENTO.get(int(score), {"label": "Sin calificar", "color": "#6B7280"})
        story.append(Paragraph(
            f"<b>{objetivo['titulo']}</b> - {float(score):.1f}/5.0 ({nivel['label']})",
            styles['ListItem']
        ))
    
    story.append(PageBreak())
    story.append(Paragraph("EVALUACIÓN DE POTENCIAL", styles['SubTitle']))
    story.append(Spacer(1, 12))
    
    if radar_fig:
        img_buffer = BytesIO()
        radar_fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        story.append(Image(img_buffer, width=400, height=400))
        plt.close(radar_fig)
    
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Detalle por Dimensión:</b>", styles['Normal']))
    story.append(Spacer(1, 6))
    for dim_id, score in potencial_scores.items():
        dimension = DESEMPENO_DIMENSIONES[int(dim_id) - 1]
        story.append(Paragraph(f"<b>{dimension['nombre']}</b> - Nivel {score}/3", styles['ListItem']))
        story.append(Paragraph(
            f"<i>{dimension['niveles'][int(score)]}</i>",
            ParagraphStyle(name='DimDesc', parent=styles['DSmall'], leftIndent=30, spaceAfter=8)
        ))
    
    story.append(PageBreak())
    story.append(Paragraph("ANÁLISIS DE FORTALEZAS Y ÁREAS DE MEJORA", styles['SubTitle']))
    story.append(Spacer(1, 12))
    
    if analysis:
        if analysis.get("fortalezas_rendimiento"):
            story.append(Paragraph("<b>✅ Fortalezas de Rendimiento:</b>", styles['Normal']))
            story.append(Spacer(1, 6))
            for item in analysis["fortalezas_rendimiento"]:
                story.append(Paragraph(f"• {item['titulo']} ({item['score']:.1f}/5.0 - {item['label']})", styles['ListItem']))
            story.append(Spacer(1, 12))
        
        if analysis.get("fortalezas_potencial"):
            story.append(Paragraph("<b>⭐ Fortalezas de Potencial:</b>", styles['Normal']))
            story.append(Spacer(1, 6))
            for item in analysis["fortalezas_potencial"]:
                story.append(Paragraph(f"• {item['nombre']} ({item['nivel']})", styles['ListItem']))
            story.append(Spacer(1, 12))
        
        if analysis.get("areas_mejora_rendimiento"):
            story.append(Paragraph("<b>⚠️ Áreas de Mejora en Rendimiento:</b>", styles['Normal']))
            story.append(Spacer(1, 6))
            for item in analysis["areas_mejora_rendimiento"]:
                story.append(Paragraph(f"• {item['titulo']} ({item['score']:.1f}/5.0 - {item['label']})", styles['ListItem']))
            story.append(Spacer(1, 12))
        
        if analysis.get("areas_desarrollo_potencial"):
            story.append(Paragraph("<b>📈 Áreas de Desarrollo en Potencial:</b>", styles['Normal']))
            story.append(Spacer(1, 6))
            for item in analysis["areas_desarrollo_potencial"]:
                story.append(Paragraph(f"• {item['nombre']} ({item['nivel']})", styles['ListItem']))
            story.append(Spacer(1, 12))
    
    story.append(PageBreak())
    story.append(Paragraph("RECOMENDACIONES Y PLAN DE ACCIÓN", styles['SubTitle']))
    story.append(Spacer(1, 12))
    
    if analysis and analysis.get("recomendaciones"):
        story.append(Paragraph("<b>💡 Recomendaciones Generales:</b>", styles['Normal']))
        story.append(Spacer(1, 6))
        for recom in analysis["recomendaciones"]:
            story.append(Paragraph(f"• {recom}", styles['ListItem']))
        story.append(Spacer(1, 18))
    
    if iniciativas and len(iniciativas) > 0:
        story.append(Paragraph("<b>🎯 Iniciativas de Mejora Definidas:</b>", styles['Normal']))
        story.append(Spacer(1, 6))
        for i, iniciativa in enumerate(iniciativas, 1):
            if iniciativa and iniciativa.strip():
                story.append(Paragraph(f"<b>Iniciativa {i}:</b>", styles['Normal']))
                story.append(Paragraph(iniciativa, styles['ListItem']))
                story.append(Spacer(1, 8))
    elif analysis and analysis.get("requiere_iniciativas"):
        story.append(Paragraph(
            "<b>⚠️ NOTA:</b> El promedio de evaluación requiere establecer iniciativas de mejora específicas.",
            ParagraphStyle(name='Alert', parent=styles['Normal'], textColor=colors.HexColor("#EF4444"))
        ))
    
    story.append(Spacer(1, 24))
    story.append(Paragraph(
        f"<i>Documento generado automáticamente el {completed_at or _now_gmt5().strftime('%Y-%m-%d %H:%M:%S')}</i>",
        styles['DSmall']
    ))

    # Sección de firmas
    story.append(Spacer(1, 40))
    empleado_nombre = candidate.get('name', '').upper()
    jefe_nombre = (evaluador_nombre or '').upper()
    firma_data = [
        [
            Paragraph(f"<b>{empleado_nombre}</b>", ParagraphStyle('_FN', alignment=1, fontSize=10, fontName='Helvetica-Bold')),
            Spacer(1, 1),
            Paragraph(f"<b>{jefe_nombre}</b>", ParagraphStyle('_FJ', alignment=1, fontSize=10, fontName='Helvetica-Bold')),
        ],
        [
            Paragraph("Firma Colaborador Evaluado", ParagraphStyle('_FL', alignment=1, fontSize=9, textColor=colors.HexColor("#6B7280"))),
            Spacer(1, 1),
            Paragraph("Firma Evaluador / Jefe Inmediato", ParagraphStyle('_FL2', alignment=1, fontSize=9, textColor=colors.HexColor("#6B7280"))),
        ],
    ]
    firma_table = Table(firma_data, colWidths=[220, 60, 220])
    firma_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (0, 0), 0.8, colors.black),
        ('LINEABOVE', (2, 0), (2, 0), 0.8, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(firma_table)

    doc.build(story)
    buffer.seek(0)
    return buffer


# =========================================================================
# DESEMPEÑO LÍDERES
# =========================================================================

def generate_desempeno_lider_pdf(candidate, competencias_scores, rendimiento_scores, potencial_scores,
                                  session_id, completed_at=None, analysis=None, evaluador_nombre=None,
                                  nivel_cargo=None, iniciativas=None):
    """Genera PDF de Evaluación de Desempeño para Líderes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    try:
        styles.add(ParagraphStyle(name='DLTitle', parent=styles['Heading1'], fontSize=16,
                                  textColor=colors.HexColor("#1E40AF"), alignment=1, spaceAfter=12))
        styles.add(ParagraphStyle(name='DLSub', parent=styles['Heading2'], fontSize=12,
                                  textColor=colors.HexColor("#374151"), spaceAfter=8))
        styles.add(ParagraphStyle(name='DLSmall', parent=styles['Normal'], fontSize=9,
                                  textColor=colors.HexColor("#6B7280")))
        styles.add(ParagraphStyle(name='DLItem', parent=styles['Normal'], fontSize=10,
                                  leftIndent=16, spaceAfter=4))
    except Exception:
        pass
    DLTitle = styles.get('DLTitle', styles['Title'])
    DLSub = styles.get('DLSub', styles['Heading2'])
    DLSmall = styles.get('DLSmall', styles['Normal'])
    DLItem = styles.get('DLItem', styles['Normal'])

    story = []
    story.extend(_build_hesego_header("FO-GH-41", version="02", fecha="30-01-24"))

    info_rows = [
        ["Colaborador:", candidate['name']],
        ["Cédula:", str(candidate['cedula'])],
        ["Cargo:", candidate.get('position', 'N/A')],
        ["Nivel de Cargo:", nivel_cargo or 'N/A'],
        ["Evaluador:", evaluador_nombre or 'N/A'],
        ["Fecha:", completed_at or 'N/A'],
        ["ID Sesión:", str(session_id)],
    ]
    it = Table(info_rows, colWidths=[130, 360])
    it.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(it)
    story.append(Spacer(1, 14))

    if analysis and analysis.get("clasificacion"):
        clasif = analysis["clasificacion"]
        bn = Table([[clasif.get("label", "")]], colWidths=[450])
        bn.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(clasif.get("color", "#374151"))),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 13),
            ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(bn)
        story.append(Spacer(1, 6))
        if clasif.get("descripcion"):
            story.append(Paragraph(clasif["descripcion"], DLSmall))

    if analysis:
        story.append(Spacer(1, 10))
        pt_data = [
            ["Componente", "Puntaje", "Máximo"],
            ["Competencias Organizacionales", f"{analysis.get('promedio_competencias', 0):.2f}", "6.00"],
            ["Rendimiento (6 objetivos)", f"{analysis.get('promedio_rendimiento', 0):.2f}", "5.00"],
            ["Potencial (5 dimensiones)", f"{analysis.get('promedio_potencial', 0):.2f}", "3.00"],
            ["Puntaje Global Ponderado", f"{analysis.get('puntaje_global', 0):.2f}", "5.00"],
        ]
        pt = Table(pt_data, colWidths=[260, 100, 90])
        pt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#DBEAFE")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(pt)

    story.append(PageBreak())
    story.append(Paragraph("COMPETENCIAS ORGANIZACIONALES", DLSub))
    story.append(Spacer(1, 6))
    nivel_req_info = COMPETENCIAS_NIVEL_REQUERIDO.get((nivel_cargo or "").upper(), None)
    comp_data = [["Competencia", "Nivel", "Requerido", "Brecha"]]
    for comp in COMPETENCIAS_ORGANIZACIONALES:
        cid = comp["id"]
        score = competencias_scores.get(cid, 0)
        req = nivel_req_info["niveles"][cid - 1] if nivel_req_info else "-"
        brecha = (score - req) if isinstance(req, int) else "-"
        brecha_str = f"+{brecha}" if isinstance(brecha, int) and brecha > 0 else str(brecha)
        comp_data.append([comp["nombre"][:50], str(score), str(req), brecha_str])
    ct = Table(comp_data, colWidths=[240, 70, 80, 60])
    ct.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#374151")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'), ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(ct)
    story.append(Spacer(1, 12))

    story.append(Paragraph("EVALUACIÓN DE RENDIMIENTO", DLSub))
    rend_data = [["Objetivo", "Puntaje", "Nivel"]]
    for obj_id, score in rendimiento_scores.items():
        objetivo = DESEMPENO_OBJETIVOS[int(obj_id) - 1]
        nivel = DESEMPENO_ESCALA_RENDIMIENTO.get(int(score), {})
        rend_data.append([objetivo["titulo"][:60], f"{score}/5", nivel.get("label", "Sin calificar")])
    rt = Table(rend_data, colWidths=[290, 60, 100])
    rt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(rt)
    story.append(Spacer(1, 12))

    story.append(Paragraph("EVALUACIÓN DE POTENCIAL", DLSub))
    pot_data = [["Dimensión", "Nivel"]]
    for dim_id, score in potencial_scores.items():
        dimension = DESEMPENO_DIMENSIONES[int(dim_id) - 1]
        pot_data.append([dimension["nombre"], f"Nivel {score}/3"])
    pot_t = Table(pot_data, colWidths=[370, 80])
    pot_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(pot_t)

    if iniciativas:
        story.append(Spacer(1, 10))
        story.append(Paragraph("INICIATIVAS DE MEJORA", DLSub))
        for i, ini in enumerate(iniciativas, 1):
            story.append(Paragraph(f"{i}. {ini}", DLItem))

    if analysis and analysis.get("recomendaciones"):
        story.append(Spacer(1, 10))
        story.append(Paragraph("RECOMENDACIONES", DLSub))
        for recom in analysis["recomendaciones"]:
            story.append(Paragraph(f"• {recom}", DLItem))

    # Sección de firmas
    story.append(Spacer(1, 40))
    empleado_nombre = candidate.get('name', '').upper()
    jefe_nombre = (evaluador_nombre or '').upper()
    firma_data = [
        [
            Paragraph(f"<b>{empleado_nombre}</b>", ParagraphStyle('_LFN', alignment=1, fontSize=10, fontName='Helvetica-Bold')),
            Spacer(1, 1),
            Paragraph(f"<b>{jefe_nombre}</b>", ParagraphStyle('_LFJ', alignment=1, fontSize=10, fontName='Helvetica-Bold')),
        ],
        [
            Paragraph("Firma Colaborador Evaluado", ParagraphStyle('_LFL', alignment=1, fontSize=9, textColor=colors.HexColor("#6B7280"))),
            Spacer(1, 1),
            Paragraph("Firma Evaluador / Jefe Inmediato", ParagraphStyle('_LFL2', alignment=1, fontSize=9, textColor=colors.HexColor("#6B7280"))),
        ],
    ]
    firma_table = Table(firma_data, colWidths=[220, 60, 220])
    firma_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (0, 0), 0.8, colors.black),
        ('LINEABOVE', (2, 0), (2, 0), 0.8, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(firma_table)

    doc.build(story)
    buf.seek(0)
    return buf


# =========================================================================
# PERÍODO DE PRUEBA
# =========================================================================

def generate_periodo_prueba_pdf(candidate, actuaciones_scores, calificaciones_scores,
                                 session_id, completed_at=None, analysis=None, evaluador_nombre=None,
                                 aprobo=False, llamados_atencion=False, conocimiento_adecuado=True,
                                 observaciones=None):
    """Genera PDF de Evaluación de Período de Prueba."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    try:
        styles.add(ParagraphStyle(name='PPTitle', parent=styles['Heading1'], fontSize=16,
                                  textColor=colors.HexColor("#1E40AF"), alignment=1, spaceAfter=12))
        styles.add(ParagraphStyle(name='PPSub', parent=styles['Heading2'], fontSize=12,
                                  textColor=colors.HexColor("#374151"), spaceAfter=8))
        styles.add(ParagraphStyle(name='PPItem', parent=styles['Normal'], fontSize=10,
                                  leftIndent=16, spaceAfter=4))
    except Exception:
        pass
    PPTitle = styles.get('PPTitle', styles['Title'])
    PPSub = styles.get('PPSub', styles['Heading2'])
    PPItem = styles.get('PPItem', styles['Normal'])

    story = []
    story.extend(_build_hesego_header("FO-GH-46", version="01", fecha="05-09-24",
                                       titulo="EVALUACIÓN PERÍODO DE PRUEBA"))

    info_rows = [
        ["Fecha de Evaluación:", completed_at or ''],
        ["Nombre del trabajador:", candidate['name'] + f"  (C.C. {candidate['cedula']})"],
        ["Cargo:", candidate.get('position', '')],
        ["Área:", candidate.get('regional', '')],
        ["Evaluador:", evaluador_nombre or ''],
    ]
    it = Table(info_rows, colWidths=[150, 352])
    it.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.black),
        ('LINEAFTER', (0, 0), (0, -1), 0.5, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(it)
    story.append(Spacer(1, 14))

    aprobacion_color = "#10B981" if aprobo else "#EF4444"
    aprobacion_text = "APROBÓ EL PERÍODO DE PRUEBA" if aprobo else "NO APROBÓ EL PERÍODO DE PRUEBA"
    bn = Table([[aprobacion_text]], colWidths=[450])
    bn.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(aprobacion_color)),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 13),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(bn)

    if analysis:
        story.append(Spacer(1, 10))
        clasif = analysis.get("clasificacion") or {}
        mt_data = [
            ["Promedio Actuaciones", f"{analysis.get('promedio_actuaciones', 0):.2f}/4.00",
             "Promedio Calificaciones", f"{analysis.get('promedio_calificaciones', 0):.2f}/5.00"],
            ["Promedio General", f"{analysis.get('promedio_general', 0):.2f}/4.00",
             "Clasificación", clasif.get("label", "N/A")],
            ["Llamados de atención", "SÍ" if llamados_atencion else "NO",
             "Conocimiento adecuado", "SÍ" if conocimiento_adecuado else "NO"],
        ]
        mt = Table(mt_data, colWidths=[140, 90, 140, 80])
        mt.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
            ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(mt)

    story.append(PageBreak())
    story.append(Paragraph("ACTUACIONES Y COMPORTAMIENTOS", PPSub))
    act_data = [["N°", "Actuación", "Calificación"]]
    for idx, actuacion in enumerate(PERIODO_PRUEBA_ACTUACIONES):
        score = actuaciones_scores.get(idx, 0)
        if score == 0:
            continue
        escala = PERIODO_PRUEBA_ESCALA_ACTUACIONES.get(score, {})
        act_data.append([str(idx + 1), actuacion[:75], escala.get("label", str(score))])
    at = Table(act_data, colWidths=[25, 330, 95])
    at.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#374151")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(at)
    story.append(Spacer(1, 12))

    story.append(Paragraph("CALIFICACIONES ESPECÍFICAS", PPSub))
    cal_data = [["Criterio", "Calificación"]]
    for idx, cal in enumerate(PERIODO_PRUEBA_CALIFICACIONES):
        score = calificaciones_scores.get(idx, 0)
        if score == 0:
            continue
        escala = PERIODO_PRUEBA_ESCALA_CALIFICACIONES.get(score, {})
        cal_data.append([cal, escala.get("label", str(score))])
    calt = Table(cal_data, colWidths=[360, 90])
    calt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#374151")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(calt)

    if observaciones:
        story.append(Spacer(1, 10))
        story.append(Paragraph("OBSERVACIONES", PPSub))
        story.append(Paragraph(str(observaciones), PPItem))

    if analysis and analysis.get("recomendaciones"):
        story.append(Spacer(1, 10))
        story.append(Paragraph("RECOMENDACIONES", PPSub))
        for recom in analysis["recomendaciones"]:
            story.append(Paragraph(f"• {recom}", PPItem))

    # --- FIRMAS ---
    story.append(Spacer(1, 30))
    firma_data = [
        ["_" * 40, "_" * 40],
        [f"Evaluador: {evaluador_nombre or ''}", f"Colaborador: {candidate['name']}"],
    ]
    firma_table = Table(firma_data, colWidths=[240, 240])
    firma_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(firma_table)

    doc.build(story)
    buf.seek(0)
    return buf
