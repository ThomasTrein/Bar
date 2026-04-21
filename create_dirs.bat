@echo off
setlocal enabledelayedexpansion

cd /d "c:\Users\Gebruiker\Documents\KSA\Bar"

echo Creating directories...
echo.

for %%D in (database services hardware routes videos backups) do (
    if exist "%%D" (
        echo SUCCESS: %%D - Already exists
    ) else (
        mkdir "%%D"
        if !errorlevel! equ 0 (
            echo SUCCESS: %%D - Created successfully
        ) else (
            echo FAILED: %%D - Creation failed
        )
    )
)

if exist "static" (
    echo SUCCESS: static - Already exists
) else (
    mkdir "static"
    echo SUCCESS: static - Created successfully
)

for %%D in (css js images) do (
    if exist "static\%%D" (
        echo SUCCESS: static\%%D - Already exists
    ) else (
        mkdir "static\%%D"
        if !errorlevel! equ 0 (
            echo SUCCESS: static\%%D - Created successfully
        ) else (
            echo FAILED: static\%%D - Creation failed
        )
    )
)

if exist "templates" (
    echo SUCCESS: templates - Already exists
) else (
    mkdir "templates"
    echo SUCCESS: templates - Created successfully
)

for %%D in (kiosk admin) do (
    if exist "templates\%%D" (
        echo SUCCESS: templates\%%D - Already exists
    ) else (
        mkdir "templates\%%D"
        if !errorlevel! equ 0 (
            echo SUCCESS: templates\%%D - Created successfully
        ) else (
            echo FAILED: templates\%%D - Creation failed
        )
    )
)

if exist "uploads" (
    echo SUCCESS: uploads - Already exists
) else (
    mkdir "uploads"
    echo SUCCESS: uploads - Created successfully
)

for %%D in (persons products) do (
    if exist "uploads\%%D" (
        echo SUCCESS: uploads\%%D - Already exists
    ) else (
        mkdir "uploads\%%D"
        if !errorlevel! equ 0 (
            echo SUCCESS: uploads\%%D - Created successfully
        ) else (
            echo FAILED: uploads\%%D - Creation failed
        )
    )
)

echo.
echo Directory creation complete.
