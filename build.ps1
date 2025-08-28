Write-Host "Building Sudoku Executable"
Remove-Item -Path "./build" -Recurse
Remove-Item -Path "./dist" -Recurse
Remove-Item -Path "./sudoku.spec"
New-Item -ItemType Directory -Path "./dist"
Copy-Item -Path "./resources" -Destination "./dist/" -Recurse
py -m PyInstaller ./game.py -n sudoku -w -F -i ./resources/icon.ico
Write-Host "Sudoku Executable Created"
