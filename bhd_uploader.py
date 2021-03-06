#!/usr/bin/env python3
import requests
import subprocess
from argparse import ArgumentParser
from pathlib import Path
import shutil
from tmdbv3api import TMDb,Movie,TV
import json
import http.cookiejar
import os
import tempfile
from guessit import guessit
from imdb import IMDb
import pickle
import math
import sys
from bs4 import BeautifulSoup
import configparser
from requests_html import HTML
config = configparser.ConfigParser(allow_no_value=True)
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter


import re
from pymediainfo import MediaInfo
from threading import Thread
from shutil import which
import bencode
from pyrobase.parts import Bunch
from rtorrent_xmlrpc import SCGIServerProxy
import logging
from datetime import datetime
from consolemenu import SelectionMenu
import copy


if sys.platform!="win32":
   from simple_term_menu import TerminalMenu

KNOWN_EDITIONS = ["Director's Cut", "Unrated", "Extended Edition", "2 in 1", "The Criterion Collection"]


class filter(logging.Filter):
    def __init__(self, args):
        super(filter, self).__init__()
        self.args = args

    def filter(self, rec):
        if rec.msg==None:
             return 1
        #change Memory address of input
        rec.msg=copy.deepcopy(rec.msg)
        try:
            rec.msg=rec.msg.decode('utf8', 'strict')
        except:
            pass

        try:
            rec.msg=vars(rec.msg)
        except:
            pass

        if type(rec.msg)==str:
            rec.msg=re.sub(self.args.tmdbapi,"your_tmdbapi",rec.msg)

        elif type(rec.msg)==dict and rec.msg.get('tmdbapi')!=None:
            rec.msg['tmdbapi']="your_tmdbapi"
        return 1



def create_config(args):
    if args.config==None or os.path.exists(args.config)==False:
        bhdlogger.warn("Could not read config")
        return args
    try:
        configpath=args.config
        config.read(configpath)

    except:
        bhdlogger.warn("Error reading config")
        return args
    if args.imgbb==None:
        args.imgbb=config['api']['imgbb']
    if args.log==None and len(config['general']['log'])!=0:
        args.log=config['general']['log']
    if args.log==None and len(config['general']['log'])==0:
        args.log="INFO"
    if args.tmdbapi==None and len(config['api']['tmdbapi'])!=0:
        args.tmdbapi=config['api']['tmdbapi']
    if args.bhdapi==None and len(config['api']['bhdapi'])!=0:
        args.bhdapi=config['api']['bhdapi']
    if args.media==None and len(config['general']['media'])!=0:
        args.media=config['general']['media']
    if args.batchmode==None and len(config['general']['batchmode'])!=0:
        args.batchmode=config['general']['batchmode']
    if args.batchmode==None and len(config['general']['batchmode'])==0:
        args.batchmode=True
    if args.client==None and len(config['client']['client'])!=0:
        args.client=config['client']['client']
    if args.clienturl==None and len(config['client']['clienturl'])!=0:
        args.clienturl=config['client']['clienturl']
    if args.clientcat==None and len(config['client']['clientcat'])!=0:
        args.clientcat=config['client']['clientcat']
    if args.clientuser==None and len(config['client']['clientuser'])!=0:
        args.clientuser=config['client']['clientuser']
    if args.clientpass==None and len(config['client']['clientpass'])!=0:
        args.clientpass=config['client']['clientpass']
    if args.font==None and len(config['general']['font'])==0:
        args.font=os.path.join(os.path.dirname(os.path.abspath(__file__)),"bin","OpenSans-Regular.ttf")
    if args.font==None :
        args.font=config['general']['font']
    if args.numscreens!=None :
        args.numscreens=int(args.numscreens)
    if args.numscreens==None and len(config['general']['numscreens'])==0:
        args.numscreens=9
    if args.numscreens==None and len(config['general']['numscreens'])!=0 :
        args.numscreen==int(config['general']['numscreens'])
    if args.mtn==None and len(config['programs']['mtn'])>0 :
        args.mtn=config['programs']['mtn']
    if args.oxipng==None and len(config['programs']['oxipng'])>0 :
        args.oxipng=config['programs']['oxipng']
    if args.dottorrent==None and len(config['programs']['dottorrent'])>0 :
        args.dottorrent=config['programs']['dottorrent']
    if args.wget==None and len(config['programs']['wget'])>0 :
        args.wget=config['programs']['wget']
    if args.fd==None and len(config['programs']['fd'])>0 :
        args.fd=config['programs']['fd']


#set flags
    if args.anon==True:
        args.anon=1

    if args.anon==False:
        args.anon=0

    if args.pack==True:
        args.pack=1

    if args.pack==False:
        args.pack=0

    if args.special==True:
        args.special=1

    if args.special==False:
        args.special=0

    if args.sd==True:
        args.sd=1

    if args.sd==False:
        args.sd=0

    if args.live==True:
        args.live=1

    if args.live==False:
        args.live=0
    #reset options to auto if in batchmode
    if args.batchmode==True:
        print("Batchmode is ON\n","Forcing Options\n","imdb set to AUTO-DETECT\n","tmdb set to AUTO-DETECT\n","mediasource set to AUTO-DETECT\n","codec set to AUTO-DETECT\n" \
        ,"group set to AUTO-DETECT\n","type set to AUTO-DETECT\n")
        args.imdb="AUTO-DETECT"
        args.tmdb="AUTO-DETECT"
        args.mediasource="AUTO-DETECT"
        args.type="AUTO-DETECT"



    #set logger

    if args.log.upper() == "DEBUG":
        bhdlogger.setLevel(logging.DEBUG)
    elif args.log.upper() == "INFO":
        bhdlogger.setLevel(logging.INFO)
    else:
        bhdlogger.setLevel(logging.WARN)
    bhdlogger.debug(args)

    return args

def clear_movie(args):
    args.imdb="AUTO-DETECT"
    args.mediasource="AUTO-DETECT"
    args.type="AUTO-DETECT"

def get_audio(info):
    output=""
    audio=info.get("audio_codec","")
    channels=info.get("audio_channels","")
    profile=info.get("audio_profile","")


    if isinstance(audio,list):
        for element in audio:
            output=output+" "+element
    elif audio=="":
        pass
    else:
        output=output+audio
    if profile=="Master Audio":
        output=output+" MA"
    if channels!="":
        output=output+" "+channels
    #fix some formatting
    output=re.sub("Dolby TrueHD","TrueHD",output)
    return output
def get_extra(title,info):
    extra=""
    if re.search("atmos",title,re.IGNORECASE)!=None:
        extra=extra+"ATMOS"
    return extra
def get_title(args,path):
    title=os.path.basename(path)
    output_title=""
    info=guessit(title)
    name=info.get("title")
    year=info.get("year","")
    res=  info.get("screen_size","")
    group=info.get("release_group","Unknown")
    channels=info.get("audio_channels","")
    codec=info.get("video_codec")
    audio=get_audio(info)
    extra=get_extra(title,info)
    season="S0"+info.get("season","")
    if args.type=="Movie" and re.search("blur|blu-r",title,re.IGNORECASE)!=None and re.search("remux",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {res} Blu-ray AVC Remux {audio } {extra}-{group}"


    elif args.type=="Movie" and re.search("blur|blu-r",title,re.IGNORECASE)!=None and re.search("264|265",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {res} Blu-ray {codec} {audio } {extra}-{group}"

    elif args.type=="Movie" and re.search("dvd",title,re.IGNORECASE)!=None and re.search("remux",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {res} DVD Remux {audio } {extra}-{group}"

    elif args.type=="Movie" and re.search("hddvd",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {res} DVD {codec} {audio } {extra}--{group}"

    elif args.type=="Movie" and re.search("dvd",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {res} DVD {codec} {audio } {extra}-{group}"

    elif args.type=="Movie" and re.search("webd|web-d",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {res} WEB-DL {audio } {extra}-{group}"
    elif args.type=="Movie" and re.search("webr|web=r",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {res} WEB-RIP {codec} {audio } {extra}-{group}"
    elif args.type=="Movie" and re.search("hdtv",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {res} HDTV {codec} {audio } {extra}-{group}"

    elif args.type=="TV" and re.search("blur|blu-r",title,re.IGNORECASE)!=None  and re.search("remux",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {season} {res} Blu-ray Remux {audio } {extra}-{group}"

    elif args.type=="TV" and re.search("blur|blu-r",title,re.IGNORECASE)!=None and re.search("264|265",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {season} {res} Blu-ray {codec} {audio } {extra}-{group}"

    elif args.type=="TV" and re.search("dvd",title,re.IGNORECASE)!=None and re.search("remux",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {season} {res} DVD Remux {audio } {extra}-{group}"

    elif args.type=="TV" and re.search("hddvd",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {season} {res} DVD {codec} {audio } {extra}-{group}"

    elif args.type=="TV" and re.search("dvd",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {season} {res} DVD {codec} {audio } {extra}-{group}"

    elif args.type=="TV" and re.search("webd|web-d",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {res} {season} WEB-DL {audio } {extra}-{group}"
    elif args.type=="TV" and re.search("webr|web-r",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {res} {season} WEB-RIP {codec} {audio } {extra}-{group}"
    elif args.type=="TV" and re.search("hdtv",title,re.IGNORECASE)!=None:
        output_title=f"{name} {year} {res} {season} HDTV {codec} {audio } {extra}-{group}"
        #final title fixes
    output_title=re.sub(" -","-",output_title)
    return output_title




def get_type(path):
    title=os.path.basename(path)
    info=guessit(title)
    res=info.get("screen_size")
    if re.search("blur|blu-r",title,re.IGNORECASE)!=None and re.search("remux",title,re.IGNORECASE)!=None:
        if res=="2160p":
            type="UHD Remux"
        else:
            type="BD Remux"
    elif re.search("blur|blu-r",title,re.IGNORECASE)!=None:
        type=res

    elif re.search("dvdr",title,re.IGNORECASE)!=None:
        type="DVD Remux"
    return type




def get_imdb_info(path):

    details=guessit(path)
    title = details['title']
    if 'year' in details:
        title = "{} {}".format(title, details['year'])
    results = IMDb().search_movie(title)
    if len(results)==0 :
        bhdlogger.warn("Unable to find imdb")
        id=input("Please Enter imdb id: ")
        id=re.sub("https://www.imdb.com/title/","",id)
        id=re.sub("tt","",id)
        id=re.sub("/","",id)
        results=IMDb().get_movie(id)
    bhdlogger.debug(results)
    if isinstance(results, list)!=True:
        return results

    counter=0
    accept='No'
    bhdlogger.warn("Searching for movie/TV Show on IMDB\n")
    while accept!="Yes":
        if counter==6:
            id=input("Pleases Enter imdb id: ")
            id=re.sub("https://www.imdb.com/title/","",id)
            id=re.sub("tt","",id)
            id=re.sub("/","",id)
            results=IMDb().get_movie(id)
            return results
        title=results[counter]['title']
        year=str(results[counter]['year'])
        t=f"{title}  {{ Movie Released-{year}}}"
        print(t)
        options=["Yes","No"]
        if sys.platform!="win32":
            menu = TerminalMenu(options)
            menu_entry_index = menu.show()
        else:
            menu_entry_index = SelectionMenu.get_selection(options)
        accept=options[menu_entry_index]
        if accept=="No":
            counter=counter+1

    if accept=="No":
        id=input("Please Enter imdb id")
        id=re.sub("https://www.imdb.com/title/","",id)
        id=re.sub("tt","",id)
        id=re.sub("/","",id)
        results=IMDb().get_movie(id)
        return results
    return results[counter]
def IMDBtoTMDB(args):
  if args.tmdb!="AUTO-DETECT":
      return
  format=""
  movie=Movie()
  tv=TV()
  tmdb = TMDb()
  tmdb.api_key = args.tmdbapi
  if(args.type=="TV"):
       format='tv_results'
  if(args.type=="Movie"):
       format='movie_results'
  tmdb = movie.external(f"{args.imdb}",f'imdb_id')
  if len(tmdb.get(format))!=0:
       args.tmdb=tmdb.get(format)[0].get("id","")


def create_binaries(args):
    print("Setting up Binaries")
    workingdir=os.path.dirname(os.path.abspath(__file__))
    if args.dottorrent==None:
        if which("dottorrent")!=None and len(which('dottorrent'))>0:
            args.dottorrent=which('dottorrent')
        else:
            dottorrent=os.path.join(workingdir,"bin","dottorrent")
            args.dottorrent=dottorrent
    bhdlogger.debug(f"dottorrent: {args.dottorrent}")
    if args.oxipng==None and sys.platform=="linux":
        if which("oxipng")!=None and len(which('oxipng'))>0:
            args.oxipng=which('oxipng')
        else:
            oxipng=os.path.join(workingdir,"bin","oxipng")
            args.oxipng=oxipng

    if args.oxipng==None and sys.platform=="win32":
       if which("oxipng.exe")!=None and len(which('oxipng.exe'))>0:
            args.oxipng=which('oxipng.exe')
       else:
           oxipng=os.path.join(workingdir,"bin","oxipng.exe")
           args.oxipng=oxipng
    bhdlogger.debug(f"oxipng: {args.oxipng}")

    if args.mtn==None and sys.platform=="linux":
        if which("mtn")!=None and len(which('mtn'))>0:
            args.mtn=which('mtn')
        else:
            mtn=os.path.join(workingdir,"bin","mtn")
            args.mtn=mtn
    if args.mtn==None and sys.platform=="win32":
        if which("mtn")!=None and len(which('mtn.exe'))>0:
            args.mtn=which('mtn.exe')
        else:
            mtn=os.path.join(workingdir,"bin","mtn-win32","bin","mtn.exe")
            args.mtn=mtn
    bhdlogger.debug(f"mtn: {args.mtn}")
    if args.wget==None and sys.platform=="linux":
        if  which('wget')!=None and len(which('wget'))>0:
            args.wget=which('wget')
        else:
            bhdlogger.warn("Please Install wget")
            quit()


    if args.wget==None and sys.platform=="win32":
        if which('wget.exe')!=None and len(which('wget.exe'))>0:
            args.wget=which('wget.exe')
        else:
            wget=os.path.join(workingdir,"bin","wget.exe")
            args.wget=wget
    bhdlogger.debug(f"wget: {args.wget}")
    if args.fd==None and sys.platform=="linux":
        if which('fd')!=None and len(which('fd'))>0:
            args.fd=which('fd')
        else:
            fd=os.path.join(workingdir,"bin","fd")
            args.fd=fd
    if args.fd==None and sys.platform=="win32":
        if which('fd.exe')!=None and len(which('fd.exe'))>0:
            args.fd=which('fd')
        else:
            fd=os.path.join(workingdir,"bin","fd.exe")
            args.fd=fd
    bhdlogger.debug(f"fd: {args.fd}")
def autodetect_type(path,args):
    imdb_info = get_imdb_info(path)
    args.imdb="tt"+imdb_info.movieID
    bhdlogger.debug(imdb_info)
    if imdb_info['kind'] == 'tv series':
        return 'TV'
    try:
        html = HTML(html=requests.get("https://www.imdb.com/title/tt{}".format(imdb_info.movieID)).text)
        if 'TV Special' in html.find('.subtext')[0].html:
            return 'TV'
    except:
        pass
    return 'Movie'


def autodetect_media_source(path):

    MEDIA_SOURCES = ['Blu-ray', 'HD-DVD', 'HDTV', 'WEB']
    if re.search("HDTV",path,re.IGNORECASE)!=None:
        return 'HDTV'
    elif re.search("WEB",path,re.IGNORECASE)!=None:
        return 'WEB'
    elif re.search("Blu-ray",path,re.IGNORECASE)!=None or re.search("Bluray",path,re.IGNORECASE)!=None :
        return 'Blu-ray'
    elif re.search("HD-DVD",path,re.IGNORECASE)!=None or re.search("HDDVD",path,re.IGNORECASE)!=None:
        return 'HD-DVD'
    elif re.search("DVD",path,re.IGNORECASE)!=None:
        return 'DVD'
    upstring=f"{os.path.basename(path)}\nWhat is the Source of the Upload?"
    print(upstring)
    if sys.platform!="win32":
            menu = TerminalMenu(MEDIA_SOURCES)
            menu_entry_index = menu.show()
    else:
        menu_entry_index = SelectionMenu.get_selection(MEDIA_SOURCES)
    value=MEDIA_SOURCES[menu_entry_index]
    return value





def autodetect_codec(path):
    if re.search("h.264",path,re.IGNORECASE)!=None and (re.search("blu",path,re.IGNORECASE)!=None or re.search("web",path,re.IGNORECASE)==None ):
        return 'h.264 Remux'
    elif re.search("h.265",path,re.IGNORECASE)!=None and (re.search("blu",path,re.IGNORECASE)!=None or re.search("web",path,re.IGNORECASE)==None):
        return 'x264'
    elif re.search("x265",path,re.IGNORECASE)!=None:
        return 'x265'
    elif re.search("x264",path,re.IGNORECASE)!=None:
        return 'x264'
    elif re.search("VC-1 Remux",path,re.IGNORECASE)!=None:
        return 'VC-1 Remux'
    elif re.search("MPEG2 Remux",path,re.IGNORECASE)!=None:
        return 'MPEG2 Remux'

    upstring=f"{os.path.basename(path)}\nWhat is the codec of the Upload?"
    print(upstring)

    options=["x264","h.264 Remux","x265","h.265 Remux","VC-1 Remux""MPEG2 Remux"]

    if sys.platform!="win32":
            menu = TerminalMenu(options)
            menu_entry_index = menu.show()
    else:
        menu_entry_index = SelectionMenu.get_selection(options)
    value=options[menu_entry_index]
    return value



def preprocessing(path, args):
    print("Detecting Upload INFO")
    assert Path(path).exists()
    if args.type == 'AUTO-DETECT':
        args.type= autodetect_type(path,args)
    if args.imdb == 'AUTO-DETECT':
        args.imdb= "tt"+get_imdb_info(path).movieID
    bhdlogger.debug(f"imdb: {args.imdb}")
    if args.mediasource == 'AUTO-DETECT':
        args.mediasource = autodetect_media_source(path)
    bhdlogger.debug(f"mediasource: {args.mediasource}")




def create_torrent(path,torrent,dottorrent):
    print("Creating Torrent For Upload")
    p = subprocess.run([sys.executable,dottorrent, '-s', '16M', '-p',path, torrent], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    bhdlogger.debug(p.stdout)
    bhdlogger.debug(f"Torrent Size: {os.path.getsize(torrent)}")
    if p.returncode != 0:
        raise RuntimeError("Error creating torrent: {}".format(p.stdout))


def get_mediainfo(path,mdpath):
    print("Getting Mediainfo")
    media_info = MediaInfo.parse(path, output="STRING", full=False)

    media_info=media_info.encode(encoding='utf8')
    media_info=media_info.decode('utf8', 'strict')
    bhdlogger.debug(media_info)
    t=open(mdpath,"w")
    t.write(media_info)



def take_screenshots(path,dir,numscreens,font,mtn,oxipng):
    print("Taking Screenshots")
    media_info = MediaInfo.parse(path)
    for track in media_info.tracks:
        if track.track_type == 'Video':
            interval=float(track.duration)/1000
            interval=math.floor(interval/numscreens)
            bhdlogger.debug(f"ScreenShot Interval: {interval} steps")
            break
    t=subprocess.run([mtn,'-n','-z','-f',font,'-o','.png','-w','0','-P','-s',str(interval),'-I',path,'-O',dir.name],stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #delete largest pic
    bhdlogger.debug(t.stdout)
    bhdlogger.debug(f"File Names Images {os.listdir(dir.name)}")
    max=0
    delete=""
    for filename in os.listdir(dir.name):
       filename=os.path.join(dir.name,filename)
       temp=os.path.getsize(filename)
       if(temp>max):
            max=temp
            delete=filename
    bhdlogger.debug(f"Deleting the thumbnail image: {delete} ")
    os.remove(delete)
    for filename in os.listdir(dir.name):
        filename=os.path.join(dir.name,filename)
        bhdlogger.debug(f"Old Size: {filename} {os.path.getsize(filename)} bytes")
        t=subprocess.run([oxipng,'-o','6','strip safe',filename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        bhdlogger.debug(f"New Size: {filename} {os.path.getsize(filename)}")


def upload_image(dir,args):
    home= os.getcwd()
    url='https://api.imgbb.com/1/upload?key=' + args.imgbb
    text=os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
    textinput= open(text,"w+")
    for filename in os.listdir(dir.name):
         image=dir.name+'/'+filename
         image = {'image': open(image,'rb')}
         upload=requests.post(url=url,files=image)
         upload=upload.json()['data']['url_viewer']
         upload=requests.post(url=upload)
         link = BeautifulSoup(upload.text, 'html.parser')
         link = link.find('input',{'id' :'embed-code-5'})
         link=link.attrs['value']+" "
         textinput.write(link)
    textinput.close()
    textoutput= open(text,"r")
    os.chdir(home)
    return textoutput.read()



def create_upload_form(args,inpath,torrentpath,mediainfopath):
    print("Starting UploadForm Process: ",inpath)
    t=datetime.now().strftime("%m.%d.%Y_%H%M")
    bhdlogger.warn(f"Creating Form {t}")
    if os.path.isdir(inpath):
        single_file=subprocess.run([args.fd,'.',inpath,'--max-results','1','-e','.mkv'],stdout=subprocess.PIPE).stdout.decode("utf-8")
        single_file=single_file.rstrip()
        single_file=f'{single_file}'



    else:
        single_file=inpath



    mediainfo=get_mediainfo(single_file,mediainfopath)


    bhdlogger.debug(f"single file: {single_file}")
    bhdlogger.debug(f"Uploading Path: {inpath}")
    imgdir = tempfile.TemporaryDirectory()
    release_info = Thread(target = take_screenshots, args = (single_file,imgdir,args.numscreens,args.font,args.mtn,args.oxipng))
    release_info.start()
    torrent=Thread(target = create_torrent, args = (inpath,torrentpath,args.dottorrent))
    torrent.start()
    preprocessing(single_file, args)
    IMDBtoTMDB(args)
    torrent.join()
    release_info.join()


    args.title=os.path.basename(single_file)
    form = {'name': get_title(args,single_file),
            'type': get_type(single_file),
            'imdb_id': re.sub("tt","",args.imdb),
            'tmdb_id': args.tmdb,
            'source': args.mediasource,
            'description': upload_image(imgdir,args),
            'category_id':{"Movie":1,"TV":2}.get(args.type),
    	    'pack':args.pack,
    	    'live':args.live,
    	    'anon':args.anon,
            'special':args.special,
            'sd':args.sd,}

    bhdlogger.debug(form)
    return form


def upload_command(args,form,torrent,media):
    print("Uploading to BHD")
    r = upload_form(args,form,torrent,media)
    if r!=None and r.status_code == 200:
        pass
    else:
        raise RuntimeError("Something went wrong while uploading! It's recommended to check BHD to verify that you"
                            "haven't uploaded a malformed or incorrect torrent.")
    t=json.loads(r.text)


    try:
        return t.get("status_message")
    except:
        return None


def upload_form(args, form,torrent,mediainfo):
    files={'file': open(torrent,'rb'),'mediainfo' : open(mediainfo,'rb')}
    try:
        t=requests.post(f"https://beyond-hd.me/api/upload/{args.bhdapi}",
                         data=form,files=files,timeout=120)
    except:
        bhdlogger.info("Upload PostRequest Failed")
        return None
    # soup = BeautifulSoup(t.text, 'html.parser')
    # soup=soup.title
    # bhdlogger.debug(f"Succesful Upload? {soup}")
    return t




def download_torrent(args,BHD_link,path):
    print("Downloading Torrent to client")
    wget=args.wget
    client=args.client
    if client not in ["rtorrent","qbit","deluge","transmission"]:
        name="".join([args.title,".torrent"])
        torrentpath=os.path.join(client,name)
        bhdlogger.info(torrentpath)
        try:
            t=subprocess.run([wget,BHD_link,'-O',torrentpath],stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            bhdlogger.debug(f"Downloading Final Torrent -No Fast Resume Data added :{t.stdout}")
        except:
            bhdlogger.warn("error downloading torrent please get directly from BHD")
    if client=="rtorrent":
        temptor=os.path.join(tempfile.gettempdir(), os.urandom(24).hex()+".torrent")
        t=subprocess.run([wget,BHD_link,'-O',temptor],stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #important line remove private infromation from download link

        t=f"Downloading Temp Torrent:{t.stdout.decode('utf8', 'strict')}"
        bhdlogger.debug(t)
        metainfo=bencode.bread(temptor)
        resumedata = add_fast_resume(metainfo, path)
        bhdlogger.info(f"resume date added?: {bencode.encode(resumedata)!=metainfo}")
        if bencode.encode(resumedata)!=metainfo:
            bencode.bwrite(resumedata,temptor)
        clienturl=re.sub("unix","scgi",args.clienturl)
        server = SCGIServerProxy(clienturl)
        if args.clientcat!=None:
            server.load.start_verbose("",temptor,f"d.directory_base.set={args.media}",f"d.custom1.set={args.clientcat}")
        else:
            server.load.start_verbose("",temptor,f"d.directory_base.set={args.media}")


def add_fast_resume(meta, datapath):
    """ Add fast resume data to a metafile dict.
    """
    # Get list of files
    files = meta["info"].get("files", None)
    single = files is None
    if single:
        if os.path.isdir(datapath):
            datapath = os.path.join(datapath, meta["info"]["name"])
        files = [Bunch(
            path=[os.path.abspath(datapath)],
            length=meta["info"]["length"],
        )]

    # Prepare resume data
    resume = meta.setdefault("libtorrent_resume", {})
    resume["bitfield"] = len(meta["info"]["pieces"]) // 20
    resume["files"] = []
    piece_length = meta["info"]["piece length"]
    offset = 0

    for fileinfo in files:
        # Get the path into the filesystem
        filepath = os.sep.join(fileinfo["path"])
        if not single:
            filepath = os.path.join(datapath, filepath.strip(os.sep))

        # Check file size
        if os.path.getsize(filepath) != fileinfo["length"]:
            raise OSError(errno.EINVAL, "File size mismatch for %r [is %d, expected %d]" % (
                filepath, os.path.getsize(filepath), fileinfo["length"],
            ))

        # Add resume data for this file
        resume["files"].append(dict(
            priority=1,
            mtime=int(os.path.getmtime(filepath)),
            completed=(offset+fileinfo["length"]+piece_length-1) // piece_length
                     - offset // piece_length,
        ))
        offset += fileinfo["length"]

    return meta



if __name__ == '__main__':
    workingdir=os.path.dirname(os.path.abspath(__file__))

    try:
        os.mkdir(os.path.join(workingdir,"Logs"))
    except:
        pass
    #Create Logger

    parser = ArgumentParser()
    parser.add_argument("--media",default=None)
    parser.add_argument("--config",default=None)
    parser.add_argument("--tmdbapi",default=None)
    parser.add_argument("--bhdapi",default=None)
    parser.add_argument("--imgbb",default=None)
    parser.add_argument("--client",default=None)
    parser.add_argument("--clienturl",default=None)
    parser.add_argument("--clientcat",default=None)
    parser.add_argument("--clientuser",default=None)
    parser.add_argument("--clientpass",default=None)
    parser.add_argument("--txtoutput",default=None)
    parser.add_argument("--font",default=None)
    parser.add_argument("--imdb",default="AUTO-DETECT")
    parser.add_argument("--tmdb",default="AUTO-DETECT")
    parser.add_argument("--mediasource",default="AUTO-DETECT")
    parser.add_argument("--type",default="AUTO-DETECT")
    parser.add_argument("--numscreens",default=None)
    parser.add_argument("--oxipng",default=None)
    parser.add_argument("--dottorrent",default=None)
    parser.add_argument("--wget",default=None)
    parser.add_argument("--mtn",default=None)
    parser.add_argument("--fd",default=None)
    parser.add_argument("--batchmode",default=None)
    parser.add_argument("--log",default=None)
    parser.add_argument('--anon', action='store_true')
    parser.add_argument('--pack', action='store_true')
    parser.add_argument('--special', action='store_true')
    parser.add_argument('--sd', action='store_true')
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    bhdlogger = logging.getLogger('BHD')
    myfilter=filter(args)
    bhdlogger.addFilter(myfilter)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    filehandler=logging.FileHandler(os.path.join(workingdir,"Logs","BHDupload.logs"))
    filehandler.setFormatter(formatter)
    bhdlogger.addHandler(filehandler)
    args=create_config(args)
    torrentpath=os.path.join(tempfile.gettempdir(), os.urandom(24).hex()+".torrent")
    mediainfopath=os.path.join(tempfile.gettempdir(), os.urandom(24).hex()+".txt")
    create_binaries(args)
    keepgoing = "Yes"
    #setup batchmode
    if os.path.isdir(args.media) and (args.batchmode==True or  args.batchmode=="True"):
        choices=sorted(os.listdir(args.media))
        if len(choices)==0:
            print("Upload Folder is Empty")
            quit()


    #single upload
    else:
        form=create_upload_form(args,args.media,torrentpath,mediainfopath)

        BHD_link=upload_command(args,form,torrentpath,mediainfopath)
        if BHD_link!=None and re.search("Draft has|info_hash value",BHD_link)==None:
            print(BHD_link)
            download_torrent(args,BHD_link,args.media)
        else:
            bhdlogger.warn("Was Not able to get torrentlink")
        quit()



    #batchmode
    while keepgoing=="Yes" or keepgoing=="yes" or keepgoing=="Y" or keepgoing=="y"  or keepgoing=="YES":
        if sys.platform!="win32":
            menu = TerminalMenu(choices)
            menu_entry_index = menu.show()
        else:
            menu_entry_index = SelectionMenu.get_selection(choices)


        if menu_entry_index>= (len(choices)):
            quit()
        try:
            path=choices[int(menu_entry_index)]

        except:
            bhdlogger.warn("Please Enter a Valid Value")
            continue
        path=os.path.join(args.media,path)
        print("\n")
        form=create_upload_form(args,path,torrentpath,mediainfopath)
        BHD_link=upload_command(args,form,torrentpath,mediainfopath)
        if BHD_link!=None and re.search("Draft has|info_hash value",BHD_link)==None:
            print(BHD_link)
            download_torrent(args,BHD_link,path)
        else:
            bhdlogger.warn("Was Not able to get torrentlink")
            print(BHD_link)
        clear_movie(args)
        keepgoing=input("Upload Another File: ")
