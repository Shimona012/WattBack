(function(){
'use strict';
const $=(s,r)=>(r||document).querySelector(s), R=document.documentElement;
const j=(u,o)=>fetch(u,o).then(r=>r.ok?r.json():Promise.reject(r));
const safe=(n,f)=>{try{f()}catch(e){console.warn('WattBack: '+n+' failed',e)}};   // one broken feature must not stop the rest
const S={get:k=>{try{return localStorage.getItem(k)}catch(e){return null}},set:(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}}};
const openDlg=d=>{if(typeof d.showModal==='function')d.showModal();else d.setAttribute('open','')};
const closeDlg=d=>{if(typeof d.close==='function')d.close();else d.removeAttribute('open')};
const isDark=()=>R.dataset.theme?R.dataset.theme==='dark':(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches);
function applyPrefs(){const g=(k,f)=>S.get(k)||f,t=g('wb_theme','auto');
  if(t==='auto')delete R.dataset.theme;else R.dataset.theme=t;
  R.dataset.lights=g('wb_lights','on');R.dataset.size=g('wb_size','md');R.dataset.glass=g('wb_glass','on')}
safe('prefs',applyPrefs);
if(!document.querySelector('link[href="/static/site.css"]')){const L=document.createElement('link');L.rel='stylesheet';L.href='/static/site.css';document.head.appendChild(L)}

// ---------- header with hamburger ----------
let nav;
safe('nav',()=>{
nav=document.createElement('nav');nav.className='site';
nav.innerHTML='<a class="brand" href="/"><b>WattBack</b><small>The light of an idea</small></a>'+
 '<button id="mb" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="mn"><span></span><span></span><span></span></button>'+
 '<div id="mn"><a href="/">Check my bill</a><a href="/admin">GEDA view</a><a href="/about">About</a><a href="/contact">Contact</a>'+
 '<button class="lnk" id="cz" type="button">Customize</button><button class="lnk" id="th" type="button" aria-label="Switch between light and dark theme">Theme</button><span id="auth"></span></div>';
document.body.prepend(nav);
nav.querySelectorAll('#mn>a').forEach(a=>{if(a.getAttribute('href')===location.pathname)a.setAttribute('aria-current','page')});
const mb=$('#mb'),setOpen=o=>{nav.classList.toggle('open',o);mb.setAttribute('aria-expanded',String(o));mb.setAttribute('aria-label',o?'Close menu':'Open menu')};
mb.onclick=()=>setOpen(!nav.classList.contains('open'));
nav.addEventListener('click',e=>{if(e.target.closest&&e.target.closest('#mn>a'))setOpen(false)});
document.addEventListener('click',e=>{if(nav.classList.contains('open')&&!nav.contains(e.target))setOpen(false)});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){setOpen(false);const c=$('#chat');if(c&&c.classList.contains('open'))$('#chatbtn').click()}});
});

// ---------- theme flip ----------
const flip=()=>{R.dataset.theme=isDark()?'light':'dark';S.set('wb_theme',R.dataset.theme);
  const p=$('#pull');if(p){p.classList.add('flash');setTimeout(()=>p.classList.remove('flash'),500)}};
safe('theme',()=>{$('#th').onclick=flip});

// ---------- bulbs and pull cord ----------
safe('bulbs',()=>{
const bl=document.createElement('div');bl.id='bulbs';bl.setAttribute('aria-hidden','true');
bl.innerHTML=[[5,140,'a',7],[24,200,'b',9],[43,110,'a',6],[60,190,'b',8],[78,150,'a',9]]
 .map((v,i)=>'<div class="bulb '+v[2]+'" style="left:'+v[0]+'%;height:'+v[1]+'px;--d:'+v[3]+'s;animation-delay:-'+(i*1.3)+'s"><i style="--f:'+(4+i%3)+'s"></i></div>').join('');
document.body.prepend(bl);
const pl=document.createElement('div');pl.id='pull';
pl.innerHTML='<div class="wire"></div><i class="pb"></i><div class="chain"></div><button id="pc" type="button" aria-label="Pull the light to switch between light and dark theme" title="Pull to switch theme"><span></span></button>';
document.body.prepend(pl);
const ch=$('.chain',pl),pc=$('#pc');let y0=null,dy=0;
const rest=()=>{y0=null;ch.style.transition='';ch.style.setProperty('--pull','0px')};
pc.onpointerdown=e=>{y0=e.clientY;dy=0;try{pc.setPointerCapture(e.pointerId)}catch(x){}ch.style.transition='none'};
pc.onpointermove=e=>{if(y0===null)return;dy=Math.max(0,Math.min(70,e.clientY-y0));ch.style.setProperty('--pull',dy+'px')};
pc.onpointerup=()=>{if(y0===null)return;const go=dy>=28||dy<4;rest();if(go)flip()};
pc.onpointercancel=rest;
pc.onclick=e=>{if(e.detail===0)flip()};   // keyboard
});

// ---------- customize panel ----------
safe('customize',()=>{
const d=document.createElement('dialog');d.className='dlg';d.id='cz-d';
d.innerHTML='<h3>Customize</h3>'+
 '<label>Theme<select data-k="wb_theme" data-f="auto"><option value="auto">Match my device</option><option value="light">Light</option><option value="dark">Dark</option></select></label>'+
 '<label>Background lights<select data-k="wb_lights" data-f="on"><option value="on">Swaying</option><option value="static">Still</option><option value="off">Off</option></select></label>'+
 '<label>Text size<select data-k="wb_size" data-f="md"><option value="md">Normal</option><option value="lg">Large</option><option value="xl">Extra large</option></select></label>'+
 '<label>Glass effect<select data-k="wb_glass" data-f="on"><option value="on">Full</option><option value="off">Simple (faster)</option></select></label>'+
 '<p class="hint">Simple glass and Still or Off lights help on slower devices. Settings stay on this device.</p>'+
 '<div class="acts"><button id="cz-r" type="button" class="ghost">Reset</button><button id="cz-c" type="button">Done</button></div>';
document.body.appendChild(d);
const sel=()=>d.querySelectorAll('select');
const sync=()=>sel().forEach(s=>{s.value=S.get(s.dataset.k)||s.dataset.f});
sel().forEach(s=>s.onchange=()=>{S.set(s.dataset.k,s.value);applyPrefs()});
$('#cz-r',d).onclick=()=>{sel().forEach(s=>S.set(s.dataset.k,s.dataset.f));applyPrefs();sync()};
$('#cz-c',d).onclick=()=>closeDlg(d);
$('#cz').onclick=()=>{sync();openDlg(d);const m=$('#mb');if(m&&nav)nav.classList.remove('open')};
});

// ---------- sign in ----------
async function auth(){
  const a=$('#auth');if(!a)return;
  let cfg,me;try{[cfg,me]=await Promise.all([j('/auth/config'),j('/me')])}catch(e){a.textContent='';return}
  if(me.user){a.innerHTML='<button class="lnk" id="mi" type="button">My insights</button><button class="lnk" id="so" type="button">Sign out</button>';
    $('#so').title=me.user.name||me.user.email;$('#so').onclick=()=>j('/auth/logout',{method:'POST'}).then(()=>location.reload());$('#mi').onclick=insights;return}
  if(cfg.client_id){a.innerHTML='<span id="g"></span>';const s=document.createElement('script');s.src='https://accounts.google.com/gsi/client';s.async=true;
    s.onerror=()=>{a.innerHTML='<span class="blocked" title="Your browser or its shield blocked Google sign-in. Allow accounts.google.com for this site, or try another browser.">Sign-in blocked</span>'};
    s.onload=()=>{try{google.accounts.id.initialize({client_id:cfg.client_id,callback:r=>j('/auth/google',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({credential:r.credential})}).then(()=>location.reload()).catch(()=>alert('Sign-in failed'))});
      google.accounts.id.renderButton($('#g'),{theme:'outline',size:'medium'})}catch(e){s.onerror()}};document.head.appendChild(s)}
  else if(cfg.dev){a.innerHTML='<button class="lnk" id="dv" type="button">Sign in (demo)</button>';$('#dv').onclick=()=>j('/auth/dev',{method:'POST'}).then(()=>location.reload())}
  else a.innerHTML='<span class="blocked">Sign-in not set up</span>'}
async function insights(){
  const d=await j('/me/insights');let dlg=$('#ins');if(!dlg){dlg=document.createElement('dialog');dlg.id='ins';dlg.className='dlg';document.body.appendChild(dlg)}
  dlg.innerHTML='<h3>Your insights</h3><p>'+d.checks+' saved check(s)</p>'+d.tips.map(t=>'<p><b>'+t.title+'.</b> '+t.text+'</p>').join('')+
   '<div class="acts"><button id="ic" type="button">Close</button><button id="idl" type="button" class="ghost">Delete my data</button></div>';
  openDlg(dlg);$('#ic').onclick=()=>closeDlg(dlg);
  $('#idl').onclick=()=>{if(confirm('Delete your account and all saved checks?'))j('/me',{method:'DELETE'}).then(()=>location.reload())}}
safe('auth',()=>{auth().catch(()=>{})});

// ---------- footer ----------
safe('footer',()=>{
const ft=document.createElement('footer');ft.className='site';
ft.innerHTML='<div class="fgrid"><div><b>WattBack</b><small>The light of an idea</small><p>Turn your electricity bill into units, insight and savings.</p></div>'+
 '<div><h4>Explore</h4><a href="/">Check my bill</a><a href="/admin">GEDA view</a><a href="/about">About</a></div>'+
 '<div><h4>Help and legal</h4><a href="/contact">Contact</a><a href="/terms">Terms of Service</a><a href="/privacy">Privacy</a><a href="/check">Browser check</a></div></div>'+
 '<p class="fine">A hackathon project by team meteor for HackCult \u201926 (IIT Gandhinagar), built on the GEDA Mission LiFE problem statement. Not an official GEDA product. Figures are estimates; check your bill and your distribution company.</p>';
document.body.appendChild(ft)});

// ---------- helper chat (icon button) ----------
safe('chat',()=>{
const b=document.createElement('button');b.id='chatbtn';b.type='button';b.setAttribute('aria-label','Chat with the WattBack helper');b.setAttribute('aria-expanded','false');b.title='Ask WattBack';
b.innerHTML='<svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true" focusable="false"><path d="M5 3h14a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3h-7l-5 4v-4H5a3 3 0 0 1-3-3V6a3 3 0 0 1 3-3z" fill="currentColor"/><circle cx="8" cy="10" r="1.4" fill="var(--bubble-dot,#0d2b26)"/><circle cx="12" cy="10" r="1.4" fill="var(--bubble-dot,#0d2b26)"/><circle cx="16" cy="10" r="1.4" fill="var(--bubble-dot,#0d2b26)"/></svg>';
const c=document.createElement('div');c.id='chat';c.setAttribute('role','dialog');c.setAttribute('aria-label','WattBack helper');
c.innerHTML='<div class="chead"><b>WattBack helper</b><button id="cx" type="button" aria-label="Close chat">\u00d7</button></div><div id="cl" aria-live="polite"><p>Hi! Ask me about your bill, slabs, solar or privacy.</p></div>'+
 '<form><input id="cm" maxlength="500" placeholder="Type a question" aria-label="Your question" autocomplete="off"><button type="submit">Send</button></form>';
document.body.append(c,b);
b.onclick=()=>{const o=c.classList.toggle('open');b.setAttribute('aria-expanded',String(o));if(o)$('#cm').focus()};
$('#cx').onclick=()=>b.click();
$('form',c).onsubmit=async e=>{e.preventDefault();const i=$('#cm'),m=i.value.trim();if(!m)return;i.value='';
  const add=(t,me)=>{const p=document.createElement('p');p.textContent=t;if(me)p.className='me';$('#cl').appendChild(p);$('#cl').scrollTop=1e9;return p};
  add(m,true);const w=add('...');
  try{const r=await j('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m,context:window.WB_CONTEXT||''})});w.textContent=r.reply}
  catch(x){w.textContent=x&&x.status===429?'You have asked a lot just now. Please try again later.':'Sorry, I could not answer. Try the Contact page.'}}});
})();
