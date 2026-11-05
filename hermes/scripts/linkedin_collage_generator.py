#!/usr/bin/env python3
"""
linkedin_collage_generator.py — Pure Photo, Document & AI Visual Engine for Arush Sengar.
RULES:
  1. DO NOT DRAW ANY SYNTHETIC TEXT, HEADERS, OR OVERLAYS.
  2. For uploaded assignment screenshots: pure cropping and tiling.
  3. If 1 image: center it cleanly in the middle of the canvas.
  4. If multiple images: tile seamlessly (3 images = hero top + 2 bottom; 4+ = 2x2 grid).
  5. If NO images uploaded: automatically generate a stunning 1200x1200 3D cyber visual
     via OmniRoute (antigravity/gemini-3.1-flash-image) with Pollinations FLUX fallback.
     NO text written on the AI image. Pure, cinematic visual art.
"""

import os
import sys
# Strip stale python3.14 paths
sys.path = [p for p in sys.path if "python3.14" not in p]

import argparse
import base64
import json
import urllib.parse
import urllib.request
from io import BytesIO
from PIL import Image

W, H = 1200, 1200
GAP = 8
BG_COLOR = (15, 20, 30)

OMNIROUTE_URL = os.environ.get("OMNIROUTE_URL", "http://localhost:20128/v1")
OMNIROUTE_KEY = os.environ.get("HERMES_CUSTOM_LOCALHOST_20128_API_KEY", "sk-971230e546e14a3e-23822a-06e1aa8d")

def crop_to_fit(im, target_w, target_h):
    """Scales to fill target_w x target_h and center-crops."""
    rw, rh = im.size
    scale = max(target_w / rw, target_h / rh)
    nw, nh = int(rw * scale), int(rh * scale)
    res = im.resize((nw, nh), Image.LANCZOS)
    cx = (nw - target_w) // 2
    cy = (nh - target_h) // 2
    return res.crop((cx, cy, cx + target_w, cy + target_h))

def center_fit(im, max_w, max_h):
    """Fits cleanly inside max_w x max_h preserving aspect ratio."""
    rw, rh = im.size
    scale = min(max_w / rw, max_h / rh)
    nw, nh = int(rw * scale), int(rh * scale)
    return im.resize((nw, nh), Image.LANCZOS)

def make_pure_collage(images, out_path):
    """Assembles pure photo collage with NO text overlays whatsoever."""
    canvas = Image.new("RGB", (W, H), BG_COLOR)
    n = len(images)
    
    if n == 0:
        canvas.save(out_path, quality=95)
        return out_path
        
    if n == 1:
        im = Image.open(images[0]).convert("RGB")
        res = center_fit(im, W - 40, H - 40)
        x = (W - res.width) // 2
        y = (H - res.height) // 2
        canvas.paste(res, (x, y))
        
    elif n == 2:
        im1 = Image.open(images[0]).convert("RGB")
        im2 = Image.open(images[1]).convert("RGB")
        pw = W
        ph = (H - GAP) // 2
        canvas.paste(crop_to_fit(im1, pw, ph), (0, 0))
        canvas.paste(crop_to_fit(im2, pw, ph), (0, ph + GAP))
        
    elif n == 3:
        top_h = int(H * 0.52)
        bot_h = H - top_h - GAP
        bot_w = (W - GAP) // 2
        
        im_top = Image.open(images[1] if len(images) > 1 else images[0]).convert("RGB")
        im_b1 = Image.open(images[0]).convert("RGB")
        im_b2 = Image.open(images[2]).convert("RGB")
        
        canvas.paste(crop_to_fit(im_top, W, top_h), (0, 0))
        canvas.paste(crop_to_fit(im_b1, bot_w, bot_h), (0, top_h + GAP))
        canvas.paste(crop_to_fit(im_b2, bot_w, bot_h), (bot_w + GAP, top_h + GAP))
        
    elif n >= 4:
        pw = (W - GAP) // 2
        ph = (H - GAP) // 2
        positions = [(0, 0), (pw + GAP, 0), (0, ph + GAP), (pw + GAP, ph + GAP)]
        for i in range(4):
            im = Image.open(images[i]).convert("RGB")
            canvas.paste(crop_to_fit(im, pw, ph), positions[i])
            
    canvas.save(out_path, quality=95)
    print(f"Generated pure collage: {out_path} ({n} images, NO text overlays)")
    return out_path

def generate_ai_concept_image(topic: str, custom_prompt: str = "", out_path: str = ""):
    """
    Generates high-impact AI concept visual via OmniRoute with Pollinations FLUX fallback.
    NO text overlays or headers are drawn — clean 1200x1200 visual art.
    """
    prompt = custom_prompt if custom_prompt else (
        f"cinematic 3D render of {topic}, futuristic cybersecurity operations room, "
        "glowing neon cyan and violet holographic data visualizations, 8k resolution, ultra-detailed, Unreal Engine 5 aesthetic, no text"
    )
    print(f"Generating AI visual for: {topic}...")
    
    raw_img_bytes = None
    
    # 1. OmniRoute AI Image Generation
    omni_models = ["antigravity/gemini-3.1-flash-image", "gemini/gemini-2.5-flash-image"]
    for m in omni_models:
        try:
            print(f"  Trying OmniRoute model: {m}...")
            url = f"{OMNIROUTE_URL}/images/generations"
            payload = {"prompt": prompt, "model": m, "n": 1, "size": "1024x1024"}
            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={
                "Authorization": f"Bearer {OMNIROUTE_KEY}",
                "Content-Type": "application/json"
            })
            with urllib.request.urlopen(req, timeout=25) as resp:
                res = json.loads(resp.read().decode())
                b64_str = res['data'][0]['b64_json']
                raw_img_bytes = base64.b64decode(b64_str)
                print(f"  OmniRoute ({m}) generated {len(raw_img_bytes)} bytes successfully!")
                break
        except Exception as e:
            print(f"  OmniRoute ({m}) failed: {e}")
            
    # 2. Pollinations FLUX fallback
    if not raw_img_bytes:
        try:
            print("  Falling back to Pollinations.ai (Flux engine)...")
            enc = urllib.parse.quote(prompt)
            poll_url = f"https://image.pollinations.ai/prompt/{enc}?width=1200&height=1200&model=flux&nologo=true"
            req = urllib.request.Request(poll_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = resp.read()
                if len(data) > 10000:
                    raw_img_bytes = data
                    print(f"  Pollinations.ai generated {len(data)} bytes successfully!")
        except Exception as e:
            print(f"  Pollinations.ai failed: {e}")
            
    # 3. Save as clean 1200x1200 image with ZERO text overlays
    if raw_img_bytes:
        im = Image.open(BytesIO(raw_img_bytes)).convert("RGB")
        res = im.resize((W, H), Image.LANCZOS)
        res.save(out_path, quality=95)
        print(f"Saved pure AI Concept Visual to {out_path} ({W}x{H}) — NO text overlays")
        return out_path
    else:
        # Ultimate fallback: clean dark canvas
        canvas = Image.new("RGB", (W, H), BG_COLOR)
        canvas.save(out_path, quality=95)
        return out_path

def render_collage(topic_data: dict, out_path: str):
    """
    Router:
    - If user uploaded photos/screenshots exist: make pure photo collage.
    - If NO images exist: automatically generate 3D cyber visual via OmniRoute/Pollinations.
    - STRICTLY NO TEXT OR SYNTHETIC HEADERS DRAWN IN BOTH CASES.
    """
    images = topic_data.get("images", [])
    if images:
        return make_pure_collage(images, out_path)
    
    topic = topic_data.get("topic", "Cyber Security Engineering")
    custom_prompt = topic_data.get("image_prompt", "")
    return generate_ai_concept_image(topic, custom_prompt=custom_prompt, out_path=out_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visual generator")
    parser.add_argument("--out", default="/home/arush/test_out.png", help="Output path")
    parser.add_argument("--mode", default="pure", choices=["pure", "ai"])
    parser.add_argument("--topic", default="Autonomous AI Homelab on Raspberry Pi 4")
    args = parser.parse_args()
    
    if args.mode == "ai":
        generate_ai_concept_image(args.topic, out_path=args.out)
    else:
        sample_imgs = [
            "/home/arush/assignment_media/Global_Internship_ArushSengar_2026_Assignment7/image1.png",
            "/home/arush/assignment_media/Global_Internship_ArushSengar_2026_Assignment7/image2.png",
            "/home/arush/assignment_media/Global_Internship_ArushSengar_2026_Assignment7/image3.png",
        ]
        make_pure_collage(sample_imgs, args.out)
