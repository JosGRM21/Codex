"""Pruebas para el cálculo de similitud y detección de diapositivas."""

from PIL import Image
from codex.core.vision import compute_image_difference

def test_identical_images_have_zero_difference():
    img1 = Image.new("RGB", (640, 480), color="white")
    img2 = Image.new("RGB", (640, 480), color="white")
    diff = compute_image_difference(img1, img2)
    assert diff == 0.0

def test_different_images_have_high_difference():
    img_white = Image.new("RGB", (640, 480), color="white")
    img_black = Image.new("RGB", (640, 480), color="black")
    diff = compute_image_difference(img_white, img_black)
    assert diff > 0.9

def test_subtle_change_below_major_threshold():
    img1 = Image.new("RGB", (640, 480), color="white")
    img2 = img1.copy()
    # Dibujar un pequeño punto de 5x5 simulando puntero de ratón
    for x in range(5):
        for y in range(5):
            img2.putpixel((100 + x, 100 + y), (0, 0, 0))
    diff = compute_image_difference(img1, img2)
    # Debe ser menor a 0.05 para no considerarse cambio de diapositiva
    assert diff < 0.02
