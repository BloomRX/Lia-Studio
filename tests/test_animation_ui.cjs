// Pure timeline/preview behavior; no real Lia mesh, browser or Forge contract.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const animation=require('../app/static/animation.js');
const html=fs.readFileSync(path.join(__dirname,'../app/static/animation.html'),'utf8');
const keys=[{time_ms:0,value:0,intensity:1,interpolation:'linear'},
            {time_ms:1000,value:1,intensity:.5,interpolation:'step'},
            {time_ms:2000,value:0,intensity:1,interpolation:'linear'}];
assert.equal(animation.sample(keys,500),.25);
assert.equal(animation.sample(keys,1500),.5);
assert.equal(animation.sample([],500),0);
const eased=[{...keys[0],interpolation:'ease'},keys[1]];
assert.ok(animation.sample(eased,250)<animation.sample(keys,250));
const clip={name:'Autoral',duration_ms:2000,loop:true,source:{kind:'own',reference:'',license:'própria'},
  tracks:{'arm.right':keys,'expression.smile':[{time_ms:0,value:.7,intensity:1,interpolation:'step'}]}};
assert.equal(animation.frame(clip,2500)['arm.right'],.25);
const pose=animation.poseAt(clip,1000);
assert.equal(pose.duration_ms,100);
assert.equal(pose.tracks['arm.right'][0].value,.5);
const combined=animation.compose(clip,pose,1800);
assert.equal(combined.tracks['arm.right'].find(key=>key.time_ms===1800).value,.5);
assert.equal(clip.tracks['arm.right'].length,3); // composição não altera origem
assert.throws(()=>animation.compose(clip,clip,100),/excede/);
for(const control of ['timeline','puppet','play','undo','redo','key-upsert','key-remove',
                       'library-apply','import-file','export-project','save-project'])
  assert.match(html,new RegExp(`id="${control}"`));
assert.match(html,/Contrato de animação Forge \/ Lia-Project pendente/);
console.log('Animation UI timeline/preview: OK');
