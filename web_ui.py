import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
from scipy.optimize import minimize
from streamlit_image_coordinates import streamlit_image_coordinates
from skimage.color import rgb2lab, deltaE_ciede2000
import json
import os
import itertools
import io
import requests
import colorsys

# Настройка страницы
st.set_page_config(page_title="ИИ-Колорист PRO", page_icon="🎨", layout="centered")

# --- СТРОГИЙ ВЫСОКОКОНТРАСТНЫЙ МИНИМАЛИСТИЧНЫЙ ИНТЕРФЕЙС (v39.0) ---
st.markdown("""
    <style>
    .stApp { background-color: #222224 !important; }
    @media (min-width: 576px) {
        .main .block-container {
            max-width: 410px !important; padding: 0.6rem 0.6rem !important; 
            border: 1px solid #3a3a3c !important; border-radius: 25px !important;
            background-color: #222224 !important; box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
            margin-top: 10px !important; margin-bottom: 10px !important;
            overflow-x: auto !important; 
        }
    }
    
    .stApp .block-container p, .stApp .block-container span, .stApp .block-container label, .stApp .block-container caption, .stApp .block-container div {
        color: #fafafa !important; font-size: 1.02rem !important; line-height: 1.3 !important;
    }
    .stApp .block-container h3 { font-size: 1.15rem !important; font-weight: 700 !important; color: #ffffff !important; margin-top: 12px !important; margin-bottom: 4px !important; border-bottom: 1px solid #3a3a3c; padding-bottom: 4px; }
    .stApp .block-container h5 { font-size: 0.95rem !important; font-weight: 700 !important; color: #ffffff !important; margin-top: 6px !important; margin-bottom: 6px !important; text-transform: uppercase; letter-spacing: 0.5px; }
    
    /* ГРАФИТОВЫЕ АКЦЕНТНЫЕ КНОПКИ (PRIMARY) */
    button[data-testid="baseButton-primary"], .stButton button[kind="primary"] {
        background-color: #48484a !important; color: #ffffff !important; border: 1px solid #545456 !important; border-radius: 12px !important;
        padding: 12px 20px !important; font-size: 1.05rem !important; font-weight: 700 !important; letter-spacing: 0.5px;
        text-transform: uppercase !important; margin-top: 6px !important; transition: none !important; box-shadow: none !important;
    }
    button[data-testid="baseButton-primary"]:hover { background-color: #545456 !important; }
    
    /* ВТОРОСТЕПЕННЫЕ КНОПКИ */
    button[data-testid="baseButton-secondary"], .stButton button[kind="secondary"] {
        background-color: #3a3a3c !important; color: #ffffff !important; border: 1px solid #48484a !important; border-radius: 12px !important;
        font-size: 1.05rem !important; padding: 12px 20px !important; transition: none !important; margin-top: 6px !important;
    }
    button[data-testid="baseButton-secondary"]:hover { background-color: #48484a !important; color: #ffffff !important; }
    
    div[data-testid="stSlider"] div { color: #ffffff !important; }
    div[data-testid="stColorPicker"] > label { display: none !important; }
    
    /* ЖЕСТКОЕ ИСПРАВЛЕНИЕ КОНТРАСТА СЕЛЕКТБОКСА */
    div[data-testid="stSelectbox"] > div { background-color: transparent !important; }
    div[data-testid="stSelectbox"] [data-baseweb="select"] {
        background-color: #3a3a3c !important; border: 1px solid #48484a !important; border-radius: 12px !important;
    }
    div[data-testid="stSelectbox"] [data-baseweb="select"] * { color: #ffffff !important; background-color: transparent !important; }
    div[data-baseweb="popover"] ul { background-color: #3a3a3c !important; border: 1px solid #48484a !important; }
    div[data-baseweb="popover"] li { color: #ffffff !important; background-color: transparent !important; }
    div[data-baseweb="popover"] li:hover { background-color: #48484a !important; }
    
    div[data-testid="stFileUploader"] section {
        background-color: #3a3a3c !important; border: 1px dashed #48484a !important; border-radius: 12px !important; padding: 12px !important;
    }
    div[data-testid="stFileUploader"] section * { color: #ffffff !important; }
    
    div[data-testid="stRadio"] div[data-baseweb="radio"] { padding: 4px 10px !important; background-color: #3a3a3c !important; border-radius: 10px !important; margin-right: 8px !important; }
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] { background-color: #3a3a3c !important; border: 1px solid #48484a !important; border-radius: 12px !important; }
    div[data-testid="stMultiSelect"] span { background-color: #222224 !important; color: #ffffff !important; border-radius: 6px !important; }
    div[data-testid="stNumberInput"] input { background-color: #3a3a3c !important; color: #ffffff !important; border: 1px solid #48484a !important; border-radius: 10px !important; padding: 6px !important; }
    div[data-testid="stNotification"] { background-color: #2c2c2e !important; border: 1px solid #3a3a3c !important; border-radius: 12px !important; padding: 8px !important; }
    .geo-badge { font-size: 0.85rem !important; color: #8a8a8f !important; text-align: center; margin-top: 8px !important; }
    
    .target-color-box { border-radius: 12px; border: 2px solid #ffffff; margin-top: 6px; margin-bottom: 4px; height: 40px; display: flex; align-items: center; justify-content: center; }
    
    .paint-drop-container { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 12px; }
    .paint-drop-container * { color: #ffffff !important; }
    .paint-blob { width: 14px; height: 14px; border-radius: 50%; margin-top: 2px; flex-shrink: 0; box-shadow: none !important; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- ПОЛНАЯ АУТЕНТИЧНАЯ БАЗА МАСЛА «МАСТЕР-КЛАСС» [R, G, B, Density] ---
def load_all_paints_v32():
    return {
        "Невская Палитра (Масло Мастер-Класс)": {
            "Белила титановые (101)": [255, 255, 255, 1.8], "Белила цинковые (100)": [255, 255, 248, 1.9],
            "Сажа газовая (801)": [15, 15, 15, 0.9], "Кость жженая (805)": [25, 22, 20, 1.1], "Шунгит (814)": [35, 35, 35, 1.2],
            "Кадмий лимонный (203)": [255, 242, 0, 1.4], "Кадмий желтый светлый (200)": [254, 207, 0, 1.4],
            "Кадмий желтый средний (201)": [255, 185, 0, 1.5], "Кадмий желтый темный (202)": [255, 140, 0, 1.5],
            "Стронциановая желтая (207)": [245, 240, 50, 1.4], "Неаполитанская желтая (219)": [245, 218, 154, 1.5],
            "Неаполитанская желтая палевая (223)": [248, 232, 180, 1.5], "Индийская желтая (имит.) (228)": [220, 150, 20, 1.1],
            "Кадмий оранжевый (304)": [255, 110, 0, 1.5], "Марс оранжевый прозрачный (329)": [200, 90, 30, 1.2],
            "Кадмий красный светлый (302)": [227, 38, 54, 1.5], "Кадмий красный темный (303)": [180, 20, 30, 1.6],
            "Алая (318)": [235, 20, 20, 1.1], "Кармин (319)": [150, 10, 40, 1.1], "Краплак красный прочный (313)": [140, 22, 46, 1.1],
            "Розовый хинакридон (334)": [210, 30, 100, 1.1], "Киноварь (имит.) (312)": [220, 50, 40, 1.2],
            "Охра светлая (218)": [212, 163, 89, 1.3], "Охра золотистая (220)": [190, 130, 50, 1.3], "Охра темная (221)": [150, 100, 40, 1.3],
            "Сиена натуральная (405)": [170, 120, 60, 1.3], "Английская красная (300)": [160, 70, 50, 1.4],
            "Охра красная (309)": [175, 80, 55, 1.3], "Индийская красная (310)": [140, 65, 55, 1.4], "Железоокисная светло-красная (321)": [165, 60, 45, 1.5],
            "Фиолетовая «ФЦ» (601)": [70, 20, 120, 1.1], "Кобальт фиолетовый светлый (602)": [150, 90, 180, 1.5],
            "Кобальт фиолетовый темный (603)": [100, 40, 110, 1.6], "Марганцовая фиолетовая светлая (612)": [160, 80, 150, 1.4], "Фиолетовый хинакридон (621)": [120, 20, 80, 1.1],
            "Ультрамарин светлый (511)": [65, 102, 245, 1.2], "Ультрамарин темный (512)": [30, 50, 180, 1.2],
            "Кобальт синий светлый (508)": [40, 110, 220, 1.3], "Кобальт синий темный (509)": [0, 71, 171, 1.4], "Голубая «ФЦ» (500)": [0, 75, 150, 1.1],
            "Берлинская лазурь (518)": [10, 40, 90, 1.2], "Индиго (516)": [20, 35, 55, 1.2], "Цвета весеннего неба/Церулеум (503)": [40, 150, 200, 1.4],
            "Марганцевая голубая (имит.) (510)": [0, 160, 210, 1.3], "Королевская голубая (527)": [160, 200, 240, 1.4],
            "Зеленая «ФЦ» (711)": [0, 110, 80, 1.1], "Изумрудная (713)": [0, 165, 114, 1.2], "Виридоновая зеленая (714)": [0, 120, 95, 1.2],
            "Волконскоит (715)": [85, 105, 65, 1.4], "Окись хрома (704)": [90, 130, 60, 1.6], "Кобальт зеленый светлый (702)": [110, 185, 135, 1.4],
            "Кобальт зеленый темный (703)": [45, 110, 85, 1.5], "Травяная зеленая (716)": [95, 140, 45, 1.2],
            "Сиена жженая (406)": [140, 70, 35, 1.3], "Умбра натуральная (418)": [115, 95, 65, 1.3], "Умбра жженая (408)": [94, 62, 43, 1.3],
            "Умбра ленинградская натуральная (421)": [90, 75, 55, 1.3], "Умбра ленинградская жженая (422)": [75, 55, 40, 1.3],
            "Марс коричневый светлый (412)": [110, 65, 35, 1.4], "Марс коричневый темный (413)": [70, 45, 30, 1.5], "Марс коричневый прозрачный (411)": [95, 55, 25, 1.2],
            "Ван-Дик коричневый (417)": [60, 45, 35, 1.1], "Сепия (419)": [50, 40, 30, 1.2],
            "Вишневая Тавуш (356)": [120, 30, 45, 1.3], "Красно-коричневая Вайк (414)": [135, 50, 40, 1.3],
            "Фиолетово-коричневая Севан (428)": [90, 45, 65, 1.3], "Гутанкарская фиолетовая (619)": [105, 55, 115, 1.3], "Зеленая Котайк (735)": [75, 95, 65, 1.3]
        },
        "Citadel Base (Warhammer / Миниатюры)": {
            "Corax White (Белый)": [240, 242, 245, 1.4], "Abaddon Black (Черный)": [10, 10, 10, 1.0],
            "Mephiston Red (Красный)": [154, 14, 24, 1.2], "Macragge Blue (Синий)": [15, 41, 130, 1.2],
            "Averland Sunset (Желтый)": [243, 180, 10, 1.3], "Waaagh! Flesh (Зеленый)": [30, 73, 43, 1.2],
            "Bugman's Glow (Телесный)": [128, 75, 64, 1.1], "Balthasar Gold (Бронза/Охра)": [140, 105, 67, 1.4],
            "Naggaroth Night (Фиолетовый)": [59, 41, 84, 1.2]
        }
    }

ALL_PALETTES = load_all_paints_v32()

def get_market_and_coverage_data():
    try:
        res = requests.get("http://ip-api.com/json/", timeout=1.5).json()
        country, city = res.get("countryCode", "RU"), res.get("city", "Москва")
    except:
        country, city = "RU", "Локальная сеть"
    return city, "руб.", {}, {}

if "geo_cache" not in st.session_state: st.session_state.geo_cache = get_market_and_coverage_data()
current_city, current_currency, _, _ = st.session_state.geo_cache

def get_complementary_color(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    h = (h + 0.5) % 1.0
    comp_r, comp_g, comp_b = colorsys.hls_to_rgb(h, l, s)
    return [int(comp_r * 255), int(comp_g * 255), int(comp_b * 255)]

def generate_html_donut_macro(recipe, paint_db, center_hex, label_text, sub_text):
    current_pct = 0
    gradient_parts = []
    for paint, pct in recipe.items():
        rgb = paint_db.get(paint, [128, 128, 128])[:3]
        hex_str = '#{:02x}{:02x}{:02x}'.format(*rgb)
        next_pct = current_pct + pct
        gradient_parts.append(f"{hex_str} {current_pct}% {next_pct}%")
        current_pct = next_pct
    gradient_str = ", ".join(gradient_parts) if gradient_parts else "#3a3a3c 0% 100%"
    
    return f"""
    <div style="display: flex; flex-direction: column; align-items: center; margin: 5px auto;">
        <div style="width: 140px; height: 140px; border-radius: 50%; background: conic-gradient({gradient_str}); display: flex; align-items: center; justify-content: center;">
            <div style="width: 88px; height: 88px; border-radius: 50%; background-color: {center_hex}; display: flex; align-items: center; justify-content: center;">
            </div>
        </div>
        <span style="font-size: 0.92rem; margin-top: 8px; font-weight: bold; color: #ffffff !important; text-align: center; line-height: 1.2;">{label_text}<br><span style="font-size: 0.76rem; font-weight: normal; opacity: 0.8; color: #8a8a8f !important;">{sub_text}</span></span>
    </div>
    """

def rgb_to_ks(rgb_array):
    norm = np.clip(rgb_array / 255.0, 0.001, 0.999)
    return ((1.0 - norm) ** 2) / (2.0 * norm)

def ks_to_rgb(ks_array):
    res = (1.0 + ks_array) - np.sqrt(np.maximum((1.0 + ks_array) ** 2 - 1.0, 0.0))
    return np.clip(res * 255.0, 0, 255)

def calculate_mix_options(target_rgb, db, allowed_paints=None):
    active_db = {k: v for k, v in db.items() if k in allowed_paints} if allowed_paints else db
    paint_names = list(active_db.keys())
    if len(paint_names) == 0: return {}
    
    neutrals = ["Белила титановые (101)", "Сажа газовая (801)", "Кость жженая (805)", "Шунгит (814)"]
    mandatory_neutrals = [p for p in neutrals if p in paint_names]
    
    target_rgb_np = np.array(target_rgb, dtype=np.float32)
    chromatic_candidates = []
    for name in paint_names:
        if name in mandatory_neutrals: continue
        p_rgb = np.array(active_db[name][:3], dtype=np.float32)
        dist = np.linalg.norm(p_rgb - target_rgb_np)
        chromatic_candidates.append((dist, name))
        
    chromatic_candidates.sort(key=lambda x: x[0])
    selected_chromatic = [c[1] for c in chromatic_candidates[:8]]
    final_pool = mandatory_neutrals + selected_chromatic
    
    paint_rgbs = np.array([active_db[name][:3] for name in final_pool], dtype=np.float32)
    paint_ks_matrix = rgb_to_ks(paint_rgbs)
    target_rgb_norm = np.array([[target_rgb]], dtype=np.float32) / 255.0
    target_lab = rgb2lab(target_rgb_norm)[0][0]
    
    results = {}
    for num_paints in [2, 3]:
        if len(final_pool) < num_paints: continue
        best_recipe, best_delta_e, best_mixed_rgb = {}, float('inf'), [255, 255, 255]
        
        for indices in itertools.combinations(range(len(final_pool)), num_paints):
            sub_names = [final_pool[i] for i in indices]
            sub_sub_ks = paint_ks_matrix[list(indices)]
            
            def loss_function(weights):
                norm_weights = weights / np.sum(weights)
                mixed_ks = np.dot(norm_weights, sub_sub_ks)
                return deltaE_ciede2000(target_lab, rgb2lab(np.reshape(ks_to_rgb(mixed_ks), (1, 1, 3)) / 255.0)[0][0])
            
            res = minimize(loss_function, np.ones(num_paints)/num_paints, method='L-BFGS-B', bounds=[(0, 1)]*num_paints)
            if res.fun < best_delta_e:
                best_delta_e = res.fun
                final_vol_weights = res.x / np.sum(res.x)
                densities = np.array([active_db[name][3] for name in sub_names], dtype=np.float32)
                mass_weights = final_vol_weights * densities
                mass_weights /= np.sum(mass_weights)
                best_mixed_rgb = [int(np.clip(x, 0, 255)) for x in ks_to_rgb(np.dot(final_vol_weights, sub_sub_ks))]
                best_recipe = {name: round(w * 100, 1) for name, w in zip(sub_names, mass_weights) if w > 0.01}
                
        if best_recipe:
            results[num_paints] = {'recipe': best_recipe, 'delta_e': best_delta_e, 'mixed_rgb': best_mixed_rgb}
    return results

# --- ОНБОРДИНГ ---
if "user_role" not in st.session_state: st.session_state.user_role = None
if "show_global_results" not in st.session_state: st.session_state.show_global_results = False
if "global_analysis" not in st.session_state: st.session_state.global_analysis = {}
if "global_blocks" not in st.session_state: st.session_state.global_blocks = []
if "show_results" not in st.session_state: st.session_state.show_results = False

if st.session_state.user_role is None:
    st.write("### 🎯 Выберите вашу роль:")
    if st.button("🎨 Художник-живописец / Реставратор", use_container_width=True, type="primary"): st.session_state.user_role = "painter"; st.rerun()
    if st.button("🏢 Дизайнер интерьеров / Проф-Маляр", use_container_width=True, type="primary"): st.session_state.user_role = "decorator"; st.rerun()
    if st.button("🧸 Хобби / Роспись и Warhammer", use_container_width=True, type="primary"): st.session_state.user_role = "hobby"; st.rerun()
    st.stop()

role_palettes = ALL_PALETTES if st.session_state.user_role == "hobby" else ({k: v for k, v in ALL_PALETTES.items() if "Citadel" not in k} if st.session_state.user_role == "painter" else {k: v for k, v in ALL_PALETTES.items() if "Citadel" in k})

col_logo, col_role_reset = st.columns([3, 1])
with col_role_reset:
    if st.button("🔄 Роль", use_container_width=True): st.session_state.user_role = None; st.session_state.show_results = False; st.session_state.show_global_results = False; st.rerun()

selected_brand = st.selectbox("Палитра красок:", list(role_palettes.keys()), label_visibility="collapsed")
uploaded_file = st.file_uploader("Загрузить фото", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
zoom_opt = st.radio("Масштаб картинки:", ["🔍 1x (Стандарт)", "🔍 2x (Средний)", "🔍 3x (Макси)"], horizontal=True, label_visibility="collapsed")
zoom_mul = {"🔍 1x (Стандарт)": 1.0, "🔍 2x (Средний)": 2.0, "🔍 3x (Макси)": 3.0}[zoom_opt]

col_pipette_controls, col_live_preview = st.columns([2, 1])
with col_pipette_controls:
    r = (6 if st.radio("Прицел:", ["Стандартный мазок", "Микро-точка"], horizontal=True, label_visibility="collapsed") == "Стандартный мазок" else 2) if st.session_state.user_role == "painter" else 12

with col_live_preview:
    live_circle_placeholder = st.empty()

if uploaded_file is not None:
    try:
        base_img = Image.open(io.BytesIO(uploaded_file.getvalue())).convert('RGB')
        max_w = int(350 * zoom_mul)
        base_img.thumbnail((max_w, int(base_img.size[1] * (max_w / base_img.size[0]))))
        width, height = base_img.size
        if "pos_x" not in st.session_state: st.session_state.pos_x, st.session_state.pos_y = width // 2, height // 2

        # --- ИСПРАВЛЕННАЯ ОЧЕРЕДНОСТЬ ИНСТРУКЦИЙ ---
        x_min, x_max = max(0, st.session_state.pos_x - r), min(width, st.session_state.pos_x + r)
        y_min, y_max = max(0, st.session_state.pos_y - r), min(height, st.session_state.pos_y + r)

        img_np = np.array(base_img, dtype=np.float32)
        marked_img = Image.fromarray(img_np.astype(np.uint8))
        draw = ImageDraw.Draw(marked_img)
        draw.rectangle([x_min, y_min, x_max, y_max], outline="#ff0000", width=2)
        draw.ellipse([st.session_state.pos_x-3, st.session_state.pos_y-3, st.session_state.pos_x+3, st.session_state.pos_y+3], fill="#ff0000")

        value = streamlit_image_coordinates(marked_img, key="manual_cal_canvas_v39_0")
        if value is not None and (value["x"] != st.session_state.pos_x or value["y"] != st.session_state.pos_y):
            st.session_state.pos_x, st.session_state.pos_y = value["x"], value["y"]; st.session_state.show_results = False; st.rerun()

        crop = img_np[y_min:y_max, x_min:x_max]
        avg_rgb = [int(round(x)) for x in np.mean(crop, axis=(0, 1))] if crop.size > 0 else [255, 255, 255]

        live_circle_placeholder.markdown(f'<div style="display: flex; justify-content: center; align-items: center; width: 100%; margin-top:4px;"><div style="width: 100px; height: 100px; border-radius: 50%; background-color: #{"{:02x}{:02x}{:02x}".format(*avg_rgb)}; border: 1px solid #48484a; box-shadow: 0 4px 10px rgba(0,0,0,0.4);"></div></div>', unsafe_allow_html=True)
        
        col_btn_single, col_btn_global = st.columns(2)
        with col_btn_single:
            if st.button("🔍 ТОЧКА (ПИПЕТКА)", type="primary", use_container_width=True):
                st.session_state.saved_options = calculate_mix_options(avg_rgb, role_palettes[selected_brand], None)
                comp_options_by_num = {}
                for num_key, data_val in st.session_state.saved_options.items():
                    calc_res = calculate_mix_options(get_complementary_color(data_val['mixed_rgb']), role_palettes[selected_brand], None)
                    if num_key in calc_res: comp_options_by_num[num_key] = calc_res[num_key]
                st.session_state.saved_comp_options = comp_options_by_num
                st.session_state.show_results = True; st.session_state.show_global_results = False; st.rerun()
        
        with col_btn_global:
            if st.button("📊 ВЕСЬ ХОЛСТ ЦЕЛИКОМ", use_container_width=True):
                with st.spinner("Глобальное тонально-колористическое картирование..."):
                    small_img = base_img.resize((16, 16), Image.Resampling.LANCZOS)
                    pixels = np.array(small_img, dtype=np.int32).reshape(-1, 3)
                    
                    quantized = (pixels // 32) * 32
                    unique_colors, counts = np.unique(quantized, axis=0, return_counts=True)
                    sorted_idx = np.argsort(-counts)
                    
                    top_n = min(4, len(unique_colors))
                    total_pixels = np.sum(counts)
                    
                    global_needs = {}
                    color_blocks = []
                    
                    for i in range(top_n):
                        color_rgb = unique_colors[sorted_idx[i]].astype(int)
                        weight = counts[sorted_idx[i]] / total_pixels
                        color_blocks.append({'rgb': color_rgb, 'pct': round(weight * 100, 1)})
                        
                        mix_res = calculate_mix_options(color_rgb, role_palettes[selected_brand], None)
                        best_mix = mix_res.get(3, mix_res.get(2, None))
                        if best_mix:
                            for paint, pct in best_mix['recipe'].items():
                                global_needs[paint] = global_needs.get(paint, 0.0) + (pct * weight)
                    
                    total_mass = sum(global_needs.values()) if global_needs else 1.0
                    st.session_state.global_analysis = {k: round((v / total_mass) * 100, 1) for k, v in global_needs.items()}
                    st.session_state.global_blocks = color_blocks
                    st.session_state.show_global_results = True; st.session_state.show_results = False; st.rerun()

        # --- ТУТ ПРИМЕНЕНА ОДНОСТРОЧНАЯ HTML-СБОРКА БЕЗ ОШИБОК МАРКДАУНА (v39.0) ---
        if st.session_state.show_global_results:
            st.write("### 👁️ Основные массы (Прищуренный взгляд):")
            blocks_html = '<div style="display: flex; gap: 8px; flex-wrap: nowrap; overflow-x: auto; margin-bottom: 15px;">'
            for block in st.session_state.get('global_blocks', []):
                hex_b = '#{:02x}{:02x}{:02x}'.format(*block['rgb'])
                blocks_html += f'<div style="flex: 1; min-width: 70px; text-align: center;"><div style="width: 100%; height: 40px; background-color: {hex_b}; border-radius: 8px; border: 1px solid #48484a;"></div><span style="font-size: 0.85rem; font-weight: bold; color: #fafafa !important;">{block["pct"]}%</span></div>'
            blocks_html += '</div>'
            st.markdown(blocks_html, unsafe_allow_html=True)
            
            st.write("### 📊 Необходимый объем чистых пигментов:")
            sorted_global = sorted(st.session_state.global_analysis.items(), key=lambda x: -x[1])
            for paint, percent in sorted_global:
                if percent > 0.5:
                    p_hex = '#{:02x}{:02x}{:02x}'.format(*role_palettes[selected_brand].get(paint, [128, 128, 128])[:3])
                    st.markdown(f'<div class="paint-drop-container"><div class="paint-blob" style="background-color: {p_hex};"></div><div style="font-size: 1.05rem; color:#ffffff!important;"><strong style="color:#ffffff!important;">{paint}</strong>: <span style="color: #2ecc71; font-weight: 700;">{percent}%</span></div></div>', unsafe_allow_html=True)

        if st.session_state.show_results and not st.session_state.show_global_results:
            options = st.session_state.saved_options
            comp_options = st.session_state.saved_comp_options
            
            col_sl1, col_sl2 = st.columns([1.8, 1.2])
            with col_sl1: thinner_pct = st.slider("💧 Разбавитель (+% к объёму):", 0, 40, 0, step=5)
            with col_sl2:
                ground_opt = st.radio("Подмалевок:", ["⬜ Белый", "🎨 Свой цвет"], horizontal=False)
                ground_rgb = [255, 255, 255] if "Белый" in ground_opt else [int(st.color_picker("Цвет:", "#b87333").lstrip('#')[i:i+2], 16) for i in (0, 2, 4)]

            opacity = 100.0 / (100.0 + thinner_pct)
            data2, data3 = options.get(2), options.get(3)

            st.write("### 🔸 Основной цвет:")
            donut_html_2 = generate_html_donut_macro(data2['recipe'], role_palettes[selected_brand], '#{:02x}{:02x}{:02x}'.format(*[int(np.clip(c * opacity + ground_rgb[i] * (1.0 - opacity), 0, 255)) for i, c in enumerate(data2['mixed_rgb'])]), "Замес (2 кр.)", f"Глазурь: {tuple([int(np.clip(c * opacity + ground_rgb[i] * (1.0 - opacity), 0, 255)) for i, c in enumerate(data2['mixed_rgb'])])}") if data2 else ""
            donut_html_3 = generate_html_donut_macro(data3['recipe'], role_palettes[selected_brand], '#{:02x}{:02x}{:02x}'.format(*[int(np.clip(c * opacity + ground_rgb[i] * (1.0 - opacity), 0, 255)) for i, c in enumerate(data3['mixed_rgb'])]), "Замес (3 кр.)", f"Глазурь: {tuple([int(np.clip(c * opacity + ground_rgb[i] * (1.0 - opacity), 0, 255)) for i, c in enumerate(data3['mixed_rgb'])])}") if data3 else ""
            st.markdown(f'<div style="display: flex; justify-content: space-around; align-items: flex-start; width: 100%; gap: 6px; flex-wrap: nowrap !important; margin-bottom: 10px;"><div style="flex:1; display:flex; justify-content:center;">{donut_html_2}</div><div style="flex:1; display:flex; justify-content:center;">{donut_html_3}</div></div>', unsafe_allow_html=True)

            col_left_recipe, col_right_recipe = st.columns(2)
            with col_left_recipe:
                if data2:
                    st.write("##### ✌️ Рецепт (2 кр.):")
                    for paint, percent in data2['recipe'].items():
                        st.markdown(f'<div class="paint-drop-container"><div class="paint-blob" style="background-color: #{"{:02x}{:02x}{:02x}".format(*role_palettes[selected_brand].get(paint, [128,128,128])[:3])};"></div><div style="font-size:1.02rem; color:#fff!important;"><strong style="color:#fff!important;">{paint}</strong>:<br><span style="color:#d1d1d6; font-weight:700;">{percent}%</span></div></div>', unsafe_allow_html=True)
            with col_right_recipe:
                if data3:
                    st.write("##### 🖖 Рецепт (3 кр.):")
                    for paint, percent in data3['recipe'].items():
                        st.markdown(f'<div class="paint-drop-container"><div class="paint-blob" style="background-color: #{"{:02x}{:02x}{:02x}".format(*role_palettes[selected_brand].get(paint, [128,128,128])[:3])};"></div><div style="font-size:1.02rem; color:#fff!important;"><strong style="color:#fff!important;">{paint}</strong>:<br><span style="color:#d1d1d6; font-weight:700;">{percent}%</span></div></div>', unsafe_allow_html=True)

            st.write("### 🔹 Цвета-компаньоны:")
            donut_comp_2 = generate_html_donut_macro(comp_options[2]['recipe'], role_palettes[selected_brand], '#{:02x}{:02x}{:02x}'.format(*[int(np.clip(c * opacity + ground_rgb[i] * (1.0 - opacity), 0, 255)) for i, c in enumerate(get_complementary_color(data2['mixed_rgb']))]), "Компаньон (2 кр.)", f"Глазурь: {tuple([int(np.clip(c * opacity + ground_rgb[i] * (1.0 - opacity), 0, 255)) for i, c in enumerate(get_complementary_color(data2['mixed_rgb']))])}") if data2 and 2 in comp_options else ""
            donut_comp_3 = generate_html_donut_macro(comp_options[3]['recipe'], role_palettes[selected_brand], '#{:02x}{:02x}{:02x}'.format(*[int(np.clip(c * opacity + ground_rgb[i] * (1.0 - opacity), 0, 255)) for i, c in enumerate(get_complementary_color(data3['mixed_rgb']))]), "Компаньон (3 кр.)", f"Глазурь: {tuple([int(np.clip(c * opacity + ground_rgb[i] * (1.0 - opacity), 0, 255)) for i, c in enumerate(get_complementary_color(data3['mixed_rgb']))])}") if data3 and 3 in comp_options else ""
            st.markdown(f'<div style="display: flex; justify-content: space-around; align-items: flex-start; width: 100%; gap: 6px; flex-wrap: nowrap !important; margin-bottom: 10px;"><div style="flex:1; display:flex; justify-content:center;">{donut_comp_2}</div><div style="flex:1; display:flex; justify-content:center;">{donut_comp_3}</div></div>', unsafe_allow_html=True)

            if data3:
                de = data3['delta_e']
                if de < 1.0: st.caption(f"✨ Идеальное совпадение CIEDE2000 (ΔE: {round(de, 2)})")
                elif de < 3.0: st.caption(f"👌 Профессиональная точность (ΔE: {round(de, 2)})")

        st.markdown(f'<p class="geo-badge">📍 Локация: {current_city} • Режим: {st.session_state.user_role}</p>', unsafe_allow_html=True)
    except Exception as e: st.error("⚠️ Сбой обработки фото.")
else:
    live_circle_placeholder.markdown('<div style="display: flex; justify-content: center; align-items: center; width: 100%; min-height: 40px; margin-top: 4px;"><div style="width: 100px; height: 100px; border-radius: 50%; background-color: #3a3a3c; border: 1px solid #48484a; box-shadow: 0 4px 10px rgba(0,0,0,0.4);"></div></div>', unsafe_allow_html=True)
    st.info("👋 Загрузите или снимите фото объекта для старта.")
