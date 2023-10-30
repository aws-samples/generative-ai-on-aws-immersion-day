## The LLMs capabilities on SEC 14A filings


## Input data
1. The original data is publically available through EDGAR in HTML format:  
https://www.sec.gov/edgar/search/#/q=ALABAMA%2520POWER%2520COMPANY&dateRange=custom&startdt=2018-05-09&enddt=2021-05-09

2. Example  
https://sec.gov/Archives/edgar/data/3153/000000315320000004/0000003153-20-000004.txt
 
## Terminology
The 14A documents are identified by SAN which stands for Accession number. Refer https://www.sec.gov/os/accessing-edgar-data for more information.
For example, 0001193125-15-118890 is the accession number, a unique identifier assigned automatically to an accepted submission by EDGAR.

## The types of data
- data/14A/14A - original SEC 14A file
- data/14A/14A_frags - extracted biography passages (pure sections)
- data/14A/14A_meta - a pre-computed metadata containing directorship positions used to refine IR

## Document Store
To explore performance of LLMs on different types of data loader and pre-processing functions we build the following abstraction layers: doc -> loader -> Doc Source -> Doc Store

1. load1.py - default HTML parser BSHTMLLoader available on Langchain.
2. load2.py - custom HTML parser BSHTMLLoaderEx adding spaces and newlines to terminate block level HTML tags.
3. load3.py - loads pre-computed textual 14A paragraphs (director biographies) and represents the ideal scenario for input data.

The DocSource is an abstraction over different loaders. There are 3 types of Doc Stores:
1. OpensearchTextFrags - uses load3.py and populates Opensearch index per single SAN doc.
2. OpensearchHTML - uses load3.py and populates Opensearch index per single SAN doc.
3. KendraHTML - uses full HTML files on s3 and is pre-populated manually (template).

