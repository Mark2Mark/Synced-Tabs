# encoding: utf-8

###########################################################################################################
#
#
#	Reporter Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Reporter
#	
#	Based on the script [Sync Edit Views.py](https://github.com/Tosche/Glyphs-Scripts/blob/master/Sync%20Edit%20Views.py) by [Tosche](https://github.com/Tosche)
#	
#	> Keep all tabs in all open fonts in sync with the currently active tab.
#	> Set a /space in other tabs, when a certain glyph is not in these fonts.
#	> Handles newline characters.
#
#	TODO: selectedLayerOrigin [https://docu.glyphsapp.com/#selectedLayerOrigin]
#	TODO: Make the same check for placeholder Layer as it is implemented for the newLine (GSControlLayer)
#
#
###########################################################################################################

from GlyphsApp.plugins import *
import traceback

currentGlyphName = ""
currentCaretPosition = None
newLine = "\n"

class SyncTool(ReporterPlugin):

	def settings(self):
		self.name = 'SyncTool'
		self.menuName = Glyphs.localize({'en': u'Synced Tabs'})
		#self.Glyphs = NSApplication.sharedApplication()
		self.activeGlyphChanged = False


	def SyncEditViews(self):
		'''
		Based on the code from Tosche : `Sync Edit Views.py` @Github
		'''

		try:
			font0 = Glyphs.font
			thisTab = font0.currentTab
			thisMaster = font0.selectedFontMaster
			mindex = thisTab.masterIndex()
			currentGraphicView = thisTab.graphicView()
			thisScale = currentGraphicView.scale()
			doKern = currentGraphicView.doKerning()
			doSpace = currentGraphicView.doSpacing()
			thisSelection = currentGraphicView.textStorage().selectedRange()
			currentVisibleRect = currentGraphicView.visibleRect()

			for otherFont in Glyphs.fonts:
				if otherFont != Glyphs.font:
					otherFontLastTool = otherFont.tool
					iTab = otherFont.tabs[-1]
					if mindex <= len(otherFont.masters):
						iTab.setMasterIndex_(mindex)
					otherView = iTab.graphicView()
					otherView.setScale_(thisScale)
					otherView.setDoKerning_(doKern)
					otherView.setDoSpacing_(doSpace)
					
					## verify glyph in font
					normalizedText, currentLayers = [], []
					for l in thisTab.layers:
						try:
							currentLayers.append(l.parent.name)
						except:
							currentLayers.append(newLine)
					for g in currentLayers: # for g in thisTab.text:
						if g != newLine:
							if g in otherFont.glyphs:
								normalizedText.append(g)
							else:
								normalizedText.append("space")
						else:
							normalizedText.append(newLine)
					
					normalizedText = "/" + "/".join([x for x in normalizedText])
					iTab.text = normalizedText

					# SET CARET INTO POSITION
					# otherFont.tool = "TextTool" # switch to tt to trigger glyphs view to focus
					otherView.textStorage().setSelectedRange_(thisSelection)
					# otherFont.tool = otherFontLastTool
					otherView.scrollRectToVisible_(currentVisibleRect) # new as proposed by WEI. Thanks!

		except:
			pass # print traceback.format_exc()


	def observeGlyphChange(self):
		'''
		Catch the event: `active glyph was changed in the edit tab`.
		Convert to str() !!! otherwise they are pyobj objects.

		Calling the own layer here to make sure it is always the one from the active font.
		Otherwise, if passing in the `layer` as argument, the observer will always take the
		layer from each font during the loop. Hence it will endlessly loop into a glyphChangeObservation
		when a glyph is selected that doesnt appear in the other fonts.
		'''
		global currentGlyphName
		global currentCaretPosition

		try:
			layer = Glyphs.font.selectedLayers[0] #Glyphs.orderedDocuments()[0].font.selectedLayers[0]
			lName = str(layer.parent.name)			
			if str(currentGlyphName) != lName:
				currentGlyphName = lName
				self.activeGlyphChanged = True
				return True
			else:
				### If same glyph, check if position in tab (Otherwise changing from one /b to another in one tab wont trigger)
				position = layer.parent.parent.currentTab.graphicView().textStorage().selectedRange()
				if currentCaretPosition != position:
					currentCaretPosition = position
					self.activeGlyphChanged = True
					return True
				### End: optional, but needed for this plugin

				self.activeGlyphChanged = False
				return False
		except:
			pass #print traceback.format_exc()


	def drawKammerakindRahmen(self, thisFont):
		pass
		'''
		#sourceFontCurrentTab = Glyphs.font.currentTab
		sourceFontCurrentTab = thisFont.currentTab
		vp = sourceFontCurrentTab.viewPort
		NSColor.colorWithCalibratedRed_green_blue_alpha_( 0, 0.8, 0.2, 0.1 ).set()
		NSBezierPath.setLineWidth_(40)
		NSBezierPath.strokeRect_(vp) # NSBezierPath.fillRect_(vp)
		'''


	def foregroundInViewCoords(self, layer): # important to make the viewport (in drawKammerakindRahmen) work.
		self.observeGlyphChange()
		if self.activeGlyphChanged:
			self.SyncEditViews()

		if layer.parent.parent == Glyphs.font:
			self.drawKammerakindRahmen(layer.parent.parent)




