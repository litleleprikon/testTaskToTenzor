# -*- coding:utf-8 -*-
import re

file=open('stops.txt','r',encoding='utf-8')
wfile=open('stops.py','w',encoding='utf-8')
print('# -*- coding:utf-8\nstops=(', file=wfile)
lines=file.readlines()
for line in lines:
    exp=re.search('[А-Яа-я]+',line)
    if exp is not None:
        print("'"+line[exp.start():exp.end()]+"',", file=wfile)


print(')', file=wfile)
file.close()
wfile.close()
