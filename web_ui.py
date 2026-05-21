import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
from scipy.optimize import minimize
from streamlit_image_coordinates import streamlit_image_coordinates
from skimage.color import rgb2lab, deltaE_cie76
import json
import os
import itertools
import io
import requests

# Настройка страницы
st.set_page_config(page_title="ИИ-Колорист PRO", page_icon="🎨", layout="centered")

# --- СУПЕР-МИНИМАЛИСТИЧНЫЙ CSS (v18.0 — Zero-Waste склад) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #222224 !important;
    }

    @media (min-width: 576px) {
        .main .block-container {
            max-width: 410px !important;
            padding: 0.6rem 0.6rem !important; 
            border: 1px solid #3a3a3c !important;
            border-radius: 25px !important;
            background-color: #222224 !important; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
            margin-top: 10px !important;
            margin-bottom: 10px !important;
        }
    }
    
    .main .block-container p, 
    .main .block-container span,
    .main .block-container label,
    .main .block-container caption,
    .main .block-container div {
        color: #fafafa !important; 
        font-size: 1.05rem !important;
        line-height: 1.3 !important;
    }

    .main .block-container h3 {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        margin-top: 4px !important;
        margin-bottom: 4px !important;
    }

    /* СТАТИЧНАЯ ЗЕЛЕНАЯ КНОПКА */
    button[data-testid="baseButton-primary"], 
    .stButton button[kind="primary"] {
        background-color: #2ecc71 !important; 
        color: #000000 !important; 
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 20px !important;
        font-size: 1.15rem !important; 
        font-weight: 800 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        margin-top: 6px !important;
        transition: none !important; 
        box-shadow: none !important;
    }
    button[data-testid="baseButton-primary"]:hover { background-color: #27ae60 !important; }

    /* Второстепенные компактные кнопки */
    button[data-testid="baseButton-secondary"] {
        background-color: #3a3a3c !important;
        color: #fafafa !important;
        border: 1px solid #48484a !important;
        border-radius: 12px !important;
        font-size: 0.95rem !important;
        padding: 8px 12px !important;
    }

    /* Радио-кнопки */
    div[data-testid="stRadio"] div[data-baseweb="radio"] {
        padding: 4px 10px !important;
        background-color: #3a3a3c !important;
        border-radius: 10px !important;
        margin-right: 8px !important;
    }

    /* Кастомизация мультиселекта под тёмную тему склада */
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] {
        background-color: #3a3a3c !important;
        border: 1px solid #48484a !important;
        border-radius: 12px !important;
    }
    div[data-testid="stMultiSelect"] span {
        background-color: #222224 !important;
        color: #ffffff !important;
        border-radius: 6px !important;
    }

    /* Индикатор цвета */
    .stApp .block-container div[style*="background-color:"] {
        border-radius: 12px !important;
        border: 2px solid #ffffff !important; 
        margin-top: 6px !important;
        margin-bottom: 4px !important;
    }

    /* Инпуты */
    div[data-testid="stNumberInput"] input {
        background-color: #3a3a3c !important;
        color: #ffffff !important;
        border: 1px solid #48484a !important;
        border-radius: 10px !important;
        padding: 6px !important;
    }

    div[data-testid="stNotification"] {
        background-color: #2c2c2e !important;
        border: 1px solid #3a3a3c !important;
        border-radius: 12px !important;
        padding: 8px !important;
        margin-top: 4px !important;
        margin-bottom: 6px !important;
    }

    .geo-badge {
        font-size: 0.85rem !important;
        color: #8a8a8f !important;
        text-align: center;
        margin-top: 8px !important;
    }
    hr { margin: 6px 0 !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p style="font-size: 0.85rem; color: #8a8a8f; text-align: center; margin-top: 0px; margin-bottom: 8px; letter-spacing: 0.5px;">ai подбор краски • ai upcycling pro</p>', unsafe_allow_html=True)

# --- ГЕОЛОКАЦИЯ, ЦЕНЫ И УКРЫВИСТОСТЬ ---
def get_market_and_coverage_data():
    try:
        res = requests.get("http://ip-api.com/json/", timeout=1.5).json()
        country = res.get("countryCode", "RU")
        city = res.get("city", "Москва")
    except:
        country = "RU"
        city = "Локальная сеть"
        
    coverage_rates = {
        "Невская Палитра (Масло Мастер-Класс)": 180, "Невская Палитра (Акрил)": 140,
        "Vista-Artista (Акрил)": 140, "Pebeo Studio (Акрил)": 130,
        "Tikkurila Symphony (Интерьерная)": 120, "Husky Interior (Хаски)": 125,
        "Интерьерная палитра RAL (Классика)": 120
    }
        
    if country == "RU":
        currency = "руб."
        price_rates = {
            "Невская Палитра (Масло Мастер-Класс)": 550, "Невская Палитра (Акрил)": 280,
            "Vista-Artista (Акрил)": 180, "Pebeo Studio (Акрил)": 350,
            "Tikkurila Symphony (Интерьерная)": 190, "Husky Interior (Хаски)": 140,
            "Интерьерная палитра RAL (Классика)": 160
        }
    else:
        currency = "€"
        price_rates = {
            "Невская Палитра (Масло Мастер-Класс)": 9.5, "Невская Палитра (Акрил)": 4.5,
            "Vista-Artista (Акрил)": 3.0, "Pebeo Studio (Акрил)": 5.8,
            "Tikkurila Symphony (Интерьерная)": 3.8, "Husky Interior (Хаски)": 2.8,
            "Интерьерная палитра RAL (Классика)": 3.2
        }
    return city, currency, price_rates, coverage_rates

if "geo_cache" not in st.session_state:
    st.session_state.geo_cache = get_market_and_coverage_data()
current_city, current_currency, market_prices, brand_coverages = st.session_state.geo_cache

# --- ЗАГРУЗКА БАЗЫ КРАСОК ---
def load_all_paints():
    json_path = "paints.json"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f: return json.load(f)
    return {"Дефолтная": {"Белила": [255,255,255], "Черная": [0,0,0]}}

ALL_PALETTES = load_all_paints()

# --- ИИ-МИКШЕР С ИНТЕГРАЦИЕЙ РЕЖИМА АПСАЙКЛИНГА ---
def calculate_mix_recipe_lab(target_rgb, db, allowed_paints=None):
    # Если мастер выбрал конкретные остатки, сужаем базу данных до этого списка
    if allowed_paints and len(allowed_paints) > 0:
        active_db = {k: v for k, v in db.items() if k in allowed_paints}
    else:
        active_db = db

    paint_names = list(active_db.keys())
    if len(paint_names) == 0:
        return {}, float('inf')
        
    paint_rgbs = np.array([active_db[name] for name in paint_names], dtype=np.float32)
    target_rgb_norm = np.array([[target_rgb]], dtype=np.float32) / 255.0
    target_lab = rgb2lab(target_rgb_norm)[0][0]
    
    best_recipe = {}
    best_delta_e = float('inf')
    
    # Безопасный цикл с учётом малого количества остатков на складе
    max_components = min(len(paint_names), 3)
    
    for num_paints in range(1, max_components + 1):
        for indices in itertools.combinations(range(len(paint_names)), num_paints):
            sub_names = [paint_names[i] for i in indices]
            sub_sub_rgbs = paint_rgbs[list(indices)]
            
            def loss_function(weights):
                norm_weights = weights / np.sum(weights)
                mixed_rgb = np.dot(norm_weights, sub_sub_rgbs)
                mixed_rgb_norm = np.reshape(mixed_rgb, (1, 1, 3)) / 255.0
                mixed_lab = rgb2lab(mixed_rgb_norm)[0][0]
                return deltaE_cie76(target_lab, mixed_lab)
            
            bounds = [(0, 1) for _ in range(num_paints)]
            init_weights = np.ones(num_paints) / num_paints
            res = minimize(loss_function, init_weights, method='L-BFGS-B', bounds=bounds)
            
            if res.fun < best_delta_e:
                best_delta_e = res.fun
                final_weights = res.x / np.sum(res.x)
                current_recipe = {}
                for name, weight in zip(sub_names, final_weights):
                    if weight > 0.01:
                        percent = round(weight * 100, 1)
                        if percent > 0: current_recipe[name] = percent
                best_recipe = current_recipe
                
    return best_recipe, best_delta_e

if "calibration_mode" not in st.session_state: st.session_state.calibration_mode = False
if "white_multipliers" not in st.session_state: st.session_state.white_multipliers = np.array([1.0, 1.0, 1.0], dtype=np.float32)
if "saved_recipe" not in st.session_state: st.session_state.saved_recipe = None
if "saved_delta_e" not in st.session_state: st.session_state.saved_delta_e = 0.0
if "show_results" not in st.session_state: st.session_state.show_results = False

selected_brand = st.selectbox("Палитра красок:", list(ALL_PALETTES.keys()), label_visibility="collapsed")

# --- ИННОВАЦИОННЫЙ ИНТЕРФЕЙС: МОЙ СКЛАД (ОСТАТКИ) ---
available_colors = list(ALL_PALETTES[selected_brand].keys())
user_stock = st.multiselect(
    "♻️ Мой склад (выберите остатки красок):",
    options=available_colors,
    default=None,
    placeholder="Всё в наличии (или выберите остатки)..."
)

uploaded_file = st.file_uploader("Загрузить фото", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

pipette_kind = st.radio("Прицел:", ["Стандартная пипетка", "Макси-область"], horizontal=True, label_visibility="collapsed")
r = 8 if pipette_kind == "Стандартная пипетка" else 22

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("⬜ Калибровка", use_container_width=True):
        st.session_state.calibration_mode = True
        st.rerun()
with col_btn2:
    if st.button("♻️ Сбросить свет", use_container_width=True):
        st.session_state.white_multipliers = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        st.session_state.calibration_mode = False
        st.session_state.show_results = False
        st.rerun()

CURRENT_PAINTS_DB = ALL_PALETTES[selected_brand]

if uploaded_file is not None:
    base_img = None
    try:
        image_bytes = uploaded_file.getvalue()
        base_img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    except:
        st.error("⚠️ Сбой загрузки. Сделайте скриншот картинки на Айфоне и загрузите его!")

    if base_img is not None:
        max_w = 350
        orig_w, orig_h = base_img.size
        ratio = max_w / orig_w
        max_h = int(orig_h * ratio)
        base_img.thumbnail((max_w, max_h)) 
        width, height = base_img.size
        
        if "pos_x" not in st.session_state:
            st.session_state.pos_x = width // 2
            st.session_state.pos_y = height // 2

        img_np = np.array(base_img, dtype=np.float32)
        corrected_np = np.clip(img_np * st.session_state.white_multipliers, 0, 255).astype(np.uint8)
        corrected_img = Image.fromarray(corrected_np)

        x_min, x_max = max(0, st.session_state.pos_x - r), min(width, st.session_state.pos_x + r)
        y_min, y_max = max(0, st.session_state.pos_y - r), min(height, st.session_state.pos_y + r)
        
        crop = corrected_np[y_min:y_max, x_min:x_max]
        if crop.size > 0:
            mean_rgb = np.mean(crop, axis=(0, 1))
            avg_rgb = [int(round(mean_rgb[0])), int(round(mean_rgb[1])), int(round(mean_rgb[2]))]
        else:
            avg_rgb = [255, 255, 255]
        
        marked_img = corrected_img.copy()
        draw = ImageDraw.Draw(marked_img)
        draw.rectangle([x_min, y_min, x_max, y_max], outline="#ffffff", width=2) 
        draw.ellipse([st.session_state.pos_x-3, st.session_state.pos_y-3, st.session_state.pos_x+3, st.session_state.pos_y+3], fill="#ffffff")

        if st.session_state.calibration_mode: st.warning("🎯 Тапните в белую/серую точку на фото!")

        value = streamlit_image_coordinates(marked_img, key="manual_cal_canvas_v18")
        if value is not None:
            clicked_x, clicked_y = value["x"], value["y"]
            if st.session_state.calibration_mode:
                raw_crop = img_np[max(0, clicked_y-2):min(height, clicked_y+2), max(0, clicked_x-2):min(width, clicked_x+3)]
                raw_rgb = np.mean(raw_crop, axis=(0, 1))
                mean_gray = np.mean(raw_rgb)
                if mean_gray > 0 and not np.any(raw_rgb == 0): st.session_state.white_multipliers = mean_gray / raw_rgb
                st.session_state.calibration_mode = False
                st.session_state.show_results = False
                st.rerun()
            else:
                if clicked_x != st.session_state.pos_x or clicked_y != st.session_state.pos_y:
                    st.session_state.pos_x = clicked_x
                    st.session_state.pos_y = clicked_y
                    st.session_state.show_results = False
                    st.rerun()

        # Тест освещения (Метамеризм)
        light_env = st.radio("Освещение:", ["☀️ День (5500K)", "💡 Лампа (3000K)"], horizontal=True, label_visibility="collapsed")
        simulated_rgb = list(avg_rgb)
        if light_env == "💡 Лампа (3000K)":
            simulated_rgb[0] = min(255, int(simulated_rgb[0] * 1.15))
            simulated_rgb[1] = min(255, int(simulated_rgb[1] * 1.05))
            simulated_rgb[2] = max(0, int(simulated_rgb[2] * 0.80))

        hex_color = '#{:02x}{:02x}{:02x}'.format(simulated_rgb[0], simulated_rgb[1], simulated_rgb[2])
        st.markdown(f'<div style="background-color:{hex_color}; width:100%; height:40px; display: flex; align-items: center; justify-content: center;"><span style="color: #fff; font-size: 0.95rem; font-weight: bold; background-color: rgba(0,0,0,0.5); padding: 1px 6px; border-radius: 4px;">RGB: {tuple(simulated_rgb)}</span></div>', unsafe_allow_html=True)
        
        if st.button("🔍 ПОДОБРАТЬ РЕЦЕПТ", type="primary", use_container_width=True):
            with st.spinner("ИИ оптимизирует склад..."):
                # Передаем выбранные остатки в алгоритм микшера
                recipe, delta_e = calculate_mix_recipe_lab(avg_rgb, CURRENT_PAINTS_DB, user_stock)
                st.session_state.saved_recipe = recipe
                st.session_state.saved_delta_e = delta_e
                st.session_state.show_results = True

        if st.session_state.show_results:
            if not st.session_state.saved_recipe:
                st.error("⚠️ Из выбранных остатков невозможно собрать цвет. Добавьте другие пигменты в список склада!")
            else:
                st.write("### 📐 Площадь и расход краски:")
                col_area, col_layers = st.columns(2)
                with col_area:
                    input_area = st.number_input("Площадь (м²):", min_value=0.1, max_value=500.0, value=1.0, step=0.5)
                with col_layers:
                    input_layers = st.number_input("Слои:", min_value=1, max_value=5, value=2, step=1)
                    
                brand_rate = brand_coverages.get(selected_brand, 130)
                auto_calculated_weight = round(input_area * input_layers * brand_rate, 1)
                
                st.info(f"ℹ️ Укрывистость: ~{brand_rate} г/м² на слой. Необходимый объём: **{auto_calculated_weight} г.**")
                total_weight = st.number_input("Вес замеса для весов (грамм):", min_value=1.0, max_value=5000.0, value=float(auto_calculated_weight), step=10.0)
                
                # Проверяем, активирован ли режим апсайклинга остатков
                is_upcycled = user_stock and len(user_stock) > 0
                
                if is_upcycled:
                    st.success("♻️ АПСАЙКЛИНГ: Рецепт перестроен под ваши остатки!")
                
                st.write("### 📝 Формула замеса:")
                raw_text_to_share = f"🎨 РЕЦЕПТ ИИ-КОЛОРИСТА (ZERO-WASTE)\\nПалитра: {selected_brand}\\nИтоговый вес: {total_weight} г\\n"
                if is_upcycled: raw_text_to_share += "[Собрано из остатков склада]\\n"
                
                for paint, percent in st.session_state.saved_recipe.items():
                    calculated_grams = round((percent / 100.0) * total_weight, 2)
                    st.markdown(f'<p style="margin-bottom: 4px !important;">🔸 <strong>{paint}</strong>: <code>{percent} %</code> → <b>{calculated_grams} г.</b></p>', unsafe_allow_html=True)
                    raw_text_to_share += f"🔸 {paint}: {percent}% ({calculated_grams}г)\\n"
                
                # --- ЛОГИКА ФИНАНСОВОЙ ЭКОНОМИИ АПСАЙКЛИНГА ---
                if is_upcycled:
                    st.markdown("💸 **Затраты на докупку новых банок:** `0.00 " + current_currency + " (Всё со склада!)`")
                    raw_text_to_share += "💸 Расходы на докупку: 0 (Всё со склада!)"
                else:
                    base_rate = market_prices.get(selected_brand, 150)
                    cost_for_weight = round((total_weight / 100.0) * base_rate, 2)
                    st.markdown(f'💸 **Итоговая цена материалов:** `{cost_for_weight} {current_currency}`')
                    raw_text_to_share += f"💸 Цена материалов: {cost_for_weight} {current_currency}"

                st.write("")
                st.components.v1.html(f"""
                    <button id="shareBtn" style="width: 100%; background-color: #3a3a3c; color: #fafafa; border: 1px solid #48484a; border-radius: 12px; font-size: 1.05rem; padding: 12px 10px; font-weight: 700; cursor: pointer; font-family: -apple-system, BlinkMacSystemFont; text-transform: uppercase;">📋 Скопировать рецепт и смету</button>
                    <textarea id="hiddenText" style="position: absolute; left: -9999px;">{raw_text_to_share}</textarea>
                    <script>
                    document.getElementById('shareBtn').addEventListener('click', function() {{
                        var tArea = document.getElementById('hiddenText'); tArea.select(); tArea.setSelectionRange(0, 99999);
                        try {{
                            if (document.execCommand('copy')) {{
                                this.innerText = '✅ Всё скопировано в буфер!'; this.style.backgroundColor = '#2ecc71'; this.style.borderColor = '#2ecc71'; this.style.color = '#000000';
                                setTimeout(() => {{ this.innerText = '📋 Скопировать рецепт и смету'; this.style.backgroundColor = '#3a3a3c'; this.style.borderColor = '#48484a'; this.style.color = '#fafafa'; }}, 2000);
                            }}
                        }} catch (err) {{ console.error(err); }}
                    }});
                    </script>
                """, height=50)

                de = st.session_state.saved_delta_e
                if de < 2.0: st.caption(f"✨ Точно (ΔE: {round(de, 1)})")
                elif de < 5.0: st.caption(f"👌 Из остатков собран близкий тон (ΔE: {round(de, 1)})")
                else: st.warning(f"⚠️ Ограниченный спектр остатков. Погрешность цвета высока (ΔE: {round(de, 1)}). Рекомендуется расширить склад.")
                
            st.markdown(f'<p class="geo-badge">📍 Регион: {current_city} • Среда: {light_env}</p>', unsafe_allow_html=True)
else:
    st.info("👋 Загрузите или снимите фото объекта для старта.")