# encoding: utf-8
from __future__ import division, print_function, unicode_literals

###########################################################################################################
#
#
#	General Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/General%20Plugin
#
#
###########################################################################################################

import objc
from AppKit import NSMenuItem
from GlyphsApp import Glyphs, VIEW_MENU, UPDATEINTERFACE, ONSTATE, OFFSTATE
from GlyphsApp.plugins import GeneralPlugin

MENU = VIEW_MENU
HOOKS = (UPDATEINTERFACE, )


class SyncTabs(GeneralPlugin):

	@objc.python_method
	def settings(self):
		self.name = Glyphs.localize({
			'en': 'Sync Tabs',
			'de': 'Tabs synchron halten',
			'fr': 'Synchroniser les onglets',
			'es': 'Sincronizar pestañas',
		})

	@objc.python_method
	def start(self):
		Glyphs.registerDefault("com.markfromberg.SyncTabs.state", False)

		self.menuItem = NSMenuItem(self.name, self.toggleSyncing_)
		Glyphs.menu[MENU].append(self.menuItem)

		self.setSyncState(Glyphs.boolDefaults["com.markfromberg.SyncTabs.state"])

	def __del__(self):
		self.setSyncState(False)

	def toggleSyncing_(self, sender=None):
		Glyphs.boolDefaults["com.markfromberg.SyncTabs.state"] = not Glyphs.boolDefaults["com.markfromberg.SyncTabs.state"]
		self.setSyncState(Glyphs.boolDefaults["com.markfromberg.SyncTabs.state"])

	@objc.python_method
	def setSyncState(self, state):
		try:
			if not state:
				for HOOK in HOOKS:
					Glyphs.removeCallback(self.syncEditViews_, callbackType=HOOK)
			else:
				for HOOK in HOOKS:
					Glyphs.addCallback(self.syncEditViews_, HOOK)
		except:
			import traceback
			print(traceback.format_exc())

		self.menuItem.setState_(ONSTATE if state else OFFSTATE)

	def syncEditViews_(self, sender=None):
		try:
			sourceFont = Glyphs.font
			sourceTab = sourceFont.currentTab
			if sourceTab and len(Glyphs.fonts) > 1:
				sourceMasterIndex = sourceFont.masterIndex
				sourceTool = sourceFont.tool
				sourceScale = sourceTab.scale
				sourceVisibleRect = sourceTab.viewPort
				sourceText = sourceTab.text
				sourceTextCursor = sourceTab.textCursor
				sourceTextRange = sourceTab.textRange
				sourceDoSpacing = sourceTab.graphicView().doSpacing()
				sourceDoKerning = sourceTab.graphicView().doKerning()
				sourceKerningMode = sourceTab.graphicView().kerningMode()

				for otherFont in Glyphs.fonts[1:]:
					if not otherFont.parent.windowForSheet().reallyVisible(): # Only apply to visible Fonts
						continue

					try:
						otherFont.masterIndex = sourceMasterIndex
					except:
						pass

					otherTab = otherFont.currentTab
					if not otherTab:
						otherTab = otherFont.newTab()

					otherView = otherTab.graphicView()

					if otherTab.text != sourceText or otherTab.textCursor != sourceTextCursor:
						try:
							otherTab.text = sourceText
							otherTab.textCursor = sourceTextCursor
							otherTab.textRange = sourceTextRange
						except:
							pass
						
						try:
							otherTab.graphicView().setDoSpacing_(sourceDoSpacing)
							otherTab.graphicView().setDoKerning_(sourceDoKerning)
							otherTab.graphicView().setKerningMode_(sourceKerningMode)
						except:
							pass

					try:
						otherFont.tool = sourceTool
					except:
						pass

					try:
						otherTab.viewPort = sourceVisibleRect
						# otherTab.graphicView().viewWillDraw()
						otherTab.scale = sourceScale
					except:
						pass
		except:
			import traceback
			print(traceback.format_exc())

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
