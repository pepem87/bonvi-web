import html
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import os
COLORS=dict(green=colors.HexColor('#294A3C'), green2=colors.HexColor('#405E50'), cream=colors.HexColor('#FBF8F0'), ivory=colors.HexColor('#F4F0E8'), line=colors.HexColor('#A8AAA0'), white=colors.HexColor('#FFFDF8'))
CATS=['VINOS','CHAMPAGNES','GIN','VODKA','WHISKYS','APERITIVOS','TEQUILA','CERVEZAS','SIDRAS','ACEITES']

def money(v,decimals=2):
    return '$ '+f'{v:,.{decimals}f}'.replace(',','X').replace('.',',').replace('X','.')

def draw_page(canvas,doc,logo,vigencia):
    c=canvas;w,h=A4;c.saveState();c.setFillColor(COLORS['ivory']);c.rect(0,0,w,h,fill=1,stroke=0)
    c.setStrokeColor(COLORS['green']);c.setLineWidth(.9);c.rect(12*mm,12*mm,w-24*mm,h-24*mm,stroke=1,fill=0)
    if logo and Path(logo).exists():
        from reportlab.lib.utils import ImageReader
        c.drawImage(ImageReader(str(logo)), w/2-17*mm, h-38*mm, width=34*mm,height=34*mm, preserveAspectRatio=True, mask='auto')
    c.setFont('Times-Bold',9);c.setFillColor(COLORS['green']);c.drawCentredString(w/2,h-41*mm,'BON VI · MERCAT')
    c.setFont('Times-Roman',7);c.drawCentredString(w/2,h-46*mm,'DISTRIBUCIÓN DE BEBIDAS · EST. 2026')
    c.setFont('Times-Bold',13);c.drawCentredString(w/2,h-54*mm,'LISTA DE PRECIOS · PERSONAS')
    c.setFont('Times-Italic',7);c.drawCentredString(w/2,h-59*mm,'PENSADO PARA HOGARES, ENCUENTROS Y BUENOS MOMENTOS')
    c.setFont('Times-Bold',6.4);c.drawString(14*mm,h-20*mm,'BUENAS BEBIDAS');c.drawString(14*mm,h-23*mm,'MEJORES ENCUENTROS')
    c.drawRightString(w-14*mm,h-20*mm,'TRADICIÓN EN CADA');c.drawRightString(w-14*mm,h-23*mm,'COPA Y NEGOCIO')
    c.setLineWidth(.4); c.line(12*mm,h-62*mm,w-12*mm,h-62*mm)
    c.setFont('Times-Bold',7.2);c.drawString(17*mm,h-66*mm,'VIGENTE HASTA '+vigencia)
    c.drawRightString(w-17*mm,h-66*mm,'PRECIOS EXPRESADOS EN PESOS ARGENTINOS ($)')
    c.setFillColor(COLORS['green']);c.setFont('Times-Roman',6.5)
    c.drawCentredString(w/2,16*mm,'BON VI · MERCAT · ENTREGA SEMANAL · LA PLATA')
    c.drawRightString(w-14*mm,16*mm,'Página '+str(doc.page))
    c.setFont('Times-Bold',6.8);c.drawCentredString(w/2,12.8*mm,'PROHIBIDA SU VENTA A MENORES DE 18 AÑOS')
    c.restoreState()

def create_pdf(path,products,vigencia,logo):
    from reportlab.lib.styles import getSampleStyleSheet
    grouped={k:[] for k in CATS}
    for p in products: grouped.setdefault(p['categoria'], []).append(p)
    head=ParagraphStyle('head',fontName='Times-Bold',fontSize=6.5,leading=7.5,textColor=COLORS['green'])
    cell=ParagraphStyle('cell',fontName='Times-Roman',fontSize=6.5,leading=7.45)
    cent=ParagraphStyle('cent',parent=cell,alignment=TA_CENTER)
    right=ParagraphStyle('right',parent=cell,alignment=TA_RIGHT)
    family=ParagraphStyle('family',fontName='Times-Bold',fontSize=7,leading=8.5,textColor=COLORS['green'])
    doc=SimpleDocTemplate(str(path),pagesize=A4,leftMargin=13*mm,rightMargin=13*mm,topMargin=72*mm,bottomMargin=18*mm,title='BON VI MERCAT - Lista personas',author='BON VI MERCAT')
    story=[]
    pad=float(os.getenv('BONVI_ROW_PADDING','1.65'))
    for cat in CATS+sorted(k for k in grouped if k not in CATS):
        arr=grouped.get(cat,[])
        if not arr:continue
        hrow=[Paragraph(html.escape(cat),family),Paragraph('CÓDIGO',head),Paragraph('DESCRIPCIÓN',head),Paragraph('MODALIDAD',head),Paragraph('PRECIO UNITARIO',head),Paragraph('PRECIO BULTO/UNIDAD',head)]
        table_data=[hrow]
        for p in arr:
            mode='BULTO x'+str(p['uxb']) if p['tipo']=='bulto' else 'UNIDAD'
            table_data.append(['',Paragraph(html.escape(p['codigo']),cent),Paragraph(html.escape(p['nombre']),cell),Paragraph(mode,cent),Paragraph(money(p['unitario']),right),Paragraph(money(p['precio']),right)])
        table=Table(table_data,colWidths=[26*mm,12*mm,67*mm,20*mm,26*mm,33*mm],repeatRows=1,hAlign='CENTER')
        table.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BACKGROUND',(1,0),(-1,0),colors.HexColor('#EEEADF')),
            ('LINEABOVE',(0,0),(-1,0),.7,COLORS['green']),('LINEBELOW',(0,0),(-1,0),.45,COLORS['green']),
            ('LINEBELOW',(1,1),(-1,-1),.18,COLORS['line']),('ROWBACKGROUNDS',(1,1),(-1,-1),[COLORS['cream'],COLORS['white']]),
            ('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2),
            ('TOPPADDING',(0,0),(-1,-1),pad),('BOTTOMPADDING',(0,0),(-1,-1),pad),
        ]))
        story.append(table);story.append(Spacer(1,1.2*mm))
    doc.build(story,onFirstPage=lambda c,d:draw_page(c,d,logo,vigencia),onLaterPages=lambda c,d:draw_page(c,d,logo,vigencia))
