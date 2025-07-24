# -*- coding: utf-8 -*-
"""
0_Basic_Info_Input.py
---------------------
AI経営診断GPT – 基本情報入力フォーム（完全版）
------------------------------------------------
機能:
    1. 日本標準産業分類 (大分類20区分 × 中分類99コード) を外部マスタ (JSON or CSV) からロード
    2. 大分類ドロップダウン → 中分類ドロップダウン (コードのみ / コード+名称 切替可)
    3. 必須入力チェック & 文字数・数値バリデーション
    4. 顧客層 / 価格帯 / 販売方法 を選択式 UI で追加
    5. 入力保存 & SessionState 管理
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
# 2. 産業分類マスタのロード
# ------------------------------------------------------------------
MASTER_PATH = pathlib.Path(__file__).parent / "industry_master.json"  # ← JSON 版を想定

if not MASTER_PATH.exists():
    st.error("産業分類マスタ (industry_master.json) が見つかりません。配置を確認してください。")
    st.stop()

with MASTER_PATH.open("r", encoding="utf-8") as fp:
    industry_major_mid: Dict[str, List[Dict[str, str]]] = json.load(fp)

major_options = list(industry_major_mid.keys())

# ------------------------------------------------------------------
# 3. セッションステート初期化
# ------------------------------------------------------------------
if "user_input" not in st.session_state:
    st.session_state["user_input"] = {}
if "errors" not in st.session_state:
    st.session_state["errors"] = {}
ui = st.session_state["user_input"]
errors = st.session_state["errors"]

# デフォルト値
ui.setdefault("業種_大分類", major_options[0])
ui.setdefault("業種_中分類", industry_major_mid[major_options[0]][0]["code"])
ui.setdefault("mid_display_mode", "コード＋名称")  # 表示切替デフォルト

# ------------------------------------------------------------------
# 4. 各種定数
# ------------------------------------------------------------------
CUSTOMER_SEGMENTS = ["BtoC (一般消費者)", "BtoB (企業向け)", "高齢者", "若年層", "インバウンド客"]
PRICE_RANGES = ["低価格帯", "中価格帯", "高価格帯"]
CHANNELS = ["店舗型", "訪問サービス", "オンライン", "店舗＋オンライン"]

INT_FIELDS = []  # 数値バリデーション対象があれば追加
JP_NUM_MAP = str.maketrans("０１２３４５６７８９．，", "0123456789..")

# ------------------------------------------------------------------
# 5. バリデーション関数
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
    for k in ["業種_大分類", "業種_中分類", "地域", "主な商品・サービス", "顧客層", "価格帯", "販売方法"]:
        if not str(ui.get(k, "")).strip():
            e[k] = "必須入力です"
    # 文字数チェック
    prod = ui.get("主な商品・サービス", "")
    if prod and not (100 <= len(prod) <= 200):
        e["主な商品・サービス"] = "100〜200文字で入力してください"
    # 数値チェック (例があれば)
    for k in INT_FIELDS:
        v = ui.get(k, "")
        if v and not is_int(v):
            e[k] = "整数で入力"
    return e

# ------------------------------------------------------------------
# 6. UI 表示
# ------------------------------------------------------------------
show_subtitle("🏢 基本情報入力")

with st.form("form_basic_info"):
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("#### 産業分類の選択 *")

    # 表示モード切替
    ui["mid_display_mode"] = st.radio("中分類表示形式", ["コード＋名称", "コードのみ"], horizontal=True)

    # 大分類
    ui["業種_大分類"] = st.selectbox("業種（大分類）", major_options, index=major_options.index(ui["業種_大分類"]))

    # 中分類リスト生成
    mids = industry_major_mid[ui["業種_大分類"]]
    if ui["mid_display_mode"] == "コードのみ":
        mid_labels = [d["code"] for d in mids]
    else:
        mid_labels = [f"{d['code']} {d['name']}" for d in mids]
    default_mid = next((i for i, d in enumerate(mids) if d["code"] == ui["業種_中分類"]), 0)
    choice = st.selectbox("業種（中分類）", mid_labels, index=default_mid)
    # 選択結果からコードを抽出
    ui["業種_中分類"] = choice.split()[0]

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("#### 事業情報 *")

    ui["地域"] = st.text_input("所在地（市区町村）", value=ui.get("地域", ""))
    ui["主な商品・サービス"] = st.text_area("商品・サービス概要 (100〜200字)", value=ui.get("主な商品・サービス", ""), height=90)

    ui["顧客層"] = st.multiselect("主な顧客層", CUSTOMER_SEGMENTS, default=ui.get("顧客層", []))
    ui["価格帯"] = st.radio("価格帯", PRICE_RANGES, index=PRICE_RANGES.index(ui.get("価格帯", PRICE_RANGES[1])))
    ui["販売方法"] = st.radio("販売方法", CHANNELS, index=CHANNELS.index(ui.get("販売方法", CHANNELS[0])))

    st.markdown('</div>', unsafe_allow_html=True)

    submitted = st.form_submit_button("保存", type="primary")

# ------------------------------------------------------------------
# 7. 保存処理
# ------------------------------------------------------------------
if submitted:
    errors.clear()
    errors.update(validate_all())
    if errors:
        st.error("⚠️ 入力内容に不備があります。赤字メッセージをご確認ください。")
    else:
        st.success("✅ 基本情報を保存しました。次ステップへ進めます。")
        st.session_state["user_input"] = ui
        st.session_state.pop("errors", None)

# エラー表示（リアルタイム）
for field, msg in errors.items():
    st.write(f"<span class='field-error'>{field}: {msg}</span>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# 8. ページ下部に戻るボタン
# ------------------------------------------------------------------
show_back_to_top()
