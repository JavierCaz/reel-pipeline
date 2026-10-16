"""CelularEscucha concept scenes — executed by _shared/pipeline/visuals.py.

Every name (Scene, T, palette constants, icons, helpers) comes from the engine; see
_shared/pipeline/docs/visual-system.md. Times come from spoken words via T("phrase", after).
"""
# flake8: noqa  (names are provided by the engine namespace)


# 00 — HOOK. A terminal window powers on, the title decodes and glitches, then the familiar
# experience plays inside it: you talk about something → hours later → the ad appears.
END0 = T("probablemente pensaste") - 0.02
s = Scene("00-titulo", 0, END0, decor=((1000, 34, "pearl"),), panel="instant")
s.window("win", 50, 96, 980, 566, "~/tu-celular", 0.0)
s.decode("clock", "14:02", 850, 103, 26, 0.4, color=MUTED, scramble=MUTED, weight=600, steps=4, stagger=0.03,
         roll=0.2, glyphs="0123456789")
t_c = 2.35  # the title shrinks into a header as the conversation begins ("hablas de algún tema")
hook = s.hook_title(OPENING_TITLE[0], OPENING_TITLE[1] if len(OPENING_TITLE) > 1 else None,
                    t=0.22, x=110, y=240, compress_at=t_c, header=(110, 160), header_scale=0.4)

# The conversation: two people, a topic bubble (coffee), and a live voice meter.
s.art("pa", i_user(SOFT), 110, 410, 160, 160)
s.enter("pa", t_c + 0.15, "pop", "pop")
s.art("pb", i_user(ACCENT), 400, 410, 160, 160)
s.enter("pb", t_c + 0.28, "pop")
s.add("chat", 215, 280, 200, 100, f'<div style="position:absolute;inset:0;background:{SURFACE};border:3px solid {INK};'
      f'box-shadow:{CARD_SHADOW}"><div style="position:absolute;left:60px;top:10px;width:80px;height:80px">{i_cup()}</div></div>')
s.enter("chat", T("específico") + 0.05, "pop", "pop")
s.inner("chat", T("específico") + 0.4, 0.16, "sine.inOut", y=-6, repeat=3, yoyo=True)
s.levels("wave", 282, 468, 108, 56, 9, T("con alguien") - 0.15, T("y a las") + 0.1)

# "y a las horas": time warp — the window clock rolls forward, streaks sweep, the scene dims.
t_w = T("horas") - 0.32
s.dim(["pa", "pb", "chat", "wave"], t_w, 0.28)
for k, (sy, length) in enumerate([(190, 420), (262, 300), (344, 520), (430, 360), (518, 460), (600, 280)]):
    key = f"streak{k}"
    s.add(key, 1030 - length, sy, length, 4, "", "", f"background:linear-gradient(90deg,transparent,{PRIMARY})")
    at = t_w + k * 0.035
    s.tw(s.sel(key), at, 0.04, "none", opacity=0.9)
    s.tw(s.sel(key), at, 0.34, "power2.in", x=-(980 - length))
    s.tw(s.sel(key), at + 0.3, 0.06, "none", opacity=0)
s.sfx(t_w, "whoosh-short")
s.exit("clock", t_w + 0.05, "fade")
s.decode("clock2", "19:47", 850, 103, 26, t_w + 0.05, color=PRIMARY, start_text="14:02", weight=600, steps=8,
         stagger=0.06, roll=0.5, glyphs="0123456789", sfx="click-soft")
s.card("later", "Horas después", 375, 588, 330, 56, "warm", 26, pill=True)
s.enter("later", T("horas") - 0.05, "up")

# "te aparece publicidad relacionada en tu teléfono": phone, ad pops, the topic links to the ad.
s.art("phone", i_phone(), 760, 175, 180, 306)
s.enter("phone", T("te aparece") - 0.18, "right", "whoosh-short")
s.card("ad", "Anuncio", 785, 268, 130, 165, "paper", 20, icon=i_cup(), icon_h=72, color=PRIMARY,
       style=f"border:3px solid {PRIMARY}")
s.enter("ad", T("aparece") + 0.02, "pop", "notification", gain=0.16)
s.inner("phone", T("aparece") + 0.1, 0.06, "sine.inOut", x=5, repeat=5, yoyo=True)
s.pulse("ad", T("publicidad"), 1.1, glow=True)
s.move("chat", T("relacionada") - 0.3, 0.3, "power2.out", opacity=1)
s.line("link", [(400, 290), (850, 268)], T("relacionada") - 0.12, color=PRIMARY, width=4, head=False,
       duration=0.4, curve=(620, 200))
s.pulse("chat", T("relacionada") + 0.3, 1.12)
s.pulse("ad", T("relacionada") + 0.3, 1.12, sfx="ping")

# 01 — "my phone is listening to me" … no, it doesn't need to
s = Scene("01-escuchando", T("probablemente pensaste") - 0.02, T("hay un mito") - 0.04, decor=((60, 640, "cube"), (960, 150, "pearl")))
s.heading("¿Mi celular me está escuchando?", T("pensaste"), size=44)
s.art("waves", i_waves(f"{s.id}-wv"), 315, 290, 450, 300)
s.art("phone", i_phone(), 450, 280, 180, 306)
s.enter("phone", T("probablemente pensaste") + 0.05, "pop", "pop")
s.art("mic", i_mic(SOFT), 490, 380, 100, 100)
s.enter("mic", T("celular") - 0.1, "pop")
s.enter("waves", T("escuchando") - 0.1, "fade", "whoosh-short", gain=0.12)
for i in range(3):
    s.set(f"#{s.id}-wv-w{i}", opacity=0.15)
    s.tw(f"#{s.id}-wv-w{i}", T("escuchando") + i * 0.14, 0.32, "sine.inOut", opacity=0.95, repeat=7, yoyo=True)
t_int = T("interesante")
s.exit("waves", T("interesante") + 0.35, "fade")
s.exit("heading", t_int, "up")
s.exit("heading-line", t_int, "fade")
s.card("better", "Hay otra explicación", 270, 210, 540, 74, "soft", 34, pill=True)
s.enter("better", t_int + 0.1, "down", "click-soft")
t_no = T("no necesita")
s.exit("better", t_no - 0.4, "up")
for key in ("phone", "mic"):
    s.exit(key, t_no - 0.4, "shrink")
s.banner("nonec", "No necesita escucharte", t_no - 0.05, y=330, h=140, size=62)

# 02 — the myth: microphone → audio → analysis → ad
s = Scene("02-mito", T("hay un mito") - 0.04, T("y aunque") - 0.04, decor=((50, 650, "pearl"), (980, 170, "cube")))
s.heading("El mito", T("mito"))
nodes = [("mic", "Micrófono", i_mic(SOFT), T("micrófono")),
         ("audio", "Audio", i_audio(f"{s.id}-au"), T("escuchando", 19)),
         ("ana", "Análisis", i_gear(f"{s.id}-g"), T("conversaciones")),
         ("ad", "Publicidad", i_megaphone(), T("publicidad", 20))]
for n, (key, label, icon, at) in enumerate(nodes):
    x = 62 + n * 248
    icon_card(s, key, label, icon, x, 330, 210, 180, "accent" if key == "ad" else "glass", 27)
    s.enter(key, at - 0.12, "up", "pop")
    if n:
        s.line(f"a{n}", [(x - 34, 420), (x - 6, 420)], at - 0.3, duration=0.22)
        s.travel(f"f{n}", [(x - 72, 420), (x - 4, 420)], at + 0.3, 0.4, HOT, 14)
s.card("rec", "Siempre encendido", 40, 528, 290, 60, "warm", 24, pill=True, color=ALERT)
s.enter("rec", T("siempre") - 0.05, "up", "click")
s.pulse("rec", T("abierto"), 1.08)
for i in range(9):
    s.set(f"#{s.id}-au-b{i}", scaleY=0.4, transformOrigin="50% 50%")
    s.tw(f"#{s.id}-au-b{i}", T("escuchando", 19) + 0.2 + i * 0.03, 0.18, "sine.inOut", scaleY=1.1, repeat=7, yoyo=True)
s.tw(f"#{s.id}-g-gear", T("conversaciones"), 2.0, "none", rotation=180, svgOrigin="50 50")
s.pulse("ad", T("publicidad", 20) + 0.3, 1.1, glow=True, sfx="ping")

# 03 — technically possible with permissions, but an inefficient way to know you
s = Scene("03-ineficiente", T("y aunque") - 0.04, T("piensa en toda") - 0.04, decor=((60, 640, "cube"), (940, 160, "capsule")))
s.card("perm", "", 250, 260, 580, 230, "glass")
s.enter("perm", T("aplicación") - 0.1, "up", "pop")
s.art("perm-mic", i_mic(SOFT), 290, 300, 150, 150)
s.enter("perm-mic", T("aplicación"), "pop")
s.text("perm-t", "Permiso: micrófono", 450, 300, 360, 60, 34, 850, INK, style="justify-content:flex-start")
s.enter("perm-t", T("permisos") - 0.1, "left", "click-soft")
s.art("perm-ok", i_check(ACCENT), 460, 380, 76, 76)
s.enter("perm-ok", T("permisos") + 0.3, "pop", "click")
s.text("perm-ok-t", "Permitido", 548, 388, 230, 60, 32, 800, PRIMARY, style="justify-content:flex-start")
s.enter("perm-ok-t", T("permisos") + 0.35, "left")
s.card("tech", "Técnicamente posible", 300, 520, 480, 74, "soft", 32, pill=True)
s.enter("tech", T("técnicamente") - 0.05, "up", "pop")
t_s = T("sería")
for key in ("perm", "perm-mic", "perm-t", "perm-ok", "perm-ok-t", "tech"):
    s.exit(key, t_s - 0.35, "up")
steps = [("Micrófono", i_mic(SOFT)), ("Audio", i_audio(f"{s.id}-au")), ("Subir", i_globe()), ("Servidor", i_server()),
         ("Transcribir", i_doc()), ("Idioma", i_gear(f"{s.id}-g")), ("Intereses", i_target()), ("Anuncio", i_megaphone())]
for n, (label, icon) in enumerate(steps):
    row, col = divmod(n, 4)
    col = col if row == 0 else 3 - col
    x, y = 70 + col * 245, 250 + row * 190
    icon_card(s, f"p{n}", label, icon, x, y, 200, 150, "glass", 25)
    s.enter(f"p{n}", t_s + n * 0.13, "pop", "click-soft" if n % 2 else "pop", gain=0.2)
    if n in (1, 2, 3, 5, 6, 7):
        if row == 0:
            s.line(f"c{n}", [(x - 40, y + 75), (x - 6, y + 75)], t_s + n * 0.13, duration=0.15)
        else:
            s.line(f"c{n}", [(x + 240, y + 75), (x + 206, y + 75)], t_s + n * 0.13, duration=0.15)
    elif n == 4:
        s.line("c4", [(x + 100, 404), (x + 100, y - 6)], t_s + n * 0.13, duration=0.15)
t_in = T("ineficiente")
s.card("cost", "Muy ineficiente", 330, 160, 420, 72, "warm", 34, pill=True, color=ALERT)
s.enter("cost", t_in, "stamp", "error", gain=0.5, rest={"rotation": -3})
for i in range(9):
    s.set(f"#{s.id}-au-b{i}", scaleY=0.4, transformOrigin="50% 50%")
    s.tw(f"#{s.id}-au-b{i}", t_s + 0.4 + i * 0.03, 0.16, "sine.inOut", scaleY=1.1, repeat=5, yoyo=True)
s.tw(f"#{s.id}-g-gear", t_s + 0.9, 1.6, "none", rotation=180, svgOrigin="50 50")
# Graphic collapse: the pipeline folds into a few everyday behaviour icons.
t_c = T("recolectar") - 0.05
for n in range(8):
    row, col = divmod(n, 4)
    col = col if row == 0 else 3 - col
    x, y = 70 + col * 245, 250 + row * 190
    s.move(f"p{n}", t_c + n * 0.02, 0.32, "power3.in", x=440 - x, y=330 - y, scale=0.2, opacity=0)
    s.live.remove(f"p{n}")
for key in ("c1", "c2", "c3", "c4", "c5", "c6", "c7", "cost"):
    s.exit(key, t_c, "fade")
behaviours = [("b0", i_cursor()), ("b1", i_heart()), ("b2", i_play()), ("b3", i_search()), ("b4", i_cart())]
for n, (key, icon) in enumerate(behaviours):
    s.art(key, icon, 130 + n * 172, 340, 130, 130)
    s.enter(key, t_c + 0.3 + n * 0.05, "pop", "pop" if n in (0, 4) else None)
s.text("datos", "tus datos", 340, 500, 400, 60, 40, 900, PRIMARY)
s.enter("datos", t_c + 0.45, "up")

# 04 — behavioural signals you already generate
s = Scene("04-senales", T("piensa en toda") - 0.04, T("individualmente") - 0.04, decor=((50, 650, "pearl"), (970, 160, "capsule")))
s.heading("Ya generas datos", T("información"))
s.art("you", i_user(SOFT), 440, 330, 200, 200)
s.enter("you", T("piensa en toda") + 0.1, "pop", "pop")
s.text("you-t", "Tú", 440, 530, 200, 50, 34, 900, INK)
s.enter("you-t", T("piensa en toda") + 0.2, "up")
signals = [("vistas", "Vistas", i_eye(), 110, 300, T("publicaciones")),
           ("saltas", "Saltas", i_skip(), 780, 300, T("skipeas")),
           ("likes", "Likes", i_heart(), 110, 490, T("like")),
           ("sigues", "Seguidos", i_follow(), 780, 490, T("cuentas"))]
d = 0
for key, label, icon, x, y, at in signals:
    icon_card(s, key, label, icon, x, y, 190, 160, "glass", 28)
    s.enter(key, at - 0.12, "left" if x < 500 else "right", "pop")
    for k in range(5):
        px, py = scatter(30, 540, 430, 230, 150, seed=d + 3)[d]
        dot(s, f"d{d}", px, py, 16 if k % 2 else 20, [PRIMARY, ACCENT, HOT][d % 3])
        s.enter(f"d{d}", at - 0.05 + k * 0.04, "fade")
        d += 1
for k in range(6):
    px, py = scatter(40, 540, 430, 260, 170, seed=11)[k]
    dot(s, f"g{k}", px, py, 14, ACCENT)
    s.enter(f"g{k}", T("generas") + k * 0.09, "pop", "click-soft" if k == 0 else None)

# 05 — one data point says little; joining signals builds a profile
s = Scene("05-perfil", T("individualmente") - 0.04, T("intereses") - 0.14, decor=((60, 640, "cube"), (950, 150, "pearl")))
s.heading("Un dato aislado", T("individualmente") + 0.1)
dot(s, "one", 540, 400, 44, PRIMARY)
s.enter("one", T("individualmente") + 0.2, "pop", "pop")
s.art("q", i_question(WARM), 590, 310, 90, 90)
s.enter("q", T("demasiado") - 0.1, "pop", "click-soft")
s.text("poco", "dice poco", 390, 470, 300, 54, 34, 800, MUTED)
s.enter("poco", T("dice") - 0.05, "up")
t_j = T("juntar")
for key in ("q", "poco", "heading", "heading-line"):
    s.exit(key, t_j - 0.3, "fade")
s.text("h2", "Señales  →  Perfil", 110, 196, 640, 72, 52, cls="v-head")
s.enter("h2", t_j - 0.1, "left")
points = scatter(28, 540, 420, 420, 165, seed=5)
for k, (px, py) in enumerate(points):
    dot(s, f"s{k}", px, py, 18 if k % 3 else 24, [PRIMARY, ACCENT, HOT, SOFT][k % 4])
    s.enter(f"s{k}", t_j - 0.25 + k * 0.012, "pop", "pop" if k == 0 else None)
t_m = T("señales", 45) + 0.25
for k, (px, py) in enumerate(points):
    s.move(f"s{k}", t_m + (k % 7) * 0.03, 0.5, "power3.in", x=540 - px, y=420 - py, scale=0.4)
    s.exit(f"s{k}", t_m + 0.55 + (k % 7) * 0.03, "fade")
s.sfx(t_m + 0.4, "whoosh-short")
s.exit("one", t_m + 0.3, "shrink")
s.add("card", 380, 290, 320, 300, f'<div style="position:absolute;left:100px;top:22px;width:120px;height:120px">{i_user(SOFT)}</div>'
      f'<div class="v-text" style="position:absolute;left:0;right:0;top:150px;height:56px;font-size:40px;font-weight:900">Perfil</div>'
      f'<div style="position:absolute;left:50px;right:50px;top:222px;height:12px;border-radius:6px;background:{SOFT}"></div>'
      f'<div style="position:absolute;left:50px;right:110px;top:248px;height:12px;border-radius:6px;background:{ACCENT};opacity:.7"></div>',
      "v-card", f"background:{TINTS['paper']}")
s.enter("card", T("armar") - 0.1, "grow", "ping")
s.pulse("card", T("perfil", 47) + 0.05, 1.06, glow=True)

# 06 — the profile: interests, habits, schedules, consumption — inferred, never typed
s = Scene("06-rasgos", T("intereses") - 0.14, T("pero aquí está") - 0.04, decor=((60, 650, "pearl"), (970, 140, "cube")))
s.add("card", 70, 250, 300, 380, f'<div style="position:absolute;left:90px;top:26px;width:120px;height:120px">{i_user(SOFT)}</div>'
      f'<div class="v-text" style="position:absolute;left:0;right:0;top:156px;height:56px;font-size:40px;font-weight:900">Perfil</div>',
      "v-card", f"background:{TINTS['paper']}")
s.enter("card", T("intereses") - 0.05, "fade")
rows = [("r0", "Intereses", i_target(), T("intereses"), ""),
        ("r1", "Hábitos", i_repeat(), T("hábitos"), ""),
        ("r2", "Horarios", i_clock(), T("horarios"), ""),
        ("r3", "Consumo", i_cart(), T("patrones"), "")]
for n, (key, label, icon, at, extra) in enumerate(rows):
    row_card(s, key, label, icon, 400, 250 + n * 98, 600, 86, "glass", 34, extra)
    s.enter(key, at - 0.1, "right", "click" if n % 2 else "pop")
    s.line(f"l{n}", [(372, 440), (396, 294 + n * 98)], at - 0.1, color=SOFT, width=4, head=False, duration=0.25)
t_y = T("y un montón")
for n in range(4):
    s.exit(f"r{n}", t_y - 0.2 + n * 0.04, "right")
    s.exit(f"l{n}", t_y - 0.2, "fade")
s.art("form", i_form(), 520, 250, 330, 330)
s.enter("form", T("cosas") - 0.1, "right", "whoosh-short")
s.text("form-t", "Formulario", 520, 580, 330, 50, 32, 850, MUTED)
s.enter("form-t", T("cosas"), "up")
s.strike("x1", 540, 290, 830, 560, T("nunca escribiste") + 0.1)
s.card("inf", "Inferido", 100, 560, 240, 66, "warm", 32, pill=True, color=ALERT)
s.enter("inf", T("explícitamente") - 0.05, "stamp", "pop", rest={"rotation": -4})

# 07 — people who behave like you (zoom out to many profiles, highlight a cluster)
s = Scene("07-grupo", T("pero aquí está") - 0.04, T("imagina") - 0.04, decor=((60, 650, "cube"), (960, 150, "pearl")))
crowd = []
for r in range(5):
    for c in range(12):
        x = 140 + c * 72 + (18 if r % 2 else 0)
        y = 290 + r * 74
        crowd.append((x, y))
# Anchor the highlighted person to an exact crowd-grid dot so it replaces that dot in place.
you = crowd[2 * 12 + 6]
near = [p for p in crowd if ((p[0] - you[0]) / 1.3) ** 2 + (p[1] - you[1]) ** 2 < 120 ** 2]
base = "".join(f'<circle cx="{x}" cy="{y}" r="17" fill="{SOFT}" opacity=".55"/>' for x, y in crowd if (x, y) != you)
s.add("crowd", 0, 0, 1080, 760, f'<svg viewBox="0 0 1080 760">{base}</svg>', origin="540px 440px")
s.set(s.sel("crowd"), scale=2.2)
s.tw(s.sel("crowd"), T("pero aquí está") + 0.1, 1.0, "power3.out", scale=1, opacity=1)
s.sfx(T("pero aquí está") + 0.1, "whoosh-short")
s.add("you", you[0] - 20, you[1] - 20, 40, 40,
      f'<svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="17" fill="{HOT}"/></svg>', z=2)
s.enter("you", T("parte") - 0.1, "pop", "pop")
s.text("you-t", "Tú", you[0] - 50, you[1] + 24, 100, 44, 30, 900, HOT_TEXT)
s.enter("you-t", T("parte"), "up")
s.heading("No necesitan entenderte", T("necesitan"), size=48)
t_g = T("grupo")
s.exit("heading", t_g - 0.5, "up")
s.exit("heading-line", t_g - 0.5, "fade")
hi = "".join(f'<circle cx="{x}" cy="{y}" r="17" fill="{PRIMARY}"/>' for x, y in near)
s.add("cluster", 0, 0, 1080, 760, f'<svg viewBox="0 0 1080 760">{hi}</svg>')
s.enter("cluster", t_g - 0.1, "fade", "sparkle", gain=0.14)
ring(s, "ring", you[0] - 190, you[1] - 150, 380, 300)
s.enter("ring", t_g, "grow")
s.text("sim", "Personas con patrones similares", 110, 190, 860, 70, 46, 900, INK)
s.enter("sim", T("personas") - 0.05, "down", "pop")
s.pulse("you", T("asemejen"), 1.25)

# 08 — similar users end up interested in a product → high probability for you
s = Scene("08-producto", T("imagina") - 0.04, T("tal vez") - 0.04, decor=((60, 650, "pearl"), (980, 170, "capsule")))
users = [(110 + (i % 4) * 100, 300 + (i // 4) * 110) for i in range(12)]
for i, (x, y) in enumerate(users):
    s.art(f"u{i}", i_user(PRIMARY if i % 3 else ACCENT), x, y, 86, 86)
    s.enter(f"u{i}", T("miles") - 0.1 + i * 0.04, "pop", "pop" if i in (0, 6) else None, gain=0.18)
s.text("users-t", "Miles de usuarios similares", 70, 196, 900, 66, 46, 900, INK, cls="v-head")
s.enter("users-t", T("usuarios") - 0.1, "left")
s.card("prod", "Cierto producto", 700, 300, 280, 250, "accent", 30, icon=i_box(), icon_h=140)
s.enter("prod", T("cierto producto") - 0.1, "right", "pop")
for i in range(0, 12, 3):
    s.line(f"to{i}", [(users[i][0] + 86 + (3 - i % 4) * 100 - 100 * (3 - i % 4), users[i][1] + 43), (690, 425)], T("interesándose") + i * 0.04, color=SOFT, width=3, head=False, duration=0.35)
for i, (x, y) in enumerate(users):
    s.art(f"ok{i}", i_check(ACCENT), x + 52, y - 4, 38, 38)
    s.enter(f"ok{i}", T("interesándose") + 0.1 + i * 0.05, "pop", "click-soft" if i % 4 == 0 else None, gain=0.16)
t_e = T("entonces existe")
for i in range(12):
    s.move(f"u{i}", t_e, 0.35, "power2.out", opacity=0.35)
    s.move(f"ok{i}", t_e, 0.35, "power2.out", opacity=0.35)
for i in range(0, 12, 3):
    s.exit(f"to{i}", t_e, "fade")
s.exit("users-t", t_e, "up")
s.text("prob", "Probabilidad de interés", 70, 196, 900, 66, 46, 900, INK, cls="v-head")
s.enter("prob", T("probabilidad", 74) - 0.25, "left")
s.add("you", 630, 560, 100, 100, i_user(HOT))
s.enter("you", T("existe") - 0.1, "pop", "pop")
s.text("you-t", "Tú", 735, 585, 80, 50, 34, 900, HOT_TEXT, style="justify-content:flex-start")
s.enter("you-t", T("existe"), "left")
bar(s, "pb", 110, 640, 480, 22, HOT)
s.enter("pb", T("alta") - 0.1, "fade")
s.enter("pb-fill", T("alta") - 0.1, "fade", rest={"scaleX": 0.02})
s.tw(s.sel("pb-fill"), T("probabilidad", 74), 0.9, "power2.out", scaleX=0.82)
s.sfx(T("probabilidad", 74) + 0.6, "ping")
s.line("p-y", [(840, 556), (720, 590)], T("tú también") - 0.1, color=HOT, width=5, duration=0.35)
s.pulse("you", T("tú también") + 0.2, 1.15, sfx="click-soft")

# 09 — coffee example: never searched an espresso machine, but…
s = Scene("09-cafetera", T("tal vez") - 0.04, T("entonces a ojos") - 0.04, decor=((60, 650, "cube"), (970, 150, "pearl")))
search = (f'<div style="position:absolute;left:22px;top:17px;width:56px;height:56px">{i_search()}</div>'
          f'<div id="{s.id}-q" class="v-text" style="position:absolute;left:96px;top:0;bottom:0;font-size:38px;font-weight:800;justify-content:flex-start;'
          f'clip-path:inset(0 100% 0 0)">cafetera de expreso</div>')
s.add("search", 140, 250, 800, 90, search, "v-card v-pill", f"background:{TINTS['paper']}")
s.enter("search", T("tal vez") + 0.05, "down", "click-soft")
s.set(f"#{s.id}-q", clipPath="inset(0 100% 0 0)")
s.tw(f"#{s.id}-q", T("cafetera") - 0.05, 0.75, "steps(12)", clipPath="inset(0 0% 0 0)")
s.sfx(T("cafetera") - 0.05, "typing", 0.32)
s.card("never", "Nunca buscado", 360, 360, 360, 70, "warm", 32, pill=True, color=ALERT)
s.enter("never", T("expreso") + 0.1, "stamp", "error", gain=0.45, rest={"rotation": -3})
t_p = T("pero sigues")
s.exit("search", t_p - 0.2, "up")
s.exit("never", t_p - 0.2, "up")
s.art("you", i_user(HOT), 90, 380, 170, 170)
s.enter("you", t_p, "pop", "pop")
s.text("you-t", "Tú", 90, 550, 170, 50, 34, 900, HOT_TEXT)
s.enter("you-t", t_p + 0.1, "up")
chips = [("c0", "Café", i_cup(), T("café")), ("c1", "Recetas", i_book(), T("recetas")), ("c2", "Cocina", i_pot(), T("cocina"))]
for n, (key, label, icon, at) in enumerate(chips):
    row_card(s, key, label, icon, 320, 260 + n * 120, 280, 96, "soft" if n == 0 else "glass", 32)
    s.enter(key, at - 0.15, "left", "pop")
    s.line(f"l{n}", [(262, 460), (314, 308 + n * 120)], at - 0.15, color=HOT, width=4, head=False, duration=0.25)
s.pulse("c2", T("like", 84) + 0.05, 1.08, sfx="click")
s.text("sim-t", "Patrón similar", 640, 236, 360, 50, 32, 900, PRIMARY)
s.enter("sim-t", T("patrón") - 0.1, "down")
for i in range(3):
    s.art(f"u{i}", i_user(PRIMARY), 680 + i * 100, 300, 90, 90)
    s.enter(f"u{i}", T("personas", 86) + i * 0.1, "pop", "pop" if i == 0 else None)
    s.art(f"m{i}", i_espresso(), 690 + i * 100, 420, 70, 70)
    s.enter(f"m{i}", T("comprando") - 0.1 + i * 0.08, "pop", "click-soft", gain=0.2)
s.card("bought", "Compraron una", 650, 520, 340, 66, "accent", 28, pill=True)
s.enter("bought", T("comprando") + 0.15, "up", "ping")

# 10 — in the algorithm's eyes you look like a potential customer (ad expands)
s = Scene("10-anuncio", T("entonces a ojos") - 0.04, T("y aquí es donde") - 0.04, decor=((60, 650, "pearl"), (960, 150, "cube")))
s.heading("A ojos del algoritmo", T("ojos") - 0.1, size=48)
s.art("you", i_user(HOT), 150, 320, 190, 190)
s.enter("you", T("entonces a ojos") + 0.05, "pop", "pop")
s.add("ad", 600, 290, 330, 300, f'<div style="position:absolute;left:12px;top:12px;padding:4px 14px;border-radius:999px;background:{ALERT};color:#fff;font:800 20px Montserrat,sans-serif">Anuncio</div>'
      f'<div style="position:absolute;left:85px;top:50px;width:160px;height:160px">{i_espresso()}</div>'
      f'<div class="v-text" style="position:absolute;left:0;right:0;top:214px;height:70px;font-size:28px;font-weight:850">Cafetera de expreso</div>',
      "v-card", f"background:{TINTS['paper']};border:3px solid {HOT}")
s.enter("ad", T("algoritmo") - 0.2, "right", "whoosh-short")
s.move("ad", T("tú también", 93) - 0.1, 0.5, "power3.inOut", x=-170)
s.card("pot", "Cliente potencial", 90, 545, 360, 66, "warm", 30, pill=True, color=ALERT)
s.enter("pot", T("cliente") - 0.05, "stamp", "pop", rest={"rotation": -3})
s.pulse("you", T("potencial"), 1.12, sfx="ping")
# Ad expand: the ad grows over the panel and dissolves into the next section.
t_x = T("potencial") + 0.02
s.move("ad", t_x, 0.45, "power3.in", scale=1.9, y=40, x=-50, opacity=0)
s.live.remove("ad")
s.sfx(t_x + 0.1, "whoosh-short")

# 11 — the curious part: ads for something you hadn't even searched
s = Scene("11-curioso", T("y aquí es donde") - 0.04, T("incluso algo") - 0.04, decor=((60, 650, "cube"), (960, 150, "pearl")))
s.heading("Lo curioso", T("curioso") - 0.1)
s.add("hist", 110, 300, 400, 260, f'<div style="position:absolute;left:24px;top:20px;width:52px;height:52px">{i_search()}</div>'
      f'<div class="v-text" style="position:absolute;left:90px;top:22px;height:50px;font-size:32px;font-weight:900">Historial</div>'
      f'<div style="position:absolute;left:28px;right:28px;top:100px;height:14px;border-radius:7px;background:{TRACK}"></div>'
      f'<div style="position:absolute;left:28px;right:120px;top:134px;height:14px;border-radius:7px;background:{TRACK}"></div>'
      f'<div class="v-text" style="position:absolute;left:0;right:0;top:172px;height:60px;font-size:30px;font-weight:850;color:{ALERT}">Sin búsquedas</div>',
      "v-card", f"background:{TINTS['paper']}")
s.enter("hist", T("ni siquiera", 99) - 0.2, "left", "click-soft")
s.art("phone", i_phone(), 640, 270, 200, 340)
s.enter("phone", T("puede aparecerte") - 0.1, "right", "whoosh-short")
s.card("ad", "Anuncio", 664, 350, 152, 200, "paper", 24, icon=i_espresso(), icon_h=100, color=ALERT, style=f"border:3px solid {HOT}")
s.enter("ad", T("publicidad", 97) - 0.05, "pop", "notification", gain=0.16)
s.pulse("hist", T("buscado") + 0.05, 1.05)

# 12 — something you were only starting to consider… it feels like mind reading
s = Scene("12-mente", T("incluso algo") - 0.04, T("pero no quiere") - 0.02, decor=((60, 650, "pearl"), (960, 150, "capsule")))
s.art("you", i_user(HOT), 130, 470, 160, 160)
s.enter("you", T("incluso algo") + 0.05, "pop", "pop")
s.add("thought", 70, 240, 330, 250, f'<div style="position:absolute;inset:0">{i_thought()}</div>'
      f'<div id="{s.id}-tm" style="position:absolute;left:110px;top:44px;width:120px;height:120px;opacity:.5">{i_espresso()}</div>')
s.enter("thought", T("considerar") - 0.25, "pop", "pop")
s.tw(f"#{s.id}-tm", T("considerar") + 0.3, 0.6, "sine.inOut", opacity=0.9)
s.art("phone", i_phone(), 720, 270, 200, 340)
s.enter("phone", T("perspectiva") - 0.2, "right", "whoosh-short")
s.card("ad", "Anuncio", 744, 350, 152, 200, "paper", 24, icon=i_espresso(), icon_h=100, color=ALERT, style=f"border:3px solid {HOT}")
s.enter("ad", T("perspectiva") + 0.1, "pop", "notification", gain=0.14)
s.add("link", 410, 420, 300, 10, "", "", f"border-top:6px dotted {PRIMARY}")
s.enter("link", T("parece") - 0.1, "wipe")
s.art("qm", i_question(WARM), 510, 350, 100, 100)
s.enter("qm", T("parece") + 0.1, "pop", "pop")
s.text("mind", "¿Leyeron mi mente?", 110, 190, 860, 70, 52, 900, INK)
s.enter("mind", T("leyeron") - 0.1, "down", "sparkle", gain=0.14)

# 13 — not necessarily listening: a prediction (hard cut in)
s = Scene("13-prediccion", T("pero no quiere") - 0.02, T("la plataforma") - 0.04, decor=((60, 650, "cube"), (960, 150, "pearl")))
s.card("mic", "", 400, 260, 280, 260, "glass", icon=i_mic(SOFT), icon_h=200)
s.enter("mic", T("pero no quiere") + 0.05, "pop", "pop")
s.card("nn", "No necesariamente", 290, 540, 500, 70, "soft", 32, pill=True)
s.enter("nn", T("escucharon") - 0.05, "up", "click-soft")
s.dim(["mic"], T("conversaciones", 109), 0.35)
t_pr = T("simplemente")
s.exit("mic", t_pr - 0.45, "shrink")
s.exit("nn", t_pr - 0.45, "down")
s.banner("pred", "Es predicción", t_pr - 0.05, y=320, h=150, size=78)
s.pulse("pred", T("predicción", 112), 1.06)

# 14 — doesn't need to know exactly; only the highest probability of being right
s = Scene("14-probabilidad", T("la plataforma") - 0.04, T("así que") - 0.04, decor=((60, 650, "pearl"), (970, 150, "cube")))
s.heading("No necesita saber exactamente", T("plataforma") - 0.1, size=44)
items = [("Cafetera", i_espresso(), 0.84, HOT), ("Audífonos", i_headphones(), 0.46, PRIMARY), ("Tenis", i_shoe(), 0.31, PRIMARY), ("Libro", i_book(), 0.22, PRIMARY)]
for n, (label, icon, value, color) in enumerate(items):
    y = 290 + n * 92
    row_card(s, f"i{n}", label, icon, 110, y, 330, 80, "glass", 30)
    s.enter(f"i{n}", T("exactamente", 114) + n * 0.12, "left", "pop" if n == 0 else "click-soft", gain=0.2)
    bar(s, f"b{n}", 470, y + 30, 400, 20, color)
    s.enter(f"b{n}", T("exactamente", 114) + 0.1 + n * 0.12, "fade")
    s.enter(f"b{n}-fill", T("exactamente", 114) + 0.1 + n * 0.12, "fade", rest={"scaleX": 0.02})
    s.text(f"q{n}", "?", 890, y + 12, 60, 56, 40, 900, MUTED)
    s.enter(f"q{n}", T("quieres") + n * 0.06, "pop", "click-soft" if n == 0 else None, gain=0.18)
t_pb = T("probabilidad", 118)
s.exit("heading", t_pb - 0.55, "up")
s.exit("heading-line", t_pb - 0.55, "fade")
s.text("h2", "Probabilidad de interés ↑", 110, 196, 860, 72, 48, cls="v-head")
s.enter("h2", t_pb - 0.3, "left")
for n, (label, icon, value, color) in enumerate(items):
    s.exit(f"q{n}", t_pb - 0.2, "fade")
    s.tw(s.sel(f"b{n}-fill"), t_pb + n * 0.08, 0.9, "power2.out", scaleX=value)
s.sfx(t_pb, "whoosh-short")
s.glow("i0", T("acertar"))
s.pulse("i0", T("acertar") + 0.05, 1.06, sfx="ping")
s.art("best", i_check(WARM), 900, 290, 72, 72)
s.enter("best", T("acertar") + 0.15, "pop")

# 15 — the wrong flank: not what you say, but what you do
s = Scene("15-sensor", T("así que") - 0.04, T("y no leen") - 0.04, decor=((60, 650, "cube"), (960, 150, "pearl")))
s.card("mic", "Escuchar", 110, 280, 380, 270, "glass", 34, icon=i_mic(SOFT), icon_h=150)
s.enter("mic", T("así que") + 0.1, "left", "pop")
s.card("flank", "Flanco equivocado", 90, 570, 420, 70, "warm", 30, pill=True, color=ALERT)
s.enter("flank", T("flanco") - 0.05, "stamp", "error", gain=0.4, rest={"rotation": -3})
s.text("dices", "lo que dices", 110, 200, 380, 60, 36, 800, MUTED)
s.enter("dices", T("dices") - 0.2, "down")
s.exit("flank", T("verdadero") - 0.15, "down")
s.card("valor", "El verdadero valor", 340, 580, 400, 68, "soft", 30, pill=True)
s.enter("valor", T("verdadero") + 0.05, "up", "click-soft")
s.dim(["mic"], T("sino") - 0.05, 0.4)
s.card("obs", "Observar", 590, 280, 380, 270, "accent", 34, icon=i_eye(), icon_h=150)
s.enter("obs", T("observar") - 0.3, "right", "pop")
s.text("haces", "lo que haces", 590, 200, 380, 60, 40, 900, PRIMARY)
s.enter("haces", T("observar") + 0.05, "down", "sparkle", gain=0.14)
s.glow("obs", T("observar") + 0.2)

# 16 — priority close: they don't read your mind; they build a profile
s = Scene("16-modelo", T("y no leen") - 0.04, T("y esto apenas") - 0.04, decor=((60, 650, "pearl"), (960, 140, "capsule")))
s.text("l1", "No leen tu mente.", 60, 180, 960, 84, 70, 900, INK)
s.enter("l1", T("leen") - 0.1, "up", "pop")
s.text("l2", "Construyen un perfil.", 60, 270, 960, 80, 62, 900, PRIMARY)
s.enter("l2", T("construyen") - 0.05, "up", "sparkle", gain=0.16)
s.line("l2-line", [(250, 352), (830, 354)], T("construyen") + 0.35, color=ACCENT, width=5, head=False)
# A silhouette made of behaviour dots assembles from scattered signals.
sil = []
for k in range(64):
    a = math.radians(k * 360 / 26)
    if k < 26:
        sil.append((540 + math.cos(a) * 46, 430 + math.sin(a) * 46))
    else:
        u = (k - 26) / 37
        sil.append((540 + (u - 0.5) * 210, 590 - abs(math.sin(u * math.pi)) * 90 + ((k * 13) % 7)))
start_pts = scatter(64, 540, 520, 470, 150, seed=9)
for k, ((sx, sy), (tx, ty)) in enumerate(zip(start_pts, sil)):
    dot(s, f"s{k}", sx, sy, 14, [PRIMARY, ACCENT, HOT, SOFT][k % 4])
    s.enter(f"s{k}", T("construyen") + 0.1 + (k % 16) * 0.025, "pop", "pop" if k == 0 else None)
    s.move(f"s{k}", T("perfil", 133) + 0.1 + (k % 9) * 0.04, 0.8, "power3.inOut", x=round(tx - sx), y=round(ty - sy))
s.sfx(T("perfil", 133) + 0.2, "whoosh-short")
s.card("enough", "Y con eso es suficiente", 280, 620, 520, 60, "glass", 28, pill=True)
s.enter("enough", T("con eso") - 0.1, "up", "ping")

# 17 — CTA: barely scratching the surface; next: fingerprinting
s = Scene("17-cta", T("y esto apenas") - 0.04, min(DURATION, OUTRO_START + 0.6), decor=((60, 650, "cube"), (960, 150, "pearl")))
s.art("ice", i_iceberg(), 240, 280, 600, 400)
s.enter("ice", T("apenas", 137) - 0.1, "up", "whoosh-short")
s.text("surface", "Apenas la superficie", 110, 196, 860, 70, 50, 900, INK, cls="v-head")
s.enter("surface", T("rasca") - 0.1, "left")
s.card("track", "Seguimiento en internet", 300, 610, 480, 64, "soft", 28, pill=True)
s.enter("track", T("seguimiento") - 0.1, "up", "pop")
t_q = T("si quieres")
for key in ("ice", "surface", "track"):
    s.exit(key, t_q - 0.25, "up")
s.text("next", "Próximo video", 110, 196, 600, 66, 46, 900, INK, cls="v-head")
s.enter("next", T("otro video") - 0.1, "left", "click-soft")
s.add("browser", 340, 300, 400, 300, f'<div style="position:absolute;inset:0">{i_browser()}</div>'
      f'<div style="position:absolute;left:130px;top:100px;width:140px;height:140px">{i_fingerprint()}</div>')
s.enter("browser", T("indaguemos") - 0.1, "pop", "pop")
s.card("fp", "Fingerprinting", 330, 610, 420, 70, "accent", 34, pill=True)
s.enter("fp", T("fingerprinting") - 0.1, "up", "sparkle", gain=0.16)
attrs = [("Pantalla", 70, 300), ("Navegador", 760, 300), ("Sistema", 70, 410), ("Fuentes", 760, 410), ("GPU", 70, 520)]
for n, (label, x, y) in enumerate(attrs):
    pill(s, f"a{n}", label, x, y, 250, 64, "glass", 28)
    s.enter(f"a{n}", T("fingerprinting") + 0.15 + n * 0.12, "left" if x < 500 else "right", "click-soft" if n % 2 == 0 else None, gain=0.2)
s.card("com", "Coméntalo", 760, 520, 250, 70, "soft", 30, pill=True)
s.enter("com", T("comentarios") - 0.15, "pop", "pop")
