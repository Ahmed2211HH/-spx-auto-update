import requests, schedule, time, io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

TELEGRAM_TOKEN = "8223218080:AAGkgSbf-wIWgdrhTKG6nHU_IUv45cPmadQ"
TELEGRAM_CHAT_ID = "-1002422090450"
POLYGON_KEY = "dzJEUppcquvIMruPfV_hyjYe0vIwPOI8"
SUPABASE_URL = "https://fwqjwwupbkhhyiybgcdb.supabase.co"
SUPABASE_KEY = "sb_publishable_OoL_dTbdgp-5r7yU4tuWeg_dDkAdymg"

state = {}

def supabase(method, path, body=None):
    r = requests.request(method, f"{SUPABASE_URL}/rest/v1/{path}", headers={
        "apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }, json=body, timeout=10)
    return r.json()

def get_contracts():
    return supabase("GET", "contracts?active=eq.true")

def get_option_price(strike, expiry, opt_type):
    try:
        exp = expiry.replace("-", "")[2:]
        strike_fmt = str(round(strike * 1000)).zfill(8)
        ticker = f"O:SPX{exp}{opt_type.upper()}{strike_fmt}"
        url = f"https://api.polygon.io/v3/snapshot/options/SPX/{ticker}?apiKey={POLYGON_KEY}"
        r = requests.get(url, timeout=10)
        result = r.json().get("results", {})
        day = result.get("day", {})
        return {
            "price": result.get("last_quote", {}).get("midpoint") or day.get("close") or 0,
            "prev_close": day.get("previous_close") or 0,
            "day_low": day.get("low") or 0,
            "day_high": day.get("high") or 0,
            "volume": day.get("volume") or 0,
            "open_interest": result.get("open_interest") or 0,
        }
    except Exception as e:
        print(f"Error: {e}"); return None

def get_spx():
    try:
        r = requests.get(f"https://api.polygon.io/v2/last/trade/I:SPX?apiKey={POLYGON_KEY}", timeout=10)
        price = r.json()["results"]["p"]
        return {"price": price, "prev_close": price}
    except: return {"price": 0, "prev_close": 0}

def draw_card(contract, opt, spx, count):
    W, H = 760, 480
    img = Image.new("RGB", (W, H), "#000000")
    draw = ImageDraw.Draw(img)
    price = opt["price"]; prev = opt["prev_close"] or price
    change = price - prev; pct = (change/prev*100) if prev else 0
    is_up = change >= 0; pc = "#00e676" if is_up else "#ff3a5c"
    for y in [110,290,400]: draw.line([(30,y),(W-30,y)], fill="#222", width=1)
    draw.line([(W//2,300),(W//2,395)], fill="#222", width=1)
    try:
        fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        fm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        fx = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except: fb=fm=fs=fx=ImageFont.load_default()
    months=["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    ep=contract["expiry"].split("-")
    draw.text((30,22), f"SPXW ${int(contract['strike']):,}", fill="#fff", font=fm)
    draw.text((30,72), f"{int(ep[2])} {months[int(ep[1])]} {ep[0][2:]} (W) {'Put' if contract['type']=='P' else 'Call'} 100", fill="#888", font=fs)
    draw.text((30,125), f"{price:.2f}", fill=pc, font=fb)
    draw.text((30,248), f"{'▲' if is_up else '▼'} {abs(change):.2f}  {'+' if pct>=0 else ''}{pct:.2f}%", fill=pc, font=fm)
    dlo=opt.get("day_low",0); dhi=opt.get("day_high",0)
    mid=(dlo+dhi)/2; vol=opt.get("volume",0)
    vol_s=f"{vol/1000:.1f}K" if vol>=1000 else str(vol)
    oi=opt.get("open_interest",0); oi_s=f"{oi:,}" if oi else "—"
    for i,(l,v) in enumerate([("Mid",f"{mid:.2f}"),("Open Int.",oi_s),("Vol.",vol_s)]):
        y=148+i*48; draw.text((W-230,y),l,fill="#888",font=fs); draw.text((W-90,y),v,fill="#fff",font=fs)
    draw.text((30,305),"Open/Prev Close",fill="#888",font=fx); draw.text((30,325),f"{prev:.2f} / {prev:.2f}",fill="#fff",font=fs)
    draw.text((30,358),"Impl. Vol.",fill="#888",font=fx); draw.text((30,378),"—",fill="#fff",font=fs)
    draw.text((W//2+20,305),"Day's Range",fill="#888",font=fx); draw.text((W//2+20,325),f"{dlo:.2f} - {dhi:.2f}",fill="#fff",font=fs)
    draw.text((W//2+20,358),"BREAKEVEN",fill="#888",font=fx); draw.text((W//2+20,378),f"{contract['strike']-price:.2f}",fill="#fff",font=fs)
    if spx["price"]:
        sc=spx["price"]; sp=spx["prev_close"] or sc; sd=sc-sp; spct=(sd/sp*100) if sp else 0
        draw.text((30,432),"SPX",fill="#888",font=fs)
        draw.text((80,432),f"{sc:.2f}  {'+' if spct>=0 else ''}{spct:.2f}%",fill="#00e676" if sd>=0 else "#ff3a5c",font=fs)
    draw.text((W-90,432),datetime.now().strftime("%H:%M ET"),fill="#555",font=fx)
    try: draw.rounded_rectangle([W-190,18,W-25,58],radius=8,fill="#ffc107")
    except: draw.rectangle([W-190,18,W-25,58],fill="#ffc107")
    draw.text((W-170,30),f"تحديث #{count}",fill="#000",font=fm)
    buf=io.BytesIO(); img.save(buf,format="PNG"); buf.seek(0); return buf

def send_photo(buf, caption=""):
    buf.seek(0)
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
        data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
        files={"photo": ("update.png", buf, "image/png")})
    print("✅ أُرسلت!" if r.json().get("ok") else f"❌ {r.json()}")

def send_msg(text):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text})

def check():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] جاري التحقق...")
    contracts = get_contracts()
    if not contracts: print("  لا توجد عقود نشطة"); return
    spx = get_spx()
    for c in contracts:
        key = f"{c['id']}"
        entry = float(c["entry_price"]); step = float(c["step"])
        if key not in state:
            state[key] = {"next_alert": entry + step, "count": 0}
        opt = get_option_price(float(c["strike"]), c["expiry"], c["type"])
        if not opt or not opt["price"]: print(f"  ⚠️ فشل {c['strike']}{c['type']}"); continue
        price = opt["price"]
        print(f"  {c['strike']}{c['type']}: ${price:.2f} | تنبيه عند ${state[key]['next_alert']:.2f}")
        if price >= state[key]["next_alert"]:
            state[key]["count"] += 1
            steps = int((price - entry) / step)
            state[key]["next_alert"] = entry + (steps + 1) * step
            buf = draw_card(c, opt, spx, state[key]["count"])
            caption = f"🔔 تحديث #{state[key]['count']} | SPX {c['strike']}{c['type']}\n💰 ${price:.2f} (+${price-entry:.2f})\n⏭ التنبيه القادم: ${state[key]['next_alert']:.2f}"
            send_photo(buf, caption)
        time.sleep(0.5)

if __name__ == "__main__":
    print("🤖 البوت v2 يعمل!")
    send_msg("🤖 البوت v2 شغال — يقرأ العقود من لوحة التحكم!")
    check()
    schedule.every(1).minutes.do(check)
    while True:
        schedule.run_pending(); time.sleep(30)
