'use strict';

// ══════════════════════════════════════════════════════
//  CURSOR - standard system cursor (custom cursor removed)
// ══════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════
//  FLOATING PARTICLES
// ══════════════════════════════════════════════════════
(function(){
  const cols=['rgba(34,197,94,.5)','rgba(16,163,74,.35)','rgba(134,239,172,.45)','rgba(187,247,208,.55)'];
  for(let i=0;i<14;i++){
    const p=document.createElement('div'); p.className='particle';
    const s=Math.random()*6+2,l=Math.random()*100,delay=Math.random()*10,dur=Math.random()*9+7;
    p.style.cssText=`width:${s}px;height:${s}px;left:${l}%;bottom:-20px;background:${cols[i%4]};animation-duration:${dur}s;animation-delay:${delay}s`;
    document.body.appendChild(p);
  }
  // Dark theme extra orb
  const orb=document.createElement('div');orb.className='dark-orb';document.body.appendChild(orb);
})();

// ══════════════════════════════════════════════════════
//  INTRO VIDEO (10 seconds)
// ══════════════════════════════════════════════════════
(function(){
  const overlay=document.getElementById('introOverlay');
  if(!overlay)return;

  // Only show once per session
  if(sessionStorage.getItem('hm_intro_shown')){
    overlay.style.display='none'; return;
  }

  const pb=document.getElementById('introPb');
  const skip=document.getElementById('introSkip');
  const DURATION=5000;
  let start=null,raf=null;

  // Animated counters
  function animCounter(id,target,suffix){
    const el=document.getElementById(id); if(!el)return;
    let cur=0; const step=Math.max(1,Math.floor(target/60));
    const timer=setInterval(()=>{
      cur=Math.min(cur+step,target);
      el.textContent=cur+(suffix||'');
      if(cur>=target)clearInterval(timer);
    },35);
  }
  setTimeout(()=>{animCounter('ic1',1200,'+');animCounter('ic2',500,'+');animCounter('ic3',14,'');},1400);

  function step(ts){
    if(!start)start=ts;
    const prog=Math.min((ts-start)/DURATION,1);
    if(pb)pb.style.width=(prog*100)+'%';
    if(prog<1){raf=requestAnimationFrame(step);}
    else{dismiss();}
  }
  raf=requestAnimationFrame(step);

  function dismiss(){
    cancelAnimationFrame(raf);
    overlay.classList.add('hidden');
    sessionStorage.setItem('hm_intro_shown','1');
    setTimeout(()=>overlay.style.display='none',650);
  }

  if(skip)skip.addEventListener('click',dismiss);
  overlay.addEventListener('click',e=>{if(e.target===overlay)dismiss();});

  // Keyboard skip
  document.addEventListener('keydown',function onKey(e){
    if(e.key==='Escape'||e.key==='Enter'||e.key===' '){dismiss();document.removeEventListener('keydown',onKey);}
  },{once:false});

  // Cycling animal emoji in title
  const animals=['🐄','🐑','🐴','🐐','🐓','🐇'];
  const logoEl=overlay.querySelector('.intro-logo-icon');
  if(logoEl){
    let ai=0;
    setInterval(()=>{ai=(ai+1)%animals.length;logoEl.style.transform='scale(0.5)';
      setTimeout(()=>{logoEl.textContent=animals[ai];logoEl.style.transform='scale(1)';logoEl.style.transition='transform .3s cubic-bezier(.34,1.56,.64,1)';},150);
    },1500);
  }
})();

// ══════════════════════════════════════════════════════
//  NAVBAR SCROLL
// ══════════════════════════════════════════════════════
(function(){
  const nav=document.querySelector('.navbar');
  if(!nav)return;
  window.addEventListener('scroll',()=>nav.classList.toggle('scrolled',window.scrollY>40),{passive:true});
})();

// ══════════════════════════════════════════════════════
//  INTERSECTION REVEAL
// ══════════════════════════════════════════════════════
(function(){
  const io=new IntersectionObserver(en=>{
    en.forEach(e=>{if(e.isIntersecting){e.target.classList.add('vis');io.unobserve(e.target);}});
  },{threshold:.1});
  document.querySelectorAll('[data-anim]').forEach(el=>{io.observe(el);});
})();

// ══════════════════════════════════════════════════════
//  COUNTER ANIMATION
// ══════════════════════════════════════════════════════
document.querySelectorAll('[data-count]').forEach(el=>{
  const io=new IntersectionObserver(entries=>{
    if(!entries[0].isIntersecting)return; io.disconnect();
    const target=parseInt(el.dataset.count),suf=el.dataset.suf||'';
    let cur=0;const step=Math.max(1,Math.floor(target/55));
    const t=setInterval(()=>{cur+=step;if(cur>=target){cur=target;clearInterval(t);}el.textContent=cur.toLocaleString()+suf;},22);
  });
  io.observe(el);
});

// ══════════════════════════════════════════════════════
//  FLASH MESSAGES
// ══════════════════════════════════════════════════════
document.querySelectorAll('.fl-x').forEach(b=>b.addEventListener('click',()=>b.closest('.fl').remove()));
setTimeout(()=>{
  document.querySelectorAll('.fl').forEach(f=>{
    f.style.transition='opacity .5s,transform .5s'; f.style.opacity='0'; f.style.transform='translateX(16px)';
    setTimeout(()=>f.remove(),500);
  });
},5000);

// ══════════════════════════════════════════════════════
//  LIVE SEARCH
// ══════════════════════════════════════════════════════
(function(){
  const inp=document.getElementById('srchInp'),dd=document.getElementById('srchDd');
  if(!inp||!dd)return;
  let timer;
  inp.addEventListener('input',()=>{
    clearTimeout(timer);
    const q=inp.value.trim();
    if(q.length<2){dd.innerHTML='';dd.classList.remove('show');return;}
    timer=setTimeout(async()=>{
      try{
        const r=await fetch(`/api/search?q=${encodeURIComponent(q)}`);
        const data=await r.json();
        if(!data.length){dd.innerHTML='<div class="srch-item" style="color:var(--mt);justify-content:center">Natija topilmadi</div>';dd.classList.add('show');return;}
        dd.innerHTML=data.map(x=>`
          <a href="/listing/${x.id}" class="srch-item">
            <span style="font-size:26px">${x.emoji}</span>
            <div style="flex:1;min-width:0">
              <div style="font-weight:700;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${x.title}</div>
              <div style="font-size:11px;color:var(--mt)">📍 ${x.region}</div>
            </div>
            <div style="font-weight:800;color:var(--g);font-size:13px;white-space:nowrap">${Number(x.price).toLocaleString()} so'm</div>
          </a>`).join('');
        dd.classList.add('show');
      }catch(e){}
    },280);
  });
  document.addEventListener('click',e=>{if(!e.target.closest('.nv-srch')){dd.classList.remove('show');}});
})();

// ══════════════════════════════════════════════════════
//  WELCOME BANNER
// ══════════════════════════════════════════════════════
(function(){
  const banner=document.getElementById('wlBanner');
  if(!banner)return;
  const shown=sessionStorage.getItem('wl_shown');
  if(!shown){
    setTimeout(()=>{banner.style.display='flex';},1800);
    sessionStorage.setItem('wl_shown','1');
  }
  const close=document.getElementById('wlClose');
  if(close)close.addEventListener('click',()=>{
    banner.style.opacity='0';banner.style.transform='scale(.95)';
    banner.style.transition='opacity .3s,transform .3s';
    setTimeout(()=>banner.style.display='none',320);
  });
  banner.addEventListener('click',e=>{if(e.target===banner){close?.click();}});
})();

// ══════════════════════════════════════════════════════
//  FAVORITES AJAX
// ══════════════════════════════════════════════════════
document.querySelectorAll('[data-fav]').forEach(btn=>{
  btn.addEventListener('click',async e=>{
    e.preventDefault();
    const lid=btn.dataset.fav;
    try{
      const r=await fetch(`/favorites/toggle/${lid}`,{method:'POST',headers:{'X-Requested-With':'XMLHttpRequest'}});
      const d=await r.json();
      const cnt=document.getElementById('favCnt');
      if(cnt)cnt.textContent=d.count;
      btn.textContent=d.action==='added'?'❤️':'🤍';
      btn.style.transform='scale(1.3)';
      setTimeout(()=>btn.style.transform='scale(1)',200);
    }catch(e){}
  });
});

// Star picker in reviews
document.querySelectorAll('.star-pick').forEach(wrap=>{
  const stars=wrap.querySelectorAll('[data-star]');
  const inp=wrap.closest('form')?.querySelector('input[name="rating"]');
  stars.forEach(s=>{
    s.addEventListener('mouseenter',()=>{
      stars.forEach(x=>x.textContent=parseInt(x.dataset.star)<=parseInt(s.dataset.star)?'⭐':'☆');
    });
    s.addEventListener('click',()=>{
      if(inp)inp.value=s.dataset.star;
      wrap.dataset.val=s.dataset.star;
    });
  });
  wrap.addEventListener('mouseleave',()=>{
    const v=parseInt(wrap.dataset.val)||5;
    stars.forEach(x=>x.textContent=parseInt(x.dataset.star)<=v?'⭐':'☆');
  });
});
