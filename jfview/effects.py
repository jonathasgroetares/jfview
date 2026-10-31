"""Image effects and filters for JFView."""

import numpy as np
from PIL import Image, ImageFilter, ImageOps


class ImageEffects:
    """Collection of image effects/filters."""

    @staticmethod
    def grayscale(image: Image.Image) -> Image.Image:
        """Convert image to grayscale."""
        return ImageOps.grayscale(image).convert("RGB")

    @staticmethod
    def negative(image: Image.Image) -> Image.Image:
        """Invert image colors (negative)."""
        if image.mode == "RGBA":
            r, g, b, a = image.split()
            rgb = Image.merge("RGB", (r, g, b))
            rgb = ImageOps.invert(rgb)
            r2, g2, b2 = rgb.split()
            return Image.merge("RGBA", (r2, g2, b2, a))
        return ImageOps.invert(image.convert("RGB"))

    @staticmethod
    def edge_detection(image: Image.Image) -> Image.Image:
        """Detect edges in the image (border/contour detection)."""
        gray = ImageOps.grayscale(image)
        edges = gray.filter(ImageFilter.FIND_EDGES)
        # Invert so edges are black on white background
        edges = ImageOps.invert(edges)
        return edges.convert("RGB")

    @staticmethod
    def nanquim(image: Image.Image) -> Image.Image:
        """Apply nanquim (India ink) effect.

        Creates a high-contrast black and white ink drawing effect
        by combining edge detection with thresholding.
        """
        gray = ImageOps.grayscale(image)

        # Edge detection for line work
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edges_np = np.array(edges, dtype=np.float32)

        # Enhance edges
        edges_enhanced = np.clip(edges_np * 2.5, 0, 255)

        # Apply threshold to create clean ink lines
        threshold = 30
        ink = np.where(edges_enhanced > threshold, 0, 255).astype(np.uint8)

        # Also add dark areas from original for filled ink regions
        gray_np = np.array(gray, dtype=np.float32)
        dark_mask = (gray_np < 80).astype(np.float32)

        # Combine edges and dark areas
        result = np.minimum(ink.astype(np.float32), (1 - dark_mask) * 255)
        result = np.clip(result, 0, 255).astype(np.uint8)

        return Image.fromarray(result).convert("RGB")

    @staticmethod
    def sepia(image: Image.Image) -> Image.Image:
        """Apply sepia tone effect."""
        gray = ImageOps.grayscale(image)
        np_img = np.array(gray, dtype=np.float32)

        # Sepia toning
        r = np.clip(np_img * 1.2 + 40, 0, 255).astype(np.uint8)
        g = np.clip(np_img * 1.0 + 20, 0, 255).astype(np.uint8)
        b = np.clip(np_img * 0.8, 0, 255).astype(np.uint8)

        return Image.merge("RGB", (
            Image.fromarray(r),
            Image.fromarray(g),
            Image.fromarray(b),
        ))

    @staticmethod
    def emboss(image: Image.Image) -> Image.Image:
        """Apply emboss effect."""
        return image.convert("RGB").filter(ImageFilter.EMBOSS)

    @staticmethod
    def sharpen(image: Image.Image) -> Image.Image:
        """Sharpen the image."""
        return image.convert("RGB").filter(ImageFilter.SHARPEN)

    @staticmethod
    def blur(image: Image.Image) -> Image.Image:
        """Apply Gaussian blur."""
        return image.convert("RGB").filter(ImageFilter.GaussianBlur(radius=2))

    @staticmethod
    def posterize(image: Image.Image, bits: int = 3) -> Image.Image:
        """Reduce color levels (posterize)."""
        return ImageOps.posterize(image.convert("RGB"), bits)

    @staticmethod
    def solarize(image: Image.Image, threshold: int = 128) -> Image.Image:
        """Apply solarize effect."""
        return ImageOps.solarize(image.convert("RGB"), threshold)

    @staticmethod
    def contour(image: Image.Image) -> Image.Image:
        """Apply contour filter."""
        return image.convert("RGB").filter(ImageFilter.CONTOUR)

    @staticmethod
    def detail(image: Image.Image) -> Image.Image:
        """Enhance detail."""
        return image.convert("RGB").filter(ImageFilter.DETAIL)

    @staticmethod
    def smooth(image: Image.Image) -> Image.Image:
        """Apply smoothing filter."""
        return image.convert("RGB").filter(ImageFilter.SMOOTH_MORE)

    @staticmethod
    def brightness(image: Image.Image, factor: float = 1.3) -> Image.Image:
        """Adjust brightness."""
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Brightness(image.convert("RGB"))
        return enhancer.enhance(factor)

    @staticmethod
    def contrast(image: Image.Image, factor: float = 1.5) -> Image.Image:
        """Adjust contrast."""
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image.convert("RGB"))
        return enhancer.enhance(factor)

    @staticmethod
    def auto_contrast(image: Image.Image) -> Image.Image:
        """Apply auto contrast."""
        return ImageOps.autocontrast(image.convert("RGB"))

    @staticmethod
    def equalize(image: Image.Image) -> Image.Image:
        """Equalize histogram."""
        return ImageOps.equalize(image.convert("RGB"))
