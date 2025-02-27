# rst2gfm - reStructuredText to GitHub Flavored Markdown Converter

A Python tool that converts reStructuredText (RST) documents to GitHub Flavored Markdown (GFM).

## Features

- Converts RST documents to GitHub Flavored Markdown
- Preserves document structure including headings, paragraphs, and formatting
- Supports common RST elements:
  - Headers/sections
  - Text formatting (bold, italic)
  - Code blocks with language highlighting
  - Lists (bullet and enumerated)
  - Tables
  - Links
  - Images
  - Block quotes
  - Definition lists

## Installation

```bash
pip install rst2gfm
```

Or install from source:

```bash
git clone https://github.com/pdh/rst2gfm.git
cd rst2gfm
pip install -e .
```

## Usage

### Command Line

Convert an RST file to Markdown:

```bash
rst2gfm input.rst -o output.md
```

Use stdin/stdout:

```bash
cat input.rst | rst2gfm > output.md
```

### Python API

```python
from rst2gfm import convert_rst_to_md

# Convert RST string to Markdown
rst_content = "**Bold text** in reStructuredText"
md_content = convert_rst_to_md(rst_content)
print(md_content)

# Convert RST file to Markdown file
with open('input.rst', 'r') as f:
    rst_content = f.read()

md_content = convert_rst_to_md(rst_content)

with open('output.md', 'w') as f:
    f.write(md_content)
```

## Limitations

This converter handles most common RST elements, but some advanced features may not be fully supported:

- Complex nested structures
- Custom RST directives
- Some Sphinx-specific extensions

## Development

### Running Tests

```bash
pip install pytest
pytest
```
