"""
Tạo file MP3 giọng đọc cho Cẩm nang iPay bằng FPT.AI Text-to-Speech (tùy chọn).
Khi có thư mục audio/ trên GitHub, mọi điện thoại nghe cùng một giọng đọc
thay cho giọng có sẵn của máy.

Cách chạy:
    pip install requests
    set FPT_API_KEY=khoa_cua_anh      (Windows)   |   export FPT_API_KEY=...  (macOS/Linux)
    python tao-giong-doc-fpt.py --voice banmai --speed -1

Kết quả: thư mục ../audio/ gồm 51 file .mp3 và manifest.json -> upload cả thư mục lên GitHub.
Lưu ý: KHÔNG đưa API key lên GitHub; kiểm tra điều khoản dùng thương mại của gói FPT.AI.
Giọng FPT.AI: banmai, thuminh, myan (nữ Bắc/Trung) · lannhi, linhsan (nữ Nam) · leminh, giahuy, minhquang (nam)
"""
import argparse, json, os, re, sys, time
from pathlib import Path
import requests

API = "https://api.fpt.ai/hmi/tts/v5"
# Cách đọc từ viết tắt (giống trong index.html)
LEX = [(r"R-ATM", "e rờ a tê em"), (r"\bATM\b", "a tê em"), (r"Soft OTP", "sóp ô tê pê"), (r"\biPay\b", "ai pay"), (r"VNeID", "vê nê ai đi"), (r"\bOTP\b", "ô tê pê"),
       (r"\bNFC\b", "en ép xi"), (r"\bQR\b", "kiu a"), (r"\bCCCD\b", "căn cước")]

def spoken(t):
    for a, b in LEX:
        t = re.sub(a, b, t)
    return t

def tts(text, key, voice, speed):
    r = requests.post(API, data=text.encode("utf-8"),
                      headers={"api-key": key, "voice": voice, "speed": str(speed)}, timeout=30)
    r.raise_for_status()
    j = r.json()
    if j.get("error", 1) != 0 or not j.get("async"):
        raise RuntimeError(j.get("message", "FPT.AI trả về lỗi"))
    url = j["async"]
    for _ in range(30):                      # file MP3 được tạo sau vài giây
        time.sleep(2)
        f = requests.get(url, timeout=30)
        if f.status_code == 200 and f.content[:3] in (b"ID3", b"\xff\xfb", b"\xff\xf3"):
            return f.content
    raise TimeoutError("Hết thời gian chờ file MP3: " + url)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="banmai")
    ap.add_argument("--speed", type=int, default=-1, help="-3 (chậm) đến 3 (nhanh)")
    ap.add_argument("--out", default=str(Path(__file__).parent.parent / "audio"))
    a = ap.parse_args()
    key = os.environ.get("FPT_API_KEY")
    if not key:
        sys.exit("Chưa có biến môi trường FPT_API_KEY")
    rows = json.load(open(Path(__file__).parent / "loi-doc.json", encoding="utf-8"))
    out = Path(a.out); out.mkdir(exist_ok=True)
    done = []
    for i, r in enumerate(rows, 1):
        dst = out / r["file"]
        if not dst.exists():
            print(f"[{i}/{len(rows)}] {r['file']}")
            dst.write_bytes(tts(spoken(r["text"]), key, a.voice, a.speed))
        done.append(r["file"])
    json.dump(done, open(out / "manifest.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Xong: {len(done)} file trong {out}")

if __name__ == "__main__":
    main()
