import test from "node:test";
import assert from "node:assert/strict";
import worker from "../src/index.js";

const origin="https://kio5232000.github.io";
const sample={dishes:[{category:"主食",name:"糙米飯"},{category:"主菜",name:"三杯雞"},{category:"蔬菜",name:"青江菜"}]};
const plan={analysis:{summary:"午餐有雞肉、米飯與蔬菜。",ingredients_to_avoid_repeating:["雞肉"],balance_note:"晚餐換成魚或豆腐。"},
 recipes:[1,2,3].map(n=>({name:"晚餐"+n,reason:"主食材換一換",ingredients:["豆腐","蔬菜","白飯"],steps:["洗淨食材。","煮至完全熟透。"],time_minutes:25})),
 disclaimer:"依菜名推測，非營養診斷，亦不代表學生實際吃下的食物。"};
class Db {
 constructor(){this.counts=new Map();this.cache=new Map();this.usage=new Map()}
 prepare(sql){return {bind:(...a)=>({
  first:async()=>{
   if(sql.startsWith("SELECT result_json")){
    const row=this.cache.get(a[0]);return row?.expires_at>a[1]&&row.result_json?row:null;
   }
   if(sql.startsWith("INSERT INTO ai_cache")){
    const [key,owner,lease,now,expiry]=a;
    const row=this.cache.get(key);
    if(row&&(row.lease_until>now||row.expires_at>expiry))return null;
    this.cache.set(key,{owner,lease_until:lease,result_json:null,expires_at:0});return {owner};
   }
   if(sql.startsWith("INSERT INTO quota")){
    const [day,key,max]=a,id=day+":"+key,used=this.counts.get(id)||0;
    if(used>=max)return null;
    this.counts.set(id,used+1);return {used:used+1};
   }
   throw Error("Unexpected first SQL: "+sql);
  },
  run:async()=>{
   if(sql.startsWith("DELETE FROM ai_cache")){
    const row=this.cache.get(a[0]);if(row?.owner===a[1]&&!row.result_json)this.cache.delete(a[0]);
    return {meta:{changes:1}};
   }
   if(sql.startsWith("UPDATE ai_cache")){
    const [result_json,expires_at,key,owner]=a,row=this.cache.get(key);
    if(row?.owner!==owner)return {meta:{changes:0}};
    Object.assign(row,{result_json,expires_at,lease_until:0});return {meta:{changes:1}};
   }
   if(sql.startsWith("INSERT INTO ai_usage_daily")){
    const [day,model,input,cached,output]=a,k=day+":"+model;
    const row=this.usage.get(k)||{responses:0,input:0,cached:0,output:0};
    row.responses++;row.input+=input;row.cached+=cached;row.output+=output;this.usage.set(k,row);
    return {meta:{changes:1}};
   }
   throw Error("Unexpected run SQL: "+sql);
  }
 })}}
}
function env(){return {OPENAI_API_KEY:"mock-server-only",IP_HASH_PEPPER:"test-pepper",QUOTA_DB:new Db()}}
function req(body=sample,ip="203.0.113.5",website=origin){
 return new Request("https://worker.example.workers.dev/recommend",{method:"POST",
  headers:{"Origin":website,"Content-Type":"application/json","CF-Connecting-IP":ip},
  body:JSON.stringify(body)});
}
const date=new Intl.DateTimeFormat("en-CA",{timeZone:"Asia/Taipei",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date());
const verified={...sample,school_code:"213601",date};
async function mockOpenai(t,fn){
 let calls=0;
 const old=globalThis.fetch;globalThis.fetch=async(url,opts)=>{
  if(new URL(url).hostname==="kio5232000.github.io"){
   return Response.json({source:"school_website",school_code:verified.school_code,date,dishes:sample.dishes});
  }
  calls++;
  assert.equal(new URL(url).hostname,"api.openai.com");
  assert.equal(opts.headers.Authorization,"Bearer mock-server-only");
  const sent=JSON.parse(opts.body);
  assert.equal(sent.store,false);
  assert.equal(sent.model,"gpt-5-mini");
  return (fn?await fn(sent):null) || new Response(JSON.stringify({
    usage:{input_tokens:501,input_tokens_details:{cached_tokens:10},output_tokens:900},
    output:[{content:[{type:"output_text",text:JSON.stringify(plan)}]}]
  }),{status:200});
 };
 t.after(()=>{globalThis.fetch=old});
 return ()=>calls;
}
test("valid request produces three recipes without exposing key",async(t)=>{
 await mockOpenai(t);const result=await worker.fetch(req(),env());
 assert.equal(result.status,200);
 const body=await result.json();assert.equal(body.recipes.length,3);
 assert.equal(body.remaining,1);assert.equal(body.mode,"ai");
 assert.equal(JSON.stringify(body).includes("mock-server-only"),false);
});
test("per IP quota blocks third AI call",async(t)=>{
 await mockOpenai(t);const e=env();
 assert.equal((await worker.fetch(req(),e)).status,200);
 assert.equal((await worker.fetch(req(),e)).status,200);
 const blocked=await worker.fetch(req(),e);
 assert.equal(blocked.status,429);
});
test("invalid content, cross origin and missing secrets fail closed",async(t)=>{
 await mockOpenai(t);
 assert.equal((await worker.fetch(req(sample,"203.0.113.5","https://evil.example"),env())).status,403);
 assert.equal((await worker.fetch(req({dishes:[]} ),env())).status,400);
 assert.equal((await worker.fetch(req(),{...env(),OPENAI_API_KEY:undefined})).status,503);
});
test("model errors do not publish fabricated recipes",async(t)=>{
 await mockOpenai(t,()=>new Response("unavailable",{status:502}));
 const response=await worker.fetch(req(),env());
 assert.equal(response.status,502);
 assert.ok((await response.json()).error);
});

test("verified reordered menus share a result across IPs, without quota or duplicate token ledger",async(t)=>{
 const calls=await mockOpenai(t);const e=env();
 const one=await worker.fetch(req(verified),e);assert.equal(one.status,200);assert.equal((await one.json()).cached,false);
 const reversed={...verified,dishes:[...verified.dishes].reverse()};
 const two=await worker.fetch(req(reversed,"203.0.113.6"),e);assert.equal(two.status,200);
 const b=await two.json();assert.equal(b.cached,true);assert.equal(b.remaining,null);assert.equal(calls(),1);
 assert.deepEqual([...e.QUOTA_DB.usage.values()],[{responses:1,input:501,cached:10,output:900}]);
 assert.equal(e.QUOTA_DB.counts.size,2);
});
test("manual and modified menus do not enter shared cache",async(t)=>{
 const calls=await mockOpenai(t);const e=env();
 const changed={...verified,dishes:[...sample.dishes.slice(0,2),{name:"高麗菜",category:"蔬菜"}]};
 assert.equal((await worker.fetch(req(changed),e)).status,200);
 assert.equal((await worker.fetch(req(sample),e)).status,200);
 assert.equal(calls(),2);assert.equal(e.QUOTA_DB.cache.size,0);
});
test("overlapping verified generation returns 409 without second model call",async(t)=>{
 let entered,finish;const enteredPromise=new Promise(r=>{entered=r});const hold=new Promise(r=>{finish=r});
 const calls=await mockOpenai(t,async()=>{entered();await hold;return null});const e=env();
 const one=worker.fetch(req(verified),e);await enteredPromise;
 const two=await worker.fetch(req(verified,"203.0.113.8"),e);
 assert.equal(two.status,409);assert.equal(calls(),1);finish();assert.equal((await one).status,200);
});
test("failed generation releases lease and can be retried",async(t)=>{
 let fail=true;const calls=await mockOpenai(t,()=>fail?new Response("failure",{status:502}):null);const e=env();
 assert.equal((await worker.fetch(req(verified),e)).status,502);assert.equal(e.QUOTA_DB.cache.size,0);
 fail=false;assert.equal((await worker.fetch(req(verified),e)).status,200);assert.equal(calls(),2);
});
test("invalid generated content is not cached but reported usage is counted",async(t)=>{
 await mockOpenai(t,()=>Response.json({usage:{input_tokens:25,output_tokens:30},output:[{content:[{type:"output_text",text:"{}"}]}]}));
 const e=env();assert.equal((await worker.fetch(req(verified),e)).status,502);
 assert.equal(e.QUOTA_DB.cache.size,0);assert.equal([...e.QUOTA_DB.usage.values()][0].output,30);
});
