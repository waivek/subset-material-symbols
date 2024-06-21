from waivek import Timer   # Single Use
timer = Timer()
from waivek import Code    # Multi-Use
from waivek import handler # Single Use
from waivek import ic, ib     # Multi-Use, import time: 70ms - 110ms
from waivek import rel2abs
import shutil
import urllib.parse
import os
import sys
import argparse
import argcomplete
import subprocess
import textwrap
import base64
Code; ic; ib; rel2abs

def get_ttf_paths() -> list[str]:
    styles = "Outlined", "Rounded", "Sharp"
    filenames = [ "MaterialSymbols{style}[FILL,GRAD,opsz,wght].ttf".format(style=style) for style in styles ]
    paths = [ rel2abs("data/" + filename) for filename in filenames ]
    return paths

def get_ttf_path(style):
    paths = get_ttf_paths()
    for path in paths:
        if style.lower() in path.lower():
            return path
    raise ValueError("Style not found: " + style)

def ensure():
    ANSI_RED_BG_BLACK_FG = "\033[41;30m"
    ANSI_GREEN_BG_BLACK_FG = "\033[42;30m"
    ANSI_BLUE_BG_BLACK_FG = "\033[44;30m"
    ANSI_RESET = "\033[0m"

    print()
    print(ANSI_BLUE_BG_BLACK_FG + " ENSURE " + ANSI_RESET)
    print()
    # check if data/ exists
    data_dir = rel2abs("data/")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print()
        print(ANSI_GREEN_BG_BLACK_FG + " CREATE " + ANSI_RESET + " " + data_dir)
    print(Code.LIGHTGREEN_EX + "✓" + " data/ exists")

    # check if aria2c exists
    executable_name = "aria2c"
    executable_path = shutil.which(executable_name)
    if executable_path is None:
        print("Executable not found: " + executable_name)
        return
    print(Code.LIGHTGREEN_EX + "✓" + " aria2c executable exists")

    # check if ttf files exist, if not generate .afl file and prompt user to download
    paths = get_ttf_paths()
    missing_files = [ path for path in paths if not os.path.exists(path) ]
    if missing_files:
        print()
        print(ANSI_RED_BG_BLACK_FG + " MISSING " + ANSI_RESET)
        print()
        for path in missing_files:
            print(" " * 4 + path)
        afl_file_contents = get_afl_file_contents()
        afl_path = rel2abs("download-material-symbols.afl")
        with open(afl_path, "w") as f:
            f.write(afl_file_contents)
        print()
        print(ANSI_GREEN_BG_BLACK_FG + " WRITE " + ANSI_RESET + " " + afl_path)
        return

    print(Code.LIGHTGREEN_EX + "✓" + " TTF files exist")

def get_afl_file_contents():
    styles = "Outlined", "Rounded", "Sharp"
    filenames = [ "MaterialSymbols{style}[FILL,GRAD,opsz,wght].ttf".format(style=style) for style in styles ]
    prefix = "https://github.com/google/material-design-icons/raw/master/variablefont/"
    escaped_filenames = [ urllib.parse.quote(filename) for filename in filenames ]
    raw_github_urls = [ prefix + escaped_filename for escaped_filename in escaped_filenames ]
    lines = []
    INDENT = " " * 4
    for filename, url in zip(filenames, raw_github_urls):
        lines.append(url)
        lines.append(INDENT + "out=" + filename)
        lines.append(INDENT + "dir=" + rel2abs("data/"))
        lines.append(INDENT + "auto-file-renaming=false")
        lines.append(INDENT + "allow-overwrite=false")
    afl_file_contents = "\n".join(lines)
    return afl_file_contents

def get_inline_stylesheet_string(style, icons, woff_path):
    with open(woff_path, "rb") as f:
        woff_bytes = f.read()
    woff_base64 = base64.b64encode(woff_bytes).decode("utf-8")
    filesize = os.path.getsize(woff_path)
    icons_comma_sep = ",".join(icons)
    filesize_kb = filesize / 1024


    template = f"""
        @font-face {{
            font-family: 'Material Symbols {style.capitalize()} [{icons_comma_sep}]';
            font-style: normal;
            font-weight: 100 700;
            /* size: {filesize_kb:.2f}KB */
            src: url(data:font/woff2;charset=utf-8;base64,{woff_base64}) format('woff2');
        }}

        .material-symbols-{style.lower()} {{
            font-family: 'Material Symbols {style.capitalize()} [{icons_comma_sep}]';
            font-weight: normal;
            font-style: normal;
            font-size: 24px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }} 
    """
    
    string = template
    string = textwrap.dedent(string).strip()
    return string

def main():
    ensure()
    # argparse
    parser = argparse.ArgumentParser(description="Subset Material Symbols")
    parser.add_argument("--style", type=str, choices=["outlined", "rounded", "sharp"], help="Style of the font")
    parser.add_argument("icons", type=str, nargs="+", help="List of icons to subset")
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    style = args.style
    icons = args.icons
    ttf_path = get_ttf_path(style)
    # subprocess
    #  subset_gf_icons MaterialSymbolsOutlined\[FILL\,GRAD\,opsz\,wght\].ttf menu alarm_on
    command = ["subset_gf_icons", "--flavor", "woff2", ttf_path] + icons
    print(" ".join(command))
    result = subprocess.run(command, capture_output=True)
    exit_code = result.returncode
    stdout = result.stdout.decode("utf-8")
    path = stdout.replace("Wrote subset to ", "").strip()
    assert os.path.exists(path)
    assert exit_code == 0
    ANSI_GREEN_BG_BLACK_FG = "\033[42;30m"
    ANSI_RESET = "\033[0m"
    path_size = os.path.getsize(path)
    print()
    print(ANSI_GREEN_BG_BLACK_FG + " WRITE " + ANSI_RESET + " " + path + " [" + "{:.2f}".format(path_size / 1024) + "KB]")
    # /home/vivek/subset-material-symbols/data/MaterialSymbolsRounded[FILL,GRAD,opsz,wght]-s
    print()
    css_string = get_inline_stylesheet_string(style, icons, path)
    output_filename = "material-symbols-{style}[{icons}].css".format(style=style.lower(), icons=",".join(icons))
    output_path = rel2abs("data/" + output_filename)

    with open(output_path, "w") as f:
        f.write(css_string)
    file_size = os.path.getsize(output_path)
    print(ANSI_GREEN_BG_BLACK_FG + " WRITE " + ANSI_RESET + " " + output_path + " [" + "{:.2f}".format(file_size / 1024) + "KB]")






if __name__ == "__main__":
    with handler():
        main()
# run.vim:--style=rounded update home
