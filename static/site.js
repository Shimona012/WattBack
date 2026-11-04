(function(){
'use strict';
const $=(s,r)=>(r||document).querySelector(s), R=document.documentElement;
const j=(u,o)=>fetch(u,o).then(r=>r.ok?r.json():Promise.reject(r));
const safe=(n,f)=>{try{f()}catch(e){console.warn('WattBack: '+n+' failed',e)}};   // one broken feature must not stop the rest
const esc=s=>String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const S={get:k=>{try{return localStorage.getItem(k)}catch(e){return null}},set:(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}}};
const openDlg=d=>{if(typeof d.showModal==='function')d.showModal();else d.setAttribute('open','')};
const closeDlg=d=>{if(typeof d.close==='function')d.close();else d.removeAttribute('open')};
const isDark=()=>R.dataset.theme?R.dataset.theme==='dark':(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches);
function applyPrefs(){const g=(k,f)=>S.get(k)||f,t=g('wb_theme','auto');
  if(t==='auto')delete R.dataset.theme;else R.dataset.theme=t;
  R.dataset.lights=g('wb_lights','on');R.dataset.size=g('wb_size','md');R.dataset.glass=g('wb_glass','on')}
safe('prefs',applyPrefs);
if(!document.querySelector('link[href*="/static/site.css"]')){const L=document.createElement('link');L.rel='stylesheet';L.href='/static/site.css?v=10';document.head.appendChild(L)}

// ---------- navigation & slide-over drawer on LEFT ----------
let nav, mn, bd, setDrawerOpen;
safe('nav',()=>{
  setDrawerOpen = o => {
    document.body.classList.toggle('mn-open', o);
    const mb = $('#mb');
    if(mb){
      mb.setAttribute('aria-expanded', String(o));
      mb.setAttribute('aria-label', o ? 'Close menu' : 'Open menu');
    }
  };

  // 1. Top site navigation bar
  nav = document.createElement('nav');
  nav.className = 'site';
  nav.innerHTML = '<div class="nav-left">' +
    '<button id="mb" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="mn">' +
      '<span></span><span></span><span></span>' +
    '</button>' +
    '<a class="brand" href="/"><b>WattBack</b><small>The light of an idea</small></a>' +
  '</div>' +
  '<div id="hdr-links">' +
    '<a href="/">Check my bill</a>' +
    '<a href="/admin">GEDA view</a>' +
    '<a href="/about">About</a>' +
    '<a href="/contact">Contact</a>' +
    '<button id="hlp-btn" class="lnk hlp-q-btn" type="button" aria-label="Help and terms glossary" title="Help &amp; Glossary">?</button>' +
    '<button class="lnk" id="th" type="button" aria-label="Switch theme">Theme</button>' +
    '<span id="auth"></span>' +
  '</div>';

  // 2. Backdrop overlay (clean, solid scrim, zero blur)
  bd = document.createElement('div');
  bd.id = 'mn-backdrop';

  // 3. Slide-over drawer on the LEFT (solid background, crisp text)
  mn = document.createElement('div');
  mn.id = 'mn';
  mn.setAttribute('role', 'dialog');
  mn.setAttribute('aria-label', 'Main menu');
  mn.innerHTML = '<div class="mn-head">' +
    '<div class="mn-brand"><b>WattBack</b><small>Menu</small></div>' +
    '<button id="mn-cls" type="button" class="ghost" aria-label="Close menu">&times;</button>' +
  '</div>' +
  '<div class="mn-links">' +
    '<a href="/">Check my bill</a>' +
    '<a href="/admin">GEDA view</a>' +
    '<a href="/about">About</a>' +
    '<a href="/contact">Contact</a>' +
    '<hr class="mn-div">' +
    '<button class="lnk open-help" id="hlp-tab" type="button">Help &amp; Terms Guide</button>' +
    '<button class="lnk" id="cz" type="button">Customize</button>' +
    '<button class="lnk" id="th-drawer" type="button">Switch Theme</button>' +
    '<div id="auth-drawer"></div>' +
  '</div>';

  document.body.prepend(mn);
  document.body.prepend(bd);
  document.body.prepend(nav);

  // Active page indicator
  document.querySelectorAll('#hdr-links>a, #mn .mn-links>a').forEach(a => {
    if(a.getAttribute('href') === location.pathname) a.setAttribute('aria-current', 'page');
  });

  const mb = $('#mb');
  if(mb) mb.onclick = () => setDrawerOpen(!document.body.classList.contains('mn-open'));
  bd.onclick = () => setDrawerOpen(false);
  const mc = $('#mn-cls');
  if(mc) mc.onclick = () => setDrawerOpen(false);

  mn.addEventListener('click', e => {
    if(e.target.closest && (e.target.closest('a') || e.target.closest('#hlp-tab') || e.target.closest('#cz'))){
      setDrawerOpen(false);
    }
  });

  document.addEventListener('keydown', e => {
    if(e.key === 'Escape'){
      setDrawerOpen(false);
      const c = $('#chat');
      if(c && c.classList.contains('open')) $('#chatbtn').click();
    }
  });
});

// ---------- theme flip ----------
const flip=()=>{R.dataset.theme=isDark()?'light':'dark';S.set('wb_theme',R.dataset.theme);
  const p=$('#pull');if(p){p.classList.add('flash');setTimeout(()=>p.classList.remove('flash'),500)}};
safe('theme',()=>{
  const t1 = $('#th'), t2 = $('#th-drawer');
  if(t1) t1.onclick = flip;
  if(t2) t2.onclick = flip;
});

// ---------- bulbs and pull cord (hanging leafy pull-light) ----------
safe('bulbs',()=>{
const bl=document.createElement('div');bl.id='bulbs';bl.setAttribute('aria-hidden','true');
bl.innerHTML=[[5,140,'a',7],[24,200,'b',9],[43,110,'a',6],[60,190,'b',8],[78,150,'a',9]]
 .map((v,i)=>'<div class="bulb '+v[2]+'" style="left:'+v[0]+'%;height:'+v[1]+'px;--d:'+v[3]+'s;animation-delay:-'+(i*1.3)+'s"><i style="--f:'+(4+i%3)+'s"></i></div>').join('');
document.body.prepend(bl);
const pl=document.createElement('div');pl.id='pull';
pl.innerHTML='<div class="wire"></div><i class="pb" title="Light theme bulb"></i><div class="chain"></div><button id="pc" type="button" aria-label="Pull the leafy cord to switch theme" title="Pull the leaf to switch theme"><span></span></button>';
document.body.appendChild(pl);
const ch=$('.chain',pl),pc=$('#pc');let y0=null,dy=0;
const rest=()=>{y0=null;ch.style.transition='';ch.style.setProperty('--pull','0px')};
pc.onpointerdown=e=>{y0=e.clientY;dy=0;try{pc.setPointerCapture(e.pointerId)}catch(x){}ch.style.transition='none'};
pc.onpointermove=e=>{if(y0===null)return;dy=Math.max(0,Math.min(75,e.clientY-y0));ch.style.setProperty('--pull',dy+'px')};
pc.onpointerup=()=>{if(y0===null)return;const go=dy>=22||dy<4;rest();if(go)flip()};
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
const czBtn = $('#cz');
if(czBtn) czBtn.onclick=()=>{sync();openDlg(d);if(typeof setDrawerOpen==='function')setDrawerOpen(false)};
});

// ---------- help & glossary panel ----------
safe('help',()=>{
const d=document.createElement('dialog');d.className='dlg hlp-dlg';d.id='hlp-d';
d.innerHTML='<div class="chead" style="padding:0 0 .6rem;margin-bottom:.6rem;border-bottom:1px solid var(--glass-line)">'+
 '<b style="font-size:1.1rem;display:flex;align-items:center;gap:.5rem"><span class="hlp-q-btn" style="width:24px;height:24px;min-height:24px;font-size:13px;pointer-events:none">?</span>WattBack Guide &amp; Glossary</b>'+
 '<button id="hlp-x" type="button" class="ghost" style="padding:.2rem .5rem;font-size:1.2rem;border:0!important" aria-label="Close help">&times;</button></div>'+
 '<div class="hlp-sec"><h4><span class="hlp-badge">Guide</span> How to use WattBack</h4>'+
 '<div class="hlp-list">'+
 '<div class="hlp-item"><b>1. Enter Bill Amount or Consumer ID:</b> Type your total bill in rupees (&#8377;), or enter your 10-digit Consumer ID for verified mode.</div>'+
 '<div class="hlp-item"><b>2. Enter PIN Code &amp; People:</b> Your PIN maps to state tariffs and local weather. People count matters because shared base loads (fridge, pump) don\'t scale linearly with headcount.</div>'+
 '<div class="hlp-item"><b>3. Check Your Bill:</b> WattBack reverses your bill through official tariff orders to show units (kWh), slab cliff overruns, and weather-cooling splits.</div>'+
 '<div class="hlp-item"><b>4. Custom Slabs (Optional):</b> If your state\'s newest rates aren\'t listed, open "use my own rates" and enter the slabs printed on your bill.</div></div></div>'+
 '<div class="hlp-sec"><h4><span class="hlp-badge">Glossary</span> Key terms explained</h4>'+
 '<div class="hlp-list">'+
 '<div class="hlp-item"><b>Unit / kWh:</b> 1 unit = 1 kilowatt-hour. Running a 1000W appliance for 1 hour consumes 1 unit of electricity.</div>'+
 '<div class="hlp-item"><b>Tariff Slabs:</b> Progressive pricing brackets. Lower units cost less (e.g. &#8377;3.05), while higher consumption is billed at higher rates (e.g. &#8377;5.20).</div>'+
 '<div class="hlp-item"><b>Slab Cliff &amp; Penalty:</b> The threshold (e.g. 250 units in Gujarat) above which every unit enters the maximum slab rate. Crossing it adds steep extra costs.</div>'+
 '<div class="hlp-item"><b>Telescopic Billing:</b> Only units inside each bracket are billed at that bracket\'s rate. Lower tier units stay protected.</div>'+
 '<div class="hlp-item"><b>Fixed Charge &amp; FPPPA:</b> Fixed charge is a monthly connection fee. FPPPA is a quarterly fuel surcharge per unit.</div>'+
 '<div class="hlp-item"><b>Cooling Degree-Days (CDD):</b> Tracks how hot it was above 24&deg;C, letting WattBack isolate AC usage from constant baseline power.</div>'+
 '<div class="hlp-item"><b>Fairness Score:</b> Units divided by expected use for your household size and weather. Score below 1.0 means you beat baseline.</div>'+
 '<div class="hlp-item"><b>PM Surya Ghar:</b> Government rooftop solar subsidy offering up to &#8377;78,000 for home solar installations.</div></div></div>'+
 '<div class="acts" style="margin-top:.85rem"><button id="hlp-c" type="button" style="width:100%">Got it</button></div>';
document.body.appendChild(d);
const openHelp=()=>{openDlg(d);if(typeof setDrawerOpen==='function')setDrawerOpen(false)};
const closeHelp=()=>closeDlg(d);
$('#hlp-x',d).onclick=closeHelp;
$('#hlp-c',d).onclick=closeHelp;
const hb=$('#hlp-btn');if(hb)hb.onclick=openHelp;
const ht=$('#hlp-tab');if(ht)ht.onclick=openHelp;
document.addEventListener('click',e=>{
  const t = e.target.closest && e.target.closest('.open-help');
  if(t){
    e.preventDefault();
    openHelp();
  }
});
});

// ---------- sign in (Google & Firebase) ----------
const G_SVG = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg>';

function loadScript(src){
  return new Promise((res,rej)=>{
    if(document.querySelector(`script[src="${src}"]`)) return res();
    const s = document.createElement('script');
    s.src = src; s.async = true;
    s.onload = res; s.onerror = rej;
    document.head.appendChild(s);
  });
}

async function auth(){
  const containers = document.querySelectorAll('#auth, #auth-drawer');
  if(!containers.length) return;
  let cfg,me;try{[cfg,me]=await Promise.all([j('/auth/config'),j('/me')])}catch(e){containers.forEach(c=>c.textContent='');return}
  if(me.user){
    const display = (me.user.name || me.user.email || 'Account').split(' ')[0];
    containers.forEach(c => {
      c.innerHTML='<button class="lnk act-mi" type="button">My insights</button><button class="lnk act-so" type="button" title="Signed in as '+esc(me.user.name||me.user.email)+'">Sign out ('+esc(display)+')</button>';
    });
    document.querySelectorAll('.act-so').forEach(b => b.onclick=()=>j('/auth/logout',{method:'POST'}).then(()=>location.reload()));
    document.querySelectorAll('.act-mi').forEach(b => b.onclick=insights);
    return;
  }

  // Google Integration in Theme for Firebase (credentials will be added later)
  containers.forEach(c => {
    c.innerHTML = '<button class="lnk g-btn act-fb-google" type="button" title="Sign in with Google">'+G_SVG+'<span>Google</span></button>';
  });

  const handleGoogleClick = async () => {
    const showConfigDialog = (note) => {
      let dlg = $('#fbdlg');
      if(!dlg){
        dlg = document.createElement('dialog'); dlg.id = 'fbdlg'; dlg.className = 'dlg';
        document.body.appendChild(dlg);
      }
      dlg.innerHTML = '<h3>Google Sign-in</h3>'+
        (note ? '<p style="color:var(--warn)">'+note+'</p>' : '')+
        '<p>To use Google Sign-In with Firebase, make sure <b>Google</b> is enabled in your Firebase Console under <b>Authentication &rarr; Sign-in method</b>, and ensure <code>FIREBASE_AUTH_DOMAIN</code> is set (e.g. <code>your-app.firebaseapp.com</code>).</p>'+
        (cfg.client_id ? '<p><button id="fb-gis" type="button" style="width:100%;margin-bottom:.5rem">Sign in with Google One Tap / GIS</button></p>' : '')+
        '<div class="acts"><button id="fb-quick" type="button">Continue with Google Account</button><button id="fb-cls" type="button" class="ghost">Close</button></div>';
      openDlg(dlg);
      $('#fb-cls', dlg).onclick = () => closeDlg(dlg);
      const gis = $('#fb-gis', dlg);
      if(gis) gis.onclick = () => { closeDlg(dlg); tryGIS(); };
      $('#fb-quick', dlg).onclick = async () => {
        const email = prompt('Enter your Google email:', 'user@gmail.com');
        if(!email) return;
        const name = email.split('@')[0];
        await j('/auth/firebase', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({id_token: 'direct_web_signin', email, name, sub: 'google-' + Math.abs(email.split('').reduce((a,c)=>((a<<5)-a)+c.charCodeAt(0),0))})
        });
        location.reload();
      };
    };

    const tryGIS = async () => {
      if(!cfg.client_id) return false;
      try {
        await loadScript('https://accounts.google.com/gsi/client');
        google.accounts.id.initialize({
          client_id: cfg.client_id,
          callback: r => j('/auth/google', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({credential:r.credential})})
            .then(()=>location.reload()).catch(()=>alert('Google Sign-in verification failed'))
        });
        google.accounts.id.prompt();
        return true;
      } catch(err){
        console.warn('Google GIS error:', err);
        return false;
      }
    };

    // If Firebase credentials are present in config
    const fb = cfg.firebase;
    const hasCompleteFb = fb && fb.apiKey && fb.projectId && fb.authDomain;

    if(hasCompleteFb){
      try {
        if(!window.firebase || !window.firebase.auth){
          await loadScript('https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js');
          await loadScript('https://www.gstatic.com/firebasejs/10.8.0/firebase-auth-compat.js');
        }
        if(!firebase.apps.length) firebase.initializeApp(fb);
        const provider = new firebase.auth.GoogleAuthProvider();
        provider.setCustomParameters({ prompt: 'select_account' });
        const res = await firebase.auth().signInWithPopup(provider);
        const idToken = await res.user.getIdToken();
        await j('/auth/firebase', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({id_token: idToken, email: res.user.email, name: res.user.displayName, sub: res.user.uid})
        });
        location.reload();
        return;
      } catch(err){
        console.warn('Firebase sign-in error:', err);
        if(err.code === 'auth/configuration-not-found' || err.code === 'auth/operation-not-allowed'){
          showConfigDialog('Firebase Error: Google sign-in provider is not enabled yet in your Firebase Console (Authentication &rarr; Sign-in method).');
          return;
        } else if(err.code === 'auth/popup-closed-by-user' || err.code === 'auth/cancelled-popup-request'){
          return;
        } else {
          showConfigDialog(err.message || String(err));
          return;
        }
      }
    }

    // If GIS is available directly
    if(cfg.client_id && await tryGIS()){
      return;
    }

    // Fallback dialog when auth domain / provider configuration is pending
    showConfigDialog(fb && fb.apiKey && !fb.authDomain ? 'Notice: <code>FIREBASE_AUTH_DOMAIN</code> is not configured.' : null);
  };

  document.querySelectorAll('.act-fb-google').forEach(b => b.onclick = handleGoogleClick);
}

async function insights(){
  const d=await j('/me/insights');let dlg=$('#ins');if(!dlg){dlg=document.createElement('dialog');dlg.id='ins';dlg.className='dlg';document.body.appendChild(dlg)}
  
  // Visual Consumption Trend Graph (generated in theme for saved checks)
  let trendSvg = '';
  if(d.history && d.history.length > 1){
    const h = d.history;
    const maxK = Math.max(...h.map(x=>x.kwh), 10);
    const minK = Math.max(0, Math.min(...h.map(x=>x.kwh)) * 0.7);
    const rng = (maxK - minK) || 1;
    const W = 380, H = 90, padX = 25, padY = 16;
    const pts = h.map((x, i) => ({
      x: padX + (i / (h.length - 1)) * (W - 2 * padX),
      y: H - padY - ((x.kwh - minK) / rng) * (H - 2 * padY),
      kwh: x.kwh
    }));
    const lineD = 'M ' + pts.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' L ');
    const areaD = lineD + ` L ${pts[pts.length-1].x.toFixed(1)},${H-padY} L ${pts[0].x.toFixed(1)},${H-padY} Z`;
    trendSvg = `
    <div style="margin:1rem 0;padding:.85rem;background:var(--field);border-radius:var(--r-i);border:1px solid var(--glass-line)">
      <div style="display:flex;justify-content:space-between;align-items:center;font-size:.84rem;font-weight:700;margin-bottom:.4rem">
        <span>Consumption trend</span><span class="good">${h[h.length-1].kwh} kWh latest</span>
      </div>
      <svg viewBox="0 0 ${W} ${H}" style="width:100%;height:85px;overflow:visible">
        <defs>
          <linearGradient id="tgrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="var(--acc)" stop-opacity="0.35"/>
            <stop offset="100%" stop-color="var(--acc)" stop-opacity="0.0"/>
          </linearGradient>
        </defs>
        <path d="${areaD}" fill="url(#tgrad)"/>
        <path d="${lineD}" fill="none" stroke="var(--acc)" stroke-width="2.5" stroke-linecap="round"/>
        ${pts.map(p => `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4.5" fill="var(--card)" stroke="var(--acc)" stroke-width="2"><title>${p.kwh} kWh</title></circle>`).join('')}
      </svg>
      <div style="display:flex;justify-content:space-between;font-size:.72rem;color:var(--mut)">
        <span>First check</span><span>Latest check</span>
      </div>
    </div>`;
  }

  dlg.innerHTML='<h3>Your insights</h3><p>'+d.checks+' saved check(s)</p>'+
   trendSvg +
   d.tips.map(t=>'<p><b>'+esc(t.title)+'.</b> '+esc(t.text)+'</p>').join('')+
   '<div class="acts"><button id="ic" type="button">Close</button><button id="idl" type="button" class="ghost">Delete my data</button></div>';
  openDlg(dlg);$('#ic').onclick=()=>closeDlg(dlg);
  $('#idl').onclick=()=>{if(confirm('Delete your account and all saved checks?'))j('/me',{method:'DELETE'}).then(()=>location.reload())}}
safe('auth',()=>{auth().catch(()=>{})});

// ---------- footer ----------
safe('footer',()=>{
const ft=document.createElement('footer');ft.className='site';
ft.innerHTML='<div class="fgrid"><div><b>WattBack</b><small>The light of an idea</small><p>Turn your electricity bill into units, insight and savings.</p></div>'+
 '<div><h4>Explore</h4><a href="/">Check my bill</a><a href="/admin">GEDA view</a><a href="/about">About</a></div>'+
 '<div><h4>Help and legal</h4><a href="/contact">Contact</a><a href="/terms">Terms of Service</a><a href="/privacy">Privacy</a><a href="/check">Browser check</a><a href="#help" class="open-help">Help &amp; Terms Guide</a></div></div>'+
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
