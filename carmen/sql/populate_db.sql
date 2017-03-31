-- Creates a "cities" table in a PostgreSQL database and populates it.
--
-- \set cities_file '\'/Users/hhan/Desktop/carmen-python/carmen/data/dump/cities1000.txt\'';

CREATE TABLE cities(
	id                 INTEGER        PRIMARY KEY  NOT NULL ,
	name               VARCHAR(200)                NOT NULL ,
	asciiname          VARCHAR(200)                         ,
	alternatenames     VARCHAR(10000)                       ,
	latitude           FLOAT                       NOT NULL ,
	longitude          FLOAT                       NOT NULL ,
	feature_class      CHAR(1)                     NOT NULL ,
	feature_code       VARCHAR(10)                 NOT NULL ,         
	country_code       CHAR(2)                     NOT NULL ,
	cc2                VARCHAR(200)                         ,
	admin1_code        VARCHAR(20)                          ,
	admin2_code        VARCHAR(80)                          ,
	admin3_code        VARCHAR(20)                          ,
	admin4_code        VARCHAR(20)                          ,
	population         BIGINT                               ,
        elevation          INTEGER                              ,
	dem                INTEGER                              ,
        timezone           VARCHAR(40)                 NOT NULL ,
        modification_date  DATE                        NOT NULL
);

CREATE TABLE admin1_codes(
	country_code       CHAR(2)                     NOT NULL ,
	admin1_code        VARCHAR(20)                 NOT NULL ,
	name               VARCHAR(200)                         ,
	asciiname          VARCHAR(200)                         ,
	id                 INTEGER                     NOT NULL 
);

CREATE TABLE admin2_codes(
	country_code       CHAR(2)                     NOT NULL ,
	admin2_code        VARCHAR(20)                 NOT NULL ,
	name               VARCHAR(200)                         ,
	asciiname          VARCHAR(200)                         ,
	id                 INTEGER                     NOT NULL 
);

CREATE TABLE country_info(
	iso                  CHAR(2)                   NOT NULL ,
	iso3                 CHAR(3)                   NOT NULL ,
	iso_numeric          CHAR(3)                   NOT NULL ,
	fips                 CHAR(2)                            ,
	country              VARCHAR(200)              NOT NULL ,
	capital              VARCHAR(200)                       ,
	area                 FLOAT                              ,
	population           BIGINT                             ,
	continent            CHAR(2)                   NOT NULL ,
	tld                  CHAR(3)                            ,
	currency_code        CHAR(3)                            ,
	currency_name        VARCHAR(20)                        ,
	phone                VARCHAR(20)                        ,
	postal_code_format   VARCHAR(100)                       ,
	postal_code_regex    VARCHAR(200)                       ,
	languages            VARCHAR(200)                       ,
	geoname_id           INTEGER                   NOT NULL ,
	neighbours           VARCHAR(100)                       ,
	equivalent_fips_code CHAR(2)
);

-- COPY cities FROM :cities_file DELIMITER E'\t' NULL AS '';
COPY cities       FROM '/Users/hhan/Desktop/carmen-python/carmen/data/dump/cities1000.txt'  DELIMITER E'\t' NULL AS '';
COPY admin1_codes FROM '/Users/hhan/Desktop/carmen-python/carmen/data/dump/admin1Codes.txt' DELIMITER E'\t' NULL AS '';
COPY admin2_codes FROM '/Users/hhan/Desktop/carmen-python/carmen/data/dump/admin2Codes.txt' DELIMITER E'\t' NULL AS '';
COPY country_info FROM '/Users/hhan/Desktop/carmen-python/carmen/data/dump/country_info.txt'  DELIMITER E'\t' NULL AS '';