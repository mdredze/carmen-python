from map_locations import coordinate_distance, name_similarity

# coords (lat, long)
geoP = (-7.7625, 110.43167) # geonames positive
geoN = (-6.4, 106.81861) # geonames negative
Carm = (-7.783315, 110.419485) # carmen to convert


dpn = coordinate_distance(geoP, geoN)
dcp = coordinate_distance(Carm, geoP)
dcn = coordinate_distance(Carm, geoN)
print('P - N')
print(dpn)
print('C - P')
print(dcp)
print('C - N')
print(dcn)
print('cp/pn')
print(dcp/dpn)
print('cn/pn')
print(dcn/dpn)
