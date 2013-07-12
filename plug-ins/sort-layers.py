#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GIMP plugin to sort layers in the image or (a) selected group layer(s)
# (c) ShadowKyogre 2013
#
#   History:
#   2013-07-07 (v0.0): First published version
#   2013-07-07 (v0.1): Added sort by width, height, area, and regex sort functionality.
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

from gimpfu import *
import re

def getLinkedLayersRecurse(layer_or_image):
	candidates=[]
	for layer in layer_or_image.layers:
		if layer.linked:
			candidates.append(layer)
		if hasattr(layer, 'layers'):
			candidates.extend(getLinkedLayersRecurse(layer))
	return candidates

# add more sorting goodies

def sortLayers(image, in_rev, key_func):
	linked_candidates=list(filter(lambda x:hasattr(x, 'layers'), getLinkedLayersRecurse(image)))
	if len(linked_candidates) > 0:
		image.undo_group_start()
		for layer in linked_candidates:
			sorted_layers=sorted(layer.layers, key=key_func, reverse=in_rev)
			for n,item in enumerate(sorted_layers):
				pdb.gimp_image_reorder_item(image, item, layer, n)
		image.undo_group_end()
		gimp.displays_flush()
		return
	elif hasattr(image.active_layer, 'layers'):
		sorted_layers=sorted(image.active_layer.layers, key=key_func, reverse=in_rev)
		parent=image.active_layer
	else:
		parent=image.active_layer.parent
		if parent is None:
			sorted_layers=sorted(image.layers, key=key_func, reverse=in_rev)
		else:
			#note: There's a weird API inconsistency with GIMP group layers
			#since layer.children will list children layers
			#yet...doing parent.layers won't work since the parent 
			#won't automatically be a group layer type.
			sorted_layers=sorted(parent.children, key=key_func, reverse=in_rev)
	image.undo_group_start()
	for n,item in enumerate(sorted_layers):
		pdb.gimp_image_reorder_item(image, item, parent, n)
	image.undo_group_end()
	gimp.displays_flush()

def sortLayersByName(image, in_rev):
	sortLayers(image, in_rev, lambda x: x.name)

def sortLayersByWidth(image, in_rev):
	sortLayers(image, in_rev, lambda x: x.width)

def sortLayersByHeight(image, in_rev):
	sortLayers(image, in_rev, lambda x: x.height)

def sortLayersByArea(image, in_rev):
	sortLayers(image, in_rev, lambda x: x.height*x.width)

def sortLayersByNameRegex(image, regex, regex_sort, in_rev):
	expression=re.compile(regex)
	sortLayers(image, in_rev, lambda x: expression.search(x.name).expand(regex_sort))

### Registrations

SORT_BY_NAMES_PARAMS=(
	'sort-layers-by-name',
	'Sort Layers By Name',
	'Sort layers in the image or (a) selected group layer(s) by name',
	'ShadowKyogre',
	'ShadowKyogre',
	'2013',
	'By Name',
	'*',
	[
		(PF_IMAGE, 'image', 'Input image', None),
		(PF_TOGGLE, 'in_rev', 'Reverse the sort order?', False),
	],
	[],
	sortLayersByName
)

SORT_BY_NAMES_REGEX_PARAMS=(
	'sort-layers-by-name-regex',
	'Sort Layers By Name (Regex)',
	'Sort layers in the image or (a) selected group layer(s) by a regex on the layer names',
	'ShadowKyogre',
	'ShadowKyogre',
	'2013',
	'By Name (regex)',
	'*',
	[
		(PF_IMAGE, 'image', 'Input image', None),
		(PF_STRING, 'regex', 'Regular expression to grab groups', '(.*)'),
		(PF_STRING, 'regex_sort', 'The string with group references to use for sorting', r'\1'),
		(PF_TOGGLE, 'in_rev', 'Reverse the sort order?', False),
	],
	[],
	sortLayersByNameRegex
)

	
SORT_BY_WIDTH_PARAMS=(
	'sort-layers-by-width',
	'Sort Layers By Width',
	'Sort layers in the image or (a) selected group layer(s) by width',
	'ShadowKyogre',
	'ShadowKyogre',
	'2013',
	'By Width',
	'*',
	[
		(PF_IMAGE, 'image', 'Input image', None),
		(PF_TOGGLE, 'in_rev', 'Reverse the sort order?', False),
	],
	[],
	sortLayersByWidth
)

SORT_BY_HEIGHT_PARAMS=(
	'sort-layers-by-height',
	'Sort Layers By Height',
	'Sort layers in the image or (a) selected group layer(s) by height',
	'ShadowKyogre',
	'ShadowKyogre',
	'2013',
	'By Height',
	'*',
	[
		(PF_IMAGE, 'image', 'Input image', None),
		(PF_TOGGLE, 'in_rev', 'Reverse the sort order?', False),
	],
	[],
	sortLayersByHeight
)
	
SORT_BY_AREA_PARAMS=(
	'sort-layers-by-area',
	'Sort Layers By Area',
	'Sort layers in the image or (a) selected group layer(s) by area',
	'ShadowKyogre',
	'ShadowKyogre',
	'2013',
	'By Area',
	'*',
	[
		(PF_IMAGE, 'image', 'Input image', None),
		(PF_TOGGLE, 'in_rev', 'Reverse the sort order?', False),
	],
	[],
	sortLayersByArea
)

	
register(
	*SORT_BY_NAMES_PARAMS,
	menu='<Image>/Layer/Sort'
)

register(
	*SORT_BY_NAMES_REGEX_PARAMS,
	menu='<Image>/Layer/Sort'
)

register(
	*SORT_BY_WIDTH_PARAMS,
	menu='<Image>/Layer/Sort'
)

register(
	*SORT_BY_HEIGHT_PARAMS,
	menu='<Image>/Layer/Sort'
)

register(
	*SORT_BY_AREA_PARAMS,
	menu='<Image>/Layer/Sort'
)

main()

