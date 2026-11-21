from html import escape

BULLETS = (
    "Task summaries with flagged and warned counts — and the reasons behind them",
    "Campaign delivery and quality, one row per campaign",
    "Team performance, limited to the people and campaigns you already see",
    "Generate a campaign report on request, emailed to your own address",
)

# The tool groups this server exposes, so the page says what is actually
# being connected rather than describing the product.
TOOL_GROUPS = (
    ("4", "Task tools"),
    ("2", "Campaign tools"),
    ("5", "People tools"),
    ("2", "Report tools"),
)

_STYLE = """
/* Light only: this is a branded page, not a themed app surface, and
   color-scheme keeps the browser from auto-darkening the inputs. */
:root {
  color-scheme: light;
  --ink: #16181d; --ink-soft: #5b6472; --line: #e6e8ec;
  --accent: #ec702e; --accent-ink: #ffffff;
  --panel: #f4f5f7; --card: #ffffff; --bad: #b42318;
}
* { box-sizing: border-box; }
html, body { height: 100%; }
body {
  margin: 0; color: var(--ink); background: var(--card);
  font: 14px/1.55 "Inter", ui-sans-serif, system-ui, -apple-system, "Segoe UI",
        Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}
.split { display: grid; grid-template-columns: 1fr 1fr; min-height: 100vh; }

/* ---------------------------------------------------------------- pitch -- */
.pitch {
  position: relative; display: flex; flex-direction: column;
  padding: 36px 48px 32px; overflow: hidden;
}
/* The faint dot grid, drawn rather than shipped as an image. */
.pitch::before {
  content: ""; position: absolute; inset: 0; z-index: 0;
  background-image: radial-gradient(circle, #e9ebef 1.1px, transparent 1.1px);
  background-size: 22px 22px;
  -webkit-mask-image: linear-gradient(to bottom, #000 0%, transparent 72%);
          mask-image: linear-gradient(to bottom, #000 0%, transparent 72%);
}
.pitch > * { position: relative; z-index: 1; }

/* align-self, because .pitch is a column flexbox and the default stretch
   would blow the mark out to the full column width. */
.logo { height: 34px; width: auto; display: block; align-self: flex-start; }

.eyebrow {
  display: flex; align-items: center; gap: 10px; margin: 32px 0 14px;
  font-size: 11px; font-weight: 800; letter-spacing: 0.13em;
  text-transform: uppercase; color: var(--accent);
}
.eyebrow::before {
  content: ""; width: 24px; height: 2px; background: var(--accent); flex: none;
}

h1 {
  margin: 0; max-width: 17ch; font-size: clamp(26px, 2.7vw, 38px);
  line-height: 1.14; letter-spacing: -0.026em; font-weight: 800;
}
h1 em { font-style: normal; color: var(--accent); }

.lede {
  margin: 16px 0 0; max-width: 46ch; color: var(--ink-soft); font-size: 13.5px;
}

.points { margin: 22px 0 0; padding: 0; list-style: none; max-width: 48ch; }
.points li {
  display: grid; grid-template-columns: 18px 1fr; gap: 10px;
  margin-bottom: 10px; font-size: 12.5px; font-weight: 600;
}
.tick {
  width: 18px; height: 18px; border-radius: 50%; background: #fdeadf;
  color: var(--accent); display: grid; place-items: center;
  font-size: 10px; font-weight: 800; margin-top: 1px;
}

.stats {
  display: flex; flex-wrap: wrap; gap: 34px; margin: auto 0 0; padding-top: 28px;
}
.stats .n { font-size: 19px; font-weight: 800; letter-spacing: -0.02em; color: var(--accent); }
.stats .k {
  margin-top: 2px; font-size: 9px; font-weight: 700; letter-spacing: 0.09em;
  text-transform: uppercase; color: var(--ink-soft);
}

/* ---------------------------------------------------------------- panel -- */
.panel {
  background: var(--panel); display: grid; place-items: center; padding: 40px 32px;
}
/* The pitch carries the brand on desktop; on a phone it is hidden, so the
   card has to say whose sign-in this is. */
.panel-brand { display: none; margin-bottom: 26px; }
.card {
  width: 100%; max-width: 384px; background: var(--card); border-radius: 14px;
  padding: 30px 28px 26px; box-shadow: 0 1px 2px rgba(16,24,40,.04),
                                       0 12px 34px rgba(16,24,40,.07);
}
h2 { margin: 0 0 18px; font-size: 19px; font-weight: 800; letter-spacing: -0.015em; }
h2 + .sub { margin: -11px 0 18px; color: var(--ink-soft); font-size: 12.5px; }

label {
  display: block; margin-bottom: 7px; font-size: 12px; font-weight: 700;
}
input {
  width: 100%; padding: 11px 13px; font: inherit; font-size: 13.5px; color: var(--ink);
  background: var(--card); border: 1px solid var(--line); border-radius: 9px;
}
input::placeholder { color: #a8b0bc; }
input:focus { outline: 2px solid var(--accent); outline-offset: 1px; border-color: transparent; }
input.otp { letter-spacing: 0.4em; text-align: center; font-size: 19px; font-weight: 700; }

button {
  width: 100%; margin-top: 16px; padding: 11px 13px; font: inherit;
  font-size: 13.5px; font-weight: 700; color: var(--accent-ink);
  background: var(--accent); border: 0; border-radius: 9px; cursor: pointer;
}
button:hover { background: #d8631f; }
button:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }

.legal, .alt { margin: 12px 0 0; font-size: 11px; color: var(--ink-soft); }
.readonly {
  margin: 14px 0 0; font-size: 11px; font-weight: 600; color: var(--ink-soft);
}
.legal a, .alt a { color: var(--accent); font-weight: 700; text-decoration: none; }
.legal a:hover, .alt a:hover { text-decoration: underline; }

.error {
  margin: 0 0 16px; padding: 10px 12px; font-size: 12px; font-weight: 600;
  color: var(--bad); background: #fef3f2; border: 1px solid #fecdca;
  border-radius: 9px;
}

/* ----------------------------------------------------------- responsive -- */
@media (max-width: 900px) {
  .split { grid-template-columns: 1fr; }
  /* The pitch is decoration; on a phone the form is the whole job. */
  .pitch { display: none; }
  .panel {
    min-height: 100%; background: var(--card); padding: 30px 22px;
    place-items: start center; align-content: center;
  }
  .card { box-shadow: none; padding: 0; max-width: 420px; }
  .panel-brand { display: block; }
}
"""


def _logo() -> str:
    return '<img class="logo" src="/login/logo.png" alt="gOGig" width="387" height="160">'


def _pitch() -> str:
    bullets = "".join(
        f'<li><span class="tick" aria-hidden="true">&#10003;</span>'
        f"<span>{escape(text)}</span></li>"
        for text in BULLETS
    )
    stats = "".join(
        f'<div><div class="n">{escape(number)}</div>'
        f'<div class="k">{escape(label)}</div></div>'
        for number, label in TOOL_GROUPS
    )
    return f"""<section class="pitch">
      {_logo()}
      <p class="eyebrow">Model Context Protocol</p>
      <h1>Your gOGig campaigns, <em>inside your AI assistant</em></h1>
      <p class="lede">Connecting lets the app ask gOGig about your tasks,
        campaigns and team in plain language — scoped to exactly what your
        account can already see, and nothing more.</p>
      <ul class="points">{bullets}</ul>
      <div class="stats">{stats}</div>
      <p class="readonly">Mostly read-only — the one exception is generating a
        report on request, which queues a job and emails the result to your
        own account address. Nothing here changes or deletes your data.</p>
    </section>"""


def _page(title: str, card: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{escape(title)}</title>
<style>{_STYLE}</style>
</head>
<body>
  <main class="split">
    {_pitch()}
    <section class="panel"><div class="card">
      <div class="panel-brand">{_logo()}</div>
      {card}
    </div></section>
  </main>
</body>
</html>"""


def _error(message: str | None) -> str:
    return f'<p class="error">{escape(message)}</p>' if message else ""


def identifier_form(txn: str, error: str | None = None) -> str:
    card = f"""<h2>Sign in to gOGig MCP</h2>
      {_error(error)}
      <form method="post" action="/login">
        <input type="hidden" name="txn" value="{escape(txn)}">
        <label for="identifier">Mobile number or email</label>
        <input id="identifier" name="identifier" autocomplete="username" autofocus
               required placeholder="98765 43210 or you@company.com">
        <button type="submit">Continue</button>
      </form>
      <p class="legal">We'll send you a one-time code. By continuing you agree to
        our <a href="https://gogig.in/terms-conditions/" target="_blank" rel="noopener">Terms
        &amp; Conditions</a> and <a href="https://gogig.in/privacy-policy/" target="_blank"
        rel="noopener">Privacy Policy</a>.</p>"""
    return _page("Sign in to gOGig MCP", card)


def otp_form(
    txn: str,
    identifier: str,
    channel: str,
    error: str | None = None,
) -> str:
    where = "your phone" if channel == "phone" else "your email"
    card = f"""<h2>Enter your code</h2>
      <p class="sub">Sent to {escape(where)} &middot; {escape(identifier)}</p>
      {_error(error)}
      <form method="post" action="/login/verify">
        <input type="hidden" name="txn" value="{escape(txn)}">
        <label for="otp">One-time code</label>
        <input id="otp" name="otp" class="otp" inputmode="numeric" pattern="[0-9]*"
               autocomplete="one-time-code" autofocus required maxlength="8">
        <button type="submit">Verify &amp; sign in</button>
      </form>
      <p class="alt"><a href="/login?txn={escape(txn)}">Use a different number</a></p>"""
    return _page("Enter your code", card)


def expired_page() -> str:
    card = """<h2>This sign-in expired</h2>
      <p class="sub">For your security the link is only good for a few minutes.</p>
      <p class="legal">Close this window and connect again from the app you
        were signing in to.</p>"""
    return _page("Sign-in expired", card)
