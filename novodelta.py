import streamlit as st
import math
from PIL import Image
import os
import datetime
import base64
import re
import pytz
from io import BytesIO
from fpdf import FPDF 

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Monitor de aplicação - Gota Perfeita", layout="centered")

def get_base64_image(image_path):
    if os.path.exists(image_path):
        try:
            img = Image.open(image_path)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
        except:
            return ""
    return ""

# Dicionário de caminhos e logos
caminhos_adj = {
    "LINHA AQUAX": "acquax.png",
    "TEK F": "TEK F.png",
    "THUNDER": "THUNDER.png",
    "ALVO": "ALVO.png",
    "CITRO X": "CITRO X.png"
}

# Carregamento das logos em Base64 para a prévia HTML
logo_gp_base64 = get_base64_image("logo.png")
logos_adj_b64 = {nome: get_base64_image(path) for nome, path in caminhos_adj.items()}

# --- 2. CSS ESTILIZADO COMPLETO ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; background-color: #4CAF50; color: white; }
    .metric-container { background-color: #f0f2f6; padding: 20px; border-radius: 15px; text-align: center; border: 1px solid #ddd; margin-bottom: 20px; }
    .status-card { padding: 20px; border-radius: 15px; text-align: center; font-weight: bold; margin-bottom: 15px; border: 1px solid #ccc; font-size: 1.5em; }
    .report-card { background-color: white; border: 2px solid #1b5e20; border-radius: 20px; padding: 0; overflow: hidden; margin-top: 20px; font-family: sans-serif; }
    .report-header { background-color: #1b5e20; padding: 15px; text-align: center; }
    .report-header img { max-height: 70px; filter: brightness(0) invert(1); }
    .report-body { padding: 20px; color: #333; }
    .report-info-bar { background-color: #f1f8e9; padding: 10px 15px; border-bottom: 1px solid #c8e6c9; font-size: 0.85em; color: #1b5e20; }
    .info-row { display: flex; justify-content: space-between; margin-bottom: 3px; font-weight: bold; }
    .adj-section { margin-top: 15px; text-align: center; border-top: 1px solid #eee; padding-top: 15px; }
    .adj-item { display: inline-block; width: 44%; margin: 8px; vertical-align: middle; text-align: center; }
    .adj-item img { max-height: 80px; width: auto; }
    .adj-dose { display: block; font-size: 1.1em; font-weight: bold; color: #1b5e20; margin-top: 5px; }
    .obs-box { margin-top: 15px; padding: 12px; background-color: #f9f9f9; border-left: 4px solid #1b5e20; border-radius: 5px; font-size: 0.95em; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES TÉCNICAS ---
def calcular_delta_t(t_seca, ur):
    tw = t_seca * math.atan(0.151977 * (ur + 8.313659)**0.5) + \
         math.atan(t_seca + ur) - math.atan(ur - 1.676331) + \
         0.00391838 * (ur)**1.5 * math.atan(0.023101 * ur) - 4.686035
    return t_seca - tw

def obter_recomendacao(dt, temp):
    if temp >= 35.1:
        return "NÃO RECOMENDADO (CALOR EXCESSIVO)", "#721c24", "white", \
               "⛔ Temperatura crítica (≥ 35.1°C). Risco elevado de fitotoxicidade e estresse hídrico. Suspenda a operação."
    if temp <= 6.0:
        return "NÃO RECOMENDADO (FRIO EXTREMO)", "#721c24", "white", \
               "❄️ Temperatura crítica (≤ 6°C). Alto risco de danos aos tecidos vegetais e baixíssima atividade metabólica. Suspenda a operação."
    if 6.0 < temp <= 15.0:
        return "ARRISCADA: BAIXA TEMPERATURA", "#ffc107", "black", \
               "❄️ Atenção: Temperatura abaixo do ideal metabólico. Verifique a temperatura base da cultura para garantir a absorção sistêmica."
    if dt < 1.0:
        return "NÃO RECOMENDADO", "#721c24", "white", \
               "⛔ Delta T crítico. Ar saturado com risco de perda por escorrimento e inversão térmica."
    elif 1.0 <= dt < 2.0:
        return "ARRISCADA: ALTA UMIDADE", "#ffc107", "black", \
               "⚠️ Condição limítrofe. Utilize CITRO X para potencializar a adesividade e fixação no alvo, evitando perdas por escorrimento."
    elif 2.0 <= dt <= 8.0:
        return "CONDIÇÃO ADEQUADA", "#28a745", "white", \
               "✅ Condições ideais para performance física e fisiológica da aplicação."
    elif 8.0 < dt <= 10.0:
        return "ARRISCADA: ALTA EVAPORAÇÃO", "#fd7e14", "white", \
               "⚠️ Evaporação acelerada. Use gotas grossas e CITRO X para proteger a gota contra a evaporação."
    else:
        return "NÃO RECOMENDADO", "#dc3545", "white", \
               "⛔ Delta T acima de 10. Perda de produto por evaporação severa antes de atingir o alvo."
def limpar_emojis(texto):
    if not texto:
        return ""
    # Remove caracteres que não estão no intervalo Latin-1 (onde moram os emojis e símbolos especiais)
    return re.sub(r'[^\x00-\xff]', '', texto)

def exportar_pdf(cliente, rtv, temp, ur, dt, status, parecer, adjs, agora_relatorio):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(0, 0, 210, 297, "F")
    pdf.set_text_color(0, 0, 0)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, "NotoSans-Regular.ttf")

    if os.path.exists(font_path):
        pdf.add_font("NotoSans", "", font_path)
        pdf.add_font("NotoSans", "B", font_path)
        pdf_font = "NotoSans"
    else:
        pdf_font = "helvetica"

    pdf.set_font(pdf_font, "B", 16)
    pdf.cell(0, 10, "Relatorio de Aplicacao - Gota Perfeita", 0, 1, "C")
    pdf.ln(5)
    
    pdf.set_font(pdf_font, "", 11)
    pdf.cell(0, 7, f"Cliente: {cliente.upper() if cliente else 'NAO INFORMADO'}".encode('latin-1', 'replace').decode('latin-1'), 0, 1)
    pdf.cell(0, 7, f"RTV: {rtv.upper() if rtv else 'NAO INFORMADO'}".encode('latin-1', 'replace').decode('latin-1'), 0, 1)
    pdf.cell(0, 7, f"Data: {agora_relatorio.strftime('%d/%m/%Y')}  |  Hora: {agora_relatorio.strftime('%H:%M')}", 0, 1)
    pdf.ln(5)
    
    pdf.set_font(pdf_font, "B", 12)
    # Suporte ao símbolo °C via encoding latin-1
    texto_cond = f"Condições: {temp}°C | UR: {ur}% | Delta T: {dt}"
    pdf.cell(0, 10, texto_cond.encode('latin-1', 'replace').decode('latin-1'), 1, 1, "C")
    pdf.ln(5)
    
    pdf.set_font(pdf_font, "B", 11)
    pdf.cell(0, 10, f"Status: {limpar_emojis(status)}".encode('latin-1', 'replace').decode('latin-1'), 0, 1)
    pdf.set_font(pdf_font, "", 10)
    pdf.multi_cell(0, 7, f"Parecer Tecnico: {limpar_emojis(parecer)}".encode('latin-1', 'replace').decode('latin-1'))
    
    if adjs:
        pdf.ln(5)
        pdf.set_font(pdf_font, "B", 10)
        pdf.cell(0, 10, "Posicionamento de Adjuvantes:", 0, 1)
        x_start, y_pos, col_width = 20, pdf.get_y(), 45
        for i, (nome, dose) in enumerate(adjs):
            img_path = caminhos_adj.get(nome)
            if img_path and os.path.exists(img_path):
                if y_pos > 250:
                    pdf.add_page()
                    pdf.set_fill_color(255, 255, 255)
                    pdf.rect(0, 0, 210, 297, "F")
                    y_pos = 20
                pdf.image(img_path, x=x_start + (i % 4) * col_width, y=y_pos, w=25)
                if dose:
                    pdf.set_xy(x_start + (i % 4) * col_width, y_pos + 22)
                    pdf.set_font(pdf_font, "B", 8)
                    pdf.cell(25, 5, f"{dose} ml/ha", 0, 0, "C")
            if (i + 1) % 4 == 0: y_pos += 35
                pdf.set_y(y_pos + 40)
    if os.path.exists("delta.png"):
        if pdf.get_y() > 180: 
            pdf.add_page()
            pdf.set_fill_color(255, 255, 255)
            pdf.rect(0, 0, 210, 297, "F")
             
    return bytes(pdf.output())

# --- 4. INTERFACE ---
if os.path.exists("logo.png"):
    st.image(Image.open("logo.png"), width=150)

st.title("Monitor de aplicação - Gota Perfeita")

col1, col2 = st.columns(2)
with col1: t_input = st.number_input("Temp. (°C)", 0.0, 50.0, 25.0, step=1.0)
with col2: ur_input = st.number_input("Umidade (%)", 1.0, 100.0, 60.0, step=5.0)

dt_resultado = calcular_delta_t(t_input, ur_input)
status, cor_bg, cor_txt, msg = obter_recomendacao(dt_resultado, t_input)

st.markdown(f"""
    <div class="metric-container">
        <span style="color: #666; font-size: 1.1em;">Delta T Atual:</span><br>
        <b style="font-size: 4em; color: #333;">{dt_resultado:.1f}</b>
    </div>
""", unsafe_allow_html=True)

st.markdown(f'<div class="status-card" style="background-color: {cor_bg}; color: {cor_txt};">{status}</div>', unsafe_allow_html=True)

if "ADEQUADA" in status: st.success(msg)
elif "NÃO RECOMENDADO" in status: st.error(msg)
else: st.warning(msg)

st.divider()

# --- SEÇÃO DO GERADOR DE RELATÓRIO ---
st.subheader("Gerador de Relatório")
with st.expander("Configurar Dados do Relatório", expanded=True):
    col_c, col_r = st.columns(2)
    cliente_input = col_c.text_input("Nome do Cliente / Fazenda")
    rtv_input = col_r.text_input("Nome do RTV")
    
    # GERENCIAMENTO DE DATA E HORA
    fuso = pytz.timezone('America/Sao_Paulo')
    if 'data_hora_ref' not in st.session_state:
        st.session_state.data_hora_ref = datetime.datetime.now(fuso)

    col_data, col_hora = st.columns(2)
    data_manual = col_data.date_input("Data da medição", st.session_state.data_hora_ref.date())
    hora_manual = col_hora.time_input("Hora da medição", st.session_state.data_hora_ref.time(), step=1800)
    agora_escolhida = datetime.datetime.combine(data_manual, hora_manual)
    
    st.write("**Posicionamento de Adjuvantes:**")
    c_adj1, c_adj2 = st.columns(2)
    aqx_chk = c_adj1.checkbox("LINHA AQUAX", value=True)
    t_chk = c_adj2.checkbox("TEK F")
    h_chk = c_adj1.checkbox("THUNDER")
    a_chk = c_adj2.checkbox("ALVO")
    x_chk = c_adj1.checkbox("CITRO X")
    
    d_tek = c_adj2.text_input("Dose TEK F (ml/ha)", "50") if t_chk else ""
    d_thu = c_adj1.text_input("Dose THUNDER (ml/ha)", "50") if h_chk else ""
    d_alv = c_adj2.text_input("Dose ALVO (ml/ha)", "50") if a_chk else ""
    d_cit = c_adj1.text_input("Dose CITRO X (ml/ha)", "100") if x_chk else ""
    parecer_obrigatorio = st.text_area("Observação Técnica e Recomendação:", value=msg)

if st.button("👁️ Resumo rápido"):
    adjs_sel = []
    if aqx_chk: adjs_sel.append(("LINHA AQUAX", ""))
    if t_chk: adjs_sel.append(("TEK F", d_tek))
    if h_chk: adjs_sel.append(("THUNDER", d_thu))
    if a_chk: adjs_sel.append(("ALVO", d_alv))
    if x_chk: adjs_sel.append(("CITRO X", d_cit))

    html_produtos = ""
    for nome, dose in adjs_sel:
        img_b64 = logos_adj_b64.get(nome, "")
        img_tag = f'<img src="data:image/png;base64,{img_b64}">' if img_b64 else f'<b>{nome}</b>'
        dose_tag = f'<span class="adj-dose">{dose} ml/ha</span>' if dose else ""
        html_produtos += f'<div class="adj-item">{img_tag}{dose_tag}</div>'

    card_html = f"""
    <div class="report-card">
        <div class="report-header"><img src="data:image/png;base64,{logo_gp_base64}"></div>
        <div class="report-info-bar">
            <div class="info-row"><span>📍 CLIENTE: {cliente_input.upper() if cliente_input else 'NÃO INFORMADO'}</span><span>📅 DATA: {agora_escolhida.strftime("%d/%m/%Y")}</span></div>
            <div class="info-row"><span>👤 RTV: {rtv_input.upper() if rtv_input else 'REPRESENTANTE'}</span><span>⏰ HORA: {agora_escolhida.strftime("%H:%M")}</span></div>
        </div>
        <div class="report-body">
            <table style="width:100%; text-align:center; border:none; margin-bottom:15px;">
                <tr>
                    <td style="border:none;"><b style="font-size:1.6em; color:#1b5e20;">{int(t_input)}°C</b><br><small>TEMPERATURA</small></td>
                    <td style="border:none;"><b style="font-size:1.6em; color:#1b5e20;">{int(ur_input)}%</b><br><small>UMIDADE</small></td>
                    <td style="border:none;"><b style="font-size:1.6em; color:#1b5e20;">{dt_resultado:.1f}</b><br><small>DELTA T</small></td>
                </tr>
            </table>
            <div style="background-color: {cor_bg}; color: {cor_txt}; padding: 12px; border-radius: 10px; text-align: center; font-weight: bold; text-transform: uppercase;">{status}</div>
            <div class="obs-box"><b style="color:#1b5e20; font-size:0.8em;">PARECER TÉCNICO:</b><br>{parecer_obrigatorio}</div>
            <div class="adj-section">{html_produtos}</div>
            <div style="text-align:center; font-size:0.7em; color:#aaa; margin-top:20px; border-top:1px solid #eee; padding-top:10px;"><b>MICROXISTO | SUSTENTABILIDADE E PRODUTIVIDADE</b></div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

st.divider()

# Preparação Final
adjs_sel_final = []
if aqx_chk: adjs_sel_final.append(("LINHA AQUAX", ""))
if t_chk: adjs_sel_final.append(("TEK F", d_tek))
if h_chk: adjs_sel_final.append(("THUNDER", d_thu))
if a_chk: adjs_sel_final.append(("ALVO", d_alv))
if x_chk: adjs_sel_final.append(("CITRO X", d_cit))

pdf_final_bytes = exportar_pdf(cliente_input, rtv_input, int(t_input), int(ur_input), f"{dt_resultado:.1f}", status, parecer_obrigatorio, adjs_sel_final, agora_escolhida)

col_p1, col_p2 = st.columns(2)
with col_p1:
    if st.button("📄 Gerar Prévia PDF"):
        base64_pdf = base64.b64encode(pdf_final_bytes).decode('utf-8')
        st.info("💡 **Dica:** Segure pressionado para compartilhar o relatório.")
        st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>', unsafe_allow_html=True)

with col_p2:
    st.download_button(
        label="📥 Baixar Relatório",
        data=pdf_final_bytes,
        file_name=f"Relatorio_{cliente_input if cliente_input else 'GP'}.pdf",
        mime="application/pdf"
    )

st.caption("Gota Perfeita | Microxisto - Sua Aplicação de Precisão")
