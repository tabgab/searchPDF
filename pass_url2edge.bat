@echo off
setlocal

:: Set your URL from the command line argument
set "URL=%~1"

:: Create a temporary HTML file
set "tempFile=%TEMP%\redir.html"

(
    echo ^<html^>
    echo ^<body^>
    echo ^<script type='text/javascript'^>
    echo window.location = '%URL%';
    echo ^</script^>
    echo ^</body^>
    echo ^</html^>
) > "%tempFile%"

:: Open the temporary file in Edge
start msedge "%tempFile%"

endlocal
