const DIGITS="0123456789ABCDEF";
const NAMES={2:"Binary",8:"Octal",10:"Decimal",16:"Hexadecimal"};
function parse(text,base){
  let s=text.trim().toUpperCase(),neg=false;
  if(s[0]==="-"){neg=true;s=s.slice(1);}
  if(!s)throw new Error("Enter a value.");
  let n=0n;const b=BigInt(base);
  for(const ch of s){
    const d=DIGITS.indexOf(ch);
    if(d<0||d>=base)throw new Error("'"+ch+"' is not a valid base-"+base+" digit.");
    n=n*b+BigInt(d);
  }
  return neg?-n:n;
}
function show(n,base){return n.toString(base).toUpperCase();}
function allBases(n){
  return [2,8,10,16].map(b=>"<tr><th>"+NAMES[b]+"</th><td class='mono'>"+show(n,b)+"</td></tr>").join("");
}
function render(id,html){document.getElementById(id).innerHTML=html;}
function err(id,e){render(id,"<p class='err'>"+String(e.message).replace(/</g,"&lt;")+"</p>");}

function doConv(){
  const v=document.getElementById("cv").value;
  if(!v.trim()){render("cout","");return;}
  try{render("cout","<div class='scroll'><table>"+allBases(parse(v,+document.getElementById("cb").value))+"</table></div>");}
  catch(e){err("cout",e);}
}
function doArith(){
  const x=document.getElementById("a1").value,y=document.getElementById("a2").value;
  if(!x.trim()&&!y.trim()){render("aout","");return;}
  const base=+document.getElementById("ab").value,op=document.getElementById("ao").value;
  try{
    const p=parse(x,base),q=parse(y,base);let html;
    if(op==="/"){
      if(q===0n)throw new Error("Cannot divide by zero.");
      const quo=p/q,rem=p%q; // BigInt division truncates toward zero
      html="<div class='out'>Quotient: "+show(quo,base)+"<br>Remainder: "+show(rem,base)+" (base "+base+")</div>"+
           "<h3>Quotient in other bases</h3><div class='scroll'><table>"+allBases(quo)+"</table></div>";
    }else{
      const r=op==="+"?p+q:op==="-"?p-q:p*q;
      html="<div class='out'>"+show(p,base)+" "+op+" "+show(q,base)+" = "+show(r,base)+" (base "+base+")</div>"+
           "<h3>Result in all bases</h3><div class='scroll'><table>"+allBases(r)+"</table></div>";
    }
    render("aout",html);
  }catch(e){err("aout",e);}
}
["cv","cb"].forEach(i=>document.getElementById(i).addEventListener("input",doConv));
["a1","a2","ao","ab"].forEach(i=>document.getElementById(i).addEventListener("input",doArith));
document.querySelectorAll("[data-tab]").forEach(btn=>btn.addEventListener("click",()=>{
  document.querySelectorAll("[data-tab]").forEach(b=>b.setAttribute("aria-selected",b===btn));
  ["ics","conv","arith"].forEach(id=>document.getElementById(id).hidden=(id!==btn.dataset.tab));
}));
