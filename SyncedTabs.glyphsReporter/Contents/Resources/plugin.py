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
#	> PREFERENCES:
#		+ change option to sync Tools: `Glyphs.defaults["com.markfromberg.syncedTabs.doSyncTools"] = True/False` in Macro panel
#
#	TODO: selectedLayerOrigin [https://docu.glyphsapp.com/#selectedLayerOrigin]
#	TODO: Make the same check for placeholder Layer as it is implemented for the newLine (GSControlLayer)
#	TODO: Add more observers
#	TODO: Keep Tools in sync as well?
#	TODO: Keep different Layers in sync (e.g. Show all Masters)
#
#	NOTES:
#		+ There was a sneaky bug that looked like it sometimes wont sync from one to another font
#		-> However, it was due to syncing into the last tab of the otherFont instead of the active one.
#		-> This is solved now by alwys syncing into the currentTab of the otherFont (see below at `*)`)
#
###########################################################################################################

from GlyphsApp.plugins import *
import traceback

version = "1.4"
vID = "com.markfromberg.syncedTabs" # vendorID

doSyncTools = False

# For the Observers
#------------------
currentGlyphName = ""
currentCaretPosition = None
currentZoom = None
currentViewPan = None
currentMasterIndex = 0
currentTool = None

newLine = "\n"

class SyncedTabs(ReporterPlugin):

	def settings(self):
		self.name = 'SyncedTabs'
		self.menuName = Glyphs.localize({'en': u'Synced Tabs'})
		#self.Glyphs = NSApplication.sharedApplication()
		
		# For the Observers
		#------------------
		self.activeGlyphChanged = False
		self.activeZoomChanged = False
		self.activeViewPanChanged = False
		self.activeMasterIndexChanged = False
		self.activeToolChanged = False


	def SyncEditViews(self):
		'''
		Based on the code from Tosche : `Sync Edit Views.py` @Github
		'''
		try:
			if Glyphs.defaults["%s.doSyncTools" % vID] == True:
				doSyncTools = True
			else:
				doSyncTools = False
		except: pass


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
			currentPreviewHeight = thisTab.previewHeight


			for otherFont in Glyphs.fonts:
				if otherFont != Glyphs.font:

					if otherFont.parent.windowForSheet().isVisible(): # Only apply to visible Fonts

						otherFontLastTool = otherFont.tool
						
						iTab = otherFont.currentTab # = otherFont.tabs[-1] # *) not syncing the last tab, but the currentTab

						#if mindex <= len(otherFont.masters):
						try:
							#print font0.parent.windowController().masterIndex(), otherFont.parent.windowController().masterIndex()
							iTab.setMasterIndex_(mindex)
						#if font0.parent.windowController().masterIndex() != otherFont.parent.windowController().masterIndex():
							otherFont.parent.windowController().setMasterIndex_(mindex)
						except: pass # print traceback.format_exc()

						otherView = iTab.graphicView()

						if otherView.scale() != thisScale:
							otherView.setScale_(thisScale)
						if otherView.doKerning() != doKern:
							otherView.setDoKerning_(doKern)
						if otherView.doSpacing() != doSpace:
							otherView.setDoSpacing_(doSpace)

						if self.activeGlyphChanged: # dont reset the content all the time. 
							# TODO: fix layer synconisation for views that where nevers synced. 
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
							# SET CARET INTO POSITION, 2 Step process
							# Step A: Catch the caret position
							otherFont.tool = "TextTool" # switch to tt to trigger glyphs view to focus
							otherView.textStorage().setSelectedRange_(thisSelection)

						## A)
						if doSyncTools:
							otherFont.tool = font0.tool
						else:
							otherFont.tool = otherFontLastTool

						## B) **UC**
						# if font0.parent.windowController().toolTempSelection():
						# 	otherFont.tool = 'SelectTool' 
						# else:
						# 	otherFont.tool = otherFontLastTool


						## C)
						# if doSyncTools:
						# 	if font0.parent.windowController().toolTempSelection().title() == "Hand":
						# 		otherFont.tool = "HandTool"
						# 		print "A Hand Tool"
						# 	else:
						# 		otherFont.tool = font0.tool
						# 		print "A Font0 Tool"
						# else:
						# 	if font0.parent.windowController().toolTempSelection().title() == "Hand":
						# 		otherFont.tool = "HandTool"
						# 		print "B Hand Tool"
						# 	else:
						# 		otherFont.tool = otherFontLastTool
						# 		print "B Font0 Tool"							



						# if iTab.previewHeight != currentPreviewHeight:
						iTab.previewHeight = currentPreviewHeight


						# Step B: Scroll to view if possible
						otherView.scrollRectToVisible_(currentVisibleRect) # new as proposed by WEI. Thanks!

		except:
			pass # print traceback.format_exc()



	# Observers
	#----------

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
				#print "Observe Glyph Change"
				self.activeGlyphChanged = True
				
			else:
				### If same glyph, check if position in tab (Otherwise changing from one /b to another in one tab wont trigger)
				position = layer.parent.parent.currentTab.graphicView().textStorage().selectedRange()
				if currentCaretPosition != position:
					currentCaretPosition = position
					self.activeGlyphChanged = True
					#print "Observe Glyph Change"
					return True
				### End: optional, but needed for this plugin

				self.activeGlyphChanged = False
				return False
		except:
			pass # print traceback.format_exc()



	def observeZoom(self):
		global currentZoom

		try:
			zoom = Glyphs.font.currentTab.scale
			if str(currentZoom) != str(zoom):
				currentZoom = zoom
				self.activeZoomChanged = True
				#print "Observe Zoom Change"
				return True
			else:
				self.activeZoomChanged = False
				return False
		except:
			pass # print traceback.format_exc()


	def observeMasterChange(self):
		global currentMasterIndex

		try:
			mIn = Glyphs.font.parent.windowController().masterIndex()
			if currentMasterIndex != mIn:
				currentMasterIndex = mIn
				self.activeMasterIndexChanged = True
				#print "Observe Master Change"
				return True
			else:
				self.activeMasterIndexChanged = False
				return False
		except:
			pass # print traceback.format_exc()



	def observeToolChange(self):
		global currentTool

		try:
			t = Glyphs.font.tool
			if currentTool != t:
				currentTool = t
				self.activeToolChanged = True
				#print "Observe Tool Change"
				return True
			else:
				self.activeToolChanged = False
				return False
		except:
			pass # print traceback.format_exc()



	#def observeMasterSwitch(self):
	## Perhaps not nessecary anymore? Seems to update already ...

	def observeViewPanning(self):
		global currentViewPan

		try:
			#viewPan = Glyphs.font.currentTab.graphicView().visibleRect().origin
			viewPan = Glyphs.font.currentTab.graphicView().visibleRect()
			if str(currentViewPan) != str(viewPan):
				currentViewPan = viewPan
				self.activeViewPanChanged = True
				#print "Observe Pan Change"
				return True
			else:
				self.activeViewPanChanged = False
				return False
		except:
			pass # print traceback.format_exc()






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



	#========
	# M A I N
	#========
	def foregroundInViewCoords(self, layer): # important to make the viewport (in drawKammerakindRahmen) work.

		self.observeGlyphChange()
		self.observeZoom()
		self.observeViewPanning()
		self.observeMasterChange()
		self.observeToolChange()

		if self.activeGlyphChanged or self.activeZoomChanged or self.activeViewPanChanged or self.activeMasterIndexChanged or self.activeToolChanged:
			self.SyncEditViews()


		if layer.parent.parent == Glyphs.font:
			self.drawKammerakindRahmen(layer.parent.parent)




