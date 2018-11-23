import urllib.request as url_request
import xml.etree.ElementTree as ET
import pandas as pd
import re
import sys, getopt

def hard_article_search(doi):
  url = "https://www.ncbi.nlm.nih.gov/pubmed/?term=" + doi
  pmid = ""
  str_received = url_request.urlopen(url).read().decode('utf-8')
  if "<dt>PMID:</dt>" in str_received:
    result = re.search('<dl class="rprtid"><dt>PMID:</dt> <dd>(.*)</dd>', str_received).group(1)
    try:
      pmid = result[:result.index('<')]
      return pmid
    except:
      print("A DOI found in Pubmed but seems there is problem with this DOI, Please do it manually ==> " + doi)
    finally:
      return pmid
  else:
    return None

def convert_doi_to_pmid(doi_csv):
  url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?tool=my_tool&email=my_email@example.com&ids=" + doi_csv
  try:
    str_received = url_request.urlopen(url).read().decode('utf-8')
  except Exception as e:
    print(e)
    sys.exit("Excution Aborted, service unavailable")
  parsed_xml = ET.fromstring(str_received)
  dfcols = ['doi', 'pmid']
  doi_pmid_df = pd.DataFrame(columns=dfcols)
  for child in parsed_xml.iter(tag="record"):
    doi_pmid_df = doi_pmid_df.append(
      pd.Series([child.get('requested-id'), child.get('pmid')], index=dfcols), ignore_index=True)
    doi_pmid_df.head()

  for index, row in doi_pmid_df.iterrows():
    if not row['pmid']:
      row['pmid'] = hard_article_search(row['doi'])
      if not row['pmid']:
        print("Can't find this DOI in PubMed ==> " + row['doi'])
  return doi_pmid_df

def getvalueofnode(article, search_tag, val_mode):
  authors_list = []
  authors = ""
  return_val = ""
  if val_mode == "SINGLE":
    for node in article.iter():
      if node.tag == search_tag:
        return_val =  node.text
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
    return_val = authors[:-2]
  else:
    sys.exit("Excution Aborted, Fatal Error: Can't determine val_mode")

  if return_val:
    return return_val
  else:
    return "No " + search_tag

# def search_in_cross_ref(doi):
#
#   url = "http://api.crossref.org/works/" + doi + "/transform/application/vnd.crossref.unixsd+xml"
#   str_received = url_request.urlopen(url).read().decode('utf-8')
#   article_content = ET.fromstring(str_received)
#   dfcols = ['Title', 'Authors', 'Abstract', 'Publisher', 'PubYear', 'PubMonth', 'PMID', 'DOI']
#   for i in article_content:
#     x = pd.Series([getvalueofnode(i, "title", "SINGLE"),
#                               getvalueofnode(i, "surname", "MULTI"),
#                               getvalueofnode(i, "jats:p", "SINGLE"),
#                               getvalueofnode(i, "institution_name", "SINGLE"),
#                               getvalueofnode(i, "year", "SINGLE"),
#                               getvalueofnode(i, "month", "SINGLE"),
#                               getvalueofnode(i, "PMID", "SINGLE"),
#                               None],
#                               index=dfcols)
#     print(x)
#   return x

def generate_pub_list(pmid_csv):
  # cross_ref_doi_list = re.findall('CROSS_REF_SEARCH_(.*)_THIS', pmid_csv)
  # print(cross_ref_doi_list)
  # cross_ref_doi_list = cross_ref_doi_list[0].replace("CROSS_REF_SEARCH_", "").replace("_THIS", "").split(",")
  # print(cross_ref_doi_list)
  url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&tool=my_tool"\
        + "&email=my_email@example.com&retmode=xml&id=" + pmid_csv
  try:
    str_received = url_request.urlopen(url).read().decode('utf-8')
  except Exception as e:
    print(e)
    sys.exit("Excution Aborted, service unavailable")
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
  # for doi in cross_ref_doi_list:
  #   df = df.append(search_in_cross_ref(doi), ignore_index=True)
  return df

def main(argv):
  inputfilename = ''
  outputfilename = ''
  error_doi_list = []
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
    if row['pmid']:
      pmid_csv += row['pmid'] + ","
    else:
      error_doi_list.append(row['doi'])
    #   pmid_csv += "CROSS_REF_SEARCH_" + row['doi'] +"_THIS,"
  pmid_csv = pmid_csv[:-1]
  df = generate_pub_list(pmid_csv)
  for index, row in df.iterrows():
    for i, r in doi_pmid_df.iterrows():
      if row["PMID"] == r["pmid"]:
        row["DOI"] = r["doi"]
        break
  md_code_str = "# Journal Club Publication List\n---\n"
  for index, row in df.iterrows():
    md_code_str += "> ### " + row['Title'] + "\n"
    md_code_str += "> ###### " + row['Publisher'] + ", Date: " + row['PubMonth'] + "/" + row['PubYear'] + "\n\n"
    md_code_str += "> #### " + row['Authors'] + "\n"
    md_code_str += "> ##### " + row['Abstract'] + "\n\n"
    if row['PMID'] and row['DOI']:
      md_code_str += "> ##### Link to article: [Pubmed](https://www.ncbi.nlm.nih.gov/pubmed/"\
                     + row['PMID'] + "), [DOI](http://doi.org/" + row['DOI'] + ")\n\n---\n"
    elif row['DOI'] and not row['PMID']:
      md_code_str += "> ##### Link to article: [DOI](http://doi.org/" + row['DOI'] + ")\n\n---\n"
    elif row['PMID'] and not row['DOI']:
      md_code_str += "> ##### Link to article: [Pubmed](https://www.ncbi.nlm.nih.gov/pubmed/" + row['PMID'] + ")\n\n---\n"
  outputfile = open(outputfilename + ".md", "w", encoding="utf-8")
  outputfile.write(md_code_str)
  outputfile.close()
  if len(error_doi_list) != 0:
    error_file = open("DOI_errors.txt", "w+", encoding="utf-8")
    error_file.write("DOIs that has errors for manual check:")
    for err_doi in error_doi_list:
      error_file.write("\n" + err_doi)
    error_file.close()
    print('\n\n\n\n***** DONE with ' + str(len(error_doi_list)) + ' errors of ' + str(doi_pmid_df.shape[0])
          + ' , check file "DOI_errors.txt" *****')
  else:
    print("\n\n\n\n***** DONE without errors! *****")

if __name__ == "__main__":
   main(sys.argv[1:])
