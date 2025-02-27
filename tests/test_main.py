from rst2gfm.main import convert_rst_to_md


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
    assert "```python"
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
    assert "```python"
    assert "def example():" in md_content
    assert "- List item" in md_content
    assert "| Name | Value |" in md_content
    assert "[Link](https://example.com)" in md_content


def test_command_line_interface(monkeypatch, capsys, tmp_path):
    """Test the command line interface."""
    from rst2gfm.main import main
    import sys

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
