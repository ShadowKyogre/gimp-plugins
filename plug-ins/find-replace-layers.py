#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GIMP plugin to sort layers in the image or (a) selected group layer(s)
# (c) ShadowKyogre 2013
#
#   History:
#   2013-07-12 (v0.0): First published version
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
from xml.etree import ElementTree

# add more sorting goodies
def getTextFromTLayer(text_layer):
	string = pdb.gimp_text_layer_get_text(text_layer)
	if string is None:
		string = ''.join(ElementTree.fromstring(pdb.gimp_text_layer_get_markup(text_layer)).itertext())
	return string

def getLayersRecurse(layer_or_image, restrict_to_linked=False):
	candidates=[]
	for layer in layer_or_image.layers:
		if restrict_to_linked:
			if layer.linked:
				candidates.append(layer)
		else:
			candidates.append(layer)
		if hasattr(layer, 'layers'):
			candidates.extend(getLayersRecurse(layer,restrict_to_linked=restrict_to_linked))
	return candidates

def findReplaceLayers(image, find_this, replacement, count, case_sensitive, regex, text_or_name, restrict_to_linked):
	#prepare our regex
	flags=re.IGNORECASE if not case_sensitive else 0
	if regex:
		expression=re.compile(find_this, flags)
	else:
		expression=re.compile(re.escape(find_this), flags)
		replacement=re.escape(replacement) #find out how to do proper escaping here
	#retrieve possible candidates
	candidates=getLayersRecurse(image, restrict_to_linked=restrict_to_linked)
	if text_or_name:
		text_func=lambda x: getTextFromTLayer(x)
		filter_func=lambda x: pdb.gimp_item_is_text_layer(x) and expression.search(text_func(x))
		replace_func=pdb.gimp_text_layer_set_text
	else:
		text_func=lambda x: x.name
		filter_func=lambda x: expression.search(text_func(x))
		replace_func=pdb.gimp_layer_set_name
	if len(candidates) > 0:
		image.undo_group_start()
		for layer in filter(filter_func, candidates):
			newtxt=expression.sub(replacement, text_func(layer), count=int(count))
			replace_func(layer, newtxt)
		image.undo_group_end()
		gimp.displays_flush()
		return
	else:
		gimp.message("There were no layers that were eligible for the search and replace.")


### Registrations
	
register(
	'find-replace-layers',
	'Find and Replace Text or Layer Names',
	'Find and Replace Text or Layer Names',
	'ShadowKyogre',
	'ShadowKyogre',
	'2013',
	'Find and Replace Text or Layer Names',
	'*',
	[
		(PF_IMAGE, 'image', 'Input image', None),
		(PF_STRING, 'find_this', 'Find:', ''),
		(PF_STRING, 'replacement', 'Replace with:', ''),
		(PF_SPINNER, 'count', "Replace only these many occurances per layer (0 means replace all) on that layer.", 0, (0,  9999, 1)),
		(PF_TOGGLE, 'case_sensitive', 'Is the match case sensitive?', True),
		(PF_TOGGLE, 'regex', 'Is the search and replace a regular expression?', False),
		(PF_TOGGLE, 'text_or_name', 'Are we working with text layers?'
			' Answering no to this will mean we\'re working with layer names.'
			'\n Using this option also means that you understand that any markup'
			' used in the text won\'t be preserved.', False),
		(PF_TOGGLE, 'restrict_to_linked', 'Restrict the search and replace to linked layers?', False),
	],
	[],
	findReplaceLayers,
	menu='<Image>/Layer'
)

main()


