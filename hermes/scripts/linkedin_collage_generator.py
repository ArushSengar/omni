#!/usr/bin/env python3
"""
linkedin_collage_generator.py — Pure Photo & Document Collage Engine for Arush Sengar.
STRICT USER RULES:
  1. DO NOT DRAW ANY SYNTHETIC TEXT, HEADERS, OR OVERLAYS.
  2. Purely tile and crop the real photos, documents, and lab evidence uploaded by Arush.
  3. If 1 image: Center it cleanly in the middle of the canvas (no empty sidebars).
  4. If 2 images: 50/50 balanced split.
  5. If 3 images: Top feature hero + 2 bottom side-by-side images.
  6. If 4+ images: 2x2 balanced grid.
"""

import os
import sys
# Strip stale python3.14 paths
sys.path = [p for p in sys.path if "python3.14" not in p]

import argparse
from PIL import Image

W, H = 1200, 1200
GAP = 8
BG_COLOR = (15, 20, 30) # Clean dark background

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
        # Fallback if no images provided
        canvas.save(out_path, quality=95)
        return out_path
        
    if n == 1:
        # Single image: Center cleanly in the middle of the canvas
        im = Image.open(images[0]).convert("RGB")
        res = center_fit(im, W - 40, H - 40)
        x = (W - res.width) // 2
        y = (H - res.height) // 2
        canvas.paste(res, (x, y))
        
    elif n == 2:
        # 2 images: 50/50 top and bottom
        im1 = Image.open(images[0]).convert("RGB")
        im2 = Image.open(images[1]).convert("RGB")
        pw = W
        ph = (H - GAP) // 2
        canvas.paste(crop_to_fit(im1, pw, ph), (0, 0))
        canvas.paste(crop_to_fit(im2, pw, ph), (0, ph + GAP))
        
    elif n == 3:
        # 3 images: Top feature hero + 2 bottom side-by-side
        top_h = int(H * 0.52)
        bot_h = H - top_h - GAP
        bot_w = (W - GAP) // 2
        
        # Pick badge image for top if available, else first image
        im_top = Image.open(images[1] if len(images) > 1 else images[0]).convert("RGB")
        im_b1 = Image.open(images[0]).convert("RGB")
        im_b2 = Image.open(images[2]).convert("RGB")
        
        canvas.paste(crop_to_fit(im_top, W, top_h), (0, 0))
        canvas.paste(crop_to_fit(im_b1, bot_w, bot_h), (0, top_h + GAP))
        canvas.paste(crop_to_fit(im_b2, bot_w, bot_h), (bot_w + GAP, top_h + GAP))
        
    elif n >= 4:
        # 4+ images: 2x2 grid
        pw = (W - GAP) // 2
        ph = (H - GAP) // 2
        positions = [(0, 0), (pw + GAP, 0), (0, ph + GAP), (pw + GAP, ph + GAP)]
        for i in range(4):
            im = Image.open(images[i]).convert("RGB")
            canvas.paste(crop_to_fit(im, pw, ph), positions[i])
            
    canvas.save(out_path, quality=95)
    print(f"Generated pure collage: {out_path} ({n} images, NO text overlays)")
    return out_path

def render_collage(topic_data: dict, out_path: str):
    """Router: uses pure photos from topic_data without any text overlays."""
    images = topic_data.get("images", [])
    if images:
        return make_pure_collage(images, out_path)
    
    # If no images found, create a clean, elegant dark canvas
    canvas = Image.new("RGB", (W, H), BG_COLOR)
    canvas.save(out_path, quality=95)
    return out_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pure collage generator (NO text overlays)")
    parser.add_argument("--out", default="/home/arush/test_pure_out.png", help="Output path")
    args = parser.parse_args()
    
    sample_imgs = [
        "/home/arush/assignment_media/Global_Internship_ArushSengar_2026_Assignment7/image1.png",
        "/home/arush/assignment_media/Global_Internship_ArushSengar_2026_Assignment7/image2.png",
        "/home/arush/assignment_media/Global_Internship_ArushSengar_2026_Assignment7/image3.png",
    ]
    make_pure_collage(sample_imgs, args.out)
