"""Chromium visual/interaction check; mocks only transport due to blocked loopback navigation.
Server authentication + DB persistence are exercised independently in tests/.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'private_views/workspace.html').read_text()
js=(ROOT/'web/workspace.js').read_text().replace("const CONNECTED=location.pathname==='/workspace';","const CONNECTED=true;")
html=html.replace('<script src="/assets/workspace.js" defer></script>',f'<script>{js}</script>')
state=json.loads((ROOT/'private_demo_seed.json').read_text())
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
    for width,height in [(1440,900),(390,844)]:
        context=browser.new_context(viewport={'width':width,'height':height})
        page=context.new_page();errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        # Mock browser fetch. The endpoint/SQL/auth behavior is exercised by TestClient tests.
        page.evaluate('''(seed)=>{
          window._tfServerState=seed;window._tfServerVersion=1;window._tfWrites=[];
          window.fetch=async function(path,opt={}){
            let data;
            if(path==='/api/auth/csrf')data={token:'testing-csrf'};
            else if(path==='/api/workspace/state'&&!opt.method)data={state:window._tfServerState,version:window._tfServerVersion};
            else if(path==='/api/workspace/state'&&opt.method){
              const req=JSON.parse(opt.body);window._tfServerState=req.data;window._tfServerVersion++;window._tfWrites.push(req);data={version:window._tfServerVersion,updated_at:new Date().toISOString()};
            }else throw Error('Unexpected route '+path);
            return new Response(JSON.stringify(data),{status:200,headers:{'Content-Type':'application/json'}});
          }
        }''',state)
        page.set_content(html,wait_until='load',timeout=30000)
        page.wait_for_timeout(700)
        cloud=page.locator('#tfCloudStatus').inner_text()
        print(width,'status',cloud,'errors',errors[:2],'home heading',page.locator('#content h1').first.inner_text())
        assert 'Salvo no servidor' in cloud and not errors
        navroot='#sidebar' if width>700 else '#mobileNav'
        page.locator(f'{navroot} [data-nav="jobs"]').click()
        page.wait_for_timeout(100)
        assert 'Vagas' in page.locator('#content h1').first.inner_text()
        if width>700:
            page.locator('[data-action="job-new"]').first.click()
            print('FORM',page.locator('#modalRoot').inner_text()[:180].replace('\n',' '))
            # The action validates and changes the central state.
            page.locator('#f_title').fill('Vaga QA conectada')
            page.locator('#modalForm button[type=submit]').click()
            page.wait_for_timeout(850)
            print('WRITES',page.evaluate('window._tfWrites.length'),'status',page.locator('#tfCloudStatus').inner_text())
            assert page.evaluate('window._tfWrites.length')>=1
            assert any(x['title']=='Vaga QA conectada' for x in page.evaluate('window._tfServerState.jobs'))
            assert not errors
        else:
            print('overflow mobile',page.evaluate('document.documentElement.scrollWidth-window.innerWidth'))
        page.screenshot(path=str(ROOT/f'docs/workspace-connected-{width}.png'),full_page=False)
        context.close()
    browser.close()
print('Frontend mocked-transport Chromium test PASS')
