
#Modules general
import os
import sys
import shutil
import ftplib

#Other module
from threading import Thread

#modules XBMC
import xbmc
import xbmcgui

#modules custom
from utilities import *
from pil_util import makeThumbnails

#module logger
try:
    logger = sys.modules[ "__main__" ].logger
except:
    import script_log as logger


#FONCTION POUR RECUPERER LES LABELS DE LA LANGUE.
_ = sys.modules[ "__main__" ].__language__

DIALOG_PROGRESS = xbmcgui.DialogProgress()

BASE_THUMBS_PATH = os.path.join( sys.modules[ "__main__" ].SPECIAL_SCRIPT_DATA, "Thumbnails" )


class ItemDescription( xbmcgui.WindowXMLDialog ):
    # control id's
    CONTROL_DOWNLOAD_BUTTON     = 5
    CONTROL_REFRESH_BUTTON      = 6
    CONTROL_GET_THUMB_BUTTON    = 10
    CONTROL_PLAY_PREVIEW_BUTTON = 11
    CONTROL_CANCEL_BUTTON       = 12
    CONTROL_CANCEL2_BUTTON      = 303 # bouton mouse only

    # autre facon de recuperer tous les infos d'un item dans la liste.
    i_thumbnail       = xbmc.getInfoImage( "ListItem.Thumb" )
    i_previewPicture  = xbmc.getInfoImage( "ListItem.Property(fanartpicture)" )
    i_date            = unicode( xbmc.getInfoLabel( "ListItem.Property(date)" ), 'utf-8')
    i_title           = unicode( xbmc.getInfoLabel( "ListItem.Property(title)" ), "utf-8")
    i_added           = unicode( xbmc.getInfoLabel( "ListItem.Property(added)" ), 'utf-8')
    i_itemId          = unicode( xbmc.getInfoLabel( "ListItem.Property(itemId)" ), 'utf-8')
    i_author          = unicode( xbmc.getInfoLabel( "ListItem.Property(author)" ), 'utf-8')
    i_version         = unicode( xbmc.getInfoLabel( "ListItem.Property(version)" ), "utf-8")
    i_language        = unicode( xbmc.getInfoLabel( "ListItem.Property(language)" ), "utf-8")
    i_fileName        = unicode( xbmc.getInfoLabel( "ListItem.Property(fileName)" ), 'utf-8')
    i_type            = unicode( xbmc.getInfoLabel( "Container.Property(Category)" ), "utf-8")
    i_description     = unicode( xbmc.getInfoLabel( "ListItem.Property(description)" ), "utf-8")
    i_previewVideoURL = unicode( xbmc.getInfoLabel( "ListItem.Property(previewVideoURL)" ), 'utf-8')

    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self, *args, **kwargs )
        self.mainwin = kwargs[ "mainwin" ]
        self._set_skin_colours()

    def onInit( self ):
        # onInit est pour le windowXML seulement
        try:
            self._set_controls_labels()
        except:
            logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )

    def _set_controls_labels( self ):
        xbmcgui.lock()
        self.i_itemId = self.i_itemId or str( self.mainwin.getCurrentListPosition()+1 )
        try:
            self.getControl( 48 ).reset()
            listitem = xbmcgui.ListItem( self.i_title, "", self.i_thumbnail, self.i_thumbnail )
            listitem.setProperty( "type", self.i_type )
            listitem.setProperty( "date", self.i_date )#
            listitem.setProperty( "title", self.i_title )
            listitem.setProperty( "added", self.i_added )
            listitem.setProperty( "itemId", self.i_itemId )
            listitem.setProperty( "author", self.i_author )
            listitem.setProperty( "version", self.i_version )
            listitem.setProperty( "language", self.i_language )
            listitem.setProperty( "fileName", self.i_fileName )
            listitem.setProperty( "description", self.i_description or _( 604 ) )
            listitem.setProperty( "fanartpicture", self.i_previewPicture )
            listitem.setProperty( "previewVideoURL", self.i_previewVideoURL )
            self.getControl( 48 ).addItem( listitem )
        except:
            logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
        try:
            self.getControl( 49 ).reset()

            listitem = xbmcgui.ListItem( "ID", self.i_itemId or _( 612 ) )
            self.getControl( 49 ).addItem( listitem )

            listitem = xbmcgui.ListItem( _( 601 ), self.i_type or _( 612 ) )
            self.getControl( 49 ).addItem( listitem )

            listitem = xbmcgui.ListItem( _( 608 ), self.i_language or _( 612 ) )
            self.getControl( 49 ).addItem( listitem )

            listitem = xbmcgui.ListItem( _( 602 ), self.i_version or _( 612 ) )
            self.getControl( 49 ).addItem( listitem )

            listitem = xbmcgui.ListItem( _( 603 ), self.i_date or _( 612 ) )
            self.getControl( 49 ).addItem( listitem )

            listitem = xbmcgui.ListItem( _( 620 ), self.i_author or _( 612 ) )
            self.getControl( 49 ).addItem( listitem )

            listitem = xbmcgui.ListItem( _( 613 ), self.i_added or _( 612 ) )
            self.getControl( 49 ).addItem( listitem )

            listitem = xbmcgui.ListItem( _( 621 ), self.i_fileName or _( 612 ) )
            self.getControl( 49 ).addItem( listitem )

        except:
            logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
        xbmcgui.unlock()

    def get_item_infos( self, main_listitem ):
        try:
            self.i_date            = unicode( main_listitem.getProperty( "date" ), 'utf-8')
            self.i_added           = unicode( main_listitem.getProperty( "added" ), 'utf-8')
            self.i_title           = unicode( main_listitem.getProperty( "title" ), 'utf-8')
            self.i_itemId          = unicode( main_listitem.getProperty( "itemId" ), 'utf-8') or str( self.mainwin.getCurrentListPosition()+1 )
            self.i_author          = unicode( main_listitem.getProperty( "author" ), 'utf-8')
            self.i_version         = unicode( main_listitem.getProperty( "version" ), 'utf-8')
            self.i_language        = unicode( main_listitem.getProperty( "language" ), 'utf-8')
            self.i_fileName        = unicode( main_listitem.getProperty( "fileName" ), 'utf-8')
            self.i_description     = unicode( main_listitem.getProperty( "description" ), 'utf-8')
            self.i_previewPicture  = unicode( main_listitem.getProperty( "fanartpicture" ), 'utf-8')
            self.i_previewVideoURL = unicode( main_listitem.getProperty( "previewVideoURL" ), 'utf-8')
        except:
            logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )

    def _set_skin_colours( self ):
        #xbmcgui.lock()
        try:
            xbmc.executebuiltin( "Skin.SetString(PassionSkinColourPath,%s)" % ( self.mainwin.settings[ "skin_colours_path" ], ) )
            xbmc.executebuiltin( "Skin.SetString(PassionSkinHexColour,%s)" % ( ( self.mainwin.settings[ "skin_colours" ] or get_default_hex_color() ), ) )
        except:
            xbmc.executebuiltin( "Skin.SetString(PassionSkinHexColour,ffffffff)" )
            xbmc.executebuiltin( "Skin.SetString(PassionSkinColourPath,default)" )
            logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
        #xbmcgui.unlock()

    def onFocus( self, controlID ):
        #cette fonction n'est pas utiliser ici, mais dans les XML si besoin
        #Note: Mais il faut la declarer :)
        pass

    def onClick( self, controlID ):
        try:
            if controlID in ( self.CONTROL_CANCEL_BUTTON, self.CONTROL_CANCEL2_BUTTON ):
                # bouton quitter, on ferme le dialog
                self._close_dialog()
            elif controlID == self.CONTROL_DOWNLOAD_BUTTON:
                #bouton downlaod ou installer
                self.mainwin.install_add_ons()
            elif controlID == self.CONTROL_REFRESH_BUTTON:
                #bouton pour rafraichir l'item en temps reel ds le dialog et l'item de la liste en court
                self.getControl( 48 ).reset()
                self.getControl( 49 ).reset()
                main_listitem = self.mainwin.refresh_item()
                self.get_item_infos( main_listitem )
                self._set_controls_labels()
            elif controlID == self.CONTROL_GET_THUMB_BUTTON:
                #bouton pour choisir une vignette quand le add-ons est downloader
                #non utilise pour le moment (desactive)
                pass
            elif controlID == self.CONTROL_PLAY_PREVIEW_BUTTON:
                #bouton pour ecouter un add-ons si disponible
                #non utilise pour le moment (desactive)
                pass
            else:
                pass
        except:
            #import traceback; traceback.print_exc()
            logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )

    def onAction( self, action ):
        #( ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_CONTEXT_MENU, )
        if action in ( 9, 10, 117 ): self._close_dialog()

    def _close_dialog( self, OK=False ):
        #xbmc.sleep( 100 )
        self.close()


def show_description( mainwin ):
    """
    Affiche une fenetre contenant les informations sur un item
    """
    file_xml = "passion-ItemDescript.xml"
    #depuis la revision 14811 on a plus besoin de mettre le chemin complet, la racine suffit
    dir_path = os.getcwd().rstrip( ";" )
    #recupere le nom du skin et si force_fallback est vrai, il va chercher les images du defaultSkin.
    current_skin, force_fallback = getUserSkin()

    #TODO: ajouter check si infoWarehouse n'a pas ete cree

    w = ItemDescription( file_xml, dir_path, current_skin, force_fallback, mainwin=mainwin )
    w.doModal()
    del w