document.getElementById("themeBtn").onclick=function(){
  var r=document.documentElement,t=r.dataset.theme==="dark"?"light":"dark";
  r.dataset.theme=t;try{localStorage.setItem("theme",t)}catch(e){}
};
