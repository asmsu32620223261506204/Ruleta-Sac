
# -*- coding: utf-8 -*-
# Roulette Wheel Game (European) with visual wheel and basic betting.
# Requirements: pygame
# Run:
#   pip install pygame
#   python main.py
#
# Controls:
#   SPACE  -> Spin
#   C      -> Clear bet slip
#   UP/DOWN -> Change chip amount
#   1..6   -> Add bet with current chip:
#             1 RED, 2 BLACK, 3 EVEN, 4 ODD, 5 LOW(1-18), 6 HIGH(19-36)
#   S      -> Enable straight-number selection mode
#   LEFT/RIGHT -> Change straight number when S mode active
#   ENTER  -> Add straight-number bet with current chip
#
# Notes: This is a simplified casino model for education.
# Payouts: even-money 1:1, straight 35:1. Zero loses even-money bets.
#
from __future__ import annotations
import math, sys, random
from typing import List, Tuple, Dict, Optional
import pygame

# -------------------- Wheel Definition (European) --------------------
# Number order clockwise when viewed from above; we'll consider angle 0 at top and increase clockwise.
WHEEL_ORDER = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23,
               10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]

RED_NUMBERS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK_NUMBERS = set(range(1,37)) - RED_NUMBERS

# -------------------- Game Config --------------------
WIDTH, HEIGHT = 1100, 900
CENTER = (450, 450)    # wheel center (leave right panel for UI)
R_OUTER = 360
R_INNER = 260
R_TEXT  = 400  # radius for placing number labels
BALL_RADIUS = 10

FPS = 60

BANKROLL_START = 1000

POCKETS = len(WHEEL_ORDER)
ANGLE_PER = 2*math.pi / POCKETS

# Colors
WHITE=(255,255,255); BLACK=(0,0,0); RED=(220,0,0); GREEN=(0,140,0); GRAY=(60,60,60); LIGHT=(220,220,220)
BG=(22,26,33); PANEL=(30,34,41); YELLOW=(245,205,66)

# -------------------- Helpers --------------------
def pocket_color(n:int):
    if n == 0: return GREEN
    return RED if n in RED_NUMBERS else BLACK

def even_money_win(n:int, bet:str)->bool:
    if n==0: return False
    if bet=="RED": return n in RED_NUMBERS
    if bet=="BLACK": return n in BLACK_NUMBERS
    if bet=="EVEN": return (n%2)==0
    if bet=="ODD": return (n%2)==1
    if bet=="LOW": return 1<=n<=18
    if bet=="HIGH": return 19<=n<=36
    return False

def round_points(cx, cy, radius, a0, a1, steps=10):
    # Points along arc from angle a0 to a1 (clockwise positive)
    pts = []
    for i in range(steps+1):
        t = a0 + (a1-a0)*i/steps
        x = cx + radius*math.sin(t)
        y = cy - radius*math.cos(t)
        pts.append((x,y))
    return pts

def wedge_polygon(cx, cy, r_outer, r_inner, a0, a1):
    outer = round_points(cx, cy, r_outer, a0, a1, steps=6)
    inner = round_points(cx, cy, r_inner, a1, a0, steps=6)
    return outer + inner

def angle_wrap(a):
    while a<0: a+=2*math.pi
    while a>=2*math.pi: a-=2*math.pi
    return a

# -------------------- Pygame Setup --------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("European Roulette — RL-ready Visual Wheel")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 20)
font_small = pygame.font.SysFont("arial", 16)
font_big = pygame.font.SysFont("arial", 28, bold=True)

# -------------------- Game State --------------------
bankroll = BANKROLL_START
chip_amount = 10
bet_slip : Dict[Tuple[str, Optional[int]], int] = {}  # key: ("RED",None) or ("STRAIGHT",17) -> amount
select_straight_mode = False
straight_number = 17

spinning = False
result_number = None
result_timer = 0

# physics
wheel_angle = 0.0
wheel_av = 0.0
ball_angle = 0.0
ball_av = 0.0

def add_bet(key:Tuple[str, Optional[int]], amount:int):
    if amount<=0: return
    bet_slip[key] = bet_slip.get(key, 0) + amount

def total_bet_amount():
    return sum(bet_slip.values())

def can_spin():
    return (not spinning) and total_bet_amount()>0 and bankroll>=total_bet_amount()

def launch_spin():
    global spinning, result_number, result_timer, wheel_av, ball_av, ball_angle, wheel_angle, bankroll
    # Deduct stake from bankroll
    stake = total_bet_amount()
    bankroll -= stake
    # Randomize starting angles and angular velocities
    wheel_angle = random.random()*2*math.pi
    ball_angle = random.random()*2*math.pi
    wheel_av  = (random.uniform(0.9, 1.2)) * (2*math.pi/8) * (-1)   # slow clockwise
    ball_av   = (random.uniform(5.0, 6.5)) * (2*math.pi/8)           # fast counterclockwise
    spinning = True
    result_number = None
    result_timer = 0

def settle(n:int):
    global bankroll
    # Payouts: even-money 1:1, straight 35:1
    payout = 0
    for (kind,arg), amt in bet_slip.items():
        if kind in ("RED","BLACK","EVEN","ODD","LOW","HIGH"):
            if even_money_win(n, kind):
                payout += amt*2  # return includes stake of that bet
        elif kind=="STRAIGHT":
            if arg == n:
                payout += amt*36
    bankroll += payout

def compute_winning_number(wheel_angle, ball_angle):
    # Determine which pocket the ball points to in wheel coordinates
    rel = angle_wrap(ball_angle - wheel_angle)  # angle of ball in wheel frame
    # We define pocket 0 spanning [0, ANGLE_PER), then next clockwise.
    idx = int((rel) // ANGLE_PER) % POCKETS
    return WHEEL_ORDER[idx]

def update_physics(dt):
    global wheel_angle, ball_angle, wheel_av, ball_av, spinning, result_number, result_timer, bet_slip

    if not spinning:
        return

    # Friction (simple linear decel)
    wheel_av *= 0.999
    ball_av  *= 0.9975

    # Minimal angular velocities
    if abs(wheel_av) < 0.01: wheel_av = 0.01 if wheel_av>=0 else -0.01
    if abs(ball_av)  < 0.2:  ball_av  = 0.2 if ball_av>=0 else -0.2

    wheel_angle = angle_wrap(wheel_angle + wheel_av*dt)
    ball_angle  = angle_wrap(ball_angle  + ball_av*dt)

    # When ball is slow enough, "drop" to final pocket with damping and finish
    if abs(ball_av) < 0.45:
        # Snap after a brief delay
        result_timer += dt
        if result_timer > 1.2:
            n = compute_winning_number(wheel_angle, ball_angle)
            result_number = n
            settle(n)
            spinning = False
            bet_slip.clear()

def draw_wheel(surface):
    # Draw table background
    surface.fill(BG)

    cx, cy = CENTER
    # Outer ring background
    pygame.draw.circle(surface, LIGHT, (int(cx), int(cy)), R_TEXT, 0)
    pygame.draw.circle(surface, BG, (int(cx), int(cy)), R_TEXT-12, 0)

    # Draw wedges
    a = 0.0
    for i, num in enumerate(WHEEL_ORDER):
        a0 = a
        a1 = a + ANGLE_PER
        poly = wedge_polygon(cx, cy, R_OUTER, R_INNER, a0, a1)
        col = pocket_color(num)
        pygame.draw.polygon(surface, col, poly)
        pygame.draw.polygon(surface, GRAY, poly, 1)
        a = a1

    # Wheel hub
    pygame.draw.circle(surface, (200,200,200), (int(cx), int(cy)), R_INNER-15, 0)
    pygame.draw.circle(surface, (120,120,120), (int(cx), int(cy)), R_INNER-15, 3)

    # Separator lines
    for i in range(POCKETS):
        ang = i*ANGLE_PER
        x0 = cx + R_INNER*math.sin(ang)
        y0 = cy - R_INNER*math.cos(ang)
        x1 = cx + R_OUTER*math.sin(ang)
        y1 = cy - R_OUTER*math.cos(ang)
        pygame.draw.line(surface, (60,60,60), (x0,y0), (x1,y1), 2)

    # Numbers around the rim (rotated with wheel)
    for i, num in enumerate(WHEEL_ORDER):
        ang = i*ANGLE_PER + ANGLE_PER/2
        # rotate by wheel_angle
        ang = angle_wrap(ang + wheel_angle)
        x = cx + (R_OUTER+20)*math.sin(ang)
        y = cy - (R_OUTER+20)*math.cos(ang)
        col = pocket_color(num)
        label = font_small.render(str(num), True, col)
        rect = label.get_rect(center=(x,y))
        surface.blit(label, rect)

    # Draw ball (rotates opposite direction)
    bx = cx + (R_OUTER-30)*math.sin(ball_angle)
    by = cy - (R_OUTER-30)*math.cos(ball_angle)
    pygame.draw.circle(surface, YELLOW, (int(bx), int(by)), BALL_RADIUS)

    # Top indicator triangle
    tip = (cx, cy - (R_OUTER + 48))
    pygame.draw.polygon(surface, (200,200,200), [
        (tip[0], tip[1]-10),
        (tip[0]-10, tip[1]+10),
        (tip[0]+10, tip[1]+10),
    ])

def draw_panel(surface):
    # Right side panel
    panel_rect = pygame.Rect(900-10, 0, 1100- (900-10), HEIGHT)
    pygame.draw.rect(surface, PANEL, panel_rect)

    x = panel_rect.x + 20
    y = 20
    surface.blit(font_big.render("RUEDA EUROPEA", True, WHITE), (x, y)); y+=40

    surface.blit(font.render(f"Bankroll: ${bankroll}", True, WHITE), (x,y)); y+=30
    surface.blit(font.render(f"Chip: ${chip_amount}   (↑/↓ para cambiar)", True, WHITE), (x,y)); y+=30

    y+=10
    surface.blit(font.render("Apuestas (ENTER para STRAIGHT)", True, LIGHT), (x,y)); y+=25

    # Show bet slip
    if bet_slip:
        for (kind,arg), amt in bet_slip.items():
            text = f"{kind}{' '+str(arg) if arg is not None else ''}: ${amt}"
            surface.blit(font_small.render(text, True, WHITE), (x,y)); y+=22
    else:
        surface.blit(font_small.render("— Vacío —", True, (180,180,180)), (x,y)); y+=22

    y+=10
    surface.blit(font.render("Total apuesta:", True, LIGHT), (x,y)); y+=25
    surface.blit(font_big.render(f"${total_bet_amount()}", True, WHITE), (x,y)); y+=40

    surface.blit(font_small.render("1 RED, 2 BLACK, 3 EVEN, 4 ODD", True, WHITE), (x,y)); y+=20
    surface.blit(font_small.render("5 LOW, 6 HIGH, S STRAIGHT num", True, WHITE), (x,y)); y+=20
    surface.blit(font_small.render("←/→ cambia número, ENTER agrega", True, WHITE), (x,y)); y+=20
    surface.blit(font_small.render("C limpia, SPACE gira", True, WHITE), (x,y)); y+=20

    y+=20
    if select_straight_mode:
        surface.blit(font.render(f"STRAIGHT nº: {straight_number}", True, YELLOW), (x,y)); y+=30

    if result_number is not None:
        col = pocket_color(result_number)
        txt = font_big.render(f"Salió: {result_number}", True, col)
        surface.blit(txt, (x, HEIGHT-60))

def handle_keydown(event_key):
    global chip_amount, select_straight_mode, straight_number
    if event_key == pygame.K_UP:
        chip_amount = min(1000, chip_amount + 5)
    elif event_key == pygame.K_DOWN:
        chip_amount = max(5, chip_amount - 5)
    elif event_key == pygame.K_c:
        bet_slip.clear()
    elif event_key == pygame.K_1:
        add_bet(("RED", None), chip_amount)
    elif event_key == pygame.K_2:
        add_bet(("BLACK", None), chip_amount)
    elif event_key == pygame.K_3:
        add_bet(("EVEN", None), chip_amount)
    elif event_key == pygame.K_4:
        add_bet(("ODD", None), chip_amount)
    elif event_key == pygame.K_5:
        add_bet(("LOW", None), chip_amount)
    elif event_key == pygame.K_6:
        add_bet(("HIGH", None), chip_amount)
    elif event_key == pygame.K_s:
        select_straight_mode = not select_straight_mode
    elif event_key == pygame.K_LEFT and select_straight_mode:
        straight_number = 36 if straight_number==0 else (straight_number-1)
    elif event_key == pygame.K_RIGHT and select_straight_mode:
        straight_number = 0 if straight_number==36 else (straight_number+1)
    elif event_key == pygame.K_RETURN and select_straight_mode:
        add_bet(("STRAIGHT", straight_number), chip_amount)

def main():
    global spinning, result_number

    # initial angles
    global wheel_angle, ball_angle, wheel_av, ball_av
    wheel_angle = 0.0
    ball_angle  = math.pi  # opposite

    running = True
    while running:
        dt = clock.tick(FPS) / 60.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if can_spin():
                        result_number = None
                        launch_spin()
                else:
                    handle_keydown(event.key)

        update_physics(dt)

        # Draw wheel rotated by wheel_angle; do this by applying an angle offset during label computation
        # We'll "bake" wheel_angle into drawing by rotating labels; wedges themselves are static but we simulate
        # rotation by effectively offsetting label angle. For visuals, we also draw ball separately.
        # Simpler approach: re-draw wedges fixed and only rotate labels/ball angles using current angles.
        # For a more realistic look, we can rotate wedges by shifting their computed angles (wheel_angle).
        # Here, we incorporate wheel_angle into the wedge generation by temporarily rotating the surface via math.
        # To keep performance OK, we approximate by drawing wedges already accounted for with base angles then overlay
        # labels that include wheel_angle. The separators and ball depiction use angles with current wheel/ball states.

        # To simulate wheel rotation in wedge colors, we redraw wedges each frame with angles + wheel_angle
        # by temporarily modifying the global draw routine. We'll re-implement a quick version here.
        def draw_wheel_with_rotation(surface):
            surface.fill(BG)
            cx, cy = CENTER

            pygame.draw.circle(surface, LIGHT, (int(cx), int(cy)), R_TEXT, 0)
            pygame.draw.circle(surface, BG, (int(cx), int(cy)), R_TEXT-12, 0)

            a = wheel_angle  # start rotated
            for i, num in enumerate(WHEEL_ORDER):
                a0 = a
                a1 = a + ANGLE_PER
                poly = wedge_polygon(cx, cy, R_OUTER, R_INNER, a0, a1)
                col = pocket_color(num)
                pygame.draw.polygon(surface, col, poly)
                pygame.draw.polygon(surface, GRAY, poly, 1)
                a = a1

            pygame.draw.circle(surface, (200,200,200), (int(cx), int(cy)), R_INNER-15, 0)
            pygame.draw.circle(surface, (120,120,120), (int(cx), int(cy)), R_INNER-15, 3)

            # Separator lines (rotated)
            for i in range(POCKETS):
                ang = wheel_angle + i*ANGLE_PER
                x0 = cx + R_INNER*math.sin(ang)
                y0 = cy - R_INNER*math.cos(ang)
                x1 = cx + R_OUTER*math.sin(ang)
                y1 = cy - R_OUTER*math.cos(ang)
                pygame.draw.line(surface, (60,60,60), (x0,y0), (x1,y1), 2)

            # Numbers around the rim
            for i, num in enumerate(WHEEL_ORDER):
                ang = wheel_angle + i*ANGLE_PER + ANGLE_PER/2
                x = cx + (R_OUTER+20)*math.sin(ang)
                y = cy - (R_OUTER+20)*math.cos(ang)
                col = pocket_color(num)
                label = font_small.render(str(num), True, col)
                rect = label.get_rect(center=(x,y))
                surface.blit(label, rect)

            # Ball
            bx = cx + (R_OUTER-30)*math.sin(ball_angle)
            by = cy - (R_OUTER-30)*math.cos(ball_angle)
            pygame.draw.circle(surface, YELLOW, (int(bx), int(by)), BALL_RADIUS)

            # Indicator
            tip = (cx, cy - (R_OUTER + 48))
            pygame.draw.polygon(surface, (200,200,200), [
                (tip[0], tip[1]-10),
                (tip[0]-10, tip[1]+10),
                (tip[0]+10, tip[1]+10),
            ])

        draw_wheel_with_rotation(screen)
        draw_panel(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
