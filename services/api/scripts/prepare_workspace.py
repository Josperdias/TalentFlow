"""Extract the original offline SPA into a guarded, same-origin connected frontend."""
from pathlib import Path
from bs4 import BeautifulSoup
import json

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'reference'/'TalentFlow-People-v1.1.html'
html=source.read_text(encoding='utf-8')
soup=BeautifulSoup(html,'html.parser')
scripts=soup.find_all('script')
assert len(scripts)==2 and scripts[0].get('id')=='seed'
seed=json.loads(scripts[0].text)
(ROOT/'private_demo_seed.json').write_text(json.dumps(seed,ensure_ascii=False),encoding='utf-8')
js=scripts[1].text
old="let state;try { state=JSON.parse(localStorage.getItem(KEY))||clone(SEED);if(!state.jobs||!state.applications)throw Error(); } catch {state=clone(SEED)}"
new="""const CONNECTED=location.pathname==='/workspace';
let state;
if(CONNECTED){state=clone(SEED);}else {try {state=JSON.parse(localStorage.getItem(KEY))||clone(SEED);if(!state.jobs||!state.applications)throw Error();}catch{state=clone(SEED)}}
const cloud={version:null,csrf:null,busy:false,pending:false,halt:false,timer:null,savedAt:null};
"""
assert js.count(old)==1
js=js.replace(old,new)
old_save="function save(){try{localStorage.setItem(KEY,JSON.stringify(state))}catch(e){notify('Armazenamento indisponível: alterações apenas nesta sessão',true)}}"
new_save="""function save(){
 if(CONNECTED){cloud.pending=true;cloudStatus('Alterações pendentes...', 'warning');clearTimeout(cloud.timer);cloud.timer=setTimeout(cloudSave,360);return;}
 try{localStorage.setItem(KEY,JSON.stringify(state))}catch(e){notify('Armazenamento indisponível: alterações apenas nesta sessão',true)}
}
function cloudStatus(message,type){
 let status=document.getElementById('tfCloudStatus');if(!status)return;
 status.textContent=message;status.dataset.type=type||'ok';
}
async function cloudRequest(path,options={}){
 const headers={'Accept':'application/json',...(options.method?{'Content-Type':'application/json','X-TF-CSRF':cloud.csrf}:{}),...(options.headers||{})};
 const response=await fetch(path,{...options,headers,credentials:'same-origin',cache:'no-store'});
 if(response.status===401){location.href='/login';throw Error('Sessão expirada')}
 const body=await response.json().catch(()=>({}));
 if(!response.ok){const detail=body.detail;const error=new Error(typeof detail==='string'?detail:(detail?.message||'Erro ao sincronizar'));
 error.status=response.status;error.payload=detail;throw error}
 return body;
}
async function cloudBoot(){
 document.getElementById('tfCloudStatus')?.remove();
 const badge=document.createElement('div');badge.id='tfCloudStatus';badge.setAttribute('role','status');badge.textContent='Conectando ao servidor...';
 document.body.appendChild(badge);
 try{
  const csrf=await cloudRequest('/api/auth/csrf');cloud.csrf=csrf.token;
  const remote=await cloudRequest('/api/workspace/state');cloud.version=remote.version;
  state=remote.state;jobId=state.jobs?.[0]?.id||null;
  render();cloudStatus('✓ Salvo no servidor · versão '+cloud.version);
 }catch(err){cloud.halt=true;document.querySelector('.layout')?.replaceChildren();cloudStatus('Não foi possível abrir os dados. '+err.message,'error');}
}
async function cloudSave(){
 if(!CONNECTED||cloud.halt||cloud.busy||!cloud.pending||cloud.version===null)return;
 cloud.busy=true;cloud.pending=false;const copy=JSON.parse(JSON.stringify(state));
 cloudStatus('Salvando no servidor...','warning');
 try{
  const result=await cloudRequest('/api/workspace/state',{method:'POST',body:JSON.stringify({version:cloud.version,data:copy})});
  cloud.version=result.version;cloud.savedAt=result.updated_at;
  cloudStatus(cloud.pending?'Alterações pendentes...':'✓ Salvo no servidor · versão '+cloud.version,cloud.pending?'warning':'ok');
 }catch(err){
  cloud.halt=true;cloud.pending=true;
  cloudStatus(err.status===409?'Conflito entre sessões. Exporte seu estado antes de recarregar.':'Erro ao salvar. Exporte um backup. '+err.message,'error');
  const panel=document.getElementById('tfCloudError')||document.createElement('div');
  panel.id='tfCloudError';panel.className='tfCloudError';
  const msg=document.createElement('p');msg.textContent=err.status===409?'Outra sessão modificou estes dados. Salve uma cópia local para comparar antes de recarregar.':'A conexão falhou. As últimas alterações ainda não estão no servidor.';
  const backup=document.createElement('button');backup.type='button';backup.textContent='Exportar meu estado';
  backup.addEventListener('click',()=>{
   const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='talentflow-backup-nao-sincronizado.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
  });
  const reload=document.createElement('button');reload.type='button';reload.textContent='Recarregar dados do servidor';reload.addEventListener('click',()=>location.reload());
  panel.replaceChildren(msg,backup,reload);document.body.appendChild(panel);
 }finally{
  cloud.busy=false;if(cloud.pending&&!cloud.halt){clearTimeout(cloud.timer);cloud.timer=setTimeout(cloudSave,200);}
 }
}
window.addEventListener('beforeunload',event=>{if(CONNECTED&&(cloud.pending||cloud.busy)){event.preventDefault();event.returnValue='';}});
"""
assert js.count(old_save)==1
js=js.replace(old_save,new_save)
assert js.endswith('render();\n})();')
js=js[:-len('render();\n})();')]+"(CONNECTED?cloudBoot():render());\n})();"
(ROOT/'web'/'workspace.js').write_text(js,encoding='utf-8')
# Preserve original HTML exactly except replacing executable script with an external script;
# browser executes it under script-src 'self' (no unsafe-inline).
start=html.index('<script>(() => {');end=html.rfind('</script>')
assert start>=0 and end>=0
output=html[:start]+'<script src="/assets/workspace.js" defer></script>'+html[end+len('</script>'):]
output=output.replace('</style></head>', '''#tfCloudStatus{position:fixed;z-index:200;bottom:12px;right:12px;border:1px solid #cbd6ed;background:#e8f9ef;color:#136b49;padding:9px 14px;border-radius:9px;font-size:12px;box-shadow:0 3px 15px #15234018}#tfCloudStatus[data-type=warning]{background:#fff4db;color:#865a13}#tfCloudStatus[data-type=error]{background:#ffe9e9;color:#a32937}.tfCloudError{position:fixed;z-index:300;bottom:60px;right:10px;background:white;border:2px solid #b83f48;border-radius:12px;padding:18px;width:min(95vw,370px);box-shadow:0 10px 50px #0003}.tfCloudError button{padding:9px;background:#6b5cc9;border:0;color:white;border-radius:7px;margin:4px;cursor:pointer}
</style></head>''',1)
(ROOT/'private_views').mkdir(exist_ok=True)
(ROOT/'private_views'/'workspace.html').write_text(output,encoding='utf-8')
print('Workspace HTML',len(output),'JS',len(js),'seed',len(json.dumps(seed)))
