//
//  MFSyncedTabs.m
//  Synced Tabs
//
//  Created by Georg Seifert on 27.03.19.
//Copyright © 2019 markfromberg. All rights reserved.
//

#import "MFSyncedTabs.h"
#import <GlyphsCore/GlyphsCore.h>
#import <GlyphsCore/GSComponent.h>
#import <GlyphsCore/GSFilterPlugin.h>
#import <GlyphsCore/GSFont.h>
#import <GlyphsCore/GSFontMaster.h>
#import <GlyphsCore/GSGlyph.h>
#import <GlyphsCore/GSWindowControllerProtocol.h>
#import <GlyphsCore/GSGlyphEditViewProtocol.h>
#import <GlyphsCore/GSGlyphViewControllerProtocol.h>
#import <GlyphsCore/GSLayer.h>
#import <GlyphsCore/GlyphsFilterProtocol.h>
#import <GlyphsCore/GSGeometrieHelper.h>

@interface NSApplication (private)
- (NSArray *)fontDocuments;
@end

@interface NSDocument (private)
- (GSFont *)font;
- (NSWindowController<GSWindowControllerProtocol>*) windowController;
@end

@interface NSView (private)
- (NSString *)displayString;
- (void)setDisplayString:(NSString *)displayString;
- (void)scrollPointToCentre:(NSPoint)aPoint;
@end

@interface NSViewController (private)
- (CGFloat)previewHeight;
- (void)setPreviewHeight:(CGFloat)previewHeight;
@end

static char *vID = "com.markfromberg.syncedTabs";

@implementation MFSyncedTabs {
	NSViewController<GSGlyphEditViewControllerProtocol>* _editViewController;
	BOOL _activeGlyphChanged;
	BOOL _activeZoomChanged;
	BOOL _activeViewPanChanged;
	BOOL _activeMasterIndexChanged;
	BOOL _activeToolChanged;
	
	NSString *_currentGlyphName;
	NSRange _currentCaretPosition;
	CGFloat _currentZoom;
	NSUInteger _currentMasterIndex;
	NSUInteger _currentToolIndex;
	NSRect _currentViewPan;
}

- (id)init {
	self = [super init];
	if (self) {
		// do stuff
	}
	return self;
}

- (void)loadPlugin {
	// Is called when the plugin is loaded.
}

- (NSUInteger)interfaceVersion {
	// Distinguishes the API verison the plugin was built for. Return 1.
	return 1;
}

- (NSString*)title {
	// This is the name as it appears in the menu in combination with 'Show'.
	// E.g. 'return @"Nodes";' will make the menu item read "Show Nodes".
	return @"Synced Tabs";

	// or localise it:
	// return NSLocalizedStringFromTableInBundle(@"TITLE", nil, [NSBundle bundleForClass:[self class]], @"DESCRIPTION");
}

- (void)syncEditViews {
	/*
	Based on the code from Tosche : `Sync Edit Views.py` @Github
	*/
	
	BOOL doSyncTools = [[NSUserDefaults standardUserDefaults] boolForKey:[NSString stringWithFormat:@"%s.doSyncTools", vID]];

	@try {
		GSFont *sourceFont = [_editViewController representedObject];
		NSUInteger sourceMasterIndex = _editViewController.masterIndex;
		
		CGFloat sourceScale = _editViewController.scale;
		NSRect sourceVisibleRect = [_editViewController.frameView visibleRect];
		NSPoint layerPos = [[_editViewController graphicView] activePosition];
		NSPoint layerCentre = NSMakePoint(NSMidX(sourceVisibleRect) - layerPos.x, NSMidY(sourceVisibleRect) - layerPos.y);
		
		CGFloat sourcePreviewHeight = [_editViewController previewHeight];
		
		NSView <GSGlyphEditViewProtocol> *sourceGraphicView = _editViewController.graphicView;
		NSRange sourceSelection = [sourceGraphicView selectedRange];
		BOOL doKern = [sourceGraphicView doKerning];
		BOOL doSpace = [sourceGraphicView doSpacing];
		
		NSArray *fontDocuments = [NSApp fontDocuments];
		
		NSString *displayString = [sourceGraphicView displayString];
		
		for (NSDocument *otherDoc in fontDocuments) {
			GSFont *otherFont = [otherDoc font];
		
			if (otherFont == sourceFont) {
				continue;
			}

			if (![[otherDoc windowForSheet] isVisible]) { // Only apply to visible Fonts
				continue;
			}
			NSLog(@"__sync %@", otherFont);
			
			NSUInteger otherFontLastToolIndex = [[otherDoc windowController] selectedToolIndex];
			
			NSViewController<GSGlyphEditViewControllerProtocol> *otherTab = [[otherDoc windowController] activeEditViewController];

			@try {
				otherTab.masterIndex = sourceMasterIndex;
			} @catch (NSException *exception) {
				// print traceback.format_exc()
			}
			NSView <GSGlyphEditViewProtocol> *otherView = [otherTab graphicView];
			if (_activeGlyphChanged) { // dont reset the content all the time.
				// TODO: fix layer synconisation for views that where nevers synced.
				//# verify glyph in font
				
//				normalizedText, currentLayers = [], []
//				for l in sourceTab.layers:
//					@try {
//						currentLayers.append(l.parent.name)
//					} @catch (NSException *exception) {
//						currentLayers.append(newLine)
//				for g in currentLayers: # for g in sourceTab.text:
//					if g != newLine:
//						if g in otherFont.glyphs:
//							normalizedText.append(g)
				//						} else {
//							normalizedText.append("space")
//					} else {
//						normalizedText.append(newLine)
//
//				normalizedText = "/" + "/".join([x for x in normalizedText])
				[otherView setDisplayString:displayString];
			}
			[otherView setSelectedRange:sourceSelection];
			otherTab.scale = sourceScale;
			if ([otherView doKerning] != doKern) {
				[otherView setDoKerning:doKern];
			}
			if ([otherView doSpacing] != doSpace) {
				[otherView setDoSpacing:doSpace];
			}
			
			// # A)
			if (doSyncTools) {
				//[[otherDoc windowController] setSelectedToolIndex:<#(NSUInteger)#> = sourceFont.tool;
			}
			else {
				//otherFont.tool = otherFontLastTool;
			}

			// //  B) **UC**
			//  if sourceFont.parent.windowController().toolTempSelection():
			//  	otherFont.tool = 'SelectTool'
			//  } else {
			//  	otherFont.tool = otherFontLastTool


			// # C)
			//  if doSyncTools:
			//  	if sourceFont.parent.windowController().toolTempSelection().title() == "Hand":
			//  		otherFont.tool = "HandTool"
			//  		print "A Hand Tool"
			//  	} else {
			//  		otherFont.tool = sourceFont.tool
			//  		print "A sourceFont Tool"
			//  } else {
			//  	if sourceFont.parent.windowController().toolTempSelection().title() == "Hand":
			//  		otherFont.tool = "HandTool"
			//  		print "B Hand Tool"
			//  	} else {
			//  		otherFont.tool = otherFontLastTool
			//  		print "B sourceFont Tool"

			if (fabs(otherTab.previewHeight - sourcePreviewHeight)) {
				[otherTab setPreviewHeight:sourcePreviewHeight];
			}

			//  Step B: Scroll to view if possible
			//otherTab.viewPort = sourceVisibleRect
			
			NSPoint otherLayerPos = [[otherTab graphicView] activePosition];
			NSPoint otherLayerCentre = NSMakePoint(otherLayerPos.x + layerCentre.x, otherLayerPos.y + layerCentre.y);
			
			[(NSView *)[otherTab frameView] scrollPointToCentre:otherLayerCentre];
			[otherView viewWillDraw];
		}
	}
	@catch (NSException *exception) {
		NSLog(@"exception %@", exception);
	}
}

- (void)observeGlyphChange {
	/*
	Catch the event: `active glyph was changed in the edit tab`.
	Convert to str() !!! otherwise they are pyobj objects.

	Calling the own layer here to make sure it is always the one from the active font.
	Otherwise, if passing in the `layer` as argument, the observer will always take the
	layer from each font during the loop. Hence it will endlessly loop into a glyphChangeObservation
	when a glyph is selected that doesnt appear in the other fonts.
	*/
//	global currentGlyphName
//	global currentCaretPosition

	//ff = Glyphs.font

	GSLayer *layer = [_editViewController activeLayer];

	@try {
		if (!layer) {
			if (_currentGlyphName) {
				_activeGlyphChanged = YES;
			}
			_currentGlyphName = nil;
			return;
		}
		NSString *thisGlyphName = layer.parent.name;
		if (nilEqual(_currentGlyphName, thisGlyphName)) {
			_currentGlyphName = thisGlyphName;
			// print "Observe Glyph Change"
			_activeGlyphChanged = YES;
		}
		else {
			// ## If same glyph, check if position in tab (Otherwise changing from one /b to another in one tab wont trigger)
			//  position = layer.parent.parent.currentTab.graphicView().textStorage().selectedRange() # deprecated
			NSRange position = [[_editViewController graphicView] selectedRange]; // new
			if (_currentCaretPosition.location != position.location || _currentCaretPosition.location != position.location) {
				_currentCaretPosition = position;
				_activeGlyphChanged = YES;
				// print "Observe Glyph Change"
				return;
			// ## End: optional, but needed for this plugin
			}
			_activeGlyphChanged = YES;
			return;
		}
	}
	@catch (NSException *exception) {
		// pass # print traceback.format_exc()
	}
}

- (void)observeZoom {
	//global currentZoom

	@try {
		CGFloat thisZoom = _editViewController.scale;
		if (fabs(_currentZoom - thisZoom) > 0.001) {
			_currentZoom = thisZoom;
			_activeZoomChanged = YES;
			// print "Observe Zoom Change"
			return;
		}
		else {
			_activeZoomChanged = NO;
			return;
		}
	}
	@catch (NSException *exception) {
		// pass # print traceback.format_exc()
	}
}

- (void)observeMasterChange {
	//global currentMasterIndex

	@try {
		NSUInteger thisMasterIndex = [_editViewController masterIndex];
		if (_currentMasterIndex != thisMasterIndex) {
			_currentMasterIndex = thisMasterIndex;
			_activeMasterIndexChanged = YES;
			// print "Observe Master Change"
			return;
		} else {
			_activeMasterIndexChanged = NO;
			return;
		}
	} @catch (NSException *exception) {
		//pass # print traceback.format_exc()
	}
}

- (void)observeToolChange {
	// global currentTool
	/*
	@try {
		NSUInteger thisToolIndex = Glyphs.font.tool;
		if currentTool != thisTool:
			currentTool = thisTool
			self.activeToolChanged = True
			// print "Observe Tool Change"
			return True
		}
		else {
			_activeToolChanged = NO;
			return
	} @catch (NSException *exception) {
		pass # print traceback.format_exc()
	}
	 */
}


//def observeMasterSwitch {
//# Perhaps not nessecary anymore? Seems to update already ...

- (void)observeViewPanning {
	//global currentViewPan

	@try {
		// thisViewPan = Glyphs.font.currentTab.graphicView().visibleRect().origin
		NSRect thisViewPan = [[_editViewController frameView] visibleRect];
		if (GSCompareRect(_currentViewPan, thisViewPan)) {
			_currentViewPan = thisViewPan;
			_activeViewPanChanged = YES;
			// print "Observe Pan Change"
			return;
		} else {
			_activeViewPanChanged = NO;
			return;
		}
	} @catch (NSException *exception) {
		// pass # print traceback.format_exc()
	}
}

- (void)drawForegroundWithOptions:(NSDictionary *)options {
	
	if (![[[_editViewController view] window] isMainWindow]) {
		return;
	}
	
	[self observeGlyphChange];
	[self observeZoom];
	[self observeViewPanning];
	[self observeMasterChange];
	[self observeToolChange];
	
	if (_activeGlyphChanged || _activeZoomChanged || _activeViewPanChanged || _activeMasterIndexChanged || _activeToolChanged) {
		[self syncEditViews];
	}
	
//	if (layer and layer.parent.parent == Glyphs.font) {
//		self.drawKammerakindRahmen(layer.parent.parent)
//	}
}

- (BOOL)needsExtraMainOutlineDrawingForInactiveLayer:(GSLayer*)Layer {
	return YES;
}

 - (NSViewController<GSGlyphEditViewControllerProtocol>*)controller {
	return _editViewController;
 }
			 
- (void)setController:(NSViewController<GSGlyphEditViewControllerProtocol> *)editViewController {
	_editViewController = editViewController;
}
@end
