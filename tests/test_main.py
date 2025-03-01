"""main tests"""

import sys

from rst2gfm.main import convert_rst_to_md, main


def test_basic_conversion():
    """Test basic RST to Markdown conversion."""
    rst_content = "Simple paragraph"
    md_content = convert_rst_to_md(rst_content)
    assert "Simple paragraph" in md_content


def test_headers():
    """Test header conversion."""
    rst_content = """
Title
=====


Subtitle
--------


Section
~~~~~~~

"""
    md_content = convert_rst_to_md(rst_content)
    assert "# Title" in md_content
    assert "## Subtitle" in md_content
    assert "### Section" in md_content


def test_emphasis():
    """Test emphasis and strong text conversion."""
    rst_content = """
*italic* and **bold** text
"""
    md_content = convert_rst_to_md(rst_content)
    assert "*italic*" in md_content
    assert "**bold**" in md_content


def test_code_blocks():
    """Test code block conversion with language specification."""
    rst_content = """
.. code-block:: python

    def hello():
        print("Hello, world!")
"""
    md_content = convert_rst_to_md(rst_content)
    assert "```python" in md_content
    assert "def hello():" in md_content
    assert 'print("Hello, world!")' in md_content
    assert "```" in md_content


def test_lists():
    """Test bullet list conversion."""
    rst_content = """
- Item 1
- Item 2
  - Nested item
- Item 3
"""
    md_content = convert_rst_to_md(rst_content)
    assert "- Item 1" in md_content
    assert "- Item 2" in md_content
    assert "- Nested item" in md_content
    assert "- Item 3" in md_content


def test_links():
    """Test link conversion."""
    rst_content = "`Link text <https://example.com>`_"
    md_content = convert_rst_to_md(rst_content)
    assert "[Link text](https://example.com)" in md_content


def test_tables():
    """Test table conversion."""
    rst_content = """
+-------+-------+
| Col 1 | Col 2 |
+=======+=======+
| A     | B     |
+-------+-------+
| C     | D     |
+-------+-------+
"""
    md_content = convert_rst_to_md(rst_content)
    assert "| Col 1 | Col 2 |" in md_content
    assert "| --- | --- |" in md_content
    assert "| A | B |" in md_content
    assert "| C | D |" in md_content


def test_literal_text():
    """Test inline code conversion."""
    rst_content = "This is ``code``"
    md_content = convert_rst_to_md(rst_content)
    assert "This is `code`" in md_content


def test_complex_document():
    """Test conversion of a more complex document."""
    rst_content = """
Document Title
=============

Section 1
---------

This is *italic* and **bold** text with ``code``.

.. code-block:: python

    def example():
        return True

- List item 1
- List item 2

+-------+-------+
| Name  | Value |
+=======+=======+
| One   | 1     |
+-------+-------+
| Two   | 2     |
+-------+-------+

`Link <https://example.com>`_
"""
    md_content = convert_rst_to_md(rst_content)

    # Check for all elements
    assert "# Document Title" in md_content
    assert "## Section 1" in md_content
    assert "*italic*" in md_content
    assert "**bold**" in md_content
    assert "`code`" in md_content
    assert "```python" in md_content
    assert "def example():" in md_content
    assert "- List item" in md_content
    assert "| Name | Value |" in md_content
    assert "[Link](https://example.com)" in md_content


def test_command_line_interface(monkeypatch, capsys, tmp_path):
    """Test the command line interface."""
    # Create a temporary input file
    input_file = tmp_path / "input.rst"
    input_file.write_text("**Bold text**")

    # Mock sys.argv
    monkeypatch.setattr(sys, "argv", ["rst2gfm", str(input_file)])

    # Call the main function
    main()

    # Capture stdout and check the output
    captured = capsys.readouterr()
    assert "**Bold text**" in captured.out


def test_math_expressions():
    """Test conversion of math expressions."""
    rst_content = """
    The quadratic formula is :math:`x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}`

    .. math::

       \\begin{aligned}
       (a + b)^2 &= a^2 + 2ab + b^2\\\\
       (a - b)^2 &= a^2 - 2ab + b^2
       \\end{aligned}
    """
    md_content = convert_rst_to_md(rst_content)
    assert (
        "The quadratic formula is $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$"
        in md_content
    )
    assert "$$" in md_content
    assert "\\begin{aligned}" in md_content


def test_admonitions():
    """Test conversion of admonitions."""
    rst_content = """
    .. note::
       This is a note admonition.

    .. warning::
       This is a warning admonition.
    """
    md_content = convert_rst_to_md(rst_content)
    assert "> **Note:**" in md_content
    assert "> This is a note admonition." in md_content
    assert "> **Warning:**" in md_content
    assert "> This is a warning admonition." in md_content


def test_footnotes():
    """Test footnote conversion."""
    rst_content = """
Here is a sentence with a footnote reference [1]_.

.. [1] This is the footnote.
    """
    md_content = convert_rst_to_md(rst_content)
    assert "Here is a sentence with a footnote reference[^1]" in md_content
    assert "[^1]: This is the footnote." in md_content


def test_nested_lists():
    """Test nested list conversion."""
    rst_content = """
* First level

  * Second level

      * Third level

* Another first level

  * Another second level
    """
    md_content = convert_rst_to_md(rst_content)
    assert "- First level" in md_content
    assert "  - Second level" in md_content
    assert "    - Third level" in md_content
    assert "- Another first level" in md_content
    assert "  - Another second level" in md_content


def test_mixed_list_types():
    """Test mixed list types conversion."""
    rst_content = """
* Bullet item

  #. Numbered subitem 1

  #. Numbered subitem 2

* Another bullet item

  #. Another numbered subitem
    """
    md_content = convert_rst_to_md(rst_content)
    assert "- Bullet item" in md_content
    assert "  1. Numbered subitem 1" in md_content
    assert "  1. Numbered subitem 2" in md_content
    assert "- Another bullet item" in md_content
    assert "  1. Another numbered subitem" in md_content


def test_complex_references():
    """Test complex reference handling."""
    rst_content = """
See `Link text <https://example.com>`_ for more information.

This is a reference to :ref:`section-label`.

.. _section-label:

Section Title
------------
This is the referenced section.
"""
    md_content = convert_rst_to_md(rst_content)
    assert "[Link text](https://example.com)" in md_content
    assert "reference to [section-label](#section-label)" in md_content
    assert '<a id="section-label"></a>' in md_content


def test_table_with_no_header():
    """Test table without header conversion."""
    rst_content = """
    .. table:: Table without header
       :class: no-header

       +-------+-------+
       | A     | B     |
       +-------+-------+
       | C     | D     |
       +-------+-------+
    """
    md_content = convert_rst_to_md(rst_content)
    assert "<!-- -->" in md_content  # Header placeholder
    assert "| A | B |" in md_content
    assert "| C | D |" in md_content
    assert "*Table: Table without header*" in md_content


def test_table_with_spans():
    """Test table with row and column spans."""
    rst_content = """
+-------+-------+-------+
| Span  | Col 2 | Col 3 |
+=======+=======+=======+
| Col 1 | Spans2columns |
+-------+-------+-------+
| Spans 2 rows  | Cell  |
+               +-------+
|               | Cell  |
+-------+-------+-------+
    """
    md_content = convert_rst_to_md(rst_content)
    assert (
        "<thead>\n<tr>\n<th>Span</th>\n<th>Col 2</th>\n<th>Col 3</th>\n</tr>\n</thead>"
        in md_content
    )
    assert (
        '<tr>\n<td>Col 1</td>\n<td colspan="2">Spans2columns</td>\n</tr>' in md_content
    )
    assert (
        '<tr>\n<td colspan="2" rowspan="2">Spans 2 rows</td>\n</tr>\n<tr>\n<td>Cell</td>\n</tr>'
        in md_content
    )


def test_code_block_with_language():
    """Test code block with language specification."""
    rst_content = """
.. code-block:: javascript
   :number-lines:

   function test() {
      console.log("Hello");
      return true;
   }
    """
    md_content = convert_rst_to_md(rst_content)
    assert "```" in md_content
    assert "function test() {" in md_content
    assert 'console.log("Hello");' in md_content
    assert "return true;" in md_content
    assert "```" in md_content


def test_line_blocks():
    """Test line block conversion."""
    rst_content = """
| Line one
| Line two
|     Indented line
| Line four
    """
    md_content = convert_rst_to_md(rst_content)
    assert "Line one<br>" in md_content
    assert "Line two<br>" in md_content
    assert "  Indented line<br>" in md_content
    assert "Line four" in md_content


def test_directive_options():
    """Test directive with options."""
    rst_content = """
    .. image:: img/diagram.png
       :width: 600px
       :alt: Architecture diagram
       :align: center
    """
    md_content = convert_rst_to_md(rst_content)
    assert "![Architecture diagram](img/diagram.png)" in md_content
    # GitHub doesn't support width/align in MD, but we can check if there's a comment
    assert "<!-- width: 600px, align: center -->" in md_content
