#!/usr/bin/env python3
"""Redesigned auth pages for the self-hosted device-code flow (frontend-design).

Pages: entry (manual code fallback), confirm (GitCode-bound / manual), error,
success, denied. One shared stylesheet; server-rendered inline, no JS deps.
"""
import html as _html


def esc(text: str) -> str:
    return _html.escape(text, quote=True)


_STYLES = """
  :root {
    --ink: #17183a;
    --ink-soft: #4c4e6d;
    --paper: #f7f7fb;
    --card: #ffffff;
    --line: #dfe0ec;
    --brand: #2f54eb;
    --brand-ink: #ffffff;
    --brand-soft: #eef1fe;
    --ok: #1f7a4d;
    --ok-soft: #e9f5ee;
    --warn: #b42318;
    --warn-soft: #fdeded;
    --code-bg: #16182f;
    --code-ink: #e8ecff;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; }
  body {
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans SC",
      system-ui, sans-serif;
    background: var(--paper);
    color: var(--ink);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 24px;
    -webkit-font-smoothing: antialiased;
  }
  .card {
    width: 100%;
    max-width: 400px;
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 36px 32px 30px;
    box-shadow: 0 1px 2px rgba(23, 24, 58, 0.04);
  }
  .brandline {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 28px;
  }
  .brandline .mark {
    width: 34px; height: 34px;
    border-radius: 9px;
    background: var(--brand);
    color: var(--brand-ink);
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 11px;
    letter-spacing: 0.5px;
    text-indent: 0.5px;
  }
  .brandline .name { font-size: 14px; font-weight: 600; color: var(--ink-soft); }
  h1 { font-size: 21px; font-weight: 700; letter-spacing: -0.2px; margin-bottom: 10px; }
  .sub { font-size: 14px; line-height: 1.65; color: var(--ink-soft); margin-bottom: 26px; }
  .sub b { color: var(--ink); font-weight: 600; }
  .code {
    font-family: ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, monospace;
    background: var(--code-bg);
    color: var(--code-ink);
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
    font-size: 26px;
    font-weight: 600;
    letter-spacing: 0.28em;
    text-indent: 0.28em;
    margin-bottom: 26px;
    user-select: all;
  }
  .identity {
    display: flex;
    align-items: center;
    gap: 12px;
    background: var(--brand-soft);
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 26px;
  }
  .identity .avatar {
    width: 36px; height: 36px;
    border-radius: 50%;
    background: var(--brand);
    color: var(--brand-ink);
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; font-weight: 700;
    flex: none;
  }
  .identity .who { font-size: 14px; line-height: 1.5; }
  .identity .who b { font-size: 15px; font-weight: 600; }
  .identity .who span { color: var(--ink-soft); }
  .actions { display: flex; gap: 12px; }
  .actions button, .actions a.button {
    flex: 1;
    font: inherit;
    font-size: 15px;
    font-weight: 600;
    border-radius: 10px;
    padding: 12px 0;
    cursor: pointer;
    text-align: center;
    text-decoration: none;
    transition: background 0.15s ease, border-color 0.15s ease;
  }
  .actions button:focus-visible, input:focus-visible, a:focus-visible {
    outline: 2px solid var(--brand);
    outline-offset: 2px;
  }
  .primary { background: var(--brand); color: var(--brand-ink); border: 1px solid var(--brand); }
  .primary:hover { background: #2748c8; }
  .ghost { background: var(--card); color: var(--ink); border: 1px solid var(--line); }
  .ghost:hover { border-color: #b9bbcd; }
  input[type="text"], input[name="user_code"], input[name="username"] {
    width: 100%;
    font: inherit;
    font-size: 15px;
    padding: 12px 14px;
    border: 1px solid var(--line);
    border-radius: 10px;
    background: var(--card);
    color: var(--ink);
  }
  input::placeholder { color: #9a9cb5; }
  .field { margin-bottom: 18px; }
  .field label { display: block; font-size: 13px; color: var(--ink-soft); margin-bottom: 6px; }
  .status-icon {
    width: 46px; height: 46px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 18px;
  }
  .status-icon svg { width: 22px; height: 22px; }
  .ok .status-icon { background: var(--ok-soft); }
  .ok .status-icon svg { stroke: var(--ok); }
  .deny .status-icon { background: var(--warn-soft); }
  .deny .status-icon svg { stroke: var(--warn); }
  .center { text-align: center; }
  .link { color: var(--brand); text-decoration: none; font-size: 14px; }
  .link:hover { text-decoration: underline; }
  .footnote {
    margin-top: 22px;
    padding-top: 16px;
    border-top: 1px solid var(--line);
    font-size: 12.5px;
    color: var(--ink-soft);
    text-align: center;
  }
  .footnote a { color: inherit; }
  @media (max-width: 420px) {
    .card { padding: 28px 22px 24px; border-radius: 12px; }
    .code { font-size: 22px; }
  }
"""


def _page(title: str, body: str) -> str:
    return (
        "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{esc(title)}</title><style>{_STYLES}</style></head>"
        f"<body>{body}</body></html>"
    )


def _brandline() -> str:
    return (
        "<div class='brandline'>"
        "<div class='mark'>CANN</div>"
        "<div class='name'>cannbot-knowledge 知识库</div>"
        "</div>"
    )


def activation_page(
    prefill: str, gitcode_available: bool, path_prefix: str = ""
) -> str:
    """Manual code entry (fallback when no GitCode app is configured)."""
    link = ""
    if gitcode_available:
        link = (
            "<p class='footnote'>终端链接通常自动跳转 GitCode 登录；"
            "如需手动登录，<a class='link' href='" + path_prefix + "/oauth/gitcode/login?state="
            + esc(prefill)
            + "'>使用 GitCode 账号登录</a></p>"
        )
    return _page(
        "设备授权 - cannbot-knowledge",
        "<div class='card'>"
        + _brandline()
        + "<h1>输入设备代码</h1>"
        "<p class='sub'>代码显示在你发起授权的终端里，由 4 位字母数字组成。</p>"
        "<form method='post'>"
        "<div class='field'>"
        "<label for='user_code'>设备代码</label>"
        "<input id='user_code' name='user_code' value='"
        + esc(prefill)
        + "' placeholder='XXXX-XXXX' autocomplete='off' autocapitalize='characters' "
        "spellcheck='false' required>"
        "</div>"
        "<div class='actions'><button class='primary' type='submit'>下一步</button></div>"
        "</form>"
        + link
        + "</div>",
    )


def authorize_page(
    code: str,
    signed_in: str,
    gitcode_available: bool,
    session_token: str = "",
    path_prefix: str = "",
) -> str:
    """Consent page for the self-hosted authorization-code grant.

    With GitCode configured the ONLY action is the GitCode login button
    (identity lands on the reentry consent page); the manual username
    fallback appears solely when no GitCode application is configured.
    The GitCode-verified identity travels as a server-side binding token
    (st), never as a username form field.
    """
    if signed_in:
        first = signed_in[:1].upper()
        identity = (
            "<div class='identity'>"
            f"<div class='avatar'>{esc(first)}</div>"
            "<div class='who'>"
            f"<b>{esc(signed_in)}</b><br>"
            "<span>GitCode 账号</span>"
            "</div>"
            "</div>"
        )
        actions = (
            "<div class='actions'>"
            "<button class='primary' name='action' value='allow'>允许访问</button>"
            "<button class='ghost' name='action' value='deny'>拒绝</button>"
            "</div>"
        )
        sub = "一个客户端正在请求访问知识库。确认是你本人在操作后，点击允许。"
    elif gitcode_available:
        identity = ""
        actions = (
            "<div class='actions'>"
            "<button class='primary' name='action' value='gitcode'>"
            "使用 GitCode 账号登录</button>"
            "</div>"
        )
        sub = "一个客户端正在请求访问知识库。请使用 GitCode 账号登录以确认身份。"
    else:
        identity = (
            "<div class='field'>"
            "<label for='username'>用户名</label>"
            "<input id='username' name='username' placeholder='你的用户名' required>"
            "</div>"
        )
        actions = (
            "<div class='actions'>"
            "<button class='primary' name='action' value='allow'>允许访问</button>"
            "<button class='ghost' name='action' value='deny'>拒绝</button>"
            "</div>"
        )
        sub = "一个客户端正在请求访问知识库。"
    hidden = f"<input type='hidden' name='code' value='{esc(code)}'>"
    if signed_in and session_token:
        hidden += f"<input type='hidden' name='st' value='{esc(session_token)}'>"
    return _page(
        "确认授权 - cannbot-knowledge",
        "<div class='card'>"
        + _brandline()
        + "<h1>确认授权</h1>"
        + f"<p class='sub'>{sub}</p>"
        + f"<form method='post' action='{path_prefix}/oauth/authorize/confirm'>"
        + hidden
        + identity
        + actions
        + "</form>"
        + "</div>",
    )


def confirm_page(
    user_code: str,
    signed_in: str,
    gitcode_available: bool,
    session_token: str = "",
    path_prefix: str = "",
) -> str:
    """Confirmation: GitCode-bound identity or manual username fallback.

    With GitCode configured the identity shown is the server-stored
    verified one and the form carries only the binding token (st) —
    never a username field. Manual username entry exists ONLY when no
    GitCode application is configured (trusted-network bootstrap).
    """
    if signed_in:
        first = signed_in[:1].upper()
        identity = (
            "<div class='identity'>"
            f"<div class='avatar'>{esc(first)}</div>"
            "<div class='who'>"
            f"<b>{esc(signed_in)}</b><br>"
            "<span>GitCode 账号</span>"
            "</div>"
            "</div>"
        )
        heading = "确认授权"
        sub = "一台设备正在请求访问知识库。确认是你本人在操作后，点击允许。"
    elif gitcode_available:
        identity = (
            "<p class='footnote' style='border:0;padding:0;text-align:left'>"
            "尚未通过 GitCode 登录。请<a class='link' href='" + path_prefix + "/oauth/gitcode/login?state="
            + esc(user_code)
            + "'>使用 GitCode 账号登录</a>后确认。</p>"
        )
        heading = "确认授权"
        sub = "一台设备正在请求访问知识库。"
    else:
        identity = (
            "<div class='field'>"
            "<label for='username'>用户名</label>"
            "<input id='username' name='username' placeholder='你的用户名' required>"
            "</div>"
        )
        heading = "确认授权"
        sub = "一台设备正在请求访问知识库。"
    hidden = f"<input type='hidden' name='user_code' value='{esc(user_code)}'>"
    if signed_in and session_token:
        hidden += f"<input type='hidden' name='st' value='{esc(session_token)}'>"
    return _page(
        "确认授权 - cannbot-knowledge",
        "<div class='card'>"
        + _brandline()
        + f"<h1>{heading}</h1>"
        + f"<p class='sub'>{sub}</p>"
        + f"<div class='code'>{esc(user_code)}</div>"
        + "<form method='post'>"
        + hidden
        + identity
        + "<div class='actions'>"
        "<button class='primary' name='action' value='allow'>允许访问</button>"
        "<button class='ghost' name='action' value='deny'>拒绝</button>"
        "</div>"
        "</form>"
        + "</div>",
    )


def success_page(username: str) -> str:
    return _page(
        "授权成功 - cannbot-knowledge",
        "<div class='card ok center'>"
        + _brandline()
        + "<div class='status-icon'><svg viewBox='0 0 24 24' fill='none' "
        "stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'>"
        "<polyline points='4.5 12.5 10 18 19.5 7.5'/></svg></div>"
        "<h1>授权成功</h1>"
        f"<p class='sub'><b>{esc(username)}</b> 已允许这台设备访问知识库。</p>"
        "<p class='sub'>回到终端即可继续，本页面可以关闭。</p>"
        "</div>",
    )


def denied_page() -> str:
    return _page(
        "已拒绝 - cannbot-knowledge",
        "<div class='card deny center'>"
        + _brandline()
        + "<div class='status-icon'><svg viewBox='0 0 24 24' fill='none' "
        "stroke-width='2.4' stroke-linecap='round'>"
        "<line x1='6' y1='6' x2='18' y2='18'/>"
        "<line x1='18' y1='6' x2='6' y2='18'/></svg></div>"
        "<h1>已拒绝授权</h1>"
        "<p class='sub'>这台设备没有获得访问权限。</p>"
        "<p class='sub'>如果是误操作，回到终端重新发起授权即可。</p>"
        "</div>",
    )


def error_page(message: str, retry_url: str | None = None) -> str:
    retry = ""
    if retry_url:
        retry = (
            "<div class='actions' style='margin-top:22px'>"
            f"<a class='button primary' href='{esc(retry_url)}'>重试</a>"
            "</div>"
        )
    return _page(
        "无法完成授权 - cannbot-knowledge",
        "<div class='card deny'>"
        + _brandline()
        + "<h1>无法完成授权</h1>"
        f"<p class='sub'>{esc(message)}</p>"
        + retry
        + "<p class='footnote'>问题持续出现时，联系知识库维护者。</p>"
        "</div>",
    )


if __name__ == "__main__":
    # Render previews to /tmp for a quick browser check.
    import pathlib

    out = pathlib.Path("/tmp/auth_pages")
    out.mkdir(exist_ok=True)
    (out / "entry.html").write_text(activation_page("", True))
    (out / "confirm.html").write_text(confirm_page("NJ5P-DC6W", "demo-user", True))
    (out / "confirm-manual.html").write_text(confirm_page("AB2C-3DEF", "", False))
    (out / "success.html").write_text(success_page("demo-user"))
    (out / "denied.html").write_text(denied_page())
    (out / "error.html").write_text(error_page("登录会话已过期。", "/activate"))
    print("previews at", out)
