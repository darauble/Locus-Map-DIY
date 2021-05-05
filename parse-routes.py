import sys
import copy
import xml.etree.ElementTree as ET
import json

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

def sort_way(way):
	return int(way.attrib["id"])

if len(sys.argv) < 2:
	print("No arguments. Provide the .osm file to parse.")
	exit(-1)

name = sys.argv[1]

print("Loading XML to memory...")

t = ET.parse(name)
root = t.getroot()

print("...done")

way_dict = {}

print("Preparing a quick access dictionary of ways...")

for way in root:
	if way.tag == "way":
		way_dict[way.attrib["id"]] = way

print("...done")


print("Parsing relations...")

relations_tree = {}

for rel_type in REL_TYPES:
	relations_tree[rel_type] = []

orig_relations = []

for child in root:
	if child.tag == "relation":
		relation = {
			"name": "",
			"route": "",
			"network": "",
			"ways": []
		}

		for rel_child in child:
			if rel_child.tag == "member" and rel_child.attrib["type"] == "way":
				relation["ways"].append(rel_child.attrib["ref"])
			elif rel_child.tag == "tag":
				if rel_child.attrib["k"] == "name":
					relation["name"] = rel_child.attrib["v"]
				elif rel_child.attrib["k"] == "route" and rel_child.attrib["v"] in REL_TYPES:
					relation["route"] = rel_child.attrib["v"]
				elif rel_child.attrib["k"] == "network":
					relation["network"] = rel_child.attrib["v"]
				elif rel_child.attrib["k"] == "osmc:symbol":
					relation["osmc:symbol"] = rel_child.attrib["v"]
				elif rel_child.attrib["k"] == "ref":
					relation["ref"] = rel_child.attrib["v"]

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

		if relation["name"] != "" and relation["route"] != "" and relation["network"] != "":
			print("\tRelation:")
			print("\t\tname: %s" % relation["name"])
			print("\t\troute: %s" % relation["route"])
			print("\t\tnetwork: %s" % relation["network"])
			if "osmc:symbol" in relation:
				print("\t\tosmc:symbol: %s" % relation["osmc:symbol"])
			if "ref" in relation:
				print("\t\tref: %s" % relation["ref"])

			relations_tree[relation["route"]].append(relation)

		orig_relations.append(child)

print("\tFound relations:")

for relation_type in REL_TYPES:
	print("\t\t%s: %d" % (relation_type, len(relations_tree[relation_type])))

for child in orig_relations:
	root.remove(child)

print("...done")


print("Modifying and copying ways...")

new_ways = []

for relation_type in REL_TYPES:
	print("\tprocessing %s" % relation_type)

	modified_ways = 0

	for relation in relations_tree[relation_type]:
		for way_id in relation["ways"]:
			if way_id in way_dict:
				way = copy.deepcopy(way_dict[way_id])

				way.attrib["id"] = str(REL_CODE[relation["route"]] + NET_CODE[relation["network"][0]] + int(way.attrib["id"]))
				way_route = ET.SubElement(way, "tag")
				way_route.attrib["k"] = "route"
				way_route.attrib["v"] = relation["route"]

				way_network = ET.SubElement(way, "tag")
				way_network.attrib["k"] = "network"
				way_network.attrib["v"] = relation["network"]

				if "osmc:symbol" in relation:
					osmc = relation["osmc:symbol"].split(":")

					if len(osmc) >= 3:
						way_ocolor = ET.SubElement(way, "tag")
						way_ocolor.attrib["k"] = "osmc_color"
						way_ocolor.attrib["v"] = osmc[0]

						way_ocolor = ET.SubElement(way, "tag")
						way_ocolor.attrib["k"] = "osmc_background"
						way_ocolor.attrib["v"] = osmc[1]

						way_ocolor = ET.SubElement(way, "tag")
						way_ocolor.attrib["k"] = "osmc_foreground"
						way_ocolor.attrib["v"] = osmc[2]

				if "ref" in relation:
					way_ocolor = ET.SubElement(way, "tag")
					way_ocolor.attrib["k"] = "ref"
					way_ocolor.attrib["v"] = relation["ref"]

				new_ways.append(way)

				modified_ways = modified_ways + 1

print("...done, copied ways: %d" % modified_ways)

print("Sorting ways...")

new_ways.sort(key=sort_way)

root.append(new_ways[0])
for i in range(1, len(new_ways)):
	if new_ways[i].attrib["id"] != new_ways[i-1].attrib["id"]:
		root.append(new_ways[i])
		

print("...done")

print("Writing new XML to the disk...")

t.write(name+".xml")

print("...done. Please wait until script releases memory and exits on its own.")

