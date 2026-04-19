import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt

# ==========================================
# PHẦN 1: LOGIC MỜ (Hệ não bộ - Giữ chuẩn Lab 5.3)
# ==========================================
river_level = ctrl.Antecedent(np.arange(0, 6, 0.1), 'Mực nước sông (m)')
rainfall = ctrl.Antecedent(np.arange(0, 201, 1), 'Lượng mưa (mm/h)')
pump_power = ctrl.Consequent(np.arange(0, 101, 1), 'Công suất bơm (%)')

river_level.automf(3, names=['Low', 'Normal', 'High'])
rainfall.automf(3, names=['None', 'Moderate', 'Heavy'])
pump_power.automf(5, names=['Off', 'Low', 'Medium', 'High', 'Max'])

# 9 Luật suy diễn chuẩn kỹ thuật
rules = [
    ctrl.Rule(river_level['Low'] & rainfall['None'], pump_power['Off']),
    ctrl.Rule(river_level['Low'] & rainfall['Moderate'], pump_power['Low']),
    ctrl.Rule(river_level['Low'] & rainfall['Heavy'], pump_power['Medium']),
    ctrl.Rule(river_level['Normal'] & rainfall['None'], pump_power['Low']),
    ctrl.Rule(river_level['Normal'] & rainfall['Moderate'], pump_power['Medium']),
    ctrl.Rule(river_level['Normal'] & rainfall['Heavy'], pump_power['High']),
    ctrl.Rule(river_level['High'] & rainfall['None'], pump_power['Medium']),
    ctrl.Rule(river_level['High'] & rainfall['Moderate'], pump_power['High']),
    ctrl.Rule(river_level['High'] & rainfall['Heavy'], pump_power['Max']),
]

flood_sim = ctrl.ControlSystemSimulation(ctrl.ControlSystem(rules))

# ==========================================
# PHẦN 2: GIAO DIỆN & ĐỒ HỌA CAO CẤP
# ==========================================
st.set_page_config(page_title="Hệ thống Chống Ngập AI", layout="wide")
st.title("🏙️ Hệ thống Fuzzy logic điều khiển công suất trạm bơm")

# Chia cột cho giao diện điều khiển và màn hình mô phỏng
col_ui, col_viz = st.columns([1, 2.5])

with col_ui:
    st.subheader("⚙️ Thông số cảm biến")
    in_river = st.slider("Mực nước sông hiện tại (m)", 0.0, 5.0, 1.5)
    in_rain = st.slider("Lượng mưa tại thành phố (mm/h)", 0, 200, 50)
    
    # 1. AI TÍNH TOÁN (Logic Mềm)
    flood_sim.input['Mực nước sông (m)'] = in_river
    flood_sim.input['Lượng mưa (mm/h)'] = in_rain
    flood_sim.compute()
    out_pump = flood_sim.output['Công suất bơm (%)']
    
    # 2. INTERLOCK BẢO VỆ PHẦN CỨNG (ĐÃ FIX THEO ĐÚNG LOGIC CỦA BẠN)
    is_dry = in_rain < 15 
    is_sump_overflow = in_rain >= 180 # NGUY CƠ TRÀN BỂ GOM DO MƯA CỰC LỚN
    
    if is_dry:
        final_pump = 0.0    # Vùng 1: Cạn nước -> Ép tắt bơm
    elif is_sump_overflow:
        final_pump = 100.0  # Vùng 3: Khẩn cấp -> Bể chứa sắp tràn, ép xả lũ 100%
    else:
        final_pump = out_pump # Vùng 2: Bình thường -> AI điều khiển
    
    # 3. HIỂN THỊ METRICS
    st.metric("Công suất AI đề xuất (Fuzzy Logic)", f"{out_pump:.1f} %")
    
    if is_dry:
        st.metric("Công suất thực tế (Lệnh VFD)", "0.0 %", delta="- Ngắt cạn")
        st.warning("⚠️ BẢO VỆ CHỐNG CHẠY KHÔ: Nước bể gom quá thấp, đã tự động ngắt bơm.")
    elif is_sump_overflow:
        st.metric("Công suất thực tế (Lệnh VFD)", "100.0 %", delta="MAX Khẩn cấp", delta_color="inverse")
        st.error("🚨 KHẨN CẤP: Lượng mưa quá lớn, bể gom sắp tràn! Ghi đè AI, xả lũ toàn lực 100%!")
    else:
        st.metric("Công suất thực tế (Lệnh VFD)", f"{final_pump:.1f} %", delta="Vận hành mượt mà", delta_color="normal")
        st.success("✅ Trạm bơm hoạt động an toàn theo biểu đồ tối ưu của AI.")

with col_viz:
    river_h_px = (in_river / 5.0) * 280 
    sump_h = (in_rain / 200.0) * 70 # Nước bể gom dâng theo mưa
    rot_speed = max(0.1, 1.5 - (final_pump/80)) if final_pump > 0 else 0

    html_code = f"""
    <div style="position:relative; width:100%; height:500px; background:#0f172a; overflow:hidden; border-radius:15px; border:2px solid #334155;">
        <div id="rain-layer" style="position:absolute; top:0; width:100%; height:70%; z-index:1;"></div>

        <div style="position:absolute; bottom:60px; left:0; width:40%; height:280px; z-index:2; clip-path: polygon(0 0, 100% 0, calc(100% - 24px) 100%, 0 100%);">
            <div style="position:absolute; bottom:0; left:0; width:100%; height:{river_h_px}px; background:linear-gradient(to top, #1d4ed8, #60a5fa); transition:0.8s;">
                <div style="position:absolute; top:15px; left:15px; color:white; font-size:14px; font-weight:bold; opacity:0.7;">SÔNG</div>
            </div>
        </div>

        <div style="position:absolute; bottom:60px; left:calc(40% - 24px); width:80px; height:280px; z-index:10; background:#475569; clip-path: polygon(24px 0, 56px 0, 80px 100%, 0 100%);">
            <div style="position:absolute; top:5px; width:100%; text-align:center; color:white; font-size:10px; font-weight:bold;">ĐÊ</div>
        </div>

        <div style="position:absolute; bottom:130px; right:20px; width:45%; display:flex; align-items:flex-end; justify-content:space-between; z-index:3;">
            <div style="width:15%; height:120px; background:#475569; border:2px solid #94a3b8; border-bottom:none; box-shadow: 0 0 10px rgba(0,0,0,0.5); position:relative;">
                <div style="position:absolute; top:20px; left:20%; width:10px; height:15px; background:#fde047; box-shadow:0 0 5px #fde047;"></div>
                <div style="position:absolute; top:50px; right:20%; width:10px; height:15px; background:#fde047; box-shadow:0 0 5px #fde047;"></div>
            </div>
            
            <div style="width:20%; height:200px; background:#334155; border:2px solid #cbd5e1; border-bottom:none; position:relative; box-shadow: 0 0 15px rgba(0,0,0,0.6);">
                <div style="position:absolute; top:30px; left:20%; width:15px; height:15px; background:#fde047; box-shadow:0 0 8px #fde047;"></div>
                <div style="position:absolute; top:80px; right:20%; width:15px; height:15px; background:#fde047; box-shadow:0 0 8px #fde047;"></div>
                <div style="position:absolute; top:130px; left:20%; width:15px; height:15px; background:#fde047; box-shadow:0 0 8px #fde047;"></div>
            </div>
            
            <div style="width:15%; height:160px; background:#475569; border:2px solid #94a3b8; border-bottom:none; box-shadow: 0 0 10px rgba(0,0,0,0.5); position:relative;">
                 <div style="position:absolute; top:40px; left:30%; width:12px; height:12px; background:#fde047; box-shadow:0 0 5px #fde047;"></div>
            </div>
            
            <div style="width:18%; height:100px; background:#64748b; border:2px solid #e2e8f0; border-bottom:none; box-shadow: 0 0 10px rgba(0,0,0,0.5); position:relative;">
                 <div style="position:absolute; top:20px; left:20%; width:8px; height:8px; background:#fde047; box-shadow:0 0 5px #fde047;"></div>
            </div>
        </div>

        <div style="position:absolute; bottom:60px; right:0; width:60%; height:70px; background:#020617; z-index:4; border-left:2px solid #334155;">
             <div style="position:absolute; bottom:0; width:100%; height:{sump_h}px; background:#2563eb; transition:0.5s; opacity:0.8;"></div>
             <div style="position:absolute; top:5px; left:100px; color:#64748b; font-size:10px;">BỂ GOM NƯỚC</div>
        </div>

        <div style="position:absolute; bottom:0; width:100%; height:60px; background:#020617; z-index:5;"></div>

        <div style="position:absolute; bottom:70px; left:37%; width:150px; height:100px; z-index:20;">
            <div style="position:absolute; top:40px; left:-50px; width:120px; height:15px; background:#334155; border-radius:5px; {'display:block' if final_pump > 0 else 'display:none'}">
                <div style="width:100%; height:100%; background:#60a5fa; opacity:0.5; animation: flow 0.3s infinite linear;"></div>
            </div>
            <div style="position:absolute; bottom:0; left:30px; width:65px; height:65px; background:#1e293b; border:3px solid {'#ef4444' if final_pump == 0 else '#38bdf8'}; border-radius:50%; display:flex; justify-content:center; align-items:center; box-shadow: 0 0 15px {'#ef4444' if final_pump == 0 else '#38bdf8'};">
                <div style="width:4px; height:45px; background:{'#ef4444' if final_pump == 0 else '#38bdf8'}; position:absolute; {'animation:spin '+str(rot_speed)+'s infinite linear' if rot_speed>0 else ''}"></div>
                <div style="width:45px; height:4px; background:{'#ef4444' if final_pump == 0 else '#38bdf8'}; position:absolute; {'animation:spin '+str(rot_speed)+'s infinite linear' if rot_speed>0 else ''}"></div>
                <div style="width:12px; height:12px; background:white; border-radius:50%; z-index:16;"></div>
            </div>
        </div>
    </div>

    <style>
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        @keyframes flow {{ from {{ background-position: 0; }} to {{ background-position: 20px; }} }}
        .drop {{ position:absolute; background:#38bdf8; width:1px; height:12px; opacity:0.3; animation:fall 0.7s infinite linear; }}
        @keyframes fall {{ to {{ transform: translateY(350px); }} }}
    </style>

    <script>
        const layer = document.getElementById('rain-layer');
        const amt = {in_rain};
        if(amt > 10) {{
            for(let i=0; i<amt; i++) {{
                let d = document.createElement('div');
                d.className = 'drop';
                d.style.left = Math.random()*100 + '%';
                d.style.top = (Math.random()*100 - 100) + '%';
                d.style.animationDelay = Math.random()*2 + 's';
                layer.appendChild(d);
            }}
        }}
    </script>
    """
    components.html(html_code, height=520)

    # Cảnh báo độc lập về đê (Nước sông quá cao)
    if in_river >= 5.0:
        st.error("🚨 CẢNH BÁO MỨC ĐÊ: Nước sông đã vượt đỉnh đê! Thành phố có nguy cơ ngập từ bên ngoài!")

# ==========================================
# PHẦN 3: ĐỒ THỊ BIỂU DIỄN LOGIC MỜ ĐỘNG
# ==========================================
st.markdown("---")
with st.expander("📊 Xem trạng thái Fuzzy logic (Cập nhật theo thời gian thực)", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig_river, ax_river = plt.subplots(figsize=(5, 3))
        ax_river.plot(river_level.universe, river_level['Low'].mf, 'b', label='Low')
        ax_river.plot(river_level.universe, river_level['Normal'].mf, 'g', label='Normal')
        ax_river.plot(river_level.universe, river_level['High'].mf, 'r', label='High')
        
        ax_river.axvline(x=in_river, color='k', linestyle='--', linewidth=2, label=f'Input: {in_river:.1f}m')
        
        ax_river.set_title("Mực nước sông (m)")
        ax_river.legend()
        st.pyplot(fig_river)
        
    with col2:
        fig_rain, ax_rain = plt.subplots(figsize=(5, 3))
        ax_rain.plot(rainfall.universe, rainfall['None'].mf, 'b', label='None')
        ax_rain.plot(rainfall.universe, rainfall['Moderate'].mf, 'g', label='Moderate')
        ax_rain.plot(rainfall.universe, rainfall['Heavy'].mf, 'r', label='Heavy')
        
        ax_rain.axvline(x=in_rain, color='k', linestyle='--', linewidth=2, label=f'Input: {in_rain}mm')
        
        ax_rain.set_title("Lượng mưa (mm/h)")
        ax_rain.legend()
        st.pyplot(fig_rain)
        
    with col3:
        fig_pump, ax_pump = plt.subplots(figsize=(5, 3))
        ax_pump.plot(pump_power.universe, pump_power['Off'].mf, 'k', label='Off')
        ax_pump.plot(pump_power.universe, pump_power['Low'].mf, 'b', label='Low')
        ax_pump.plot(pump_power.universe, pump_power['Medium'].mf, 'g', label='Medium')
        ax_pump.plot(pump_power.universe, pump_power['High'].mf, 'orange', label='High')
        ax_pump.plot(pump_power.universe, pump_power['Max'].mf, 'r', label='Max')
        
        ax_pump.axvline(x=out_pump, color='gray', linestyle='--', linewidth=1.5, label=f'AI Đề xuất: {out_pump:.1f}%')
        
        if final_pump != out_pump:
            ax_pump.axvline(x=final_pump, color='purple', linestyle='--', linewidth=3, label=f'THỰC TẾ (GHI ĐÈ): {final_pump:.1f}%')
        else:
            ax_pump.axvline(x=final_pump, color='purple', linestyle='--', linewidth=3, label=f'THỰC TẾ (VFD): {final_pump:.1f}%')
        
        ax_pump.set_title("Công suất bơm (%)")
        ax_pump.legend()
        st.pyplot(fig_pump)