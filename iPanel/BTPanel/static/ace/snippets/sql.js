define("ace/snippets/sql",["require","exports","module"],function(e,t,n){"use strict";t.snippetText="snippet tbl\n	create table ${1:table} (\n		${2:columns}\n	);\nsnippet col\n	${1:name}	${2:type}	${3:default ''}	${4:not null}\nsnippet ccol\n	${1:name}	varchar2(${2:size})	${3:default ''}	${4:not null}\nsnippet ncol\n	${1:name}	number	${3:default 0}	${4:not null}\nsnippet dcol\n	${1:name}	date	${3:default sysdate}	${4:not null}\nsnippet ind\n	create index ${3:$1_$2} on ${1:table}(${2:column});\nsnippet uind\n	create unique index ${1:name} on ${2:table}(${3:column});\nsnippet tblcom\n	comment on table ${1:table} is '${2:comment}';\nsnippet colcom\n	comment on column ${1:table}.${2:column} is '${3:comment}';\nsnippet addcol\n	alter table ${1:table} add (${2:column} ${3:type});\nsnippet seq\n	create sequence ${1:name} start with ${2:1} increment by ${3:1} minvalue ${4:1};\nsnippet s*\n	select * from ${1:table}\n",t.scope="sql"});                (function() {
                    window.require(["ace/snippets/sql"], function(m) {
                        if (typeof module == "object" && typeof exports == "object" && module) {
                            module.exports = m;
                        }
                    });
                })();
            

