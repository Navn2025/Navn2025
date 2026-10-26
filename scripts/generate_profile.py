"""Generate self-contained ASCII SVGs from the selected source photograph.

The original wall background is deliberately retained. SVGs contain actual
characters and native vectors, with no scripts or embedded raster images.
"""
from pathlib import Path
from html import escape
import json

from PIL import Image, ImageFilter, ImageOps
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "profile"
CFG = json.loads((ROOT / "profile" / "config.json").read_text(encoding="utf-8"))
GREEN = "#00ff87"
BG = "#0d1117"
MUTED = "#8b949e"
INK = "#d7e0e8"
FONT = "Consolas, 'Liberation Mono', Menlo, monospace"
COLS, ROWS = 100, 78
CELL_W, CELL_H = 400/COLS, 407/ROWS
PORTRAIT_FONT = 5.4
ROW_DURATION = 3.6/ROWS
CONTENT_SIZE = round(1024*(1-2*CFG.get('portrait_padding',.12)))


def label(x, y, text, size=14, fill=INK, extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" {extra}>{escape(text)}</text>'


def document(w, h, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="title" font-family="{FONT}">'
            f'<title id="title">{escape(title)}</title>{body}</svg>')


def frame(w, h, title):
    parts = [f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12" fill="{BG}" stroke="#30363d"/>',
             f'<path d="M1 38H{w-1}" stroke="#30363d"/>']
    for i, color in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        parts.append(f'<circle cx="{20+i*16}" cy="19" r="4.5" fill="{color}"/>')
    parts.append(label(w/2 + 24, 23, title, 11, MUTED, 'text-anchor="middle"'))
    return "".join(parts)


def sample_portrait():
    photo = Image.open(ROOT / "profile" / CFG.get("photo_source","source-photo.png")).convert("RGBA")
    alpha = photo.getchannel("A")
    # Use the complete photo, including the softly blurred beige wall. Alpha is only
    # used for the outer canvas padding, never for person/background separation.
    bounds = alpha.point(lambda value: 255 if value > 200 else 0).getbbox()
    if not bounds:
        raise ValueError("Source photograph is empty")
    # Keep enough source resolution for fine facial features. The old 224px
    # intermediate and 8 ink levels flattened the eyes and smile into bands.
    subject = ImageOps.contain(photo.crop(bounds),(CONTENT_SIZE,CONTENT_SIZE),Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA",(1024,1024),(0,0,0,0))
    canvas.alpha_composite(subject,((1024-subject.width)//2,(1024-subject.height)//2))
    mask = canvas.getchannel("A")
    gray = ImageOps.autocontrast(ImageOps.grayscale(canvas),cutoff=.5,mask=mask)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=2,percent=100,threshold=2))
    cols, rows = COLS, ROWS
    small = gray.resize((cols,rows),Image.Resampling.BOX)
    # Erode by a pixel before box sampling: every printed cell must lie inside
    # the foreground rather than crossing a soft, partially transparent edge.
    alpha = mask.filter(ImageFilter.MinFilter(3)).resize((cols,rows),Image.Resampling.BOX)
    return small, alpha


def portrait_rows():
    small, alpha = sample_portrait()
    # Use only the alpha silhouette as a sampling guide. All person pixels still
    # come from the chosen original/soft-background photo, never the cutout RGB.
    matte = Image.open(ROOT/'profile'/'portrait-cutout.png').getchannel('A')
    matte = ImageOps.contain(matte,(CONTENT_SIZE,CONTENT_SIZE),Image.Resampling.LANCZOS)
    matte_canvas = Image.new('L',(1024,1024),0)
    matte_canvas.paste(matte,((1024-matte.width)//2,(1024-matte.height)//2))
    subject_mask = matte_canvas.resize((COLS,ROWS),Image.Resampling.BOX)
    cols, rows = small.size
    ramp = ' .`^",:;Il!i~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$'
    result, shades = [], []
    for y in range(rows):
        row, tones = [], []
        for x in range(cols):
            if alpha.getpixel((x, y)) < 235:
                row.append(" ")
                tones.append(0)
            elif subject_mask.getpixel((x,y)) < 160:
                seed = (x*73856093 ^ y*19349663) & 0xffff
                row.append('.' if seed%5 == 0 else ' ')
                tones.append(36 if seed%5 == 0 else 0)
            else:
                light = (small.getpixel((x,y))/255) ** .85
                density = .06 + .86*(light**1.2)
                row.append(ramp[min(len(ramp)-1, round(density * (len(ramp)-1)))])
                tones.append(round(64+191*light))
        result.append("".join(row))
        shades.append(tones)
    return result, shades


def portrait(rows, shades, static=False):
    body = [frame(440, 540, "navneet@github: ~/portrait")]
    body.append(label(20, 65, "$ render --ascii navneet.png", 12, GREEN))
    body.append('<defs><clipPath id="portraitViewport"><rect x="20" y="83" width="400" height="408"/></clipPath></defs><g clip-path="url(#portraitViewport)">')
    body.append('<style>@media(prefers-reduced-motion:reduce){.typed{clip-path:none!important}.cursor{display:none}}</style>')
    for i, row in enumerate(rows):
        top, baseline = 83+i*CELL_H, 83+i*CELL_H+CELL_H*.82
        runs = []
        for index, char in enumerate(row):
            tone = shades[i][index]
            if runs and runs[-1][0] == tone:
                runs[-1][1] += char
            else:
                runs.append([tone, char, index])
        spans = []
        for tone, chars, start in runs:
            # Explicit cell positions also work across nested tspans. SVG's
            # textLength spacing can drift with colored runs and trailing spaces.
            positions = " ".join(f'{20+(start+j)*CELL_W:.3f}' for j in range(len(chars)))
            color = f'#{tone:02x}{tone:02x}{tone:02x}'
            spans.append(f'<tspan x="{positions}" fill="{color}">{escape(chars)}</tspan>')
        text = (f'<text x="20" y="{baseline:.3f}" font-size="{PORTRAIT_FONT:.3f}" font-weight="400" xml:space="preserve" '
                f'>{"".join(spans)}</text>')
        if static:
            body.append(text)
            continue
        # Finite row-wise reveal; the completed portrait stays visible.
        begin = .35+i*ROW_DURATION
        # Reveal only along x. A tight per-row y clip can shave antialiased
        # glyph pixels and bring back horizontal stripes at small font sizes.
        body.append(f'<defs><clipPath id="row{i}"><rect x="20" y="83" width="400" height="408">'
                    f'<animate attributeName="width" values="0;400" begin="{begin:.4f}s" dur="{ROW_DURATION:.4f}s" fill="freeze"/>'
                    f'<set attributeName="width" to="0" begin="0s" end="{begin:.3f}s"/>'
                    '</rect></clipPath></defs>')
        body.append(f'<g class="typed" clip-path="url(#row{i})">{text}</g>')
        body.append(f'<rect class="cursor" x="20" y="{top:.3f}" width="{CELL_W:.3f}" height="{CELL_H:.3f}" fill="{GREEN}" opacity="0">'
                    f'<set attributeName="opacity" to="1" begin="{begin:.4f}s" dur="{ROW_DURATION:.4f}s"/>'
                    f'<animate attributeName="x" from="20" to="420" begin="{begin:.4f}s" dur="{ROW_DURATION:.4f}s"/>'
                    '</rect>')
    body.append('</g><path d="M16 504H424" stroke="#21262d"/>')
    body.append(label(20, 525, f"{COLS} cols / dotted backdrop / Navn2025", 11, MUTED))
    return "".join(body)


def info():
    parts = [frame(544, 540, "navneet@github: ~$ neofetch")]
    parts.append(label(24, 76, "navneet@github", 19, GREEN, 'font-weight="bold"'))
    parts.append(label(24, 98, "------------------------------", 13, MUTED))
    for i, (key, value) in enumerate(CFG["info"]):
        y = 116 + i*22
        parts.append(label(24, y, key, 12, "#ffb454"))
        parts.append(label(123, y, value, 13))
    parts.append('<path d="M24 451H520" stroke="#21262d"/>')
    parts.append(f'<circle cx="29" cy="476" r="3.5" fill="{GREEN}"/>')
    parts.append(label(42, 480, "SYSTEM ONLINE  /  ALWAYS BUILDING", 12, GREEN))
    parts.append(label(24, 508, CFG["tagline"], 13, MUTED))
    return "".join(parts)


def portrait_art(rows, shades, static=False):
    # Same actual ASCII as the terminal panel, presented full-bleed like the
    # supplied reference. Keep terminal chrome outside this standalone artwork.
    root = ET.fromstring('<svg>'+portrait(rows,shades,static)+'</svg>')
    defs = ET.tostring(root.find('defs'),encoding='unicode')
    foreground = ET.tostring(root.find('g'),encoding='unicode')
    _, alpha = sample_portrait()
    backdrop = ['<rect width="400" height="408" fill="#090a0b"/>']
    for y in range(ROWS):
        glyphs, positions = [], []
        for x in range(COLS):
            value = (x*73856093 ^ y*19349663) & 0xffff
            if alpha.getpixel((x,y)) < 235 and value%7 == 0:
                glyphs.append('.' if value%3 else ',')
                positions.append(f'{x*CELL_W:.3f}')
        if glyphs:
            backdrop.append(f'<text x="{" ".join(positions)}" y="{y*CELL_H+CELL_H*.8:.3f}" font-size="2.8" fill="#25272a">{"".join(glyphs)}</text>')
    body = ''.join(backdrop)+'<g transform="translate(-20 -83)" opacity=".84">'+defs+foreground+'</g>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1020" viewBox="0 0 400 408" '
            f'role="img" aria-labelledby="title" font-family="{FONT}"><title id="title">'
            'Navneet Tripathi — full-bust letter-and-symbol ASCII portrait</title>'+body+'</svg>')


def banner(width=1000):
    columns = 3 if width >= 800 else 2
    badge_width = 284 if columns == 3 else 244
    badge_rows = (len(CFG['roles'])+columns-1)//columns
    footer_y = 134+badge_rows*41
    banner_height = footer_y+26
    center = width/2
    parts = [f'<rect width="{width}" height="{banner_height}" rx="12" fill="{BG}"/>']
    parts.append(label(center,48,"> NAVNEET TRIPATHI.exe",29 if columns==3 else 25,GREEN,
                       'text-anchor="middle" font-weight="bold"'))
    # Allocate a complete slot for every role, rather than reusing the old
    # three-role / 12-second timeline when more roles are added.
    cycle = max(1,len(CFG['roles']))*4
    for i, role in enumerate(CFG["roles"]):
        width = len(role)*11.5
        x = (center*2-width)/2
        parts.append(f'<g opacity="{1 if i == 0 else 0}">')
        parts.append(f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.002;{3.8/cycle:.6f};{4/cycle:.6f};1" dur="{cycle}s" begin="{i*4}s" repeatCount="indefinite"/>')
        parts.append(f'<clipPath id="role{i}"><rect x="{x}" y="67" width="{width}" height="28">'
                     f'<animate attributeName="width" values="0;{width};{width}" keyTimes="0;{1.6/cycle:.6f};1" dur="{cycle}s" begin="{i*4}s" repeatCount="indefinite"/></rect></clipPath>')
        parts.append(f'<g clip-path="url(#role{i})">'+label(center,88,role,19,INK,'text-anchor="middle"')+'</g></g>')
    # Show the complete set immediately as well as in the typing carousel.
    for i,role in enumerate(CFG['roles']):
        row,column = divmod(i,columns)
        row_count = min(columns,len(CFG['roles'])-row*columns)
        start_x = (center*2-(row_count*badge_width+(row_count-1)*16))/2
        x,y = start_x+column*(badge_width+16),111+row*41
        parts.append(f'<rect x="{x}" y="{y}" width="{badge_width}" height="31" rx="6" fill="#101c1b" stroke="#24443c"/>')
        parts.append(label(x+badge_width/2,y+20,role,13,'#9edfc9','text-anchor="middle"'))
    parts.append(label(center,footer_y,"[ SYSTEM ONLINE ]   [ AI ENGINEERING ]   [ BACKEND SYSTEMS ]",11,MUTED,'text-anchor="middle"'))
    parts.append('<style>@media(prefers-reduced-motion:reduce){g{display:none}.fallback{display:block!important}}</style>')
    parts.append('<g class="fallback" style="display:none">'+label(center,88,CFG["roles"][0],19,INK,'text-anchor="middle"')+'</g>')
    return document(int(center*2),banner_height,"Navneet Tripathi — "+', '.join(CFG['roles']),"".join(parts))


def logo(slug, x, y, size, prefix):
    icons = ROOT / "profile" / "icons"
    available = {item["slug"]:item for item in json.loads((icons/"manifest.json").read_text(encoding="utf-8"))}
    item = available[slug]
    icon = ET.fromstring((icons/f"{slug}.svg").read_text(encoding="utf-8"))
    ids = {node.get("id"):f'{prefix}-{node.get("id")}' for node in icon.iter() if node.get("id")}
    for node in icon.iter():
        for key,value in list(node.attrib.items()):
            if key == "id":
                node.set(key,ids[value])
            else:
                for previous,new in ids.items():
                    value = value.replace(f"url(#{previous})",f"url(#{new})")
                    if value == "#"+previous:
                        value = "#"+new
                node.set(key,value)
        if slug in ["express","github","aws"] and node.tag.endswith("path"):
            if node.get("fill","#000000").lower() in ["#000","#000000","#181616","#252f3e","#253b4b"]:
                node.set("fill",INK)
    if item.get("library") == "Simple Icons":
        color = item["color"]
        # Use a contrasting monochrome variant for dark brand marks; the
        # downloaded path geometry remains completely unchanged.
        if slug in ["ollama","modelcontextprotocol","numpy","pandas"]:
            color = "#e6edf3"
        icon.set("fill",color)
    icon.set("x",str(x)); icon.set("y",str(y))
    icon.set("width",str(size)); icon.set("height",str(size))
    return ET.tostring(icon,encoding="unicode")


def tech_stack(category="software", columns=9, width=1000):
    selected = {
        "software":["python","java","javascript","typescript","react","nextjs","nodejs","express","fastapi",
                    "postgresql","mysql","redis","mongodb","docker","git","linux","aws","githubactions"],
        "ai":["langchain","langgraph","modelcontextprotocol","huggingface","ollama",
              "googlegemini","scikitlearn","numpy","pandas","opencv"],
    }[category]
    available = {item["slug"]:item for item in json.loads((ROOT/"profile/icons/manifest.json").read_text(encoding="utf-8"))}
    cell = (104 if columns == 9 else 192) if width == 1000 else (80 if columns == 6 else 96)
    tile = 76 if width == 1000 else (58 if columns == 6 else 64)
    size = 48 if width == 1000 else 38
    row_height = 110 if width == 1000 else 94
    height = ((len(selected)+columns-1)//columns)*row_height+20
    parts = [f'<rect width="{width}" height="{height}" rx="12" fill="{BG}"/>']
    ET.register_namespace("","http://www.w3.org/2000/svg")
    for i,slug in enumerate(selected):
        x = (width-columns*cell)/2+(i%columns)*cell+(cell-tile)/2
        y = 12+(i//columns)*row_height
        parts.append(f'<rect x="{x}" y="{y}" width="{tile}" height="{tile}" rx="14" fill="#1c2531"/>')
        parts.append(logo(slug,x+(tile-size)/2,y+(tile-size)/2,size,f"{category}-{i}"))
        parts.append(label(x+tile/2,y+tile+20,available[slug]["label"],11 if width==1000 else 9,MUTED,'text-anchor="middle"'))
    title = "Software and backend stack" if category == "software" else "AI, agent engineering and machine learning stack"
    return document(width,height,title,"".join(parts))


def social_badge(slug):
    styles = {
        'github':('GitHub',128,'#18212c','#3b4654','#e6edf3'),
        'linkedin':('LinkedIn',144,'#0a66c2','#3085da','#ffffff'),
        'leetcode':('LeetCode',148,'#25221b','#795522','#ffd08b'),
        'email':(CFG['email'],320,'#2d2029','#79455c','#ffc0d3'),
    }
    name,width,background,border,ink = styles[slug]
    mark = ('<g transform="translate(12 9)" fill="none" stroke="#ffacc9" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="20" height="16" rx="3"/><path d="m2 5 9 7 9-7"/></g>'
            if slug=='email' else logo(slug,12,9,22,'social-'+slug))
    body = (f'<rect x=".5" y=".5" width="{width-1}" height="39" rx="7" fill="{background}" stroke="{border}"/>'
            +mark+label(45,25,name,13 if slug=='email' else 14,ink,'font-weight="bold"'))
    return document(width,40,name,body)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, shades = portrait_rows()
    (OUT / "portrait.txt").write_text("\n".join(rows)+"\n", encoding="utf-8")
    (OUT / "portrait.svg").write_text(portrait_art(rows,shades),encoding="utf-8")
    (OUT / "portrait-static.svg").write_text(portrait_art(rows,shades,True),encoding="utf-8")
    (OUT / "info-card.svg").write_text(document(544, 540, "Navneet Tripathi's neofetch profile", info()), encoding="utf-8")
    mobile = '<g transform="translate(52 0)">'+portrait(rows, shades)+'</g><g transform="translate(0 556)">'+info()+'</g>'
    (OUT / "terminal-profile-mobile.svg").write_text(document(544, 1096, "Navneet's ASCII portrait and profile, stacked for mobile", mobile), encoding="utf-8")
    for static in [False, True]:
        name = "terminal-profile-static.svg" if static else "terminal-profile.svg"
        body = portrait(rows, shades, static) + '<g transform="translate(456 0)">'+info()+'</g>'
        (OUT / name).write_text(document(1000, 540, "Navneet Tripathi — ASCII portrait and neofetch profile", body), encoding="utf-8")
    (OUT / "header.svg").write_text(banner(), encoding="utf-8")
    (OUT / "header-mobile.svg").write_text(banner(540),encoding="utf-8")
    for network in ['github','linkedin','leetcode','email']:
        (OUT/f'social-{network}.svg').write_text(social_badge(network),encoding='utf-8')
    (OUT / "tech-stack.svg").write_text(tech_stack(), encoding="utf-8")
    (OUT / "tech-stack-mobile.svg").write_text(tech_stack("software",6,492), encoding="utf-8")
    (OUT / "ai-stack.svg").write_text(tech_stack("ai",5), encoding="utf-8")
    (OUT / "ai-stack-mobile.svg").write_text(tech_stack("ai",5,492), encoding="utf-8")
    print("Generated portrait, neofetch panel, combined terminal and animated header.")


if __name__ == "__main__":
    main()
