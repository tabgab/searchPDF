#!pip install llama-index openai pypdf langchain faiss-cpu tiktoken colorama

import os
import sys
import hashlib
import json
import argparse
import subprocess
import pkg_resources
import glob

from colorama import Fore
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from texttable import Texttable


# Constants
HASH_STORE_FILENAME = "hash_store.json"


# Initialization
os_name = sys.platform
folder_path = "./"

REQUIRED_PACKAGES = [
    "llama-index",
    "openai",
    "pypdf",
    "langchain",
    "faiss-cpu",
    "tiktoken",
    "colorama",
    "texttable"
]


# Helper functions
def print_os_specific_message():
    if os_name.startswith('linux'):
        print("Running on Linux")
    elif os_name.startswith('darwin'):
        print("Running on macOS")
    elif os_name.startswith('win'):
        print("Running on Windows")
    else:
        print("Running on an unrecognized operating system")


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


def load_openai_key():
    with open('openai_key.txt', 'r') as file:
        key = file.read().strip()
    return key


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

    return stored_hashes == current_hashes


# Main function
def main(args):
    # Print operating system
    print_os_specific_message()

    # Check for OpenAI key
    if os.path.exists("openai_key.txt"):
        print("OpenAI key found, proceeding.")
    else:
        print(f"{Fore.RED}This program cannot function without an OpenAI key. "
              f"There must be an {Fore.CYAN}openai_key.txt {Fore.RED}file in the same directory as searchPDF, "
              f"and it must contain your own unique OpenAI API key. Refer to the internet on how to get one.{Fore.WHITE}")
        sys.exit()

    # Search for PDF documents in the folder specified as pdfp (PDF path)
    pdf_files = glob.glob(args.pdfp + "/*.pdf")

    # Check if there are any PDF files
    if len(pdf_files) == 0:
        print(f"{Fore.RED}No PDF documents found in the folder.{Fore.WHITE}")
        sys.exit()

    # Check for required packages and install them if needed
    for package in REQUIRED_PACKAGES:
        if not check_package(package):
            install_package(package)

    # Set the place to check for a local index file
    index_file_path = args.pdfp+'/mylocalFAISSindex.index'
    hash_file_path = args.pdfp+"/"+HASH_STORE_FILENAME

    # Set OpenAI key from config file
    openai_key = load_openai_key()
    os.environ['OPENAI_API_KEY'] = openai_key

    #----------------------------------------------------------------------------------
    # Continue the rest of the logic as before...
    #See if there is a local index and hash file available.
    if os.path.exists(index_file_path):
        haslocalindex = True
    else:
        haslocalindex = False
    if os.path.exists(hash_file_path):
        stored_hash_available = True
    else:
        stored_hash_available = False
    
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

    from texttable import Texttable    
    docs = faiss_index.similarity_search(args.q, k=4)
    for doc in docs:
    #print(Fore.BLUE+str(doc.metadata["page"]) + ":", Fore.WHITE+doc.page_content[:300])
        table = Texttable()
        table.set_deco(Texttable.HEADER)
        table.set_cols_align(["l"])
        table.set_cols_valign(["m"])

        content = Fore.CYAN+doc.page_content[:300]+Fore.WHITE
        first_line = content.split('\n')[0]
        header = Fore.BLUE+str(doc.metadata["page"])+" "+first_line+Fore.WHITE
        after_first_newline = content.split('\n', 1)[1]
    
        print("\n")
        table.add_rows([[header],[after_first_newline]]),
        print(table.draw())
        print("Metadata is:"+Fore.YELLOW+str(doc.metadata)+Fore.WHITE)
        full_path = os.path.abspath(str(doc.metadata["source"]))
        if os_name.startswith('darwin'):
            print(f"To jump directly to this section, copy this command: \n"+Fore.GREEN+"osascript openPage.scpt "+str(full_path)+" "+str(doc.metadata["page"])+Fore.WHITE)
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



if __name__ == "__main__":
    #Parse command line arguments and store them.
    parser = argparse.ArgumentParser(
    description="""Search PDF documents in a given folder for parts that match your question.""",
)
    parser.add_argument('-pdfp', default='./', help="The path of the directory containing your PDF documents to search")
    parser.add_argument('-q', required=True, help="Specifies your question. Follow this with your question in parentheses.")
    args=parser.parse_args()
    args = parser.parse_args()

    main(args)
