import{v as s,i as t}from"./page_layout.js?v=1752142539265";const{t:e}=t.global,a=t=>s.post("/site?action=GetSSL",t),o=t=>s.post("/site?action=HttpToHttps",t,{requestOptions:{loading:e("WP.api.tamper_8"),successMessage:!0}}),i=t=>s.post("/site?action=CloseToHttps",t,{requestOptions:{loading:e("WP.api.tamper_8"),successMessage:!0}}),p=t=>s.post("/site?action=CloseSSLConf",t,{requestOptions:{loading:e("WP.api.tamper_8"),successMessage:!0}}),c=()=>s.post("/ssl?action=GetCertList"),n=t=>s.post("/site?action=GetSSL",t);export{p as a,a as b,i as c,c as d,n as g,o as s};


