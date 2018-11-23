# Journal_Club_DOI_to_PubMeta
This python script takes a comma separated values of DOIs then searches for these DOI in "NCBI PubMed" to get the metadata from it then it makes a markdown file contains briefing of the publications.
Sometimes DOI cannot be found in PubMed, the script will notify you and will dump an error file with the DOIs that have problems.
Usage: 
meta_doi.py -i inputfilename_CSV_ONLY -o outputfilename
