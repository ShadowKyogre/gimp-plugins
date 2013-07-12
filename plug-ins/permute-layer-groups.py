#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GIMP plugin to export layer combination possibilities defined by groups
# (c) ShadowKyogre 2013
#
#   History:
#   2013-07-03 (v0.0): First published version
#   2013-07-03 (v0.1): Add getting combinations of layer groups
#   2013-07-07 (v0.2): Add specifying whether the layer groups inside a layer group
#                      are to have combinations calculated and which ones have other layers 
#                      in the same group are to be treated as items to be layered instead of separate
#                      possibilities. Also make use of GIMP's native dialogs for various file formats.
#                      Also fix bug for layers in the get group combos that weren't being retrieved for 
#                      layers that were generated in the dump.
#   2013-07-09 (v0.3): Use a more definitive check for checking if generated layers were put in dump images.
#                      Also make use of parasites for storing plugin settings.
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


"""
Notes:
	* New parasite: <object>.parasite_attach(name, flags, string) (flags should be PARASITE_PERSISTENT)
	* Update parasite data: <object>.parasite_detach(parasite.name);<object>.parasite_attach(parasite.name, parasite.flags, string)
"""

from gimpfu import *
from gimpui import gtk
import gimpui
import os
from itertools import product, chain
import re

REMOVE_TAGS=re.compile(r'\((prm|hasbg)\)')
REMOVE_EWHITESPACE=re.compile(' +')

def deleteAllLayers(image):
	for l in image.layers:
		image.remove_layer(l)

def group_layer_combos(layer, dump=None):
	target = pdb.gimp_image_new(layer.image.width, layer.image.height, RGB)
	if dump is None:
		#dummy image to hold child combinations
		dump = pdb.gimp_image_new(layer.image.width, layer.image.height, RGB)
		dump.disable_undo()
	target.disable_undo()

	src_lyrs=[]
	only_leaves=True
	for lyr in filter(lambda x: x.visible, layer.layers):
		#only consider children in the canditates for product if they are visible
		if hasattr(lyr,"layers") and '(prm)' in lyr.name:
			src_lyrs.append(group_layer_combos(lyr, dump=dump)[0])
			if '(hasbg)' in lyr.name:
				only_leaves=False
		else:
			src_lyrs.append([lyr])

	results=[]
	if only_leaves:
		#only leaves indicates we want some choices
		src_lyrs=chain.from_iterable(src_lyrs)
		possibilities=product(src_lyrs)
	else:
		possibilities=product(*src_lyrs)
	#Get permutations for the layer groups
	counter=0
	for prm in possibilities:
		#place the layers in the mixture into a brand spanking new image
		#print([item.name for item in prm])
		for idx,l in enumerate(reversed(prm)):
			n=pdb.gimp_layer_new_from_drawable(l,target)
			#print(layer, l.parent, l.name)
			target.add_layer(n,0)
			if l.image is dump:
				#we have a layer from the dump, get the appropriate blend mode
				#and opacity from the original layer group that was permuted
				n.mode=layer.layers[idx].mode
				n.opacity=layer.layers[idx].opacity*l.opacity/1E2

		#process!
		result=target.merge_visible_layers(EXPAND_AS_NECESSARY) #or CLIP_TO_IMAGE
		result_copy=pdb.gimp_layer_new_from_drawable(result,dump)
		
		#add this line to still allow the layer names for the other groupies
		if not only_leaves or layer.parent is not None:
			#workaround for now, probably implement a better work around later
			found_parasite = layer.parasite_find('permute-layer-groups-perm-format')
			#print(prm)
			if found_parasite is not None:
				newname=found_parasite.data[:-1].format(*prm,layer=layer,counter=counter)
				#print(newname)
				result_copy.name=newname
			else:
				newname=REMOVE_TAGS.sub("",layer.name)
				result_copy.name="{}.{}".format(REMOVE_EWHITESPACE.sub(" ",newname).strip(),counter)
			counter+=1
			#end workaround
		else:
			result_copy.name=result_copy.name.rstrip(" copy")
		results.append(result_copy)
		deleteAllLayers(target)
	pdb.gimp_image_delete(target)
	return results, dump

def permuteLayers(image, dirname, fnf, get_group_layer_combos):
	#image.undo_group_start()
	target = pdb.gimp_image_new(image.width, image.height, RGB)
	target.disable_undo()
	src_lyrs=[] # get all top lvl layer groups
	dumps=[]
	for lyr in filter(lambda x: x.visible, image.layers):
		#only consider children in the candidates for product if they are visible
		if hasattr(lyr,"layers"):
			if get_group_layer_combos:
				if '(prm)' in lyr.name:
					r=group_layer_combos(lyr)
					#return
					dumps.append(r[1])
					src_lyrs.append(r[0])
				else:
					src_lyrs.append([lyr])
			else:
				src_lyrs.append([l for l in lyr.layers if l.visible])
		else:
			src_lyrs.append([lyr])
	gotsettings=False
	run_mode=RUN_INTERACTIVE
	#Get permutations for the layer groups
	for prm in product(*src_lyrs):
		#place the layers in the mixture into a brand spanking new image
		for l in reversed(prm):
			n=pdb.gimp_layer_new_from_drawable(l,target)
			if l.parent is not None:
				n.mode=l.parent.mode
				n.opacity=l.parent.opacity*l.opacity/1E2
			target.add_layer(n,0)
		#process!
		expanded_fnf=fnf.format(*prm)
		fullname=os.path.join(dirname,expanded_fnf)
		if not os.path.exists(os.path.dirname(fullname)):
			os.makedirs(os.path.dirname(fullname))
		result=target.merge_visible_layers(EXPAND_AS_NECESSARY) #or CLIP_TO_IMAGE
		#gimp.message(expanded_fnf)
		pdb.gimp_file_save(target, 
				result, 
				fullname, 
				os.path.basename(fullname), 
				run_mode=run_mode)
		if not gotsettings:
			gotsettings=True
			run_mode=RUN_WITH_LAST_VALS
		deleteAllLayers(target)
	
	#clean up any dumps that were acquired if group_layer_combos was called
	for dump in dumps:
		deleteAllLayers(dump)
		pdb.gimp_image_delete(dump)
	pdb.gimp_image_delete(target)
	#image.undo_group_end()

class PermuteLayerSettingsWindow(gtk.Window):
	def __init__(self):
		gtk.Window.__init__(self)
		selector=gimpui.LayerComboBox()
		model=selector.get_model()
		layergroupsonly=model.filter_new()
		#del selector
		layergroupsonly.set_visible_func(self._visible_func)
		tv=gtk.TreeView()
		tv.set_model(layergroupsonly)

		cell = gtk.CellRendererText()
		pbcell = gtk.CellRendererPixbuf()
		tvcolumn = gtk.TreeViewColumn('Layer Name')
		tvcolumn.pack_start(pbcell, False)
		tvcolumn.pack_start(cell, True)
		tvcolumn.set_attributes(cell, text=1)
		tvcolumn.set_attributes(pbcell, pixbuf=3)
		tv.append_column(tvcolumn)
		
		cell2 = gtk.CellRendererText()
		parasite_view = gtk.TreeViewColumn('Permutation Format', cell2)
		parasite_view.set_cell_data_func(cell2, self._layer_perm_format_string)
		tv.append_column(parasite_view)
		cell2.set_property('editable', True)
		cell2.connect('edited', self._set_layer_perm_format_string, layergroupsonly)

		self.add(tv)
		tv.show()
		#[16, '-- permute-layer-groups-use-cases.xcf-1 / text shine-16', None, <gtk.gdk.Pixbuf object at 0x2a93910 (GdkPixbuf at 0x2c13450)>, None]

	def _visible_func(self, model, iter):
		layer=gimp._id2drawable(model[iter][0])
		return pdb.gimp_item_is_group(layer) == 1

	def _layer_perm_format_string(self, tvc, cell, model, iter):
		entry = model[iter]
		layer=gimp._id2drawable(entry[0])
		layer_parasite=layer.parasite_find('permute-layer-groups-perm-format')
		if layer_parasite is not None:
			cell.set_property('text',layer_parasite.data[:-1]) #remove the null character
		else:
			cell.set_property('text',"")
	
	def _set_layer_perm_format_string(self, cell, path, new_text, model):
		entry = model[path]
		layer=gimp._id2drawable(entry[0])
		layer.image.undo_group_start()
		if new_text is None or new_text == "":
			layer.parasite_detach('permute-layer-groups-perm-format')
		else:
			if layer.parasite_find('permute-layer-groups-perm-format') is not None:
				layer.parasite_detach('permute-layer-groups-perm-format')
			layer.attach_new_parasite('permute-layer-groups-perm-format', PARASITE_PERSISTENT|PARASITE_UNDOABLE, new_text)
		layer.image.undo_group_end()

def permuteLayerSettings(image):
	window=PermuteLayerSettingsWindow()
	window.connect("destroy", gtk.main_quit)
	window.show()
	gtk.main()

### Registrations
	
register(
	'permute-layer-groups',
	'Permute Layer Groups',
	'Save all possible permutations for each layer group combination to files',
	'ShadowKyogre',
	'ShadowKyogre',
	'2013',
	'Permute Layer Groups',
	'*',
	[
		(PF_IMAGE, 'image', 'Input image', None),
		(PF_DIRNAME, 'dirname', 'Output Directory', os.path.expanduser('~')),
		(PF_STRING, 'fnf', 'Filename format:\n'
						'Use {i.name} for the layer name picked out from the '
						'top level group.\n'
						'Numbers start at 0 from the topmost layer', 
						"{0.name}/{1.name}.png"),
		(PF_TOGGLE, 'get_group_layer_combos', 'Get combinations for subgroups?\n'
						'Note: This will only generate the combinations'
						' of groups with (prm) in the layer name. \nAnswering no'
						' will disable recursion for getting group layer combinations.', False),
	],
	[],
	permuteLayers,
	menu='<Image>/File/Save',
)


register(
	'permute-layer-groups-settings',
	'Permute Layer Groups Settings',
	'Set the permutation format string for your layer groups',
	'ShadowKyogre',
	'ShadowKyogre',
	'2013',
	'Permute Layer Group Settings',
	'*',
	[
		(PF_IMAGE, "image",  "Input image", None),
	],
	[],
	permuteLayerSettings,
	menu='<Image>/Image',
)

main()
