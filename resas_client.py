import requests

BASE_URL = "https://opendata.resas-portal.go.jp/api/v1"

def get_population(pref_code: int, city_code: str) -> dict:
    """
    総人口構成（推移）。都道府県・市区町村単位
    """
    url = f"{BASE_URL}/population/composition/perYear"
    params = {"prefCode": pref_code, "cityCode": city_code}
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()

def get_population_pyramid(pref_code: int, city_code: str) -> dict:
    """
    年齢階層別人口ピラミッド
    """
    url = f"{BASE_URL}/population/pyramid/perYear"
    params = {"prefCode": pref_code, "cityCode": city_code}
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()

def get_daytime_population(pref_code: int, city_code: str) -> dict:
    """
    昼夜間人口（昼間人口・夜間人口・流入流出）
    """
    url = f"{BASE_URL}/population/movement/perDay"
    params = {"prefCode": pref_code, "cityCode": city_code}
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()

def get_commuter_flow(pref_code: int, city_code: str) -> dict:
    """
    通勤・通学の流入出データ
    """
    url = f"{BASE_URL}/population/movement/forCommuter"
    params = {"prefCode": pref_code, "cityCode": city_code}
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()

def get_industry_structure(pref_code: int, sic_code: str, city_code: str = "-") -> dict:
    """
    業種別事業所・従業員数（都道府県/市区町村単位）
    """
    url = f"{BASE_URL}/industry/structure/forIndustry"
    params = {"prefCode": pref_code, "cityCode": city_code, "sicCode": sic_code}
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()

def get_industry_sales(pref_code: int, sic_code: str, city_code: str = "-") -> dict:
    """
    業種別売上規模（都道府県/市区町村単位）
    """
    url = f"{BASE_URL}/industry/sales/forIndustry"
    params = {"prefCode": pref_code, "cityCode": city_code, "sicCode": sic_code}
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()

def get_openclose_trend(pref_code: int, sic_code: str, city_code: str = "-") -> dict:
    """
    業種別開廃業推移（都道府県/市区町村単位）
    """
    url = f"{BASE_URL}/industry/openclose/perYear"
    params = {"prefCode": pref_code, "cityCode": city_code, "sicCode": sic_code}
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()


# --- 利用例 ---
if __name__ == "__main__":
    # 東京都新宿区（pref_code=13, city_code="13104"）・製造業（09）
    pref_code = 13
    city_code = "13104"
    sic_code = "09"

    print("【人口推移】")
    print(get_population(pref_code, city_code))

    print("【年齢別人口ピラミッド】")
    print(get_population_pyramid(pref_code, city_code))

    print("【昼夜間人口】")
    print(get_daytime_population(pref_code, city_code))

    print("【流入/流出（通勤・通学）】")
    print(get_commuter_flow(pref_code, city_code))

    print("【業種別事業所数/従業員数】")
    print(get_industry_structure(pref_code, sic_code, city_code))

    print("【業種別売上規模】")
    print(get_industry_sales(pref_code, sic_code, city_code))

    print("【業種別開廃業推移】")
    print(get_openclose_trend(pref_code, sic_code, city_code))
