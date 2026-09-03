# -*- coding: utf-8 -*-
"""
歯科ドクターズ — 静的サイトビルダー

data/ の JSON を読んで docs/ に HTML を書き出す。標準ライブラリだけで動く。
    python build.py

出力先 docs/ は GitHub Pages がそのまま配信する。
独自ドメインに移すときは data/site.json の base_url を書き換えて再ビルドするだけ。
"""
import json
import os
import re
import shutil
from datetime import date
from html import escape
from urllib.parse import urlparse, quote

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "docs")

DAY_EN = {"月": "Monday", "火": "Tuesday", "水": "Wednesday",
          "木": "Thursday", "金": "Friday", "土": "Saturday", "日": "Sunday"}


# ---------------------------------------------------------------- 読み込み

def load():
    site = json.load(open(os.path.join(DATA, "site.json"), encoding="utf-8"))
    features = json.load(open(os.path.join(DATA, "features.json"), encoding="utf-8"))
    cdir = os.path.join(DATA, "clinics")
    clinics = []
    for fn in sorted(os.listdir(cdir)):
        if not fn.endswith(".json"):
            continue
        c = json.load(open(os.path.join(cdir, fn), encoding="utf-8"))
        if c.get("published"):
            clinics.append(c)
    site["base_path"] = urlparse(site["base_url"]).path.rstrip("/")
    return site, features, clinics


SITE, FEATURES, CLINICS = load()
FEAT = {f["key"]: f for f in FEATURES}
PAGES = []  # sitemap 用


def u(path):
    """サイト内リンク。base_path を前置きする。"""
    return (SITE["base_path"] + path) or "/"


def e(s):
    return escape(str(s), quote=True)


def obf(addr):
    """メールアドレスを数値文字参照にする。画面では普通に読めるが、
    ソースを正規表現でなめる収集業者には拾われない。"""
    body = "".join(f"&#{ord(ch)};" for ch in addr)
    href = "".join(f"&#{ord(ch)};" for ch in "mailto:" + addr)
    return f'<a href="{href}">{body}</a>'


# ---------------------------------------------------------------- 共通の枠

def layout(path, title, desc, body, jsonld=None, breadcrumb=None):
    """1ページ書き出す。path は '/clinic/xxx/' の形。"""
    PAGES.append(path)
    full_title = title if title.endswith(SITE["name"]) else f"{title}｜{SITE['name']}"
    canonical = SITE["base_url"] + path

    bc = ""
    if breadcrumb:
        parts = []
        for label, href in breadcrumb[:-1]:
            parts.append(f'<a href="{e(href)}">{e(label)}</a>')
        parts.append(f'<span aria-current="page">{e(breadcrumb[-1][0])}</span>')
        bc = ('<div class="wrap"><nav class="bc">'
              + '<span>›</span>'.join(parts) + '</nav></div>')

    ld = ""
    for obj in (jsonld or []):
        ld += ('<script type="application/ld+json">'
               + json.dumps(obj, ensure_ascii=False) + '</script>')

    html = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:site_name" content="{e(SITE['name'])}">
<link rel="stylesheet" href="{u('/assets/style.css')}">
{ld}
</head>
<body>
<header class="hd"><div class="hd-in">
  <a class="logo" href="{u('/')}">歯科<span>ドクターズ</span></a>
  <span class="hd-tag">{e(SITE['tagline'])}</span>
  <nav class="hd-nav">
    <a href="{u('/tokyo/')}">エリアから探す</a>
    <a href="{u('/feature/')}">こだわりから探す</a>
    <a href="{u('/about/')}">このサイトについて</a>
    <a class="hd-cta" href="{u('/entry/')}">掲載をご希望の医院様へ</a>
  </nav>
</div></header>
{bc}
{body}
<footer><div class="wrap">
  <div class="fnav">
    <a href="{u('/')}">トップ</a>
    <a href="{u('/tokyo/')}">エリアから探す</a>
    <a href="{u('/feature/')}">こだわりから探す</a>
    <a href="{u('/about/')}">このサイトについて</a>
    <a href="{u('/entry/')}">掲載のご案内</a>
    <a href="{u('/policy/')}">掲載方針・免責事項</a>
  </div>
  <div class="fine">
    {e(SITE['name'])}は、全国の歯科医院を院長インタビューで紹介する情報サイトです。<br>
    掲載内容は各医院からご提供いただいた情報および取材に基づくもので、
    治療の効果を保証するものではありません。受診の判断は必ず医療機関にご相談ください。<br>
    運営：{e(SITE['operator'])}／お問い合わせ：{obf(SITE['contact_email'])}<br>
    &copy; {date.today().year} {e(SITE['name'])}
  </div>
</div></footer>
</body>
</html>
"""
    dest = os.path.join(OUT, path.strip("/"), "index.html") if path != "/" \
        else os.path.join(OUT, "index.html")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8", newline="\n").write(html)


# ---------------------------------------------------------------- 部品

def clinic_card(c):
    tags = "".join(f'<span class="tag">{e(FEAT[k]["label"])}</span>'
                   for k in c.get("features", [])[:5] if k in FEAT)
    badge = '<span class="badge">インタビュー掲載</span>' if c.get("plan") == "interview" else ""
    ac = c["access"][0]
    return f"""<article class="card">
  {badge}
  <h3><a href="{u('/clinic/' + c['slug'] + '/')}">{e(c['name'])}</a></h3>
  <p class="meta">{e(c['prefecture'])}{e(c['city'])}／{e(ac['station'])}から徒歩{ac['minutes']}分</p>
  <p class="lead">{e(c.get('lead',''))}</p>
  <div class="tags">{tags}</div>
</article>"""


def cards(cs):
    if not cs:
        return ('<p class="sec-note">現在この条件で掲載中の医院はありません。'
                f'<a href="{u("/entry/")}">掲載をご希望の医院様はこちら</a></p>')
    return '<div class="grid">' + "".join(clinic_card(c) for c in cs) + '</div>'


def hours_rows(c):
    out = []
    for h in c["hours"]:
        out.append(f"<tr><th>{e(h['days'])}</th><td>{e(' / '.join(h['slots']))}</td></tr>")
    out.append(f"<tr><th>休診日</th><td>{e(c['closed'])}</td></tr>")
    return "".join(out)


def opening_spec(c):
    spec = []
    for h in c["hours"]:
        days = [DAY_EN[d] for d in re.split(r"[・,、]", h["days"]) if d in DAY_EN]
        for slot in h["slots"]:
            o, cl = re.split(r"[〜~-]", slot)
            spec.append({
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": days,
                "opens": o.strip(),
                "closes": cl.strip(),
            })
    return spec


# ---------------------------------------------------------------- 各ページ

def page_top():
    prefs = {}
    for c in CLINICS:
        prefs.setdefault((c["pref_slug"], c["prefecture"]), []).append(c)

    pref_links = "".join(
        f'<a href="{u("/" + s + "/")}">{e(n)}<span class="n">{len(cs)}件</span></a>'
        for (s, n), cs in sorted(prefs.items())
    ) or '<p class="sec-note">準備中です。</p>'

    used = sorted({k for c in CLINICS for k in c.get("features", [])},
                  key=lambda k: [f["key"] for f in FEATURES].index(k))
    feat_chips = "".join(
        f'<a class="chip" href="{u("/feature/" + k + "/")}">{e(FEAT[k]["label"])}</a>'
        for k in used if k in FEAT)

    # 掲載数が少ないうちは件数を出さない（信頼性を損なうため）。10件を超えたら自動で出る
    if len(CLINICS) >= 10:
        stat_block = f"""<div class="stat">
    <div><b>{len(CLINICS)}</b>掲載医院</div>
    <div><b>{len(prefs)}</b>都道府県</div>
    <div><b>0円</b>基本掲載料</div>
  </div>"""
    else:
        stat_block = """<div class="stat">
    <div><b>0円</b>基本掲載料</div>
    <div><b>公開前確認</b>医院様のご承認後に掲載</div>
    <div><b>口コミなし</b>医療広告ガイドライン準拠</div>
  </div>"""

    body = f"""
<div class="hero"><div class="wrap">
  <h1>歯科医師の考え方から、<br>歯医者を選ぶ。</h1>
  <p>診療時間とアクセスだけでは、自分に合う歯医者かどうかは分かりません。{e(SITE['name'])}は、
     院長へのインタビューを通じて「どんな考えで治療をしている先生なのか」まで分かるようにした情報サイトです。</p>
  <div class="searchbox">
    <h2>こだわりから探す</h2>
    <div class="chips">{feat_chips}</div>
  </div>
  {stat_block}
</div></div>

<main><div class="wrap">
  <section>
    <h2 class="sec">エリアから探す</h2>
    <p class="sec-note">お住まい・お勤め先の近くから探せます。</p>
    <div class="linklist">{pref_links}</div>
  </section>

  <section>
    <h2 class="sec">新着のインタビュー</h2>
    <p class="sec-note">院長ご本人にお話を伺い、確認をいただいたうえで掲載しています。</p>
    {cards(CLINICS[:6])}
  </section>

  <section>
    <h2 class="sec">歯科医院の皆さまへ</h2>
    <p class="sec-note">基本情報の掲載は無料です。インタビュー記事の作成もお引き受けしています。</p>
    <div class="panel">
      <p style="margin-top:0">「設備や料金では違いが伝わらない」「初診の方に、うちの考え方を先に知ってほしい」——
      そうした医院様のための掲載枠です。取材は{e(SITE['name'])}が行い、
      公開前に必ず医院様のご確認をいただきます。</p>
      <p style="margin-bottom:0"><a href="{u('/entry/')}">掲載のご案内を見る →</a></p>
    </div>
  </section>
</div></main>"""

    layout("/", f"{SITE['name']}｜{SITE['tagline']}", SITE["description"], body,
           jsonld=[{
               "@context": "https://schema.org",
               "@type": "WebSite",
               "name": SITE["name"],
               "url": SITE["base_url"] + "/",
               "description": SITE["description"],
           }])


def page_pref(pref_slug, pref_name, cs):
    cities = {}
    for c in cs:
        cities.setdefault((c["city_slug"], c["city"]), []).append(c)
    city_links = "".join(
        f'<a href="{u("/" + pref_slug + "/" + s + "/")}">{e(n)}<span class="n">{len(x)}件</span></a>'
        for (s, n), x in sorted(cities.items()))

    body = f"""
<div class="ph"><div class="wrap">
  <h1>{e(pref_name)}の歯科医院</h1>
  <p class="sub">{len(cs)}件を掲載しています。市区町村から絞り込めます。</p>
</div></div>
<main><div class="wrap">
  <section>
    <h2 class="sec">市区町村から探す</h2>
    <div class="linklist">{city_links}</div>
  </section>
  <section>
    <h2 class="sec">{e(pref_name)}の掲載医院</h2>
    {cards(cs)}
  </section>
</div></main>"""
    layout(f"/{pref_slug}/", f"{pref_name}の歯科医院",
           f"{pref_name}の歯科医院を院長インタビューで紹介しています。市区町村・診療内容から探せます。",
           body, breadcrumb=[(SITE["name"], u("/")), (pref_name, "")])


def page_city(pref_slug, pref_name, city_slug, city_name, cs):
    stations = sorted({a["station"] for c in cs for a in c["access"]})
    body = f"""
<div class="ph"><div class="wrap">
  <h1>{e(city_name)}（{e(pref_name)}）の歯科医院</h1>
  <p class="sub">{len(cs)}件を掲載／最寄駅：{e('・'.join(stations))}</p>
</div></div>
<main><div class="wrap">
  <section>{cards(cs)}</section>
  <section>
    <h2 class="sec">{e(city_name)}で歯科医院を選ぶときに</h2>
    <div class="panel prose">
      <p style="margin-top:0">歯科医院は、設備や料金表だけを見ても違いが分かりにくいものです。
      通い続けられるかどうかは、通院距離・診療時間帯と、担当の先生の考え方で決まる部分が大きくなります。</p>
      <ul>
        <li><b>通える時間帯か</b>：平日夜や土曜の診療があるか、予約が取りやすいか</li>
        <li><b>治療の説明があるか</b>：いまの状態・選択肢・それぞれの利点と欠点・治療しない場合まで説明があるか</li>
        <li><b>予防まで見てくれるか</b>：治したあと、再発を防ぐところまで一緒に考えてくれるか</li>
      </ul>
      <p style="margin-bottom:0">{e(SITE['name'])}では、この3点目が分かるよう院長ご本人の言葉を掲載しています。</p>
    </div>
  </section>
</div></main>"""
    layout(f"/{pref_slug}/{city_slug}/", f"{city_name}の歯科医院",
           f"{pref_name}{city_name}の歯科医院を院長インタビューで紹介。診療時間・アクセス・診療内容から探せます。",
           body,
           breadcrumb=[(SITE["name"], u("/")), (pref_name, u(f"/{pref_slug}/")), (city_name, "")])


def page_feature_index():
    items = []
    for f in FEATURES:
        n = sum(1 for c in CLINICS if f["key"] in c.get("features", []))
        items.append(f'<a href="{u("/feature/" + f["key"] + "/")}">{e(f["label"])}'
                     f'<span class="n">{n}件</span></a>')
    body = f"""
<div class="ph"><div class="wrap">
  <h1>こだわりから歯科医院を探す</h1>
  <p class="sub">診療内容・通いやすさの条件から絞り込めます。</p>
</div></div>
<main><div class="wrap"><section>
  <div class="linklist">{''.join(items)}</div>
</section></div></main>"""
    layout("/feature/", "こだわりから歯科医院を探す",
           "土曜診療・矯正歯科・インプラント・小児歯科など、条件から歯科医院を探せます。",
           body, breadcrumb=[(SITE["name"], u("/")), ("こだわりから探す", "")])


def page_feature(f):
    cs = [c for c in CLINICS if f["key"] in c.get("features", [])]
    others = "".join(
        f'<a class="chip" href="{u("/feature/" + x["key"] + "/")}">{e(x["label"])}</a>'
        for x in FEATURES if x["key"] != f["key"])
    body = f"""
<div class="ph"><div class="wrap">
  <h1>{e(f['label'])}に対応した歯科医院</h1>
  <p class="sub">{e(f['lead'])}（{len(cs)}件）</p>
</div></div>
<main><div class="wrap">
  <section>{cards(cs)}</section>
  <section>
    <h2 class="sec">ほかの条件から探す</h2>
    <div class="chips">{others}</div>
  </section>
</div></main>"""
    layout(f"/feature/{f['key']}/", f"{f['label']}の歯科医院",
           f"{f['lead']} 院長インタビュー付きで紹介しています。",
           body,
           breadcrumb=[(SITE["name"], u("/")), ("こだわりから探す", u("/feature/")), (f["label"], "")])


def page_clinic(c):
    ac = c["access"][0]
    qa = "".join(f'<div class="qa"><p class="q">{e(x["q"])}</p><p class="a">{e(x["a"])}</p></div>'
                 for x in c.get("interview", []))
    interview = ""
    if qa:
        who = c["doctor"]["name"]
        interview = f"""<div class="panel">
      <h2>院長インタビュー</h2>
      <p class="sub" style="color:var(--muted);font-size:.85rem;margin:-8px 0 20px">
        お話を伺った方：{e(c['doctor']['title'])}　{e(who)}</p>
      {qa}
    </div>"""

    svc = "".join(f'<span class="tag">{e(s)}</span>' for s in c.get("services", []))
    feat = "".join(f'<a class="chip" href="{u("/feature/" + k + "/")}">{e(FEAT[k]["label"])}</a>'
                   for k in c.get("features", []) if k in FEAT)
    notes = "".join(f"<li>{e(n)}</li>" for n in c.get("notes_for_patients", []))
    notes_html = f'<div class="notice"><b>自由診療について</b><ul style="margin:6px 0 0;padding-left:1.1em">{notes}</ul></div>' if notes else ""
    mapq = quote(c.get("map_query", c["address"]))

    body = f"""
<div class="ph"><div class="wrap">
  <span class="badge">インタビュー掲載</span>
  <h1>{e(c['name'])}</h1>
  <p class="sub">{e(c['prefecture'])}{e(c['city'])}／{e(ac['line'])} {e(ac['station'])}{e(ac.get('exit',''))}から徒歩{ac['minutes']}分</p>
</div></div>

<main><div class="wrap"><div class="cols">
  <div class="main">
    <div class="panel">
      <p style="margin:0">{e(c.get('lead',''))}</p>
    </div>
    {interview}
    <div class="panel">
      <h2>診療内容</h2>
      <div class="tags">{svc}</div>
      <h2 style="margin-top:22px">この医院の条件</h2>
      <p class="sec-note" style="padding-left:0;margin:-8px 0 12px">同じ条件の医院を探せます。</p>
      <div class="chips">{feat}</div>
    </div>
    {notes_html}
    <div class="panel">
      <h2>医院情報</h2>
      <table class="info">
        <tr><th>医院名</th><td>{e(c['name'])}</td></tr>
        <tr><th>開設者</th><td>{e(c.get('corporation','—'))}</td></tr>
        <tr><th>住所</th><td>〒{e(c['postal'])}　{e(c['address'])}
          <br><a href="https://www.google.com/maps/search/?api=1&amp;query={mapq}" target="_blank" rel="noopener">地図で見る</a></td></tr>
        <tr><th>アクセス</th><td>{e(ac['line'])} {e(ac['station'])}{e(ac.get('exit',''))}から徒歩{ac['minutes']}分</td></tr>
        <tr><th>電話</th><td>{e(c['tel'])}</td></tr>
        {hours_rows(c)}
        <tr><th>お支払い</th><td>{e('／'.join(c.get('payments', ['—'])))}</td></tr>
        <tr><th>公式サイト</th><td><a href="{e(c['website'])}" target="_blank" rel="noopener">{e(c['website'])}</a></td></tr>
      </table>
    </div>
  </div>

  <aside class="side">
    <div class="panel">
      <p class="tel">{e(c['tel'])}</p>
      <p class="tel-note">お電話でのご予約・お問い合わせ</p>
      <a class="btn" href="{e(c.get('reservation_url') or c['website'])}" target="_blank" rel="noopener">予約ページを開く</a>
      <a class="btn sub" href="{e(c['website'])}" target="_blank" rel="noopener">公式サイトを見る</a>
      <table class="info" style="margin-top:14px">{hours_rows(c)}</table>
    </div>
  </aside>
</div></div></main>"""

    ld = {
        "@context": "https://schema.org",
        "@type": "Dentist",
        "name": c["name"],
        "url": SITE["base_url"] + f"/clinic/{c['slug']}/",
        "telephone": c["tel"],
        "address": {
            "@type": "PostalAddress",
            "postalCode": c["postal"],
            "addressRegion": c["prefecture"],
            "addressLocality": c["city"],
            "streetAddress": c["address"],
            "addressCountry": "JP",
        },
        "openingHoursSpecification": opening_spec(c),
        "availableService": [{"@type": "MedicalProcedure", "name": s} for s in c.get("services", [])],
        "sameAs": [c["website"]],
    }
    bc_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE["name"], "item": SITE["base_url"] + "/"},
            {"@type": "ListItem", "position": 2, "name": c["prefecture"], "item": SITE["base_url"] + f"/{c['pref_slug']}/"},
            {"@type": "ListItem", "position": 3, "name": c["city"], "item": SITE["base_url"] + f"/{c['pref_slug']}/{c['city_slug']}/"},
            {"@type": "ListItem", "position": 4, "name": c["name"]},
        ],
    }
    layout(f"/clinic/{c['slug']}/", c["name"],
           f"{c['prefecture']}{c['city']}の{c['name']}（{ac['station']}徒歩{ac['minutes']}分）。"
           f"院長インタビュー・診療時間・アクセス・診療内容を掲載。",
           body, jsonld=[ld, bc_ld],
           breadcrumb=[(SITE["name"], u("/")),
                       (c["prefecture"], u(f"/{c['pref_slug']}/")),
                       (c["city"], u(f"/{c['pref_slug']}/{c['city_slug']}/")),
                       (c["name"], "")])


def page_entry():
    body = f"""
<div class="ph"><div class="wrap">
  <h1>掲載をご希望の歯科医院様へ</h1>
  <p class="sub">基本情報の掲載は無料です。インタビュー記事の取材・執筆もお引き受けしています。</p>
</div></div>
<main><div class="wrap"><div class="prose">

  <section>
    <h2 class="sec">こういう医院様に向いています</h2>
    <div class="panel">
      <ul style="margin:0">
        <li>設備や料金では、他院との違いが伝わらないと感じている</li>
        <li>初診の患者さんに、治療方針の考え方を先に知っておいてほしい</li>
        <li>ホームページを作ったが、院長の人柄まで載せられていない</li>
        <li>自費のカウンセリングで、毎回同じ説明を一から繰り返している</li>
      </ul>
    </div>
  </section>

  <section>
    <h2 class="sec">掲載までの流れ</h2>
    <div class="panel">
      <ol class="steps">
        <li><b>お申し込み</b>下のメールアドレスに医院名・ご連絡先をお送りください。</li>
        <li><b>取材</b>10問程度の質問にお答えいただきます。ご記入でも、お電話・録音データでも構いません。所要は30分ほどです。</li>
        <li><b>原稿の確認</b>こちらで記事の形に整え、公開前に必ず医院様にご確認いただきます。修正のご依頼は何度でも承ります。</li>
        <li><b>公開</b>ご承認をいただいてから公開します。掲載後の内容変更・取り下げもいつでも承ります。</li>
      </ol>
    </div>
  </section>

  <section>
    <h2 class="sec">掲載プラン</h2>
    <div class="price">
      <div class="p">
        <h3>基本掲載</h3>
        <p class="amt">無料</p>
        <ul>
          <li>医院名・住所・電話・診療時間</li>
          <li>アクセス・診療内容・お支払い方法</li>
          <li>エリア別・条件別の一覧に掲載</li>
          <li>公式サイトへのリンク</li>
        </ul>
      </div>
      <div class="p hi">
        <h3>インタビュー掲載</h3>
        <p class="amt">準備中<small>（開設記念につき当面は無料）</small></p>
        <ul>
          <li>基本掲載のすべて</li>
          <li>院長インタビュー記事（Q&amp;A形式・4〜8問）</li>
          <li>一覧での優先表示</li>
          <li>公開前の原稿確認・修正対応</li>
        </ul>
      </div>
    </div>
    <p class="sec-note" style="padding-left:0">
      掲載順は、掲載料の多寡では決めていません（医療広告ガイドラインで禁じられている比較優良広告に当たらないようにするためです）。
    </p>
  </section>

  <section>
    <h2 class="sec">お申し込み・ご相談</h2>
    <div class="panel">
      <p style="margin-top:0">下記までメールでご連絡ください。営業のお電話はいたしません。</p>
      <p style="font-size:1.15rem;font-weight:700;color:var(--navy);margin:0 0 6px">{obf(SITE['contact_email'])}</p>
      <p style="margin-bottom:0;font-size:.88rem;color:var(--muted)">
        件名に「掲載希望」とご記入ください。医院名・ご住所・お電話番号・ご担当者名をお知らせいただけますとスムーズです。</p>
    </div>
  </section>

</div></div></main>"""
    layout("/entry/", "掲載をご希望の歯科医院様へ",
           "全国の歯科医院を院長インタビューで紹介する歯科ドクターズの掲載案内。基本情報の掲載は無料です。",
           body, breadcrumb=[(SITE["name"], u("/")), ("掲載のご案内", "")])


def page_about():
    body = f"""
<div class="ph"><div class="wrap">
  <h1>このサイトについて</h1>
  <p class="sub">{e(SITE['tagline'])}</p>
</div></div>
<main><div class="wrap"><div class="prose">
  <div class="panel">
    <h2 style="margin-top:0">なぜ作ったか</h2>
    <p>歯科医院を探すとき、多くの情報サイトで分かるのは診療時間・住所・診療科目までです。
    しかし実際に通い続けられるかどうかを決めているのは、「担当の先生が、何を大事にして治療しているか」の部分です。</p>
    <p>同じむし歯でも、すぐに削る先生と、経過を見ながら進める先生がいます。どちらが正しいという話ではなく、
    <b>患者さんが自分の考えに近い先生を選べること</b>が大事だと考えています。{e(SITE['name'])}は、
    そこが分かるように院長ご本人の言葉を掲載しています。</p>

    <h2>掲載の考え方</h2>
    <ul>
      <li><b>順位を売りません。</b>掲載料によって表示順を変えることはしていません。</li>
      <li><b>口コミは掲載しません。</b>医療広告ガイドラインで、患者さんの体験談の広告掲載は認められていないためです。</li>
      <li><b>「名医」「日本一」といった表現は使いません。</b>比較優良広告に当たるためです。</li>
      <li><b>公開前に必ず医院様の確認をいただきます。</b>取材した内容をこちらの判断で脚色することはありません。</li>
    </ul>

    <h2>運営</h2>
    <p>{e(SITE['operator'])}<br>
    お問い合わせ：{obf(SITE['contact_email'])}</p>
    <p style="margin-bottom:0"><a href="{u('/policy/')}">掲載方針・免責事項はこちら →</a></p>
  </div>
</div></div></main>"""
    layout("/about/", "このサイトについて",
           f"{SITE['name']}の運営方針。掲載順を売らない・口コミを載せない・公開前に医院確認を行うという3つの原則で運営しています。",
           body, breadcrumb=[(SITE["name"], u("/")), ("このサイトについて", "")])


def page_policy():
    body = f"""
<div class="ph"><div class="wrap">
  <h1>掲載方針・免責事項</h1>
  <p class="sub">医療広告ガイドラインへの対応と、情報の取り扱いについて</p>
</div></div>
<main><div class="wrap"><div class="prose">
  <div class="panel">
    <h2 style="margin-top:0">1. 情報の出どころ</h2>
    <p>掲載している医院情報は、各医院様からご提供いただいた内容、および{e(SITE['name'])}による取材に基づいています。
    公開前に必ず医院様のご確認をいただいていますが、診療時間・診療内容は変更される場合があります。
    受診の前に、各医院の公式サイトまたはお電話で最新の情報をご確認ください。</p>

    <h2>2. 広告該当性について</h2>
    <p>本サイトの医院ページは、医療法および「医業若しくは歯科医業又は病院若しくは診療所に関する広告等に関する指針」
    （医療広告ガイドライン）の対象となりうるものとして運用しています。具体的には次のとおりです。</p>
    <ul>
      <li>患者さんの体験談・口コミは掲載しません</li>
      <li>「名医」「地域No.1」などの比較優良広告に当たる表現は用いません</li>
      <li>治療効果を断定・保証する表現は用いません</li>
      <li>ビフォーアフター写真は、必要な説明を伴わない形では掲載しません</li>
      <li>自由診療について記載する場合は、費用・治療期間・想定されるリスクおよび副作用が分かるようにします</li>
    </ul>

    <h2>3. 掲載順について</h2>
    <p>一覧の掲載順は、掲載料の多寡によって変えていません。インタビュー掲載の医院が先に並ぶことがありますが、
    これは記載情報量の違いによるものです。</p>

    <h2>4. リンクについて</h2>
    <p>本サイトから各医院の公式サイトへのリンクは、利用者の利便のために設けているものです。
    リンクの掲載・被リンクの提供を目的とした有償の取引は行っていません。</p>

    <h2>5. 免責</h2>
    <p>本サイトは情報提供を目的としたものであり、診断・治療行為を行うものではありません。
    掲載情報に基づいて生じた損害について、運営者は責任を負いかねます。
    体調や症状に関する判断は、必ず医療機関にご相談ください。</p>

    <h2>6. 掲載の停止・修正</h2>
    <p>掲載内容の修正・掲載の取り下げは、いつでも承ります。{obf(SITE['contact_email'])} までご連絡ください。</p>
  </div>
</div></div></main>"""
    layout("/policy/", "掲載方針・免責事項",
           f"{SITE['name']}の掲載方針。医療広告ガイドラインへの対応、掲載順の扱い、免責事項を記載しています。",
           body, breadcrumb=[(SITE["name"], u("/")), ("掲載方針・免責事項", "")])


# ---------------------------------------------------------------- 実行

def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    open(os.path.join(OUT, ".nojekyll"), "w").close()

    page_top()

    prefs = {}
    for c in CLINICS:
        prefs.setdefault((c["pref_slug"], c["prefecture"]), []).append(c)
    for (ps, pn), cs in prefs.items():
        page_pref(ps, pn, cs)
        cities = {}
        for c in cs:
            cities.setdefault((c["city_slug"], c["city"]), []).append(c)
        for (cs_slug, cn), ccs in cities.items():
            page_city(ps, pn, cs_slug, cn, ccs)

    page_feature_index()
    for f in FEATURES:
        page_feature(f)

    for c in CLINICS:
        page_clinic(c)

    page_entry()
    page_about()
    page_policy()

    today = date.today().isoformat()
    urls = "".join(
        f"<url><loc>{SITE['base_url']}{p}</loc><lastmod>{today}</lastmod></url>"
        for p in sorted(set(PAGES)))
    open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8", newline="\n").write(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + "</urlset>")
    open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8", newline="\n").write(
        f"User-agent: *\nAllow: /\nSitemap: {SITE['base_url']}/sitemap.xml\n")

    print(f"{len(set(PAGES))} ページを docs/ に書き出しました（掲載医院 {len(CLINICS)}件）")
    for p in sorted(set(PAGES)):
        print("  ", p)


if __name__ == "__main__":
    main()
