Write-Host "Building Sudoku Executable"
Remove-Item -Path "./build" -Recurse
Remove-Item -Path "./dist" -Recurse
Remove-Item -Path "./sudoku.spec"
py -m PyInstaller ./game.py -n sudoku -w -F -i ./resources/icon.ico
Copy-Item -Path "./resources" -Destination "./dist/" -Recurse
Write-Host "Sudoku Executable Created"
