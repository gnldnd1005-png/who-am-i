import re
import os
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Who Am I?",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.main .block-container {
    padding: 1.2rem 1rem 3rem 1rem;
    max-width: 480px;
    margin: 0 auto;
}
.who-card {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    padding: 1.4rem 1.2rem;
    border-radius: 20px;
    color: white;
    margin: 0.5rem 0 1rem 0;
    box-shadow: 0 8px 32px rgba(79,70,229,0.25);
}
.card-title {
    text-align: center;
    font-size: 1.15rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
}
.answer-row {
    background: rgba(255,255,255,0.15);
    padding: 0.7rem 0.9rem;
    border-radius: 12px;
    margin: 0.4rem 0;
}
.q-label {
    font-size: 0.75rem;
    opacity: 0.82;
    margin-bottom: 0.15rem;
}
.q-answer {
    font-size: 1rem;
    font-weight: 600;
    line-height: 1.4;
    word-break: keep-all;
}
.stButton > button {
    width: 100%;
    text-align: left !important;
    padding: 0.75rem 1rem !important;
    border-radius: 12px !important;
    font-size: 1rem !important;
    border: 1.5px solid #e5e7eb !important;
    background: white !important;
    color: #1f2937 !important;
    margin: 0.15rem 0 !important;
    box-shadow: none !important;
}
.stButton > button:hover {
    border-color: #4f46e5 !important;
    color: #4f46e5 !important;
    background: #f5f3ff !important;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

QUESTIONS = [
    ("mbti",     "나의 MBTI는?",                     "🧠"),
    ("birthday", "나의 생일은?",                      "🎂"),
    ("blood",    "혈액형",                             "🩸"),
    ("food",     "내가 제일 좋아하는 음식은?",         "🍽️"),
    ("hobby",    "나의 취미는?",                       "🎨"),
    ("dislike",  "내가 싫어하는 것은?",               "😤"),
    ("intro",    "나를 한마디로 소개한다면?",          "✨"),
]

def sheets_url_to_csv_url(url: str) -> str | None:
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        return None
    sheet_id = match.group(1)
    gid_match = re.search(r"gid=(\d+)", url)
    gid = gid_match.group(1) if gid_match else "0"
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

DEFAULT_FILE = "survey.xlsx"


def load_data(source, is_excel=False) -> pd.DataFrame:
    df = pd.read_excel(source) if is_excel else pd.read_csv(source)
    first_col = df.columns[0]
    if "타임스탬프" in str(first_col) or "Timestamp" in str(first_col):
        df = df.drop(columns=[first_col])
    expected_keys = ["name"] + [q[0] for q in QUESTIONS]
    rename_map = {df.columns[i]: expected_keys[i] for i in range(min(len(df.columns), len(expected_keys)))}
    df = df.rename(columns=rename_map)
    df = df.fillna("-")
    return df

def show_card(row, reveal: bool):
    title = f"👤 {row.get('name', '?')}" if reveal else "🎭 이 사람은 누구일까요?"
    rows_html = "".join(
        f'<div class="answer-row">'
        f'<div class="q-label">{emoji} {label}</div>'
        f'<div class="q-answer">{row.get(key, "-")}</div>'
        f'</div>'
        for key, label, emoji in QUESTIONS
    )
    st.markdown(
        f'<div class="who-card"><p class="card-title">{title}</p>{rows_html}</div>',
        unsafe_allow_html=True,
    )

def main():
    for k, v in [("selected", None), ("revealed", False), ("view", "list"), ("df", None), ("sheets_csv_url", None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # 기본 엑셀 파일 자동 로드
    if st.session_state.df is None and os.path.exists(DEFAULT_FILE):
        try:
            df = load_data(DEFAULT_FILE, is_excel=True)
            if len(df) > 0:
                st.session_state.df = df
        except Exception:
            pass

    st.title("🎯 Who Am I?")

    # ── 데이터 불러오기 (아직 로드 안 된 경우)
    if st.session_state.df is None:
        st.markdown("#### 응답 데이터 불러오기")
        sheets_url = st.text_input(
            "구글 시트 URL 붙여넣기",
            placeholder="https://docs.google.com/spreadsheets/d/...",
        )
        if sheets_url:
            csv_url = sheets_url_to_csv_url(sheets_url)
            if csv_url is None:
                st.error("올바른 구글 시트 URL을 입력해주세요.")
            else:
                try:
                    df = load_data(csv_url)
                    st.session_state.df = df
                    st.session_state.sheets_csv_url = csv_url
                    st.rerun()
                except Exception as e:
                    st.error(f"불러오기 실패: {e}\n\n구글 시트가 '링크가 있는 모든 사용자' 공개로 설정되어 있는지 확인해주세요.")

        st.divider()
        st.markdown("또는 CSV 파일 직접 업로드")
        uploaded = st.file_uploader("CSV 업로드", type=["csv"], label_visibility="collapsed")
        if uploaded:
            try:
                df = load_data(uploaded)
                st.session_state.df = df
                st.rerun()
            except Exception as e:
                st.error(f"파일 오류: {e}")
        return

    df = st.session_state.df

    # ── 목록 뷰
    if st.session_state.view == "list":
        col_title, col_refresh, col_reset = st.columns([3, 1, 1])
        with col_title:
            st.markdown(f"**총 {len(df)}명 참가**")
        with col_refresh:
            if st.button("🔄"):
                if st.session_state.sheets_csv_url:
                    try:
                        st.session_state.df = load_data(st.session_state.sheets_csv_url)
                        st.rerun()
                    except:
                        st.error("업데이트 실패")
        with col_reset:
            if st.button("🔗"):
                st.session_state.df = None
                st.session_state.sheets_csv_url = None
                st.session_state.selected = None
                st.session_state.view = "list"
                st.rerun()
        st.divider()
        for idx, row in df.iterrows():
            name = row.get("name", f"참가자 {idx+1}")
            if st.button(f"👤  {name}", key=f"p_{idx}"):
                st.session_state.selected = int(idx)
                st.session_state.revealed = False
                st.session_state.view = "card"
                st.rerun()

    # ── 카드 뷰
    elif st.session_state.view == "card":
        idx = st.session_state.selected
        row = df.iloc[idx]

        if st.button("← 목록으로"):
            st.session_state.view = "list"
            st.rerun()

        st.markdown(
            f"<p style='color:#6b7280;font-size:0.85rem;margin:0.2rem 0 0.5rem;'>"
            f"참가자 {idx+1} / {len(df)}</p>",
            unsafe_allow_html=True,
        )

        show_card(row, reveal=st.session_state.revealed)

        if not st.session_state.revealed:
            if st.button("🎉 정답 공개!", use_container_width=True):
                st.session_state.revealed = True
                st.balloons()
                st.rerun()
        else:
            st.success(f"정답은 바로... **{row.get('name', '?')}** 🎊")

        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⬅️ 이전", use_container_width=True, disabled=(idx == 0)):
                st.session_state.selected = idx - 1
                st.session_state.revealed = False
                st.rerun()
        with col_next:
            if st.button("다음 ➡️", use_container_width=True, disabled=(idx >= len(df) - 1)):
                st.session_state.selected = idx + 1
                st.session_state.revealed = False
                st.rerun()

if __name__ == "__main__":
    main()
