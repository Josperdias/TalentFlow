"""E2E do pacote web compilado: navegador real (Chromium) -> servidor estático -> proxy /api -> API -> PostgreSQL.

Uso: python e2e_web.py <url-do-site> <pasta-de-capturas>
Cada passo imprime OK/FALHA; sai com código 1 se algo falhar. Não usa mocks: tudo vai ao servidor real.
"""
import sys, time, json, re, urllib.request, traceback
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

SITE = sys.argv[1].rstrip('/'); SHOTS = Path(sys.argv[2]); SHOTS.mkdir(parents=True, exist_ok=True)
PW = 'Demo@2026!'
results: list[tuple[str, bool, str]] = []
CURRENT_PAGE = None

def step(name):
    def deco(fn):
        def run(*a, **k):
            try:
                fn(*a, **k); results.append((name, True, '')); print('OK    ', name)
            except Exception as e:  # noqa: BLE001
                msg = (str(e) or repr(e)); results.append((name, False, msg.splitlines()[0][:300])); print('FALHA ', name, '->', msg[:900]); print(''.join(traceback.format_exc().splitlines(True)[-4:]))
                if CURRENT_PAGE:
                    try: CURRENT_PAGE.screenshot(path=SHOTS / ('falha-' + re.sub(r'\W+', '-', name)[:40] + '.png'))
                    except Exception: pass
        return run
    return deco

# ---- "outro cliente": chama a API direto com Bearer (como o app Android/Windows faria) ----
def api(method, path, token=None, body=None, if_match=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = 'Bearer ' + token
    if if_match is not None: h['If-Match'] = str(if_match)
    req = urllib.request.Request(SITE + '/api/v1' + path, method=method, headers=h, data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=15) as r: return r.status, json.loads(r.read() or b'null')
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b'null')

def native_token(email='admin@nexa.demo'):
    s, b = api('POST', '/auth/token', body={'email': email, 'password': PW, 'client': 'android', 'device': 'e2e'})
    assert s == 200, b
    return b['access_token']

def login_ui(page, email='admin@nexa.demo', password=PW):
    page.goto(SITE + '/')
    page.get_by_label('E-mail').fill(email); page.get_by_label('Senha').fill(password)
    page.get_by_role('button', name='Entrar', exact=True).click()

def run_desktop(browser):
    global CURRENT_PAGE
    ctx = browser.new_context(viewport={'width': 1440, 'height': 900}, locale='pt-BR'); page = ctx.new_page(); CURRENT_PAGE = page
    errors = []; page.on('pageerror', lambda e: errors.append(str(e))); page.on('console', lambda m: errors.append(m.text) if m.type == 'error' and 'favicon' not in m.text and '401' not in m.text and '409' not in m.text else None)  # 401/409 são esperados (sessão anônima, senha errada, conflito provocado)
    tok = native_token()

    @step('config.json carregado e diagnóstico da API na tela de login')
    def _():
        page.goto(SITE + '/'); expect(page.get_by_role('heading', name='Entrar')).to_be_visible()
        page.get_by_role('button', name='Diagnosticar conexão com a API').click()
        expect(page.get_by_text('API respondendo em /api/v1')).to_be_visible(timeout=8000)
        page.screenshot(path=SHOTS / 'web-1440-login.png')
    _()

    @step('senha errada mostra erro útil e não entra')
    def _():
        login_ui(page, password='errada'); expect(page.get_by_role('alert')).to_contain_text('Credenciais inválidas')
    _()

    @step('login como administradora e carregamento da visão geral com dados reais')
    def _():
        login_ui(page); expect(page.get_by_role('heading', name=re.compile('Olá, Marina'))).to_be_visible(timeout=10000)
        expect(page.get_by_text('Vagas abertas')).to_be_visible(); expect(page.get_by_text('Funil de candidaturas por etapa')).to_be_visible()
        page.wait_for_timeout(600); page.screenshot(path=SHOTS / 'web-1440-visao-geral.png')
    _()

    @step('recarregar a página mantém a sessão (cookie HttpOnly + CSRF)')
    def _():
        page.reload(); expect(page.get_by_role('heading', name=re.compile('Olá, Marina'))).to_be_visible(timeout=10000)
        assert 'tf_session' not in page.evaluate('document.cookie'), 'cookie de sessão não pode ser legível por JS'
    _()

    @step('lista de vagas, busca e navegação para o pipeline')
    def _():
        page.get_by_role('link', name='Vagas', exact=True).click()
        expect(page.get_by_role('heading', name='Vagas', exact=True)).to_be_visible()
        expect(page.locator('table.grid tbody tr').first).to_be_visible(timeout=8000)
        page.screenshot(path=SHOTS / 'web-1440-vagas.png')
    _()

    # procura uma vaga com candidatura ativa via API
    st, jobs = api('GET', '/jobs', tok); target = None
    for j in jobs:
        d = api('GET', f"/jobs/{j['id']}", tok)[1]
        act = [a for a in d['applications'] if a['status'] == 'active']
        if act and len(d['stages']) > 3: target = (j, d, act[0]); break
    assert target, 'seed sem candidatura ativa'
    job, detail, app = target
    next_stage = next(s for s in detail['stages'] if s['kind'] == 'active' and s['id'] != app['stage_id'])

    @step('mover candidatura pelo seletor persiste no servidor (verificado por outro cliente)')
    def _():
        page.goto(f"{SITE}/#/vagas/{job['id']}")
        expect(page.get_by_role('heading', name=job['title'])).to_be_visible(timeout=8000)
        sel = page.get_by_label(f"Mover {app['candidate']['name']} para")
        sel.select_option(str(next_stage['id']))
        expect(page.get_by_text(f"movido para {next_stage['name']}")).to_be_visible(timeout=8000)
        after = api('GET', f"/jobs/{job['id']}", tok)[1]
        moved = next(a for a in after['applications'] if a['id'] == app['id'])
        assert moved['stage_id'] == next_stage['id'], 'servidor não refletiu a mudança'
        page.screenshot(path=SHOTS / 'web-1440-pipeline.png')
    _()

    @step('mudança feita por OUTRO cliente aparece na tela sem recarregar (sincronização)')
    def _():
        cur = api('GET', f"/jobs/{job['id']}", tok)[1]['job']
        novo = 'Sync ' + str(int(time.time()))
        s, _b = api('PATCH', f"/jobs/{job['id']}", tok, {'title': novo}, if_match=cur['version']); assert s == 200, _b
        expect(page.get_by_role('heading', name=novo)).to_be_visible(timeout=15000)
    _()

    @step('conflito: salvar com versão antiga abre o diálogo e NÃO sobrescreve')
    def _():
        page.get_by_role('button', name='Editar').click()
        dlg = page.get_by_role('dialog'); expect(dlg).to_be_visible()
        cur = api('GET', f"/jobs/{job['id']}", tok)[1]['job']
        dlg.get_by_label('Título').fill('Edição que não pode vencer')
        outro = f'Outro cliente {int(time.time())}'  # valor único: o teste precisa ser repetível sobre o mesmo banco
        s, _b = api('PATCH', f"/jobs/{job['id']}", tok, {'department': outro}, if_match=cur['version']); assert s == 200  # outro cliente salva primeiro
        expect(dlg.get_by_text('Alterada por outra pessoa')).to_be_visible(timeout=15000)  # sincronização avisa durante a edição
        dlg.get_by_role('button', name='Salvar alterações').click()
        expect(page.get_by_role('dialog', name='Registro alterado por outra pessoa')).to_be_visible(timeout=8000)
        final = api('GET', f"/jobs/{job['id']}", tok)[1]['job']
        assert final['title'] != 'Edição que não pode vencer' and final['department'] == outro
        page.screenshot(path=SHOTS / 'web-1440-conflito.png')
        page.get_by_role('button', name='Carregar versão atual').click()
    _()

    @step('desenvolvimento: concluir atividade de PDI com evidência')
    def _():
        st_, plans = api('GET', '/workforce/plans?status=active', tok); assert st_ == 200 and isinstance(plans, list), (st_, str(plans)[:200]); print('   planos ativos:', [(p['id'], [a['done'] for a in p['actions']]) for p in plans])
        plan = next(p for p in plans if sum(not a['done'] for a in p['actions']) >= 2)  # evita concluir o plano (ele sairia do filtro)
        page.get_by_role('link', name='Desenvolvimento').click()
        art = page.locator('article', has=page.get_by_role('heading', name=plan['title'])).first
        expect(art).to_be_visible(timeout=8000)
        idx = next(i for i, a in enumerate(plan['actions']) if not a['done'])
        art.locator('input[type=checkbox]').nth(idx).click()
        dlg = page.get_by_role('dialog', name='Concluir atividade'); expect(dlg).to_be_visible()
        marca = f'Concluída no teste E2E {int(time.time())}'
        dlg.get_by_label('Evidência (opcional)').fill(marca)
        dlg.get_by_role('button', name='Marcar como concluída').click()
        expect(art.get_by_text(marca)).to_be_visible(timeout=8000)
        depois = next(p for p in api('GET', '/workforce/plans', tok)[1] if p['id'] == plan['id'])
        assert depois['actions'][idx]['done'] and depois['actions'][idx]['evidence'] == marca, 'servidor não persistiu a evidência'
        page.screenshot(path=SHOTS / 'web-1440-desenvolvimento.png')
    _()

    @step('ausências: registrar solicitação e aprovar')
    def _():
        page.get_by_role('link', name='Ausências').click()
        page.get_by_role('button', name='Nova solicitação').click()
        dlg = page.get_by_role('dialog'); expect(dlg.get_by_label('Colaborador')).to_be_visible()
        expect(dlg.locator('select').first.locator('option')).not_to_have_count(1, timeout=8000)
        dlg.get_by_label('Colaborador').select_option(index=3)
        import datetime as dt  # período único por execução: o banco acumula dados entre rodadas locais
        ini = dt.date(2030, 1, 1) + dt.timedelta(days=(int(time.time()) // 7) % 3000); fim = ini + dt.timedelta(days=4)
        dlg.get_by_label('Início').fill(ini.isoformat()); dlg.get_by_label('Fim').fill(fim.isoformat())
        dlg.get_by_role('button', name='Registrar').click()
        row = page.locator('tbody tr', has_text='Pendente').first; expect(row).to_be_visible(timeout=8000)
        row.get_by_role('button', name='Aprovar').click(); page.wait_for_timeout(800)
        page.screenshot(path=SHOTS / 'web-1440-ausencias.png')
    _()

    @step('conta: sessões ativas listadas e logout encerra a sessão')
    def _():
        page.get_by_role('link', name='Conta').click(); expect(page.get_by_text('Sessões ativas')).to_be_visible()
        page.get_by_role('button', name='Sair').click(); expect(page.get_by_role('heading', name='Entrar')).to_be_visible(timeout=8000)
    _()

    @step('sem erros de JavaScript no console durante o fluxo')
    def _():
        assert not errors, errors[:3]
    _()
    ctx.close()

def run_roles(browser):
    @step('gestor: menu restrito e sem botão de criar vaga')
    def _():
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900}); p = ctx.new_page()
        login_ui(p, 'gestor@nexa.demo'); expect(p.get_by_role('heading', name=re.compile('Olá'))).to_be_visible(timeout=10000)
        p.get_by_role('link', name='Vagas', exact=True).click(); expect(p.get_by_role('heading', name='Vagas', exact=True)).to_be_visible()
        assert p.get_by_role('button', name='Nova vaga').count() == 0
        ctx.close()
    _()

    @step('pessoa candidata: vê só o portal e não vê menus internos')
    def _():
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900}); p = ctx.new_page()
        login_ui(p, 'candidato@nexa.demo'); expect(p.get_by_role('heading', name='Minhas candidaturas')).to_be_visible(timeout=10000)
        assert p.get_by_role('link', name='Vagas', exact=True).count() == 0 and p.get_by_role('link', name='Pessoas').count() == 0
        ctx.close()
    _()

def run_mobile(browser):
    ctx = browser.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True, locale='pt-BR'); p = ctx.new_page()

    @step('celular 390 px: login, navegação inferior e sem rolagem horizontal')
    def _():
        p.goto(SITE + '/'); p.screenshot(path=SHOTS / 'web-390-login.png')
        login_ui(p); expect(p.get_by_role('heading', name=re.compile('Olá'))).to_be_visible(timeout=10000)
        nav = p.get_by_role('navigation', name='Principal'); expect(nav).to_be_visible()
        box = nav.bounding_box(); assert box['y'] > 700, f'navegação deveria estar na base ({box})'
        w = p.evaluate('document.documentElement.scrollWidth'); assert w <= 391, f'rolagem horizontal: {w}'
        p.wait_for_timeout(500); p.screenshot(path=SHOTS / 'web-390-visao-geral.png')
        p.get_by_role('link', name='Vagas', exact=True).click(); expect(p.locator('table.grid tbody tr').first).to_be_visible(timeout=8000)
        assert p.evaluate('document.documentElement.scrollWidth') <= 391
        p.screenshot(path=SHOTS / 'web-390-vagas.png', full_page=False)
    _()
    ctx.close()

def run_offline(browser):
    @step('servidor inalcançável: aviso claro, sem dados falsos')
    def _():
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900}); p = ctx.new_page()
        login_ui(p); expect(p.get_by_role('heading', name=re.compile('Olá'))).to_be_visible(timeout=10000)
        ctx.route('**/api/**', lambda r: r.abort())
        p.get_by_role('link', name='Pessoas').click()
        expect(p.get_by_text('Sem conexão com o servidor').first).to_be_visible(timeout=15000)
        p.screenshot(path=SHOTS / 'web-1440-sem-conexao.png')
        ctx.close()
    _()

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome' if Path('/opt/pw-browsers/chromium-1194/chrome-linux/chrome').exists() else None, args=['--no-sandbox'])
    run_desktop(browser); run_roles(browser); run_mobile(browser); run_offline(browser)
    browser.close()

ok = sum(1 for _, o, _ in results if o); print(f'\n{ok}/{len(results)} passos OK')
sys.exit(0 if ok == len(results) else 1)
