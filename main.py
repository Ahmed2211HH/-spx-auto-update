import requests
import schedule
import time
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ==============================
# ⚙️ إعدادات
# ==============================
TELEGRAM_TOKEN = "8223218080:AAGkgSbf-wIWgdrhTKG6nHU_IUv45cPmadQ"
TELEGRAM_CHAT_ID = "-1002422090450"
POLYGON_KEY = "dzJEUppcquvIMruPfV_hyjYe0vIwPOI8"

# العقود - عدّلها أنت
CONTRACTS = [
    {"strike": 7100, "expiry": "2026-07-05", "type": "P", "entry_price": 3.00, "step": 0.25},
]

# ==============================
# 💾 حالة البوت
# ==============================
state = {}
for c in CONTRACTS:
    key = f"{c['strike']}{c['type']}"
    state[key] = {"next_alert": c["entry_price"] + c["step"], "alerts_count": 0}

# ==============================
# 📡 جلب السعر من Polygon
# ==============================
def get_option_price(strike, expiry, opt_type):
    try:
        # تحويل التاريخ لصيغة Polygon: O:SPX260705P07100000
        exp = expiry.replace("-", "")[2:]  # 260705
        strike_fmt = str(round(strike * 1000)).zfill(8)  # 07100000
        ticker = f"O:SPX{exp}{opt_type.upper()}{strike_fmt}"

        url = f"https://api.polygon.io/v2/last/trade/{ticker}?apiKey={POLYGON_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()

        if data.get("status") != "OK":
            # جرب snapshot
            url2 = f"https://api.polygon.io/v3/snapshot/options/SPX/{ticker}?apiKey={POLYGON_KEY}"
            r2 = requests.get(url2, timeout=10)
            data2 = r2.json()
            result = data2.get("results", {})
            details = result.get("details", {})
            day = result.get("day", {})
            greeks = result.get("greeks", {})
            return {
                "price": result.get("last_quote", {}).get("midpoint") or day.get("close") or 0,
                "prev_close": day.get("previous_close") or 0,
                "day_low": day.get("low") or 0,
                "day_high": day.get("high") or 0,
                "volume": day.get("volume") or 0,
                "open_interest": result.get("open_interest") or 0,
                "iv": result.get("implied_volatility") or 0,
            }

        price = data["results"]["p"]
        return {
            "price": price,
            "prev_close": price,
            "day_low": price,
            "day_high": price,
            "volume": data["results"].get("s") or 0,
            "open_interest": 0,
            "iv": 0,
        }
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_spx_price():
    try:
        url = f"https://api.polygon.io/v2/last/trade/I:SPX?apiKey={POLYGON_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()
        price = data["results"]["p"]
        # prev close
        url2 = f"https://api.polygon.io/v1/open-close/I:SPX/{datetime.now().strftime('%Y-%m-%d')}?apiKey={POLYGON_KEY}"
        r2 = requests.get(url2, timeout=10)
        data2 = r2.json()
        prev = data2.get("close") or price
        return {"price": price, "prev_close": prev}
    except:
        return {"price": 0, "prev_close": 0}

# ==============================
# 🎨 رسم الصورة
# ==============================
def draw_card(contract, opt_data, spx_data, alerts_count):
    W, H = 760, 480
    img = Image.new("RGB", (W, H), "#000000")
    draw = ImageDraw.Draw(img)

    price = opt_data["price"]
    prev_close = opt_data["prev_close"] or price
    change = price - prev_close
    change_pct = (change / prev_close * 100) if prev_close else 0
    is_up = change >= 0
    price_color = "#00e676" if is_up else "#ff3a5c"

    # خطوط فاصلة
    draw.line([(30, 110), (W-30, 110)], fill="#222222", width=1)
    draw.line([(30, 290), (W-30, 290)], fill="#222222", width=1)
    draw.line([(30, 400), (W-30, 400)], fill="#222222", width=1)
    draw.line([(W//2, 300), (W//2, 395)], fill="#222222", width=1)

    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_xs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except:
        font_big = font_med = font_sm = font_xs = ImageFont.load_default()

    # Header
    draw.text((30, 22), f"SPXW ${contract['strike']:,}", fill="#ffffff", font=font_med)
    months = ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    ep = contract['expiry'].split("-")
    exp_str = f"{int(ep[2])} {months[int(ep[1])]} {ep[0][2:]} (W) {'Put' if contract['type']=='P' else 'Call'} 100"
    draw.text((30, 72), exp_str, fill="#888888", font=font_sm)

    # السعر الكبير
    draw.text((30, 125), f"{price:.2f}", fill=price_color, font=font_big)

    # التغيير
    arrow = "▲" if is_up else "▼"
    draw.text((30, 248), f"{arrow} {abs(change):.2f}  {'+' if change_pct>=0 else ''}{change_pct:.2f}%", fill=price_color, font=font_med)

    # Stats يمين
    day_low = opt_data.get("day_low") or 0
    day_high = opt_data.get("day_high") or 0
    mid = (day_low + day_high) / 2
    vol = opt_data.get("volume") or 0
    oi = opt_data.get("open_interest") or 0
    vol_str = f"{vol/1000:.1f}K" if vol >= 1000 else str(vol)
    oi_str = f"{oi:,}" if oi else "—"

    for i, (label, val) in enumerate([("Mid", f"{mid:.2f}"), ("Open Int.", oi_str), ("Vol.", vol_str)]):
        y = 148 + i * 48
        draw.text((W-230, y), label, fill="#888888", font=font_sm)
        draw.text((W-90, y), val, fill="#ffffff", font=font_sm)

    # Stats أسفل يسار
    draw.text((30, 305), "Open/Prev Close", fill="#888888", font=font_xs)
    draw.text((30, 325), f"{prev_close:.2f} / {prev_close:.2f}", fill="#ffffff", font=font_sm)
    draw.text((30, 358), "Impl. Vol.", fill="#888888", font=font_xs)
    iv = opt_data.get("iv") or 0
    draw.text((30, 378), f"{iv*100:.2f}%" if iv else "—", fill="#ffffff", font=font_sm)

    # Stats أسفل يمين
    draw.text((W//2+20, 305), "Day's Range", fill="#888888", font=font_xs)
    draw.text((W//2+20, 325), f"{day_low:.2f} - {day_high:.2f}", fill="#ffffff", font=font_sm)
    draw.text((W//2+20, 358), "BREAKEVEN", fill="#888888", font=font_xs)
    draw.text((W//2+20, 378), f"{contract['strike'] - price:.2f}", fill="#ffffff", font=font_sm)

    # SPX footer
    spx_price = spx_data.get("price") or 0
    spx_prev = spx_data.get("prev_close") or spx_price
    if spx_price:
        spx_change = spx_price - spx_prev
        spx_pct = (spx_change / spx_prev * 100) if spx_prev else 0
        spx_color = "#00e676" if spx_change >= 0 else "#ff3a5c"
        draw.text((30, 432), "SPX", fill="#888888", font=font_sm)
        draw.text((80, 432), f"{spx_price:.2f}  {'+' if spx_pct>=0 else ''}{spx_pct:.2f}%", fill=spx_color, font=font_sm)

    now = datetime.now().strftime("%H:%M ET")
    draw.text((W-90, 432), now, fill="#555555", font=font_xs)

    # Badge
    draw.rounded_rectangle([W-190, 18, W-25, 58], radius=8, fill="#ffc107")
    draw.text((W-170, 30), f"تحديث #{alerts_count}", fill="#000000", font=font_sm)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ==============================
# 📤 إرسال الصورة
# ==============================
def send_photo(image_buf, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    image_buf.seek(0)
    r = requests.post(
        url,
        data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
        files={"photo": ("update.png", image_buf, "image/png")}
    )
    result = r.json()
    if result.get("ok"):
        print(f"✅ صورة أُرسلت!")
    else:
        print(f"❌ خطأ تيليجرام: {result}")

def send_message(text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text}
    )

# ==============================
# 🔄 المراقبة
# ==============================
def check():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] جاري التحقق...")
    spx = get_spx_price()

    for contract in CONTRACTS:
        key = f"{contract['strike']}{contract['type']}"
        opt = get_option_price(contract["strike"], contract["expiry"], contract["type"])
        if not opt or not opt["price"]:
            print(f"  ⚠️ فشل جلب {key}")
            continue

        price = opt["price"]
        next_alert = state[key]["next_alert"]
        print(f"  {key}: ${price:.2f} | تنبيه عند ${next_alert:.2f}")

        if price >= next_alert:
            state[key]["alerts_count"] += 1
            steps = int((price - contract["entry_price"]) / contract["step"])
            state[key]["next_alert"] = contract["entry_price"] + (steps + 1) * contract["step"]

            img_buf = draw_card(contract, opt, spx, state[key]["alerts_count"])
            caption = (
                f"🔔 تحديث #{state[key]['alerts_count']} | SPX {contract['strike']}{contract['type']}\n"
                f"💰 ${price:.2f} (+${price - contract['entry_price']:.2f})\n"
                f"⏭ التنبيه القادم: ${state[key]['next_alert']:.2f}"
            )
            send_photo(img_buf, caption)

        time.sleep(0.5)

# ==============================
# 🚀 تشغيل
# ==============================
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 بوت SPX Options")
    print("=" * 50)
    send_message("🤖 البوت شغال وجاهز!")
    check()
    schedule.every(1).minutes.do(check)
    while True:
        schedule.run_pending()
        time.sleep(30)
