# -*- coding: utf-8 -*-
# =====================================================================
# 0_Basic_Info_Input.py
#  AI経営診断GPT – 基本情報入力フォーム（UX徹底改善/リセット安全/2カラム/粗利率マイナス対応）
# =====================================================================
from __future__ import annotations

import streamlit as st
from config import init_page
from ui_components import show_subtitle, show_back_to_top

# ======= 必ず最初 =======
init_page(title="AI経営診断 – 基本情報入力")


### --- 安全リセット実装 --- ###
def reset_all():
    for k in [
        "user_input",
        "external_output",
        "deep_dive_questions",
        "deep_dive_answers",
        "swot_output",
        "root_cause_output",
        "action_result",
    ]:
        st.session_state.pop(k, None)
    st.session_state["step"] = 1
    st.session_state["show_reset_confirm"] = False
    st.rerun()


with st.sidebar:
    if st.button("🔄 新規診断（全データリセット）"):
        st.session_state["show_reset_confirm"] = True
    if st.session_state.get("show_reset_confirm"):
        st.warning("全ての入力・分析データが消去されます。本当にリセットしますか？")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("はい、リセットする", key="do_reset"):
                reset_all()
        with col2:
            if st.button("キャンセル", key="cancel_reset"):
                st.session_state["show_reset_confirm"] = False

# -- デザインカスタマイズ
st.markdown(
    """
<style>
.required-label:after {
    content: " *";
    color: #e53935;
    font-weight: bold;
}
.field-error {
    color: #e53935;
    font-size: 0.98em;
    margin-top: 2px;
    margin-bottom: 0;
}
.form-section {
    margin-bottom: 1.2em;
    padding: 1.3em 1.2em 1.2em 1.2em;
    background: linear-gradient(100deg,#fafdff,#eaf4ff 90%);
    border-radius: 13px;
    box-shadow: 0 2px 9px #e2eaf3;
    border-left: 5px solid #1976d2;
}
.save-btn {
    width: 100%;
    font-size: 1.22em !important;
    font-weight: 700;
    background: #1976d2 !important;
    color: #fff !important;
    border-radius: 11px;
    padding: .7em 0;
    margin-top:1em;
    margin-bottom:.5em;
    box-shadow: 0 2px 11px #e1ebfc;
    border: none;
    transition: background .19s;
}
.save-btn:hover { background: #16408a !important; }
@media (max-width: 700px) {
    .block-container {
        max-width: 98vw !important;
        padding-left: 0.2rem !important;
        padding-right: 0.2rem !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

if not isinstance(st.session_state.get("user_input"), dict):
    st.session_state["user_input"] = {}
if not isinstance(st.session_state.get("errors"), dict):
    st.session_state["errors"] = {}

user_input: dict[str, any] = st.session_state["user_input"]
errors: dict[str, str] = st.session_state["errors"]

show_subtitle("🏢 基本情報入力")

# --- 定義 ---
ALL_FIELDS = [
    ("会社名・屋号", True, "例）サンプル株式会社"),
    ("業種（できるだけ詳しく）", True, "例）自動車整備業、IT受託開発など"),
    ("地域", True, "例）東京都新宿区"),
    ("主な商品・サービス", True, "例）自動車修理、ケーキ販売など"),
    ("主な顧客層", True, "例）地域の一般消費者"),
    ("年間売上高（おおよそ）", False, "例）10,000,000（円）"),
    ("粗利率（おおよそ）", False, "例）30.5（％）"),
    ("最終利益（税引後・おおよそ）", False, "例）1,000,000（円）"),
    ("借入金額（だいたい）", False, "例）5,000,000（円）"),
]
INT_FIELDS = [
    "年間売上高（おおよそ）",
    "最終利益（税引後・おおよそ）",
    "借入金額（だいたい）",
]
# --- 全角数字・全角小数点・全角カンマ→半角変換
JP_NUM_MAP = str.maketrans("０１２３４５６７８９．，", "0123456789..")

for k, *_ in ALL_FIELDS:
    user_input.setdefault(k, "")


def _to_half(v: str) -> str:
    """全角数字→半角、小数点（．）→半角（.）、カンマ（，）→除去"""
    return v.replace(",", "").replace("，", "").translate(JP_NUM_MAP).strip()


def _is_int(v: str) -> bool:
    try:
        int(_to_half(v))
        return True
    except:
        return False


def _is_percent(v: str) -> bool:
    """粗利率。マイナス〜プラス100%まで許可"""
    try:
        f = float(_to_half(v).replace("%", ""))
        return -100 <= f <= 100  # マイナスもOK
    except:
        return False


def validate_field(k: str, v: str) -> str:
    if k in [f for f, req, _ in ALL_FIELDS if req]:
        if not v.strip():
            return "必須入力です"
    if k in INT_FIELDS:
        if v and not _is_int(v):
            return "整数で入力"
    if k == "粗利率（おおよそ）":
        if v and not _is_percent(v):
            return "-100〜100の数値(％)"
    return ""


def validate_all() -> dict[str, str]:
    e = {}
    for k, req, _ in ALL_FIELDS:
        v = user_input[k]
        msg = validate_field(k, v)
        if msg:
            e[k] = msg
    # 経営の問題点チェック
    if not user_input.get("経営の問題点", "").strip():
        e["経営の問題点"] = "必須入力です"
    return e


# ===== 2カラム＋ブロックUIでフォーム表示 =====
with st.form("form_basic_info"):
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("### 企業情報")
    cols = st.columns(2)
    for idx, (key, required, placeholder) in enumerate(ALL_FIELDS):
        label = f"{key}{' *' if required else ''}"
        col = cols[idx % 2]
        with col:
            user_input[key] = st.text_input(
                label=label,
                value=str(user_input[key]),
                placeholder=placeholder,
                key=f"input_{key}",
                label_visibility="visible",
            )
            err = errors.get(key, "")
            if err:
                st.markdown(
                    f'<div class="field-error">{err}</div>', unsafe_allow_html=True
                )
    st.markdown("</div>", unsafe_allow_html=True)

    # 経営の問題点（全幅で）
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown(
        "### 📋 経営の問題点<span style='color:#e53935;'>*</span>",
        unsafe_allow_html=True,
    )
    user_input["経営の問題点"] = st.text_area(
        "今の経営で困っていること、悩んでいること、改善したいことがあれば、どんなことでも具体的にご記入ください。",
        value=user_input.get("経営の問題点", ""),
        key="input_経営の問題点",
        placeholder="例）月の売上変動が大きく、在庫が不足しがちでキャッシュが圧迫されています",
    )
    if errors.get("経営の問題点"):
        st.markdown(
            f'<div class="field-error">{errors["経営の問題点"]}</div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # 保存ボタン（中央・幅広・hover演出つき）
    submitted = st.form_submit_button(
        "保存", use_container_width=True, help="入力内容を保存します", type="primary"
    )
    st.markdown(
        '<div style="text-align:center;"><a href="#" onclick="window.location.reload();" style="font-size:1em;color:#1976d2;text-decoration:underline;">▲ 新しい診断をはじめる</a></div>',
        unsafe_allow_html=True,
    )

    st.info("保存後、サイドバーの『AI経営診断』タブから診断ステップに進めます。")

# ===== リアルタイムバリデーション =====
for k, _, _ in ALL_FIELDS:
    err = validate_field(k, user_input[k])
    if err:
        errors[k] = err
    elif k in errors:
        errors.pop(k)
err_prob = validate_field("経営の問題点", user_input.get("経営の問題点", ""))
if err_prob:
    errors["経営の問題点"] = err_prob
elif "経営の問題点" in errors:
    errors.pop("経営の問題点")

# ===== 保存ボタン処理 =====
if submitted:
    errors.clear()
    errors.update(validate_all())
    if errors:
        # 最初のエラー項目へ自動スクロールJS
        first_error = next(iter(errors))
        st.markdown(
            f"""
            <script>
            var errorElem = window.parent.document.querySelector('div.field-error');
            if(errorElem){{ errorElem.scrollIntoView({{behavior:"smooth",block:"center"}}); }}
            </script>
        """,
            unsafe_allow_html=True,
        )
        st.error("⚠️ 入力内容に不備があります。赤字メッセージをご確認ください。")
        st.session_state["errors"] = errors
    else:
        # 保存時に分析・質問等の全データをリセット
        for k in [
            "external_output",
            "deep_dive_questions",
            "deep_dive_answers",
            "swot_output",
            "root_cause_output",
            "action_result",
        ]:
            st.session_state.pop(k, None)
        # 数値正規化
        for k in INT_FIELDS:
            v = str(user_input[k]).strip()
            if v:
                user_input[k] = int(_to_half(v))
        v = str(user_input["粗利率（おおよそ）"]).strip()
        if v:
            user_input["粗利率（おおよそ）"] = float(_to_half(v).replace("%", ""))
        st.session_state["user_input"] = user_input
        st.session_state.pop("errors", None)
        st.success(
            "✅ 入力内容を保存しました。前回の診断データはすべてクリアされました。新しい会社で診断を始められます。"
        )

if len(ALL_FIELDS) + 1 > 8:
    show_back_to_top()
