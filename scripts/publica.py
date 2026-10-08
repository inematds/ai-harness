"""Publica as duas versões do vídeo AI harness (explicavideos v2, refazvideo) em inematds/ai-harness.
Release video-v2.0.0 (MP4 + SRT de cada versão) + Pages: videos/index.html com 2 players, capítulos e legendas VTT.
Uso: python3 scripts/publica.py
Idempotente: sobe só o que mudou de tamanho; commit só se houver diff. Adaptado de gestor-de-agentes/scripts/publica.py."""
import html, json, re, subprocess, sys, time, urllib.request
from pathlib import Path

ID = 'ai-harness'
OUT = Path.home() / 'projetos/output/explica-lNum1UFDYn0'
REPO = Path(__file__).resolve().parent.parent
GH = f'inematds/{ID}'
TAG = 'video-v2.0.0'
BASE = f'https://github.com/{GH}/releases/download/{TAG}/'
PAGES = f'https://inematds.github.io/{ID}/'
TITLE = 'AI harness: quem faz o trabalho da IA'
H1 = 'Não é o modelo que trabalha: <b>é o harness.</b>'
LEAD = ('O modelo de IA sozinho é um cérebro num pote: só lê e escreve texto. Quem faz o trabalho no Claude Code e no Codex '
        'é o que existe em volta dele, o harness. O vídeo mostra as cinco partes (contexto, memória, ferramentas, verificação '
        'e permissões), o loop do agente e o que vem por aí. Duas versões com a mesma fala: quadro branco e telas profissionais.')
VERSOES = [
    dict(k='quadro-branco', nome='Versão quadro branco', v2=OUT / 'v2'),
    dict(k='profissional', nome='Versão telas profissionais', v2=OUT / 'v2-pro'),
]


def sh(*a, **kw):
    return subprocess.run(a, check=True, text=True, capture_output=True, **kw).stdout


def dur(p):
    return float(sh('ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)))


def main():
    stage = OUT / 'release'; stage.mkdir(exist_ok=True)
    assets, cards, delivery = [], [], {}
    folder = REPO / 'videos'; folder.mkdir(exist_ok=True)
    for v in VERSOES:
        V2 = v['v2']
        rec = json.loads((V2 / 'verification/assembled-pt.json').read_text())
        full = Path(rec['file'])
        assert full.stat().st_size == rec['bytes'] and (V2 / 'verification/decode-full-pt.log').read_text() == ''
        for b in rec['blocks']:
            assert json.loads((V2 / f'final/{b}/alignment.json').read_text())['ratio'] > .90, b
        scenes = json.loads((V2 / 'docs/lesson-pt.json').read_text())
        assert len(rec['chapters']) == len(scenes)
        chapters = [(int(c['time']), scenes[c['scene'] - 1]['title']) for c in rec['chapters']]
        name = f'{ID}-{v["k"]}-16x9'
        d = dur(full); dd = f"{int(d // 60)}min{int(d % 60):02d}s"
        for src, ext in ((full, 'mp4'), (full.with_suffix('.srt'), 'srt')):
            dst = stage / f'{name}.{ext}'
            if not dst.exists() or dst.stat().st_size != src.stat().st_size:
                dst.write_bytes(src.read_bytes())
            assets.append(dst)
        (folder / f'{v["k"]}.vtt').write_text('WEBVTT\n\n' + re.sub(r'(\d\d:\d\d:\d\d),(\d{3})', r'\1.\2', full.with_suffix('.srt').read_text()))
        caps = ''.join(f'<button type="button" data-time="{s}">{s // 60:02d}:{s % 60:02d} · {html.escape(c)}</button>' for s, c in chapters)
        cards.append(f'''<section class="card" id="{v["k"]}"><h2>{v["nome"]} <span>{dd}</span></h2>
<video controls preload="metadata" playsinline><source src="{BASE}{name}.mp4" type="video/mp4"><track default kind="subtitles" src="{v["k"]}.vtt" srclang="pt" label="Português"></video>
<p><a href="{BASE}{name}.mp4">Baixar MP4</a> · <a href="{BASE}{name}.srt">Baixar legendas</a></p>
<details><summary>Capítulos</summary>{caps}</details></section>''')
        delivery[v['k']] = {'url': BASE + name + '.mp4', 'srt': BASE + name + '.srt', 'duration': round(d, 2)}
    if subprocess.run(['gh', 'release', 'view', TAG, '--repo', GH], capture_output=True).returncode:
        notes = stage / 'RELEASE.md'
        notes.write_text(f'{TITLE} — vídeo com avatar e voz do Nei, telas refeitas em português e legendas. Duas versões: quadro branco e telas profissionais.\n\n'
                         f'Assistir: {PAGES}videos/\n\nProdução: https://inematds.github.io/explicavideos/guia/ (Explicavideos v2)\n\n'
                         'Fonte: vídeo de Nick Saraev no YouTube.')
        sh('gh', 'release', 'create', TAG, '--repo', GH, '--draft', '--title', f'{TITLE} (vídeo v2)', '--notes-file', str(notes))
    have = {a['name']: a['size'] for a in json.loads(sh('gh', 'release', 'view', TAG, '--repo', GH, '--json', 'assets'))['assets']}
    for f in assets:
        if have.get(f.name) != f.stat().st_size:
            print('upload', f.name, flush=True); sh('gh', 'release', 'upload', TAG, str(f), '--repo', GH, '--clobber')
    page = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(TITLE)} · INEMA.CLUB</title><meta name="description" content="{html.escape(LEAD)}">
<style>:root{{color-scheme:dark}}*{{box-sizing:border-box}}body{{margin:0;background:#0D1321;color:#F0EBD8;font:18px/1.6 system-ui,sans-serif}}main{{max-width:1100px;margin:auto;padding:32px 16px}}
a{{color:#FFC300}}h1{{font-size:clamp(1.8rem,5vw,2.8rem);line-height:1.15;margin:.4em 0}}h1 b{{color:#FFC300}}.lead{{color:#b9c3d0;max-width:780px}}
.card{{background:#1D2D44;border:1px solid #3E5C76;border-radius:16px;padding:20px;margin:28px 0}}.card h2{{margin:0 0 4px;font-size:1.3rem}}.card h2 span{{color:#748CAB;font-size:1rem;font-weight:500}}
video{{width:100%;aspect-ratio:16/9;background:#0a0f19;border-radius:12px}}
summary{{cursor:pointer;color:#FFC300;margin-top:8px}}button{{display:block;background:#0D1321;color:#F0EBD8;border:1px solid #3E5C76;border-radius:8px;padding:10px 12px;margin:6px 0;text-align:left;cursor:pointer;width:100%;font:inherit}}
:focus-visible{{outline:3px solid #FFC300;outline-offset:3px}}footer{{color:#748CAB;font-size:15px;margin-top:40px}}</style></head>
<body><main><nav><a href="https://inema.club">INEMA.CLUB</a> · <a href="https://github.com/{GH}">GitHub</a></nav>
<h1>{H1}</h1>
<p class="lead">{html.escape(LEAD)}</p>
{"".join(cards)}
<footer>Fonte: vídeo de Nick Saraev no YouTube. Telas refeitas em português e produzidas com o <a href="https://inematds.github.io/explicavideos/guia/">Explicavideos v2</a>. Conteúdo aberto e gratuito do <a href="https://inema.club">INEMA.CLUB</a>.</footer></main>
<script>document.querySelectorAll('[data-time]').forEach(b=>b.addEventListener('click',()=>{{const v=b.closest('.card').querySelector('video');v.currentTime=Number(b.dataset.time);v.play();}}));</script></body></html>
'''
    (folder / 'index.html').write_text(page)
    (REPO / 'index.html').write_text(f'<!doctype html><meta charset="utf-8"><title>{html.escape(TITLE)}</title><meta http-equiv="refresh" content="0; url=videos/"><a href="videos/">Assistir</a>\n')
    (folder / 'delivery.json').write_text(json.dumps(delivery, indent=2) + '\n')
    g = lambda *a: sh('git', '-c', 'user.name=inematds', '-c', 'user.email=inematds@gmail.com', *a, cwd=REPO)
    g('add', '-A')
    if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=REPO).returncode:
        g('commit', '-m', f'feat: {TITLE} em vídeo (v2, duas versões)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>')
        g('push', '-q', 'origin', 'HEAD:main')
    sh('gh', 'release', 'edit', TAG, '--repo', GH, '--draft=false')
    for n in delivery.values():
        with urllib.request.urlopen(urllib.request.Request(n['url'], method='HEAD'), timeout=60) as r:
            assert r.status == 200
    for _ in range(40):
        try:
            with urllib.request.urlopen(PAGES + 'videos/delivery.json?v=' + str(int(time.time())), timeout=30) as f:
                if 'profissional' in f.read().decode():
                    break
        except Exception:
            pass
        time.sleep(30)
    else:
        sys.exit('push e release feitos; Pages ainda não respondeu')
    print('OK', PAGES + 'videos/')


if __name__ == '__main__':
    main()
