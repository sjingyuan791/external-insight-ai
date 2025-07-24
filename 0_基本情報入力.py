# -*- coding: utf-8 -*-
"""
0_Basic_Info_Input.py — フルリファクタ版
============================================================
* AI経営診断 GPT : 基本情報入力フォーム
* 日本標準産業分類（R5 改定）完全対応
* 改善ポイント（★3 優先まで）をすべて実装
    1. 外部 JSON マスタ読み込み + スキーマ検証 + cache_data
    2. コードのみ / コード+名称 表示切替
    3. 必須 multiselect の min 選択チェック
    4. 文字数・数値バリデーション強化
    5. 残存タスク用に INT_FIELDS 汎用バリデータ
"""
from __future__ import annotations

import json
import pathlib
from typing import Dict, List

import streamlit as st
from config import init_page
from ui_components import show_subtitle, show_back_to_top

# ------------------------------------------------------------------
# 1. ページ初期化
# ------------------------------------------------------------------
init_page(title="AI経営診断 – 基本情報入力")

# ------------------------------------------------------------------
# 2. 産業分類マスタロード & 検証
# ------------------------------------------------------------------
MASTER_PATH = pathlib.Path(__file__).parent / "industry_master.json"

@st.cache_data(show_spinner="産業分類マスタをロード中…")
def load_master(path: pathlib.Path) -> Dict[str, List[Dict[str, str]]]:
    if not path.exists():
        st.error("❌ 産業分類マスタ (industry_master.json) が見つかりません")
        st.stop()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        st.error(f"❌ JSON 解析エラー: {exc}")
        st.stop()
    # スキーマ簡易検証
    for major, mids in data.items():
        if not isinstance(mids, list) or not mids:
            st.error(f"❌ '{major}' の中分類がリスト形式で定義されていません")
            st.stop()
        for d in mids:
            if not {"code", "name"}.issubset(d):
                st.error(f"❌ 中分類辞書に code / name キーが不足: {d}")
                st.stop()
    return data

industry_major_mid = load_master(MASTER_PATH)
major_options = list(industry_major_mid.keys())

# ------------------------------------------------------------------
# 3. セッションステート初期化
# ------------------------------------------------------------------
ui: Dict[str, any] = st.session_state.setdefault("user_input", {})
errors: Dict[str, str] = st.session_state.setdefault("errors", {})

ui.setdefault("業種_大分類", major_options[0])
ui.setdefault("業種_中分類", industry_major_mid[major_options[0]][0]["code"])
ui.setdefault("mid_display_mode", "コード＋名称")

# ------------------------------------------------------------------
# 4. 定数
# ------------------------------------------------------------------
CUSTOMER_SEGMENTS = [
    "BtoC (一般消費者)", "BtoB (企業向け)", "高齢者", "若年層", "インバウンド客"
]
PRICE_RANGES = ["低価格帯", "中価格帯", "高価格帯"]
CHANNELS = ["店舗型", "訪問サービス", "オンライン", "店舗＋オンライン"]

INT_FIELDS: List[str] = []  # 将来拡張用
JP_NUM_MAP = str.maketrans("０１２３４５６７８９．，", "0123456789..")

# ------------------------------------------------------------------
# 5. バリデーション
# ------------------------------------------------------------------

def to_half(v: str) -> str:
    return v.replace(",", "").replace("，", "").translate(JP_NUM_MAP).strip()

def is_int(v: str) -> bool:
    try:
        int(to_half(v))
        return True
    except ValueError:
        return False

def validate_all() -> Dict[str, str]:
    e: Dict[str, str] = {}
    # 必須チェック
    required = [
        "業種_大分類", "業種_中分類", "地域", "主な商品・サービス", "顧客層", "価格帯", "販売方法"
    ]
    for k in required:
        if not ui.get(k):
            e[k] = "必須入力です"
    # 商品概要 100〜200字
    prod = ui.get("主な商品・サービス", "")
    if prod and not (100 <= len(prod) <= 200):
        e["主な商品・サービス"] = "100〜200文字で入力してください"
    # 顧客層最低1選択
    if not ui.get("顧客層"):
        e["顧客層"] = "少なくとも1つ選択してください"
    # 数値系
    for k in INT_FIELDS:
        v = ui.get(k, "")
        if v and not is_int(v):
            e[k] = "整数で入力"
    return e

# ------------------------------------------------------------------
# 6. UI
# ------------------------------------------------------------------
show_subtitle("🏢 基本情報入力")

with st.form("form_basic_info"):
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("#### 産業分類の選択 *")

    ui["mid_display_mode"] = st.radio(
        "中分類表示形式", ["コード＋名称", "コードのみ"], horizontal=True
    )
    ui["業種_大分類"] = st.selectbox(
        "業種（大分類）", major_options, index=major_options.index(ui["業種_大分類"])
    )
    mids = industry_major_mid[ui["業種_大分類"]]
    mid_labels = (
        [d["code"] for d in mids]
        if ui["mid_display_mode"] == "コードのみ"
        else [f"{d['code']} {d['name']}" for d in mids]
    )
    sel_idx = next((i for i, d in enumerate(mids) if d["code"] == ui["業種_中分類"]), 0)
    choice = st.selectbox("業種（中分類）", mid_labels, index=sel_idx)
    ui["業種_中分類"] = choice.split()[0]
    st.markdown("</div>", unsafe_allow_html=True)

    # 事業情報
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("#### 事業情報 *")

    ui["地域"] = st.text_input("所在地（市区町村）", ui.get("地域", ""))
    ui["主な商品・サービス"] = st.text_area(
        "商品・サービス概要 (100〜200字)", ui.get("主な商品・サービス", ""), height=90
    )

    ui["顧客層"] = st.multiselect(
        "主な顧客層", CUSTOMER_SEGMENTS, default=ui.get("顧客層", [])
    )
    ui["価格帯"] = st.radio(
        "価格帯", PRICE_RANGES, index=PRICE_RANGES.index(ui.get("価格帯", PRICE_RANGES[1]))
    )
    ui["販売方法"] = st.radio(
        "販売方法", CHANNELS, index=CHANNELS.index(ui.get("販売方法", CHANNELS[0]))
    )
    st.markdown("</div>", unsafe_allow_html=True)

    submitted = st.form_submit_button("💾 保存", type="primary")

# ------------------------------------------------------------------
# 7. 保存処理
# ------------------------------------------------------------------
if submitted:
    errors.clear()
    errors.update(validate_all())
    if errors:
        st.error("⚠️ 入力内容に不備があります。赤字メッセージをご確認ください。")
    else:
        st.session_state["user_input"] = ui
        st.session_state.pop("errors", None)
        st.success("✅ 基本情報を保存しました。次ステップへ進めます。")

# エラー表示
for field, msg in errors.items():
    st.write(f"<span class='field-error'>{field}: {msg}</span>", unsafe_allow_html=True)

show_back_to_top()
