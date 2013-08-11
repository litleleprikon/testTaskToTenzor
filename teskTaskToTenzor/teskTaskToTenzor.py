#-*- encoding: utf-8 -*-

from urllib.request import urlopen
from urllib.parse import urlparse, urlencode
import urllib
from html.parser import HTMLParser
from html.entities import name2codepoint
import html
import re
from htmlTags import interestingTags, badTags, notClosedTags
from stops import stops
import math

class HTMLNode:

    def __init__(self,name,attrs, file):
        #print (attrs)
        self.name=name.lower()
        self.maxDepth=0
        self.childsAndData=[]
        self.sizeOfData=0
        self.link=None

        if self.name.lower()=='a':
            for attr in attrs:
                if attr[0].lower() == 'href':
                    self.link=attr[1]
                
        self.numChilds=0
        self.attrs=attrs
        self.file=file
        self.data=''
        #print('add tag', name)

    def __str__(self):
        string=''
        
        for child in self.childsAndData:
            string+=str(child)
        if self.name == 'a':
            return string.replace(' ','_')+'['+str(self.link)+']'
        else:
            return string

    def printNode(self,n):
        print(self.name, 'attrs:', self.attrs, file=self.file)

        for child in self.childsAndData:
            if type(child) is not str:
                child.printNode(n+1)
            else:
                print(child, file=self.file)

    def cleaning(self):
        diff=0
        for numOfIteration  in range(len(self.childsAndData)):
            i=numOfIteration-diff
            if type(self.childsAndData[i]) is str:
                while True:
                    exp=re.search(r'\s{2,}',self.childsAndData[i])
                    if exp is not None:
                        #print(exp.start(), exp.end())
                        self.childsAndData[i]=self.childsAndData[i][:exp.start()]+' '+self.childsAndData[i][exp.end():]
                    else: 
                        break

                while True:
                    exp=re.search(r'<!--.*-->',self.childsAndData[i],re.DOTALL)
                    if exp is not None:
                        #print(exp.start(), exp.end())
                        self.childsAndData[i]=self.childsAndData[i][:exp.start()]+' '+self.childsAndData[i][exp.end():]
                    else: 
                        break
                self.data=self.data+str(self.childsAndData[i])
                

            else:
                if self.childsAndData[i].name in badTags:
                    toDel=self.childsAndData.pop(i)
                    diff+=1
                    del(toDel)
                else:
                    s=self.childsAndData[i].cleaning()
                    self.data=self.data+str(s)
            self.sizeOfData=len(self.data)
        return self.data

    def analysis(self):
        childsResult=[]

        #def linkInfo(x):
        #    return (-1*abs(math.log2(x/7))+5)/15+1

        if self.childsAndData is not None:
            for child in self.childsAndData:
                if type(child) is HTMLNode:
                    #print(child)
                    childsResult.append(child.analysis())
        
        j=1
        while j< len(childsResult)-1:
            if childsResult[j-1]['sizeOfData']<childsResult[j]['sizeOfData'] and j>0:
                childsResult[j-1],childsResult[j]=childsResult[j],childsResult[j-1]
                j-=1
            else:
                j+=1


        for result in childsResult:
            if result['maxDepth']>self.maxDepth:
                self.maxDepth=result['maxDepth']
        
        if self.maxDepth>3:
            return childsResult[-1]

        numOfLinks=0
        for child in self.childsAndData:
            if type(child) is str:
                for word in child.split(' '):
                    if word in stops:
                        self.sizeOfData+=0.5*len(child)
                        #print(word)
            elif type(child) is HTMLNode:
                if child.name is 'a':
                    numOfLinks+=1
                elif child.name is 'h1' or 'h2' or 'h3' or 'h4' or 'h5' or 'h6':
                    self.sizeOfData+=0.7*len(str(child))
                elif child.name is 'b' or 'i' or 'abbr' or 'acronym' or 'br' or 'cite' or 'code' or 'em' or 'q' or 's' or 'strong' or 'sub' or 'sup' or 'tt':
                    self.sizeOfData+=0.5*child.sizeOfData
        
        #if numOfLinks:
        #    self.sizeOfData*=linkInfo(numOfLinks)

        toReturn={
                  'self':self,
                  'maxDepth':self.maxDepth+1,
                  'sizeOfData':self.sizeOfData
                 }

        return toReturn




    def __del__(self):
        #print('start deleting',self.name)
        while self.childsAndData:
            toDel=self.childsAndData.pop()
            del(toDel)


class HTMLTree:
    def __init__(self,root,coding,file):
        self.file=file
        self.root=root

    def printTree(self):
        self.root.cleaning()
        print(str(self.root.analysis()['self']), file=self.file)

        self.file.close()


class MyParser(HTMLParser):

    def __init__(self,coding):
        HTMLParser.__init__(self, strict=True)
        self.file=open('res/result.txt','w', encoding=coding)
        self.stack=[]
        self.tree=None
        self.coding=coding

    def getstring(self):
        self.tree.printTree()

    def handle_starttag(self, tag, attrs):
        name=tag.lower()
        if name=='body' or self.stack:
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
        name=tag.lower()

        if self.stack and name in interestingTags and name not in notClosedTags:
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

        line=self.site.read()

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

            parser.feed(line.decode(coding))

        except UnicodeEncodeError:
            print('Something bad in coding')
            return None
        except html.parser.HTMLParseError:
            print('Sorry, but this page is not valid')
            return None
        finally:
            self.file.close()

        parser.getstring()
        print('ok')


if __name__=="__main__":
    #url=str(input("What's url?\n"))
    parse=Logic('http://lenta.ru/news/2013/08/11/bolt/')
    
    input()