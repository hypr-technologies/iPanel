import{j as e}from"./index.js?v=1722509364692";const t=(t,o="")=>{const s=localStorage.getItem(t);return e(o)?null!=s?JSON.parse(s):o:null!=s?s:o},o=(e,t)=>{localStorage.setItem(e,"".concat(t))},s=(e,t)=>{const o=new Date;o.setTime(o.getTime()+2592e6),document.cookie=e+"="+escape(t)+";expires="+o.toUTCString()};export{s as a,t as g,o as s};


