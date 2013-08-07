#-*- encoding: utf-8 -*-

from urllib.request import urlopen
from urllib.parse import urlparse, urlencode
import urllib
from html.parser import HTMLParser
from html.entities import name2codepoint
from htmlTags import *
import re

class HTMLNode:

    def __init__(self,name,attrs, file):
        self.name=name
        self.maxDepth=0
        self.childsAndData=[]
        self.sizeOfData=0
        self.link=None
        self.numChilds=0
        self.attrs=attrs
        self.file=file
        self.data=''

    def __str__(self):
        pass

    def printNode(self,n):
        print(self.name, 'attrs:', self.attrs, file=self.file)

        for child in self.childsAndData:
            if type(child) is not str:
                child.printNode(n+1)
            else:
                print(child, file=self.file)

    def cleaning(self):
        print('clean', self.name)
        for i  in range(len(self.childsAndData)):
            if type(self.childsAndData[i]) is str:
                while True:
                    exp=re.search(r'\s{2,}',self.childsAndData[i])
                    if exp is not None:
                        #print(exp.start(), exp.end())
                        self.childsAndData[i]=self.childsAndData[i][:exp.start()]+' '+self.childsAndData[i][exp.end():]
                    else: 
                        break
                while True:
                    exp=re.search(r'[\n]{2,}',self.childsAndData[i])
                    if exp is not None:
                        print(exp.start(), exp.end())
                        self.childsAndData[i]=self.childsAndData[i][:exp.start()]+'\n'+self.childsAndData[i][exp.end():]
                    else: 
                        break
                while True:
                    exp=re.search(r'<!--.*-->',self.childsAndData[i],re.DOTALL)
                    if exp is not None:
                        #print(exp.start(), exp.end())
                        self.childsAndData[i]=self.childsAndData[i][:exp.start()]+' '+self.childsAndData[i][exp.end():]
                    else: 
                        break
            elif type(self.childsAndData[i]) is HTMLNode:
                self.childsAndData[i].cleaning()

        



class HTMLTree:
    def __init__(self,root,coding,file):
        self.file=file
        self.root=root

    def printTree(self):
        self.root.cleaning()
        print('stop cleaning')
        self.root.printNode(0)
        self.file.close()

class MyParser(HTMLParser):

    def __init__(self,coding):
        HTMLParser.__init__(self)
        self.file=open('res/result.txt','w', encoding=coding)
        self.stack=[]
        self.tree=None
        self.coding=coding

    def handle_starttag(self, tag, attrs):
        name=tag.lower()

        if name in interestingTags and name not in notClosedTags:
            node=HTMLNode(tag, attrs,self.file)
            if self.tree is None:
                self.tree=HTMLTree(node, self.coding, self.file)
            if len(self.stack)>0:
                self.stack[-1].childsAndData.append(node)
            self.stack.append(node)
        
        if name in notClosedTags:
            if len(self.stack)>0:
                self.stack[-1].childsAndData.append(HTMLNode(name,attrs,self.file))
                
            

    def handle_endtag(self, tag):
        if tag.lower() in interestingTags and tag.lower() not in notClosedTags:
            if len(self.stack)>0:
                self.stack.pop()

    def handle_data(self, data):
        if len(self.stack)>0:
            self.stack[-1].childsAndData.append(data.strip())
    
    def handle_charref(self, name):
        if len(self.stack)>0:
            if name.startswith('x'):
                c = chr(int(name[1:], 16))
            else:
                c = chr(int(name))
            self.stack[-1].childsAndData.append( c)

    def __del__(self):
        self.tree.printTree()


class Logic:

    def __init__(self,url):

        self.file=open('res/parsed.txt', 'w')

        if not urlparse(url)[0]:
            url='http://{}'.format(url)
            
        try:
            self.site=urlopen(url, timeout=10)
        except urllib.error.URLError:
            print("I think, that you input wrong link")
            return None
        except urllib.error.HTTPError as error:
            if error.code==404:
                print('This is not the web page you are looking for.')
            else:
                print("I don't know about this error =(")
            return None

        
        
        lines=self.site.readlines()

        ct=self.site.headers['Content-Type']
        for key in self.site.headers:
            print(key, self.site.headers[key])

        print(ct)
        if ct.lower().find('charset=utf-8')!= -1:
            coding='utf-8'
        elif ct.lower().find('charset=windows-1251')!= -1:
            coding='cp1251'
        else:
            print('Bad coding')
            return None
        parser=MyParser(coding)

        #parser.feed(self.site.read().decode(self.coding))
        try:
            for line in lines:
                parser.feed(line.decode(coding))
        except UnicodeEncodeError:
            print('Something bad in coding')
            return None

        del(parser)
        self.file.close()
        print('ok')


if __name__=="__main__":
    #url=str(input("What's url?\n"))
    parse=Logic('http://www.gazeta.ru/politics/2013/08/07_a_5545693.shtml')
    
    input()