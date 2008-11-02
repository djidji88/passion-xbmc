# -*- coding: cp1252 -*-
from string import *
import sys#, os.path
import re
from time import gmtime, strptime, strftime
import os
import ftplib
import ConfigParser
import xbmcgui, xbmc
import traceback
import time
import urllib2
import socket
import time
import shutil

try:
    del sys.modules['BeautifulSoup']
except:
    pass 
from BeautifulSoup import BeautifulStoneSoup,Tag, NavigableString  #librairie de traitement XML
import htmlentitydefs


try: Emulating = xbmcgui.Emulating
except: Emulating = False


############################################################################
# Get actioncodes from keymap.xml
############################################################################

ACTION_MOVE_LEFT                 = 1
ACTION_MOVE_RIGHT                = 2
ACTION_MOVE_UP                   = 3
ACTION_MOVE_DOWN                 = 4
ACTION_PAGE_UP                   = 5
ACTION_PAGE_DOWN                 = 6
ACTION_SELECT_ITEM               = 7
ACTION_HIGHLIGHT_ITEM            = 8
ACTION_PARENT_DIR                = 9
ACTION_PREVIOUS_MENU             = 10
ACTION_SHOW_INFO                 = 11

ACTION_PAUSE                     = 12
ACTION_STOP                      = 13
ACTION_NEXT_ITEM                 = 14
ACTION_PREV_ITEM                 = 15

#############################################################################
# autoscaling values
#############################################################################

HDTV_1080i      = 0 #(1920x1080, 16:9, pixels are 1:1)
HDTV_720p       = 1 #(1280x720, 16:9, pixels are 1:1)
HDTV_480p_4x3   = 2 #(720x480, 4:3, pixels are 4320:4739)
HDTV_480p_16x9  = 3 #(720x480, 16:9, pixels are 5760:4739)
NTSC_4x3        = 4 #(720x480, 4:3, pixels are 4320:4739)
NTSC_16x9       = 5 #(720x480, 16:9, pixels are 5760:4739)
PAL_4x3         = 6 #(720x576, 4:3, pixels are 128:117)
PAL_16x9        = 7 #(720x576, 16:9, pixels are 512:351)
PAL60_4x3       = 8 #(720x480, 4:3, pixels are 4320:4739)
PAL60_16x9      = 9 #(720x480, 16:9, pixels are 5760:4739)

############################################################################
class cancelRequest(Exception):
    """
    Exception, merci a Alexsolex 
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class rssReader:
    """
    
    Class responsable de la recuperation du flux RSS et de l'extraction des infos RSS
    
    """
    def __init__(self,rssUrl):
        """
        Init de rssReader
        """
        self.rssURL = rssUrl
        self.rssPage = self.get_rss_page(self.rssURL)

    def get_rss_page(self,rssUrl):
        """
        T�l�charge et renvoi la page RSS
        """
        try:
            #request = urllib2.Request("http://passion-xbmc.org/service-importation/?action=.xml;type=rss2;limit=1")
            request = urllib2.Request(rssUrl)
            request.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9) Gecko/2008052906 Firefox/3.0')
            request.add_header('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
            request.add_header('Accept-Language','fr,fr-fr;q=0.8,en-us;q=0.5,en;q=0.3')
            request.add_header('Accept-Charset','ISO-8859-1,utf-8;q=0.7,*;q=0.7')
#            request.add_header('Keep-Alive','300')
#            request.add_header('Connection','keep-alive')
            response = urllib2.urlopen(request)
            the_page = response.read()
        except Exception, e:
            print("Exception get_rss_page")
            print(e)
            the_page = ""
        # renvo a page the RSS
        return the_page

    def unescape(self,text):
        """
        credit : Fredrik Lundh
        trouve : http://effbot.org/zone/re-sub.htm#unescape-html"""
        def fixup(m):# m est un objet match
            text = m.group(0)#on r�cup�re le texte correspondant au match
            if text[:2] == "&#":# dans le cas o� le match ressemble � &#
                # character reference
                try:
                    if text[:3] == "&#x":#si plus pr�cis�ment le texte ressemble � &#38;#x (donc notation hexa)
                        return unichr(int(text[3:-1], 16))#alors on retourne le unicode du caract�re en base 16 ( hexa)
                    else:
                        return unichr(int(text[2:-1]))#sinon on retourne le unicode du caract�re en base 10 (donc notation d�cimale)
                except ValueError: #si le caract�re n'est pas unicode, on le passe simplement
                    pass
            else: #sinon c'est un caract�re nomm� (htmlentities)
                # named entity
                try:
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])#on renvoi le unicode de la correspondance pour le caract�re nomm�
                except KeyError:
                    pass #si le caract�re nomm� n'est pas d�fini dans les htmlentities alors on passe
            return text # leave as is #dans tous les autres cas, le match n'�tait pas un caract�re d'�chapement html on le retourne tel quel
     
        #par un texte issu de la fonction fixup
        return re.sub("&#?\w+;", fixup,   text)    
    
    def GetRssInfo(self):
        """
        Recupere les information du FLux RSS de passion XBMC
        Merci a Alexsolex
        """
        soup = BeautifulStoneSoup(self.rssPage)
        maintitle = soup.find("description").string.encode("cp1252", 'xmlcharrefreplace').replace("&#224;","�").replace("&#234;","�").replace("&#232;","�").replace("&#233;","�").replace("&#160;","  ***  ") # Note: &#160;=&
        items = ""
        for item in soup.findAll("item"): #boucle si plusieurs items dans le rss
            # Titre de l'Item 
            itemsTitle = item.find("title").string.encode("cp1252", 'xmlcharrefreplace').replace("&#224;","�").replace("&#234;","�").replace("&#232;","�").replace("&#233;","�").replace("&#160;","  ***  ") # Note: &#160;=&
            items = items + itemsTitle + ":  "
            # la ligne suivante supprime toutes les balises au sein de l'info "description"
            clean_desc = re.sub(r"<.*?>", r"", "".join(item.find("description").contents))
            # on imprime le texte sans les caracteres d'echappements html
            # Description de l'item 
            itemDesc = self.unescape(clean_desc).strip().encode("cp1252", 'xmlcharrefreplace').replace("&#224;","�").replace("&#234;","�").replace("&#232;","�").replace("&#233;","�").replace("&#160;","  ***  ") # Note: &#160;=&
            itemDesc = itemDesc.replace("-Plus d'info","").replace("-Voir la suite...","") # on supprime "-Plus d'info" et "-Voir la suite..."
            #TODO: supprimer balise link plutot que remplacer les chaines -Voir la suite...
            # Concatenation
            items = items + " " + itemDesc
        return maintitle,items




class scriptextracter:
    """
    
    Extracteur de script, dezip ou derar une archive et l'efface

    """
    def zipfolder (self):
        import zipfile
        self.zfile = zipfile.ZipFile(self.archive, 'r')
        for i in self.zfile.namelist():  ## On parcourt l'ensemble des fichiers de l'archive
            print i
            if i.endswith('/'):
                dossier = self.pathdst + os.sep + i
                try:
                    os.makedirs(dossier)
                except Exception, e:
                    print "Erreur creation dossier de l'archive = ",e
            else:
                print "File Case"

        # On ferme l'archive
        self.zfile.close()

    def  extract(self,archive,TargetDir):
        self.pathdst = TargetDir
        self.archive = archive
        print "self.pathdst = %s"%self.pathdst
        print "self.archive = %s"%self.archive
        
        if archive.endswith('zip'):
            self.zipfolder() #generation des dossiers dans le cas d'un zip
        #extraction de l'archive
        xbmc.executebuiltin('XBMC.Extract(%s,%s)'%(self.archive,self.pathdst) )

class ftpDownloadCtrl:
    """

    Controleur de download via FTP
    Cette classe gere les download via FTP de fichiers et repertoire

    """
    def __init__(self,host,user,password,remotedirList,localdirList,typeList):
        """
        Fonction d'init de la classe ftpDownloadCtrl
        Initialise toutes les variables et lance la connection au serveur FTP
        """

        #Initialise les attributs de la classe ftpDownloadCtrl avec les parametres donnes au constructeur
        self.host                   = host
        self.user                   = user
        self.password               = password
        self.remotedirList          = remotedirList
        self.localdirList           = localdirList
        self.downloadTypeList       = typeList
#        self.remoteplugindirlist    = remoteplugindirlist
#        self.localplugindirlist     = localplugindirlist   
        
        self.connected          = False # status de la connection (inutile pour le moment)
        self.curLocalDirRoot    = ""
        self.curRemoteDirRoot   = ""
        #self.idcancel           = False
        print "self.host = ",self.host
        print "self.user= ",self.user
        #print "self.password = ",self.password

        #Connection au serveur FTP
        self.openConnection()

    def openConnection(self):
        """
        Ouvre la connexion FTP
        """
        #Connection au serveur FTP
        try:
            self.ftp = ftplib.FTP(self.host,self.user,self.password) # on se connecte
            #self.ftp.cwd(self.remotedirList)# va au chemin specifie
            
            # DEBUG: Seulement pour le dev
            #self.ftp.set_debuglevel(2)
            
            self.connected = True
            #self.ftp.sendcmd('PASV')

        except Exception, e:
            print "ftpDownloadCtrl: __init__: Exception durant la connection FTP",e
            print "ftpDownloadCtrl: Impossible de se connecter au serveur FTP: %s"%self.host
            print ("error/MainWindow __init__: " + str(sys.exc_info()[0]))
            traceback.print_exc()
            
    def closeConnection(self):
        """
        Ferme la connexion FTP
        """
        #on se deconnecte du serveur pour etre plus propre
        self.ftp.quit()

    def getDirList(self,remotedir):
        """
        Retourne la liste des elements d'un repertoire sur le serveur
        """
        curDirList = []
        
        # Recuperation de la liste
        try:
            #self.ftp.sendcmd('PASV')
            curDirList = self.ftp.nlst(remotedir)
        except Exception, e:
            print "getDirList: __init__: Exception durant la recuperation de la liste des fichiers du repertoire: %s"%remotedir,e
            print ("error/MainWindow __init__: " + str(sys.exc_info()[0]))
            traceback.print_exc()
        
        # Tri de la liste et renvoi
        curDirList.sort(key=str.lower)
        return curDirList

    def isDir(self,pathsrc):
        """
        Verifie si le chemin sur le serveur correspond a un repertoire
        """
        isDir = True
        # Verifie se on telecharge un repertoire ou d'un fichier
        try:
            self.ftp.cwd(pathsrc) # c'est cette commande qui genere l'exception dans le cas d'un fichier
            # Pas d'excpetion => il s'agit d'un dossier
            print "isDir: %s EST un DOSSIER"%pathsrc
        except Exception, e:
            print "isDir: %s EST un FICHIER"%pathsrc
            isDir = False
        return isDir

    def isAlreadyDownloaded(self,pathsrc,rootdirsrc,typeIndex):
        """
        Verifie si un repertoire local correspondanf au rootdirsrc existe dans dans pathsrc
        Pour le moment on verifie la meme chose pour un fichier ais cela ne couvre pas encore le cas 
        d'un archive extraite localement
        retourne True si c'est le cas, False sinon
        """
        isDownloaded     = False
        curLocalDirRoot  = self.localdirList[typeIndex]
        curRemoteDirRoot = rootdirsrc
        localAbsDirPath  = None
        
        #TODO: couvrir le cas d'une archive?
        
        # Cree le chemin du repertorie local
        # Extrait le chemin relatif: soustrait au chemin remote le chemin de base: par exemple on veut retirer du chemin; /.passionxbmc/Themes
        remoteRelDirPath = pathsrc.replace(curRemoteDirRoot,'')

        # On remplace dans le chemin sur le serveur FTP les '/' par le separateur de l'OS sur lequel on est
        localRelDirPath = remoteRelDirPath.replace('/',os.sep)

        # Cree le chemin local (ou on va sauver)
        localAbsDirPath = os.path.join(curLocalDirRoot, localRelDirPath)
    
        # Verifie se on telecharge un repertoire ou d'un fichier
        if self.isDir(pathsrc):
            # cas d'un repertoire
            isDownloaded = os.path.isdir(localAbsDirPath)
        else:
            # Cas d'un fichier
            isDownloaded = os.path.exists(localAbsDirPath)
        return isDownloaded,localAbsDirPath

    def download(self,pathsrc,rootdirsrc,typeIndex,progressbar_cb=None,dialogProgressWin=None):
        """
        Telecharge les elements a un chemin specifie (repertoires, sous repertoires et fichiers)
        a dans un repertorie local dependant du type de telechargement (theme, scraper, script ...)
        pathsrc     : chemin sur le serveur de l'element a telecharger
        rootdirsrc  : Repertoire root sur le server (correspondant a un type de download) - Exemple : "/.passionxbmc/Scraper/" pour les scrapers
        typeIndex   : Index correspondant au type de telechargement, permet notamment de definir le repertorie local de telechargement
        Renvoi le status du download:
            - (-1) pour telechargement annule
            - (1)  pour telechargement OK
        """
            
        self.curLocalDirRoot  = self.localdirList[typeIndex]
        self.curRemoteDirRoot = rootdirsrc

#        try:
#            if (progressbar_cb != None) and (dialogProgressWin != None):
#                percent = 0
#                #print "=================================="
#                #print
#                #print "Pourcentage telecharger: %d"%percent
#                #print
#                #print "=================================="
#                # Initialisation de la barre de progression (via callback)
#                progressbar_cb(percent,dialogProgressWin)
#        except Exception, e:
#            print("download - Exception ProgressBar UI callback for download")
#            print(e)
#            print progressbar_cb

        # Appel de la fonction privee en charge du download - on passe en parametre l'index correspondant au type
        status = self._download(pathsrc,progressbar_cb,dialogProgressWin,0,1)
        return  status # retour du status du download recupere


    def _download(self, pathsrc,progressbar_cb=None,dialogProgressWin=None,curPercent=0,coeff=1):
        """
        Fonction privee (ne pouvant etre appelee que par la classe ftpDownloadCtrl elle meme)
        Telecharge un element sur le server FTP
        Renvoi le status du download:
            - (-1) pour telechargement annule
            - (1)  pour telechargement OK
        """
        result = 1 # 1 pour telechargement OK
        # Liste le repertoire
        curDirList     = self.ftp.nlst(pathsrc) #TODO: ajouter try/except
        curDirListSize = len(curDirList) # Defini le nombre d'elements a telecharger correspondant a 100% - pour le moment on ne gere que ce niveau de granularite pour la progressbar
        # On teste le nombre d'element dans la liste : si 0 -> rep vide
        # !!PB!!: la commande NLST dans le cas ou le path est un fichier retourne les details sur le fichier => donc liste non vide
        # donc pour le moment on essaira de telecharger en tant que fichier un rep vide (apres avoir fait un _downloaddossier)
        # mais ca ira ds une exception donc OK mais pas propre
        #TODO: a ameliorer donc
        #print "_download: Repertoire NON vide - demarrage boucle"
        for i in curDirList:
            if dialogProgressWin.iscanceled():
                print "Telechargement annul� par l'utilisateur"
                # Sortie de la boucle via return
                result = -1 # -1 pour telechargement annule
                break
            else:
                # Calcule le pourcentage avant download
                #TODO: verifier que la formule pour le pourcentage est OK (la ca ette fait un peu trop rapidement) 
                #percent = min(curPercent + int((float(curDirList.index(i)+1)*100)/(curDirListSize * coeff)),100)
                percentBefore = min(curPercent + int((float(curDirList.index(i)+0)*100)/(curDirListSize * coeff)),100)
                #print "=================================="
                #print
                #print "Pourcentage t�l�charg�: %d"%percent
                #print
                #print "=================================="
                # Verifie si le chemin correspond a un repertoire
                
                try :

                    # Mise a jour de la barre de progression (via callback)
                    # percent est le poucentage du FICHIER telecharger et non le pourcentage total
                    dialogProgressWin.update(0,"T�l�chargement Total: %d%%"%percentBefore, "%s"%i)
                except Exception, e:
                    print("downloadVideo - Exception calling UI callback for download")
                    print(e)
                    print progressbar_cb
                    
                if self.isDir(i):
                    # pathsrc est un repertoire
                    # Telechargement du dossier
                    self._downloaddossier(i,dialogProgressWin=dialogProgressWin,curPercent=percentBefore,coeff=coeff*curDirListSize)
                    #percent = int((float(curDirList.index(i)+1)*100)/(curDirListSize * coeff))
                    
                else:
                    # pathsrc est un fichier
                    # Telechargement du fichier
                    self._downloadfichier(i,dialogProgressWin=dialogProgressWin,curPercent=percentBefore,coeff=coeff*curDirListSize)
                    
                percentAfter = min(curPercent + int((float(curDirList.index(i)+1)*100)/(curDirListSize * coeff)),100)
                try :

                    #Mise a jour de la barre de progression (via callback)
                    #TODO: Resoudre le pb que la ligbe ci-dessous est invible (trop rapide)
                    dialogProgressWin.update(100,"T�l�chargement Total: %d%%"%percentAfter, "%s"%i)
                    #time.sleep(1)
                except Exception, e:
                    print("downloadVideo - Exception calling UI callback for download")
                    print(e)
                    print progressbar_cb
        

        # Calcul pourcentage final
        percent = min(curPercent + int(100/(coeff)),100)
        try :

            #Mise a jour de la barre de progression (via callback)
            dialogProgressWin.update(100,"T�l�chargement Total: %d%%"%percent, "%s"%i)
            #time.sleep(3)
        except Exception, e:
            print("downloadVideo - Exception calling UI callback for download")
            print(e)
            print progressbar_cb
            
        # verifie si on a annule le telechargement
        if dialogProgressWin.iscanceled():
            print "Telechargement annul� par l'utilisateur"
            # Sortie de la boucle via return
            result = -1 # -1 pour telechargement annule

        return result 

    def _downloaddossier(self, dirsrc,progressbar_cb=None,dialogProgressWin=None,curPercent=0,coeff=1):
        """
        Fonction privee (ne pouvant etre appelee que par la classe ftpDownloadCtrl elle meme)
        Telecharge un repertoire sur le server FTP
        Note: fait un appel RECURSIF sur _download
        """
        emptydir = False
        
        try:
            dirContent = self.ftp.nlst(dirsrc)
            print dirContent
        except Exception, e:
            # Repertoire non vide -> il faut telecharger les elementss de ce repertoire
            emptydir = True

        # Cree le chemin du repertorie local
        # Extrait le chemin relatif: soustrait au chemin remote le chemin de base: par exemple on veut retirer du chemin; /.passionxbmc/Themes
        remoteRelDirPath = dirsrc.replace(self.curRemoteDirRoot,'')

        # On remplace dans le chemin sur le serveur FTP les '/' par le separateur de l'OS sur lequel on est
        localRelDirPath = remoteRelDirPath.replace('/',os.sep)

        # Cree le chemin local (ou on va sauver)
        localAbsDirPath = os.path.join(self.curLocalDirRoot, localRelDirPath)

        try:
            os.makedirs(localAbsDirPath)
        except Exception, e:
            print "_downloaddossier: Exception - Impossible de creer le dossier: %s"%localAbsDirPath
            print e
        if (emptydir == True):
            #print "_downloaddossier: Repertoire %s VIDE"%dirsrc
            pass
        else:
            # Repertoire non vide - lancement du download (!!!APPEL RECURSIF!!!)
            self._download(dirsrc,dialogProgressWin=dialogProgressWin,curPercent=curPercent,coeff=coeff)
            
    def _downloadfichier(self, filesrc,dialogProgressWin=None,curPercent=0,coeff=1):
        """
        Fonction privee (ne pouvant etre appelee que par la classe ftpDownloadCtrl elle meme)
        Telecharge un fichier sur le server FTP
        """
        # Recupere la taille du fichier
        remoteFileSize = 1
        block_size = 4096
        #block_size = 2048
        # Recuperation de la taille du fichier
        try:
            self.ftp.sendcmd('TYPE I')
            remoteFileSize = int(self.ftp.size(filesrc))
            if remoteFileSize <= 0:
                # Dans le cas ou ub fichier n'a pas une taille valide ou corrompue
                remoteFileSize = 1
        except Exception, e:
            print "_downloadfichier: Excpetion lors la recuperation de la taille du fichier: %s"%filesrc
            print e
            traceback.print_exc(file = sys.stdout)
        
        # Cree le chemin du repertorie local
        # Extraction du chemin relatif: soustrait au chemin remote le chemin de base: par exemple on veut retirer du chemin; /.passionxbmc/Themes
        remoteRelFilePath = filesrc.replace(self.curRemoteDirRoot,'')

        # On remplace dans le chemin sur le serveur FTP les '/' par le separateur de l'OS sur lequel on est
        localRelFilePath = remoteRelFilePath.replace('/',os.sep)

        # Creation du chemin local (ou on va sauver)
        localAbsFilePath = xbmc.translatePath(os.path.join(self.curLocalDirRoot, localRelFilePath))
        #localFileName = os.path.basename(localAbsFilePath)

        localFile = open(localAbsFilePath, "wb")
        try:
            # Creation de la fonction callback appele a chaque block_size telecharge
            ftpCB = FtpCallback(remoteFileSize, localFile,filesrc,dialogProgressWin,curPercent,coeff*remoteFileSize)
            
            # Telecahrgement (on passe la CB en parametre)
            # Note on utilise un implemenation locale et non celle de ftplib qui ne supporte pas l'interuption d'un telechargement
            self.retrbinary('RETR ' + filesrc, ftpCB, block_size)
        except Exception, e:
            print "_downloadfichier: Exception lors la recuperation du fichier: %s"%filesrc
            print e
            traceback.print_exc(file = sys.stdout)
        # On ferme le fichier
        localFile.close()
        
    def retrbinary(self, cmd, callback, blocksize=8192,rest=None):
        """
        Cette version de retrbinary permet d'interompte un telechargement en cours alors que la version de ftplib ne le permet pas
        Inspir�e du code dispo a http://www.archivum.info/python-bugs-list@python.org/2007-03/msg00465.html
        """
        self.ftp.voidcmd('TYPE I')
        conn = self.ftp.transfercmd(cmd, rest)
        fp = conn.makefile('rb')
        while 1:
            data = fp.read(blocksize)   
            if not data:
                break
            try:
                callback(data)
            except cancelRequest:
                traceback.print_exc(file = sys.stdout)
                print "retrbinary: Download ARRETE par l'utilisateur"
                break
        fp.close()
        conn.close()
        return self.ftp.voidresp()

        
        
class FtpCallback(object):
    """
    Inspired from source Justin Ezequiel (Thanks)
    http://coding.derkeiler.com/pdf/Archive/Python/comp.lang.python/2006-09/msg02008.pdf
    """
    def __init__(self, filesize, localfile, filesrc, dp=None, curPercent=0, coeff=1):
        self.filesize   = filesize
        self.localfile  = localfile
        self.srcName    = filesrc
        self.received   = 0
        self.curPercent = curPercent # Pourcentage total telecharger (et non du fichier en cours)
        self.coeff      = coeff
        self.dp         = dp
#        print filesize
#        print "FtpCallback"
#        print self.filesize
#        print  self.localfile
#        print self.received
#        print self.curPercent
#        print self.coeff
#        print self.dp

        
    def __call__(self, data):
        if self.dp != None:
            if self.dp.iscanceled(): 
                print "FtpCallback: DOWNLOAD CANCELLED" # need to get this part working
                #dp.close() #-> will be close in calling function
                raise cancelRequest,"User pressed CANCEL button"
        self.localfile.write(data)
        self.received += len(data)
        try:
            percent = min((self.received*100)/self.filesize, 100)
#            print "FtpCallback - percent = "
#            print percent
            if self.dp != None:
                self.dp.update(percent,"T�l�chargement Total: %d%%"%self.curPercent, "%s"%self.srcName)
        except Exception, e:        
            print("FtpCallback - Exception during percent computing AND update")
            print(e)
            percent = 100
            traceback.print_exc(file = sys.stdout)
            if self.dp != None:
                #TODO: garder le titre principal
                self.dp.update(percent,"T�l�chargement Total: %d%%"%self.curPercent, "%s"%(self.srcName))

class userDataXML:
    """
    Cette classe represente le fichier sources.xml dans user data
    """
    def __init__(self,filesrc,filedest=None):
        self.newEntry = False
        self.filesrc  = filesrc
        self.filedest = filedest
        self.soup     =  BeautifulStoneSoup(open(filesrc).read())
        
        
    def addPluginEntry(self,plugintype,pluginNameStr,pluginPathStr):        
        if plugintype == "Plugins Musique":
            typeTag  = self.soup.find("music")
            
        elif plugintype == "Plugins Images":
            typeTag  = self.soup.find("pictures")
            
        elif plugintype == "Plugins Programmes":
            typeTag  = self.soup.find("programs")
            
        elif plugintype == "Plugins Vid�os":
            typeTag  = self.soup.find("video")
            
        sourceTag = Tag(self.soup, "source")
        typeTag.insert(0, sourceTag)
        
        nameTag = Tag(self.soup, "name")
        sourceTag.insert(0, nameTag)
        textName = NavigableString(pluginNameStr)
        nameTag.insert(0, textName)
        
        pathTag = Tag(self.soup, "path")
        sourceTag.insert(1, pathTag)
        pathText = NavigableString(pluginPathStr)
        pathTag.insert(0, pathText)
    
        print "Plugin entry %s added"%pluginNameStr
        self.newEntry = True
    def commit(self):
        """
        Sauvegarde les modification dans self.filedest
        retourne True si la sauvegarde s'est bine passee False autrement
        """
        # sauvegarde nouveau fichier
        result = False
        if self.newEntry == True:
            print "userDataXML: sauvegarde du fichier modifi� %s"%self.filedest
            try:
                newFile = open(self.filedest, 'w+')
                newFile.write(self.soup.prettify())
                newFile.close()
                result = True
            except Exception, e:        
                print("userDataXML - Exception durant la creation de %s"%self.filedest)
                print(e)
                percent = 100
                traceback.print_exc(file = sys.stdout)
                result = False
        else:
            print "userDataXML: aucun changement de %s"%self.filesrc
            result = False
        return result


class directorySpy:
    """
    Permet d'observer l'ajout suppressuin des elements d'un repertoire
    """
    def __init__(self,dirpath):
        """
        Capture le contenu d'un repertoire a l'init
        On s'en servira comme reference dans le future pour observer les modifications dans ce repertoire
        """
        self.dirPath            = dirpath
        self.dirContentInitList = []
        if os.path.isdir(dirpath):
            # On capture le contenu du repertoire et on le sauve
            self.dirContentInitList = os.listdir(dirpath)
        else:
            print "directorySpy - __init__: %s n'est pas un repertoire"%self.dirPath
            #TODO: Lever un exception
        print "directorySpy - __init__: Liste des nouveaux elements du repertoire %s a l'instanciation"%self.dirPath
        print self.dirContentInitList
        
    def getNewItemList(self):
        # On capture le contenu courant du repertoire
        dirContentCurrentList = os.listdir(self.dirPath)
        try:
            newItemList = list(set(dirContentCurrentList).difference(set(self.dirContentInitList)))
        except Exception, e: 
            print "directorySpy - getNewItemList: Exception durant la comparaison du repertoires %s"%self.dirPath
            print e
            traceback.print_exc(file = sys.stdout)
            newItemList = []
        #print "directorySpy - getNewItemList: Liste des nouveaux elements du repertoire %s"%self.dirPath
        #print newItemList
        return newItemList


class MainWindow(xbmcgui.Window):
    """

    Interface graphique

    """
    def __init__(self):
        """
        Initialisation de l'interface
        """
        if Emulating: xbmcgui.Window.__init__(self)
        if not Emulating:
            self.setCoordinateResolution(PAL_4x3) # Set coordinate resolution to PAL 4:3

        #TODO: TOUTES ces varibales devraient etre passees en parametre du constructeur de la classe (__init__ si tu preferes)
        # On ne devraient pas utiliser de variables globale ou rarement en prog objet

        self.host               = host
        self.user               = user
        self.rssfeed            = rssfeed
        self.password           = password
        self.remotedirList      = remoteDirLst
        self.localdirList       = localDirLst
        self.downloadTypeList   = downloadTypeLst
        
        self.racineDisplayList  = racineDisplayLst
        self.pluginDisplayList  = pluginDisplayLst
        self.pluginsDirSpyList  = []
        #self.pluginsExitList    = []
         
        self.curDirList         = []
        self.connected          = False # status de la connection (inutile pour le moment)
        self.index              = ""
        self.scraperDir         = scraperDir
        self.type               = "racine"
        self.USRPath            = USRPath
        self.rightstest         = ""
        self.scriptDir          = scriptDir
        self.extracter          = scriptextracter() # On cree un instance d'extracter
        self.CacheDir           = CACHEDIR
        self.userDataDir        = userdatadir # userdata directory
        self.targetDir          = ""
        self.delCache           = ""
        self.scrollingSizeMax   = 480
        self.RssOk              = False

        # Display Loading Window while we are loading the information from the website
        dialogUI = xbmcgui.DialogProgress()
        dialogUI.create("Installeur Passion XBMC", "Creation de l'interface Graphique", "Veuillez patienter...")

        # Verifie si les repertoires cache et imagedir existent et les cree s'il n'existent pas encore
        self.verifrep(CACHEDIR)
        self.verifrep(IMAGEDIR)
        self.verifrep(pluginProgDir)

        #TODO: A nettoyer, ton PMIIIDir n'est pas defini pour XBOX sans le test si dessous
        if self.USRPath == True:
            self.PMIIIDir = PMIIIDir


        # Background image
        self.addControl(xbmcgui.ControlImage(0,0,720,576, os.path.join(IMAGEDIR,"background.png")))

        # Set List border image
        self.listborder = xbmcgui.ControlImage(19,120,681,446, os.path.join(IMAGEDIR, "list-border.png"))
        self.addControl(self.listborder)
        self.listborder.setVisible(True)

        # Set List background image
        self.listbackground = xbmcgui.ControlImage(20, 163, 679, 402, os.path.join(IMAGEDIR, "list-white.png"))
        self.addControl(self.listbackground)
        self.listbackground.setVisible(True)

        # Set List hearder image
        # print ("Get Logo image from : " + os.path.join(IMAGEDIR,"logo.gif"))
        self.header = xbmcgui.ControlImage(20,121,679,41, os.path.join(IMAGEDIR, "list-header.png"))
        self.addControl(self.header)
        self.header.setVisible(True)

        # Title of the current pages
        self.strMainTitle = xbmcgui.ControlLabel(35, 130, 200, 40, "S�lection", 'special13')
        self.addControl(self.strMainTitle)

        # item Control List
        self.list = xbmcgui.ControlList(22, 166, 674 , 420,'font14','0xFF000000', buttonTexture = os.path.join(IMAGEDIR,"list-background.png"),buttonFocusTexture = os.path.join(IMAGEDIR,"list-focus.png"), imageWidth=40, imageHeight=32, itemTextXOffset=0, itemHeight=55)
        self.addControl(self.list)

        # Version and author(s):
        self.strVersion = xbmcgui.ControlLabel(621, 69, 350, 30, version, 'font10','0xFF000000', alignment=1)
        self.addControl(self.strVersion)

        # Recupeartion du Flux RSS
        try:
            # Cree une instance de rssReader recuperant ainsi le flux/page RSS
            self.passionRssReader = rssReader(self.rssfeed)
            
            # Extraction des infos du la page RSS
            maintitle,title = self.passionRssReader.GetRssInfo()
            self.RssOk = True

        except Exception, e:
            print "Window::__init__: Exception durant la recuperation du Flux RSS",e
            
            # Message a l'utilisateur
            dialogRssError = xbmcgui.Dialog()
            dialogRssError.ok("Erreur", "Impossible de recuperer le flux RSS")
            print ("error/MainWindow __init__: " + str(sys.exc_info()[0]))
            traceback.print_exc()

        if (self.RssOk == True):
            # Scrolling message
            self.scrollingText = xbmcgui.ControlFadeLabel(20, 87, 680, 30, 'font12', '0xFFFFFFFF')
            self.addControl(self.scrollingText)
            scrollStripTextSize = len(title)

            # Afin d'avoir un message assez long pour defiler, on va ajouter des espaces afin d'atteindre la taille max de self.scrollingSizeMax
            scrollingLabel = title.rjust(self.scrollingSizeMax)
            scrollingLabelSize = len(scrollingLabel)
            self.scrollingText.addLabel(scrollingLabel)
            #self.scrollingText.setVisible(False)

        
        # Connection au serveur FTP
        try:
            
            self.passionFTPCtrl = ftpDownloadCtrl(self.host,self.user,self.password,self.remotedirList,self.localdirList,self.downloadTypeList)
            self.connected = True

            # Recuperation de la liste des elements
            self.updateList()

        except Exception, e:
            print "Window::__init__: Exception durant la connection FTP",e
            print "Impossible de se connecter au serveur FTP: %s"%self.host
            dialogError = xbmcgui.Dialog()
            dialogError.ok("Erreur", "Exception durant l'initialisation")
            print ("error/MainWindow __init__: " + str(sys.exc_info()[0]))
            traceback.print_exc()

        # Close the Loading Window
        dialogUI.close()

        # Capturons le contenu des sous-repertoires plugins
        for type in self.downloadTypeList:
            if type.find("Plugins") != -1:
                #self.pluginsInitList.append(os.listdir(self.localdirList[self.downloadTypeList.index(type)]))
                self.pluginsDirSpyList.append(directorySpy(self.localdirList[self.downloadTypeList.index(type)]))
            else:
                self.pluginsDirSpyList.append(None)
        print "self.pluginsDirSpyList:"
        print self.pluginsDirSpyList

    def onAction(self, action):
        """
        Remonte l'arborescence et quitte le script
        """
        try:
            if action == ACTION_PREVIOUS_MENU:
                
                # Sortie du script
                #print('action recieved: previous')

                # On se deconnecte du serveur pour etre plus propre
                self.passionFTPCtrl.closeConnection()

                # On efface le repertoire cache
                self.deleteDir(CACHEDIR)


                # Verifions si des plugins on ete ajoutes

                # Capturons le contenu des sous-repertoires plugins a la sortie du script
                xmlConfFile = userDataXML(os.path.join(self.userDataDir,"sources.xml"),os.path.join(self.userDataDir,"sourcesNew.xml"))
                for type in self.downloadTypeList:
                    if type.find("Plugins") != -1:
                        #self.pluginsExitList.append(os.listdir(self.localdirList[self.downloadTypeList.index(type)]))
                        
                        # Verifions si on a de nouveau elements:
                        newPluginList = None
                        try:
                            #newPluginList = list(set(self.pluginsExitList[self.downloadTypeList.index(type)]).difference(set(self.pluginsInitList[self.downloadTypeList.index(type)])))
                            newPluginList = self.pluginsDirSpyList[self.downloadTypeList.index(type)].getNewItemList()
                        except Exception, e: 
                            print "deleteDir: Exception durant la comparaison des repertoires plugin avant et apres installation"
                            print e
                            traceback.print_exc(file = sys.stdout)
                        if len(newPluginList) > 0:
                            for newPluginName in newPluginList:
                                print "newPluginName:"
                                print newPluginName
                                # Creation du chemin qui sera ajoute au XML, par ex : "plugin://video/Google video/"
                                # TODO: extraire des chemins local des plugins les strings, 'music', 'video' ... et n'avoir qu'une implementation 
                                if type == "Plugins Musique":
                                    categorieStr = "music"
                                    
                                elif type == "Plugins Images":
                                    categorieStr = "pictures"
                                    
                                elif type == "Plugins Programmes":
                                    categorieStr = "programs"
                                    
                                elif type == "Plugins Vid�os":
                                    categorieStr = "video"
                                newPluginPath = "plugin://" + categorieStr + "/" + newPluginName + "/"
                                
                                # Mise a jour de sources.xml
                                print "adding new plugin entry: %s"%newPluginName
                                xmlConfFile.addPluginEntry(type,newPluginName,newPluginPath)
                    else:
                        #self.pluginsExitList.append(None)
                        pass
                        
                newConfFile = xmlConfFile.commit()
                del xmlConfFile
                #print "self.pluginsExitList:"
                #print self.pluginsExitList
                
                # On verifie si on a cree un nouveau XML
                if newConfFile:
                    currentTimeStr = str(time.time())
                    # on demande a l'utilisateur s'il veut remplacer l'ancien xml par le nouveau
                    menuList = ["Mettre a jour la configuation et sortir","Mettre a jour la configuation et redemarrer (XBOX)","Sortir sans rien faire"]
                    dialog = xbmcgui.Dialog()
                    chosenIndex = dialog.select("Modifications dans sources.xml, que d�sirez vous faire?", menuList)               
                    if chosenIndex == 0: 
                        # Mettre a jour la configuation et sortir
                        # On renomme source.xml en ajoutant le timestamp
                        os.rename(os.path.join(self.userDataDir,"sources.xml"),os.path.join(self.userDataDir,"sources_%s.xml"%currentTimeStr))
                        # On renomme sourcesNew.xml source.xml
                        os.rename(os.path.join(self.userDataDir,"sourcesNew.xml"),os.path.join(self.userDataDir,"sources.xml"))
                        
                    elif chosenIndex == 1: 
                        # Mettre a jour la configuation et redemarrer
                        # On renomme source.xml en ajoutant le timestamp
                        os.rename(os.path.join(self.userDataDir,"sources.xml"),os.path.join(self.userDataDir,"sources_%s.xml"%currentTimeStr))
                        # On renomme sourcesNew.xml source.xml
                        os.rename(os.path.join(self.userDataDir,"sourcesNew.xml"),os.path.join(self.userDataDir,"sources.xml"))
                        # on redemarre
                        xbmc.restart()
                    else:
                        # On supprime le xml que nous avons genere
                        os.remove(os.path.join(self.userDataDir,"sourcesNew.xml"))

                #on ferme tout
                self.close()

            if action == ACTION_PARENT_DIR:
                #remonte l'arborescence
                # On verifie si on est a l'interieur d'un ses sous section plugin 
                if (self.type == "Plugins Musique") or (self.type == "Plugins Images") or (self.type == "Plugins Programmes") or (self.type == "Plugins Vid�os"):
                    self.type = "Plugins"
                    try:
                        print "Appel updateList()"
                        self.updateList()
                    except Exception, e:
                        print "Window::onAction ACTION_PREVIOUS_MENU: Exception durant updateList()",e
                        print ("error/onaction: " + str(sys.exc_info()[0]))
                        traceback.print_exc()
                else:
                    # cas standard
                    self.type = "racine"
                    try:
                        print "Appel updateList()"
                        self.updateList()
                    except Exception, e:
                        print "Window::onAction ACTION_PREVIOUS_MENU: Exception durant updateList()",e
                        print ("error/onaction: " + str(sys.exc_info()[0]))
                        traceback.print_exc()
                
        except Exception, e:
            print "Window::onAction: Exception",e
            print ("error/onaction: " + str(sys.exc_info()[0]))
            traceback.print_exc()

    def onControl(self, control):
        """
        Traitement si selection d'un element de la liste
        """
        try:
            if control == self.list:

                if (self.type   == "racine"):
                    self.index = self.list.getSelectedPosition()
                    self.type = self.downloadTypeList[self.racineDisplayList[self.list.getSelectedPosition()]] # On utilise le filtre
                    
                    print "Type courant est Racine - nouveau type est:%s"%self.type
                    print "Mise a jour de la liste"

                    self.updateList() #on raffraichit la page pour afficher le contenu

                elif (self.type   == "Plugins"):
                    self.index = self.list.getSelectedPosition()
                    self.type = self.downloadTypeList[self.pluginDisplayList[self.list.getSelectedPosition()]] # On utilise le filtre
                    
                    print "Type courant est Plugins - nouveau type est:%s"%self.type
                    print "Mise a jour de la liste"
                    
                    self.updateList() #on raffraichit la page pour afficher le contenu

                else:
                    downloadOK = True
                    correctionPM3bidon = False
                    self.index = self.list.getSelectedPosition()
                    source = self.curDirList[self.index]

                    if self.type == self.downloadTypeList[0]:   #Themes
                        # Verifions le themes en cours d'utilisation
                        mySkinInUse = xbmc.getSkinDir()
                        if mySkinInUse in source:
                            # Impossible de telecharger une skin en cours d'utlisation
                            dialog = xbmcgui.Dialog()
                            dialog.ok('Action impossible', "Vous ne pouvez �craser le Theme en cours d'utilisation", "Merci de changer le Theme en cours d'utilisation", "avant de le t�l�charger")
                            downloadOK = False
                        if 'Project Mayhem III' in source and self.USRPath == True:
                            self.linux_chmod(self.PMIIIDir)
                            if self.rightstest == True:
                                self.localdirList[0]= self.PMIIIDir
                                downloadOK = True
                                correctionPM3bidon = True
                            else:
                                dialog = xbmcgui.Dialog()
                                dialog.ok('Action impossible', "Vous ne pouvez installer ce theme sans les droits", "d'administrateur")
                                downloadOK = False


                    elif self.type == self.downloadTypeList[1] and self.USRPath == True:   #Linux Scrapers
                        self.linux_chmod(self.scraperDir)
                        if self.rightstest == True :
                            downloadOK = True
                        else:
                            dialog = xbmcgui.Dialog()
                            dialog.ok('Action impossible', "Vous ne pouvez installer le scraper sans les droits", "d'administrateur")
                            downloadOK = False
                            
                    if source.endswith('zip') or source.endswith('rar'):
                        self.targetDir = self.localdirList[self.downloadTypeList.index(self.type)]
                        self.localdirList[self.downloadTypeList.index(self.type)]= self.CacheDir
                        
                    if downloadOK == True:
                        continueDownload = True
                        
                        # on verifie le si on a deja telecharge cet element (ou une de ses version anterieures)
                        isDownloaded,localDirPath = self.passionFTPCtrl.isAlreadyDownloaded(source, self.remotedirList[self.downloadTypeList.index(self.type)], self.downloadTypeList.index(self.type))
                    
                        if (isDownloaded) and  (localDirPath != None):
                            print "Repertoire deja present localement"
                            # On traite le repertorie deja present en demandant a l'utilisateur de choisir
                            continueDownload = self.processOldDownload(localDirPath)
                        else:
                            print localDirPath
                            print isDownloaded

                        if continueDownload == True:
                            # Fenetre de telechargement
                            
                            dp = xbmcgui.DialogProgress()
                            lenbasepath = len(self.remotedirList[self.downloadTypeList.index(self.type)])
                            downloadItem = source[lenbasepath:]
                            percent = 0
                            dp.create("T�l�chargement: %s"%downloadItem,"T�l�chargement Total: %d%%"%percent)
                            
                            # Type est desormais reellement le type de download, on utlise alors les liste pour recuperer le chemin que l'on doit toujours passer
                            # on appel la classe passionFTPCtrl avec la source a telecharger
                            downloadStatus = self.passionFTPCtrl.download(source, self.remotedirList[self.downloadTypeList.index(self.type)], self.downloadTypeList.index(self.type),progressbar_cb=self.updateProgress_cb,dialogProgressWin = dp)
                            dp.close()
    
                            if downloadStatus == -1:
                                # Telechargment annule par l'utilisateur
                                title    = "T�l�chargement annul�"
                                message1 = "%s: %s"%(self.type,downloadItem)
                                message2 = "T�l�chargement annul� alors qu'il etait en cours "
                                message3 = "Voulez-vous supprimer les fichiers d�j� t�l�charg�s?"
                                dialogInfo = xbmcgui.Dialog()
                                if dialogInfo.yesno(title, message1, message2,message3):
                                    print "Suppression du repertoire %s"%localDirPath
                                    dialogInfo2 = xbmcgui.Dialog()
                                    if os.path.isdir(localDirPath):
                                        if self.deleteDir(localDirPath):
                                            dialogInfo2.ok("R�pertoire supprim�", "Le r�pertoire:", localDirPath,"a bien �t� supprim�")
                                        else:
                                            dialogInfo2.ok("Erreur", "Impossible de supprimer le r�pertoire", localDirPath)
                                    else:
                                        try:
                                            os.remove(localDirPath)
                                            dialogInfo2.ok("Fichier supprim�", "Le fichier:", localDirPath,"a bien �t� supprim�")
                                        except Exception, e: 
                                            dialogInfo2.ok("Erreur", "Impossible de supprimer le fichier", localDirPath)
                            else:
                                title    = "T�l�chargement termin�"
                                message1 = "%s: %s"%(self.type,downloadItem)
                                message2 = "a �t� t�l�charg� dans le repertoire:"
                                message3 = "%s"%self.localdirList[self.downloadTypeList.index(self.type)]
    
                                dialogInfo = xbmcgui.Dialog()
                                dialogInfo.ok(title, message1, message2,message3)
    
                            #TODO: Attention correctionPM3bidon n'est pa defini dans le cas d'un scraper ou script
                            #      Je l'ai donc defini a False au debut
                            # On remet a la bonne valeur initiale self.localdirList[0]
                            if correctionPM3bidon == True:
                                self.localdirList[0] = themesDir
                                correctionPM3bidon = False
                            # On se base sur l'extension pour determiner si on doit telecharger dans le cache.
                            # Un tour de passe passe est fait plus haut pour echanger les chemins de destination avec le cache, le chemin de destination
                            # est retabli ici 'il s'agit de targetDir'
                            print "download status"
                            print downloadStatus
                            if downloadItem.endswith('zip') or downloadItem.endswith('rar'):
                                if downloadStatus != -1:
                                    installCancelled = False
                                    installError     = None
                                    dp = xbmcgui.DialogProgress()
                                    dp.create("Installation: %s"%downloadItem,"T�l�chargement Total: %d%%"%percent)
                                    dialogUI = xbmcgui.DialogProgress()
                                    dialogUI.create("Installation en cours ...", "%s est en cours d'installation"%downloadItem, "Veuillez patienter...")
                                    
                                    #Appel de la classe d'extraction des archives
                                    print "Extraction de l'archives: %s"%downloadItem
                                    remoteDirPath = self.remotedirList[self.downloadTypeList.index(self.type)]#chemin ou a ete telecharge le script
                                    localDirPath = self.localdirList[self.downloadTypeList.index(self.type)]
                                    archive = source.replace(remoteDirPath,localDirPath + os.sep)#remplacement du chemin de l'archive distante par le chemin local temporaire
                                    self.localdirList[self.downloadTypeList.index(self.type)]= self.targetDir
                                    fichierfinal0 = archive.replace(localDirPath,self.localdirList[self.downloadTypeList.index(self.type)])
                                    if fichierfinal0.endswith('.zip'):
                                        fichierfinal = fichierfinal0.replace('.zip','')
                                    elif fichierfinal0.endswith('.rar'):
                                        fichierfinal = fichierfinal0.replace('.rar','')
        
                                    # On n'a besoin d'ue d'un instance d'extracteur sinon on va avoir une memory leak ici car on ne le desalloue jamais
                                    # Je l'ai donc creee dans l'init comme attribut de la classe
                                    #self.extracter.extract(archive,self.localdirList[self.downloadTypeList.index(self.type)])
                                    
                                    # Capture reperoire cache avant extraction
                                    cacheDirSpy = directorySpy(self.CacheDir)
                                    
                                    # Extraction dans cache
                                    self.extracter.extract(archive,self.CacheDir)
                                    
                                    newCacheItemList = None
                                    if downloadItem.endswith('rar'):
                                        # du fait de  xbmc.executebuiltin pour les rar il va falloir attendre avant d'avoir le repertoire dispo
                                        time.sleep(2)
                                           
                                        extraction_attempt=8 #nombre de tentatives maxi
                                        while extraction_attempt:
                                            # Recuperation du nom de l'element cr��
                                            newCacheItemList = cacheDirSpy.getNewItemList()
                                            if len(newCacheItemList) > 0:
                                                extraction_attempt = 0
                                            else:
                                                extraction_attempt = extraction_attempt -1 #on d�cr�mente les tentatives....
                                                time.sleep(2)
                                    else:
                                        # Autre archives
                                        # Recuperation du nom de l'element cr��
                                        newCacheItemList = cacheDirSpy.getNewItemList()
                                                                                    
                                    if len(newCacheItemList) == 1:
                                       # On verifie si le repertorie suivant existe deja:
                                        destination = os.path.join(self.localdirList[self.downloadTypeList.index(self.type)],newCacheItemList[0])
                                        print destination
                                        if os.path.exists(destination):
                                            # Repertoire d�ja pr�sent
                                            # On demande a l'utilisateur ce qu'il veut faire
                                            if self.processOldDownload(destination):
                                                try:
                                                    #shutil2.copy2(xbmc.makeLegalFilename(os.path.join(self.CacheDir,newCacheItemList[0])),xbmc.makeLegalFilename(destination),overwrite=True)
                                                    #shutil2.move(os.path.join(self.CacheDir,newCacheItemList[0]),destination,overwrite=True)
                                                    if os.path.exists(destination) == False:
                                                        shutil.move(os.path.join(self.CacheDir,newCacheItemList[0]),destination)
                                                    else:
                                                        dialogInfo = xbmcgui.Dialog()
                                                        dialogInfo.ok("Erreur - Installation impossible", "Le r�pertoire", destination,"n'a pas �t� renomm� ou supprim�")
                                                        installError = "%s n'a pas �t� renomm� ou supprim�"%destination
                                                except:
                                                    installError = "Exception durant le deplacement de %s"%destination
                                                    print ("error/onControl: " + str(sys.exc_info()[0]))
                                                    traceback.print_exc()
                                            else:
                                                installCancelled = True
                                                print "L'installation de %s a �t� annul�e par l'utilisateur"%downloadItem 
                                        else:
                                            # Le Repertoire n'est pas present localement -> on peut deplacer le repertoire depuis cache
                                            try:
                                                shutil.move(os.path.join(self.CacheDir,newCacheItemList[0]),destination)
                                            except:
                                                installError = "Exception durant le deplacement de %s"%destination
                                                print ("error/onControl: " + str(sys.exc_info()[0]))
                                                traceback.print_exc()
                                                

                                    elif len(newCacheItemList) == 0:
                                        installError = "%s d�ja d�compress� dans cache"%archive
                                        print "Erreur - Aucun nouveau r�pertoire n'a �t� cr�� a l'extraction de %s"%archive
                                        print "Merci de verifier s'il n'existait pas deja"
                                    else:
                                        installError = "Plus d'un r�pertoire � la racine de %s"%archive
                                        print "Erreur: plus d'un nouvel element cr�� a l'extraction de %s dans le repertoire cache"%archive
                                    
                                    # Deplacement de l'element dans le bon repertoire
                                    #TODO: faire un test si l'extraction etait OK
                                    
                                    # On supprime le repertoire decompresse
                                    if len(newCacheItemList) > 0:
                                        self.deleteDir(os.path.join(self.CacheDir,newCacheItemList[0]))
                                    
                                    # Close the Loading Window
                                    dialogUI.close()
                                    
                                    dialogInfo = xbmcgui.Dialog()
                                    if installCancelled == False and installError == None:
                                        dialogInfo.ok("Installation Termin�e", "L'installation de %s est termin�e"%downloadItem)
                                    else:
                                        if installError != None:
                                            # Erreur durant l'install (meme si on a annule)
                                            dialogInfo.ok("Erreur - Installation impossible", installError, "Veuillez v�rifier les logs")
                                        elif installCancelled == True:
                                            # Install annulee
                                            dialogInfo.ok("Installation annul�e", "L'installation de %s a �t� annul�e"%downloadItem)
                                        else:
                                            # Install annulee
                                            dialogInfo.ok("Erreur - Installation impossible", "Erreur inconnue", "Veuillez v�rifier les logs")
                                else:
                                    # On remet a la bonne valeur initiale self.localdirList
                                    self.localdirList[self.downloadTypeList.index(self.type)]= self.targetDir
                                
        except:
            print ("error/onControl: " + str(sys.exc_info()[0]))
            traceback.print_exc()
            
    def updateProgress_cb(self, percent, dp=None):
        """
        Met a jour la barre de progression
        """
        #TODO Dans le futur, veut t'on donner la responsabilite a cette fonction le calcul du pourcentage????
        try:
            print percent
            dp.update(percent)
        except:
            percent = 100
            dp.update(percent)

    def updateList(self):
        """
        Mise a jour de la liste affichee
        """
        # On verifie self.type qui correspond au type de liste que l'on veut afficher
        dialogUI = xbmcgui.DialogProgress()
        dialogUI.create("Installeur Passion-XBMC", "Chargement des informations", "Veuillez patienter...")
        if (self.type  == "racine"):
            #liste virtuelle des sections
#            del self.curDirList[:] # on vide la liste
            self.curDirList = self.racineDisplayList
            
        elif (self.type  == "Plugins"):
            #liste virtuelle des sections
#            del self.curDirList[:] # on vide la liste
            self.curDirList = self.pluginDisplayList
            
        elif (self.type == "Plugins Musique") or (self.type == "Plugins Images") or (self.type == "Plugins Programmes") or (self.type == "Plugins Vid�os"):
            self.curDirList = self.passionFTPCtrl.getDirList(self.remotedirList[self.pluginDisplayList[self.index]])
            print "self.curDirList pour une section"
            print self.curDirList
            
        else:
            #liste virtuelle des sections
            #del self.curDirList[:] # on vide la liste

            #liste physique d'une section sur le ftp
            self.curDirList = self.passionFTPCtrl.getDirList(self.remotedirList[self.index])

        xbmcgui.lock()
        
        # Clear all ListItems in this control list
        self.list.reset()

        # Calcul du nombre d'elements de la liste
        itemnumber = len(self.curDirList)

        # On utilise la fonction range pour faire l'iteration sur index
        for j in range(itemnumber):
            if (self.type  == "racine") or (self.type  == "Plugins"):
                # Element de la liste
                if (self.type  == "racine"):
                    sectionName = self.downloadTypeList[self.racineDisplayList[j]] # On utilise le filtre
                    # Met a jour le titre:
                    self.strMainTitle.setLabel("S�lection")
                elif (self.type  == "Plugins"):
                    sectionName = self.downloadTypeList[self.pluginDisplayList[j]] # On utilise le filtre
                    # Met a jour le titre:
                    self.strMainTitle.setLabel("Plugins")

                # Affichage de la liste des sections
                # -> On compare avec la liste affichee dans l'interface
                #sectionName = self.downloadTypeList[j]
                if sectionName == self.downloadTypeList[0]:
                    imagePath = os.path.join(IMAGEDIR,"icone_theme.png")
                elif sectionName == self.downloadTypeList[1]:
                    imagePath = os.path.join(IMAGEDIR,"icone_scrapper.png")
                elif sectionName == self.downloadTypeList[2]:
                    imagePath = os.path.join(IMAGEDIR,"icone_script.png")
                elif sectionName == self.downloadTypeList[3]:
                    imagePath = os.path.join(IMAGEDIR,"icone_script.png")
                else:
                    # Image par defaut (ou aucune si = "")
                    imagePath = imagePath = os.path.join(IMAGEDIR,"icone_script.png")

                displayListItem = xbmcgui.ListItem(label = sectionName, thumbnailImage = imagePath)
                self.list.addItem(displayListItem)
                
            elif (self.type == "Plugins Musique") or (self.type == "Plugins Images") or (self.type == "Plugins Programmes") or (self.type == "Plugins Vid�os"):
                # Element de la liste
                ItemListPath = self.curDirList[j]
                
                lenindex = len(self.remotedirList[self.pluginDisplayList[self.index]]) # on a tjrs besoin de connaitre la taille du chemin de base pour le soustraire/retirer du chemin global plus tard
                
                #TODO: creer de nouveau icones pour les sous-sections plugins
                # Met a jour le titre et les icones:
                if self.type == self.downloadTypeList[4]:   #Themes
                    self.strMainTitle.setLabel(str(itemnumber) + " Plugins Musique")
                    imagePath = os.path.join(IMAGEDIR,"icone_theme.png")
                elif self.type == self.downloadTypeList[5]: #Scrapers
                    self.strMainTitle.setLabel(str(itemnumber) + " Plugins Images")
                    imagePath = os.path.join(IMAGEDIR,"icone_scrapper.png")
                elif self.type == self.downloadTypeList[6]: #Scripts
                    self.strMainTitle.setLabel(str(itemnumber) + " Plugins Programmes")
                    imagePath = os.path.join(IMAGEDIR,"icone_script.png")
                elif self.type == self.downloadTypeList[7]: #Plugins
                    self.strMainTitle.setLabel(str(itemnumber) + " Plugins Vid�os")
                    imagePath = os.path.join(IMAGEDIR,"icone_script.png")
                else:
                    # Image par defaut (ou aucune si = "")
                    imagePath = ""

                item2download = ItemListPath[lenindex:]

                displayListItem = xbmcgui.ListItem(label = item2download, thumbnailImage = imagePath)
                self.list.addItem(displayListItem)
                
            else:
                # Element de la liste
                ItemListPath = self.curDirList[j]
                
                #affichage de l'interieur d'une section
                #self.numindex = self.index
                lenindex = len(self.remotedirList[self.index]) # on a tjrs besoin de connaitre la taille du chemin de base pour le soustraire/retirer du chemin global plus tard

                # Met a jour le titre et les icones:
                if self.type == self.downloadTypeList[0]:   #Themes
                    self.strMainTitle.setLabel(str(itemnumber) + " Themes")
                    imagePath = os.path.join(IMAGEDIR,"icone_theme.png")
                elif self.type == self.downloadTypeList[1]: #Scrapers
                    self.strMainTitle.setLabel(str(itemnumber) + " Scrapers")
                    imagePath = os.path.join(IMAGEDIR,"icone_scrapper.png")
                elif self.type == self.downloadTypeList[2]: #Scripts
                    self.strMainTitle.setLabel(str(itemnumber) + " Scripts")
                    imagePath = os.path.join(IMAGEDIR,"icone_script.png")
                else:
                    # Image par defaut (ou aucune si = "")
                    imagePath = ""

                item2download = ItemListPath[lenindex:]

                displayListItem = xbmcgui.ListItem(label = item2download, thumbnailImage = imagePath)
                self.list.addItem(displayListItem)
        xbmcgui.unlock()
        
        # Set Focus on list
        self.setFocus(self.list)
        dialogUI.close()

    def deleteDir(self,path):
        """
        Efface un repertoire et tout son contenu (le repertoire n'a pas besoin d'etre vide)
        retourne True si le repertoire est effece False sinon
        """
        result = True
        if os.path.isdir(path):
            dirItems=os.listdir(path)
            for item in dirItems:
                itemFullPath=os.path.join(path, item)   
                try:
                    if os.path.isfile(itemFullPath):
                        # Fichier
                        os.remove(itemFullPath)
                    elif os.path.isdir(itemFullPath):
                        # Repertoire
                        self.deleteDir(itemFullPath)
                except Exception, e: 
                    result = False
                    print "deleteDir: Exception la suppression du reperoire: %s"%path
                    print e
                    traceback.print_exc(file = sys.stdout)
            # Suppression du repertoire pere
            try :
                os.rmdir(path)
            except Exception, e: 
                result = False
                print "deleteDir: Exception la suppression du reperoire: %s"%path
                print e
                traceback.print_exc(file = sys.stdout)
        else:
            print "deleteDir: %s n'est pas un repertoire"%path
            result = False
            
        return result

    def delFiles(self,folder):
        """
        Source: Joox
        Efface tous le fichier d'un repertorie donne ainsi que des sous-repertoires
        Note: les sous-repertoires eux-memes ne sont pas effaces
        folder: chemin du repertpoire local
        """
        for root, dirs, files in os.walk(folder , topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except Exception, e:
                    print e

    def verifrep(self,folder):
        """
        Source: myCine
        Verifie l'existance  d'un repertoire et le cree si besoin
        """
        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
        except Exception, e:
            print("verifrep - Exception durant la creation du repertoire: " + folder)
            print(e)
            pass

    def linux_chmod(self,path):
        """
        Effectue un chmod sur un repertoire pour ne plus etre bloque par les droits root sur plateforme linux
        """
        Wtest = os.access(path,os.W_OK)
        if Wtest == True:
            self.rightstest = True
            print "rightest OK"
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok('Demande de mot de passe', "Vous devez saisir votre mot de passe administrateur", "systeme")
            keyboard = xbmc.Keyboard("","Mot de passe Administrateur", True)
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                password = keyboard.getText()
                PassStr = "echo %s | "%password
                ChmodStr = "sudo -S chmod 777 -R %s"%path
                try:
                    os.system(PassStr + ChmodStr)
                    self.rightstest = True

                except Exception, e:
                    print "erreur CHMOD %s"%path
                    print e
                    self.rightstest = False
            else:
                self.rightstest = False

    def processOldDownload(self,localAbsDirPath):
        """
        Traite les ancien download suivant les desirs de l'utilisateur
        retourne True si le download peut continuer.
        """
        continueDownload = True
        
        # Verifie se on telecharge un repertoire ou d'un fichier
        if os.path.isdir(localAbsDirPath):
            # Repertoire
            menuList = ["Supprimer le r�pertoire","Renommer le repertoire","Annuler"]
            dialog = xbmcgui.Dialog()
            chosenIndex = dialog.select("%s est deja present, que d�sirez vous faire?"%(os.path.basename(localAbsDirPath)), menuList)               
            #if (dialog.yesno("Erreur", "%s est deja present, voulez vous le renommer"%(os.path.basename(localAbsDirPath)),"Sinon il sera �cras�")):
            if chosenIndex == 0: 
                # Supprimer
                print "Supprimer le r�pertoire"
                self.deleteDir(localAbsDirPath)
            elif chosenIndex == 1: # Renommer
                # Suppression du repertoire
                print "Renommer le repertoire"
                keyboard = xbmc.Keyboard("", heading = "Saisir le nouveau nom:")
                keyboard.setHeading('Saisir le nouveau nom:')  # optional
                keyboard.setDefault(os.path.basename(localAbsDirPath))                    # optional

                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    inputText = keyboard.getText()
                    print"Nouveau nom: %s"%inputText
                    os.rename(localAbsDirPath,localAbsDirPath.replace(os.path.basename(localAbsDirPath),inputText))
                    dialogInfo = xbmcgui.Dialog()
                    dialogInfo.ok("L'�l�ment a �t� renomm�:", localAbsDirPath.replace(os.path.basename(localAbsDirPath),inputText))
                del keyboard
            else:
                print "Annulation"
                continueDownload = False
        else:
            # Fichier
            print "processOldDownload: Fichier : %s - ce cas n'est pas encore trait�"%localAbsDirPath
            #TODO: cas a implementer
            
        return continueDownload

                

########
#
# Main
#
########



def go():
    #Fonction de demarrage
    w = MainWindow()
    w.doModal()
    del w

ROOTDIR = os.getcwd().replace(';','')

##############################################################################
#                   Initialisation conf.cfg                                  #
##############################################################################
fichier = os.path.join(ROOTDIR, "conf.cfg")
config = ConfigParser.ConfigParser()
config.read(fichier)

##############################################################################
#                   Initialisation parametres locaux                         #
##############################################################################
IMAGEDIR        = config.get('InstallPath','ImageDir')
CACHEDIR        = config.get('InstallPath','CacheDir')
themesDir       = config.get('InstallPath','ThemesDir')
scriptDir       = config.get('InstallPath','ScriptsDir')
scraperDir      = config.get('InstallPath','ScraperDir')
pluginDir       = config.get('InstallPath','PluginDir')
pluginMusDir    = config.get('InstallPath','PluginMusDir')
pluginPictDir   = config.get('InstallPath','PluginPictDir')
pluginProgDir   = config.get('InstallPath','PluginProgDir')
pluginVidDir    = config.get('InstallPath','PluginVidDir')
userdatadir     = config.get('InstallPath','UserDataDir')
USRPath         = config.getboolean('InstallPath','USRPath')
if USRPath == True:
    PMIIIDir = config.get('InstallPath','PMIIIDir')
RACINE = True

##############################################################################
#                   Initialisation parametres serveur                        #
##############################################################################
host                = config.get('ServeurID','host')
user                = config.get('ServeurID','user')
rssfeed             = config.get('ServeurID','rssfeed')
password            = config.get('ServeurID','password')

downloadTypeLst     = ["Themes","Scrapers","Scripts","Plugins","Plugins Musique","Plugins Images","Plugins Programmes","Plugins Vid�os"]
#TODO: mettre les chemins des rep sur le serveur dans le fichier de conf
remoteDirLst        = ["/.passionxbmc/Themes/","/.passionxbmc/Scraper/","/.passionxbmc/Scripts/","/.passionxbmc/Plugins/","/.passionxbmc/Plugins/Music/","/.passionxbmc/Plugins/Pictures/","/.passionxbmc/Plugins/Programs/","/.passionxbmc/Plugins/Videos/"]
localDirLst         = [themesDir,scraperDir,scriptDir,pluginDir,pluginMusDir,pluginPictDir,pluginProgDir,pluginVidDir]

racineDisplayLst    = [0,1,2,3] # Liste de la racine: Cette liste est un filtre (utilisant l'index) sur les listes ci-dessus
pluginDisplayLst    = [4,5,6,7] # Liste des plugins : Cette liste est un filtre (utilisant l'index) sur les listes ci-dessus

##############################################################################
#                   Version et auteurs                                       #
##############################################################################
version         = config.get('Version','version')
author          = 'Seb & Temhil'
graphicdesigner = 'Jahnrik'

##############################################################################
#                   Verification parametres locaux et serveur                #
##############################################################################
print "FTP host: %s"%host
print "Chemin ou les themes seront telecharges: %s"%themesDir

print("===================================================================")
print("")
print("        Passion XBMC Installeur " + version + " STARTS")
print("        Auteurs : "+ author)
print("        Graphic Design by : "+ graphicdesigner)
print("")
print("===================================================================")

if __name__ == "__main__":
    #ici on pourrait faire des action si le script �tait lanc� en tant que programme
    print "demarrage du script INSTALLEUR.py en tant que programme"
    go()
else:
    #ici on est en mode librairie import�e depuis un programme
    pass
