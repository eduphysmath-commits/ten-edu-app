import streamlit as st
import requests
import json
import os
import time
import io
from PIL import Image
from dotenv import load_dotenv

# 1. Құпия мәліметтерді оқу
load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
TABLE_NAME = "submissions"

# Беттің баптаулары міндетті түрде ең жоғарыда тұруы керек
st.set_page_config(page_title="Ten-Edu: Тексеру жүйесі", layout="wide", page_icon="🎓")

def send_data(payload):
    """Supabase-ке дерек жіберу функциясы"""
    headers = {
        "apikey": KEY, 
        "Authorization": f"Bearer {KEY}", 
        "Content-Type": "application/json"
    }
    return requests.post(f"{URL}/rest/v1/{TABLE_NAME}", json=payload, headers=headers)

def main():
    # --- СЕССИЯ ЖАДЫН ҚҰРУ ---
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False
    if 'photos' not in st.session_state:
        st.session_state.photos = [] 
    if 'cam_key' not in st.session_state:
        st.session_state.cam_key = 0 

    # --- СІЛТЕМЕДЕН ПӘНДІ АНЫҚТАУ ---
    # Егер сілтемеде ?exam=3 болса қазақ тілі, әйтпесе mặc định Алгебра (4)
    query_params = st.query_params
    exam_param = query_params.get("exam", "4")
    
    if exam_param == "3":
        current_exam_id = 3
        subject_name = "ҚАЗАҚ ТІЛІ ЖӘНЕ ӘДЕБИЕТІ"
        current_max_score = 30
        icon = "🇰🇿"
    else:
        current_exam_id = 4
        subject_name = "АЛГЕБРА: 9-СЫНЫП"
        current_max_score = 20
        icon = "📐"

    # 2. СТИЛЬ (Дизайн)
    st.markdown("""
        <style>
        .stApp { background-color: #f0f2f6; }
        .main-title { color: #2c3e50; text-align: center; font-weight: 800; padding: 20px; border-bottom: 3px solid #3498db; }
        .search-section { background-color: #e3f2fd; padding: 25px; border-radius: 15px; border: 2px dashed #1e88e5; margin-top: 50px; }
        .camera-box { background-color: #fff9c4; padding: 20px; border-radius: 10px; border: 2px dashed #fbc02d; margin-bottom: 20px; }
        </style>
    """, unsafe_allow_html=True)

    # 3. НЕГІЗГІ БЕТ
    st.markdown(f"<h1 class='main-title'>{icon} {subject_name} (ТЖБ)</h1>", unsafe_allow_html=True)

    if st.session_state.submitted:
        st.balloons()
        st.success("🎉 Жұмысың сәтті қабылданды! Төмендегі іздеу бөлімінен нәтижені біле аласың.")
        if st.button("Қайта бастау 🔄"):
            st.session_state.submitted = False
            st.session_state.photos = []
            st.session_state.cam_key += 1
            st.rerun()
    else:
        st.info("📝 **Нұсқаулық:** Жұмысыңыз бірнеше беттен тұрса, әр бетті жеке түсіріп немесе жүктеп, «Тізімге қосу» батырмасын басыңыз. Соңында «Тапсыру» батырмасын басыңыз.")
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("👤 Оқушының аты-жөні:", placeholder="Мысалы: Асқаров Нұрлан")
        with col2:
            s_class = st.selectbox("🏫 Сыныбыңыз:", ["9-A", "9-B", "9-C", "9-D", "9-E", "9-F", "9-G"])

        if name:
            st.markdown("<div class='camera-box'><b>📸 Жұмысты суретке түсіру немесе жүктеу:</b></div>", unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["📂 Дайын суретті жүктеу (Ұсынылады)", "📸 Камерамен түсіру"])
            
            with tab1:
                uploaded_file = st.file_uploader("Телефоннан немесе компьютерден анық суретті таңдаңыз", type=["jpg", "jpeg", "png"], key=f"upload_{st.session_state.cam_key}")
                if uploaded_file:
                    if st.button("➕ Осы файлды жұмысқа тіркеу", use_container_width=True, key="btn_upload"):
                        st.session_state.photos.append(uploaded_file.getvalue())
                        st.session_state.cam_key += 1
                        st.rerun()

            with tab2:
                cam_image = st.camera_input("Дәптер бетін түсіріңіз", key=f"camera_{st.session_state.cam_key}")
                if cam_image:
                    if st.button("➕ Камерадағы суретті тіркеу", use_container_width=True, key="btn_cam"):
                        st.session_state.photos.append(cam_image.getvalue())
                        st.session_state.cam_key += 1 
                        st.rerun() 

            if st.session_state.photos:
                st.write("---")
                st.markdown(f"**Сіздің жұмысыңыз ({len(st.session_state.photos)} бет):**")
                cols = st.columns(min(len(st.session_state.photos), 4))
                
                for i, photo_bytes in enumerate(st.session_state.photos):
                    with cols[i % 4]:
                        st.image(photo_bytes, caption=f"{i+1}-бет", use_container_width=True)
                        if st.button(f"🗑️ Өшіру", key=f"delete_{i}"):
                            st.session_state.photos.pop(i)
                            st.rerun()
                
                if st.button("❌ Барлығын қайтадан бастау (Суреттерді өшіру)"):
                    st.session_state.photos = []
                    st.session_state.cam_key += 1
                    st.rerun()

                st.write("---")
                
                if st.button("ЖҰМЫСТЫ ТАПСЫРУ ✅", type="primary", use_container_width=True):
                    with st.spinner("Суреттер біріктіріліп, мұғалімге жіберілуде..."):
                        images = [Image.open(io.BytesIO(img_bytes)).convert("RGB") for img_bytes in st.session_state.photos]
                        
                        widths, heights = zip(*(i.size for i in images))
                        max_width = max(widths)
                        total_height = sum(heights)

                        stitched_image = Image.new('RGB', (max_width, total_height))
                        y_offset = 0
                        for img in images:
                            stitched_image.paste(img, (0, y_offset))
                            y_offset += img.height

                        file_name = f"exam_{current_exam_id}_student_{int(time.time())}.jpg"
                        stitched_image.thumbnail((1500, 1500 * len(images))) 
                        
                        img_byte_arr = io.BytesIO()
                        stitched_image.save(img_byte_arr, format='JPEG', quality=80, optimize=True)
                        compressed_bytes_data = img_byte_arr.getvalue()
                        
                        storage_url = f"{URL}/storage/v1/object/exam_images/{file_name}"
                        storage_headers = {
                            "apikey": KEY,
                            "Authorization": f"Bearer {KEY}",
                            "Content-Type": "image/jpeg"
                        }
                        upload_res = requests.post(storage_url, headers=storage_headers, data=compressed_bytes_data)

                        if upload_res.status_code in [200, 201]:
                            public_image_url = f"{URL}/storage/v1/object/public/exam_images/{file_name}"
                            payload = {
                                "exam_id": current_exam_id,
                                "student_name": name, 
                                "student_class": s_class,
                                "answers": {"lang": "kz", "image_url": public_image_url},
                                "status": "pending"
                            }
                            resp = send_data(payload)
                            if resp.status_code in [200, 201, 204]:
                                st.session_state.submitted = True
                                st.rerun()
                            else:
                                st.error(f"⚠️ Базаға сақтау қатесі: {resp.text}")
                        else:
                            st.error(f"⚠️ Қоймаға жүктеу қатесі: {upload_res.text}")

    # 4. НӘТИЖЕНІ ІЗДЕУ ЖӘНЕ КӨРСЕТУ
    st.markdown("<div class='search-section'><h3>🔎 Нәтижеңді тексер</h3></div>", unsafe_allow_html=True)
    search_query = st.text_input("", key="search_input", placeholder="Іздеу үшін есіміңізді жазыңыз...")

    if search_query:
        s_headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
        res = requests.get(f"{URL}/rest/v1/{TABLE_NAME}?student_name=ilike.*{search_query}*&exam_id=eq.{current_exam_id}&select=*&order=id.desc", headers=s_headers)
        
        if res.status_code == 200:
            results = res.json()
            if len(results) > 0:
                for data in results:
                    with st.container():
                        st.markdown(f"#### 👤 {data['student_name']} ({data['student_class']})")
                        if data['status'] == 'pending':
                            st.warning("⏳ Мұғалім (AI) әлі тексеріп жатыр. Сәл күте উভয়ңыз...")
                        else:
                            col_score, col_fb = st.columns([1, 3])
                            with col_score:
                                raw_score = data.get('score', 0)
                                percentage = int((raw_score / current_max_score) * 100)
                                st.metric("Нәтиже", f"{percentage}%", delta=f"{raw_score}/{current_max_score} балл")
                                st.progress(min(raw_score / current_max_score, 1.0))
                            with col_fb:
                                with st.expander("📝 Мұғалімнің талдауы (AI)", expanded=True):
                                    st.write(data.get('ai_feedback', 'Талдау жасалуда...'))
                        st.markdown("<br>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()