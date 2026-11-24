import pygame

SCREEN_SIZE = (960, 660)
HUD_RECT = pygame.Rect(20, 16, 920, 62)
MAP_RECT = pygame.Rect(20, 90, 920, 474)
STATUS_RECT = pygame.Rect(20, 576, 500, 40)
HINT_BUTTON = pygame.Rect(534, 576, 118, 40)
RESET_BUTTON = pygame.Rect(662, 576, 118, 40)
SUBMIT_BUTTON = pygame.Rect(790, 576, 150, 40)
CAPTION_POS = (22, 630)

CARD_RECT = pygame.Rect(260, 115, 440, 430)
CARD_LEFT_BUTTON = pygame.Rect(288, 469, 180, 44)
CARD_RIGHT_BUTTON = pygame.Rect(492, 469, 180, 44)

SMALL_CARD_RECT = pygame.Rect(300, 200, 360, 250)
SMALL_LEFT_BUTTON = pygame.Rect(324, 378, 150, 44)
SMALL_RIGHT_BUTTON = pygame.Rect(486, 378, 150, 44)
SMALL_WIDE_BUTTON = pygame.Rect(370, 378, 220, 44)


def menu_cards(count, cols=3):
    w, h, gap = 260, 112, 24
    x0 = (SCREEN_SIZE[0] - (cols * w + (cols - 1) * gap)) // 2
    y0 = 292
    return [
        pygame.Rect(x0 + (i % cols) * (w + gap), y0 + (i // cols) * (h + gap), w, h)
        for i in range(count)
    ]
