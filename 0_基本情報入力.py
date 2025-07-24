# -*- coding: utf-8 -*-
"""
0_Basic_Info_Input.py — UX プレミアム版
============================================================
* AI経営診断 GPT : 基本情報入力フォーム
* 日本標準産業分類 (R5) 完全対応 / 外部 JSON マスタ
* 追加 UX 改善点
    - スキーマ検証を jsonschema で正式対応 (フォールバックあり)
    - 商品概要リアルタイム文字数カウンタ (100〜200 文字範囲を色で示す)
    - 入力完了率プログレスバー
    - フォームをタブ UI で分割 (産業分類 / 事業情報)
    - 保存ボタンはバリデーション OK 時のみ有効
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Dict, List, TypedDict, Any

import streamlit as st
from config import init_page
from ui_components import show_subtitle, show_back_to_top

# ------------------------------------------------------------------
# 0. 定数
# ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
MASTER_PATH = ROOT / "industry_master.json"
NEXT_PAGE = "1_External_Analysis.py"

# ------------------------------------------------------------------
# 1. ページ / CSS
# ------------------------------------------------------------------
init_page(title="AI経営診断 – 基本情報入力")

st.markdown(
    """
<style>
.char-count {
  font-size: 0.85em;
  margin-top: -0.3rem;
}
.char-ok   { color: #4caf50; }
.char-warn { color: #f9a825; }
.char-err  { color: #e53935; }
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# 2. JSON マスタロード & 検証
# ------------------------------------------------------------------
SCHEMA = {
    "type": "object",
    "patternProperties": {
        ".*": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["code", "name"],
                "properties": {"code": {"type": "string"}, "name": {"type": "string"}},
            },
        }
    },
}

@st.cache_data(show_spinner="⚙️ 産業分類マスタをロード中…")
def load_master(path: Path) -> Dict[str, List[Dict[str, str]]]:
    if not path.exists():
        st.error("❌ industry_master.json が見つかりません")
        st.stop()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        st.error(f"❌ JSON 解析エラー: {exc}")
        st.stop()

    try:
        jsonschema = importlib.import_module("jsonschema")
        jsonschema.validate(data, SCHEMA)  # type: ignore[attr-defined]
    except ModuleNotFoundError:
        # fallback 簡易検証
        for major, mids in data.items():
            if not mids:
                st.error(f"❌ '{major}' に中分類がありません")
                st.stop()
            for d in mids:
                if not {"code", "name"}.issubset(d):
                    st.error(f"❌ スキーマ不整合: {d}")
                    st.stop()
    except Exception as exc:
        st.error(f"❌ スキーマバリデーション失敗: {exc}")
        st.stop()
    return data

industry_major_mid = load_master(MASTER_PATH)
major_opts = list(industry_major_mid.keys())

# ------------------------------------------------------------------
# 3. 型 & SessionState
# ------------------------------------------------------------------
class UI(TypedDict, total=False):
    業種_大分類: str
    業種_中分類: str
    mid_display: str
    地域: str
    主な商品・サービス: str
    顧客層: List[str]
    価格帯: str
    販売方法: str

ui: UI = st.session_state.setdefault("user_input", UI())  # type: ignore[arg-type]
errors: Dict[str, str] = st.session_state.setdefault("errors", {})

# 初期値
ui.setdefault("業種_大分類", major_opts[0])
ui.setdefault("業種_中分類", industry_major_mid[major_opts[0]][0]["code"])
ui.setdefault("mid_display", "コード＋名称")

# 定数
CUSTOMERS = ["BtoC (一般)", "BtoB (企業)", "高齢者", "若年層", "インバウンド"]
PRICES = ["低価格帯", "中価格帯", "高価格帯"]
CHANNELS = ["店舗型", "訪問サービス", "オンライン", "店舗＋オンライン"]

# バリデーション util ----------------------------------------------
JP_MAP = str.maketrans("０１２３４５６７８９．，", "0123456789..")

def to_half(txt: str) -> str:
    return txt.translate(JP_MAP).replace(",", "").replace("，", "").strip()

def count_chars(s: str) -> int:
    return len(s)  # マルチバイトも 1

def validate() -> Dict[str, str]:
    e: Dict[str, str] = {}
    req = ["業種_大分類", "業種_中分類", "地域", "主な商品・サービス", "顧客層", "価格帯", "販売方法"]
    for k in req:
        if not ui.get(k):
            e[k] = "必須入力です"
    if isinstance(ui.get("顧客層"), list) and not ui["顧客層"]:
        e["顧客層"] = "1 つ以上選択してください"
    prod = ui.get("主な商品・サービス", "")
    if prod and not (100 <= count_chars(prod) <= 200):
        e["主な商品・サービス"] = "100〜200文字で入力"
    return e

# プログレス計算 ------------------------------------------------------
TOTAL_REQUIRED = 7
filled = sum(1 for k in ["業種_大分類", "業種_中分類", "地域", "主な商品・サービス", "顧客層", "価格帯", "販売方法"] if ui.get(k))
progress = filled / TOTAL_REQUIRED

# ------------------------------------------------------------------
# 4. UI
# ------------------------------------------------------------------
show_subtitle("🏢 基本情報入力")

st.progress(progress, text=f"入力完了度 {int(progress*100)}%")

tab_major, tab_biz = st.tabs(["産業分類選択", "事業情報入力"])

with st.form("basic_form"):
    with tab_major:
        st.markdown("### 産業分類 *")
        ui["mid_display"] = st.radio("表示形式", ["コード＋名称", "コードのみ"], horizontal=True)
        ui["業種_大分類"] = st.selectbox("大分類", major_opts, index=major_opts.index(ui["業種_大分類"]))
        mids = industry_major_mid[ui["業種_大分類"]]
        labels = [d["code"] if ui["mid_display"] == "コードのみ" else f"{d['code']} {d['name']}" for d in mids]
        sel = next((i for i,d in enumerate(mids) if d["code"]==ui["業種_中分類"]), 0)
        choice = st.selectbox("中分類", labels, index=sel)
        ui["業種_中分類"] = choice.split()[0]

    with tab_biz:
        st.markdown("### 事業情報 *")
        ui["地域"] = st.text_input("所在地（市区町村）", ui.get("地域", ""))

        prod = st.text_area("商品・サービス概要 (100〜200字)", ui.get("主な商品・サービス", ""), height=100, key="prod_text")
        ui["主な商品・サービス"] = prod
        char_len = count_chars(prod)
        if char_len == 0:
            cls = "char-err"
        elif 100 <= char_len <= 200:
            cls = "char-ok"
        else:
            cls = "char-warn"
        st.markdown(f"<span class='char-count {cls}'>現在 {char_len} 文字</span>", unsafe_allow_html=True)

        ui["顧客層"] = st.multiselect("主な顧客層", CUSTOMERS, default=ui.get("顧客層", []))
        ui["価格帯"] = st.radio("価格帯", PRICES, index=PRICES.index(ui.get("価格帯", PRICES[1])))
        ui["販売方法"] = st.radio("販売方法", CHANNELS, index=CHANNELS.index(ui.get("販売方法", CHANNELS[0])))

    submitted = st.form_submit_button("💾 保存", disabled=bool(validate()))

# ------------------------------------------------------------------
if submitted:
    errors.clear()
    # validate() 呼び出しは disabled 状態で空想定だが安全に
    errors.update(validate())
    if errors:
        st.error("⚠️ 入力不備があります")
    else:
        st.session_state["user_input"] = ui
        st.success("✅ 保存しました")
        if (ROOT / NEXT_PAGE).exists():
            st.button("👉 次へ進む", on_click=lambda: st.switch_page(NEXT_PAGE))
        else:
            st.warning("次ページが見つかりません")

# エラー表示
for k, msg in errors.items():
    st.write(f"<span class='field-error'>{k}: {msg}</span>", unsafe_allow_html=True)

show_back_to_top()
