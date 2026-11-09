
/* Shared cinematic visual effects — works without changing existing page logic */
(()=>{'use strict';
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
const canvas=document.createElement('canvas');canvas.className='tw-ambient';canvas.setAttribute('aria-hidden','true');document.body.prepend(canvas);
const ctx=canvas.getContext('2d');let w=0,h=0,dpr=1,dots=[],raf=0,playing=!reduce;
function resize(){w=innerWidth;h=innerHeight;dpr=Math.min(devicePixelRatio||1,1.6);canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);dots=Array.from({length:Math.min(110,Math.max(45,Math.round(w*h/15000)))},()=>({x:Math.random()*w,y:Math.random()*h,r:.5+Math.random()*1.4,a:.18+Math.random()*.5,v:.03+Math.random()*.12,p:Math.random()*6.28}));}
function draw(t){ctx.clearRect(0,0,w,h);for(const p of dots){ctx.fillStyle='rgba(204,183,255,'+(p.a*(.75+.25*Math.sin(t*.001+p.p)))+')';ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fill();if(playing){p.y-=p.v;if(p.y<0){p.y=h;p.x=Math.random()*w}}}if(playing)raf=requestAnimationFrame(draw)}
resize();draw(0);addEventListener('resize',()=>{cancelAnimationFrame(raf);resize();draw(0)},{passive:true});
const sections=document.querySelectorAll('.hero,.sec-head,.card,.stat,.cta,.price-card,.pricing-card,.template-card,.feature-card,.package-card');
if('IntersectionObserver'in window&&!reduce){const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('tw-in');observer.unobserve(e.target)}}),{threshold:.07});sections.forEach((el,i)=>{el.classList.add('tw-reveal');el.style.transitionDelay=Math.min(i%5*60,240)+'ms';observer.observe(el)})}
const visited=(()=>{try{return sessionStorage.getItem('tw-intro-seen')==='1'}catch(e){return false}})();
if(visited||reduce)return;
const intro=document.createElement('div');intro.className='tw-intro';intro.setAttribute('role','status');intro.setAttribute('aria-label','Loading Twist Automation');
intro.innerHTML='<canvas aria-hidden="true"></canvas><i class="tw-corner a"></i><i class="tw-corner b"></i><i class="tw-corner c"></i><i class="tw-corner d"></i><div class="tw-top"><span>TWIST® / AUTOMATION</span><span>SYSTEM ONLINE · 2026</span></div><div class="tw-core"><div class="tw-orbit"><span>✳</span></div><div class="tw-kicker">INITIALIZING DIGITAL EXPERIENCE</div><div class="tw-word" aria-label="TWIST"><span>T</span><span>W</span><span>I</span><span>S</span><span>T</span><span class="tw-dot">.</span></div><div class="tw-sub">BEYOND THE ORDINARY / AUTOMATION STUDIO</div><div class="tw-progress"><div class="tw-progress-line"><i></i></div><div class="tw-progress-label"><span class="tw-stage">ESTABLISHING SIGNAL</span><span class="tw-percent">000%</span></div></div></div><div class="tw-bottom"><span>DESIGNED TO MOVE</span><button type="button" class="tw-skip">SKIP INTRO ↗</button></div>';
document.body.appendChild(intro);const glyphs=[...intro.querySelectorAll('.tw-word span')],bar=intro.querySelector('.tw-progress-line i'),pct=intro.querySelector('.tw-percent'),stage=intro.querySelector('.tw-stage');
let done=false,start=performance.now(),anim=0,partsRaf=0;
const ic=intro.querySelector('canvas'),ix=ic.getContext('2d');let particles=[];
function resizeIntro(){const d=Math.min(devicePixelRatio||1,1.6);ic.width=Math.round(innerWidth*d);ic.height=Math.round(innerHeight*d);ix.setTransform(d,0,0,d,0,0);particles=Array.from({length:Math.min(160,Math.max(90,Math.round(innerWidth*innerHeight/11000)))},(_,i)=>({x:Math.random()*innerWidth,y:Math.random()*innerHeight,r:(i%12===0?2.2:1)+Math.random()*1.6,v:.1+Math.random()*.4,a:.25+Math.random()*.65,p:Math.random()*7}))}
function sparkle(t){if(done)return;ix.clearRect(0,0,innerWidth,innerHeight);for(const p of particles){let y=(p.y-t*.014*p.v+innerHeight*2)%innerHeight,x=p.x+Math.sin(t*.0005+p.p)*10;ix.fillStyle='rgba(212,185,255,'+(p.a*(.8+.2*Math.sin(t*.002+p.p)))+')';ix.beginPath();ix.arc(x,y,p.r,0,7);ix.fill()}partsRaf=requestAnimationFrame(sparkle)}
resizeIntro();partsRaf=requestAnimationFrame(sparkle);
function finish(){if(done)return;done=true;cancelAnimationFrame(anim);cancelAnimationFrame(partsRaf);glyphs.forEach(x=>x.classList.add('on'));bar.style.width='100%';pct.textContent='100%';stage.textContent='ACCESS GRANTED';intro.classList.add('tw-exit');try{sessionStorage.setItem('tw-intro-seen','1')}catch(e){}setTimeout(()=>intro.remove(),850)}
intro.querySelector('.tw-skip').addEventListener('click',finish);
function tick(now){if(done)return;const el=now-start,progress=Math.min(el/3600,1);glyphs.forEach((x,i)=>{if(el>420+i*210)x.classList.add('on')});const value=Math.floor(100*progress);bar.style.width=value+'%';pct.textContent=String(value).padStart(3,'0')+'%';stage.textContent=progress>.8?'ENTERING THE STUDIO':progress>.48?'SYNCHRONIZING SYSTEM':'ESTABLISHING SIGNAL';if(progress>=1)finish();else anim=requestAnimationFrame(tick)}
anim=requestAnimationFrame(tick);
})();
