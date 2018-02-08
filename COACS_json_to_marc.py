#!/usr/bin/env python3
import argparse
import os
# map from IANA 2-character language codes to ISO639-2 3-character language codes, as used in MARC

lang_map = {
    "af": "afr",
    "an": "arg",
    "ar": "ara",
    "az": "aze",
    "be": "bel",
    "bg": "bul",
    "br": "bre",
    "bs": "bos",
    "ca": "cat",
    "cs": "cze",
    "cy": "wel",
    "da": "dan",
    "de": "ger",
    "el": "gre",
    "en": "eng",
    "eo": "epo",
    "es": "spa",
    "et": "est",
    "eu": "baq",
    "fa": "per",
    "fi": "fin",
    "fo": "fao",
    "fr": "fre",
    "gl": "glg",
    "he": "heb",
    "hr": "hrv",
    "hu": "hun",
    "id": "ind",
    "it": "ita",
    "ja": "jpn",
    "jv": "jav",
    "ka": "geo",
    "ko": "kor",
    "ku": "kur",
    "ky": "kir",
    "la": "lat",
    "lb": "ltz",
    "lo": "lao",
    "lt": "lit",
    "lv": "lav",
    "mg": "mlg",
    "mk": "mac",
    "mr": "mar",
    "mt": "mlt",
    "nl": "dut",
    "no": "nno",
    "oc": "oci",
    "pl": "pol",
    "pt": "por",
    "ro": "rum",
    "ru": "rus",
    "sk": "slo",
    "sl": "slv",
    "sr": "srp",
    "sv": "swe",
    "sw": "swa",
    "tl": "tgl",
    "tr": "tur",
    "uk": "ukr",
    "ur": "urd",
    "vi": "vie",
    "wa": "wln",
    "zh": "chi"
}   




# In[6]:


# extract relevant bibliographic information from the AWOL index json dump 
# and produce marc files for use in library catalogues  

import glob
import json
import re
from pymarc import Record, Field
from pymarc import MARCReader
import time
from datetime import timedelta

start_time = time.time()

# marc fields for each journal record
def json_to_marc(infilename, outfilename):
    print('Processing: ' + infilename)  #progress message
    data = json.load(open(infilename, "r"))
    record = Record(force_utf8=True)   #create MARC record, enforce Unicode 
    
    # add fields 006, 007 and 008 with minimal physical information to every marc file
    record.add_field(
        Field(
            tag = '006',
            data = "m"))   
    record.add_field(
        Field(
            tag = '007',
            data = "cr"))
    
    # the iana language code from the json file is taken, checked against the list of language codes,
    # substituted with its iso639-2 equivalent and put in position 21-24 of the field 008 content
    field008val = "            o       0eng d" # DEFAULT ENG
    try:
        if 'languages' in data and data['languages'][0] is not None:
            field008val = field008val[0:21] + lang_map.get(data['languages'][0], "   ") + field008val[24:]
    except IndexError:
        field008val = field008val[0:21] + "   " + field008val[24:]
        
                
    record.add_field(
        Field(
            tag = '008',
            data = field008val))

        
    
    # extract issn, in json 'generic' and/or 'electronic', and put into separate subfields of 022
    
    if "identifiers" in data and "issn" in data["identifiers"]:
        field_issn = Field(
                tag='022',
                indicators=['0', '#']
        )
        
        if "generic" in data["identifiers"]["issn"]:
            field_issn.add_subfield('a', data["identifiers"]["issn"]["generic"][0])
            
        if "electronic" in data["identifiers"]["issn"]:
            field_issn.add_subfield('l', data["identifiers"]["issn"]["electronic"][0])
            
        record.add_field(field_issn)
    

            
        
    # title of the series or journal
    if data["is_part_of"] is not None and data["is_part_of"]['title_full']:
            record.add_field(
                Field(
                    tag = '245',
                    indicators=['0', '0'],
                    subfields=["a", data["is_part_of"]["title_full"][:9000]]))
    if data["title"]:
        record.add_field(
            Field(
                tag='246',
                indicators=['0', '0'],
                subfields=["a", data["title"][:9000]])
        )
    
    if data["year"]:
        record.add_field(
            Field(
                tag="260",
                indicators=["#", "#"],
                subfields=["c", data["year"]]))
     
    # add field 506 to all records, as not present in all json files
    record.add_field(
        Field(
            tag='506',
            indicators=['0', '#'],
            subfields=["a", "Open access"])
    )
    
    # some json files contain a very long description; the maximum length of data in a variable field 
    #in MARC21 is 9,999 bytes, so here only a certain amount of content is put into the 520 field
    if data["description"]:
        record.add_field(
            Field(
                tag='520',
                indicators=['2', '#'],
                subfields=["a", data["description"][:9000]])
        )

                    
        
    
    # keep together the journal url, host and domain as different subfields of field 856 
    # check if either exists, before initializing a new field instance
    if data['url'] or (data['is_part_of'] is not None and data['is_part_of']['url']):
        field = Field(
                tag='856',
                indicators=['0', '0']
        )
        if data['domain']:
            field.add_subfield('a', data['domain'])

        if data['is_part_of'] is not None and data['is_part_of']['url']:
            field.add_subfield('d', data['is_part_of']['url'])

        if data['url']:
            field.add_subfield('u',  data['url'])


        record.add_field(field)

        if data["volume"]:
            record.add_field(
                Field(
                tag='866',
                indicators=['0', '0'],
                subfields=["a", data["volume"]])
            )

        #output marc file with same filename in Output directory
        out = open(outfilename, 'wb')
        out.write(record.as_marc())
        out.close()	

        # execute function for creating separate records for subordinate resources
        if data['subordinate_resources'] is not None: 
            subordinate_records = create_subordinate_records(record, data['subordinate_resources'])

        counter = 0

        # add counter and "-sub" to filenames of subordinate records
        for subordinate_record in subordinate_records:
            out = open(outfilename.replace(".marc", "-sub"+str(counter)+".marc"), 'wb')
            out.write(subordinate_record.as_marc())
            out.close()
            counter = counter + 1



def create_subordinate_records(parent_record, subordinate_data_list):
	'''If a journal record includes a list of individual issues or volumes,    this function creates separate marc files for each of those issues or volumes. The journal title and url    are taken from the parent record (the journal record) and kept in the subordinate records.'''
	result_list = []
	
	for subordinate_resource in subordinate_data_list:
		sub_record = Record(force_utf8=True)

		# add fields 006, 007 and 008 with minimal physical information to every marc file
		if 'title_full' in subordinate_resource:
			sub_record.add_field(
				Field(
					tag = '006',
					data = "m"))   
			sub_record.add_field(
				Field(
					tag = '007',
					data = "cr"))
			
			# the value of field 008 is taken from the parent record and put into the subordinate one
			field008val = "            o       0eng d" # DEFAULT ENG
			if 'languages' in parent_record and parent_record['languages'] is not None:
				field008val = field008val[0:21] + lang_map.get(parent_record['languages'][0], "   ") + field008val[24:]
			
				
			sub_record.add_field(
				Field(
					tag = '008',
					data = field008val))
			
	
			sub_record.add_field(
				Field(
					tag='245',
					indicators=['0', '0'],
					subfields=['a', subordinate_resource['title_full'][:9000]]
					)
			)
			sub_record.add_field(
				Field(
					tag='506',
					indicators=['0', '#'],
					subfields=["a", "Open access"])
			)

		if parent_record['246']['a']:
			sub_record.add_field(
				Field(
					tag='490',
					indicators=['0', '0'],
					subfields=['a', parent_record['246']['a']])
			)

		
		# put together the issue/volume url, the journal url and the domain in field 856; 
		# domain and journal url taken from the parent record, issue/volume url taken from the subordinate record
		if 'url' in subordinate_resource:
			current_field = Field(
				tag='856',
				indicators=['0', '0']
			)

			current_field.add_subfield('u', subordinate_resource['url'])

			if parent_record['856']['a']:
				current_field.add_subfield('a', parent_record['856']['a'])

			if parent_record['856']['u']:
				current_field.add_subfield('d', parent_record['856']['u'])

			sub_record.add_field(
				current_field
			)

		result_list.append(sub_record)

	return result_list


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='json to marc')
	parser.add_argument('input_dir', type=str,
						help='put path to input directory')
	parser.add_argument('out_dir',
						help='put path to output direct0ry')
	
	args = parser.parse_args()
	
	for parent, dir_names, file_names in os.walk(args.input_dir):
		for fn in file_names:
			if fn.endswith(".json" ):
				infilepath = os.path.join(parent, fn)
				marc_fn = fn.replace(".json", ".marc")
				outfilepath = os.path.join(args.out_dir, marc_fn)
				
				print(infilepath, outfilepath)
				json_to_marc(infilepath, outfilepath)
				


