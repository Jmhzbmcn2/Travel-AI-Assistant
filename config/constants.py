"""
Constants — node names, search types, IATA codes.
"""

# ── Node names ────────────────────────────────────
NODE_PARSER = "parser"
NODE_SEARCH = "search"
NODE_RANKER = "ranker"
NODE_RESPONSE = "response"
NODE_ASK_USER = "ask_user"

# ── Search types ──────────────────────────────────
SEARCH_FLIGHTS = "flights"
SEARCH_HOTELS = "hotels"
SEARCH_BOTH = "both"

# ── City → IATA code mapping ─────────────────────
CITY_IATA = {
    "hồ chí minh": "SGN",
    "hcm": "SGN",
    "sài gòn": "SGN",
    "saigon": "SGN",
    "hà nội": "HAN",
    "hanoi": "HAN",
    "đà nẵng": "DAD",
    "da nang": "DAD",
    "nha trang": "CXR",
    "phú quốc": "PQC",
    "phu quoc": "PQC",
    "đà lạt": "DLI",
    "da lat": "DLI",
    "huế": "HUI",
    "hue": "HUI",
    "quy nhơn": "UIH",
    "cần thơ": "VCA",
    "hải phòng": "HPH",
    "buôn ma thuột": "BMV",
    "buôn mê thuột": "BMV",
    "ban mê thuột": "BMV",
    "vinh": "VII",
    "thanh hóa": "THD",
    "pleiku": "PXU",
    "côn đảo": "VCS",
    "tuy hòa": "TBB",
    "rạch giá": "VKG",
    "cà mau": "CAH",
    "đồng hới": "VDH",
}

# ── IATA code → City name (reverse lookup) ────────
IATA_CITY = {
    "SGN": "Hồ Chí Minh",
    "HAN": "Hà Nội",
    "DAD": "Đà Nẵng",
    "CXR": "Nha Trang",
    "PQC": "Phú Quốc",
    "DLI": "Đà Lạt",
    "HUI": "Huế",
    "UIH": "Quy Nhơn",
    "VCA": "Cần Thơ",
    "HPH": "Hải Phòng",
    "BMV": "Buôn Ma Thuột",
    "VII": "Vinh",
    "THD": "Thanh Hóa",
    "PXU": "Pleiku",
    "VCS": "Côn Đảo",
    "TBB": "Tuy Hòa",
    "VKG": "Rạch Giá",
    "CAH": "Cà Mau",
    "VDH": "Đồng Hới",
}
