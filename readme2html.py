from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.presets import commonmark




HEADER: str = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>body { font-family: sans-serif; padding: 0 1rem 4rem 1rem; } #readme { max-width: 900px; }</style>
<title>HYLANDBOOK</title>
</head>
<body>
<div id="readme">
'''.strip()

FOOTER: str = '''
</div><!--/#readme-->
</body>
</html>
'''.strip()




if __name__ == '__main__':
    in_file: Path = Path().cwd() / 'README.md'
    out_file: Path = Path().cwd() / 'dist' / 'README.html'
    md_config = commonmark.make()
    md = MarkdownIt(md_config)
    out_file.write_text(HEADER + md.render(in_file.read_text()) + FOOTER)
