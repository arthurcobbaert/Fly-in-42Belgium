"""Crisp rendering on high-DPI (Retina) screens.

pygame 2's `display.set_mode` never asks SDL for a high-DPI window, so on
a Retina Mac the window gets a 1x framebuffer that macOS stretches to 2x,
which makes every line and letter blurry. On macOS this module opens the
window through pygame's bundled SDL with SDL_WINDOW_ALLOW_HIGHDPI and
shows a full-resolution pygame Surface through an SDL texture. Anywhere
else (or if anything goes wrong) it falls back to a plain pygame window.

Surface sizes are in *pixels*; window sizes and mouse positions reported
by SDL are in *points*. `scale` is pixels per point.
"""
import ctypes
import glob
import os
import sys
import pygame

_ALLOW_HIGHDPI = 0x00002000
_SHOWN = 0x00000004
_RESIZABLE = 0x00000020
_CENTERED = 0x2FFF0000
_RENDERER_ACCELERATED = 0x00000002
_TEXTUREACCESS_STREAMING = 1
_PIXELFORMAT_XRGB8888 = 0x16161804


def _load_sdl() -> ctypes.CDLL | None:
    """The SDL library pygame itself uses (never a second copy)."""
    if sys.platform != "darwin":
        return None
    libs = glob.glob(os.path.join(os.path.dirname(pygame.__file__),
                                  ".dylibs", "libSDL2-2.0*.dylib"))
    if not libs:
        return None
    try:
        sdl = ctypes.CDLL(libs[0])
    except OSError:
        return None
    vp, i, u32 = ctypes.c_void_p, ctypes.c_int, ctypes.c_uint32
    pi = ctypes.POINTER(ctypes.c_int)
    sdl.SDL_CreateWindow.argtypes = [ctypes.c_char_p, i, i, i, i, u32]
    sdl.SDL_CreateWindow.restype = vp
    sdl.SDL_CreateRenderer.argtypes = [vp, i, u32]
    sdl.SDL_CreateRenderer.restype = vp
    sdl.SDL_CreateTexture.argtypes = [vp, u32, i, i, i]
    sdl.SDL_CreateTexture.restype = vp
    sdl.SDL_DestroyTexture.argtypes = [vp]
    sdl.SDL_UpdateTexture.argtypes = [vp, vp, vp, i]
    sdl.SDL_RenderCopy.argtypes = [vp, vp, vp, vp]
    sdl.SDL_RenderPresent.argtypes = [vp]
    sdl.SDL_GetWindowSize.argtypes = [vp, pi, pi]
    sdl.SDL_GetRendererOutputSize.argtypes = [vp, pi, pi]
    sdl.SDL_SetWindowMinimumSize.argtypes = [vp, i, i]
    return sdl


class Display:
    """A resizable window with a pixel-sized drawing surface."""

    def __init__(self, title: str, size: tuple[int, int],
                 min_size: tuple[int, int]) -> None:
        self._sdl = _load_sdl()
        self._win: int | None = None
        self._ren: int | None = None
        self._tex: int | None = None
        self._fallback_size = (0, 0)
        if self._sdl is not None:
            try:
                self._open_native(title, size, min_size)
            except (OSError, ValueError, pygame.error):
                self._sdl = None
        if self._sdl is None:
            pygame.display.set_mode(size, pygame.RESIZABLE)
            pygame.display.set_caption(title)
        self.min_size = min_size
        self.scale = 1.0
        self.surface = pygame.Surface((1, 1))
        self.sync_size()

    # ---------------------------------------------------------- native

    def _open_native(self, title: str, size: tuple[int, int],
                     min_size: tuple[int, int]) -> None:
        assert self._sdl is not None
        win = self._sdl.SDL_CreateWindow(
            title.encode(), _CENTERED, _CENTERED, size[0], size[1],
            _ALLOW_HIGHDPI | _SHOWN | _RESIZABLE,
        )
        if not win:
            raise ValueError("SDL_CreateWindow failed")
        ren = self._sdl.SDL_CreateRenderer(win, -1, _RENDERER_ACCELERATED)
        if not ren:
            raise ValueError("SDL_CreateRenderer failed")
        self._sdl.SDL_SetWindowMinimumSize(win, min_size[0], min_size[1])
        self._win, self._ren = win, ren

    def _native_sizes(self) -> tuple[tuple[int, int], tuple[int, int]]:
        assert self._sdl is not None
        pw, ph, ow, oh = (ctypes.c_int() for _ in range(4))
        self._sdl.SDL_GetWindowSize(self._win, ctypes.byref(pw),
                                    ctypes.byref(ph))
        self._sdl.SDL_GetRendererOutputSize(self._ren, ctypes.byref(ow),
                                            ctypes.byref(oh))
        return (pw.value, ph.value), (ow.value, oh.value)

    # ---------------------------------------------------------- public

    @property
    def size(self) -> tuple[int, int]:
        """Drawing surface size, in pixels."""
        return self.surface.get_size()

    def sync_size(self) -> bool:
        """Match the surface to the window. True if it was (re)built."""
        if self._sdl is None:
            screen = pygame.display.get_surface()
            # pygame may reuse the same Surface object after a resize
            if (screen is self.surface
                    and screen.get_size() == self._fallback_size):
                return False
            self._fallback_size = screen.get_size()
            self.surface, self.scale = screen, 1.0
            return True
        points, pixels = self._native_sizes()
        if pixels == self.surface.get_size() and self._tex:
            return False
        self.scale = pixels[0] / max(1, points[0])
        self.surface = pygame.Surface(pixels, 0, 32)
        if self.surface.get_masks()[:3] != (0xFF0000, 0xFF00, 0xFF):
            self.surface = pygame.Surface(
                pixels, 0, 32, (0xFF0000, 0xFF00, 0xFF, 0))
        if self._tex:
            self._sdl.SDL_DestroyTexture(self._tex)
        self._tex = self._sdl.SDL_CreateTexture(
            self._ren, _PIXELFORMAT_XRGB8888, _TEXTUREACCESS_STREAMING,
            pixels[0], pixels[1],
        )
        return True

    def resized(self, w: int, h: int) -> None:
        """Handle a pygame VIDEORESIZE event (fallback window only)."""
        if self._sdl is None:
            pygame.display.set_mode(
                (max(self.min_size[0], w), max(self.min_size[1], h)),
                pygame.RESIZABLE,
            )

    def to_pixels(self, pos: tuple[int, int]) -> tuple[int, int]:
        """Mouse position (points) -> surface position (pixels)."""
        return (int(pos[0] * self.scale), int(pos[1] * self.scale))

    def present(self) -> None:
        if self._sdl is None:
            pygame.display.flip()
            return
        surf = self.surface
        self._sdl.SDL_UpdateTexture(self._tex, None, surf._pixels_address,
                                    surf.get_pitch())
        self._sdl.SDL_RenderCopy(self._ren, self._tex, None, None)
        self._sdl.SDL_RenderPresent(self._ren)
