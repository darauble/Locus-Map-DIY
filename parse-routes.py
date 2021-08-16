import osmium
import os
import sys

REL_TYPES = ["historic", "mtb", "bicycle", "foot", "hiking"]
HIKING_NETWORKS = ["rwn", "lwn", "nwn", "iwn"]
CYCLING_NETWORKS = ["rcn", "lcn", "ncn", "icn"]

all_ways = {}

class RelationsHandler(osmium.SimpleHandler):
	def __init__(self, all_ways):
		osmium.SimpleHandler.__init__(self)
		self.all_ways = all_ways

	def relation(self, r):
		if "route" in r.tags and r.tags.get("route") in REL_TYPES:
			#print("Relation:")

			relation = {
				"name": "",
				"route": "",
				"network": "",
			}

			for k, v in r.tags:
				#print("\t", k, "=", v)
				relation[k] = v

			#print("\t", r.members)

			for m in r.members:
				#print(m.type)
				if m.type == "w":
					#print("\tway: %s" % m.ref)
					if m.ref not in self.all_ways:
						self.all_ways[m.ref] = []
					self.all_ways[m.ref].append(relation)

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


			if relation["name"] != "" and relation["network"] != "":
				print("\tRelation:")
				print("\t\tname: %s" % relation["name"])
				print("\t\troute: %s" % relation["route"])
				print("\t\tnetwork: %s" % relation["network"])

				if "osmc:symbol" in relation:
					osmc = relation["osmc:symbol"].split(":")

					if len(osmc) >= 3:
						relation["osmc"] = "yes"
						relation["osmc_color"]  = osmc[0]
						relation["osmc_background"]  = osmc[1]
						relation["osmc_foreground"]  = osmc[2]

					print("\t\tosmc:symbol: %s" % relation["osmc:symbol"])

					del relation["osmc:symbol"]

				if "ref" in relation:
					print("\t\tref: %s" % relation["ref"])
				else:
					relation["ref"] = relation["name"]

class WayHandler(osmium.SimpleHandler):
	def __init__(self, all_ways, way_writer):
		osmium.SimpleHandler.__init__(self)
		self.all_ways = all_ways
		self.way_writer = way_writer
		self.way_id = -800000000000

	def way(self, w):
		if w.id in self.all_ways:
			#self.way_writer.add_way(w)
			rel_count = len(self.all_ways[w.id])
			#for relation in self.all_ways[w.id]:

			for i in range(0, rel_count):
				relation = self.all_ways[w.id][i]

				if (
					(rel_count == 2 and i == 1)
					or
					(rel_count > 2 and (relation["route"] == "bicycle" or relation["route"] == "mtb"))
				):
					way_nodes = []

					for node in w.nodes:
						way_nodes.append(node)

					new_nodes = []

					for i in range(len(way_nodes)-1, -1, -1):
						new_nodes.append(way_nodes[i])

					way = w.replace(id=self.way_id, nodes=new_nodes, tags=relation)
				else:
					way = w.replace(id=self.way_id, tags=relation)
					

				self.way_writer.add_way(way)
				self.way_id = self.way_id + 1
				

file_name = sys.argv[1]
bbox_name = sys.argv[1] + ".bbox"
output_tmp = sys.argv[1] + ".tmp.xml"
output_name = sys.argv[2]

print("Reading header...")
reader = osmium.io.Reader(file_name)
header = reader.header()
box = header.box()
print("\t", header.box())
reader.close()
print("...done")

print("Writing bounding box...")

with open(bbox_name, "wb") as f:
	bounding_param = "  <bounds minlon=\"%s\" minlat=\"%s\" maxlon=\"%s\" maxlat=\"%s\" origin=\"Darau, Blė parser\"/>" % (
		min(box.bottom_left.lon, box.top_right.lon), min(box.top_right.lat, box.bottom_left.lat), 
		max(box.bottom_left.lon, box.top_right.lon), max(box.top_right.lat, box.bottom_left.lat)
	) + os.linesep
	f.write(bounding_param.encode("utf-8"))

print("...done")

print("Parsing relations...")

rel_parser = RelationsHandler(all_ways)
rel_parser.apply_file(file_name)

print("...done, found ways: %d" % len(all_ways))

print("Extracting relation ways...")

if os.path.exists(output_tmp):
	os.remove(output_tmp)

if os.path.exists(output_name):
	os.remove(output_name)

way_writer = osmium.SimpleWriter(output_tmp)
way_parser = WayHandler(all_ways, way_writer)
way_parser.apply_file(file_name)
way_writer.close()


print("...done")

print("Hell, adding bounding box...")

with open(output_name, "w") as output:
	with open(output_tmp, "r") as tmp:
		i = 0
		for l in tmp:
			output.write(l)
			i = i + 1

			if i == 2:
				with open(bbox_name) as bbox:
					for bl in bbox:
						output.write(bl)

os.remove(output_tmp)
os.remove(bbox_name)

print("...done")

