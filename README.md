# COACS #
### Cataloguing Open Access Classics Serials ###

**Project team:**

 * Gabriel Bodard (Institute of Classical Studies, University of London)
 * Simona Stoyanova (Institute of Classical Studies, University of London)

The Cataloguing Open Access Classics Serials (COACS) project will leverage the various sites that list or index open access (OA) publications, especially journals and serials in classics and ancient history, to produce a resource that subject libraries may use to automatically catalogue the publications and articles therein. The project is based in the ICS, in collaboration with the Combined Library of the Hellenic and Roman Societies, and in consultation with the Warburg Institute, the Institute for the Study of the Ancient World (NYU) and the German Archaeological Institute.

**More news:**

 * [ICS project announcement](http://ics.sas.ac.uk/about-us/news/cataloguing-open-access-classics-serials)
 * [Stoa blog post](http://www.stoa.org/archives/2381)
 
**Partner institutions:**
 
 * Institute of Classical Studies and Hellenic and Roman Societies Combined Library
 * Warburg Institute, School of Advanced Study, London
 * Institute for the Study of the Ancient World, New York University
 * Pennsylvania State University Library
  
**Project progress and notes:**

 * [Project outline](notes/outline.md)
 * [Useful links](notes/useful_links.md)
 * [Feb–May 2017 notes](notes/notes201702-05.md)
  
**This repository contains:**

 * Master branch:
   * Jupyter notebook and separate Python script to convert json files to MARC
   * script coverting language codes to IANA
   * awol_python3: started conversion of awol code to Python3, unfinished
   * Output: top-level and article-level bibliographic records in MARC
   
 * SHL_ingest branch:
   * Jupyter notebook with additional code to produce ids and add a project code to each record
   * SHL_mrc: bundles of 5000 records combined into .mrc files
   * SHL_title: individual top-level records
   * COACS_toplevel.mrc: tidied and corrected top-level records

   
