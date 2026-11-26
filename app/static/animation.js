"use strict";
/* Studio-only draft editor. No Forge serializer, runtime, 3D mesh or inference. */
const CHANNEL_LABELS = {
  "root.x":"Corpo · horizontal", "root.y":"Corpo · vertical", "head.tilt":"Cabeça · inclinação",
  "arm.left":"Braço esquerdo", "arm.right":"Braço direito", "leg.left":"Perna esquerda",
  "leg.right":"Perna direita", "expression.smile":"Expressão · sorriso",
  "expression.blink":"Expressão · piscar", "expression.brow":"Expressão · sobrancelhas",
  "effect.glow":"Efeito · brilho"
};
const CHANNELS = Object.keys(CHANNEL_LABELS);
const clone = value => JSON.parse(JSON.stringify(value));
const safe = value => String(value ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;");
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
function sample(keys, time) {
  if (!keys || !keys.length || time < keys[0].time_ms) return 0;
  const left = keys.findIndex(k => k.time_ms > time);
  if (left < 0) { const k = keys[keys.length-1]; return k.value * k.intensity; }
  const a = keys[left-1], b = keys[left];
  let u = (time-a.time_ms)/(b.time_ms-a.time_ms);
  if (a.interpolation === "step") u = 0;
  if (a.interpolation === "ease") u = u*u*(3-2*u);
  return (a.value*a.intensity)*(1-u) + (b.value*b.intensity)*u;
}
function frame(clip, time) {
  const t = clip.loop && time > clip.duration_ms ? time % clip.duration_ms : clamp(time,0,clip.duration_ms);
  return Object.fromEntries(CHANNELS.map(ch => [ch, sample(clip.tracks[ch], t)]));
}
function compose(target, source, offset) {
  if (!Number.isInteger(offset) || offset < 0) throw Error("Cursor inválido");
  const next = clone(target);
  for (const [channel, keys] of Object.entries(source.tracks)) {
    const merged = new Map((next.tracks[channel] || []).map(k => [k.time_ms,k]));
    for (const key of keys) {
      if (key.time_ms + offset > target.duration_ms) throw Error("A composição excede a duração. Amplie a animação antes de inserir.");
      merged.set(key.time_ms + offset, {...key, time_ms:key.time_ms+offset});
    }
    next.tracks[channel] = Array.from(merged.values()).sort((a,b)=>a.time_ms-b.time_ms);
  }
  return next;
}
function poseAt(clip, time) {
  const values = frame(clip,time);
  return {...clone(clip), name:clip.name+" · pose", duration_ms:100, loop:false,
    tracks:Object.fromEntries(Object.entries(values).filter(([,v])=>Math.abs(v)>0.00001)
      .map(([ch,v])=>[ch,[{time_ms:0,value:clamp(v,-1,1),intensity:1,interpolation:"linear"}]]))};
}

if (typeof document !== "undefined" && document.getElementById("timeline")) {
  const $ = id => document.getElementById(id);
  const state = {projects:[],library:[],id:null,clip:null,revision:null,dirty:false,
    undo:[],redo:[],time:0,selected:null,playing:false,lastFrame:0,raf:0};
  const message = text => {const el=$("anim-message"); el.textContent=text; el.hidden=!text;};
  const status = (text,kind="") => {$("save-status").textContent=text; $("save-status").className="status "+kind;};
  async function api(method,url,body) {
    const response=await fetch(url,{method,headers:{"Content-Type":"application/json"},
      ...(body===undefined?{}:{body:JSON.stringify(body)})});
    const data=await response.json();
    if(!response.ok) throw Error(data.error || `HTTP ${response.status}`);
    return data;
  }
  function fail(error) { message(error.message || String(error)); status("Não salvo","dirty"); }
  const askLoss = () => !state.dirty || confirm("Descartar as alterações não salvas deste projeto?");
  function push(next) {
    state.undo.push(clone(state.clip)); if(state.undo.length>60) state.undo.shift();
    state.redo=[]; state.clip=next; state.dirty=true; message(""); status("Alterações não salvas","dirty"); renderEditor();
  }
  function undo() { if(!state.undo.length)return;state.redo.push(clone(state.clip));state.clip=state.undo.pop();state.dirty=true;renderEditor();status("Desfazer não salvo","dirty"); }
  function redo() { if(!state.redo.length)return;state.undo.push(clone(state.clip));state.clip=state.redo.pop();state.dirty=true;renderEditor();status("Refazer não salvo","dirty"); }
  function resetAnimation() {state.playing=false;cancelAnimationFrame(state.raf);$("play").textContent="▶ Reproduzir";}
  async function refreshLists() {
    const data=await api("GET","/api/animation");state.projects=data.projects;state.library=data.library;
    $("project-list").innerHTML='<option value="">Selecione um projeto</option>'+data.projects.map(p=>
      `<option value="${safe(p.id)}">${safe(p.name)}</option>`).join("");
    $("project-list").value=state.id||"";
    $("library-list").innerHTML='<option value="">Selecione uma pose, gesto ou animação</option>'+data.library.map(p=>
      `<option value="${safe(p.id)}">${safe(p.name)} · ${safe(p.kind)} · ${p.status==='approved'?'aprovado localmente':'rascunho'}</option>`).join("");
  }
  async function open(id) {
    resetAnimation();const data=await api("GET",`/api/animation/projects/${id}`);
    state.id=id;state.clip=data.clip;state.revision=data.revision;state.dirty=false;
    state.undo=[];state.redo=[];state.time=0;state.selected=null;
    $("project-list").value=id;status("Salvo neste computador","saved");message("");renderEditor();
  }
  function renderEditor() {
    const clip=state.clip; if(!clip)return;
    $("clip-name").value=clip.name;$("clip-duration").value=clip.duration_ms;
    $("clip-loop").checked=clip.loop;$("clip-source").value=clip.source.kind;
    $("clip-reference").value=clip.source.reference;$("clip-license").value=clip.source.license;
    $("scrub").max=clip.duration_ms;$("scrub").value=clamp(state.time,0,clip.duration_ms);
    $("key-channel").innerHTML=CHANNELS.map(ch=>`<option value="${ch}">${safe(CHANNEL_LABELS[ch])}</option>`).join("");
    if(state.selected) $("key-channel").value=state.selected.channel;
    const key=state.selected && clip.tracks[state.selected.channel]?.find(k=>k.time_ms===state.selected.time);
    $("key-time").max=clip.duration_ms;$("key-time").value=key?.time_ms??Math.round(state.time);
    $("key-value").value=key?.value??0;$("key-intensity").value=key?.intensity??1;
    $("key-interpolation").value=key?.interpolation??"linear";
    $("key-remove").disabled=!key;
    $("key-count").textContent=Object.values(clip.tracks).reduce((n,keys)=>n+keys.length,0)+" keyframes";
    $("timeline").innerHTML=CHANNELS.map(channel=>`<div class="track-row"><div class="track-name" title="${safe(CHANNEL_LABELS[channel])}">${safe(CHANNEL_LABELS[channel])}</div><div class="track-lane" data-channel="${channel}" aria-label="Trilha ${safe(CHANNEL_LABELS[channel])}"><div class="playhead" style="left:${100*state.time/clip.duration_ms}%"></div>${(clip.tracks[channel]||[]).map(key=>`<button type="button" class="key-dot ${state.selected?.channel===channel&&state.selected.time===key.time_ms?'selected':''}" data-time="${key.time_ms}" style="left:${100*key.time_ms/clip.duration_ms}%" title="${safe(CHANNEL_LABELS[channel])} · ${key.time_ms} ms · ${key.interpolation}" aria-label="Keyframe ${safe(CHANNEL_LABELS[channel])} em ${key.time_ms} ms (arraste ou use setas)"></button>`).join("")}</div></div>`).join("");
    renderFrame();
  }
  function renderFrame() {
    if(!state.clip)return;
    const clip=state.clip, t=clamp(state.time,0,clip.duration_ms), f=frame(clip,t);
    $("time-readout").textContent=(t/1000).toFixed(2)+" s";
    $("scrub-label").textContent=Math.round(t)+" ms";
    $("scrub").value=Math.round(t);
    document.querySelectorAll(".track-lane .playhead").forEach(el=>el.style.left=(100*t/clip.duration_ms)+"%");
    $("character").setAttribute("transform",`translate(${200+f["root.x"]*75} ${150-f["root.y"]*65})`);
    $("head").setAttribute("transform",`rotate(${f["head.tilt"]*22} 0 -83)`);
    $("arm-left").setAttribute("transform",`rotate(${f["arm.left"]*75} -29 -65)`);
    $("arm-right").setAttribute("transform",`rotate(${-f["arm.right"]*75} 29 -65)`);
    $("leg-left").setAttribute("transform",`rotate(${f["leg.left"]*40} 0 15)`);
    $("leg-right").setAttribute("transform",`rotate(${-f["leg.right"]*40} 0 15)`);
    const blink=clamp(f["expression.blink"],0,1);
    $("eyes").setAttribute("d",`M-19 -116 L-12 ${-116+blink*5} M12 ${-116+blink*5} L19 -116`);
    $("mouth").setAttribute("d",`M-12 -96 Q0 ${-96+f["expression.smile"]*15} 12 -96`);
    $("brows").setAttribute("transform",`translate(0 ${-f["expression.brow"]*8})`);
    $("effect").setAttribute("opacity",String(clamp(f["effect.glow"],0,1)));
  }
  function tick(now) {
    if(!state.playing)return;
    const delta=Math.min(100,now-state.lastFrame);state.lastFrame=now;
    state.time+=Math.max(0,delta);
    if(state.time>=state.clip.duration_ms){if(state.clip.loop)state.time%=state.clip.duration_ms;else {state.time=state.clip.duration_ms;resetAnimation();}}
    renderFrame();if(state.playing)state.raf=requestAnimationFrame(tick);
  }
  function place(channel,oldTime,newTime) {
    const clip=clone(state.clip), keys=clip.tracks[channel]||[];
    const current=keys.find(k=>k.time_ms===oldTime);
    if(!current||newTime<0||newTime>clip.duration_ms)return;
    clip.tracks[channel]=keys.filter(k=>k.time_ms!==oldTime&&k.time_ms!==newTime)
      .concat([{...current,time_ms:newTime}]).sort((a,b)=>a.time_ms-b.time_ms);
    state.selected={channel,time:newTime};state.time=newTime;push(clip);
  }
  $("timeline").addEventListener("click",event=>{
    const marker=event.target.closest(".key-dot"),lane=event.target.closest(".track-lane");
    if(!lane||!state.clip)return;
    if(marker){state.selected={channel:lane.dataset.channel,time:Number(marker.dataset.time)};state.time=state.selected.time;renderEditor();return;}
    state.time=clamp(Math.round((event.clientX-lane.getBoundingClientRect().left)/lane.clientWidth*state.clip.duration_ms),0,state.clip.duration_ms);renderEditor();
  });
  let dragging=null;
  $("timeline").addEventListener("pointerdown",event=>{
    const dot=event.target.closest(".key-dot");if(dot)dragging={channel:dot.closest(".track-lane").dataset.channel,time:Number(dot.dataset.time)};
  });
  window.addEventListener("pointerup",event=>{
    if(!dragging)return;
    const lane=document.elementFromPoint(event.clientX,event.clientY)?.closest(".track-lane");
    if(lane?.dataset.channel===dragging.channel){const rect=lane.getBoundingClientRect();
      const next=clamp(Math.round((event.clientX-rect.left)/rect.width*state.clip.duration_ms),0,state.clip.duration_ms);
      if(next!==dragging.time){place(dragging.channel,dragging.time,next);dragging=null;return;}}
    dragging=null;
  });
  $("timeline").addEventListener("keydown",event=>{
    if(!["ArrowLeft","ArrowRight"].includes(event.key)||!event.target.classList.contains("key-dot"))return;
    event.preventDefault();const lane=event.target.closest(".track-lane"),time=Number(event.target.dataset.time);
    place(lane.dataset.channel,time,clamp(time+(event.key==="ArrowRight"?50:-50),0,state.clip.duration_ms));
  });
  $("scrub").oninput=event=>{state.time=Number(event.target.value);renderFrame();};
  $("play").onclick=()=>{if(!state.clip)return;if(state.playing){resetAnimation();return;}
    if(state.time>=state.clip.duration_ms)state.time=0;
    state.playing=true;state.lastFrame=performance.now();$("play").textContent="Ⅱ Pausar";state.raf=requestAnimationFrame(tick);};
  $("stop").onclick=()=>{resetAnimation();state.time=0;renderFrame();};
  $("undo").onclick=undo;$("redo").onclick=redo;
  for(const id of ["clip-name","clip-duration","clip-loop","clip-source","clip-reference","clip-license"]){
    $(id).onchange=()=>{if(!state.clip)return;const next=clone(state.clip);
      next.name=$("clip-name").value.trim();next.duration_ms=Number($("clip-duration").value);
      next.loop=$("clip-loop").checked;next.source={kind:$("clip-source").value,reference:$("clip-reference").value,license:$("clip-license").value};
      if(!next.name||!Number.isInteger(next.duration_ms)||next.duration_ms<100||next.duration_ms>120000||
         Object.values(next.tracks).some(keys=>keys.some(k=>k.time_ms>next.duration_ms))){fail(Error("Nome, duração ou keyframes fora dos limites; a edição não foi aplicada."));renderEditor();return;}
      if(next.source.kind==="permitted"&&!next.source.license.trim()){fail(Error("Declare a permissão de uso antes de salvar a origem externa."));renderEditor();return;}
      state.time=Math.min(state.time,next.duration_ms);push(next);};
  }
  $("key-upsert").onclick=()=>{if(!state.clip)return;
    const channel=$("key-channel").value,time=Number($("key-time").value),value=Number($("key-value").value),intensity=Number($("key-intensity").value),interpolation=$("key-interpolation").value;
    if(!CHANNELS.includes(channel)||!Number.isInteger(time)||time<0||time>state.clip.duration_ms||!Number.isFinite(value)||value< -1||value>1||!Number.isFinite(intensity)||intensity<0||intensity>1||!["linear","ease","step"].includes(interpolation)){fail(Error("Keyframe inválido; revise tempo, valor e intensidade."));return;}
    const next=clone(state.clip),keys=next.tracks[channel]||[];
    next.tracks[channel]=keys.filter(k=>k.time_ms!==time&&!(state.selected?.channel===channel&&k.time_ms===state.selected.time))
      .concat([{time_ms:time,value,intensity,interpolation}]).sort((a,b)=>a.time_ms-b.time_ms);
    state.selected={channel,time};state.time=time;push(next);
  };
  $("key-remove").onclick=()=>{if(!state.selected||!state.clip)return;
    const next=clone(state.clip),{channel,time}=state.selected;
    next.tracks[channel]=next.tracks[channel].filter(k=>k.time_ms!==time);
    state.selected=null;push(next);};
  $("project-list").onchange=async e=>{if(!askLoss()){e.target.value=state.id||"";return;}
    if(e.target.value)try{await open(e.target.value);}catch(error){fail(error);}};
  $("create-project").onclick=async()=>{if(!askLoss())return;
    const clip={name:"Nova animação",duration_ms:2000,loop:true,tracks:{},source:{kind:"own",reference:"",license:"Criação própria (declaração)"}};
    try{const p=await api("POST","/api/animation/projects",{clip});await refreshLists();await open(p.id);}catch(error){fail(error);}};
  $("save-project").onclick=async()=>{if(!state.clip)return;
    try{const p=await api("PUT",`/api/animation/projects/${state.id}`,{clip:state.clip,revision:state.revision});
      state.revision=p.revision;state.dirty=false;await refreshLists();status("Salvo neste computador","saved");message("");}
    catch(error){fail(error);}};
  $("export-project").onclick=async()=>{if(!state.id)return;
    if(state.dirty){fail(Error("Salve as alterações antes de exportar o rascunho."));return;}
    try{const data=await api("GET",`/api/animation/projects/${state.id}/export`);
      const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:"application/json"}));
      const link=document.createElement("a");link.href=url;link.download=`studio-animation-${state.id}.json`;link.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);message("");}catch(error){fail(error);}};
  $("import-project").onclick=()=>$("import-file").click();
  $("import-file").onchange=async e=>{const file=e.target.files[0];e.target.value="";
    if(!file||!askLoss())return;
    if(file.size>2*1024*1024){fail(Error("Arquivo acima de 2 MB; importação recusada."));return;}
    try{const document=JSON.parse(await file.text());const p=await api("POST","/api/animation/import",{document});
      await refreshLists();await open(p.id);}catch(error){fail(error);}};
  $("library-save").onclick=async()=>{if(!state.id)return;
    if(state.dirty){fail(Error("Salve o projeto antes de guardar uma pose ou gesto."));return;}
    try{const kind=$("library-kind").value;
      await api("POST","/api/animation/library",{
        clip:kind==="pose"?poseAt(state.clip,state.time):state.clip,kind});
      await refreshLists();status("Item guardado na biblioteca local","saved");message("");}catch(error){fail(error);}};
  $("library-apply").onclick=async()=>{if(!state.clip||!$("library-list").value)return;
    try{const item=await api("GET",`/api/animation/library/${$("library-list").value}`);
      push(compose(state.clip,item.clip,Math.round(state.time)));}catch(error){fail(error);}};
  $("library-approve").onclick=async()=>{const id=$("library-list").value;if(!id)return;
    const note=$("library-approval-note").value.trim();
    if(!note){fail(Error("Informe uma nota de revisão dos direitos deste item antes de aprová-lo localmente."));return;}
    if(!confirm("Aprovar esta cópia apenas na biblioteca local? Isto NÃO a publica no Forge, no runtime ou em uma engine."))return;
    try{await api("POST",`/api/animation/library/${id}/approve`,{note,confirm:true});await refreshLists();
      $("library-list").value=id;status("Aprovado apenas na biblioteca local","saved");message("");}catch(error){fail(error);}};
  refreshLists().then(()=>{if(state.projects.length)return open(state.projects[0].id);
    status("Nenhum projeto — crie ou importe um rascunho");$("timeline").innerHTML='<div class="empty">Comece criando um projeto de animação.</div>';})
    .catch(fail);
}
if(typeof module!=="undefined")module.exports={sample,frame,compose,poseAt,CHANNELS};
