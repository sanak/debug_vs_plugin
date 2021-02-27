# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DebugVS
                                 A QGIS plugin
 Plugin to connect Visual Studio Remote Debugger
                             -------------------
        begin                : 2018-10-16
        copyright            : (C) 2018 by Luiz Motta
        email                : motta.luiz@gmail.com

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'Luiz Motta'
__date__ = '2018-10-16'
__copyright__ = '(C) 2018, Luiz Motta'
__revision__ = '$Format:%H$'


import os, sys
from past.builtins import execfile

from qgis.PyQt.QtCore import QObject, pyqtSlot
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QToolButton, QMenu, QAction, QFileDialog

from qgis.core import QgsApplication


def classFactory(iface):
  return DebugVSPlugin( iface )

class DebugVSPlugin( QObject ):

  def __init__(self, iface):
    super().__init__()
    self.iface = iface
    self.ptvsd = None
    try:
      import ptvsd
      self.ptvsd = ptvsd
    except:
      pass
    self.port = 5678
    self.host = 'localhost'
    self.actionsScript = []

    self.toolButton = QToolButton()
    self.toolButton.setMenu( QMenu() )
    self.toolButton.setPopupMode( QToolButton.MenuButtonPopup )
    self.toolBtnAction = self.iface.addToolBarWidget( self.toolButton )


    self.msgBar = iface.messageBar()
    self.pluginName = 'DebugVS'
    self.nameActionEnable = 'Enable Debug for Visual Studio'
    self.action = None
    # Check exist sys.argv - /ptvsd/.../pydevd_process_net_command
    if not hasattr(sys, 'argv'):
      sys.argv = []

  def initGui(self):
    # Action Run
    icon = QIcon( os.path.join( os.path.dirname(__file__), 'code.svg' ) )
    self.actionEnable = QAction( icon, self.nameActionEnable, self.iface.mainWindow() )
    self.actionEnable.setToolTip( self.nameActionEnable )
    self.actionEnable.triggered.connect( self.enable )
    self.iface.addPluginToMenu( f"&{self.nameActionEnable}" , self.actionEnable )
    # Action Load Script
    title = 'Load script'
    icon = QgsApplication.getThemeIcon('mActionScriptOpen.svg')
    self.actionLoad = QAction( icon, title, self.iface.mainWindow() )
    self.actionLoad.setToolTip( title )
    self.actionLoad.triggered.connect( self.load )
    self.iface.addPluginToMenu( f"&{self.nameActionEnable}" , self.actionLoad )
    #
    m = self.toolButton.menu()
    m.addAction( self.actionEnable )
    m.addAction( self.actionLoad )
    self.toolButton.setDefaultAction( self.actionEnable )

  def unload(self):
    for action in [ self.actionEnable, self.actionLoad ] + self.actionsScript:
        self.iface.removePluginMenu( f"&{self.nameActionEnable}", action )
        self.iface.removeToolBarIcon( action )
        self.iface.unregisterMainWindowAction(action)
    
    self.iface.removeToolBarIcon( self.toolBtnAction )

  def _addActionScript(self, filename):
    icon = QgsApplication.getThemeIcon('processingScript.svg')
    title = os.path.split( filename )[-1]
    action = QAction( icon, title, self.iface.mainWindow() )
    action.setToolTip( filename )
    action.triggered.connect( self.run )
    m = self.toolButton.menu()
    m.addAction( action )

    self.actionsScript.append( action )

  def _existsActionScript(self, filename):
    filenames = [ a.toolTip() for a in self.actionsScript ]
    return filename in filenames

  @pyqtSlot(bool)
  def enable(self, checked):
    self.msgBar.popWidget()
    if self.ptvsd is None:
      self.msgBar.pushCritical( self.pluginName, "Need install ptvsd: pip3 install ptvsd")
      return
    msgPort = f'"request": "attach", "Port": {self.port}, "host": "{self.host}"'
    if self.ptvsd.is_attached():
      self.msgBar.pushWarning( self.pluginName, f"Remote Debug for Visual Studio is active({msgPort})")
      return
    t_, self.port = self.ptvsd.enable_attach( address = ( self.host, self.port ) )
    msgPort = f'"request": "attach", "Port": {self.port}, "host": "{self.host}"'
    self.msgBar.pushInfo( self.pluginName, f"Remote Debug for Visual Studio is running({msgPort})")
    
  @pyqtSlot(bool)
  def load(self, checked):
    if not self.ptvsd.is_attached():
      self.msgBar.popWidget()
      msg = f"{self.nameActionEnable} AND attach in Visual Studio Code"
      self.msgBar.pushWarning( self.pluginName, self.nameActionEnable )
      return

    filename, _ = QFileDialog.getOpenFileName(None, 'Debug script', '','Python Files (*.py)' )
    if not filename:
        return

    self.ptvsd.wait_for_attach()
    execfile( filename )

    if not self._existsActionScript( filename ):
      self._addActionScript( filename )

  @pyqtSlot(bool)
  def run(self, checked):
    if not self.ptvsd.is_attached():
      msg = f"{self.nameActionEnable} AND attach in Visual Studio Code"
      self.msgBar.popWidget()
      self.msgBar.pushWarning( self.pluginName, msg )
      return

    action = self.sender()
    filename = action.toolTip()

    self.ptvsd.wait_for_attach()
    execfile( filename )
