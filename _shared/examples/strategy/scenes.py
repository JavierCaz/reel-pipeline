"""Strategy concept scenes — executed by _shared/pipeline/visuals.py.

Every name (Scene, T, palette constants, icons, helpers) comes from the engine; see
_shared/pipeline/docs/visual-system.md. Times come from spoken words via W("phrase", after).
Labels follow the recording (it says "transporte público" and "auto" where the brief said camión/Uber).
"""
# flake8: noqa  (names are provided by the engine namespace)

MODES = [("walk", i_walk), ("bus", i_bus), ("car", i_car)]


def W(phrase, after=None):
    """T() scoped to the current scene: the first occurrence at or after the scene start."""
    return T(phrase, s.start if after is None else after)


CLASSES = ["WalkingRoute", "BusRoute", "UberRoute"]   # brief's class names (not spoken)


def klass(s, key, name, x, y, w=300, h=128, kicker=None, tint="glass", style="", size=30):
    """A UML-ish class card: optional kicker, the name, a rule; the method is typed in separately."""
    top = 14
    body = ""
    if kicker:
        body += f'<div class="v-kicker" style="position:absolute;left:18px;top:12px;font-size:20px">{kicker}</div>'
        top = 40
    body += (f'<div style="position:absolute;left:18px;right:12px;top:{top}px;font-size:{size}px;font-weight:700;'
             f'letter-spacing:-.04em;white-space:nowrap">{name}</div>'
             f'<div style="position:absolute;left:0;right:0;top:{top + 46}px;height:2px;background:{LINE}"></div>')
    return s.add(key, x, y, w, h, body, "v-card", f"background:{TINTS[tint]};{style}")


# 00 — HOOK over clips 1–2. The window powers on, the series title decodes, then shrinks into a
# header; three transport options appear ("no siempre eliges el mismo transporte") and clip 2
# pairs each one with its situation.
END0 = clip_end(2) - 0.02
s = Scene("00-titulo", 0, END0, decor=((1000, 34, "pearl"),), panel="instant")
s.window("win", 50, 96, 980, 566, "~/" + common.CONFIG["id"], 0.0)
t_c = 2.0
s.hook_title(OPENING_TITLE[0], OPENING_TITLE[1] if len(OPENING_TITLE) > 1 else None,
             t=0.22, x=110, y=250, compress_at=t_c, header=(110, 160), header_scale=0.42)
cols = [100, 415, 730]
for n, (key, icon) in enumerate(MODES):
    s.card(key, "", cols[n], 268, 250, 200, "glass", icon=icon(), icon_h=150)
    s.enter(key, W("mismo transporte") - 0.25 + n * 0.1, "pop", "pop" if n == 0 else "click-soft", gain=0.2)
labels = [("A pie", W("ir a pie")), ("Camión", W("un camión")), ("Uber", W("pedirte un"))]
situations = [[("Cercano", W("cercano") - 0.1)],
              [("Más lejos", W("más lejos") - 0.05)],
              [("Muchas cosas", W("muchas cosas") - 0.05), ("Llegar rápido", W("llegar rápido") - 0.05)]]
for n, (label, at) in enumerate(labels):
    s.text(f"l{n}", label, cols[n], 476, 250, 50, 36, 800, PRIMARY)
    s.enter(f"l{n}", at, "up", "click")
    s.glow(MODES[n][0], at, at + 1.2 if n < 2 else None)
    for k, (sit, st) in enumerate(situations[n]):
        pill(s, f"s{n}{k}", sit, cols[n] + 5, 538 + k * 60, 240, 50, "warm", 24, color=WARM)
        s.enter(f"s{n}{k}", st, "down", "pop" if k == 0 else None, gain=0.18)

# 01 — same need, the best way depends on the situation and the destination
s = Scene("01-necesidad", clip_start(3) - 0.02, clip_end(3) - 0.02, decor=((60, 650, "cube"), (960, 150, "pearl")))
s.heading("Misma necesidad", W("necesidad"))
for n, (key, icon) in enumerate(MODES):
    s.card(key, "", 110, 284 + n * 122, 120, 104, "glass", icon=icon(), icon_h=80)
    s.enter(key, W("La necesidad") + n * 0.08, "left", "click-soft" if n == 0 else None, gain=0.2)
s.card("goal", "Llegar a donde vas", 470, 300, 500, 250, "accent", 32, icon=i_pin(), icon_h=150, color=PRIMARY)
s.enter("goal", W("llegar a donde") - 0.1, "pop", "pop")
for n in range(3):
    s.line(f"a{n}", [(244, 336 + n * 122), (462, 425)], W("llegar a donde") + 0.1 + n * 0.08, color=SOFT if THEME != "terminal" else LINE,
           width=4, duration=0.3)
s.pulse("goal", W("vas") + 0.05, 1.05)
s.text("dep", "depende de:", 470, 566, 230, 50, 28, 700, MUTED)
s.enter("dep", W("depende") - 0.05, "fade")
pill(s, "sit", "Situación", 470, 616, 240, 52, "warm", 26, color=WARM)
s.enter("sit", W("situación") - 0.25, "up", "click")
pill(s, "dest", "Destino", 730, 616, 240, 52, "warm", 26, color=WARM)
s.enter("dest", W("y tu destino") - 0.12, "up", "click")

# 02 — each transport option is a different strategy to reach the destination
s = Scene("02-estrategia", clip_start(4) - 0.02, clip_end(4) - 0.02, decor=((60, 650, "pearl"), (970, 150, "cube")))
s.heading("Cada opción, una estrategia", W("Cada opción"), size=46)
dot(s, "you", 150, 470, 44, HOT)
s.enter("you", W("Cada opción") + 0.05, "pop", "pop")
s.text("you-t", "Tú", 110, 500, 80, 46, 30, 800, HOT_TEXT)
s.enter("you-t", W("Cada opción") + 0.1, "up")
s.art("pin", i_pin(), 890, 400, 90, 90)
s.enter("pin", W("opción de transporte") - 0.05, "drop")
routes = [(520, 250), (520, 466), (520, 690)]          # quadratic control points; icons sit on each curve's midpoint
mids = [(round((176 + 2 * cx + 884) / 4), round((470 + 2 * cy + 462) / 4)) for cx, cy in routes]
for n, ((cx, cy), (mx_, my_)) in enumerate(zip(routes, mids)):
    s.line(f"r{n}", [(176, 470), (884, 462)], W("transporte") + n * 0.12, color=[PRIMARY, WARM, ACCENT][n], width=5,
           head=False, duration=0.45, curve=(cx, cy))
    s.card(f"m{n}", "", mx_ - 48, my_ - 42, 96, 84, "glass", icon=MODES[n][1](), icon_h=64)
    s.enter(f"m{n}", W("transporte") + 0.2 + n * 0.12, "pop", "click-soft" if n == 1 else None, gain=0.2)
    pill(s, f"e{n}", f"Estrategia {n + 1}", mx_ + 62, my_ - 26, 250, 52, "accent", 26, color=PRIMARY)
    s.enter(f"e{n}", W("estrategia distinta") - 0.05 + n * 0.12, "left", "pop" if n == 0 else None, gain=0.2)
for n, (mx_, my_) in enumerate(mids):
    s.travel(f"t{n}", [(176, 470), (mx_, my_), (884, 462)], W("para llegar") + n * 0.08, 0.55, [PRIMARY, WARM, ACCENT][n])
s.pulse("pin", W("destino final"), 1.15, sfx="ping")

def layout(mode, clip):
    """The presenter-layout segment (config "stage") of this mode in this clip."""
    return next(seg for seg in STAGE if seg["mode"] == mode and seg["clip"] == clip)


# 03a — Strategy is a behavioural pattern (top panel; the presenter stays full frame).
s = Scene("03a-strategy", clip_start(5) - 0.02, clip_end(5) - 0.02, decor=((60, 650, "cube"), (960, 150, "pearl")))
s.text("prog", "En programación", 110, 196, 600, 60, 40, 700, MUTED, cls="v-head")
s.enter("prog", W("programación") - 0.1, "left")
s.decode("name", "Strategy", 210, 300, 120, W("Strategy") - 0.1, color=PRIMARY, sfx="typing", gain=0.4, cursor_at=W("Strategy") + 0.6)
s.card("kind", "Patrón de comportamiento", 190, 470, 700, 82, "warm", 38, pill=True, color=WARM)
s.enter("kind", W("patrón de comportamiento") - 0.1, "stamp", "pop", rest={"rotation": -2})
s.pulse("kind", W("comportamiento") + 0.25, 1.06)

# 03b — CIRCLE: the task → three ways → choose diagram takes the frame; the face floats bottom right.
s = Scene("03b-maneras", clip_start(6) - 0.02, clip_end(6) - 0.02, decor=((60, 1290, "cube"), (960, 150, "pearl")))
s.text("h2", "Strategy", 60, 196, 600, 66, 50, 700, INK, cls="v-head")
s.enter("h2", W("Nos permite"), "left")
xs = [40, 380, 720]
for n in range(3):
    s.card(f"w{n}", f"Manera {n + 1}", xs[n], 600, 320, 130, "glass", 40)
    s.enter(f"w{n}", W("diferentes maneras") + n * 0.12, "up", "pop" if n == 0 else "click-soft", gain=0.2)
s.card("task", "Tarea", 340, 330, 400, 116, "paper", 54, style=f"border-color:{INK}")
s.enter("task", W("una tarea") - 0.1, "down", "click")
for n in range(3):
    s.line(f"c{n}", [(540, 456), (xs[n] + 160, 590)], W("una tarea") + 0.15 + n * 0.06, color=LINE, width=5, duration=0.25)
t_e = W("elegir cuál")
s.dim(["w0", "w2", "c0", "c2"], t_e + 0.1, 0.3)
s.glow("w1", t_e)
s.pulse("w1", t_e + 0.05, 1.08, sfx="click")
s.art("ok", i_check(PRIMARY), 660, 566, 76, 76)
s.enter("ok", t_e + 0.25, "pop")
pill(s, "need", "Según nuestras necesidades", 40, 790, 620, 66, "soft", 30)
s.enter("need", W("según nuestras") - 0.05, "up", "click-soft")

# 04 — CARD: full-width map app; routes per mode (walking, public transport, car); all reach the goal.
s = Scene("04-mapa", clip_start(7) - 0.02, clip_end(8) - 0.02, decor=((60, 1290, "pearl"), (970, 150, "capsule")))
s.heading("Aplicación de mapa", W("aplicación de mapa") - 0.05, x=60, size=50)
streets = "".join(f'<path d="M0 {y}H960" stroke="{LINE}" stroke-width="14"/>' for y in (80, 280, 480)) + \
          "".join(f'<path d="M{x} 0V560" stroke="{LINE}" stroke-width="14"/>' for x in (80, 480, 860))
s.add("map", 60, 290, 960, 560, f'<svg viewBox="0 0 960 560">{streets}</svg>', "v-card", f"background:{TINTS['soft']}")
s.enter("map", W("aplicación de mapa"), "fade", "whoosh-short")
dot(s, "you", 140, 770, 44, HOT)
s.enter("you", W("puede definir") - 0.1, "pop", "pop")
s.art("pin", i_pin(), 884, 296, 72, 72)
s.enter("pin", W("una ruta") - 0.1, "drop")
paths = [[(140, 770), (140, 570), (540, 570), (540, 370), (900, 370)],
         [(140, 770), (920, 770), (920, 385)],
         [(140, 770), (140, 370), (900, 370)]]
colors = [PRIMARY, WARM, ACCENT]
modes = [("A pie", i_walk(), W("vayamos a pie") + 0.4), ("Transporte público", i_bus(), W("transporte público")),
         ("Auto", i_car(), W("un auto"))]
for n, (label, icon, at) in enumerate(modes):
    row_card(s, f"mode{n}", label, icon, 60, 890 + n * 112, 520, 96, "glass", 30)
    s.enter(f"mode{n}", at - 0.15, "left", "click")
    s.line(f"p{n}", paths[n], at, color=colors[n], width=10, head=False, duration=0.5)
    if n:
        s.dim([f"p{n - 1}", f"mode{n - 1}"], at, 0.3)
t_d = W("de manera diferente")
for n in range(3):
    s.move(f"mode{n}", t_d - 0.3 + n * 0.25, 0.25, "power2.out", opacity=1)
    s.move(f"p{n}", t_d - 0.3 + n * 0.25, 0.25, "power2.out", opacity=1)
    s.pulse(f"mode{n}", t_d - 0.05 + n * 0.25, 1.05, sfx="click-soft" if n == 1 else None)
s.pulse("pin", W("mismo objetivo"), 1.2, sfx="ping")
pill(s, "goal", "Ayudarte a llegar", 60, 1228, 520, 60, "accent", 30, color=PRIMARY)
s.enter("goal", W("ayudarte") - 0.1, "up", "sparkle", gain=0.14)

# 05 — CIRCLE: the code diagram with the face in a circle (bottom right); then the app delegates to the chosen
# strategy without knowing its details (face back in a circle).
s = Scene("05-codigo", clip_start(9) - 0.02, clip_end(10) - 0.02, decor=((60, 1290, "cube"), (960, 150, "pearl")))
s.heading("En el código", W("En el código"), x=60, size=50)
cx = [40, 380, 720]
for n, name in enumerate(CLASSES):
    klass(s, f"k{n}", name, cx[n], 640, 320, 160)
    s.enter(f"k{n}", W("cada forma de viajar") + 0.15 + n * 0.14, "up", "pop" if n == 0 else "click-soft", gain=0.2)
s.text("strat", "estrategias distintas", 240, 830, 600, 50, 34, 700, MUTED)
s.enter("strat", W("estrategia distinta") - 0.05, "fade")
s.exit("strat", W("pero todas") - 0.1, "fade")
klass(s, "iface", "RouteStrategy", 380, 300, 660, 180, kicker="«interface»", tint="accent")
s.enter("iface", W("mismo método") - 0.25, "down", "pop")
for n in range(3):
    s.line(f"i{n}", [(cx[n] + 160, 634), (530 + n * 180, 492)], W("mismo método") + 0.2 + n * 0.06, color=PRIMARY, width=4, duration=0.3)
t_m = W("calcularRuta")
s.typewrite("im", "calcularRuta()", 400, 418, 36, t_m - 0.05, cps=40, color=PRIMARY, weight=700, sfx="typing", gain=0.3)
for n in range(3):
    s.typewrite(f"km{n}", "calcularRuta()", cx[n] + 18, 712, 30, t_m + 0.2 + n * 0.08, cps=50, color=ACCENT)
# clip 10 — the app uses the chosen strategy (presenter back as a circle, bottom right)
row_card(s, "app", "App", i_phone(), 40, 335, 300, 110, "paper", 38)
s.enter("app", W("La aplicación") - 0.1, "left", "click")
s.line("use", [(346, 390), (372, 390)], W("usa la estrategia") - 0.05, color=INK, width=5, duration=0.25)
t_el = W("elegida")
s.dim(["k0", "k2", "km0", "km2", "i0", "i2"], t_el, 0.28)
s.glow("k1", t_el)
s.travel("go", [(710, 492), (540, 634)], t_el + 0.1, 0.45, HOT, 20)
s.pulse("k1", t_el + 0.5, 1.06, sfx="click")
pill(s, "hide", "Sin saber los detalles", 40, 860, 620, 62, "warm", 30, color=WARM)
s.enter("hide", W("sin saber") - 0.05, "up", "pop")
s.inner("k1", W("detalles") - 0.1, 0.3, "power2.inOut", opacity=0.45)

# 06 — without the pattern: a tower of conditions; with Strategy: separate strategies, add a new one
s = Scene("06-condicionales", clip_start(11) - 0.02, clip_end(12) - 0.02, decor=((60, 650, "pearl"), (970, 150, "cube")))
s.heading("Sin este patrón", W("Sin este patrón"), size=48)
s.window("code", 80, 280, 920, 330, "~/ruta", W("el código") - 0.15, crt=False, sfx="click-soft")
code = [('if (modo == "camión") {…}', W("es en camión")),
        ('else if (modo == "a pie") {…}', W("es a pie")),
        ('else if (modo == "auto") {…}', W("es en auto"))]
for n, (line, at) in enumerate(code):
    s.typewrite(f"cl{n}", line, 112, 350 + n * 62, 32, at - 0.1, cps=55, color=INK if n == 0 else MUTED, sfx="typing" if n == 0 else "key-press", gain=0.3)
s.card("warn", "Llena de condiciones", 560, 532, 400, 60, "warm", 28, pill=True, color=ALERT)
s.enter("warn", W("condiciones") - 0.15, "stamp", "error", gain=0.4, rest={"rotation": -3})
# Graphic transition: the chain collapses into separate strategies.
t_s = W("Con Strategy")
for key in ("code", "cl0", "cl1", "cl2", "warn"):
    s.exit(key, t_s - 0.3, "shrink")
s.exit("heading", t_s - 0.3, "up")
s.text("h2", "Con Strategy", 110, 196, 600, 66, 50, 700, PRIMARY, cls="v-head")
s.enter("h2", t_s, "left", "whoosh-short")
grid = [(110, 300), (560, 300), (110, 480)]
for n, name in enumerate(CLASSES):
    klass(s, f"k{n}", name, grid[n][0], grid[n][1], 410, 128)
    s.enter(f"k{n}", W("cada forma") - 0.1 + n * 0.12, "pop", "pop" if n == 0 else "click-soft", gain=0.2)
    s.typewrite(f"km{n}", "calcularRuta()", grid[n][0] + 18, grid[n][1] + 74, 26, W("calcular la ruta") + n * 0.08, cps=50, color=ACCENT)
t_sep = W("queda separada")
for n in range(3):
    s.pulse(f"k{n}", t_sep + 0.1 + n * 0.08, 1.05, sfx="click-soft" if n == 0 else None)
s.add("slot", 560, 480, 410, 128, "", "v-card", f"background:transparent;border:3px dashed {PRIMARY};box-shadow:none")
s.enter("slot", W("agregamos") - 0.1, "pop", "click")
klass(s, "new", "+ Nueva estrategia", 560, 480, 410, 128, tint="accent")
s.enter("new", W("añadir") - 0.1, "stamp", "ping", rest={"rotation": -2})
s.typewrite("newm", "calcularRuta()", 578, 554, 26, W("nueva estrategia") - 0.1, cps=50, color=PRIMARY)

# 07 — the same idea elsewhere: payments, sorting, discounts (top panel).
s = Scene("07-casos", clip_start(13) - 0.02, clip_end(13) - 0.02, decor=((60, 650, "cube"), (960, 150, "pearl")))
s.heading("Otros casos", W("otros casos") - 0.1)
uses = [("Métodos de pago", i_card(), W("métodos de pago")),
        ("Ordenar un resultado", i_sort(), W("ordenar un resultado")),
        ("Calcular un descuento", i_tag(), W("calcular un descuento"))]
for n, (label, icon, at) in enumerate(uses):
    row_card(s, f"u{n}", label, icon, 70, 290 + n * 122, 640, 100, "glass", 32)
    s.enter(f"u{n}", at - 0.15, "left", "pop")
    pill(s, f"g{n}", "Strategy", 750, 308 + n * 122, 240, 64, "accent", 28, color=PRIMARY)
    s.enter(f"g{n}", at + 0.25, "right", "click-soft", gain=0.2)

# 08 — recap: separate the ways, choose the one that fits; the city analogy maps to code
s = Scene("08-cierre", clip_start(14) - 0.02, T("Déjamelo") - 0.04, decor=((60, 650, "pearl"), (970, 150, "cube")))
s.card("task", "Tarea", 390, 290, 300, 90, "paper", 40, style=f"border-color:{INK}")
s.enter("task", W("una tarea") - 0.1, "down", "click")
mx = [215, 415, 615]
for n in range(3):
    s.card(f"w{n}", f"Manera {n + 1}", mx[n], 470, 250, 90, "glass", 30)
    s.enter(f"w{n}", W("varias maneras") + n * 0.1, "up", "pop" if n == 0 else None, gain=0.2)
t_sp = W("separarlas")
for n, x in enumerate([90, 405, 720]):
    s.move(f"w{n}", t_sp - 0.1, 0.45, "back.out(1.4)", x=x - mx[n])
s.sfx(t_sp - 0.1, "whoosh-short")
t_el = W("elegir la que")
s.dim(["w0", "w2"], t_el, 0.3)
s.glow("w1", t_el)
s.move("w1", W("mejor encaje") - 0.1, 0.4, "back.out(1.6)", y=-84)
s.sfx(W("encaje"), "click")
# clip 15 — "así como eliges cómo moverte por tu ciudad, en código puedes elegir estrategias"
t_a = W("Así como")
for key in ("task", "w0", "w1", "w2"):
    s.exit(key, t_a - 0.15, "up")
s.text("city-t", "Tu ciudad", 90, 220, 400, 56, 38, 800, INK)
s.enter("city-t", t_a, "down")
for n, (key, icon) in enumerate(MODES):
    s.card(f"c{n}", "", 90 + n * 140, 300, 120, 104, "glass", icon=icon(), icon_h=80)
    s.enter(f"c{n}", W("moverte") + n * 0.08, "pop", "pop" if n == 0 else None, gain=0.2)
s.text("code-t", "En código", 590, 220, 400, 56, 38, 800, PRIMARY)
s.enter("code-t", W("en código") - 0.05, "down")
for n, name in enumerate(CLASSES):
    pill(s, f"k{n}", name, 590, 290 + n * 44, 400, 40, "soft", 24)
    s.enter(f"k{n}", W("en código") + 0.1 + n * 0.08, "right", "click-soft" if n == 0 else None, gain=0.2)
s.line("eq", [(520, 352), (566, 352)], W("puedes elegir") - 0.2, color=PRIMARY, width=5, duration=0.25)
s.banner("big", "Strategy", W("elegir estrategias") - 0.1, y=450, h=130, size=90)
s.card("kind", "Patrón de comportamiento", 230, 610, 620, 60, "warm", 30, pill=True, color=WARM)
s.enter("kind", W("estrategias", clip_start(15)) + 0.1, "up", "pop")
# CTA question over the same panel: "¿tienes algún proyecto donde utilizarías este patrón?"
t_q = W("tienes algún proyecto")
for key in ("city-t", "c0", "c1", "c2", "code-t", "k0", "k1", "k2", "eq"):
    s.exit(key, t_q - 0.35, "up")
s.card("q", "¿Dónde usarías este patrón?", 120, 260, 840, 110, "paper", 40, style=f"border-color:{PRIMARY}")
s.enter("q", W("algún proyecto") - 0.05, "down", "pop")

# 09 — CTA: comments and follow; the end card follows
s = Scene("09-cta", T("Déjamelo") - 0.04, min(DURATION, OUTRO_START + 0.6), decor=((60, 650, "cube"), (960, 150, "pearl")))
s.card("com", "Déjamelo en los comentarios", 140, 260, 800, 230, "glass", 36, icon=i_comment(), icon_h=130)
s.enter("com", W("Déjamelo") + 0.05, "pop", "pop")
s.pulse("com", W("comentarios") + 0.1, 1.05, sfx="click")
s.exit("com", W("Y si te gustó") - 0.2, "up")
s.card("follow", "Sígueme", 300, 260, 480, 230, "accent", 40, icon=i_follow(), icon_h=130, color=PRIMARY)
s.enter("follow", W("sígueme") - 0.15, "pop", "notification", gain=0.16)
pill(s, "more", "Más sobre desarrollo de software", 140, 530, 800, 64, "soft", 30)
s.enter("more", W("desarrollo de software") - 0.3, "up", "sparkle", gain=0.14)


# COVER — static illustration for the cover image (step 9, `npm run build -- cover`): the analogy in
# one picture — you, three routes (walk, bus, car), the same destination. Stage coordinates, y ≈ 780–1250.
def cover(c):
    you, goal = (170, 1015), (885, 1000)
    colors = [PRIMARY, WARM, ACCENT]
    for n, cy in enumerate((690, 1010, 1330)):
        mx, my = round((you[0] + 2 * 528 + goal[0]) / 4), round((you[1] + 2 * cy + goal[1]) / 4)
        c.line(f"r{n}", [you, goal], 0, color=colors[n], width=7, head=False, curve=(528, cy))
        c.card(f"m{n}", "", mx - 62, my - 54, 124, 108, "paper", icon=MODES[n][1](), icon_h=82)
    dot(c, "you", you[0], you[1], 54, HOT)
    c.text("you-t", "Tú", you[0] - 50, you[1] + 34, 100, 50, 36, 800, HOT_TEXT)
    c.art("pin", i_pin(), goal[0] - 6, goal[1] - 104, 110, 110)
