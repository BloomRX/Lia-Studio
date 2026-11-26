// Duas entradas de UI; sugestão não cria projeto nem aciona agente.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const elements = {
  view: {innerHTML: '', focus() {}},
  toast: {textContent: '', hidden: true},
  'np-name': {value: 'Ilhas'},
  'np-loc': {value: ''},
  'np-intent': {value: 'preciso de um prompt para executor'},
  'np-suggestion': {textContent: ''},
};
const radios = [{value:'guided', checked:false}, {value:'brief', checked:false}];
const calls = [];
const context = {
  document: {
    body: {dataset:{}},
    getElementById: id => elements[id],
    querySelectorAll: () => radios,
    querySelector: () => radios.find(r => r.checked),
  },
  window: {addEventListener() {}},
  location: {hash:'#/home'},
  fetch: async (url, opts) => {
    calls.push([url,opts]);
    if (url === '/api/projects' && opts.method === 'GET')
      return {ok:true, json:async()=>({projects:[]})};
    if (url === '/api/start-routes/recommend')
      return {ok:true, json:async()=>({suggested:'brief',reason:'Texto para executor',runtime_connected:false})};
    if (url === '/api/projects' && opts.method === 'POST')
      return {ok:true, json:async()=>({id:'project-1',start_route:JSON.parse(opts.body).start_route})};
    throw new Error(url);
  },
  clearTimeout, setTimeout:()=>1,
};
const source=fs.readFileSync(path.join(__dirname,'../app/static/app.js'),'utf8');
vm.runInNewContext(source.replace(/navigate\(\);\s*$/, ''),context);
(async()=>{
  await context.renderHome();
  assert.match(elements.view.innerHTML,/value="guided"/);
  assert.doesNotMatch(elements.view.innerHTML,/value="guided" checked/);
  assert.match(elements.view.innerHTML,/value="brief"/);
  await context.createProject();
  assert.equal(calls.filter(([url,opts])=>url==='/api/projects'&&opts.method==='POST').length,0);
  assert.match(context.projectBootstrap('project-1',{docs:[],entry:{start_route:'brief'}}),/id="b-delivery"/);
  assert.doesNotMatch(context.projectBootstrap('project-1',{docs:[],entry:{start_route:'guided'}}),/id="b-delivery"/);
  await context.suggestStartRoute();
  assert.equal(calls.at(-1)[0],'/api/start-routes/recommend');
  assert.equal(calls.filter(([url,opts])=>url==='/api/projects'&&opts.method==='POST').length,0);
  assert.equal(radios[0].checked,false); // sugestão não troca a escolha
  assert.equal(radios[1].checked,false);
  assert.match(elements['np-suggestion'].textContent,/Sugestão: brief para executor/);
  radios[0].checked=false; radios[1].checked=true; // escolha consciente do Dev
  await context.createProject();
  assert.equal(JSON.parse(calls.at(-1)[1].body).start_route,'brief');
  assert.equal(context.location.hash,'#/project/project-1/bootstrap');
  // Manual selection remains possible even after a suggestion.
  radios[1].checked=false;radios[0].checked=true;
  await context.createProject();
  assert.equal(JSON.parse(calls.at(-1)[1].body).start_route,'guided');
  const inputs={
    'b-idea':'Explorar ilhas','b-origin':'','b-exp':'Curiosidade','b-aud':'','b-plat':'',
    'b-pillars':'','b-rest':'','b-ref':'','b-vs':'','b-eng':'','b-delivery':'Protótipo',
    'b-req':'Sem combate','b-examples':'Um farol','b-delegated':'Escolher movimento'
  };
  context.document.getElementById=id=>({value:inputs[id]});
  context.fetch=async(url,opts)=>{calls.push([url,opts]);return {ok:true,json:async()=>({})};};
  await context.runBootstrap('project-1','brief');
  const [url,request]=calls.at(-1);
  assert.equal(url,'/api/projects/project-1/bootstrap');
  const answers=JSON.parse(request.body).answers;
  assert.equal(answers.delivery,'Protótipo');
  assert.equal(answers.requirements[0],'Sem combate');
  assert.equal(answers.examples[0],'Um farol');
  assert.equal(answers.delegated[0],'Escolher movimento');
  assert.equal(request.body.includes('game-prompt-architect'),false);
  console.log('UI rotas: escolha, sugestão sem escrita e brief opcional OK');
})().catch(e=>{console.error(e);process.exitCode=1;});
