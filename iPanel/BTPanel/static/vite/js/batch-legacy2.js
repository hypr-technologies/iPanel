System.register(["./index.vue_vue_type_script_setup_true_lang-legacy.js?v=1752142539265","./index.vue_vue_type_script_setup_true_lang-legacy2.js?v=1752142539265","./index.vue_vue_type_script_setup_true_lang-legacy16.js?v=1752142539265","./mail-legacy.js?v=1752142539265","./vue-legacy.js?v=1752142539265","./naive-legacy.js?v=1752142539265","./index-legacy96.js?v=1752142539265","./page_layout-legacy.js?v=1752142539265","./common-legacy.js?v=1752142539265","./__commonjsHelpers__-legacy.js?v=1752142539265","./public-legacy.js?v=1752142539265"],(function(a,e){"use strict";var l,u,t,n,o,s,i,r,_,d,p,c,m,v,x,g,q,y,b,w;return{setters:[a=>{l=a._},a=>{u=a._},a=>{t=a._},a=>{n=a.aj},a=>{o=a.k,s=a.P,i=a.r,r=a.e,_=a.a1,d=a.X,p=a.a2,c=a.Q,m=a.an,v=a.W,x=a.V},a=>{g=a.cz,q=a.aq,y=a.bZ,b=a.c1,w=a.cD},null,null,null,null,null],execute:function(){const e={class:"w-100px ml-10px"};a("default",o({__name:"batch",props:{data:{}},setup(a,{expose:o}){const f=a,{getList:h}=f.data,{t:j}=s(),B=i(null),M=r({domain:"",password:"",random_str:"",maxnum:20,quota:5,quota_unit:"GB",quota_limit:1}),k=[{label:"GB",value:"GB"},{label:"MB",value:"MB"}],U={password:{required:!0,trigger:"blur",message:j("Config.Panel.index_67")}};return o({onConfirm:async()=>{await(B.value?.validate()),await n({domain:M.domain,password:M.password,random_str:M.random_str,maxnum:M.maxnum||20,quota:M.quota?M.quota+" "+M.quota_unit:"5 GB",quota_active:M.quota_limit}),h?.()}}),(a,n)=>{const o=g,s=u,i=q,r=y,f=b,h=w,j=l;return d(),_(j,{ref_key:"formRef",ref:B,model:v(M),rules:U,class:"p-20px"},{default:p((()=>[c(o,{label:a.$t("Layout.Sider.mail_3"),"show-require-mark":!0},{default:p((()=>[c(t,{class:"w-280px",value:v(M).domain,"onUpdate:value":n[0]||(n[0]=a=>v(M).domain=a),all:!1},null,8,["value"])])),_:1},8,["label"]),c(o,{label:a.$t("Config.Panel.index_66"),path:"password","show-require-mark":!0},{default:p((()=>[c(s,{class:"w-280px",value:v(M).password,"onUpdate:value":n[1]||(n[1]=a=>v(M).password=a),length:8,placeholder:a.$t("Config.Panel.index_67")},null,8,["value","placeholder"])])),_:1},8,["label"]),c(o,{label:a.$t("Mail.MailBox.index_32")},{default:p((()=>[c(i,{class:"w-280px!",value:v(M).random_str,"onUpdate:value":n[2]||(n[2]=a=>v(M).random_str=a),placeholder:""},null,8,["value"])])),_:1},8,["label"]),c(o,{label:a.$t("Mail.MailBox.index_33")},{default:p((()=>[c(r,{class:"w-280px!",min:1,"show-button":!1,value:v(M).maxnum,"onUpdate:value":n[3]||(n[3]=a=>v(M).maxnum=a)},null,8,["value"])])),_:1},8,["label"]),c(o,{label:"Quota limit"},{default:p((()=>[c(f,{"checked-value":1,"unchecked-value":0,value:v(M).quota_limit,"onUpdate:value":n[4]||(n[4]=a=>v(M).quota_limit=a)},null,8,["value"])])),_:1}),v(M).quota_limit?(d(),_(o,{key:0,label:a.$t("Mail.MailBox.index_3"),path:"quota"},{default:p((()=>[c(r,{value:v(M).quota,"onUpdate:value":n[5]||(n[5]=a=>v(M).quota=a),class:"w-170px",min:1,"show-button":!1,placeholder:""},null,8,["value"]),x("div",e,[c(h,{value:v(M).quota_unit,"onUpdate:value":n[6]||(n[6]=a=>v(M).quota_unit=a),options:k},null,8,["value"])])])),_:1},8,["label"])):m("",!0)])),_:1},8,["model"])}}}))}}}));


