import{y as t}from"./vue.js?v=1723125373998";function e(e,l=3){let o=null,a=!1,n=0;const r=()=>{a||(n>=3?i():o=window.setTimeout((async()=>{try{await e(),n=0}catch(t){n++}finally{r()}}),1e3*l))},i=()=>{o&&(clearTimeout(o),o=null)};return t((()=>{a=!0,i()})),{loop:r,clearTimer:i}}export{e as u};


