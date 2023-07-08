#!pip install llama-index
#!pip install openai
#!pip install pypdf
#!pip install langchain
#!pip install faiss-cpu
#!pip install tiktoken (MAC-re kellett terminalban panaszkodott miatta)
#!pip install colorama


import argparse
import os
import re
import sys
import importlib
import subprocess
import pkg_resources
import hashlib
import json
import glob


# Provide the path to the folder containing the PDF documents
folder_path = "./"


#Store what OS we are running on. This will be important when composing links to PDF pages.
os_name = sys.platform

# Conditional branch based on the operating system
if os_name.startswith('linux'):
    # Linux-specific code
    print("Running on Linux")
    # Add your Linux-specific code here

elif os_name.startswith('darwin'):
    # macOS-specific code
    print("Running on macOS")
    # Add your macOS-specific code here

elif os_name.startswith('win'):
    # Windows-specific code
    print("Running on Windows")
    # Add your Windows-specific code here

else:
    # Code for other operating systems
    print("Running on an unrecognized operating system")
    # Add code for other operating systems here



#Parse command line arguments and store them.
parser = argparse.ArgumentParser(
    prog='searchPDF',
    description="""Search PDF documents in a given folder for parts that match your question.\n

    This tool searches all PDF documents in the folder specified, with the questions specified.\n
    If no path is specified for the PDFs, it is assumed to be the current folder.\n
\n
    You have to specify an OpenAI API key for this tool to work.\n
\n
    The tool will build a local index to avoid having to index the documents every time,\n
    and if no changes are made to the documents, the stored index will be used for the \n
    next query as well.\n
\n
    A hash will be calculated to keep track of any changes and if changes are detected,\n
    the index will be regenerated and stored locally again for later use.\n

    The tool will list the document and page where a similar text was found and also\n
    provide you with commands you can simply copy-paste to quickly open the documents\n
    at the correct page.\n
\n
    Unfortunately, since this is a tricky thing to do, the tool keeps track on what\n
    operating system it is running on, and provides specific commands.\n
    For Windows and macOS, helper scripts are needed and are provided for this to work.\n
    \n
    """,
    epilog=''
)
parser.add_argument('-pdfp', default='./', help = "The path of the directory containing your PDF documents to search", required=False)
parser.add_argument('-q', required=True, help = "Specifies your question. Follow this with your question in parentheses.")
parser.add_argument('-h, -help')
args=parser.parse_args()

import colorama
from colorama import Fore
from langchain.document_loaders import PyPDFDirectoryLoader

#print the help text to the console when called
def printhelp():
    helpstring = """
    This tool searches all PDF documents in the folder specified, with the questions specified.\n
    If no path is specified for the PDFs, it is assumed to be the current folder.\n
\n
    You have to specify an OpenAI API key for this tool to work.\n
\n
    The tool will build a local index to avoid having to index the documents every time,\n
    and if no changes are made to the documents, the stored index will be used for the \n
    next query as well.\n
\n
    A hash will be calculated to keep track of any changes and if changes are detected,\n
    the index will be regenerated and stored locally again for later use.\n

    The tool will list the document and page where a similar text was found and also\n
    provide you with commands you can simply copy-paste to quickly open the documents\n
    at the correct page.\n
\n
    Unfortunately, since this is a tricky thing to do, the tool keeps track on what\n
    operating system it is running on, and provides specific commands.\n
    For Windows and macOS, helper scripts are needed and are provided for this to work.\n
    \n
    """
    print (helpstring)  
    print("Usage: python3 searchPDF PATH [options] ")
    print("         -h or --help Prints this help. ")
    print("""options: 
    -pdfp [file of directory with PDFs]
    -q specify the question you wish to ask. This is not a chatbot, be brief and precise to get good answers.
         """)
    print("")
    return

# Search for PDF documents in the folder specified as pdfp (PDF path)
pdf_files = glob.glob(args.pdfp + "/*.pdf")

# Check if there are any PDF files
if len(pdf_files) == 0:
    print(Fore.RED+"No PDF documents found in the folder."+Fore.WHITE)
    sys.exit()  

#List of required packages
packages = [
    "llama-index",
    "openai",
    "pypdf",
    "langchain",
    "faiss-cpu",
    "tiktoken",
    "colorama"
]
#Check for required packages and install them if needed.
def check_package(package_name):
    try:
        dist = pkg_resources.get_distribution(package_name)
        print(f"{package_name} {dist.version} is already installed.")
        return True
    except pkg_resources.DistributionNotFound:
        print(f"{package_name} is not installed.")
        return False

def install_package(package_name):
    subprocess.check_call(["pip", "install", package_name])
    print(f"{package_name} has been installed.")

#Install missing packages
for package in packages:
    if not check_package(package):
        install_package(package)

# This is where you should put your OPENAI API KEY
os.environ['OPENAI_API_KEY'] = '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'

#Check command line arguments, we need a question at least.
if len(sys.argv) < 2:

       printhelp()
     

#Set the place to check for a local index file
HASH_STORE_FILENAME = "hash_store.json"
index_file_path = args.pdfp+'/mylocalFAISSindex.index'
hash_file_path = args.pdfp+"/"+HASH_STORE_FILENAME
print("Index file path is:"+index_file_path)
print("Hash file path is: "+hash_file_path)


#Import multiple PDFs from a directory
from langchain.document_loaders import PyPDFDirectoryLoader

#Build an index, do a search, ask the question
print("Building index and searching index for question.")
print(f"Question given is: " + args.q)
question=args.q
print(f"Path used for building index of documents used is:"+args.pdfp)
print("=====================================================================")
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS

#TODO compare hash of PDF files in path given to see if they are stale or not.
#See if there is a local index and hash file available.
if os.path.exists(index_file_path):
    haslocalindex = True
else:
    haslocalindex = False
if os.path.exists(hash_file_path):
    stored_hash_available = True
else:
    stored_hash_available = False

#Functions needed for creating, storing, loading and comparing hashes of documents in the folder.
def calculate_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def calculate_hashes_in_folder(folder_path):
    file_hashes = {}

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) and filename.lower().endswith(".pdf"):
            file_hash = calculate_hash(file_path)
            file_hashes[filename] = file_hash

    return file_hashes

def store_hashes(folder_path, file_hashes):
    hash_store_path = os.path.join(folder_path, HASH_STORE_FILENAME)
    with open(hash_store_path, "w") as file:
        json.dump(file_hashes, file)

def load_hashes(folder_path):
    hash_store_path = os.path.join(folder_path, HASH_STORE_FILENAME)
    if os.path.isfile(hash_store_path):
        with open(hash_store_path, "r") as file:
            return json.load(file)
    return {}

def compare_hashes(folder_path):
    stored_hashes = load_hashes(folder_path)
    current_hashes = calculate_hashes_in_folder(folder_path)

    if stored_hashes == current_hashes:
        return True
    else:
        return False

if haslocalindex == False: 
    print (Fore.RED+"There is no local index stored, building index of pdf files, this could take a while."+Fore.WHITE)
    #If a pdfpath is given, use it. Else use the default, which is the current directory.
    loader = PyPDFDirectoryLoader(args.pdfp)
    docu = loader.load()
    faiss_index = FAISS.from_documents(docu, OpenAIEmbeddings())
    FAISS.save_local(faiss_index, index_file_path)
else:
    print(Fore.GREEN+"Local index store found, checking for hash file."+Fore.WHITE)
    if (stored_hash_available):
        print("Loading hash file.")
        stored_hashes = load_hashes(args.pdfp)
        print ("Checking for changes in folder using hash file")
        hash_is_valid = compare_hashes(args.pdfp)
        if (hash_is_valid == True):
            print(Fore.GREEN+"Hash still valid, using stored document index."+Fore.RED)
        else:
            print(Fore.RED+"Hash is stale, changes have been detected in the documents. Recalculating before use."+Fore.WHITE)
            loader = PyPDFDirectoryLoader(args.pdfp)
            docu = loader.load()
            faiss_index = FAISS.from_documents(docu, OpenAIEmbeddings())
            FAISS.save_local(faiss_index, index_file_path)
            #Calculate hashes and store them to the local file
            current_hashes = calculate_hashes_in_folder(args.pdfp)
            store_hashes(args.pdfp, current_hashes)
    else:
        #Calculate hashes and store them to the local file
        current_hashes = calculate_hashes_in_folder(args.pdfp)
        store_hashes(args.pdfp, current_hashes)
    faiss_index = FAISS.load_local(index_file_path, OpenAIEmbeddings())
    
docs = faiss_index.similarity_search(question, k=4)
for doc in docs:
    print(Fore.BLUE+str(doc.metadata["page"]) + ":", Fore.WHITE+doc.page_content[:300])
    print("Metadata is:"+Fore.YELLOW+str(doc.metadata)+Fore.WHITE)
    full_path = os.path.abspath(str(doc.metadata["source"]))
    if os_name.startswith('darwin'):
        print(f"To jump directly to this section, copy this command: "+Fore.GREEN+"osascript openPage.scpt "+str(full_path)+" "+str(doc.metadata["page"])+Fore.WHITE)
    elif os_name.startswith('win'):
        s = "file:///"+str(full_path)+"#page="+str(doc.metadata["page"])
        #print("tp was "+s)
        s = s.replace("\\", "/")
        #print("tp is now"+s)
        print(f"To jump directly to this section, copy this command: "+Fore.GREEN+"start pass_url2edge.bat "+s+Fore.WHITE)
    elif os_name.startswith('linux'):
        print(f"To jump directly to this section, copy this command: "+Fore.GREEN+"firefox "+str(full_path)+"#page="+str(doc.metadata["page"])+Fore.WHITE)
    else:
        print(Fore.RED+"Unfortunately, the OS could not be determined, I cannot generate a direct link to the page."+Fore.WHITE)

