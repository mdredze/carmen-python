# Mapping Carmen Database -> Geonames

## Setup
1. Download the Geonames data:
```bash
cd geoname_mapping
mkdir Geonames
curl http://download.geonames.org/export/dump/cities15000.zip -o cities15000.zip
unzip cities15000.zip
curl http://download.geonames.org/export/dump/admin1CodesASCII.txt -o admin1CodesASCII.txt
curl http://download.geonames.org/export/dump/admin2Codes.txt -o admin2Codes.txt
curl http://download.geonames.org/export/dump/countryInfo.txt -o countryInfo.txt
```

2. Remove the comments from the top of `countryInfo.txt` but leave the header row (without the "#")

3. Add the column names to the top of the following files (tab separated):
```bash
code  name  ascii  geonameid > admin1CodesASCII.txt
concatenated codes  name    ascii   geonameId > admin2Codes.txt
```
