import test from "node:test";
import assert from "node:assert/strict";
import worker from "../src/index.js";

const origin="https://kio5232000.github.io";
const sample={dishes:[{category:"主食",name:"糙米飯"},{category:"主菜",name:"三杯雞"},{category:"蔬菜",name:"青江菜"}]};
const plan={analysis:{summary:"午餐有雞肉、米飯與蔬菜。",ingredients_to_avoid_repeating:["雞肉"],balance_note:"晚餐換成魚或豆腐。"},
 recipes:[1,2,3].map(n=>({name:"晚餐"+n,reason:"主食材換一換",ingredients:["豆腐","蔬菜","白飯"],steps:["洗淨食材。","煮至完全熟透。"],time_minutes:25})),
 disclaimer:"依菜名推測，非營養診斷，亦不代表學生實際吃下的食物。"};
class Db {
 constructor(){this.counts=new Map()}
 prepare(sql){return {bind:(day,key,max)=>({first:async()=>{
  const id=day+":"+key,used=this.counts.get(id)||0;
  if(used>=max)return null;
  this.counts.set(id,used+1);
  return {used:used+1};
 }})}}
}
function env(){return {OPENAI_API_KEY:"mock-server-only",IP_HASH_PEPPER:"test-pepper",QUOTA_DB:new Db()}}
function req(body=sample,ip="203.0.113.5",website=origin){
 return new Request("https://worker.example.workers.dev/recommend",{method:"POST",
  headers:{"Origin":website,"Content-Type":"application/json","CF-Connecting-IP":ip},
  body:JSON.stringify(body)});
}
async function mockOpenai(t,fn){
 const old=globalThis.fetch;globalThis.fetch=async(url,opts)=>{
  assert.equal(new URL(url).hostname,"api.openai.com");
  assert.equal(opts.headers.Authorization,"Bearer mock-server-only");
  const sent=JSON.parse(opts.body);
  assert.equal(sent.store,false);
  assert.equal(sent.model,"gpt-5-mini");
  return fn?.(sent) || new Response(JSON.stringify({
    output:[{content:[{type:"output_text",text:JSON.stringify(plan)}]}]
  }),{status:200});
 };
 t.after(()=>{globalThis.fetch=old});
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
