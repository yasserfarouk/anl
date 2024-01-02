@echo off

rem Iterate through notebooks and convert to Markdown (4 times for robustness)
for %%notebook in ("..\notebooks\tutorials\*.ipynb") do (
    jupyter nbconvert --TagRemovePreprocessor.remove_cell_tags='{"remove_cell"}' --to markdown "%%notebook"
    jupyter nbconvert --TagRemovePreprocessor.remove_cell_tags='{"remove_cell"}' --to markdown "%%notebook"
    jupyter nbconvert --TagRemovePreprocessor.remove_cell_tags='{"remove_cell"}' --to markdown "%%notebook"
    jupyter nbconvert --TagRemovePreprocessor.remove_cell_tags='{"remove_cell"}' --to markdown "%%notebook"
)

rem Remove and recreate the docs/tutorials directory
rmdir /s /q docs\tutorials
mkdir docs\tutorials

rem Move Markdown files and static files
move "..\notebooks\tutorials\*.md" docs\tutorials
copy .\static_tutorials\*.* docs\tutorials

rem Move files with _files suffix
for %%fils in ("..\notebooks\tutorials\*_files") do (
    move "%%fils" docs\tutorials
)

rem Create a subdirectory for notebooks
mkdir docs\tutorials\notebooks

rem Copy notebooks to the subdirectory
for %%notebook in ("..\notebooks\tutorials\*.ipynb") do (
    copy "%%notebook" docs\tutorials\notebooks
)

rem Add download links to Markdown files
for %%mdfile in (docs\tutorials\*.md) do (
    for %%i in ("%%mdfile") do set filename=%%~ni
    echo [Download Notebook](/tutorials/notebooks/%filename%.ipynb) >> "%%mdfile"
)

echo ------------------------------------------------

rem Build and deploy documentation (assuming mkdocs is installed)
mkdocs build
mkdocs gh-deploy

rem (Commented-out section for image handling is omitted for now, as it requires further clarification on expected behavior in Windows.)
