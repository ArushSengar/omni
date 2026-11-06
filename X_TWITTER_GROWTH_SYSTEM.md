# 🚀 100% FREE & UNPAID X (Twitter) Autonomous Engine

> **Zero Official API Cost ($0.00 forever)**  
> **Zero Monthly Developer Fees**  
> **100% Self-Hosted on Raspberry Pi 4**

---

## 1. Why Paid APIs Are NOT Needed

Twitter/X official developer tier charges **$100 to $200 per month** just for basic API bot posting.

Humne is poore cost ko eliminate karne ke liye **Headless Playwright Browser Engine (`x_autopost.py`)** implement kar diya hai — **the exact same architecture you already use for LinkedIn (`linkedin_autopost.py`)**:

1. **Self-Hosted Chromium on Pi**: Raspberry Pi ke andar installed Chromium browser headless mode mein chalta hai.
2. **Persistent Cookie Session (`~/.twitter-profile`)**: Aapke account ke session cookies use karke direct web interface se post karta hai.
3. **Dual Formats Supported**:
   - Single Punchy Tweet (<280 chars)
   - Viral 3-Tweet Mini-Thread (<280 chars each, auto-chained with '+' button)
   - Branded 1200x1200 Proof-of-Work Images & Pure Assignment Collages

---

## 2. ⚡ 1-Minute Free Setup (One-Time Only)

Aapko bas ek baar apne browser ke 2 cookies Pi par save karne hain (yeh cookies mahino tak valid rehte hain):

### Step A: Apne Laptop Browser Se 2 Cookies Copy Karein
1. Laptop par Chrome/Edge/Brave mein `https://x.com` kholein (jahan aap logged in hain).
2. Keyboard par **`F12`** press karein (Developer Tools khulega).
3. Upar **`Application`** tab par click karein (agar na dikhe to `>>` arrow par click karein).
4. Left sidebar mein **`Storage` $\to$ `Cookies` $\to$ `https://x.com`** par click karein.
5. List mein se yeh do cookies ki **Value** copy karein:
   - **`auth_token`** *(e.g. `3a4f89b...`)*
   - **`ct0`** *(e.g. `c9f280a...`)*

### Step B: Pi Terminal Par Run Karein
Pi terminal (`arush@arush:~ $`) par yeh command paste karein:

```bash
python3 ~/x_setup_cookies.py --auth-token "PASTE_YOUR_AUTH_TOKEN_HERE" --ct0 "PASTE_YOUR_CT0_HERE"
```

*(Alternative: Agar aap "Cookie-Editor" extension use karte hain, to Export $\to$ JSON karke `python3 ~/x_setup_cookies.py --file cookies.json` run kar sakte hain).*

---

## 3. 🎯 Execution Commands (100% Free)

Cookies save hone ke baad aap bina kisi API fee ke commands run kar sakte hain:

```bash
# 1. Full auto single tweet (dry-run preview)
python3 ~/x_daily_post.py --dry-run

# 2. Viral 3-tweet thread (dry-run preview)
python3 ~/x_daily_post.py --dry-run --thread

# 3. Live publish 100% Free to X (Single Tweet)
python3 ~/x_daily_post.py

# 4. Live publish 100% Free to X (3-Tweet Thread)
python3 ~/x_daily_post.py --thread

# 5. Direct standalone browser test
python3 ~/x_autopost.py "Testing my 100% free autonomous Pi bot! #BuildInPublic"
```

---

## 4. 📂 System Files on Pi

| File | Path | Function |
| :--- | :--- | :--- |
| **Setup Script** | `~/x_setup_cookies.py` | One-time free cookie injector. |
| **Free Browser Poster** | `~/x_autopost.py` | Playwright Chromium automation (types text, adds media, clicks post). |
| **Master Orchestrator** | `~/x_daily_post.py` | Detects assignment/topic $\to$ writes copy $\to$ renders visual $\to$ triggers `x_autopost.py`. |
| **Profile & Screenshots** | `~/.twitter-profile/shots/` | Stores post verification screenshots (`01_home_feed.png`, `04_image_attached.png`, `06_post_published.png`). |
