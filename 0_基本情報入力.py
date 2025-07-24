# -*- coding: utf-8 -*-
"""
0_Basic_Info_Input.py — FINAL 市区町村セレクトボックス対応
----------------------------------------------------------
・市区町村はExcelから都道府県→市区町村のセレクト方式
・API連携/自動化のため pref_code, city_code も保存
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, TypedDict

import streamlit as st
import pandas as pd
from config import init_page
from ui_components import show_subtitle, show_back_to_top

# ========================================================================= #
# 0. 産業分類 (大分類 → 中分類 list[dict(code,name)] )                      #
# ========================================================================= #
industry_major_mid: Dict[str, List[Dict[str, str]]] = {
    "農業，林業": [
        {"code": "01", "name": "農業"},
        {"code": "02", "name": "林業"},
    ],
    "漁業": [
        {"code": "03", "name": "漁業（水産養殖業を除く）"},
        {"code": "04", "name": "水産養殖業"},
    ],
    "鉱業，採石業，砂利採取業": [
        {"code": "05", "name": "鉱業，採石業，砂利採取業"},
    ],
    "建設業": [
        {"code": "06", "name": "総合工事業"},
        {"code": "07", "name": "職別工事業（設備工事業を除く）"},
        {"code": "08", "name": "設備工事業"},
    ],
    "製造業": [
        {"code": "09", "name": "食料品製造業"},
        {"code": "10", "name": "飲料・たばこ・飼料製造業"},
        {"code": "11", "name": "繊維工業"},
        {"code": "12", "name": "木材・木製品製造業（家具を除く）"},
        {"code": "13", "name": "家具・装備品製造業"},
        {"code": "14", "name": "パルプ・紙・紙加工品製造業"},
        {"code": "15", "name": "印刷・同関連業"},
        {"code": "16", "name": "化学工業"},
        {"code": "17", "name": "石油製品・石炭製品製造業"},
        {"code": "18", "name": "プラスチック製品製造業（別掲を除く）"},
        {"code": "19", "name": "ゴム製品製造業"},
        {"code": "20", "name": "なめし革・同製品・毛皮製造業"},
        {"code": "21", "name": "窯業・土石製品製造業"},
        {"code": "22", "name": "鉄鋼業"},
        {"code": "23", "name": "非鉄金属製造業"},
        {"code": "24", "name": "金属製品製造業"},
        {"code": "25", "name": "はん用機械器具製造業"},
        {"code": "26", "name": "生産用機械器具製造業"},
        {"code": "27", "name": "業務用機械器具製造業"},
        {"code": "28", "name": "電子部品・デバイス・電子回路製造業"},
        {"code": "29", "name": "電気機械器具製造業"},
        {"code": "30", "name": "情報通信機械器具製造業"},
        {"code": "31", "name": "輸送用機械器具製造業"},
        {"code": "32", "name": "その他の製造業"},
    ],
    "電気・ガス・熱供給・水道業": [
        {"code": "33", "name": "電気業"},
        {"code": "34", "name": "ガス業"},
        {"code": "35", "name": "熱供給業"},
        {"code": "36", "name": "水道業"},
    ],
    "情報通信業": [
        {"code": "37", "name": "通信業"},
        {"code": "38", "name": "放送業"},
        {"code": "39", "name": "情報サービス業"},
        {"code": "40", "name": "インターネット附随サービス業"},
        {"code": "41", "name": "映像・音声・文字情報制作業"},
    ],
    "運輸業，郵便業": [
        {"code": "42", "name": "鉄道業"},
        {"code": "43", "name": "道路旅客運送業"},
        {"code": "44", "name": "道路貨物運送業"},
        {"code": "45", "name": "水運業"},
        {"code": "46", "name": "航空運輸業"},
        {"code": "47", "name": "倉庫業"},
        {"code": "48", "name": "運輸に附帯するサービス業"},
        {"code": "49", "name": "郵便業（信書便事業を含む）"},
    ],
    "卸売業，小売業": [
        {"code": "50", "name": "各種商品卸売業"},
        {"code": "51", "name": "繊維・衣服等卸売業"},
        {"code": "52", "name": "飲食料品卸売業"},
        {"code": "53", "name": "建築材料，鉱物・金属材料等卸売業"},
        {"code": "54", "name": "機械器具卸売業"},
        {"code": "55", "name": "その他の卸売業"},
        {"code": "56", "name": "各種商品小売業"},
        {"code": "57", "name": "織物・衣服・身の回り品小売業"},
        {"code": "58", "name": "飲食料品小売業"},
        {"code": "59", "name": "機械器具小売業"},
        {"code": "60", "name": "その他の小売業"},
        {"code": "61", "name": "無店舗小売業"},
    ],
    "金融業，保険業": [
        {"code": "62", "name": "銀行業"},
        {"code": "63", "name": "協同組織金融業"},
        {"code": "64", "name": "貸金業，クレジットカード業等非預金信用機関"},
        {"code": "65", "name": "金融商品取引業，商品先物取引業"},
        {"code": "66", "name": "補助的金融業等"},
        {"code": "67", "name": "保険業（保険媒介代理業，保険サービス業を含む）"},
    ],
    "不動産業，物品賃貸業": [
        {"code": "68", "name": "不動産取引業"},
        {"code": "69", "name": "不動産賃貸業・管理業"},
        {"code": "70", "name": "物品賃貸業"},
    ],
    "学術研究，専門・技術サービス業": [
        {"code": "71", "name": "学術・開発研究機関"},
        {"code": "72", "name": "専門サービス業（他に分類されないもの）"},
        {"code": "73", "name": "広告業"},
        {"code": "74", "name": "技術サービス業（他に分類されないもの）"},
    ],
    "宿泊業，飲食サービス業": [
        {"code": "75", "name": "宿泊業"},
        {"code": "76", "name": "飲食店"},
        {"code": "77", "name": "持ち帰り・配達飲食サービス業"},
    ],
    "生活関連サービス業，娯楽業": [
        {"code": "78", "name": "洗濯・理容・美容・浴場業"},
        {"code": "79", "name": "その他の生活関連サービス業"},
        {"code": "80", "name": "娯楽業"},
    ],
    "教育，学習支援業": [
        {"code": "81", "name": "学校教育"},
        {"code": "82", "name": "その他の教育・学習支援業"},
    ],
    "医療，福祉": [
        {"code": "83", "name": "医療業"},
        {"code": "84", "name": "保健衛生"},
        {"code": "85", "name": "社会保険・社会福祉・介護事業"},
    ],
    "複合サービス事業": [
        {"code": "86", "name": "郵便局"},
        {"code": "87", "name": "協同組合（他に分類されないもの）"},
    ],
    "サービス業（他に分類されないもの）": [
        {"code": "88", "name": "廃棄物処理業"},
        {"code": "89", "name": "自動車整備業"},
        {"code": "90", "name": "機械等修理業（別掲を除く）"},
        {"code": "91", "name": "職業紹介・労働者派遣業"},
        {"code": "92", "name": "その他の事業サービス業"},
        {"code": "93", "name": "政治・経済・文化団体"},
        {"code": "94", "name": "宗教"},
        {"code": "95", "name": "その他のサービス業"},
    ],
    "公務（他に分類されるものを除く）": [
        {"code": "96", "name": "外国公務"},
        {"code": "97", "name": "国家公務"},
        {"code": "98", "name": "地方公務"},
    ],
    "分類不能の産業": [
        {"code": "99", "name": "分類不能の産業"},
    ],
}

ROOT      = Path(__file__).resolve().parent
NEXT_PAGE = "1_External_Analysis.py"
CUSTOMERS = ["BtoC (一般)","BtoB (企業)","高齢者","若年層","インバウンド"]
PRICES    = ["低価格帯","中価格帯","高価格帯"]
CHANNELS  = ["店舗型","訪問サービス","オンライン","店舗＋オンライン"]
INT_FIELDS= ["従業員数"]
JP_MAP    = str.maketrans("０１２３４５６７８９．，", "0123456789..")

init_page(title="AI経営診断 – 基本情報入力")

st.markdown("""
<style>
.char-count{font-size:.85em;margin-top:-.25rem}
.char-ok{color:#4caf50}.char-warn{color:#f9a825}.char-err{color:#e53935}
.field-error{color:#e53935;font-size:.9em;margin:0 0 4px 0}
.sticky{position:fixed;bottom:0;left:0;width:100%;padding:.7rem 1rem;
background:#ffffffee;backdrop-filter:blur(6px);box-shadow:0 -1px 6px rgba(0,0,0,.1)}
.sticky .stButton>button{width:100%;font-weight:700}
</style>
""", unsafe_allow_html=True)

# --- 市区町村マスタ読込
@st.cache_data
def load_city_master(filepath: str) -> pd.DataFrame:
    df = pd.read_excel(filepath, dtype=str)
    df = df[["都道府県名", "都道府県コード", "市区町村名", "市区町村コード"]]
    return df

city_master = load_city_master("/mnt/data/000925835.xlsx")

# --- State
class UI(TypedDict, total=False):
    業種_大分類: str
    業種_中分類: str
    mid_display: str
    pref_name: str
    city_name: str
    pref_code: str
    city_code: str
    主な商品・サービス: str
    顧客層: List[str]
    価格帯: str
    販売方法: str
    従業員数: str

ui: UI = st.session_state.setdefault("user_input", UI())  # type: ignore[arg-type]
errors: Dict[str,str] = st.session_state.setdefault("errors", {})

major_opts = list(industry_major_mid.keys())
ui.setdefault("業種_大分類", major_opts[0])
ui.setdefault("業種_中分類", industry_major_mid[major_opts[0]][0]["code"])
ui.setdefault("mid_display", "コード＋名称")
ui.setdefault("pref_name", city_master["都道府県名"].iloc[0])
ui.setdefault("city_name", city_master[city_master["都道府県名"]==ui["pref_name"]]["市区町村名"].iloc[0])

# ---- バリデーション
def to_half(v:str)->str:
    return v.translate(JP_MAP).replace(",","").replace("，","").strip()
def is_int(v:str)->bool:
    return v and to_half(v).isdigit()
def char_len(s:str)->int:
    return len(s)

def validate()->Dict[str,str]:
    e:Dict[str,str]={}
    req=["業種_大分類","業種_中分類","pref_name","city_name",
         "主な商品・サービス","顧客層","価格帯","販売方法"]
    for k in req:
        if not ui.get(k): e[k]="必須入力です"
    if isinstance(ui.get("顧客層"),list) and not ui["顧客層"]:
        e["顧客層"]="1 つ以上選択してください"
    prod=ui.get("主な商品・サービス","")
    if prod and not (100<=char_len(prod)<=200):
        e["主な商品・サービス"]="100〜200文字で入力してください"
    for f in INT_FIELDS:
        if ui.get(f) and not is_int(ui[f]): e[f]="整数で入力してください"
    return e

# ---- プログレスバー
REQ_KEYS = ["業種_大分類","業種_中分類","pref_name","city_name",
            "主な商品・サービス","顧客層","価格帯","販売方法"]
progress = sum(bool(ui.get(k)) for k in REQ_KEYS)/len(REQ_KEYS)
st.progress(progress, text=f"入力完了度 {int(progress*100)}%")

show_subtitle("🏢 基本情報入力")

tab_major, tab_biz = st.tabs(["産業分類","事業情報"])

with tab_major:
    ui["mid_display"] = st.radio("表示形式",["コード＋名称","コードのみ"], horizontal=True)
    ui["業種_大分類"] = st.selectbox("大分類", major_opts, index=major_opts.index(ui["業種_大分類"]))
    mids = industry_major_mid[ui["業種_大分類"]]
    labels = [d["code"] if ui["mid_display"]=="コードのみ"
              else f"{d['code']} {d['name']}" for d in mids]
    sel = next((i for i,d in enumerate(mids) if d["code"]==ui["業種_中分類"]),0)
    choice = st.selectbox("中分類", labels, index=sel)
    ui["業種_中分類"] = choice.split()[0]

with tab_biz:
    col1, col2 = st.columns(2)
    with col1:
        # 都道府県・市区町村ドロップダウン
        pref_name = st.selectbox("都道府県", sorted(city_master["都道府県名"].unique()),
                                 index=list(city_master["都道府県名"].unique()).index(ui["pref_name"]))
        cities = city_master[city_master["都道府県名"]==pref_name]["市区町村名"].unique()
        city_name = st.selectbox("市区町村", sorted(cities),
                                 index=list(cities).index(ui["city_name"]) if ui["city_name"] in cities else 0)
        ui["pref_name"] = pref_name
        ui["city_name"] = city_name
        # コードを自動取得
        ui["pref_code"] = city_master[city_master["都道府県名"]==pref_name]["都道府県コード"].values[0]
        ui["city_code"] = city_master[(city_master["都道府県名"]==pref_name) & (city_master["市区町村名"]==city_name)]["市区町村コード"].values[0]

        ui["従業員数"] = st.text_input("従業員数", ui.get("従業員数",""), placeholder="例) 10")
    with col2:
        prod = st.text_area("商品・サービス概要 (100〜200字)", ui.get("主な商品・サービス",""), height=110)
        ui["主な商品・サービス"] = prod
        L = char_len(prod)
        cls = "char-ok" if 100<=L<=200 else ("char-warn" if L else "char-err")
        st.markdown(f"<span class='char-count {cls}'>現在 {L} 文字</span>", unsafe_allow_html=True)

    ui["顧客層"]   = st.multiselect("主な顧客層", CUSTOMERS, default=ui.get("顧客層", []))
    ui["価格帯"]   = st.radio("価格帯", PRICES, index=PRICES.index(ui.get("価格帯",PRICES[1])))
    ui["販売方法"] = st.radio("販売方法", CHANNELS, index=CHANNELS.index(ui.get("販売方法",CHANNELS[0])))

# ---- エラー表示 & Sticky Action Bar
errors.clear(); errors.update(validate())
for k,msg in errors.items():
    st.markdown(f"<div class='field-error'>{k}: {msg}</div>",unsafe_allow_html=True)

def save():
    st.session_state["user_input"] = ui
    st.success("✅ 入力を保存しました")

st.markdown("<div style='height:70px'></div>", unsafe_allow_html=True)
st.markdown("<div class='sticky'>", unsafe_allow_html=True)
c1,c2 = st.columns(2)
with c1:
    st.button("💾 保存", on_click=save, disabled=bool(errors))
with c2:
    if (ROOT/NEXT_PAGE).exists():
        st.button("👉 次へ進む", disabled=bool(errors),
                  on_click=lambda: st.switch_page(NEXT_PAGE))
    else:
        st.button("次ページがありません", disabled=True)
st.markdown("</div>", unsafe_allow_html=True)

show_back_to_top()
