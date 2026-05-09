import cv2
import numpy as np
from typing import List, Tuple

from models import (
    DetectedElement, ShapeType, ColorGroup, COLOR_GROUP_TO_CHANNEL,
)


def _classify_color(h: float, s: float, v: float) -> ColorGroup:
    """h: 0-180 (OpenCV), s: 0-255, v: 0-255"""
    if s < 40:
        if v < 50:
            return ColorGroup.BLACK
        elif v > 200:
            return ColorGroup.WHITE
        else:
            return ColorGroup.GRAY

    if h < 10 or h >= 170:
        return ColorGroup.RED
    elif h < 25:
        return ColorGroup.ORANGE
    elif h < 35:
        return ColorGroup.YELLOW
    elif h < 85:
        return ColorGroup.GREEN
    elif h < 100:
        return ColorGroup.CYAN
    elif h < 130:
        return ColorGroup.BLUE
    elif h < 160:
        return ColorGroup.PURPLE
    else:
        return ColorGroup.RED


def _classify_shape(contour: np.ndarray) -> ShapeType:
    area = cv2.contourArea(contour)
    peri = cv2.arcLength(contour, True)
    if peri == 0:
        return ShapeType.OTHER

    circularity = 4 * np.pi * area / (peri * peri)
    approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
    vertices = len(approx)

    if circularity > 0.72:
        return ShapeType.CIRCLE
    elif vertices == 3:
        return ShapeType.TRIANGLE
    elif 4 <= vertices <= 6:
        return ShapeType.RECTANGLE
    else:
        return ShapeType.OTHER


def analyze_image(
    image_path: str,
    num_clusters: int = 6,
    sensitivity: int = 50,
) -> Tuple[List[DetectedElement], np.ndarray]:
    """
    Detect visual elements in an image via K-means color quantization and
    contour analysis.

    Returns (elements sorted by X position, original BGR image).
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot load image: {image_path}")

    # Limit size for performance
    max_dim = 1200
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        h, w = img.shape[:2]

    img_area = h * w
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # K-means color quantization
    pixels = img.reshape(-1, 3).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1.0)
    _, labels, centers = cv2.kmeans(
        pixels, num_clusters, None, criteria, 10, cv2.KMEANS_PP_CENTERS
    )
    centers = centers.astype(np.uint8)
    labels = labels.reshape(h, w)

    # min area: scales with sensitivity (10→0.5%, 50→0.15%, 90→0.05%)
    min_area_frac = 0.005 - (sensitivity / 90) * 0.0045
    min_area = img_area * min_area_frac

    morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    elements: List[DetectedElement] = []

    for cluster_idx in range(num_clusters):
        mask = (labels == cluster_idx).astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, morph_kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, morph_kernel)

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            x, y, cw, ch = cv2.boundingRect(contour)

            region_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.drawContours(region_mask, [contour], -1, 255, -1)

            mean_hsv = cv2.mean(hsv_img, mask=region_mask)[:3]
            mean_bgr = cv2.mean(img, mask=region_mask)[:3]

            region_pixels = gray_img[region_mask == 255]
            texture_var = float(np.std(region_pixels)) if len(region_pixels) > 0 else 0.0

            shape = _classify_shape(contour)
            color_group = _classify_color(mean_hsv[0], mean_hsv[1], mean_hsv[2])

            cx = (x + cw / 2) / w
            cy = (y + ch / 2) / h
            size_norm = area / img_area

            color_rgb = (int(mean_bgr[2]), int(mean_bgr[1]), int(mean_bgr[0]))
            color_hsv = (float(mean_hsv[0]), float(mean_hsv[1]), float(mean_hsv[2]))

            elements.append(DetectedElement(
                shape=shape,
                color_group=color_group,
                color_rgb=color_rgb,
                color_hsv=color_hsv,
                position=(cx, cy),
                size=size_norm,
                texture_variance=texture_var,
                bbox=(x, y, cw, ch),
                contour=contour,
            ))

    elements.sort(key=lambda e: e.position[0])
    return elements, img
