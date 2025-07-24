# -*- coding: utf-8 -*-
"""
0_Basic_Info_Input.py  –  極プロダクション版
============================================================
機能概要
---------
1. **外部 JSON マスタ (industry_master.json)** から日本標準産業分類（令和5年）をロード
   - `jsonschema` で正式スキーマ検証（モジュールが無い場合はフォールバック）
   - `st.cache_data` で I/O キャッシュ
2. **大分類 → 中分類** 連動ドロップダウン
   - 表示切替 *コードのみ / コード+名称*
3. **必須・文字数・数値・最小選択数** バリデーション
   - 商品・サービス概要は *100〜200 文字*（マルチバイト安全カウント）
4. **顧客層 / 価格帯 / 販売方法** を選択 UI で実装
5. **保存成功後** に “次へ進む” ボタン表示（存在しない場合は警告）
6. **型ヒント厳格化**（`TypedDict`）
7. **ローカライズ準備**（簡易辞書）
"""
from __future__ import annotations

import importlib
import json
import unicodedata
from pathlib import Path
from typing import Dict, List, TypedDict, Any

import streamlit as st
from config import init_page
from ui_components import show_subtitle, show_back_to_top

# ------------------------------------------------------------------
# 0. 定数 / 設定
# ------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
MASTER_PATH = ROOT_DIR / "industry_master.json"
NEXT_PAGE = "1_External_Analysis.py"  # 次ページが無ければ警告表示

# i18n (簡易) -------------------------------------------------------
LANG = st.session_state.get("lang", "ja")
_ = {
    "ja": {
        "title": "AI経営診断 – 基本情報入力",
        "industry_loading": "⚙️ 産業分類マスタをロード中…",
        "master_missing": "❌ industry_master.json が見つかりません",
        "json_error": "❌ JSON 解析エラー",
        "schema_error": "❌ 産業分類マスタのスキーマが不正です",
        "select_major": "業種（大分類）",
        "select_mid": "業種（中分類）",
        "mid_display": "中分類表示形式",
        "business_info": "事業情報 *",
        "loc": "所在地（市区町村）",
        "product": "商品・サービス概要 (100〜200字)",
        "cust_seg": "主な顧客層",
        "price_range": "価格帯",
        "channel": "販売方法",
        "save": "💾 保存",
        "saved": "✅ 基本情報を保存しました。次ステップへ進めます。",
        "next": "👉 次へ進む (外部環境分析)",
        "next_missing": "⚠️ 次ページが存在しません。ファイルを配置してください。",
        "error": "⚠️ 入力内容に不備があります。赤字メッセージをご確認ください。",
        "require": "必須入力です",
        "prod_len": "100〜200文字で入力してください",
        "cust_min": "少なくとも 1 つ選択してください",
        "int_err": "整数で入力",
    }
}[LANG]

# ------------------------------------------------------------------
# 1. ページ初期化
# ------------------------------------------------------------------
init_page(title=_["title"])

# ------------------------------------------------------------------
# 2. マスタロード + スキーマ検証
# ------------------------------------------------------------------
SCHEMA = {
    "type": "object",
    "patternProperties": {
        ".*": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["code", "name"],
                "properties": {
                    "code": {"type": "string"},
                    "name": {"type": "string"},
                },
            },
        }
    },
}

JsonDict = Dict[str, List[Dict[str, str]]]

@st.cache_data(show_spinner=_["industry_loading"])
def load_master(path: Path) -> JsonDict:
    if not path.exists():
        st.error(_["master_missing"])
        st.stop()
    try:
        data: JsonDict = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        st.error(f"{_[ 'json_error' ]}: {exc}")
        st.stop()

    # schema validate
    try:
        jsonschema = importlib.import_module("jsonschema")
        jsonschema.validate(data, SCHEMA)  # type: ignore[attr-defined]
    except ModuleNotFoundError:
        # fallback 手動チェック
        for major, mids in data.items():
            if not isinstance(mids, list) or not mids:
                st.error(f"{_[ 'schema_error' ]}: '{major}' が空です")
                st.stop()
            for d in mids:
                if not {"code", "name"}.issubset(d):
                    st.error(f"{_[ 'schema_error' ]}: {d}")
                    st.stop()
    except Exception as exc:
        st.error(f"{_[ 'schema_error' ]}: {exc}")
        st.stop()
    return data

industry_major_mid = load_master(MASTER_PATH)
major_options = list(industry_major_mid.keys())

# ------------------------------------------------------------------
# 3. 型定義 & セッションステート
# ------------------------------------------------------------------
class UIState(TypedDict, total=False):
    業種_大分類: str
    業種_中分類: str
    mid_display_mode: str
    地域: str
    主な商品・サービス: str
    顧客層: List[str]
    価格帯: str
    販売方法: str

ui: UIState = st.session_state.setdefault("user_input", UIState())  # type: ignore[arg-type]
errors: Dict[str, str] = st.session_state.setdefault("errors", {})

ui.setdefault("業種_大分類", major_options[0])
ui.setdefault("業種_中分類", industry_major_mid[major_options[0]][0]["code"])
ui.setdefault("mid_display_mode", "コード＋名称")

# ------------------------------------------------------------------
# 4. ビジネス定数
# ------------------------------------------------------------------
CUSTOMER_SEGMENTS = [
    "BtoC (一般消費者)", "BtoB (企業向け)", "高齢者", "若年層", "インバウンド客"
]
PRICE_RANGES = ["低価格帯", "中価格帯", "高価格帯"]
CHANNELS = ["店舗型", "訪問サービス", "オンライン", "店舗＋オンライン"]
INT_FIELDS: List[str] = []
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

def char_len(text: str) -> int:
    return sum(1 for _ in text)

def validate() -> Dict[str, str]:
    e: Dict[str, str] = {}
    req = [
        "業種_大分類", "業種_中分類", "地域", "主な商品・サービス", "顧客層", "価格帯", "販売方法"
    ]
    for k in req:
        if not ui.get(k):
            e[k] = _["require"]
    if isinstance(ui.get("顧客層"), list) and not ui["顧客層"]:
        e["顧客層"] = _["cust_min"]
    prod = ui.get("主な商品・サービス", "")
    if prod and not (100 <= char_len(prod) <= 200):
        e["主な商品・サービス"] = _["prod_len"]
    for f in INT_FIELDS:
        v = ui.get(f, "")
        if v and not is_int(v):
            e[f] = _["int_err"]
    return e

# ------------------------------------------------------------------
# 6. UI レンダリング
# ------------------------------------------------------------------
show_subtitle("🏢 基本情報入力")

with st.form("basic_info_form"):
    # 産業分類セクション -------------------------------------------------
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown("#### 産業分類の選択 *")

    ui["mid_display_mode"] = st.radio(_["mid_display"], ["コード＋名称", "コードのみ"], horizontal=True)

    ui["業種_大分類"] = st.selectbox(
        _["select_major"], major_options, index=major_options.index(ui["業種_大分類"])
    )

    mids = industry_major_mid[ui["業種_大分類"]]
    mid_labels = (
        [d["code"] for d in mids] if ui["mid_display_mode"] == "コードのみ" else [f"{d['code']} {d['name']}" for d in mids]
    )
    sel = next((i for i, d in enumerate(mids) if d["code"] == ui["業種_中分類"]), 0)
    choice = st.selectbox(_["select_mid"], mid_labels, index=sel)
    ui["業種_中分類"] = choice.split()[0]
    st.markdown("</div>", unsafe_allow_html=True)

    # 事業情報セクション -------------------------------------------------
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown(f"#### {_[ 'business_info' ]}")

    ui["地域"] = st.text_input(_["loc"], ui.get("地域", ""))
    ui["主な商品・サービス"] = st.text_area(
        _["product"], ui.get("主な商品・サービス", ""), height=90
    )
    ui["顧客層"] = st.multiselect(_["cust_seg"], CUSTOMER_SEGMENTS, default=ui.get("顧客層", []))
    ui["価格帯"] = st.radio(_["price_range"], PRICE_RANGES, index=PRICE_RANGES.index(ui.get("価格帯", PRICE_RANGES[1])))
    ui["販売方法"] = st.radio(_["channel"], CHANNELS, index=CHANNELS.index(ui.get("販売方法", CHANNELS[0])))
    st.markdown("</div>", unsafe_allow_html=True)

    submitted = st.form_submit_button(_["save"], type="primary")

# ------------------------------------------------------------------
# 7. 保存処理
# ------------------------------------------------------------------
if submitted:
    errors.clear()
    errors.update(validate())
    if errors:
        st.error(_["error"])
    else:
        st.session_state["user_input"] = ui
        st.session_state.pop("errors", None)
        st.success(_["saved"])
        if Path(ROOT_DIR / NEXT_PAGE).exists():
            if st.button(_["next"]):
                st.switch_page(NEXT_PAGE)
        else:
            st.warning(_["next_missing"])

# ------------------------------------------------------------------
# 8. エラー描画 & 戻るボタン
# ------------------------------------------------------------------
for field, msg in errors.items():
    st.write(f"<span class='field-error'>{field}: {msg}</span>", unsafe_allow_html=True)

show_back_to_top()
