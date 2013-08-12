#-*- encoding: utf-8 -*-

from urllib.request import urlopen
from urllib.parse import urlparse, urlencode
import urllib
from html.parser import HTMLParser
from html.entities import name2codepoint
import html
import re
import os
from htmlTags import interestingTags, badTags, notClosedTags
from stops import stops
import math

class HTMLNode:

    def __init__(self,name,attrs):
        self.name=name.lower()
        self.maxDepth=0
        self.childsAndData=[]
        self.sizeOfData=0
        self.link=None

        if self.name.lower()=='a':
            for attr in attrs:
                if attr[0].lower() == 'href':
                    self.link=attr[1]
                
        self.attrs=attrs
        self.data=''

    def __str__(self):
        string=''
        
        for child in self.childsAndData:
            string+=str(child)+' '

        if self.name is 'h1' or 'h2' or 'h3' or 'h4' or 'h5' or 'h6' or 'br' or 'hr':
            return string+'\n'

        if self.name == 'a':
            return string.replace(' ','_')+'['+str(self.link)+']'
        else:
            return string

    def cleaning(self):
        diff=0
        for numOfIteration  in range(len(self.childsAndData)):
            i=numOfIteration-diff
            if type(self.childsAndData[i]) is str:
                while True:
                    exp=re.search(r'\s{2,}',self.childsAndData[i])
                    if exp is not None:
                        self.childsAndData[i]=self.childsAndData[i][:exp.start()]+' '+self.childsAndData[i][exp.end():]
                    else: 
                        break

                while True:
                    exp=re.search(r'<!--.*-->',self.childsAndData[i],re.DOTALL)
                    if exp is not None:
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

        def linkInfo(x):
            return x**6/2520-11*x**5/420+1129*x**4/2520-453*x**3/140+13169*x*x/1260-1327*x/105+7

        DEPTH_THRESHOLD=3

        childsResults=[]
        numOfLinks=0
        dataInLinks=0



        for child in self.childsAndData:
            if type(child) is HTMLNode:
                
                childsResults.append(child.analysis())
                numOfLinks+=childsResults[-1]['numOfLinks']
                dataInLinks+=childsResults[-1]['dataInLinks']

                if child.name is 'a':
                    numOfLinks+=1
                    for i in child.childsAndData:
                        dataInLinks+=len(str(i))                

                elif child.name is 'h1' or 'h2' or 'h3' or 'h4' or 'h5' or 'h6':
                    self.sizeOfData+=0.7*len(str(child))
                
                elif child.name is 'b' or 'i' or 'abbr' or 'acronym' or 'br' or 'cite' or 'code' or 'em' or 'q' or 's' or 'strong' or 'sub' or 'sup' or 'tt':
                    self.sizeOfData+=0.5*child.sizeOfData


                if childsResults:
                    if childsResults[-1]['maxDepth']>self.maxDepth:
                        self.maxDepth=childsResults[-1]['maxDepth']

            elif type(child) is str:
                for word in child.split(' '):
                    if word in stops:
                        self.sizeOfData+=0.5*len(child)

        j=1
        while j<=len(childsResults)-1:       #Вот здесь вот можно бы и быструю сортировку написать, для увеличения быстродействия, но мне больше нравится гномья
            if childsResults[j-1]['sizeOfData']<childsResults[j]['sizeOfData'] and j>0:
                childsResults[j-1],childsResults[j]=childsResults[j],childsResults[j-1]
                j-=1
            else:
                j+=1

        if self.maxDepth>=DEPTH_THRESHOLD:
            return childsResults[0]

        if numOfLinks:
            self.sizeOfData+=linkInfo(numOfLinks)*dataInLinks

        toReturn={
                  'self':self,
                  'maxDepth':self.maxDepth+1,
                  'sizeOfData':self.sizeOfData,
                  'numOfLinks':numOfLinks,
                  'dataInLinks':dataInLinks
                 }

        if childsResults:
            if self.sizeOfData<childsResults[0]['sizeOfData']:
                return childsResults[0]
        
        return toReturn

    def __del__(self):
        while self.childsAndData:
            toDel=self.childsAndData.pop()
            del(toDel)


class HTMLTree:
    def __init__(self,root,coding,file):
        self.file=file
        self.root=root

    def printTree(self):
        self.root.cleaning()
        arrayOfWords=str(self.root.analysis()['self']).split(' ')
        lines=[]
        lenght=len(arrayOfWords)
        line=''

        for word in arrayOfWords:
            if len(line)+len(word)>80:
                lines.append(line)
                line=word+' '
            else:
                if len(word)>80:
                    lines.append(line)
                    lines.append(word)
                    line=''
                else:
                    line+=word+' '
        lines.append(line)

        for line in lines:
            print(line, file=self.file)


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
                node=HTMLNode(tag, attrs)
                if self.tree is None:
                    self.tree=HTMLTree(node, self.coding, self.file)
                if len(self.stack)>0:
                    self.stack[-1].childsAndData.append(node)
                self.stack.append(node)

            if name in notClosedTags:
                if len(self.stack)>0:
                    self.stack[-1].childsAndData.append(HTMLNode(name,attrs))      

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

        if ct.lower().find('charset=utf-8')!= -1:
            coding='utf-8'
        elif ct.lower().find('charset=windows-1251')!= -1:
            coding='cp1251'
        else:
            print('Bad coding')
            return None
        parser=MyParser(coding)

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
    parse=Logic('http://habrahabr.ru/post/189772/')
    os.system('start res/result.txt')
    input()