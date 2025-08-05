Write-Host "Building Sudoku Executable"
Remove-Item -Path "./build" -Recurse
Remove-Item -Path "./dist" -Recurse
Remove-Item -Path "./sudoku.spec"
py -m PyInstaller ./game.py -n sudoku -w -F
Copy-Item -Path "./arial" -Destination "./dist/" -Recurse
Write-Host "Sudoku Executable Created"
