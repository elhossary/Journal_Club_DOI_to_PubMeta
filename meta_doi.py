import urllib.request as url_request
import xml.etree.ElementTree as ET
import pandas as pd
import re
import sys, getopt

def hard_article_search(doi):
  url = "https://www.ncbi.nlm.nih.gov/pubmed/?term=" + doi
  str_received = url_request.urlopen(url).read().decode('utf-8')
  if "<dt>PMID:</dt>" in str_received:
    result = re.search('<dl class="rprtid"><dt>PMID:</dt> <dd>(.*)</dd>', str_received).group(1)
    return result[:result.index('<')]
  else:
    return None

def convert_doi_to_pmid(doi_csv):
  url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?tool=my_tool&email=my_email@example.com&ids=" + doi_csv
  str_received = url_request.urlopen(url).read().decode('utf-8')
  parsed_xml = ET.fromstring(str_received)
  dfcols = ['doi', 'pmid']
  doi_pmid_df = pd.DataFrame(columns=dfcols)
  for child in parsed_xml.iter(tag="record"):
    doi_pmid_df = doi_pmid_df.append(
      pd.Series([child.get('requested-id'), child.get('pmid')], index=dfcols), ignore_index=True)
    doi_pmid_df.head()

  for index, row in doi_pmid_df.iterrows():
    if row['pmid'] == None:
      row['pmid'] = hard_article_search(row['doi'])
      if row['pmid'] == None:
        print("Can't find this DOI in PubMed ==> " + row['doi'])
  return doi_pmid_df

def getvalueofnode(article, search_tag, val_mode):
  authors_list = []
  authors = ""
  if val_mode == "SINGLE":
    for node in article.iter():
      if node.tag == search_tag:
        return node.text
  elif val_mode == "MULTI":
    for node in article.iter():
      if node.tag == search_tag:
        for subnode in node.iter():
          if subnode.tag == "LastName":
            authors_list.append(subnode.text)
          elif subnode.tag == "ForeName":
            authors_list[-1] += (" " + subnode.text)
    for i in authors_list:
      authors += i + ", "
    authors = authors[:-2]
    return authors
  else:
    sys.exit("Excution Aborted, Fatal Error: Can't determine val_mode")

def generate_pub_list(pmid_csv):
  url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&tool=my_tool&email=my_email@example.com&retmode=xml&id=" + pmid_csv
  str_received = url_request.urlopen(url).read().decode('utf-8')
  article_set = ET.fromstring(str_received)
  dfcols = ['Title', 'Authors', 'Abstract', 'Publisher', 'PubYear', 'PubMonth', 'PMID', 'DOI']
  df = pd.DataFrame(columns=dfcols)
  for article in article_set:
    df = df.append(pd.Series([getvalueofnode(article, "ArticleTitle", "SINGLE"),
                              getvalueofnode(article, "Author", "MULTI"),
                              getvalueofnode(article, "AbstractText", "SINGLE"),
                              getvalueofnode(article, "Title", "SINGLE"),
                              getvalueofnode(article, "Year", "SINGLE"),
                              getvalueofnode(article, "Month", "SINGLE"),
                              getvalueofnode(article, "PMID", "SINGLE"),
                              None],
                              index=dfcols), ignore_index=True)
  return df

def main(argv):
  inputfilename = ''
  outputfilename = ''
  try:
    opts, args = getopt.getopt(argv, "hi:o:", ["ifile=", "ofile="])
  except getopt.GetoptError:
    print('meta_doi.py -i <inputfile> -o <outputfile>')
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-h':
      print('meta_doi.py -i <inputfile CSV ONLY> -o <outputfile>')
      sys.exit()
    elif opt in ("-i", "--ifile"):
      inputfilename = arg
    elif opt in ("-o", "--ofile"):
      outputfilename = arg
  inputfile = open(inputfilename, "r", encoding="utf-8")
  doi_pmid_df = convert_doi_to_pmid(inputfile.read())
  inputfile.close()
  pmid_csv = ""
  for index, row in doi_pmid_df.iterrows():
    if row['pmid'] != None:
      pmid_csv += row['pmid'] + ","
  pmid_csv = pmid_csv[:-1]
  df = generate_pub_list(pmid_csv)
  for index, row in df.iterrows():
    for i, r in doi_pmid_df.iterrows():
      if row["PMID"] == r["pmid"]:
        row["DOI"] = r["doi"]
        break
  md_code_str = "# Publication List\n"
  for index, row in df.iterrows():
    md_code_str += "> ### " + row['Title'] + "\n"
    md_code_str += "> ######" + row['Publisher'] + ", Date: " + row['PubMonth'] + "/" + row['PubYear'] + "\n\n"
    md_code_str += "> #### " + row['Authors'] + "\n"
    md_code_str += "> ##### " + row['Abstract'] + "\n\n"
    md_code_str += "> ##### Link to article: [Pubmed](https://www.ncbi.nlm.nih.gov/pubmed/" + row['PMID'] + "), [DOI](http://doi.org/" + row['DOI'] + ")\n\n---\n"
  outputfile = open(outputfilename + ".md", "w", encoding="utf-8")
  outputfile.write(md_code_str)
  outputfile.close()
  print("***** DONE! *****")

if __name__ == "__main__":
   main(sys.argv[1:])