
#
# load useful libraries
#
import os
import glob
import xml.etree.ElementTree as ET
import xmltodict
import pandas as pd
import html
import pickle

#
# user settings
#
directory_data = '/home/emily/Downloads/pubmed'
filename_output = 'output/pmid_and_title.pickled'

#
# get a list of files to process
#
list_files_xml = sorted(glob.glob(directory_data + '/*.xml.gz'))

#
# define wrapper function
#
def decompression_wrapper(filename, list_functions_to_use):
    os.system('gunzip ' + filename)

    dict_results = {}
    for function_to_use in list_functions_to_use:

        function_name = str(function_to_use).split('function ')[1].split(' ')[0]
        dict_results[function_name] = function_to_use(filename.replace('.gz', ''))
    
    os.system('gzip ' + filename.replace('.gz', ''))
    return dict_results

#
# define function that extracts PMID and title using ElementTree
#
def extract_all_article_ids_and_titles_using_ElementTree(xml_file : str) -> pd.DataFrame:
    tree = ET.parse(xml_file)
    root = tree.getroot()
    extracted_data = []

    for article in root.findall(".//PubmedArticle"):
        pmid_str = article.findtext(".//PMID").strip()  # kept a string for now

        title_element = article.find(".//ArticleTitle")
        title = ET.tostring(title_element, encoding="unicode").strip()
        title = title.replace('ArticleTitle>', '')[1:-2]
        title = html.unescape(title)
        
        if pmid_str != '' and title != '':
            extracted_data.append({'pmid_str' : pmid_str, 'title' : title})

    df = pd.DataFrame(extracted_data)
    return df

#
# define function that extracts PMID and title using xmltodict
#
def extract_all_article_ids_and_titles_using_xmltodict(xml_file : str) -> pd.DataFrame:

    with open(xml_file, 'r', encoding='utf-8') as file:
        xml_data = file.read()
    dict_pm = xmltodict.parse(xml_data)
    
    extracted_data = []
    for item in dict_pm['PubmedArticleSet']['PubmedArticle']:
        article = item['MedlineCitation']['Article']
        pmid_str = item['MedlineCitation']['PMID']['#text']
        
        title = article['ArticleTitle']
        if isinstance(title, dict):

            # WTF?
            if '#text' in title:
                new_title = title['#text']
            elif 'i' in title:
                new_title = title['i']
            else:
                new_title = 'FAILED TITLE GRAB'

            title = new_title
        
        if pmid_str != '' and title != '':
            extracted_data.append({'pmid_str' : pmid_str, 'title' : title})

    df = pd.DataFrame(extracted_data)
    return df

#
# Run the two methods
#
list_dict_id_title = []
for filename in list_files_xml:
    print(filename)
    
    dict_results = decompression_wrapper(
        filename, [
            extract_all_article_ids_and_titles_using_ElementTree,
            extract_all_article_ids_and_titles_using_xmltodict,
        ]
    )
    dict_results['filename'] = filename
    list_dict_id_title.append(dict_results)

#
# save results
#
with open(filename_output, 'wb') as f:
    pickle.dump(list_dict_id_title, f)
