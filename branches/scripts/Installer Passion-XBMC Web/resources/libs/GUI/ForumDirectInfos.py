﻿
#Modules general
import os
import re
import sys
import urllib
from StringIO import StringIO
from traceback import print_exc

import elementtree.HTMLTreeBuilder as HTB


#modules XBMC
import xbmc
import xbmcgui

#modules custom
import PassionXBMC
from utilities import *
from convert_utc_time import set_local_time

#module logger
try:
    logger = sys.modules[ "__main__" ].logger
except:
    import script_log as logger


SPECIAL_TEMP_DIR = sys.modules[ "__main__" ].SPECIAL_TEMP_DIR

DIALOG_PROGRESS = xbmcgui.DialogProgress()

#FONCTION POUR RECUPERER LES LABELS DE LA LANGUE.
_ = sys.modules[ "__main__" ].__language__

DIRECT_INFOS = "http://passion-xbmc.org%s/?action=.xml;type=rss;limit=" #max 100

EXCLUDE_IMGS = re.compile( "smiley|imagesonboard" ).search


def load_infos( url, onerror=True ):
    try:
        #html = urllib.urlopen( url )
        html = PassionXBMC.get_page( url )
        source = re.sub( "<!\[CDATA\[|\]\]>", "", html )#.read() )
        #html.close()
        return HTB.parse( StringIO( source ), "utf-8"  ).findall( "channel" )[ 0 ]
    except:
        if onerror:
            print_exc()
            #logger.EXC_INFO( logger.LOG_DEBUG, sys.exc_info() )
        # si on arrive ici le retour est automatiquement None



class DirectInfos( xbmcgui.WindowXML ):
    # control id's
    CONTROL_RSS_LIST = 150
    CONTROL_FEEDS_LIST = 191

    TOPIC_LIMIT = [ "5", "10", "15", "20", "25", "50", "100" ]

    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXML.__init__( self, *args, **kwargs )
        self.is_started = True
        self.rss_id = 0

    def onInit( self ):
        try:
            self._get_settings()
            self._set_skin_colours()
            if self.is_started:
                self.is_started = False

                DIALOG_PROGRESS.create( _( 199 ), _( 239 ), _( 110 ) )
                self.set_user_authentification()
                self.set_list_container_150()
                self.set_list_container_191()
        except:
            print_exc()#logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
        DIALOG_PROGRESS.close()

    def _get_settings( self, defaults=False ):
        """ reads settings """
        self.settings = Settings().get_settings( defaults=defaults )

        self.topics_limit = self.settings[ "topics_limit" ]

        try:
            for limit in self.TOPIC_LIMIT:
                self.getControl( 9003 ).addItem( xbmcgui.ListItem( "Limite:", limit ) )
            pos = self.TOPIC_LIMIT.index( self.topics_limit )
            self.getControl( 9003 ).selectItem( pos )
        except:
            print_exc()

    def _set_skin_colours( self ):
        #xbmcgui.lock()
        try:
            xbmc.executebuiltin( "Skin.SetString(PassionSkinColourPath,%s)" % ( self.settings[ "skin_colours_path" ], ) )
            xbmc.executebuiltin( "Skin.SetString(PassionSkinHexColour,%s)" % ( ( self.settings[ "skin_colours" ] or get_default_hex_color() ), ) )
        except:
            xbmc.executebuiltin( "Skin.SetString(PassionSkinHexColour,ffffffff)" )
            xbmc.executebuiltin( "Skin.SetString(PassionSkinColourPath,default)" )
            print_exc()#logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
        #xbmcgui.unlock()

    def set_user_authentification( self, connect=False ):
        self.connexion = None
        try:
            self.getControl( 200 ).setLabel( "Connect" )
            self.getControl( 200 ).setSelected( False )
            self.getControl( 201 ).setLabel( "Message(s)" )
            self.getControl( 201 ).setVisible( False )
        except:
            pass
        if connect: self.pseudo, self.connexion, self.avatar, self.mp = PassionXBMC.Connect()
        else: self.pseudo, self.connexion, self.avatar, self.mp = PassionXBMC.IsAuthenticated()
        if self.connexion:
            if self.mp == 0: notif = "Bonjour %s,Vous êtes connecté !,5000,%s" % ( self.pseudo, self.avatar, )
            else: notif = "Bonjour %s,Vous avez %i message !,5000,%s"  % ( self.pseudo, self.mp, self.avatar, )
            xbmc.executebuiltin( "XBMC.Notification(%s)" % notif )
            try:
                self.getControl( 200 ).setLabel( self.pseudo )
                self.getControl( 200 ).setSelected( bool( self.connexion ) )
            except:
                pass
            try:
                self.getControl( 201 ).setVisible( True )
                if ( self.mp > 0 ):
                    self.getControl( 201 ).setLabel( "Message(s) [%i]" % self.mp )
            except:
                pass

    def set_list_container_150( self ):
        self.new_list_container_150 = []
        self.getControl( self.CONTROL_RSS_LIST ).reset()
        txt = os.path.join( os.getcwd(), "resources", "forum_links.txt" )
        f = open( txt, "r" )
        for line in f.readlines():
            if line.startswith( "##" ):
                rss = line.strip( "# " + os.linesep ).split( ", " )
                link = rss[ 1 ]
                icon = rss[ 2 ].split( " + " )
                if ( len( icon ) == 2 ) and ( not load_infos( link, False ) ):
                    continue
                labels = rss[ 0 ].split( " | " )
                label1 = labels[ 1 ]
                label2 = labels[ 0 ]
                self.getControl( self.CONTROL_RSS_LIST ).addItem( xbmcgui.ListItem( label1, label2, icon[ 0 ], icon[ 0 ] ) )
                self.new_list_container_150.append( ( label2, label1, link, icon[ -1 ] ) )

    def set_list_container_191( self ):
        try:
            cat, section, url, icone = self.new_list_container_150[ self.rss_id ]
            self.category = cat + " - " + section

            if not xbmc.getCondVisibility( "Window.IsActive(progressdialog)" ):
                DIALOG_PROGRESS.create( _( 199 ), self.category, _( 239 ), _( 110 ) )
            try:
                has_new_limit = self.getControl( 9003 ).getSelectedItem().getLabel2()
                if int( has_new_limit ) != int( self.topics_limit ):
                    self.topics_limit = self.settings[ "topics_limit" ] = has_new_limit
                    OK = Settings().save_settings( self.settings )
            except:
                print_exc()
            url += ";limit=" + self.topics_limit
            root = load_infos( url )
            if root is not None:
                self.setProperty( "Category", self.category )
                items = root.findall( "item" )

                self.list_infos = list()
                total_items = len( items ) or 1
                diff = ( 100.0 / total_items )
                percent = 0

                self.getControl( self.CONTROL_FEEDS_LIST ).reset()
                for count, item in enumerate( items ):
                    percent += diff
                    imgs = set()
                    slideshow = ""
                    try:
                        title = item.findtext( "title" ).replace( u'\xa0', " " )
                        pubdate = set_local_time( item.findtext( "pubdate" ) )
                        guid = item.findtext( "guid" )
                        _desc = item.find( "description" )
                        description = " ".join( [ ( _desc.text or "" ), ( _desc.tail or "" ) ] ).replace( '&nbsp;', "    " ).replace( "\t", "" ).strip()

                        for txt in _desc.getchildren():
                            _text = " ".join( [ ( txt.text or "" ), ( txt.tail or "" ) ] ).replace( '&nbsp;', "    " ).replace( "\t", "" ).strip()
                            if txt.tag == "br":
                                if txt.text == txt.tail: _text = "\n"
                                else: _text = "\n" + _text
                            elif txt.tag == "b":
                                _text = bold_text( _text )
                            elif txt.tag == "i":
                                _text = italic_text( _text )
                            elif txt.tag in ( "img", "a" ):
                                img = txt.attrib.get( "src", "" ) or txt.attrib.get( "href", "" )
                                if not EXCLUDE_IMGS( img.lower() ) and is_playable_media( img ):
                                    imgs.update( [ img ] )
                                    slideshow = "true"

                            description += _text
                        description = set_xbmc_carriage_return( description.strip( "\r\n" ) )
                        general_category = ""
                        if ( self.rss_id == 0 ):
                            # pour la page general seulement
                            general_category = item.findtext( "category" )
                    except:
                        print_exc()#logger.EXC_INFO( logger.LOG_DEBUG, sys.exc_info(), self )
                    else:
                        DIALOG_PROGRESS.update( int( percent ), "Topic: %i / %i" % ( count + 1, total_items, ), title )
                        listitem = xbmcgui.ListItem( title, pubdate, icone, icone )
                        listitem.setProperty( "general_category", general_category )
                        listitem.setProperty( "Topic", description )
                        listitem.setProperty( "Slideshow", slideshow )
                        self.getControl( self.CONTROL_FEEDS_LIST ).addItem( listitem )
                        self.list_infos.append( ( guid, list( imgs ) ) )

                self.setFocusId( self.CONTROL_FEEDS_LIST )
            else:
                xbmcgui.Dialog().ok( _( 199 ), self.category, _( 240 ) )
        except:
            print_exc()#logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
            xbmcgui.Dialog().ok( _( 199 ), self.category, _( 241 ) )
        DIALOG_PROGRESS.close()

    def set_list_container_191_for_pm( self ):
        try:
            #[( auteur_avatar, auteur, title, date, isread, message )]
            MP = PassionXBMC.getMP()
            if bool( MP ):
                self.category = "Messages personnels"
                self.setProperty( "Category", self.category )

                self.list_infos = list()
                total_items = len( MP ) or 1
                diff = ( 100.0 / total_items )
                percent = 0

                self.getControl( self.CONTROL_FEEDS_LIST ).reset()
                for count, mp in enumerate( MP ):
                    percent += diff
                    imgs = set()
                    slideshow = ""
                    try:
                        auteur_avatar, auteur, title, date, isread, message = mp
                        for img in re.findall( '<a href=".*?" rel="highslide"><img src="(.*?)" alt="" width=".*?" height=".*?" border=".*?" /></a>', message, re.DOTALL ):
                            if img and not EXCLUDE_IMGS( img.lower() ) and is_playable_media( img ):
                                imgs.update( [ img ] )
                                slideshow = "true"
                        #print message.encode( "ISO-8859-1" )
                        #print
                        #message = re.sub( "(?s)<[^>]*>", "", message )
                    except:
                        print_exc()
                    else:
                        DIALOG_PROGRESS.update( int( percent ), "MP: %i / %i" % ( count + 1, total_items, ), title )
                        listitem = xbmcgui.ListItem( auteur + " - " + title, date, auteur_avatar, auteur_avatar )
                        listitem.setProperty( "Topic", message )
                        listitem.setProperty( "Slideshow", slideshow )
                        listitem.setProperty( "general_category", "" )
                        self.getControl( self.CONTROL_FEEDS_LIST ).addItem( listitem )
                        self.list_infos.append( ( None, list( imgs ) ) )

                self.setFocusId( self.CONTROL_FEEDS_LIST )
            else:
                xbmcgui.Dialog().ok( "Passion-XBMC", "%i Messages personnels de récuéper!" % len( MP ), "Respirez à fond et refaites un essai [B]:)[/B]" )
        except:
            print_exc()
            xbmcgui.Dialog().ok( "Passion-XBMC", "Respirez à fond et refaites un essai [B]:)[/B]" )
        DIALOG_PROGRESS.close()

    def onFocus( self, controlID ):
        #cette fonction n'est pas utiliser ici, mais dans les XML si besoin
        pass

    def onClick( self, controlID ):
        try:
            if controlID == self.CONTROL_RSS_LIST:
                pos = self.getControl( self.CONTROL_RSS_LIST ).getSelectedPosition()
                if pos >= 0:
                    self.rss_id = pos
                    self.set_list_container_191()
            elif controlID == self.CONTROL_FEEDS_LIST:
                pos = self.getControl( self.CONTROL_FEEDS_LIST ).getSelectedPosition()
                if pos >= 0:
                    self._url_launcher( self.list_infos[ pos ][ 0 ] )
            elif controlID == 200:
                if self.connexion:
                    notif = "Passion-XBMC,Au Revoir %s,5000,%s" % ( self.pseudo, self.avatar, )
                    self.pseudo, self.connexion, self.avatar, self.mp = PassionXBMC.Disconnect()
                    if not self.connexion:
                        self.getControl( 200 ).setLabel( "Connect" )
                        self.getControl( 200 ).setSelected( False )
                        self.getControl( 201 ).setLabel( "Message(s)" )
                        self.getControl( 201 ).setVisible( False )
                        xbmc.executebuiltin( "XBMC.Notification(%s)" % notif )
                else:
                    self.set_user_authentification( True )
                DIALOG_PROGRESS.create( _( 199 ), _( 239 ), _( 110 ) )
                self.rss_id = 0
                self.set_list_container_150()
                self.set_list_container_191()
            elif controlID == 201:
                DIALOG_PROGRESS.create( "Passion-XBMC", "Messages personnels...", _( 110 ) )
                self.set_list_container_191_for_pm()
            elif controlID == 5:
                self.set_list_container_191()
            else:
                pass
        except:
            print_exc()#logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
            DIALOG_PROGRESS.close()

    def _url_launcher( self, url ):
        if not url: return
        if ( not SYSTEM_PLATFORM in ( "windows", "linux", "osx" ) ):
            logger.LOG( logger.LOG_INFO, "Unsupported platform: %s", SYSTEM_PLATFORM )
            return
        try:
            if not self.settings[ "web_navigator" ]:
                web_navigator = set_web_navigator( self.settings[ "web_navigator" ] )
                if web_navigator:
                    self.settings[ "web_title" ] = web_navigator[ 0 ] # utiliser dans le dialog settings
                    self.settings[ "web_navigator" ] = web_navigator[ 1 ]
                    OK = Settings().save_settings( self.settings )

            if self.settings[ "win32_exec_wait" ] and ( SYSTEM_PLATFORM == "windows" ):
                # Execute shell commands and freezes XBMC until shell is closed
                cmd = "System.ExecWait"
            else:
                # cette commande semble fonctionel pour linux, osx and windows
                # Execute shell commands
                cmd = "System.Exec"

            command = None
            if ( SYSTEM_PLATFORM == "windows" ):
                command = '%s("%s" "%s")' % ( cmd, self.settings[ "web_navigator" ], url, )
            else:#if ( SYSTEM_PLATFORM == "linux" ):
                # sous linux la vigule pose probleme. solution obtenir la redirection de l'url
                url = self.get_redirected_url( url )
                command = '%s(%s %s)' % ( cmd, self.settings[ "web_navigator" ], url, )

            if command is not None:
                logger.LOG( logger.LOG_DEBUG, "Url Launcher: %s", command )
                selected_label = self._unicode( self.getControl( self.CONTROL_FEEDS_LIST ).getSelectedItem().getLabel() )
                if xbmcgui.Dialog().yesno( self.settings[ "web_title" ], _( 236 ), selected_label, url.split( "/" )[ -1 ], _( 237 ), _( 238 ) ):
                    try:
                        xbmc.executebuiltin( command )
                    except:
                        os.system( "%s %s" % ( web_navigator, url, ) )

        except:
            print_exc()#logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )

    def get_redirected_url( self, url ):
        from urllib2 import urlopen
        from urlparse import urlparse, urlunparse
        try:
            redirection = urlopen( url ).geturl()
            scheme1, host1, path1, params1, query1, fragment1 = urlparse( url )
            scheme2, host2, path2, params2, query2, fragment2 = urlparse( redirection )
            url = urlunparse( ( scheme2, host2, path2, params2, None, fragment1 ) )
        except:
            print_exc()#logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )
        del urlopen, urlparse, urlunparse
        return url

    def _unicode( self, s, encoding="utf-8" ):
        try: s = unicode( s, encoding )
        except: pass
        return s

    def onAction( self, action ):
        #( ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_CONTEXT_MENU, )
        if action in ( 9, 10, 117, ): self._close_dialog()
        # show slideshow
        if action == 11:
            try:
                pos = self.getControl( self.CONTROL_FEEDS_LIST ).getSelectedPosition()
                if pos >= 0:
                    screens = self.list_infos[ pos ][ 1 ]
                    if screens and len( screens ) == 1:
                        xbmc.executehttpapi( "ShowPicture(%s)" % ( screens[ 0 ], ) )
                    elif screens:
                        m3u = os.path.join( SPECIAL_TEMP_DIR, "passion_slideshow.m3u" )
                        f = open( m3u, "w+" )
                        f.write( "#EXTM3U" )
                        for count, screen in enumerate( screens ):
                            f.write( "\n#EXTINF:0,%i - %s\n%s" % ( ( count + 1 ), os.path.basename( screen ), screen, ) )
                        f.close()
                        xbmc.executehttpapi( "PlaySlideshow(%s;false)" % ( m3u, ) )
            except:
                print_exc()#logger.EXC_INFO( logger.LOG_ERROR, sys.exc_info(), self )

    def _close_dialog( self ):
        #xbmc.sleep( 100 )
        self.close()


def show_direct_infos():
    dir_path = os.getcwd().rstrip( ";" )
    #recupere le nom du skin et si force_fallback est vrai, il va chercher les images du defaultSkin.
    current_skin, force_fallback = getUserSkin()
    file_xml = ( "IPX-DirectInfos.xml", "passion-DirectInfos.xml" )[ current_skin != "Default.HD" ]

    w = DirectInfos( file_xml, dir_path, current_skin, force_fallback )
    w.doModal()
    del w
