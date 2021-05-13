import sys
import xml.etree.ElementTree as ET
import mmap
import re
import os

import tracemalloc

REL_TYPES = ["historic", "mtb", "bicycle", "foot", "hiking"]
REL_CODE = {
	"historic": 10000000000000000,
	"mtb": 20000000000000000,
	"bicycle": 30000000000000000,
	"foot": 40000000000000000,
	"hiking": 50000000000000000,
}

NET_CODE = {
	"r": 1000000000000000,
	"l": 2000000000000000,
	"n": 3000000000000000,
	"i": 4000000000000000,
}

HIKING_NETWORKS = ["rwn", "lwn", "nwn", "iwn"]
CYCLING_NETWORKS = ["rcn", "lcn", "ncn", "icn"]

def build_index(file_name, tag):
	print("Start building index on %s in %s..." % (tag, file_name))
	way_dict = {}
	search_id = re.compile("id=['\"](\d+)['\"]")
	way_count = 0

	with open(file_name, 'rb', 0) as f:
		search_pos = 0
		exit = False
		s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

		start_token = ('<%s' % tag).encode("utf-8")
		end_token = ('</%s>' % tag).encode("utf-8")

		while not exit:
			start = s.find(start_token, search_pos)
			tag_close = s.find(b'>', start + 4)
			way_id = search_id.search(s[start:tag_close+1].decode("utf-8"))

			if start != -1 and tag_close != -1:
				end = s.find(end_token, tag_close + 1)

				if end != -1:
					search_pos = end + len(tag) + 3

					if way_id:
						way_dict[way_id[1]] = { "start": start, "end": search_pos }
						way_count = way_count + 1

				else:
					exit = True
			else:
				exit = True

	print("... done, found %d tags" % way_count)
	return way_dict

def build_relations_tree(file_name, relations_dict):
	print("Start building relations tree on %s..." % file_name)
	relations_tree = {}

	for rel_type in REL_TYPES:
		relations_tree[rel_type] = []

	events = ("start", "end")
	start_relation = False

	with open(file_name, 'rb', 0) as f:
		s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

		for k, v in relations_dict.items():
			rel_xml_string = s[v["start"]:v["end"]].decode("utf-8")
			root = ET.fromstring(rel_xml_string)

			relation = {
				"name": "",
				"route": "",
				"network": "",
				"ways": []
			}

			for rel_child in root:
				if rel_child.tag == "member" and rel_child.attrib["type"] == "way":
					relation["ways"].append(rel_child.attrib["ref"])
				elif rel_child.tag == "tag":
					relation[rel_child.attrib["k"]] = rel_child.attrib["v"]
					#if rel_child.attrib["k"] == "name":
					#	relation["name"] = rel_child.attrib["v"]
					#elif rel_child.attrib["k"] == "route" and rel_child.attrib["v"] in REL_TYPES:
					#	relation["route"] = rel_child.attrib["v"]
					#elif rel_child.attrib["k"] == "network":
					#	relation["network"] = rel_child.attrib["v"]
					#elif rel_child.attrib["k"] == "osmc:symbol":
					#	relation["osmc:symbol"] = rel_child.attrib["v"]
					#elif rel_child.attrib["k"] == "ref":
					#	relation["ref"] = rel_child.attrib["v"]

			if relation["network"] not in HIKING_NETWORKS and relation["network"] not in CYCLING_NETWORKS:
				if relation["route"] == "hiking" or relation["route"] == "foot" or relation["route"] == "historic":
					if relation["network"] == "lt:regional":
						relation["network"] = "rwn"
					else:
						relation["network"] = "lwn"
				else:
					if relation["network"] == "lt:regional":
						relation["network"] = "rcn"
					else:
						relation["network"] = "lcn"

			if relation["name"] != "" and relation["route"] in REL_TYPES and relation["network"] != "":
				print("\tRelation:")
				print("\t\tname: %s" % relation["name"])
				print("\t\troute: %s" % relation["route"])
				print("\t\tnetwork: %s" % relation["network"])
				if "osmc:symbol" in relation:
					print("\t\tosmc:symbol: %s" % relation["osmc:symbol"])
				if "ref" in relation:
					print("\t\tref: %s" % relation["ref"])
				else:
					relation["ref"] = relation["name"]

				relations_tree[relation["route"]].append(relation)

			root.clear()
			root = None

	print("\tFound relations:")

	for relation_type in REL_TYPES:
		print("\t\t%s: %d" % (relation_type, len(relations_tree[relation_type])))

	print("...done")

	return relations_tree

def generate_ways(file_name, tmp_name, way_dict, relations_tree):
	print("Write temporary ways file %s..." % tmp_name)

	copied_ways = 0
	with open(file_name, "rb", 0) as r:
		ways_file = mmap.mmap(r.fileno(), 0, access=mmap.ACCESS_READ)

		with open(tmp_name, "wb") as w:
			for relation_type in REL_TYPES:
				print("\tprocessing %s" % relation_type)

				for relation in relations_tree[relation_type]:
					for way_id in relation["ways"]:
						if way_id in way_dict:
							way_entry = way_dict[way_id]
							way_xml_string = ways_file[way_entry["start"]:way_entry["end"]].decode("utf-8")
							way = ET.fromstring(way_xml_string)

							way_tags = []

							for way_elm in way:
								if way_elm.tag == "tag":
									way_tags.append(way_elm)

							for way_elm in way_tags:
								way.remove(way_elm)

							way.attrib["id"] = str(REL_CODE[relation["route"]] + NET_CODE[relation["network"][0]] + int(way.attrib["id"]))


							# Reverse direction of bicycle routes, so their colorization is on the opposite side of hiking route
							if relation["route"] == "bicycle" or relation["route"] == "mtb":
								way_nodes = []
								for node in way:
									if node.tag == "nd":
										way_nodes.append(node)

								for node in way_nodes:
									way.remove(node)

								for i in range(len(way_nodes)-1, -1, -1):
									way.append(way_nodes[i])

							for k, v in relation.items():
								if k == "osmc:symbol":
									osmc = relation["osmc:symbol"].split(":")

									way_ocolor = ET.SubElement(way, "tag")
									way_ocolor.attrib["k"] = "osmc_color"
									way_ocolor.attrib["v"] = osmc[0]
									way_ocolor.tail = "\n"

									way_ocolor = ET.SubElement(way, "tag")
									way_ocolor.attrib["k"] = "osmc_background"
									way_ocolor.attrib["v"] = osmc[1]
									way_ocolor.tail = "\n"

									way_ocolor = ET.SubElement(way, "tag")
									way_ocolor.attrib["k"] = "osmc_foreground"
									way_ocolor.attrib["v"] = osmc[2]
									way_ocolor.tail = "\n"
								elif k != "ways":
									way_tag = ET.SubElement(way, "tag")
									way_tag.attrib["k"] = k
									way_tag.attrib["v"] = v
									way_tag.tail = "\n"


							w.write(ET.tostring(way, encoding="utf-8"))
							copied_ways = copied_ways + 1

							way.clear()
							way = None

	print("..done, copied ways: %d" % copied_ways)
						

def sort_way_id(way_id):
	return int(way_id)

def sort_new_ways(file_name, tmp_name, final_name, new_way_dict):
	print("Sorting ways from %s..." % tmp_name)
	header = ""
	
	with open(file_name, "rb", 0) as f:
		s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

		bpos = s.find(b'<bounds', 0)

		if bpos != -1:
			bend = s.find(b'/>')
			if bend != -1:
				header = s[0:bend+2]
			else:
				print("\tcould not find file header (2)")
		else:
			print("\tcould not find file header (1)")

	way_id_list = [key for key in new_way_dict]

	way_id_list.sort(key=sort_way_id)

	print("\tsorted, now writing to the final file...")

	with open(tmp_name, "rb", 0) as r:
		ways_file = mmap.mmap(r.fileno(), 0, access=mmap.ACCESS_READ)

		with open(final_name, "wb") as w:
			w.write(header)

			way_entry = new_way_dict[way_id_list[0]]
			way_xml = ways_file[way_entry["start"]:way_entry["end"]]
			w.write(way_xml)

			for i in range(1, len(way_id_list)):
				if way_id_list[i] != way_id_list[i-1]:
					way_entry = new_way_dict[way_id_list[i]]
					way_xml = ways_file[way_entry["start"]:way_entry["end"]]
					w.write(way_xml)

			if header != "":
				w.write(b'</osm>')

	print("...done")

### Execution starts here ###
tracemalloc.start()

file_name = sys.argv[1]
tmp_name = "ways.tmp"
final_name = file_name + ".xml"

## Step 1 ##
way_dict = build_index(file_name, "way")

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB")

## Step 2 ##
rel_dict = build_index(file_name, "relation")

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB")

## Step 3 ##
rel_tree = build_relations_tree(file_name, rel_dict)

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB")

## Step 4 ##
generate_ways(file_name, tmp_name, way_dict, rel_tree)

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB")

## Step 5 ##
way_dict = None
rel_dict = None
rel_tree = None

new_way_dict = build_index(tmp_name, "way")

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB")

### Step 6 ###
sort_new_ways(file_name, tmp_name, final_name, new_way_dict)

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB")

os.remove(tmp_name)

tracemalloc.stop()

