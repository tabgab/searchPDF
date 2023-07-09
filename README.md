Search PDF documents in a given folder for parts that match your question.

    This tool searches all PDF documents in the folder specified, with the questions specified.
    If no path is specified for the PDFs, it is assumed to be the current folder.

    You have to specify an OpenAI API key for this tool to work. This, you must store in
    the openai_key.txt file, please create this file yourself and it should only contain
    your own OpenAI API key.

    The tool will build a local index to avoid having to index the documents every time,
    and if no changes are made to the documents, the stored index will be used for the 
    next query as well.

    A hash will be calculated to keep track of any changes and if changes are detected,
    the index will be regenerated and stored locally again for later use.

    The tool will list the document and page where a similar text was found and also
    provide you with commands you can simply copy-paste to quickly open the documents
    at the correct page.

    Unfortunately, since this is a tricky thing to do, the tool keeps track on what
    operating system it is running on, and provides specific commands.
    For Windows and macOS, helper scripts are needed and are provided for this to work.

