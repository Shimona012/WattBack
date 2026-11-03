(function(){
const $=(s,r=document)=>r.querySelector(s), j=(u,o)=>fetch(u,o).then(r=>r.ok?r.json():Promise.reject(r));
const L=document.createElement('link');L.rel='stylesheet';L.href='/static/site.css';document.head.appendChild(L);
const nav=document.createElement('nav');nav.className='site';
nav.innerHTML='<a class="brand" href="/">WattBack</a><button id="mb" aria-expanded="false" aria-controls="mn">Menu</button><div id="mn"><a href="/">Check my bill</a><a href="/admin">GEDA view</a><a href="/about">About</a><a href="/contact">Contact</a><a href="/terms">Terms</a><a href="/privacy">Privacy</a><span id="auth"></span></div>';
document.body.prepend(nav);
$('#mb').onclick=()=>{const o=$('#mn').classList.toggle('open');$('#mb').setAttribute('aria-expanded',o)};
// ----- sign in -----
async function auth(){
  const [cfg,me]=await Promise.all([j('/auth/config'),j('/me')]);const a=$('#auth');
  if(me.user){a.innerHTML=`<button class="lnk" id="mi">My insights</button> <button class="lnk" id="so">Sign out (${me.user.name||me.user.email})</button>`;
    $('#so').onclick=()=>j('/auth/logout',{method:'POST'}).then(()=>location.reload());$('#mi').onclick=insights;return}
  if(cfg.client_id){a.innerHTML='<span id="g"></span>';const s=document.createElement('script');s.src='https://accounts.google.com/gsi/client';s.async=true;
    s.onload=()=>{google.accounts.id.initialize({client_id:cfg.client_id,callback:r=>j('/auth/google',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({credential:r.credential})}).then(()=>location.reload()).catch(()=>alert('Sign-in failed'))});
      google.accounts.id.renderButton($('#g'),{theme:'outline',size:'medium'})};document.head.appendChild(s)}
  else if(cfg.dev){a.innerHTML='<button class="lnk" id="dv">Sign in (demo)</button>';$('#dv').onclick=()=>j('/auth/dev',{method:'POST'}).then(()=>location.reload())}
  else a.innerHTML='<span style="color:var(--mut)">Sign-in not set up</span>'}
async function insights(){
  const d=await j('/me/insights');let dlg=$('#ins');if(!dlg){dlg=document.createElement('dialog');dlg.id='ins';document.body.appendChild(dlg)}
  dlg.innerHTML=`<h3>Your insights</h3><p>${d.checks} saved check(s)</p>${d.tips.map(t=>`<p><b>${t.title}.</b> ${t.text}</p>`).join('')}
   <button id="ic">Close</button><button id="idl">Delete my data</button>`;
  dlg.showModal();$('#ic').onclick=()=>dlg.close();
  $('#idl').onclick=()=>{if(confirm('Delete your account and all saved checks?'))j('/me',{method:'DELETE'}).then(()=>location.reload())}}
auth().catch(()=>{});
// ----- helper chat -----
const b=document.createElement('button');b.id='chatbtn';b.textContent='Ask WattBack';b.setAttribute('aria-expanded','false');
const c=document.createElement('div');c.id='chat';c.setAttribute('role','dialog');c.setAttribute('aria-label','WattBack helper');
c.innerHTML='<div id="cl"><p>Hi! Ask me about your bill, slabs, solar or privacy.</p></div><form><input id="cm" maxlength="500" placeholder="Type a question" aria-label="Your question"><button>Send</button></form>';
document.body.append(c,b);
b.onclick=()=>{const o=c.classList.toggle('open');b.setAttribute('aria-expanded',o);if(o)$('#cm').focus()};
$('form',c).onsubmit=async e=>{e.preventDefault();const i=$('#cm'),m=i.value.trim();if(!m)return;i.value='';
  const add=(t,me)=>{const p=document.createElement('p');p.textContent=t;if(me)p.className='me';$('#cl').appendChild(p);$('#cl').scrollTop=1e9;return p};
  add(m,true);const w=add('...');
  try{const r=await j('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m,context:window.WB_CONTEXT||''})});w.textContent=r.reply}
  catch(x){w.textContent=x.status===429?'You have asked a lot just now. Please try again later.':'Sorry, I could not answer. Try the Contact page.'}};
})();
