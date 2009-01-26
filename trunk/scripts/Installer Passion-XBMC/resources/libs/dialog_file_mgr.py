
#Modules general
import os
import re
import sys

#modules XBMC
import xbmc
import xbmcgui

#modules custom
import shutil2
from utilities import *
#from convert_utc_time import set_local_time

#module logger
try:
    logger = sys.modules[ "__main__" ].logger
except:
    import script_log as logger
    
#import traceback

# INITIALISATION CHEMIN RACINE
ROOTDIR = os.getcwd().replace( ";", "" )

#FONCTION POUR RECUPERER LES LABELS DE LA LANGUE.
_ = sys.modules[ "__main__" ].__language__

DIALOG_PROGRESS = xbmcgui.DialogProgress()


############################################################################
# Get actioncodes from keymap.xml
############################################################################
#ACTION_MOVE_LEFT = 1
#ACTION_MOVE_RIGHT = 2
#ACTION_MOVE_UP = 3
#ACTION_MOVE_DOWN = 4
#ACTION_PAGE_UP = 5
#ACTION_PAGE_DOWN = 6
#ACTION_SELECT_ITEM = 7
#ACTION_HIGHLIGHT_ITEM = 8
ACTION_PARENT_DIR = 9
ACTION_PREVIOUS_MENU = 10
ACTION_SHOW_INFO = 11
#ACTION_PAUSE = 12
#ACTION_STOP = 13
#ACTION_NEXT_ITEM = 14
#ACTION_PREV_ITEM = 15
ACTION_CONTEXT_MENU = 117 # ACTION_MOUSE_RIGHT_CLICK *sa marche maintenant avec les derniere SVN*
CLOSE_CONTEXT_MENU = ( ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_CONTEXT_MENU, )




##################################################

TYPE_ROOT            = _( 10 )
TYPE_SKIN            = _( 11 )
TYPE_SCRAPER         = _( 12 )      
TYPE_SCRIPT          = _( 13 )      
TYPE_PLUGIN          = _( 14 )  
TYPE_PLUGIN_MUSIC    = _( 15 )
TYPE_PLUGIN_PICTURES = _( 16 )
TYPE_PLUGIN_PROGRAMS = _( 17 )
TYPE_PLUGIN_VIDEO    = _( 18 )

#INDEX_ROOT            = None
INDEX_SKIN            = 0
INDEX_SCRAPER         = 1      
INDEX_SCRIPT          = 2      
INDEX_PLUGIN          = 3  
INDEX_PLUGIN_MUSIC    = 4
INDEX_PLUGIN_PICTURES = 5
INDEX_PLUGIN_PROGRAMS = 6
INDEX_PLUGIN_VIDEO    = 7




typeList  = [ TYPE_SKIN,         TYPE_SCRAPER,         TYPE_SCRIPT,        TYPE_PLUGIN,        TYPE_PLUGIN_MUSIC,         TYPE_PLUGIN_PICTURES,         TYPE_PLUGIN_PROGRAMS,         TYPE_PLUGIN_VIDEO ] # Note: TYPE_ROOT est en dehors de la liste
thumbList = [ "icone_theme.png", "icone_scrapper.png", "icone_script.png", "icone_script.png", "passion-icone-music.png", "passion-icone-pictures.png", "passion-icone-programs.png", "passion-icone-video.png" ] # Note: TYPE_ROOT est en dehors de la liste

#TODO: mettre les chemins des rep sur le serveur dans le fichier de conf
#localDirLst = [ themesDir, scraperDir, scriptDir, pluginDir, pluginMusDir, pluginPictDir, pluginProgDir, pluginVidDir ]

rootDisplayList   = [ INDEX_SKIN, INDEX_SCRAPER, INDEX_SCRIPT, INDEX_PLUGIN ]                                # Liste de la racine: Cette liste est un filtre ( utilisant l'index ) sur les listes ci-dessus
pluginDisplayList = [ INDEX_PLUGIN_MUSIC, INDEX_PLUGIN_PICTURES, INDEX_PLUGIN_PROGRAMS, INDEX_PLUGIN_VIDEO ] # Liste des plugins : Cette liste est un filtre ( utilisant l'index ) sur les listes ci-dessus


def copy_func( cpt_blk, taille_blk, total_taille ):
    updt_val = int( ( cpt_blk * taille_blk ) / 10.0 / total_taille )
    if updt_val > 100: updt_val = 100
    DIALOG_PROGRESS.update( updt_val )
    # DON'T ALLOW Progress().iscanceled() BUG CREATE, FIXED SOON
    #if xbmcgui.DialogProgress().iscanceled():
    #    xbmcgui.DialogProgress().close()


class ListItemObject:
    """
    Structure de donnee definissant un element de la liste
    """
    def __init__( self, type='unknown', name='', local_path=None, thumb='default' ):
        self.type       = type
        self.name       = name
        self.local_path = local_path
        self.thumb      = thumb



class fileMgr:
    """
    
    File manager
    
    """
#    #TODO: Create superclass, inherit and overwrite init
#    def __init__(self,checkList):
##        self.verifrep(checkList[0]) #CACHEDIR
##        self.verifrep(checkList[1]) #DOWNLOADDIR
#        for i in range(len(checkList)):
#            self.verifrep(checkList[i]) 
#
#        # Set variables needed by NABBOX module
#        NABBOX.HTMLFOLDER = checkList[0] #CACHEDIR
#        print"browser - set NABBOX.HTMLFOLDER: %s"%(NABBOX.HTMLFOLDER)

    def verifrep(self, folder):
        """
        Check a folder exists and make it if necessary
        """
        try:
            #print("verifrep check if directory: " + folder + " exists")
            if not os.path.exists(folder):
                logger.LOG( logger.LOG_DEBUG, "verifrep: Impossible de trouver le repertoire - Tentative de creation du repertoire: %s", folder )
                os.makedirs(folder)
        except Exception, e:
            logger.LOG( logger.LOG_DEBUG, "verifrep: Exception durant la suppression du reperoire: %s", folder )
            logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
            
    def listDirFiles(self, path):
        """
        List the files of a directory
        @param path:
        """
        logger.LOG( logger.LOG_DEBUG, "listDirFiles: Liste le repertoire: %s", path )
        dirList = os.listdir( str( path ) )        

        return dirList
        
    def renameItem( self, base_path, old_name, new_name):
        """
        Renomme un fichier ou repertoire
        """
        os.rename( os.path.join(base_path, old_name), os.path.join(base_path, new_name) )
    
    def deleteItem( self, item_path):
        """
        Supprime un element (repertoire ou fichier)
        """
        if os.path.isdir(item_path):
            self.deleteDir(item_path)
        else:
            self.deleteFile(item_path)
            
    def deleteFile(self, filename):
        """
        Delete a file form download directory
        @param filename:
        """
        os.remove(filename)
            
    def deleteDir( self, path ):
        """
        Efface un repertoire et tout son contenu ( le repertoire n'a pas besoin d'etre vide )
        retourne True si le repertoire est effece False sinon
        """
        result = True
        if os.path.isdir( path ):
            dirItems=os.listdir( path )
            for item in dirItems:
                itemFullPath=os.path.join( path, item )
                try:
                    if os.path.isfile( itemFullPath ):
                        # Fichier
                        os.remove( itemFullPath )
                    elif os.path.isdir( itemFullPath ):
                        # Repertoire
                        self.deleteDir( itemFullPath )
                except:
                    result = False
                    logger.LOG( logger.LOG_DEBUG, "deleteDir: Exception la suppression du reperoire: %s", path )
                    logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
            # Suppression du repertoire pere
            try:
                os.rmdir( path )
            except:
                result = False
                logger.LOG( logger.LOG_DEBUG, "deleteDir: Exception la suppression du reperoire: %s", path )
                logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
        else:
            logger.LOG( logger.LOG_DEBUG, "deleteDir: %s n'est pas un repertoire", path )
            result = False

        return result
    
    def  extract(self,archive,targetDir):
        """
        Extract an archive in targetDir
        """
        xbmc.executebuiltin('XBMC.Extract(%s,%s)'%(archive,targetDir) )
        

    def linux_is_write_access( self, path ):
        """
        Linux
        Verifie si on a les dorit en ecriture sur un element
        """
        Wtest = os.access( path, os.W_OK )
        if Wtest == True:
            rightstest = True
            logger.LOG( logger.LOG_NOTICE, "linux chmod rightest OK for %s"%path )
        else:
            logger.LOG( logger.LOG_NOTICE, "linux chmod rightest NOT OK for %s"%path )
            rightstest = False
        return rightstest
        
    def linux_set_write_access( self, path, password ):
        """
        Linux
        Effectue un chmod sur un repertoire pour ne plus etre bloque par les droits root sur plateforme linux
        Retourne True en cas de succes ou False dans le cas contraire
        """
        PassStr = "echo %s | "%password
        ChmodStr = "sudo -S chmod 777 -R %s"%path
        try:
            os.system( PassStr + ChmodStr )
            rightstest = True
        except:
            rightstest = False
            logger.LOG( logger.LOG_ERROR, "erreur CHMOD %s", path )
            logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
        return rightstest


class FileMgrWindow( xbmcgui.WindowXML ):
    # control id's
    CONTROL_MAIN_LIST      = 150
    CONTROL_FORUM_BUTTON   = 300
    CONTROL_OPTIONS_BUTTON = 310

    def __init__( self, *args, **kwargs ):
        """
        Initialisation de l'interface
        """
        xbmcgui.WindowXML.__init__( self, *args, **kwargs )

        self.mainwin           = kwargs[ "mainwin" ]
        self.configManager     = self.mainwin.configManager
        self.localdirList      = self.mainwin.localdirList      # Liste des repertoire locaux

        #self.ItemTypeList      = self.mainwin.downloadTypeList  # Liste des types des items geres (plugins, scripts, skins ...)
        #self.racineDisplayList = self.mainwin.racineDisplayList # Liste de la racine: Cette liste est un filtre ( utilisant l'index ) sur les listes downloadTypeList et localdirList
        #self.pluginDisplayList = self.mainwin.pluginDisplayList # Liste des plugins : Cette liste est un filtre ( utilisant l'index ) sur les listes downloadTypeList et localdirList
        self.itemTypeList      = typeList          # Liste des types des items geres (plugins, scripts, skins ...)
        self.itemThumbList     = thumbList         # Liste des icones standards
        self.rootDisplayList   = rootDisplayList   # Liste de la racine: Cette liste est un filtre ( utilisant l'index ) sur les listes downloadTypeList et localdirList
        self.pluginDisplayList = pluginDisplayList # Liste des plugins : Cette liste est un filtre ( utilisant l'index ) sur les listes downloadTypeList et localdirList
        self.scraperDir        = self.mainwin.scraperDir
        self.USRPath           = self.mainwin.USRPath
        self.rightstest        = self.mainwin.rightstest
        self.scriptDir         = self.mainwin.scriptDir
        self.CacheDir          = self.mainwin.CacheDir
        self.userDataDir       = self.mainwin.userDataDir
        #self.rightstest         = ""
        
        self.curListType        = TYPE_ROOT
        self.currentItemList    = []
        self.index              = ""
        self.main_list_last_pos = []

        self.fileMgr             = fileMgr()

        #TODO: TOUTES ces varibales devraient etre passees en parametre du constructeur de la classe ( __init__ si tu preferes )
        # On ne devraient pas utiliser de variables globale ou rarement en prog objet


        #TODO: A nettoyer, ton PMIIIDir n'est pas defini pour XBOX sans le test si dessous
        if self.USRPath == True:
            self.PMIIIDir = PMIIIDir

        self.is_started = True


    def onInit( self ):
        # Title of the current pages
        self.setProperty( "Category", _( 10 ) )

        self._get_settings()
        self._set_skin_colours()
        
        # Verifications des permissions sur les repertoires
        self.check_w_rights()
        
        if self.is_started:
            self.is_started = False

            self.updateDataAndList()
            
    def onFocus( self, controlID ):
        #self.controlID = controlID
        #cette fonction n'est pas utiliser ici, mais dans les XML si besoin
        #Note: Mais il faut la declarer : )
        pass

    def onClick( self, controlID ):
        """
        Traitement si selection d'un element de la liste
        """
        try:
            if controlID == self.CONTROL_MAIN_LIST:
                self.show_context_menu()
        except:
            logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )

    def show_context_menu( self ):
        try: self.main_list_last_pos.append( self.getControl( self.CONTROL_MAIN_LIST ).getSelectedPosition() )
        except: self.main_list_last_pos.append( 0 )
        
        self.index = self.getControl( self.CONTROL_MAIN_LIST ).getSelectedPosition()
        if ( self.curListType == TYPE_ROOT or self.curListType == TYPE_PLUGIN):
            self.curListType = self.currentItemList[ self.index ].type # On extrait le type de l'item selectionne
            self.updateDataAndList()

        else:
            # On va ici afficher un menu des options du gestionnaire de fichiers
            item_path     = self.currentItemList[ self.index ].local_path # On extrait le chemin de l'item
            item_basename = os.path.basename( item_path )

            if ( self.curListType == TYPE_SCRIPT ) or ( self.itemTypeList.index(self.curListType) in self.pluginDisplayList ):
                # liste des options pour plugins et scripts
                menuList = [ _( 160 ), _( 157 ), _( 156 ), _( 161 ), _( 162 ), _( 153 ) ]
                #menuList = [ _( 160 ) % item_basename, _( 157 ) % item_basename, _( 156 ) % item_basename, _( 153 ) ]
            else:
                # liste des options pour skins et scrapers
                menuList = [ _( 157 ), _( 156 ), _( 161 ), _( 162 ), _( 153 ) ]
                #menuList = [ _( 157 ) % item_basename, _( 156 ) % item_basename, _( 153 ) ]
            chosenIndex = xbmcgui.Dialog().select( "%s : %s" % ( _( 5 ), bold_text( item_basename ) ), menuList )
            if chosenIndex != -1:
                # si liste des options est pour les skins et scrapers, augmente la valeur de +1
                if len( menuList ) == 5:
                    chosenIndex += 1
                if chosenIndex == 0: # Executer/Lancer
                    if ( self.itemTypeList.index(self.curListType) in self.pluginDisplayList ):
                        # Cas d'un sous-plugin (video, musique ...)
                        # window id's : http://xbmc.org/wiki/?title=Window_IDs
                        if ( self.curListType == TYPE_PLUGIN_VIDEO ):
                            command = "XBMC.ActivateWindow(10025,plugin://video/%s/)" % ( item_basename, )
                        elif ( self.curListType == TYPE_PLUGIN_MUSIC ):
                            command = "XBMC.ActivateWindow(10502,plugin://music/%s/)" % ( item_basename, )
                        elif ( self.curListType == TYPE_PLUGIN_PROGRAMS ):
                            command = "XBMC.ActivateWindow(10001,plugin://programs/%s/)" % ( item_basename, )
                        elif ( self.curListType == TYPE_PLUGIN_PICTURES ):
                            command = "XBMC.ActivateWindow(10002,plugin://pictures/%s/)" % ( item_basename, )
                    elif ( self.curListType == TYPE_SCRIPT ):
                        command = "XBMC.RunScript(%s)" % ( os.path.join( item_path, "default.py" ), )

                    #on ferme le script en court pour pas generer des conflits
                    self._close_dialog()
                    self.mainwin._close_script()
                    #maintenant qu'il y a plus de conflit possible, on execute la command
                    xbmc.executebuiltin( command )

                elif chosenIndex == 1: # Renommer
                    # Renommer l'element
                    item_dirname  = os.path.dirname( item_path )
                    keyboard = xbmc.Keyboard( item_basename, _( 154 ) )
                    keyboard.doModal()
                    if ( keyboard.isConfirmed() ):
                        inputText = keyboard.getText()
                        self.fileMgr.renameItem( item_dirname, item_basename, inputText )
                        xbmcgui.Dialog().ok( _( 155 ), inputText )
                        self.updateDataAndList()

                elif chosenIndex == 2:
                    # Supprimer l'element
                    if xbmcgui.Dialog().yesno( _( 158 )%item_basename, _( 159 )%item_basename ):
                        self.fileMgr.deleteItem( item_path )
                        self.updateDataAndList() 

                elif chosenIndex == 3:
                    # copier l'element
                    new_path = xbmcgui.Dialog().browse( 3, _( 167 ) % item_basename, "files" )
                    if bool( new_path ):
                        src = os.path.normpath( item_path )
                        dst = os.path.normpath( os.path.join( new_path, item_basename ) )
                        if xbmcgui.Dialog().yesno( _( 163 ), _( 165 ), src, dst ):
                            DIALOG_PROGRESS.create( _( 176 ), _( 178 ) + src, _( 179 ) + dst, _( 110 ) )
                            try:
                                if os.path.isdir( src ):
                                    if not os.path.isdir( os.path.dirname( dst ) ):
                                        os.makedirs( os.path.dirname( dst ) )
                                    shutil2.copytree( src, dst, reportcopy=copy_func, overwrite=True )
                                else:
                                    shutil2.copy( src, dst, reportcopy=copy_func, overwrite=True )
                            except:
                                xbmcgui.Dialog().ok( _( 169 ), _( 170 ), _( 171 ) )
                                logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
                                #import traceback; traceback.print_exc()
                            #self.updateDataAndList()
                            DIALOG_PROGRESS.close()

                elif chosenIndex == 4:
                    # deplacer l'element
                    new_path = xbmcgui.Dialog().browse( 3, _( 168 ) % item_basename, "files" )
                    if bool( new_path ):
                        src = os.path.normpath( item_path )
                        dst = os.path.normpath( os.path.join( new_path, item_basename ) )
                        if xbmcgui.Dialog().yesno( _( 164 ), _( 166 ), src, dst ):
                            DIALOG_PROGRESS.create( _( 177 ), _( 178 ) + src, _( 179 ) + dst, _( 110 ) )
                            try:
                                if os.path.isdir( src ):
                                    if not os.path.isdir( os.path.dirname( dst ) ):
                                        os.makedirs( os.path.dirname( dst ) )
                                    shutil2.copytree( src, dst, reportcopy=copy_func, overwrite=True )
                                else:
                                    shutil2.copy( src, dst, reportcopy=copy_func, overwrite=True )
                                self.fileMgr.deleteItem( src )
                            except:
                                xbmcgui.Dialog().ok( _( 169 ), _( 172 ), _( 173 ) )
                                logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
                                #import traceback; traceback.print_exc()
                            self.updateDataAndList()
                            DIALOG_PROGRESS.close()

    def _close_dialog( self ):
        #xbmc.sleep( 100 )
        self.close()

    def onAction( self, action ):
        """
        Remonte l'arborescence et quitte le script
        """
        try:
            if ( action == ACTION_CONTEXT_MENU ) and not ( self.curListType == TYPE_ROOT or self.curListType == TYPE_PLUGIN ):
                # Affiche les options pour l'utilisateur
                self.show_context_menu()

            elif ( action == ACTION_PREVIOUS_MENU ):
                # Sortie du script
                self._close_dialog()

            elif ( action == ACTION_PARENT_DIR ):
                # remonte l'arborescence
                if not self.main_list_last_pos:
                    try: self.main_list_last_pos.append( self.getControl( self.CONTROL_MAIN_LIST ).getSelectedPosition() )
                    except: self.main_list_last_pos.append( 0 )
                try:
                    # on verifie si on est un sous plugin
                    #if ( TYPE_PLUGIN + ' ' in self.curListType ):
                    if ( self.itemTypeList.index(self.curListType) in self.pluginDisplayList ): 
                        self.curListType = TYPE_PLUGIN
                    else:
                        # cas standard
                        self.curListType = TYPE_ROOT
                    self.updateDataAndList()
                except:
                    logger.LOG( logger.LOG_DEBUG, "FileMgrWindow::onAction::ACTION_PREVIOUS_MENU: Exception durant updateList()" )
                    logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )

                if self.main_list_last_pos:
                    self.getControl( self.CONTROL_MAIN_LIST ).selectItem( self.main_list_last_pos.pop() )

            elif ( action == ACTION_SHOW_INFO ):
                # Affiche la description de l'item selectionn�
                pass

        except:
            logger.LOG( logger.LOG_DEBUG, "FileMgrWindow::onAction: Exception" )
            logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )

    def _get_settings( self, defaults=False ):
        """ reads settings """
        self.settings = Settings().get_settings( defaults=defaults )
        
    def _set_skin_colours( self ):
        #xbmcgui.lock()
        try:
            self.setProperty( "style_PMIII.HD", ( "", "true" )[ ( self.settings[ "skin_colours_path" ] == "style_PMIII.HD" ) ] )
            self.setProperty( "Skin-Colours-path", self.settings[ "skin_colours_path" ] )
            self.setProperty( "Skin-Colours", ( self.settings[ "skin_colours" ] or get_default_hex_color() ) )
        except:
            logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
        #xbmcgui.unlock()

    def updateProgress_cb( self, percent, dp=None ):
        """
        Met a jour la barre de progression
        """
        #TODO Dans le futur, veut t'on donner la responsabilite a cette fonction le calcul du pourcentage????
        try:
            dp.update( percent )
        except:
            percent = 100
            dp.update( percent )

    def updateDataAndList( self ):
        DIALOG_PROGRESS.create( _( 0 ), _( 104 ), _( 110 ) )
        try:
            self.updateData() # On met a jour les donnees
            self.updateList() # On raffraichit la page pour afficher le contenu
        except:
            logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
        DIALOG_PROGRESS.close()

    def updateData( self ):
        """
        Mise a jour des donnnees de la liste courante
        """
        try:
            # Vide la liste
            del self.currentItemList[:]
            
            #if xbmc.getCondVisibility( "!Window.IsActive(progressdialog)" ):
            #    DIALOG_PROGRESS.create( _( 0 ), _( 104 ), _( 110 ) )
                
            # Recuperation des infos
            if ( self.curListType == TYPE_ROOT ):
                for index, filterIdx in enumerate( self.rootDisplayList ):
                    item = ListItemObject( type=self.itemTypeList[ filterIdx ], name=self.itemTypeList[ filterIdx ], local_path=self.localdirList[ filterIdx ], thumb=self.itemThumbList[ filterIdx ] )
                    self.currentItemList.append(item)
            elif ( self.curListType == TYPE_PLUGIN ):
                for index, filterIdx in enumerate( self.pluginDisplayList ):
                    item = ListItemObject( type=self.itemTypeList[ filterIdx ], name=self.itemTypeList[ filterIdx ], local_path=self.localdirList[ filterIdx ], thumb=self.itemThumbList[ filterIdx ] )
                    self.currentItemList.append(item)
            #elif TYPE_PLUGIN + ' ' in self.curListType:
            elif ( ( self.curListType == TYPE_SCRIPT ) or ( self.itemTypeList.index(self.curListType) in self.pluginDisplayList ) ):
                listdir = self.fileMgr.listDirFiles( self.localdirList[ self.itemTypeList.index(self.curListType) ] )
                for index, item  in enumerate( listdir ):
                    # Note:  dans le futur on pourra ici initialiser 'thumb' avec l'icone du script, plugin, themes ... 
                    #        pour le moment on prend l'icone correspondant au type
                    script_path    = os.path.join(self.localdirList[ self.itemTypeList.index(self.curListType) ],item)
                    thumbnail_path = os.path.join(script_path, "default.tbn")
                    if not os.path.exists(thumbnail_path):
                        thumbnail_path = self.itemThumbList[ self.itemTypeList.index(self.curListType) ]
                    item = ListItemObject( type=self.curListType, name=item, local_path=script_path, thumb=thumbnail_path )
                    self.currentItemList.append(item)
            else:
                listdir = self.fileMgr.listDirFiles( self.localdirList[ self.itemTypeList.index(self.curListType) ] )
                for index, item  in enumerate( listdir ):
                    # Note:  dans le futur on pourra ici initialiser 'thumb' avec l'icone du script, plugin, themes ... 
                    #        pour le moment on prend l'icone correspondant au type
                    item = ListItemObject( type=self.curListType, name=item, local_path=os.path.join(self.localdirList[ self.itemTypeList.index(self.curListType) ],item), thumb=self.itemThumbList[ self.itemTypeList.index(self.curListType) ] )
                    self.currentItemList.append(item)
        except:
            logger.LOG( logger.LOG_DEBUG, "FileMgrWindow: Exception durant la recuperation des donnees" )
            logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )

        #DIALOG_PROGRESS.close()

    def updateList( self ):
        """
        Mise a jour de la liste affichee
        """
        #if xbmc.getCondVisibility( "!Window.IsActive(progressdialog)" ):
        #    DIALOG_PROGRESS.create( _( 0 ), _( 104 ), _( 110 ) )

        #xbmcgui.lock()

        # Clear all ListItems in this control list
        self.getControl( self.CONTROL_MAIN_LIST ).reset()

        # Calcul du nombre d'elements de la liste
        itemnumber = len( self.currentItemList )
        
        # Titre de la categorie
        self.setProperty( "Category", self.curListType )

        cur_skin = xbmc.getSkinDir()
        for index, item  in enumerate( self.currentItemList ):
            if ( item.local_path == ROOTDIR ) or ( item.name == cur_skin ):
                label1 = item.name + " (Running)"
            else:
                label1 = item.name
            displayListItem = xbmcgui.ListItem( label1, "", thumbnailImage = item.thumb )
            self.getControl( self.CONTROL_MAIN_LIST ).addItem( displayListItem )

        #xbmcgui.unlock()

        #DIALOG_PROGRESS.close()

    def check_w_rights(self):
        """
        Verifie les droits en ecriture des repertoires principaux dont on a besoin
        """
        set_write_access = False
        if ( ( SYSTEM_PLATFORM == "linux" ) or ( SYSTEM_PLATFORM == "osx" ) ):
            # On fait un check rapide pour voir si on a les droit en ecriture
            for index, filterIdx in enumerate( self.rootDisplayList ):
                local_path=self.localdirList[ filterIdx ]
                if self.fileMgr.linux_is_write_access( local_path ):
                    # Au moins un element n'a pas les droit, on ne pas pas plus loin et on demande le mot de passe
                    set_write_access = True
                    break
                
            if ( set_write_access == True ):
                # On parcoure tous les repertoire et on met a jour les droits si besoin
                xbmcgui.Dialog().ok( _( 19 ), _( 20 ) )
                keyboard = xbmc.Keyboard( "", _( 21 ), True )
                keyboard.doModal()
                if keyboard.isConfirmed():
                    password = keyboard.getText()
                    for index, filterIdx in enumerate( self.rootDisplayList ):
                        local_path=self.localdirList[ filterIdx ]
                        if self.fileMgr.linux_is_write_access( local_path ):
                            self.fileMgr.linux_set_write_access( local_path, password )
        
        


def show_file_manager( mainwin ):
    """
    Affiche la fenetre du gestionnaire de fichier
    Merci a Frost pour l'algo
    """
    file_xml = "passion-FileMgr.xml"
    dir_path = os.getcwd().rstrip( ";" )
    #recupere le nom du skin et si force_fallback est vrai, il va chercher les images du defaultSkin.
    current_skin, force_fallback = getUserSkin() # Appel fonction dans Utilities

    w = FileMgrWindow( file_xml, dir_path, current_skin, force_fallback, mainwin=mainwin )
    w.doModal()
    del w