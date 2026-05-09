import cv2
import numpy as np
from typing import List

from models import DetectedElement, CHANNEL_COLORS_RGB, CHANNEL_NAMES


def _text_color(r: int, g: int, b: int) -> tuple:
    brightness = 0.299 * r + 0.587 * g + 0.114 * b
    return (0, 0, 0) if brightness > 140 else (255, 255, 255)


def annotate_image(img: np.ndarray, elements: List[DetectedElement]) -> np.ndarray:
    out = img.copy()
    h, w = out.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Pass 1: draw contour outlines (white halo then channel color)
    for el in elements:
        ch = el.midi_channel
        r, g, b = CHANNEL_COLORS_RGB.get(ch, (200, 200, 200))
        bgr = (b, g, r)
        cv2.drawContours(out, [el.contour], -1, (255, 255, 255), 4)
        cv2.drawContours(out, [el.contour], -1, bgr, 2)

    # Pass 2: labels
    for el in elements:
        ch = el.midi_channel
        r, g, b = CHANNEL_COLORS_RGB.get(ch, (200, 200, 200))
        bgr = (b, g, r)
        txt_bgr = _text_color(r, g, b)

        bx, by, bw, bh = el.bbox
        line1 = f"Ch{ch+1} {el.note_name}"
        line2 = el.shape.value[:4].title()

        fs = 0.42
        (tw1, th1), _ = cv2.getTextSize(line1, font, fs, 1)
        (tw2, th2), _ = cv2.getTextSize(line2, font, 0.34, 1)
        box_w = max(tw1, tw2) + 8
        box_h = th1 + th2 + 10

        lx = max(0, bx)
        ly = by - 6
        if ly - box_h < 0:
            ly = by + bh + box_h + 4
        ly = min(ly, h - 4)

        # Filled label background
        x1 = max(0, lx - 2)
        y1 = max(0, ly - box_h)
        x2 = min(w - 1, lx + box_w)
        y2 = min(h - 1, ly + 4)
        cv2.rectangle(out, (x1, y1), (x2, y2), bgr, -1)

        cv2.putText(out, line1, (lx + 2, ly - th2 - 4),
                    font, fs, txt_bgr, 1, cv2.LINE_AA)
        cv2.putText(out, line2, (lx + 2, ly - 2),
                    font, 0.34, txt_bgr, 1, cv2.LINE_AA)

    _draw_legend(out, elements)
    return out


def _draw_legend(img: np.ndarray, elements: List[DetectedElement]) -> None:
    if not elements:
        return

    img_h, img_w = img.shape[:2]
    channels = sorted(set(el.midi_channel for el in elements))
    font = cv2.FONT_HERSHEY_SIMPLEX
    line_h = 20
    pad = 8
    legend_w = 162
    legend_h = len(channels) * line_h + pad * 2 + 18

    lx = img_w - legend_w - 10
    ly = 10
    x2, y2 = lx + legend_w, ly + legend_h

    overlay = img.copy()
    cv2.rectangle(overlay, (lx, ly), (x2, y2), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.78, img, 0.22, 0, img)

    cv2.putText(img, "MIDI Channels", (lx + pad, ly + pad + 11),
                font, 0.40, (200, 200, 200), 1, cv2.LINE_AA)

    for i, ch in enumerate(channels):
        r, g, b = CHANNEL_COLORS_RGB.get(ch, (200, 200, 200))
        bgr = (b, g, r)
        ty = ly + pad + 18 + i * line_h + 12
        cv2.rectangle(img, (lx + pad, ty - 10), (lx + pad + 13, ty + 2), bgr, -1)
        label = f"Ch{ch+1}: {CHANNEL_NAMES.get(ch, '')}"
        cv2.putText(img, label, (lx + pad + 17, ty),
                    font, 0.38, bgr, 1, cv2.LINE_AA)
