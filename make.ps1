Param(
    [Parameter(Mandatory)]
    [ValidateSet("install", "format", "lint", "build", "clean")]
    [string]
    $command
)

if ($command -eq "install") {
    # check python installation
    if ($null -eq $(Get-Command python -ea SilentlyContinue)) {
        Write-Host "Python is not installed."
        exit 1
    }

    # check python version
    if ($(python -V) -match "(?<=Python 3\.)[0-9]+(?=\.[0-9]+)") {
        $minor = $Matches[0] -as [System.Int16]
        if ($minor -lt 10) {
            Write-Host "Python version must be 3.10 or higher."
            Write-Host "Current version is $(python -V)"
            exit 1
        }
    } else {
        Write-Host "Python version must be 3.10 or higher."
        Write-Host "Current version is $(python -V)"
        exit 1
    }

    # check poetry installation
    if ($null -eq (python -m pip list | Select-String "poetry")) {
        Write-Host "Install poetry"
        python -m pip install pip -U
        python -m pip install poetry
    }

    # install package
    python -m poetry config --local virtualenvs.in-project true
    python -m poetry config --local virtualenvs.create true
    python -m poetry install
} elseif ($command -eq "format") {
    python -m poetry run black .
} elseif ($command -eq "lint") {
    python -m poetry run pflake8
} elseif ($command -eq "build") {
    pyinstaller ./quiz_practice/app/main.py --onefile --clean --noconsole
 }elseif ($command -eq "clean") {
    Remove-Item -Recurse ./.venv/ -ea SilentlyContinue
    Remove-Item -Recurse ./dist/ -ea SilentlyContinue
    Remove-Item -Recurse ./build/ -ea SilentlyContinue
    Remove-Item ./*.spec -ea SilentlyContinue
}