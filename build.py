#!/usr/bin/env python3
"""Bygger den statiske jylkat-bar.dk.

  python3 build.py            -> dist/      (til one.com: rene adresser som /menukort)
  python3 build.py --preview  -> preview/   (prøveversion: links til .html, billeder hentes fra jylkat-bar.dk)
"""
import json, os, re, shutil, sys, html
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
C = lambda n: json.load(open(os.path.join(ROOT, 'content', n + '.json'), encoding='utf-8'))
COMMON, HOME, MENU, ABOUT, GAL, BOOK, CONTACT, BLOG, JUL = (C(n) for n in
    ['common', 'home', 'menu', 'about', 'gallery', 'booking', 'contact', 'blog', 'julefrokost'])
LANGS = ['da', 'en', 'de', 'sv']
DOMAIN = 'https://jylkat-bar.dk'
TEST = '--test' in sys.argv                 # skjult testmappe på serveren: /ny-side/
PREVIEW = '--preview' in sys.argv or TEST
BASE = '/ny-side' if TEST else ''
OUT = os.path.join(ROOT, 'test' if TEST else 'preview' if PREVIEW else 'dist')
MEDIA = '' if (TEST or not PREVIEW) else DOMAIN   # billeder ligger i /media på serveren
FORM_ACTION = BASE + '/send.php'
OG_LOCALE = {'da': 'da_DK', 'en': 'en_GB', 'de': 'de_DE', 'sv': 'sv_SE'}
e = lambda s: html.escape(s or '', quote=True)


def t(d, lang):
    return d.get(lang) or d.get('da') if isinstance(d, dict) else d


def path(lang, slug):
    """Den offentlige adresse (uden domæne)."""
    pre = '' if lang == 'da' else '/' + lang
    if not slug:
        return pre + '/' if lang == 'da' else pre
    return pre + '/' + slug


def href(lang, slug):
    if not PREVIEW:
        return path(lang, slug)
    pre = BASE + ('' if lang == 'da' else '/' + lang)
    return pre + '/' + (slug or 'index') + '.html'


def outfile(lang, slug):
    pre = '' if lang == 'da' else lang + '/'
    return pre + (slug or 'index') + '.html'


def img(src):
    return MEDIA + src if src.startswith('/media') else src


def nav_html(lang, current):
    items = []
    for slug, label in COMMON['nav']:
        if slug == 'GIFT':
            items.append(f'<a href="{COMMON["gift_url"]}">{e(t(label, lang))}</a>')
            continue
        target = href('da' if slug == 'blog' else lang, slug)
        cur = ' aria-current="page"' if slug == current else ''
        items.append(f'<a href="{target}"{cur}>{e(t(label, lang))}</a>')
    items.append(f'<a class="btn" href="{href(lang, "bordbestilling")}">{e(t(COMMON["cta"], lang))}</a>')
    return '\n'.join(items)


def langs_html(lang, slug, langs):
    out = []
    for L in LANGS:
        if L not in langs:
            continue
        cur = ' aria-current="true"' if L == lang else ''
        out.append(f'<a href="{href(L, slug)}" hreflang="{L}" lang="{L}"{cur}>{L.upper()}</a>')
    return '<div class="langs">' + ''.join(out) + '</div>'


def footer(lang):
    F = COMMON['foot']
    return f'''<footer class="foot"><div class="wrap"><div class="grid">
<div><img class="logo" src="{img(COMMON['logo_white'])}" alt="Jylkat Bar logo" width="84" height="84" loading="lazy">
<p><strong>Jylkat Bar</strong><br>{e(t(F['tagline'], lang))}</p><p class="small">{t(F['part'], lang)}</p></div>
<div><h4>{e(t(F['shortcuts'], lang))}</h4><ul>
<li><a href="{href(lang, 'menukort')}">{e(t(COMMON['nav'][0][1], lang))}</a></li>
<li><a href="{href(lang, 'bordbestilling')}">{e(t(COMMON['nav'][3][1], lang))}</a></li>
<li><a href="{href('da', 'blog')}">{e(t(COMMON['nav'][4][1], lang))}</a></li>
<li><a href="{COMMON['gift_url']}">{e(t(COMMON['nav'][6][1], lang))}</a></li></ul></div>
<div><h4>{e(t(F['find'], lang))}</h4><p>Ejnar Mikkelsensvej 14<br>3760 Gudhjem<br>Bornholm</p></div>
<div><h4>{e(t(F['contact'], lang))}</h4><p><a href="tel:{COMMON['phone_tel']}">{COMMON['phone']}</a><br><a href="mailto:{COMMON['email']}">{COMMON['email']}</a></p></div>
<div><h4>{e(t(F['follow'], lang))}</h4><ul><li><a href="{e(COMMON['instagram'])}" rel="me">Instagram</a></li><li><a href="{e(COMMON['facebook'])}" rel="me">Facebook</a></li><li><a href="{e(COMMON['tripadvisor'])}">Tripadvisor</a></li></ul></div>
</div><div class="copy">© {date.today().year} Jylkat Bar. {e(t(F['rights'], lang))}</div></div></footer>'''


def local_business(lang):
    hrs = [{"@type": "OpeningHoursSpecification", "dayOfWeek": h['days'], "opens": h['opens'],
            "closes": h['closes'], "validFrom": h['from'], "validThrough": h['to']} for h in COMMON['hours_ld']]
    return {
        "@context": "https://schema.org", "@type": "BarOrPub", "@id": DOMAIN + "/#bar",
        "name": "Jylkat Bar", "url": DOMAIN + "/", "telephone": "+45 31 68 88 29", "email": COMMON['email'],
        "image": [DOMAIN + COMMON['og_image'], DOMAIN + HOME['hero']['img']], "logo": DOMAIN + COMMON['logo'],
        "description": t(HOME['desc'], lang),
        "address": {"@type": "PostalAddress", "streetAddress": "Ejnar Mikkelsensvej 14", "postalCode": "3760",
                    "addressLocality": "Gudhjem", "addressRegion": "Bornholm", "addressCountry": "DK"},
        "hasMenu": DOMAIN + path(lang, 'menukort'), "acceptsReservations": DOMAIN + path(lang, 'bordbestilling'),
        "servesCuisine": ["Barmad", "Seafood", "Cocktails"], "priceRange": "$$",
        "openingHoursSpecification": hrs,
        "sameAs": [COMMON['instagram'], COMMON['facebook'], COMMON['tripadvisor']],
        "parentOrganization": {"@type": "Hotel", "name": "Klippen Hotel", "url": "https://www.hotelklippen.com"}}


def page(lang, slug, title, desc, body, langs=LANGS, noindex=False, ld=None, og_img=None, current=None, extra_head=''):
    canon = DOMAIN + path(lang, slug)
    alts = ''
    if not noindex:
        alts = ''.join(f'<link rel="alternate" hreflang="{L}" href="{DOMAIN + path(L, slug)}">' for L in langs if len(langs) > 1)
        if len(langs) > 1:
            alts += f'<link rel="alternate" hreflang="x-default" href="{DOMAIN + path("da", slug)}">'
    lds = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    og = DOMAIN + (og_img or COMMON['og_image'])
    robots = '<meta name="robots" content="noindex, nofollow">' if (noindex or TEST) else ''
    banner = ('<div class="preview-banner">TESTVERSION af den nye jylkat-bar.dk – ikke offentlig endnu. Formularerne sender ikke.</div>' if TEST else
              '<div class="preview-banner">PRØVEVERSION – ikke online endnu. Formularerne sender ikke.</div>' if PREVIEW else '')
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{robots}<link rel="canonical" href="{canon}">{alts}
<meta property="og:type" content="website"><meta property="og:site_name" content="Jylkat Bar">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canon}"><meta property="og:image" content="{e(og)}"><meta property="og:locale" content="{OG_LOCALE[lang]}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{img(COMMON['logo'])}">
<link rel="preload" href="{BASE}/assets/fonts/source-serif.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{BASE}/assets/site.css">
{lds}{extra_head}
</head>
<body>
{banner}<header class="top"><div class="wrap">
<a class="brand" href="{href(lang, '')}" aria-label="{e(t(COMMON['home_label'], lang))}"><img src="{img(COMMON['logo'])}" alt="Jylkat Bar logo" width="64" height="64">Jylkat</a>
<button class="burger" aria-label="{e(t(COMMON['menu_label'], lang))}" aria-expanded="false" onclick="var n=document.getElementById('nav');n.classList.toggle('open');this.setAttribute('aria-expanded',n.classList.contains('open'))">☰</button>
<nav class="nav" id="nav">{nav_html(lang, current or slug)}
{langs_html(lang, slug, langs)}</nav>
</div></header>
<main>
{body}
</main>
{footer(lang)}
<script src="{BASE}/assets/site.js" defer></script>
</body>
</html>
'''


# ---------- sektioner ----------
def info_block(lang):
    L = COMMON['lbl']
    return f'''<dl class="info">
<dt>{e(t(L['address'], lang))}</dt><dd>{e(COMMON['address'])}, Bornholm</dd>
<dt>{e(t(L['hours'], lang))}</dt><dd>{e(t(COMMON['hours'], lang))}</dd>
<dt>{e(t(L['phonemail'], lang))}</dt><dd><a href="tel:{COMMON['phone_tel']}">{COMMON['phone']}</a> · <a href="mailto:{COMMON['email']}">{COMMON['email']}</a></dd></dl>'''


def map_block(lang):
    L = COMMON['lbl']
    q = 'Jylkat+Bar,+Ejnar+Mikkelsensvej+14,+3760+Gudhjem'
    return f'''<div class="map" data-map="https://www.google.com/maps?q={q}&amp;output=embed" data-title="{e(t(L['map_title'], lang))}">
<button class="btn" type="button">{e(t(L['map_btn'], lang))}</button>
<p class="small">{e(t(L['map_note'], lang))}<br><a href="https://www.google.com/maps/search/?api=1&amp;query={q}">{e(t(L['map_link'], lang))}</a></p></div>'''


def home(lang):
    H = HOME
    h = H['hero']
    xm = H['xmas']
    fd = H['food']
    rv = H['reviews']
    ab = H['about']
    body = f'''<section class="hero"><img class="bg" src="{img(h['img'])}" alt="{e(t(h['alt'], lang))}" fetchpriority="high">
<div class="wrap"><img class="logo" src="{img(COMMON['logo'])}" alt="" width="96" height="96">
<p class="kicker">{e(t(h['kicker'], lang))}</p><h1>{e(t(h['h1'], lang))}</h1><p>{e(t(h['text'], lang))}</p>
<div class="btns"><a class="btn" href="{href(lang, 'bordbestilling')}">{e(t(h['btn1'], lang))}</a><a class="btn ghost" href="{href(lang, 'menukort')}">{e(t(h['btn2'], lang))}</a></div></div></section>
<section class="sec center"><div class="wrap narrow"><p class="kicker">{e(t(H['notice']['kicker'], lang))}</p><h2>{e(t(H['notice']['h2'], lang))}</h2>
<p class="lead" style="margin:0 auto">{e(t(H['notice']['text'], lang))}</p><div class="btns"><a class="btn" href="{href(lang, 'bordbestilling')}">{e(t(H['notice']['btn'], lang))}</a></div></div></section>
<section class="sec" style="padding-top:0"><div class="wrap"><div class="center"><p class="kicker">{e(t(xm['kicker'], lang))}</p><h2>{e(t(xm['h2'], lang))}</h2></div>
<div class="grid g3" style="margin-top:28px">{''.join(f'<div class="card"><h3>{e(t(i["h3"], lang))}</h3><p>{e(t(i["p"], lang))}</p></div>' for i in xm['items'])}</div>
<div class="center"><div class="btns"><a class="btn" href="{href(lang, 'bordbestilling')}">{e(t(xm['btn'], lang))}</a></div>
<p class="small" style="margin-top:14px">{e(t(xm['small'], lang))}</p></div></div></section>
<section class="sec sage"><div class="wrap"><div class="split-head"><div><p class="kicker">{e(t(fd['kicker'], lang))}</p><h2>{e(t(fd['h2'], lang))}</h2><p class="tag">{e(t(fd['tag'], lang))}</p></div><p>{e(t(fd['text'], lang))}</p></div>
<div class="grid g3">{''.join(f'<article class="dish"><img src="{img(d["img"])}" alt="{e(t(d["name"], lang))}" loading="lazy"><div class="body"><div class="row"><h3>{e(t(d["name"], lang))}</h3><span class="price">{d["price"]}</span></div><p class="small">{e(t(d["p"], lang))}</p></div></article>' for d in fd['dishes'])}</div>
<div class="center"><div class="btns"><a class="btn" href="{href(lang, 'menukort')}">{e(t(fd['btn'], lang))}</a></div></div></div></section>
<section class="sec center"><div class="wrap"><p class="kicker">{e(t(rv['kicker'], lang))}</p><h2>{e(t(rv['h2'], lang))}</h2><p class="tag">★★★★★ {e(t(rv['score'], lang))}</p>
<div class="grid g3" style="margin-top:30px;text-align:left">{''.join(f'<figure class="card quote" style="margin:0"><blockquote>“{e(t(q, lang))}”</blockquote><figcaption class="who">{e(t(rv["who"], lang))}</figcaption></figure>' for q in rv['quotes'])}</div>
<div class="btns"><a class="btn ghost" href="{e(rv['url'])}">{e(t(rv['btn'], lang))}</a></div></div></section>
<section class="sec" style="padding-top:0"><div class="wrap grid g2"><img class="photo" src="{img(ab['img'])}" alt="{e(t(ab['alt'], lang))}" loading="lazy">
<div><p class="kicker">{e(t(ab['kicker'], lang))}</p><h2>{e(t(ab['h2'], lang))}</h2>{''.join(f'<p>{e(t(p, lang))}</p>' for p in ab['ps'])}
<div class="btns"><a class="btn" href="{href(lang, 'om-baren')}">{e(t(ab['btn'], lang))}</a></div></div></div></section>
<section class="sec sage"><div class="wrap"><div class="center"><p class="kicker">{e(t(H['gallery']['kicker'], lang))}</p><h2>{e(t(H['gallery']['h2'], lang))}</h2></div>
<div class="gallery-strip" style="margin-top:28px">{''.join(f'<img src="{img(s)}" alt="{e(next((a for x, a in GAL["imgs"] if x == s), "Jylkat Bar"))}" loading="lazy">' for s in H['gallery']['imgs'][1:])}</div>
<div class="center"><div class="btns"><a class="btn" href="{href(lang, 'galleri')}">{e(t(H['gallery']['btn'], lang))}</a></div></div></div></section>
<section class="sec mist"><div class="wrap grid g2"><div><p class="kicker">{e(t(H['contact']['kicker'], lang))}</p><h2>{e(t(H['contact']['h2'], lang))}</h2><p>{e(t(H['contact']['text'], lang))}</p>
{info_block(lang)}<div class="btns"><a class="btn" href="{href(lang, 'kontakt')}">{e(t(H['contact']['btn'], lang))}</a></div></div>{map_block(lang)}</div></section>
<section class="sec mist" style="padding-top:0"><div class="wrap narrow center"><p class="kicker">{e(t(H['gift']['kicker'], lang))}</p><h2>{e(t(H['gift']['h2'], lang))}</h2><p>{e(t(H['gift']['text'], lang))}</p>
<div class="btns"><a class="btn" href="{COMMON['gift_url']}">{e(t(H['gift']['btn'], lang))}</a></div></div></section>'''
    ld = [local_business(lang)]
    return page(lang, '', t(H['title'], lang), t(H['desc'], lang), body, ld=ld)


def tr_wine(name, lang):
    if isinstance(name, dict):
        return t(name, lang)
    if lang == 'da':
        return name
    for k, v in MENU['countries'].items():
        name = re.sub(r'(?<![\wæøå])' + re.escape(k) + r'(?![\wæøå])', v[lang], name)
    return name


def menu(lang):
    M = MENU
    food = ''.join(f'<div class="mi"><div class="row"><h3>{e(t(d["name"], lang))}</h3><span class="price">{d["price"]}</span></div><p>{e(t(d["p"], lang))}</p></div>' for d in M['food'])
    tabs, cats = [], []
    for i, c in enumerate(M['drinks']):
        cid = 'd' + str(i + 1)
        tabs.append(f'<a href="#{cid}">{e(t(c["cat"], lang))}</a>')
        items = []
        for name, price, note in c['items']:
            if isinstance(note, str):
                note = t(M['notes'][note], lang) if note in M['notes'] else ''
            else:
                note = t(note, lang)
            items.append(f'<div class="mi"><div class="row"><h3>{e(tr_wine(name, lang))}</h3><span class="price">{e(price)}</span></div>' + (f'<p>{e(note)}</p>' if note else '') + '</div>')
        cats.append(f'<div class="drinkcat" id="{cid}"><h3>{e(t(c["cat"], lang))}</h3><div class="menu-list">{"".join(items)}</div></div>')
    body = f'''<section class="sec dark pagehead"><div class="wrap"><p class="kicker" style="color:#e5e9e1">{e(t(M['kicker'], lang))}</p><h1>{e(t(M['h1'], lang))}</h1><p class="lead">{e(t(M['intro'], lang))}</p></div></section>
<section class="sec sage" style="padding-bottom:0"><div class="wrap"><img class="wide" src="{img(M['img'])}" alt="{e(t(M['alt'], lang))}"></div></section>
<section class="sec sage"><div class="wrap"><p class="kicker">{e(t(M['food_kicker'], lang))}</p><h2>{e(t(M['food_h2'], lang))}</h2><p class="tag">{e(t(M['takeaway'], lang))}</p><div class="menu-list">{food}</div></div></section>
<section class="sec"><div class="wrap"><p class="kicker">{e(t(M['drinks_kicker'], lang))}</p><h2>{e(t(M['drinks_h2'], lang))}</h2><nav class="tabs">{''.join(tabs)}</nav>{''.join(cats)}
<div class="btns"><a class="btn" href="{href(lang, 'bordbestilling')}">{e(t(COMMON['cta'], lang))}</a></div></div></section>'''
    ld = [{"@context": "https://schema.org", "@type": "Menu", "name": t(M['h1'], lang), "url": DOMAIN + path(lang, 'menukort'), "inLanguage": lang,
           "hasMenuSection": [{"@type": "MenuSection", "name": t(M['food_h2'], lang), "hasMenuItem": [
               {"@type": "MenuItem", "name": t(d['name'], lang), "description": t(d['p'], lang),
                "offers": {"@type": "Offer", "price": d['price'].split()[0], "priceCurrency": "DKK"}} for d in M['food']]}]}]
    return page(lang, 'menukort', t(M['title'], lang), t(M['desc'], lang), body, ld=ld, og_img=M['img'])


def about(lang):
    A = ABOUT
    body = f'''<section class="hero short"><img class="bg" src="{img(A['hero_img'])}" alt="{e(t(A['hero_alt'], lang))}" fetchpriority="high">
<div class="wrap"><p class="kicker">{e(t(A['kicker'], lang))}</p><h1>{e(t(A['h1'], lang))}</h1></div></section>
<section class="sec sage"><div class="wrap narrow"><p class="lead">{t(A['intro'], lang)}</p></div></section>
<section class="sec mist"><div class="wrap grid g2"><img class="photo" src="{img(A['tent_img'])}" alt="{e(t(A['tent_alt'], lang))}" loading="lazy">
<div><h2>{e(t(A['tent_h2'], lang))}</h2>{''.join(f'<p>{e(t(p, lang))}</p>' for p in A['tent_ps'])}</div></div></section>
<section class="sec sage"><div class="wrap narrow">{''.join(f'<p>{e(t(p, lang))}</p>' for p in A['story_ps'])}</div></section>
<section class="sec mist"><div class="wrap grid g2"><div><p class="kicker">{e(t(A['pind_kicker'], lang))}</p><p class="lead">{e(t(A['pind_text'], lang))}</p></div>
<img class="photo" src="{img(A['pind_img'])}" alt="{e(t(A['pind_alt'], lang))}" loading="lazy"></div></section>
<section class="sec sage"><div class="wrap"><div class="gallery-strip">{''.join(f'<img src="{img(s)}" alt="{e(next((a for x, a in GAL["imgs"] if x == s), "Jylkat Bar"))}" loading="lazy">' for s in A['imgs'])}</div>
<div class="center"><div class="btns"><a class="btn" href="{href(lang, 'bordbestilling')}">{e(t(COMMON['cta'], lang))}</a><a class="btn ghost" href="{href(lang, 'menukort')}">{e(t(COMMON['nav'][0][1], lang))}</a></div></div></div></section>'''
    return page(lang, 'om-baren', t(A['title'], lang), t(A['desc'], lang), body, og_img=A['tent_img'])


def gallery(lang):
    G = GAL
    body = f'''<section class="sec pagehead sage"><div class="wrap"><p class="kicker">{e(t(G['kicker'], lang))}</p><h1>{e(t(G['h1'], lang))}</h1></div></section>
<section class="sec" style="padding-top:40px"><div class="wrap"><div class="gallery">{''.join(f'<img src="{img(s)}" alt="{e(a)}" loading="lazy">' for s, a in G['imgs'])}</div>
<div class="center"><div class="btns"><a class="btn" href="{href(lang, 'bordbestilling')}">{e(t(COMMON['cta'], lang))}</a></div></div></div></section>'''
    return page(lang, 'galleri', t(G['title'], lang), t(G['desc'], lang), body)


def field(name, typ, label, req, opts=None, ph='', full=False):
    r = ' required' if req else ''
    cls = ' class="full"' if full or typ in ('textarea', 'radio') else ''
    fid = 'f-' + name
    if typ == 'textarea':
        ctl = f'<textarea id="{fid}" name="{name}" placeholder="{e(ph)}"{r}></textarea>'
    elif typ == 'select':
        ctl = f'<select id="{fid}" name="{name}"{r}>' + ''.join(f'<option value="{e(v)}">{e(l)}</option>' for v, l in opts) + '</select>'
    elif typ == 'radio':
        return f'<fieldset{cls}><legend><label>{e(label)}</label></legend>' + ''.join(f'<label><input type="radio" name="{name}" value="{e(o)}"> {e(o)}</label>' for o in opts) + '</fieldset>'
    else:
        extra = ' min="1" max="50"' if typ == 'number' else ''
        auto = {'full_name': 'name', 'phone': 'tel', 'submitter_email': 'email', 'company': 'organization'}.get(name)
        ac = f' autocomplete="{auto}"' if auto else ''
        ctl = f'<input id="{fid}" type="{typ}" name="{name}"{extra}{ac}{r}>'
    return f'<div{cls}><label for="{fid}">{e(label)}</label>{ctl}</div>'


def form(kind, lang, fields_html, submit, thanks, error, fid='form'):
    return f'''<form class="f" id="{fid}" action="{FORM_ACTION}" method="post" data-ajax>
<input type="hidden" name="form" value="{e(kind)}"><input type="hidden" name="lang" value="{lang}">
<div class="hp" aria-hidden="true"><label>Firma<input type="text" name="_hp_company" tabindex="-1" autocomplete="off"></label></div>
{fields_html}
<div class="full"><button class="btn" type="submit">{e(submit)}</button>
<p class="small" style="margin-top:12px">{e(t(COMMON['form_privacy'], lang))}</p></div>
<div class="full msg" data-ok hidden>{e(thanks)}</div><div class="full msg" data-err hidden>{e(error)}</div>
</form>'''


def booking(lang):
    B = BOOK
    F = B['fields']
    fs = ''.join([
        field('full_name', 'text', t(F['full_name'], lang), True),
        field('phone', 'tel', t(F['phone'], lang), True),
        field('submitter_email', 'email', t(F['email'], lang), True),
        field('guests', 'number', t(F['guests'], lang), True),
        field('date', 'date', t(F['date'], lang), True),
        field('time', 'time', t(F['time'], lang), True),
        field('message', 'textarea', t(F['message'], lang), False, ph=t(F['message_ph'], lang))])
    body = f'''<section class="hero short"><img class="bg" src="{img(B['img'])}" alt="{e(t(B['alt'], lang))}" fetchpriority="high">
<div class="wrap"><p class="kicker">{e(t(B['kicker'], lang))}</p><h1>{e(t(B['h1'], lang))}</h1><p>{e(t(B['intro'], lang))}</p></div></section>
<section class="sec mist"><div class="wrap grid g2" style="align-items:start">
<div id="booking">{form('Bordbestilling', lang, fs, t(F['submit'], lang), t(F['thanks'], lang), t(F['error'], lang))}</div>
<div>{info_block(lang)}</div></div></section>'''
    return page(lang, 'bordbestilling', t(B['title'], lang), t(B['desc'], lang), body)


def contact(lang):
    K = CONTACT
    F = K['fields']
    fs = ''.join([field('full_name', 'text', t(F['full_name'], lang), True), field('submitter_email', 'email', t(F['email'], lang), True),
                  field('phone', 'tel', t(F['phone'], lang), False, full=True), field('message', 'textarea', t(F['message'], lang), True)])
    body = f'''<section class="sec pagehead sage"><div class="wrap"><p class="kicker">{e(t(K['kicker'], lang))}</p><h1>{e(t(K['h1'], lang))}</h1></div></section>
<section class="sec sage" style="padding-top:0"><div class="wrap grid g2" style="align-items:start"><div>{info_block(lang)}</div>{map_block(lang)}</div></section>
<section class="sec mist"><div class="wrap narrow"><h2>{e(t(K['form_h2'], lang))}</h2>{form('Kontakt', lang, fs, t(F['submit'], lang), t(F['thanks'], lang), t(BOOK['fields']['error'], lang))}</div></section>'''
    return page(lang, 'kontakt', t(K['title'], lang), t(K['desc'], lang), body, ld=[local_business(lang)])


DK_MONTHS = ['januar', 'februar', 'marts', 'april', 'maj', 'juni', 'juli', 'august', 'september', 'oktober', 'november', 'december']


def dkdate(s):
    y, m, d = map(int, s.split('-'))
    return f'{d}. {DK_MONTHS[m - 1]} {y}'


def blog_index():
    B = BLOG
    cards = ''.join(f'''<a class="post" href="{href('da', 'blog/' + p['slug'])}"><img src="{img(p['img'])}" alt="{e(p['alt'])}" loading="lazy">
<div class="body">{f'<p class="meta">{e(p["tag"])}</p>' if p['tag'] else ''}<h2>{e(p['title'])}</h2><p>{e(p['excerpt'])}</p><p class="meta"><time datetime="{p['date']}">{dkdate(p['date'])}</time></p></div></a>''' for p in B['posts'])
    body = f'''<section class="sec pagehead sage"><div class="wrap"><p class="kicker">{e(t(B['kicker'], 'da'))}</p><h1>{e(t(B['h1'], 'da'))}</h1></div></section>
<section class="sec" style="padding-top:40px"><div class="wrap"><div class="posts">{cards}</div></div></section>'''
    return page('da', 'blog', t(B['title'], 'da'), t(B['desc'], 'da'), body, langs=['da'])


def blog_post(p):
    parts = []
    for b in p['body']:
        if b[0] == 'p':
            parts.append(f'<p>{b[1]}</p>')
        elif b[0] == 'h2':
            parts.append(f'<h2>{e(b[1])}</h2>')
        elif b[0] == 'img':
            parts.append(f'<img src="{img(b[1])}" alt="{e(b[2])}" loading="lazy">')
    body = f'''<section class="sec" style="padding-top:48px"><div class="wrap"><div class="article">
<p><a href="{href('da', 'blog')}">{e(BLOG['back'])}</a></p>{f'<p class="kicker">{e(p["tag"])}</p>' if p['tag'] else ''}
<h1 style="font-size:clamp(2rem,4.5vw,3.2rem)">{e(p['title'])}</h1><p class="meta"><time datetime="{p['date']}">{dkdate(p['date'])}</time></p>
<img class="wide" src="{img(p['img'])}" alt="{e(p['alt'])}">
{''.join(parts)}
<div class="btns"><a class="btn" href="{href('da', 'bordbestilling')}">Book et bord</a><a class="btn ghost" href="{href('da', 'menukort')}">Se menukortet</a></div>
</div></div></section>'''
    ld = [{"@context": "https://schema.org", "@type": "BlogPosting", "headline": p['title'], "description": p['desc'],
           "datePublished": p['date'], "image": DOMAIN + p['img'], "inLanguage": "da",
           "mainEntityOfPage": DOMAIN + path('da', 'blog/' + p['slug']),
           "author": {"@type": "Organization", "name": "Jylkat Bar", "url": DOMAIN + "/"},
           "publisher": {"@id": DOMAIN + "/#bar"}}]
    return page('da', 'blog/' + p['slug'], p['title'] + ' - Jylkat Bar', p['desc'], body, langs=['da'], ld=ld, og_img=p['img'], current='blog')


def julefrokost(slug):
    J = JUL
    P = J['pages'][slug]
    fid = P['form_id']
    btn = f'<div class="btns"><a class="btn" href="#{fid}">Book jeres julefrokost</a></div>'
    lists = ''
    for i, L in enumerate(P['lists']):
        cls = 'sage' if i % 2 == 0 else 'mist'
        inner = (f'<p>{e(L["p"])}</p>' if L['p'] else '') + '<ul class="stars">' + ''.join(f'<li>{e(x)}</li>' for x in L['items']) + '</ul>'
        if L.get('img'):
            lists += f'<section class="sec {cls}"><div class="wrap grid g2"><img class="photo" src="{img(J[L["img"]])}" alt="{e(J["img_alt"])}" loading="lazy"><div><h2>{e(L["h2"])}</h2>{inner}</div></div></section>'
        else:
            lists += f'<section class="sec {cls}"><div class="wrap narrow"><h2>{e(L["h2"])}</h2>{inner}</div></section>'
    after = ''.join(f'<section class="sec {"mist" if i % 2 == 0 else "sage"}"><div class="wrap narrow"><h2>{e(a["h2"])}</h2><p>{e(a["p"])}</p>{btn if a.get("btn") else ""}</div></section>' for i, a in enumerate(P['after_menu']))
    fields = []
    for f in P['fields']:
        name, typ, label, req = f[:4]
        if typ == 'date-select':
            fields.append(field(name, 'select', label, req, opts=[('', 'Vælg en dato')] + [(d, d) for d in J['dates']]))
        elif typ == 'radio':
            fields.append(field(name, 'radio', label, req, opts=f[4]))
        else:
            fields.append(field(name, typ, label, req))
    no_img = 'img_lamps' if not any(L.get('img') for L in P['lists']) else P['tent_img']
    body = f'''<section class="hero"><img class="bg" src="{img(J[P['hero']])}" alt="{e(J['img_alt'])}" fetchpriority="high">
<div class="wrap"><p class="kicker">{e(P['kicker'])}</p><h1>{e(P['h1'])}</h1><p>{e(P['lead'])}</p><div class="btns"><a class="btn" href="#{fid}">Forespørg på jeres dato</a></div></div></section>
<section class="sec mist"><div class="wrap grid g2"><img class="photo" src="{img(J[P['tent_img']])}" alt="{e(J['img_alt'])}" loading="lazy"><div><h2>{e(J['tent_h2'])}</h2><p>{e(J['tent_p'])}</p>{btn}</div></div></section>
{lists}
<section class="sec mist"><div class="wrap grid g2">{f'<img class="photo" src="{img(J["img_lamps"])}" alt="{e(J["img_alt"])}" loading="lazy">' if no_img == 'img_lamps' else ''}<div><h2>{e(P['menu_h2'])}</h2><ul class="stars">{''.join(f'<li>{e(d)}</li>' for d in J['dishes'])}</ul>
<p><strong>{e(P['menu_price'])}</strong></p>{f'<p>{e(P["menu_note"])}</p>' if P['menu_note'] else ''}{btn}</div></div></section>
{after}
<section class="sec sage"><div class="wrap narrow"><h2>{e(P['overnight_h2'])}</h2><p>{e(P['overnight_p'])}</p><div class="btns"><a class="btn ghost" href="{J['overnight_url']}">Book overnatning</a></div></div></section>
<section class="sec dark"><div class="wrap"><h2>{e(J['dates_h2'])}</h2><p>{e(J['dates_p'])}</p>
<div class="chips">{''.join(f'<a href="#{fid}" data-date="{e(d)}">{e(d)}</a>' for d in J['dates'])}</div>
<img class="wide" src="{img(J[P['tent_img']])}" alt="{e(J['img_alt'])}" loading="lazy"></div></section>
<section class="sec mist" id="{fid}"><div class="wrap narrow"><h2>Forespørg på jeres dato</h2>
{form(P['form_type'], 'da', ''.join(fields), 'Send forespørgsel', 'Tak! Vi har modtaget jeres forespørgsel og vender tilbage hurtigst muligt.', t(BOOK['fields']['error'], 'da'), fid='f-' + fid)}
<p class="small" style="margin-top:18px">{P['after_form']}</p></div></section>'''
    return page('da', slug, P['title'], P['desc'], body, langs=['da'], noindex=True, current='bordbestilling')


def notfound(lang='da'):
    nf = COMMON['notfound']['da']
    body = f'''<section class="sec pagehead sage"><div class="wrap narrow"><p class="kicker">404</p><h1>{e(nf[0])}</h1><p>{e(nf[1])}</p>
<div class="btns"><a class="btn" href="/">Jylkat – forsiden</a><a class="btn ghost" href="/menukort">Menukort</a></div></div></section>'''
    return page('da', '404', nf[0] + ' - Jylkat Bar', nf[1], body, langs=['da'], noindex=True)


def write(rel, content):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)


def sitemap():
    today = date.today().isoformat()
    urls = []
    for slug in ['', 'menukort', 'om-baren', 'galleri', 'bordbestilling', 'kontakt']:
        for L in LANGS:
            alts = ''.join(f'<xhtml:link rel="alternate" hreflang="{A}" href="{DOMAIN + path(A, slug)}"/>' for A in LANGS)
            alts += f'<xhtml:link rel="alternate" hreflang="x-default" href="{DOMAIN + path("da", slug)}"/>'
            urls.append(f'<url><loc>{DOMAIN + path(L, slug)}</loc><lastmod>{today}</lastmod>{alts}</url>')
    urls.append(f'<url><loc>{DOMAIN}/blog</loc><lastmod>{today}</lastmod></url>')
    for p in BLOG['posts']:
        urls.append(f'<url><loc>{DOMAIN}/blog/{p["slug"]}</loc><lastmod>{p["date"]}</lastmod></url>')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + '\n'.join(urls) + '\n</urlset>\n')


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(ROOT, 'site'), OUT)
    for L in LANGS:
        for slug, fn in [('', home), ('menukort', menu), ('om-baren', about), ('galleri', gallery), ('bordbestilling', booking), ('kontakt', contact)]:
            write(outfile(L, slug), fn(L))
    write('blog.html', blog_index())
    for p in BLOG['posts']:
        write(f'blog/{p["slug"]}.html', blog_post(p))
    for s in JUL['pages']:
        write(s + '.html', julefrokost(s))
    write('404.html', notfound())
    write('sitemap.xml', sitemap())
    write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n')
    if TEST:
        for f in ['.htaccess', 'sitemap.xml', 'robots.txt', 'send.php']:
            os.remove(os.path.join(OUT, f))
    elif PREVIEW:
        os.remove(os.path.join(OUT, '.htaccess')) if os.path.exists(os.path.join(OUT, '.htaccess')) else None
        os.remove(os.path.join(OUT, 'send.php')) if os.path.exists(os.path.join(OUT, 'send.php')) else None
    n = sum(len(f) for _, _, f in os.walk(OUT))
    print(f'{n} filer i {OUT}')


if __name__ == '__main__':
    main()
