(() => {
  "use strict";
  const source = window.SCHULUNGSPLAN_KUNDENPAKET;
  if (!source || !source.view || !source.exchange) return;
  const view = source.view;
  const DAYS = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag"];
  const DAY_INDEX = Object.fromEntries(DAYS.map((name,index)=>[name,index]));
  const HOUR_HEIGHT = 72;
  const SNAP = 15;
  const VISIBLE_TYPES = new Set(["training","arrival","departure"]);
  const MOVABLE_TYPES = new Set(["training","arrival","departure"]);
  let blocks = JSON.parse(JSON.stringify(view.blocks || []));
  const baseline = JSON.parse(JSON.stringify(view.blocks || []));
  const baselineById = new Map(baseline.map(block => [block.id, block]));
  let draggedId = "";
  let dragOffsetMinutes = 0;

  const $ = selector => document.querySelector(selector);
  const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
  const toMinutes = value => { const [h,m] = String(value).split(":").map(Number); return h*60+m; };
  const formatTime = value => `${String(Math.floor(value/60)).padStart(2,"0")}:${String(value%60).padStart(2,"0")}`;
  const formatHours = minutes => `${(minutes/60).toLocaleString("de-DE",{minimumFractionDigits:1,maximumFractionDigits:2})} h`;
  const snap = value => Math.round(value / SNAP) * SNAP;
  const duration = block => toMinutes(block.end)-toMinutes(block.start);
  const setStatus = (text, kind="") => { const el=$("#status"); el.textContent=text; el.className=`status ${kind}`.trim(); };

  function mondayOfStart(){
    if(!/^\d{4}-\d{2}-\d{2}$/.test(view.start_date||"")) return null;
    const [y,m,d]=view.start_date.split("-").map(Number); const date=new Date(y,m-1,d,12); const wd=date.getDay(); date.setDate(date.getDate()+(wd===0?-6:1-wd)); return date;
  }
  function calendarDate(week,day){ const monday=mondayOfStart(); if(!monday)return null; const result=new Date(monday); result.setDate(result.getDate()+(week-1)*7+DAY_INDEX[day]); return result; }
  function germanDate(date){ return date?`${String(date.getDate()).padStart(2,"0")}.${String(date.getMonth()+1).padStart(2,"0")}.${date.getFullYear()}`:""; }
  function weekHeading(week){ return `Woche ${week} · ${germanDate(calendarDate(week,"Montag"))}–${germanDate(calendarDate(week,"Freitag"))}`; }
  function availabilityRecord(week,trainer){ return (view.trainer_availability||[]).find(item=>Number(item.week)===Number(week)&&String(item.trainer||"")===String(trainer||"")); }
  function dayIsOnOrAfterStart(week,day){ if(!view.start_date)return true; const date=calendarDate(week,day); if(!date)return true; const [y,m,d]=view.start_date.split("-").map(Number); const start=new Date(y,m-1,d,12); return date.getTime()>=start.getTime(); }
  function dayAvailable(week,trainer,day){ if(!dayIsOnOrAfterStart(week,day))return false; const record=availabilityRecord(week,trainer); const weekdays=record&&Array.isArray(record.weekdays)?record.weekdays:DAYS.slice(0,4); return weekdays.includes(day); }
  function parkedTrainingBlocks(){ return blocks.filter(block=>block.type==="training"&&!dayAvailable(block.week,block.trainer,block.day)); }
  function laneBlocks(week,trainer,day){ return blocks.filter(b=>VISIBLE_TYPES.has(b.type)&&Number(b.week)===Number(week)&&b.trainer===trainer&&b.day===day).sort((a,b)=>a.start.localeCompare(b.start)); }
  function conflict(moving,target){ return blocks.find(other => other.id!==moving.id && Number(other.week)===Number(target.week) && other.day===target.day && other.trainer===target.trainer && toMinutes(target.start)<toMinutes(other.end) && toMinutes(other.start)<toMinutes(target.end)); }

  function changedMoves(){
    return blocks.filter(block=>MOVABLE_TYPES.has(block.type)).filter(block=>{
      const original=baselineById.get(block.id); return original && ["week","day","trainer","start","end"].some(key=>String(block[key])!==String(original[key]));
    }).map(block=>({block_id:block.id,week:Number(block.week),day:block.day,trainer:block.trainer,start:block.start,end:block.end}));
  }
  function updateCount(){ const count=changedMoves().length; const parked=parkedTrainingBlocks().length; $("#change-count").textContent=`${count} Änderung${count===1?"":"en"}${parked?` · ${parked} geparkt`:""}`; const download=$("#download"); download.disabled=parked>0; download.title=parked?"Geparkte Schulungen müssen zuerst auf verfügbare Trainer-Tage verschoben werden.":"Änderungen als JSON herunterladen"; }

  function blockHtml(block){
    const dayStart=toMinutes(view.settings.day_start); const top=((toMinutes(block.start)-dayStart)/60)*HOUR_HEIGHT; const height=Math.max(22,(duration(block)/60)*HOUR_HEIGHT);
    const draggable=MOVABLE_TYPES.has(block.type); const title=block.type==="arrival"?"Anreise":block.type==="departure"?"Abreise":block.title; const parked=block.type==="training"&&!dayAvailable(block.week,block.trainer,block.day);
    return `<article class="block ${escapeHtml(block.type)} ${draggable?"movable":"fixed"} ${parked?"parked":""}" data-id="${escapeHtml(block.id)}" ${draggable?'draggable="true"':''} style="top:${top}px;height:${height}px;--block-bg:${escapeHtml(block.background_color||"#eef2ff")}">
      <strong>${escapeHtml(title)}</strong>${parked?`<span class="parked-badge">Geparkt</span>`:""}${block.group?`<span class="group">${escapeHtml(block.group)}</span>`:""}<span class="meta">${escapeHtml(block.start)}–${escapeHtml(block.end)} · ${escapeHtml(formatHours(duration(block)))}</span>
    </article>`;
  }
  function timeLabels(){ const start=toMinutes(view.settings.day_start), end=toMinutes(view.settings.day_end); let out=""; for(let minute=start;minute<=end;minute+=15){ out+=`<span class="time-label" style="top:${((minute-start)/60)*HOUR_HEIGHT}px">${formatTime(minute)}</span>`;} return out; }
  function dayHtml(week,trainer,day){ const total=(toMinutes(view.settings.day_end)-toMinutes(view.settings.day_start)); const height=(total/60)*HOUR_HEIGHT; const available=dayAvailable(week,trainer,day); return `<section class="day ${available?"available":"unavailable"}"><div class="day-head"><strong>${day}</strong><span>${germanDate(calendarDate(week,day))}</span><em>${available?"Verfügbar":"Nicht verfügbar · Parkfläche"}</em></div><div class="day-body ${available?"available":"unavailable"}" data-week="${week}" data-trainer="${escapeHtml(trainer)}" data-day="${day}" style="--calendar-height:${height}px">${timeLabels()}${laneBlocks(week,trainer,day).map(blockHtml).join("")}</div></section>`; }
  function render(){
    const scrollY=window.scrollY; const meta=[view.customer,view.location,view.product].filter(Boolean).join(" · "); $("#project-meta").textContent=meta;
    $("#calendar").innerHTML=(view.weeks||[]).map(week=>`<section class="week-wrap"><h2 class="week-heading">${weekHeading(week)}</h2>${(view.trainers||[]).map(trainer=>`<section class="trainer-week"><div class="trainer-title">Trainer: ${escapeHtml(trainer)}</div><div class="calendar-scroll"><div class="calendar">${DAYS.map(day=>dayHtml(week,trainer,day)).join("")}</div></div></section>`).join("")}</section>`).join("");
    bindDrag(); updateCount(); requestAnimationFrame(()=>window.scrollTo({top:scrollY}));
  }
  function bindDrag(){
    document.querySelectorAll('.block.movable').forEach(el=>el.addEventListener('dragstart',event=>{ draggedId=el.dataset.id; const rect=el.getBoundingClientRect(); dragOffsetMinutes=((event.clientY-rect.top)/HOUR_HEIGHT)*60; el.classList.add('dragging'); event.dataTransfer.effectAllowed='move'; event.dataTransfer.setData('text/plain',draggedId); }));
    document.querySelectorAll('.block.movable').forEach(el=>el.addEventListener('dragend',()=>el.classList.remove('dragging')));
    document.querySelectorAll('.day-body').forEach(body=>{
      body.addEventListener('dragover',event=>{event.preventDefault();body.classList.add('drop-target');}); body.addEventListener('dragleave',()=>body.classList.remove('drop-target'));
      body.addEventListener('drop',event=>{ event.preventDefault(); body.classList.remove('drop-target'); const block=blocks.find(item=>item.id===(draggedId||event.dataTransfer.getData('text/plain'))); if(!block||!MOVABLE_TYPES.has(block.type))return;
        const week=Number(body.dataset.week), day=body.dataset.day, trainer=body.dataset.trainer;
        const rect=body.getBoundingClientRect(); const length=duration(block); const dayStart=toMinutes(view.settings.day_start), dayEnd=toMinutes(view.settings.day_end); let start=snap(dayStart+((event.clientY-rect.top)/HOUR_HEIGHT)*60-dragOffsetMinutes); start=Math.max(dayStart,Math.min(start,dayEnd-length));
        const target={...block,week,day,trainer,start:formatTime(start),end:formatTime(start+length)}; const hit=conflict(block,target); if(hit){const hidden=hit.type==="break"||hit.type==="lunch";setStatus(hidden?"Der Zielbereich ist nicht verfügbar.":`Der Zielbereich ist durch „${hit.title||hit.type}“ belegt.`,"error");return;}
        Object.assign(block,target); draggedId=""; dragOffsetMinutes=0; if(block.type==="training"&&!dayAvailable(block.week,block.trainer,block.day)){setStatus("Schulungsblock geparkt. Für die Rückgabedatei muss er wieder auf einen verfügbaren Trainer-Tag verschoben werden.","error");}else{setStatus(block.type==="training"?"Schulungsblock verschoben.":block.type==="arrival"?"Anreise verschoben.":"Abreise verschoben.","ok");} render();
      });
    });
  }
  function safePart(value,fallback){ const normalized=String(value||fallback).normalize("NFKD").replace(/[\u0300-\u036f]/g,""); return normalized.replace(/[^A-Za-z0-9]+/g,"-").replace(/^-+|-+$/g,"")||fallback; }
  function download(){ const parked=parkedTrainingBlocks(); if(parked.length){setStatus(`${parked.length} Schulungsblock${parked.length===1?" ist":"e sind"} noch auf nicht verfügbaren Trainer-Tagen geparkt. Bitte zuerst auf verfügbare Tage verschieben.`,"error");return;} const now=new Date(); const date=`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")}`; const time=`${String(now.getHours()).padStart(2,"0")}${String(now.getMinutes()).padStart(2,"0")}`; const payload={format:"schulungsplantool-customer-return",schema_version:1,returned_at:now.toISOString(),exchange:source.exchange,moves:changedMoves()}; const blob=new Blob([JSON.stringify(payload,null,2)],{type:"application/json"}); const url=URL.createObjectURL(blob); const link=document.createElement("a"); link.href=url; link.download=`${safePart(view.customer,"kunde")}_${safePart(view.location,"standort")}_${safePart(view.product,"produkt")}_kundenplanung_${date}_${time}.json`; link.click(); URL.revokeObjectURL(url); setStatus("Rückgabedatei wurde erstellt.","ok"); }
  $("#download").addEventListener("click",download); $("#reset").addEventListener("click",()=>{blocks=JSON.parse(JSON.stringify(baseline));setStatus("Ausgangsplanung wiederhergestellt.");render();}); render();
})();
