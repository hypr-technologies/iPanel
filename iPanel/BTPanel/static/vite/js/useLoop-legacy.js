System.register(["./vue-legacy.js?v=1723125373998"],(function(e,t){"use strict";var n;return{setters:[e=>{n=e.y}],execute:function(){e("u",(function(e,t=3){let r=null,u=!1,c=0;const i=()=>{u||(c>=3?l():r=window.setTimeout((async()=>{try{await e(),c=0}catch{c++}finally{i()}}),1e3*t))},l=()=>{r&&(clearTimeout(r),r=null)};return n((()=>{u=!0,l()})),{loop:i,clearTimer:l}}))}}}));


