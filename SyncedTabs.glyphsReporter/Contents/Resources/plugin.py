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
#	TODO: Make the same check for placeholder Layer. Works different than it is implemented for the newLine (GSControlLayer)
#			print Font.currentTab
#			Font.newTab("abd/Placeholder a\nthis is") # <GSEditViewController abd/Placeholder a\nthis is>
#			-> only the newLine is a <GSControlLayer "newline"> <objective-c class GSControlLayer at 0x10e595510>
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
placeholder = "/Placeholder "

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



	def getSelectedRange(self):
		# new in Glyphs 2.3 or 2.4
		# https://forum.glyphsapp.com/t/selectedrange-stopped-working/7302
		self.graphicView = self.Doc.windowController().activeEditViewController().graphicView()
		Range = self.graphicView.selectedRange()
		return Range
		# Range = self.graphicView.selectedLayerRange()
		# return Range


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
			sourceFont = Glyphs.font
			sourceMasterIndex = sourceFont.masterIndex
			
			sourceTab = sourceFont.currentTab
			sourceScale = sourceTab.scale
			sourceVisibleRect = sourceTab.viewPort
			sourcePreviewHeight = sourceTab.previewHeight
			
			sourceGraphicView = sourceTab.graphicView()
			sourceSelection = sourceGraphicView.selectedRange()
			doKern = sourceGraphicView.doKerning()
			doSpace = sourceGraphicView.doSpacing()

			for otherFont in Glyphs.fonts:
				if otherFont == sourceFont:
					continue

				if not otherFont.parent.windowForSheet().isVisible(): # Only apply to visible Fonts
					continue

				otherFontLastTool = otherFont.tool
				
				otherTab = otherFont.currentTab

				try:
					otherFont.masterIndex = sourceMasterIndex
				except:
					pass # print traceback.format_exc()

				otherView = otherTab.graphicView()
				if self.activeGlyphChanged: # dont reset the content all the time. 
					# TODO: fix layer synconisation for views that where nevers synced.
					## verify glyph in font
					normalizedText, currentLayers = [], []
					for l in sourceTab.layers:
						try:
							currentLayers.append(l.parent.name)
						except:
							currentLayers.append(newLine)
					for g in currentLayers: # for g in sourceTab.text:
						if g != newLine:
							if g in otherFont.glyphs:
								normalizedText.append(g)
							else:
								normalizedText.append("space")
						else:
							normalizedText.append(newLine)
				
					normalizedText = "/" + "/".join([x for x in normalizedText])
					otherTab.text = normalizedText

				otherView.setSelectedRange_(sourceSelection)
				otherTab.scale = sourceScale
				if otherView.doKerning() != doKern:
					otherView.setDoKerning_(doKern)
				if otherView.doSpacing() != doSpace:
					otherView.setDoSpacing_(doSpace)
				
				## A)
				if doSyncTools:
					otherFont.tool = sourceFont.tool
				else:
					otherFont.tool = otherFontLastTool

				## B) **UC**
				# if sourceFont.parent.windowController().toolTempSelection():
				# 	otherFont.tool = 'SelectTool' 
				# else:
				# 	otherFont.tool = otherFontLastTool


				## C)
				# if doSyncTools:
				# 	if sourceFont.parent.windowController().toolTempSelection().title() == "Hand":
				# 		otherFont.tool = "HandTool"
				# 		print "A Hand Tool"
				# 	else:
				# 		otherFont.tool = sourceFont.tool
				# 		print "A sourceFont Tool"
				# else:
				# 	if sourceFont.parent.windowController().toolTempSelection().title() == "Hand":
				# 		otherFont.tool = "HandTool"
				# 		print "B Hand Tool"
				# 	else:
				# 		otherFont.tool = otherFontLastTool
				# 		print "B sourceFont Tool"

				# if otherTab.previewHeight != sourcePreviewHeight:
				otherTab.previewHeight = sourcePreviewHeight

				# Step B: Scroll to view if possible
				otherTab.viewPort = sourceVisibleRect
				otherView.viewWillDraw()

		except:
			print traceback.format_exc()



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

		ff = Glyphs.font

		layer = ff.currentTab.activeLayer()

		try:
			if not layer:
				if currentGlyphName:
					self.activeGlyphChanged = True
				currentGlyphName = None
				return
			thisGlyphName = str(layer.parent.name)
			if str(currentGlyphName) != thisGlyphName:
				currentGlyphName = thisGlyphName
				#print "Observe Glyph Change"
				self.activeGlyphChanged = True
				
			else:
				### If same glyph, check if position in tab (Otherwise changing from one /b to another in one tab wont trigger)
				# position = layer.parent.parent.currentTab.graphicView().textStorage().selectedRange() # deprecated
				position = layer.parent.parent.currentTab.graphicView().selectedRange() # new
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
			thisZoom = Glyphs.font.currentTab.scale
			if str(currentZoom) != str(thisZoom):
				currentZoom = thisZoom
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
			thisMasterIndex = Glyphs.font.parent.windowController().masterIndex()
			if currentMasterIndex != thisMasterIndex:
				currentMasterIndex = thisMasterIndex
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
			thisTool = Glyphs.font.tool
			if currentTool != thisTool:
				currentTool = thisTool
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
			#thisViewPan = Glyphs.font.currentTab.graphicView().visibleRect().origin
			thisViewPan = Glyphs.font.currentTab.graphicView().visibleRect()
			if str(currentViewPan) != str(thisViewPan):
				currentViewPan = thisViewPan
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


		if layer and layer.parent.parent == Glyphs.font:
			self.drawKammerakindRahmen(layer.parent.parent)




