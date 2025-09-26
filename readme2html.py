from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.presets import commonmark




HEADER: str = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>body { font-family: sans-serif; padding: 0 1rem 4rem 1rem; } main { display: block; max-width: 900px; }</style>
<title>HYLANDBOOK</title>
</head>
<body>
<main>
'''.strip()

FOOTER: str = '''
</main>
</body>
</html>
'''.strip()




if __name__ == '__main__':
    md_config = commonmark.make()
    md = MarkdownIt(md_config)

    cwd: Path = Path().cwd()

    fmap: list[dict[str, Path]] = [
        {
            'in': cwd / 'README.md',
            'out': cwd / 'dist' / 'README.html',
        },
        {
            'in': cwd / 'CHANGELOG.md',
            'out': cwd / 'dist' / 'CHANGELOG.html',
        },
    ]

    for f in fmap:
        print(f"{f['in']} -> {f['out']}")
        f['out'].write_text(HEADER + md.render(f['in'].read_text()) + FOOTER)
