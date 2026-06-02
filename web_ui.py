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

# --- СТРОГИЙ ВЫСОКОКОНТРАСТНЫЙ МИНИМАЛИСТИЧНЫЙ ИНТЕРФЕЙС (v29.5) ---
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
    
    .stApp .block-container p, .stApp .block-container label, .stApp .block-container caption {
        color: #fafafa !important; font-size: 1.02rem !important; line-height: 1.3 !important;
    }
    .stApp .block-container h3 { font-size: 1.15rem !important; font-weight: 700 !important; color: #ffffff !important; margin-top: 4px !important; margin-bottom: 4px !important; }
    .stApp .block-container h5 { font-size: 0.95rem !important; font-weight: 700 !important; color: #ffffff !important; margin-top: 6px !important; margin-bottom: 6px !important; text-transform: uppercase; letter-spacing: 0.5px; }
    
    /* ГРАФИТОВЫЕ АКЦЕНТНЫЕ КНОПКИ (PRIMARY) */
    button[data-testid="baseButton-primary"], .stButton button[kind="primary"] {
        background-color: #48484a !important; color: #ffffff !important; border: 1px solid #545456 !important; border-radius: 12px !important;
        padding: 12px 20px !important; font-size: 1.05rem !important; font-weight: 700 !important; letter-spacing: 0.5px;
        text-transform: uppercase !important; margin-top: 6px !important; transition: none !important; box-shadow: none !important;
    }
    button[data-testid="baseButton-primary"]:hover { background-color: #545456 !important; }
    
    /* ВТОРОСТЕПЕННЫЕ КНОПКИ (Включая кнопку РОЛЬ и КАЛИБРОВКУ) */
    button[data-testid="baseButton-secondary"], .stButton button[kind="secondary"] {
        background-color: #3a3a3c !important; color: #ffffff !important; border: 1px solid #48484a !important; border-radius: 12px !important;
        font-size: 1.05rem !important; padding: 12px 20px !important; transition: none !important; margin-top: 6px !important;
    }
    button[data-testid="baseButton-secondary"]:hover { background-color: #48484a !important; color: #ffffff !important; }
    
    /* ЖЕСТКОЕ ИСПРАВЛЕНИЕ КОНТРАСТА СЕЛЕКТБОКСА */
    div[data-testid="stSelectbox"] > div { background-color: transparent !important; }
    div[data-testid="stSelectbox"] [data-baseweb="select"] {
        background-color: #3a3a3c !important; border: 1px solid #48484a !important; border-radius: 12px !important;
    }
    div[data-testid="stSelectbox"] [data-baseweb="select"] * { color: #ffffff !important; background-color: transparent !important; }
    div[data-baseweb="popover"] ul { background-color: #3a3a3c !important; border: 1px solid #48484a !important; }
    div[data-baseweb="popover"] li { color: #ffffff !important; background-color: transparent !important; }
    div[data-baseweb="popover"] li:hover { background-color: #48484a !important; }
    
    /* ИСПРАВЛЕНИЕ КОНТРАСТА ЗАГРУЗЧИКА ФАЙЛОВ */
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
    
    /* ФИКС ЦВЕТА НАЗВАНИЙ КРАСОК */
    .paint-drop-container { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 12px; }
    .paint-drop-container * { color: #ffffff !important; }
    .paint-blob { width: 14px; height: 14px; border-radius: 50%; margin-top: 2px; flex-shrink: 0; box-shadow: none !important; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- УЛЬТИМАТИВНАЯ БАЗА КРАСОК ---
def load_all_paints_v23():
    return {
        "Citadel Base (Warhammer / Миниатюры)": {
            "Corax White (Белый)": [240, 242, 245], "Abaddon Black (Черный)": [10, 10, 10],
            "Mephiston Red (Красный)": [154, 14, 24], "Macragge Blue (Синий)": [15, 41, 130],
            "Averland Sunset (Желтый)": [243, 180, 10], "Waaagh! Flesh (Зеленый)": [30, 73, 43],
            "Bugman's Glow (Телесный)": [128, 75, 64], "Balthasar Gold (Бронза/Охра)": [140, 105, 67],
            "Naggaroth Night (Фиолетовый)": [59, 41, 84]
        },
        "Vallejo Model Color (Акрил для росписи)": {
            "Foundation White (70.951)": [253, 253, 253], "Black (70.950)": [20, 20, 20],
            "Flat Red (70.957)": [179, 35, 35], "Royal Blue (70.962)": [26, 50, 133],
            "Flat Yellow (70.953)": [240, 210, 14], "Olive Green (70.967)": [74, 94, 43],
            "Light Flesh (70.928)": [242, 191, 162], "Chocolate Brown (70.872)": [87, 59, 46]
        },
        "Невская Палитра (Масло Мастер-Класс)": {
            "Белила титановые": [255, 255, 255], "Неаполитанская желтая": [245, 218, 154],
            "Кадмий желтый светлый": [254, 207, 0], "Охра светлая": [212, 163, 89],
            "Кадмий красный светлый": [227, 38, 54], "Краплак красный прочный": [140, 22, 46],
            "Ультрамарин светлый": [65, 102, 245], "Кобальт синий спектральный": [0, 71, 171],
            "Изумрудная зеленая": [0, 165, 114], "Умбра жженая": [94, 62, 43],
            "Виноградная черная": [41, 40, 38], "Сажа газовая": [15, 15, 15]
        },
        "Maimeri Classico (Италия, Масло)": {
            "Zinc White (Цинковые)": [255, 255, 250], "Titanium White (Титановые)": [253, 253, 253],
            "Naples Yellow Reddish": [244, 194, 145], "Permanent Yellow Light": [252, 214, 0],
            "Yellow Ochre": [219, 168, 79], "Vermilion Light (Имит.)": [218, 54, 46],
            "Burnt Sienna": [138, 51, 36], "Ultramarine Blue": [27, 43, 156],
            "Phthalo Blue": [11, 45, 103], "Permanent Green Light": [46, 150, 67],
            "Raw Umber": [110, 89, 64], "Vine Black (Виноградная)": [38, 38, 37],
            "Ivory Black": [22, 22, 22]
        },
        "Royal Talens Van Gogh (Акрил/Масло)": {
            "Titanium White (105)": [255, 255, 255], "Naples Yellow Light (222)": [250, 224, 172],
            "Azo Yellow Light (268)": [255, 221, 0], "Azo Orange (276)": [247, 120, 32],
            "Azo Red Light (312)": [222, 34, 44], "Quinacridone Rose (366)": [196, 20, 94],
            "Ultramarine (504)": [38, 50, 156], "Cerulean Blue Phthalo (535)": [0, 114, 179],
            "Permanent Green Deep (619)": [16, 112, 58], "Yellow Ochre (227)": [204, 150, 69],
            "Burnt Umber (409)": [77, 52, 41], "Vandyke Brown (403)": [56, 43, 38],
            "Oxide Black (735)": [28, 28, 28]
        },
        "Tikkurila Symphony (Интерьерная)": {
            "База AP (Белая)": [250, 250, 248], "F300 (Жасмин)": [242, 232, 208], "☀️ H300 (Персик)": [247, 214, 173],
            "M300 (Глина)": [194, 157, 126], "V381 (Аметист)": [142, 134, 156], "N494 (Нефрит)": [84, 115, 102],
            "🎨 База C (Прозрачная/Черная)": [40, 41, 43]
        },
        "Интерьерная палитра RAL (Классика)": {
            "RAL 9016 (Белый)": [247, 249, 250], "RAL 1015 (Сл. кость)": [230, 214, 184],
            "RAL 1018 (Желтый)": [247, 211, 43], "RAL 3020 (Красный)": [187, 30, 16],
            "RAL 5002 (Синий)": [22, 43, 115], "RAL 6002 (Зеленый)": [50, 102, 46],
            "RAL 7016 (Серый)": [56, 62, 66], "RAL 9005 (Черный)": [14, 14, 16]
        }
    }

ALL_PALETTES = load_all_paints_v23()

def get_market_and_coverage_data():
    try:
        res = requests.get("http://ip-api.com/json/", timeout=1.5).json()
        country, city = res.get("countryCode", "RU"), res.get("city", "Москва")
    except:
        country, city = "RU", "Локальная сеть"
    coverage_rates = {
        "Citadel Base (Warhammer / Миниатюры)": 130, "Vallejo Model Color (Акрил для росписи)": 135,
        "Невская Палитра (Масло Мастер-Класс)": 180, "Maimeri Classico (Италия, Масло)": 185,
        "Royal Talens Van Gogh (Акрил/Масло)": 145, "Tikkurila Symphony (Интерьерная)": 120,
        "Интерьерная палитра RAL (Классика)": 120
    }
    if country == "RU":
        currency = "руб."
        price_rates = { "Citadel Base (Warhammer / Миниатюры)": 450, "Vallejo Model Color (Акрил для росписи)": 380, "Невская Палитра (Масло Мастер-Класс)": 580, "Maimeri Classico (Италия, Масло)": 950, "Royal Talens Van Gogh (Акрил/Масло)": 720, "Tikkurila Symphony (Интерьерная)": 210, "Интерьерная палитра RAL (Классика)": 180 }
    else:
        currency = "€"
        price_rates = { "Citadel Base (Warhammer / Миниатюры)": 4.5, "Vallejo Model Color (Акрил для росписи)": 3.9, "Невская Палитра (Масло Мастер-Класс)": 9.5, "Maimeri Classico (Италия, Масло)": 14.8, "Royal Talens Van Gogh (Акрил/Масло)": 11.2, "Tikkurila Symphony (Интерьерная)": 3.8, "Интерьерная палитра RAL (Классика)": 3.4 }
    return city, currency, price_rates, coverage_rates

if "geo_cache" not in st.session_state: st.session_state.geo_cache = get_market_and_coverage_data()
current_city, current_currency, market_prices, brand_coverages = st.session_state.geo_cache

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
        rgb = paint_db.get(paint, [128, 128, 128])
        hex_str = '#{:02x}{:02x}{:02x}'.format(*rgb)
        next_pct = current_pct + pct
        gradient_parts.append(f"{hex_str} {current_pct}% {next_pct}%")
        current_pct = next_pct
    gradient_str = ", ".join(gradient_parts) if gradient_parts else "#3a3a3c 0% 100%"
    
    html = f"""
    <div style="display: flex; flex-direction: column; align-items: center; margin: 10px auto;">
        <div style="width: 140px; height: 140px; border-radius: 50%; background: conic-gradient({gradient_str}); display: flex; align-items: center; justify-content: center;">
            <div style="width: 88px; height: 88px; border-radius: 50%; background-color: {center_hex}; display: flex; align-items: center; justify-content: center;">
            </div>
        </div>
        <span style="font-size: 0.92rem; margin-top: 8px; font-weight: bold; color: #ffffff !important; text-align: center; line-height: 1.2;">{label_text}<br><span style="font-size: 0.76rem; font-weight: normal; opacity: 0.8; color: #8a8a8f !important;">{sub_text}</span></span>
    </div>
    """
    return html

def calculate_mix_options(target_rgb, db, allowed_paints=None):
    active_db = {k: v for k, v in db.items() if k in allowed_paints} if allowed_paints else db
    paint_names = list(active_db.keys())
    if len(paint_names) == 0: return {}
        
    paint_rgbs = np.array([active_db[name] for name in paint_names], dtype=np.float32)
    target_rgb_norm = np.array([[target_rgb]], dtype=np.float32) / 255.0
    target_lab = rgb2lab(target_rgb_norm)[0][0]
    
    results = {}
    for num_paints in [2, 3]:
        if len(paint_names) < num_paints: continue
        
        combo_candidates = []
        for indices in itertools.combinations(range(len(paint_names)), num_paints):
            sub_names = [paint_names[i] for i in indices]
            sub_sub_rgbs = paint_rgbs[list(indices)]
            avg_paint_rgb = np.mean(sub_sub_rgbs, axis=0)
            rgb_dist = np.sum((avg_paint_rgb - target_rgb) ** 2)
            combo_candidates.append((rgb_dist, indices, sub_names, sub_sub_rgbs))
        
        combo_candidates.sort(key=lambda x: x[0])
        top_candidates = combo_candidates[:12]
        best_recipe, best_delta_e, best_mixed_rgb = {}, float('inf'), [255, 255, 255]
        
        for _, indices, sub_names, sub_sub_rgbs in top_candidates:
            def loss_function(weights):
                norm_weights = weights / np.sum(weights)
                mixed_rgb = np.dot(norm_weights, sub_sub_rgbs)
                mixed_rgb_norm = np.reshape(mixed_rgb, (1, 1, 3)) / 255.0
                return deltaE_ciede2000(target_lab, rgb2lab(mixed_rgb_norm)[0][0])
            
            bounds = [(0, 1) for _ in range(num_paints)]
            init_weights = np.ones(num_paints) / num_paints
            res = minimize(loss_function, init_weights, method='L-BFGS-B', bounds=bounds)
            
            if res.fun < best_delta_e:
                best_delta_e = res.fun
                final_weights = res.x / np.sum(res.x)
                mixed_rgb_np = np.dot(final_weights, sub_sub_rgbs)
                best_mixed_rgb = [int(np.clip(x, 0, 255)) for x in mixed_rgb_np]
                
                current_recipe = {}
                for name, weight in zip(sub_names, final_weights):
                    if weight > 0.01:
                        percent = round(weight * 100, 1)
                        if percent > 0: current_recipe[name] = percent
                best_recipe = current_recipe
                
        if best_recipe:
            results[num_paints] = {'recipe': best_recipe, 'delta_e': best_delta_e, 'mixed_rgb': best_mixed_rgb}
    return results

# --- ОНБОРДИНГ ---
if "user_role" not in st.session_state: st.session_state.user_role = None

if st.session_state.user_role is None:
    st.write("### 🎯 Выберите вашу роль:")
    if st.button("🎨 Художник-живописец / Реставратор", use_container_width=True, type="primary"): st.session_state.user_role = "painter"; st.rerun()
    if st.button("🏢 Дизайнер интерьеров / Проф-Маляр", use_container_width=True, type="primary"): st.session_state.user_role = "decorator"; st.rerun()
    if st.button("🧸 Хобби / Роспись и Warhammer", use_container_width=True, type="primary"): st.session_state.user_role = "hobby"; st.rerun()
    st.stop()

if st.session_state.user_role == "painter":
    role_palettes = {k: v for k, v in ALL_PALETTES.items() if "Tikkurila" not in k and "RAL" not in k and "Citadel" not in k and "Vallejo" not in k}
    default_r = 6
elif st.session_state.user_role == "decorator":
    role_palettes = {k: v for k, v in ALL_PALETTES.items() if "Tikkurila" in k or "RAL" in k}
    default_r = 12
else:
    role_palettes = ALL_PALETTES
    default_r = 10

if "calibration_mode" not in st.session_state: st.session_state.calibration_mode = False
if "white_multipliers" not in st.session_state: st.session_state.white_multipliers = np.array([1.0, 1.0, 1.0], dtype=np.float32)
if "saved_options" not in st.session_state: st.session_state.saved_options = {}
if "saved_comp_options" not in st.session_state: st.session_state.saved_comp_options = {}
if "show_results" not in st.session_state: st.session_state.show_results = False
if "active_num" not in st.session_state: st.session_state.active_num = 3

col_logo, col_role_reset = st.columns([3, 1])
with col_role_reset:
    if st.button("🔄 Роль", use_container_width=True): st.session_state.user_role = None; st.rerun()

selected_brand = st.selectbox("Палитра красок:", list(role_palettes.keys()), label_visibility="collapsed")

user_stock = None
if st.session_state.user_role != "painter":
    user_stock = st.multiselect("♻️ Мой склад (утилизация остатков):", options=list(role_palettes[selected_brand].keys()), default=None, placeholder="Всё в наличии...")

uploaded_file = st.file_uploader("Загрузить фото", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

zoom_opt = st.radio("Масштаб картинки:", ["🔍 1x (Стандарт)", "🔍 2x (Средний)", "🔍 3x (Макси)"], horizontal=True, label_visibility="collapsed")
zoom_mul = {"🔍 1x (Стандарт)": 1.0, "🔍 2x (Средний)": 2.0, "🔍 3x (Макси)": 3.0}[zoom_opt]

col_pipette_controls, col_live_preview = st.columns([3, 1])
with col_pipette_controls:
    if st.session_state.user_role == "painter":
        pipette_kind = st.radio("Прицел:", ["Стандартный мазок", "Микро-точка"], horizontal=True, label_visibility="collapsed")
        r = 6 if pipette_kind == "Стандартный мазок" else 2
    else:
        pipette_kind = st.radio("Прицел:", ["Стандартная пипетка", "Макси-область"], horizontal=True, label_visibility="collapsed")
        r = 10 if pipette_kind == "Стандартная пипетка" else 24

with col_live_preview:
    live_circle_placeholder = st.empty()

if st.session_state.user_role != "painter":
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("⬜ Калибровка", use_container_width=True): st.session_state.calibration_mode = True; st.rerun()
    with col_btn2:
        if st.button("♻️ Сбросить свет", use_container_width=True):
            st.session_state.white_multipliers = np.array([1.0, 1.0, 1.0], dtype=np.float32); st.session_state.calibration_mode = False; st.session_state.show_results = False; st.rerun()
else:
    st.session_state.white_multipliers = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    st.session_state.calibration_mode = False

if uploaded_file is not None:
    try:
        base_img = Image.open(io.BytesIO(uploaded_file.getvalue())).convert('RGB')
        max_w = int(350 * zoom_mul)
        base_img.thumbnail((max_w, int(base_img.size[1] * (max_w / base_img.size[0]))))
        width, height = base_img.size
        
        if "pos_x" not in st.session_state: st.session_state.pos_x, st.session_state.pos_y = width // 2, height // 2

        img_np = np.array(base_img, dtype=np.float32)
        corrected_np = np.clip(img_np * st.session_state.white_multipliers, 0, 255).astype(np.uint8)
        
        x_min, x_max = max(0, st.session_state.pos_x - r), min(width, st.session_state.pos_x + r)
        y_min, y_max = max(0, st.session_state.pos_y - r), min(height, st.session_state.pos_y + r)
        
        crop = corrected_np[y_min:y_max, x_min:x_max]
        avg_rgb = [int(round(x)) for x in np.mean(crop, axis=(0, 1))] if crop.size > 0 else [255, 255, 255]
        
        marked_img = Image.fromarray(corrected_np)
        draw = ImageDraw.Draw(marked_img)
        draw.rectangle([x_min, y_min, x_max, y_max], outline="#ffffff", width=2)
        draw.ellipse([st.session_state.pos_x-3, st.session_state.pos_y-3, st.session_state.pos_x+3, st.session_state.pos_y+3], fill="#ffffff")

        if st.session_state.calibration_mode: st.warning("🎯 Тапните в белую/серую точку на фото!")

        value = streamlit_image_coordinates(marked_img, key="manual_cal_canvas_v29_5")
        if value is not None:
            cx, cy = value["x"], value["y"]
            if st.session_state.calibration_mode:
                raw_crop = img_np[max(0, cy-2):min(height, cy+2), max(0, cx-2):min(width, cx+3)]
                mean_rgb = np.mean(raw_crop, axis=(0, 1))
                if np.mean(mean_rgb) > 0: st.session_state.white_multipliers = np.mean(mean_rgb) / mean_rgb
                st.session_state.calibration_mode = False; st.session_state.show_results = False; st.rerun()
            elif cx != st.session_state.pos_x or cy != st.session_state.pos_y:
                st.session_state.pos_x, st.session_state.pos_y = cx, cy; st.session_state.show_results = False; st.rerun()

        light_env = "☀️ День (5500K)"
        if st.session_state.user_role != "painter":
            light_env = st.radio("Освещение:", ["☀️ День (5500K)", "💡 Лампа (3000K)"], horizontal=True, label_visibility="collapsed")
        
        simulated_rgb = list(avg_rgb)
        if light_env == "💡 Лампа (3000K)":
            simulated_rgb[0] = min(255, int(simulated_rgb[0] * 1.15))
            simulated_rgb[1] = min(255, int(simulated_rgb[1] * 1.05))
            simulated_rgb[2] = max(0, int(simulated_rgb[2] * 0.80))

        hex_color = '#{:02x}{:02x}{:02x}'.format(*simulated_rgb)
        
        live_circle_placeholder.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; height: 100%; min-height: 40px;">
            <div style="width: 36px; height: 36px; border-radius: 50%; background-color: {hex_color}; border: 1px solid #48484a;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔍 ПОДОБРАТЬ РЕЦЕПТ", type="primary", use_container_width=True):
            with st.spinner("Мгновенный квантовый расчет..."):
                options = calculate_mix_options(avg_rgb, role_palettes[selected_brand], user_stock)
                st.session_state.saved_options = options
                
                comp_options_by_num = {}
                for num_key, data_val in options.items():
                    c_rgb = get_complementary_color(data_val['mixed_rgb'])
                    calc_res = calculate_mix_options(c_rgb, role_palettes[selected_brand], user_stock)
                    if num_key in calc_res:
                        comp_options_by_num[num_key] = calc_res[num_key]
                st.session_state.saved_comp_options = comp_options_by_num
                st.session_state.show_results = True

        if st.session_state.show_results:
            options = st.session_state.saved_options
            comp_options = st.session_state.saved_comp_options
            
            if not options:
                st.error("⚠️ Недостаточно пигментов для создания замеса.")
            else:
                if st.session_state.user_role == "decorator":
                    c1, c2 = st.columns(2)
                    with c1: input_area = st.number_input("Площадь (м²):", min_value=0.1, max_value=500.0, value=1.0, step=0.5)
                    with c2: input_layers = st.number_input("Слои:", min_value=1, max_value=5, value=2, step=1)
                    auto_w = round(input_area * input_layers * brand_coverages.get(selected_brand, 120), 1)
                    total_weight = st.number_input(f"Вес замеса (расход ~{auto_w}г):", min_value=1.0, value=float(auto_w))
                else:
                    total_weight = 100.0

                is_upcycled = user_stock and len(user_stock) > 0
                if is_upcycled: st.success("♻️ АПСАЙКЛИНГ: Рецепты собраны из остатков!")

                if st.session_state.active_num not in options and options:
                    st.session_state.active_num = list(options.keys())[0]

                col_toggle_l, col_toggle_r = st.columns(2)
                with col_toggle_l:
                    b2_type = "primary" if st.session_state.active_num == 2 else "secondary"
                    if st.button("✌️ 2 пигмента", use_container_width=True, type=b2_type, disabled=(2 not in options)):
                        st.session_state.active_num = 2
                        st.rerun()
                with col_toggle_r:
                    b3_type = "primary" if st.session_state.active_num == 3 else "secondary"
                    if st.button("🖖 3 пигмента", use_container_width=True, type=b3_type, disabled=(3 not in options)):
                        st.session_state.active_num = 3
                        st.rerun()

                num = st.session_state.active_num
                data = options[num]
                
                m_rgb = data['mixed_rgb']
                c_rgb = get_complementary_color(m_rgb)
                m_hex, c_hex = '#{:02x}{:02x}{:02x}'.format(*m_rgb), '#{:02x}{:02x}{:02x}'.format(*c_rgb)
                
                col_donut_l, col_donut_r = st.columns(2)
                with col_donut_l:
                    donut_html_main = generate_html_donut_macro(data['recipe'], role_palettes[selected_brand], m_hex, f"Реал. замес ({num} кр.)", f"RGB: {tuple(m_rgb)}")
                    st.markdown(donut_html_main, unsafe_allow_html=True)
                with col_donut_r:
                    if num in comp_options:
                        donut_html_comp = generate_html_donut_macro(comp_options[num]['recipe'], role_palettes[selected_brand], c_hex, "Компаньон", f"RGB: {tuple(c_rgb)}")
                        st.markdown(donut_html_comp, unsafe_allow_html=True)
                
                col_left_recipe, col_right_recipe = st.columns(2)
                raw_text = f"🎨 ИИ-КОЛОРИСТ ({num} пигмента)\\n\\n[ОСНОВНОЙ ЦВЕТ]\\n"
                
                with col_left_recipe:
                    st.write("##### 🔸 Основной цвет:")
                    for paint, percent in data['recipe'].items():
                        g = round((percent / 100.0) * total_weight, 2)
                        p_rgb = role_palettes[selected_brand].get(paint, [128, 128, 128])
                        p_hex = '#{:02x}{:02x}{:02x}'.format(*p_rgb)
                        
                        weight_str = f" → <b>{g} г.</b>" if st.session_state.user_role == "decorator" else ""
                        # ВШИТЫ СТИЛИ ЦВЕТА НАПРЯМУЮ: color: #ffffff !important;
                        st.markdown(f"""
                        <div class="paint-drop-container">
                            <div class="paint-blob" style="background-color: {p_hex};"></div>
                            <div style="font-size: 1.02rem; line-height: 1.3; color: #ffffff !important;">
                                <strong style="color: #ffffff !important;">{paint}</strong>:<br>
                                <span style="color: #d1d1d6; font-weight: 700;">{percent}%</span>{weight_str}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        raw_text += f"🔸 {paint}: {percent}%\\n"
                
                with col_right_recipe:
                    if num in comp_options:
                        comp_data = comp_options[num]
                        st.write("##### 🔹 Компаньон:")
                        raw_text += f"\\n[ЦВЕТ-КОМПАНЬОН - {c_hex}]\\n"
                        for paint, percent in comp_data['recipe'].items():
                            g = round((percent / 100.0) * total_weight, 2)
                            p_rgb = role_palettes[selected_brand].get(paint, [128, 128, 128])
                            p_hex = '#{:02x}{:02x}{:02x}'.format(*p_rgb)
                            
                            weight_str = f" → <b>{g} г.</b>" if st.session_state.user_role == "decorator" else ""
                            # ВШИТЫ СТИЛИ ЦВЕТА НАПРЯМУЮ: color: #ffffff !important;
                            st.markdown(f"""
                            <div class="paint-drop-container">
                                <div class="paint-blob" style="background-color: {p_hex};"></div>
                                <div style="font-size: 1.02rem; line-height: 1.3; color: #ffffff !important;">
                                    <strong style="color: #ffffff !important;">{paint}</strong>:<br>
                                    <span style="color: #d1d1d6; font-weight: 700;">{percent}%</span>{weight_str}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            raw_text += f"🔹 {paint}: {percent}%\\n"

                st.write("")
                if st.session_state.user_role == "decorator":
                    cost = 0 if is_upcycled else round((total_weight / 100.0) * market_prices.get(selected_brand, 150), 2)
                    st.markdown(f'💸 **Затраты:** `{cost} {current_currency}`' if not is_upcycled else "💸 **Затраты:** `0 (Из остатков)`")
                
                st.components.v1.html(f"""
                    <button id="btn{num}" style="width: 100%; background-color: #3a3a3c; color: #fafafa; border: 1px solid #48484a; border-radius: 12px; font-size: 1rem; padding: 10px; font-weight: 700; cursor: pointer; text-transform: uppercase;">📋 Скопировать обе формулы</button>
                    <textarea id="txt{num}" style="position: absolute; left: -9999px;">{raw_text}</textarea>
                    <script>
                    document.getElementById('btn{num}').addEventListener('click', function() {{
                        var t = document.getElementById('txt{num}'); t.select(); t.setSelectionRange(0, 99999);
                        if (document.execCommand('copy')) {{
                            this.innerText = '✅ Обе формулы в буфере!'; this.style.backgroundColor = '#545456'; this.style.borderColor = '#545456'; this.style.color = '#fff';
                            setTimeout(() => {{ this.innerText = '📋 Скопировать обе формулы'; this.style.backgroundColor = '#3a3a3c'; this.style.borderColor = '#48484a'; this.style.color = '#fafafa'; }}, 2000);
                        }}
                    }});
                    </script>
                """, height=55)

                de = data['delta_e']
                if de < 1.0: st.caption(f"✨ Идеальное совкадение CIEDE2000 (ΔE: {round(de, 2)})")
                elif de < 3.0: st.caption(f"👌 Профессиональная точность (ΔE: {round(de, 2)})")
                else: st.warning(f"⚠️ Тон близок к пределу палитры (ΔE: {round(de, 2)})")

            st.markdown(f'<p class="geo-badge">📍 Локация: {current_city} • Режим: {st.session_state.user_role}</p>', unsafe_allow_html=True)
    except Exception as e:
        st.error("⚠️ Сбой обработки фото.")
else:
    live_circle_placeholder.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; height: 100%; min-height: 40px;">
        <div style="width: 36px; height: 36px; border-radius: 50%; background-color: #3a3a3c; border: 1px solid #48484a;"></div>
    </div>
    """, unsafe_allow_html=True)
    st.info("👋 Загрузите или снимите фото объекта для старта.")
