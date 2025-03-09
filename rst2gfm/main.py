"""rst2gfm - restructured text to github flavored markdown"""

import argparse
import sys
import re
from docutils.core import publish_parts
from docutils.writers import Writer
from docutils.nodes import NodeVisitor, SkipNode


class MarkdownTranslator(NodeVisitor):
    """
    Translates reStructuredText nodes to GitHub Flavored Markdown.
    """
    # pylint: disable=unused-argument
    # pylint: disable=missing-docstring disable=invalid-name

    def __init__(self, document):
        """
        The `__init__` method initializes a new instance of the class with a document. It sets up various attributes to manage the parsing and processing of the document.
        Args:
            document any: The document to be processed.
        """
        super().__init__(document)
        self.output = []
        self.list_depth = 0
        self.section_level = 0
        self.in_code_block = False
        self.in_line_block = False
        self.code_language = "python"
        self.in_table = False
        self.table_data = []
        self.table_has_header = True
        self.table_caption = ""
        self.table_type = "simple"
        self.current_row = []
        self.entry_text = []
        self.list_type = []
        self.reference_stack = []
        self.pending_refs = []
        self.refs_map = {}
        self.skip_children = False
        self.spans = []
        self.current_cell_colspan = None
        self.current_cell_rowspan = None
        self.in_footnote = False
        self.footnote_label_seen = False
        self.math_content = ""
        self.math_start = 0

    def _make_anchor(self, ref_id):
        """
        Convert RST reference ID to GitHub-compatible anchor.
        Args:
            ref_id str: The RST reference ID to be converted.
        Returns:
            str: The GitHub-compatible anchor.
        """
        # GitHub lowercases anchors and replaces spaces with hyphens
        anchor = ref_id.lower().replace(" ", "-")
        # Remove special characters
        anchor = re.sub(r"[^\w\-]", "", anchor)
        return anchor

    def _normalize_refname(self, refname):
        """Normalize reference name for use in markdown reference-style links."""
        return refname.lower().replace(" ", "-")

    def astext(self):
        return "".join(self.output)

    def default_visit(self, node):
        """Default visit method for all nodes."""

    def default_departure(self, node):
        """
        Default departure method for all nodes.
        Args:
            node node: The node for which the departure is being handled.
        """

    def visit_directive(self, node):
        if node.tagname == "math":
            self.visit_math_block(node)
        if node.tagname == "code-block" or (
            hasattr(node, "attributes")
            and "code-block" in node.attributes.get("classes", [])
        ):
            self.in_code_block = True

            # Extract language
            language = ""
            if len(node.arguments) > 0:
                language = node.arguments[0]

            # Handle options
            linenos = "linenos" in node.options
            emphasize_lines = node.options.get("emphasize-lines", "")

            # Add comment for options that GFM doesn't support natively
            if linenos or emphasize_lines:
                self.output.append("\n# Options: ")
                if linenos:
                    self.output.append("line numbers, ")
                if emphasize_lines:
                    self.output.append(f"emphasize lines {emphasize_lines}")
                self.output.append("\n")

            # Start code block
            self.output.append(f"\n```{language}")

    def depart_directive(self, node):
        """
        Process the departure of a directive in the document.
        Args:
            node DirectiveNode: The directive node being processed.
        """
        if node.tagname == "code-block" or (
            hasattr(node, "attributes")
            and "code-block" in node.attributes.get("classes", [])
        ):
            self.in_code_block = False
            self.output.append("\n```\n\n")

    def visit_document(self, node):
        """visit documents"""

    def depart_document(self, node):
        """depart document"""
        # Add any pending reference definitions at the end
        if self.pending_refs:
            self.output.append("\n\n")
            for ref_id, refname in self.pending_refs:
                if refname in self.refs_map:
                    self.output.append(f"[{ref_id}]: {self.refs_map[refname]}\n")

    def visit_section(self, node):
        """
        This method is used to visit a section, increasing the section level.
        Args:
            node Any: The section node to visit.
        """
        self.section_level += 1

    def depart_section(self, node):
        """
        This method decreases the section level.
        Params:
            node Node: The node representing the section to be departed.
        Returns:
            None: This method does not return any value.
        """
        self.section_level -= 1

    def visit_subtitle(self, node):
        """
        handle subtitle
        """
        self.output.append("## ")
        self.section_level += 1

    def depart_subtitle(self, node):
        """
        handle subtitle exit
        """
        self.output.append("\n\n")
        # TODO not sure if this section leveling is quite right
        # self.section_level -= 1

    def visit_title(self, node):
        """
        handle rst title
        """
        if self.in_table:
            # This is a table caption/title
            self.table_caption = node.astext()
        else:
            # Regular section title
            self.output.append(f"{'#' * (self.section_level + 1)} ")

    def depart_title(self, node):
        """handle title exit"""
        self.output.append("\n\n")

    def visit_paragraph(self, node):
        """
        handle rst paragraph
        """

    def depart_paragraph(self, node):
        """
        This method is responsible for handling the exit of an RST (ReStructuredText) paragraph. When an RST paragraph ends, it appends a double newline character to the output to ensure proper formatting in the generated document.
        Args:
            self object: The instance of the class.
            node object: The node representing the RST paragraph being exited.
        Returns:
            None: This method does not return any value.
        """
        self.output.append("\n\n")

    def visit_Text(self, node):
        """
        handle rst Text
        Args:
            node Any: The node being visited.
        """
        text = node.astext()

        # Check for :ref: pattern
        ref_pattern = r":ref:`([^`]+)`"
        if re.search(ref_pattern, text):
            # Replace :ref:`target` with [target](#target)
            processed_text = re.sub(ref_pattern, r"[\1](#\1)", text)
            if self.in_table and self.entry_text is not None:
                self.entry_text.append(processed_text)
            else:
                self.output.append(processed_text)
            return

        # Regular text handling
        if self.in_table and self.entry_text is not None:
            self.entry_text.append(text)
        else:
            self.output.append(text)

    def visit_image(self, node):
        """
        handle rst image
        Args:
            node dict: The dictionary representing the image node.
        """
        uri = node.get("uri", "")
        alt = node.get("alt", "")

        # Extract image options
        options = []
        for option in ["width", "height", "scale", "align"]:
            if option in node:
                options.append(f"{option}: {node[option]}")

        # Add the image with alt text
        self.output.append(f"![{alt}]({uri})")

        # Add options as HTML comment if present
        if options:
            self.output.append(f" <!-- {', '.join(options)} -->")

    def depart_image(self, node):
        pass

    def visit_line_block(self, node):
        """Handle RST line blocks."""
        self.in_line_block = True

    def depart_line_block(self, node):
        """
        This method is responsible for departing from a line block by setting the `in_line_block` attribute to False and appending two newline characters to the `output` list.
        Params:
            node any: The node representing the line block to depart from.
        """
        self.in_line_block = False
        self.output.append("\n\n")

    def visit_line(self, node):
        """Handle individual lines in a line block."""
        # Get the original source text to preserve indentation
        text = node.astext()
        # Check if this line has indentation
        indent = ""
        if hasattr(node, "indent"):
            indent = " " * node.indent
        else:
            # Try to extract indentation from the text
            match = re.match(r"^(\s+)", text)
            if match:
                indent = match.group(1)

        # Add the line with preserved indentation
        self.output.append(f"{indent}{text}<br>\n")
        raise SkipNode

    def depart_line(self, node):
        pass

    def visit_emphasis(self, node):
        """
        Adds an asterisk (*) to the output list.
        Params:
            node any: The node to visit.
        """
        self.output.append("*")

    def depart_emphasis(self, node):
        self.output.append("*")

    def visit_strong(self, node):
        """
        Visits a strong node and appends '**' to the output.
        Params:
            node Node: The strong node to visit.
        Returns:
            None: The method does not return any value.
        """
        self.output.append("**")

    def depart_strong(self, node):
        self.output.append("**")

    def visit_literal(self, node):
        self.output.append("`")

    def depart_literal(self, node):
        """
        Appends a backtick (`) to the output.
        Args:
            node any: The node to process.
        """
        self.output.append("`")

    def visit_bullet_list(self, node):
        """
        Visits a bullet list node and updates the list depth and type.
        Args:
            node object: The AST node representing the bullet list.
        """
        self.list_depth += 1
        self.list_type.append("bullet")

        # Ensure proper spacing between list items
        if self.list_depth > 1 and self.output and self.output[-1] != "\n":
            self.output.append("\n")

    def depart_bullet_list(self, node):
        """
        Decreases the current list depth and pops the last list type from the stack, then appends a newline character to the output.
        Args:
            node any: The node parameter is not used within the method, it appears to be a placeholder or documentation error.
        Returns:
            None: The method does not return any value.
        """
        self.list_depth -= 1
        self.list_type.pop()
        self.output.append("\n")

    def visit_list_item(self, node):
        """
        Visits a list item node and appends it to the output with appropriate indentation and list marker based on the list type.
        Args:
            node Any: The node to visit.
        Yields:
            None: None
        """
        indent = "  " * (self.list_depth - 1)
        ## Check if we have list_type (we should)
        if self.list_type and len(self.list_type) > 0:
            if self.list_type[-1] == "bullet":
                self.output.append(f"\n{indent}- ")
            else:  # enumerated
                self.output.append(f"\n{indent}1. ")
        else:
            # Fallback if list_type is empty
            self.output.append(f"\n{indent}- ")

        # Store the current position to track if we need to handle nested content

    def depart_list_item(self, node):
        """
        Removes any incorrect formatting that might have been added to a list item and cleans up the content by removing unwanted bold markers or colons.
        Args:
            node any: The node representing the list item to be processed.
        Returns:
            void: The method does not return any value.
        """
        # Remove any incorrect formatting that might have been added
        if hasattr(self, "list_item_start"):
            content = "".join(self.output[self.list_item_start :])
            # Remove any unwanted bold markers or colons that might have been added
            content = content.replace("**", "").replace(":\n", "\n")
            self.output = self.output[: self.list_item_start]
            self.output.append(content)
            delattr(self, "list_item_start")

    def visit_reference(self, node):
        """
        This method is called when a reference node is visited.
        Args:
            self object: The instance of the class.
            node node: The reference node being visited.
        """
        self.reference_stack.append({"start": len(self.output), "text": node.astext()})

        # Determine reference type
        if "refuri" in node:
            # External URI
            self.output.append("[")
        elif "refid" in node:
            # Internal reference
            self.output.append("[")
        elif "refname" in node:
            # Named reference
            self.output.append("[")
        else:
            # Unknown reference type
            self.output.append("[")

    def depart_reference(self, node):
        if not self.reference_stack:
            return

        ref_info = self.reference_stack.pop()
        ref_text = ref_info["text"]

        # Replace content with reference text if needed
        if len(self.output) > ref_info["start"] + 1:
            # Content was added by children, replace it
            self.output = self.output[: ref_info["start"] + 1]
            self.output.append(ref_text)

        if "refuri" in node:
            # External URI
            self.output.append(f"]({node['refuri']})")
        elif "refid" in node:
            # Internal reference - convert to GFM compatible anchor
            anchor = self._make_anchor(node["refid"])
            self.output.append(f"](#{anchor})")
        elif "refname" in node:
            # Named reference - use reference-style link
            ref_id = self._normalize_refname(node["refname"])
            self.output.append(f"][{ref_id}]")
            self.pending_refs.append((ref_id, node["refname"]))
        else:
            self.output.append("]")

    def visit_literal_block(self, node):
        """
        Visits a literal block node in the AST and formats it as a code block in Markdown, potentially with language syntax highlighting and line number options.
        Args:
            node dict: The node representing the literal block in the AST.
        """
        self.in_code_block = True
        language = ""
        # Check for language in various attributes
        if "language" in node:
            language = node["language"]
        elif "classes" in node and len(node["classes"]) > 0:
            # RST often puts language in classes
            for cls in node["classes"]:
                if cls != "code":
                    language = cls
                    break

        # TODO docutils doesn't support linenos, highlight_args, emphasis
        # https://docutils.sourceforge.io/docs/ref/rst/directives.html#code
        options = []
        if "linenos" in node or any(
            "linenos" in cls for cls in node.get("classes", [])
        ):
            options.append("line numbers")
        if "highlight_args" in node and "linenostart" in node["highlight_args"]:
            options.append(
                f"starting from line {node['highlight_args']['linenostart']}"
            )
        if "highlight_args" in node and "hl_lines" in node["highlight_args"]:
            options.append(f"highlighting lines {node['highlight_args']['hl_lines']}")

        # Add language specifier to code block
        self.output.append(f"\n```{language}")
        # # Add comment for options
        if options:
            self.output.append(f"\n# {', '.join(options)}")

    def depart_literal_block(self, node):
        """
        This method is responsible for departing from a literal block in the document and appending a closing code block marker to the output.
        """
        self.in_code_block = False
        self.output.append("\n```\n\n")

    def visit_table(self, node):
        self.table_data = []
        self.in_table = True
        self.spans = []
        # Detect table type from node attributes
        if "classes" in node:
            if "csv-table" in node["classes"]:
                self.table_type = "csv"
            elif "list-table" in node["classes"]:
                self.table_type = "list"
            elif "grid" in node["classes"]:
                self.table_type = "grid"
            else:
                self.table_type = "simple"
        else:
            self.table_type = "simple"

        # Check if table should have a header
        # Look for classes or other indicators in the node
        if "classes" in node and "no-header" in node["classes"]:
            self.table_has_header = False
        else:
            self.table_has_header = True

    def depart_table(self, node):
        if not self.table_data:
            return

        # Process spans and convert to GitHub Markdown or HTML
        has_complex_spans = any(span.get("morerows", 0) > 0 for span in self.spans)

        if has_complex_spans:
            # For tables with row spans, use HTML
            self._convert_to_html_table()
        else:
            # For tables with only column spans, use markdown with || trick
            self._convert_to_markdown_table()

    def _convert_to_markdown_table(self):
        # Process table data into markdown table
        col_count = max(len(row) for row in self.table_data)

        table_md = []

        if self.table_has_header and len(self.table_data) > 0:
            # Use first row as header
            header = self.table_data[0]
            # Ensure header has enough columns
            while len(header) < col_count:
                header.append("")
            table_md.append("| " + " | ".join(header) + " |")
            table_md.append("| " + " | ".join(["---"] * len(header)) + " |")
            data_rows = self.table_data[1:]
        else:
            # No header - use GitHub's HTML comment hack for headerless tables
            empty_header = ["<!-- -->"] * col_count
            table_md.append("| " + " | ".join(empty_header) + " |")
            table_md.append("| " + " | ".join(["---"] * col_count) + " |")
            data_rows = self.table_data
        # Add data rows
        for row_idx, row in enumerate(data_rows):
            row_str = "| "
            col_idx = 0
            while col_idx < len(row):
                # Check if this cell has a colspan
                span = next(
                    (
                        s
                        for s in self.spans
                        if s["row"] == row_idx + 1 and s["col"] == col_idx
                    ),
                    None,
                )
                if span and span["morecols"] > 0:
                    # Add the cell content
                    row_str += row[col_idx] + " |" + "".join([""] * span["morecols"])
                    col_idx += span["morecols"] + 1
                else:
                    # Regular cell
                    row_str += row[col_idx] + " | "
                    col_idx += 1
            table_md.append(row_str)

        if hasattr(self, "table_caption"):
            table_md.append(f"\n*Table: {self.table_caption}*\n")
            delattr(self, "table_caption")

        self.output.append("\n" + "\n".join(table_md) + "\n\n")
        self.in_table = False

    def _convert_to_html_table(self):
        html = ["<table>"]

        # Add header row
        if self.table_data:
            html.append("<thead>")
            html.append("<tr>")
            for cell in self.table_data[0]:
                html.append(f"<th>{cell}</th>")
            html.append("</tr>")
            html.append("</thead>")

        # Add data rows
        if len(self.table_data) > 1:
            html.append("<tbody>")
            for row_idx, row in enumerate(self.table_data[1:]):
                html.append("<tr>")
                col_idx = 0
                while col_idx < len(row):
                    # Check for spans
                    span = next(
                        (
                            s
                            for s in self.spans
                            if s["row"] == row_idx + 1 and s["col"] == col_idx
                        ),
                        None,
                    )
                    if span:
                        colspan = span.get("morecols", 0) + 1
                        rowspan = span.get("morerows", 0) + 1
                        attrs = []
                        if colspan > 1:
                            attrs.append(f'colspan="{colspan}"')
                        if rowspan > 1:
                            attrs.append(f'rowspan="{rowspan}"')

                        html.append(f"<td {' '.join(attrs)}>{row[col_idx]}</td>")
                        col_idx += colspan
                    else:
                        html.append(f"<td>{row[col_idx]}</td>")
                        col_idx += 1
                html.append("</tr>")
            html.append("</tbody>")

        html.append("</table>")
        self.output.append("\n" + "\n".join(html) + "\n\n")

    def visit_row(self, node):
        self.current_row = []

    def depart_row(self, node):
        self.table_data.append(self.current_row)

    def visit_entry(self, node):
        self.entry_text = []

        # Track spans
        morecols = node.get("morecols", 0)
        morerows = node.get("morerows", 0)
        self.current_cell_colspan = morecols
        self.current_cell_rowspan = morerows

        if morecols > 0 or morerows > 0:
            # Store span information for this cell
            self.spans.append(
                {
                    "row": len(self.table_data),
                    "col": len(self.current_row),
                    "morecols": morecols,
                    "morerows": morerows,
                }
            )

    def depart_entry(self, node):
        text = "".join(self.entry_text).replace("\n", "<br>").strip()

        # Add the cell to the current row
        self.current_row.append(text)

        # If we have colspan, add empty cells to account for it
        if hasattr(self, "current_cell_colspan") and self.current_cell_colspan > 1:
            for _ in range(self.current_cell_colspan - 1):
                self.current_row.append("")
        self.entry_text = None

    def visit_transition(self, node):
        self.output.append("\n---\n\n")

    def depart_transition(self, node):
        pass

    def visit_block_quote(self, node):
        self.output.append("\n> ")

    def depart_block_quote(self, node):
        self.output.append("\n\n")

    def visit_enumerated_list(self, node):
        self.list_depth += 1
        self.list_type.append("enumerated")

    def depart_enumerated_list(self, node):
        self.list_depth -= 1
        self.output.append("\n")
        self.list_type.pop()

    def visit_definition_list(self, node):
        pass

    def depart_definition_list(self, node):
        self.output.append("\n")

    def visit_definition_list_item(self, node):
        pass

    def depart_definition_list_item(self, node):
        pass

    def visit_term(self, node):
        self.output.append("\n**")

    def depart_term(self, node):
        self.output.append("**\n")

    def visit_definition(self, node):
        self.output.append(": ")

    def depart_definition(self, node):
        self.output.append("\n")

    def visit_role(self, node):
        """Handle roles like :ref:"""
        role_name = node.get("name")
        if role_name == "ref":
            # This is a reference to an internal target
            target = node.get("target")
            # Create a Markdown link to the target
            self.output.append(f"[{target}](#{target})")
            # Skip processing children
            raise SkipNode

    def visit_admonition(self, node):
        """Generic handler for admonition nodes."""
        self.output.append("\n> ")

        # Get admonition type from node class
        admonition_type = node.__class__.__name__
        if admonition_type.endswith("Admonition"):
            admonition_type = admonition_type[:-10]  # Remove 'Admonition' suffix

        # Add admonition title in bold
        self.output.append(f"\n**{admonition_type.title()}:** ")

    def depart_admonition(self, node):
        self.output.append("\n\n")

    # Add specific handlers for common admonition types
    def visit_note(self, node):
        self.output.append(f"\n> **Note:** \n> {node.astext()}")

    def depart_note(self, node):
        self.output.append("\n\n")

    def visit_warning(self, node):
        self.output.append(f"\n> **Warning:** \n> {node.astext()}")

    def depart_warning(self, node):
        self.output.append("\n\n")

    def visit_attention(self, node):
        self.output.append(f"\n> **Attention:** \n> {node.astext()}")

    def depart_attention(self, node):
        self.output.append("\n\n")

    def visit_caution(self, node):
        self.output.append("\n> **Caution:** ")

    def depart_caution(self, node):
        self.output.append("\n\n")

    def visit_danger(self, node):
        self.output.append("\n> **Danger:** ")

    def depart_danger(self, node):
        self.output.append("\n\n")

    def visit_tip(self, node):
        self.output.append("\n> **Tip:** ")

    def depart_tip(self, node):
        self.output.append("\n\n")

    def visit_important(self, node):
        self.output.append("\n> **Important:** ")

    def depart_important(self, node):
        self.output.append("\n\n")

    def visit_footnote_reference(self, node):
        """Handle footnote references in the text."""
        # Extract the reference ID
        refid = node.astext()

        # Check if the last character in output is a space and remove it
        if self.output and self.output[-1].endswith(" "):
            self.output[-1] = self.output[-1].rstrip()

        # Add the footnote reference in GFM format
        self.output.append(f"[^{refid}]")

        # Skip processing children since we've already used the text
        raise SkipNode()

    def visit_footnote(self, node):
        """Handle the footnote definition."""
        # Extract the footnote ID
        footnote_id = node.get("names", [""])[0]
        if not footnote_id:
            # Try to get it from the first child if it's a label
            for child in node.children:
                if child.tagname == "label":
                    footnote_id = child.astext()
                    break

        # Start the footnote definition
        self.output.append(f"\n[^{footnote_id}]: ")

        # We'll handle the content in the children, but skip the label
        self.in_footnote = True
        self.footnote_label_seen = False

    def depart_footnote(self, node):
        self.in_footnote = False
        self.output.append("\n\n")

    def visit_label(self, node):
        """Handle footnote labels."""
        if hasattr(self, "in_footnote") and self.in_footnote:
            # Skip the label in footnote definitions
            self.footnote_label_seen = True
            raise SkipNode()
        else:
            # For other labels, just output the text
            pass

    def visit_math(self, node):
        """Handles inline math expressions."""
        # Store the math content
        self.math_content = node.astext()
        # Mark the start position to replace content later
        self.math_start = len(self.output)
        # Add the opening delimiter
        self.output.append("$")

    def depart_math(self, node):
        # Remove any duplicate content added by children
        if hasattr(self, "math_start"):
            # Keep only up to the $ delimiter
            self.output = self.output[: self.math_start + 1]
            # Add the math content
            self.output.append(self.math_content)
            # Remove the attribute
            delattr(self, "math_start")

        # Add the closing delimiter
        self.output.append("$")

    def visit_math_block(self, node):
        """Handles block/display math expressions."""
        # GitHub uses $$ for block math
        self.output.append("\n$$\n")
        self.output.append(node.astext())

    def depart_math_block(self, node):
        self.output.append("\n$$\n")

    def visit_displaymath(self, node):
        """Handles Sphinx displaymath node."""
        self.output.append("\n$$\n")
        if node.get("nowrap", False):
            # No wrapping - output as is
            self.output.append(node["latex"])
        else:
            # May need to handle alignment
            latex = node["latex"]
            if "\\begin{align" in latex or "\\begin{equation" in latex:
                # Already has environment, output as is
                self.output.append(latex)
            else:
                # Wrap in equation environment
                self.output.append(latex)

    def depart_displaymath(self, node):
        self.output.append("\n$$\n")

    def visit_target(self, node):
        if "refid" in node:
            # This is an anchor target
            anchor = self._make_anchor(node["refid"])
            self.output.append(f'<a id="{anchor}"></a>')
        elif "refuri" in node:
            # This is a reference definition
            if "names" in node and node["names"]:
                self.refs_map[node["names"][0]] = node["refuri"]

    def visit_interpreted(self, node):
        """Handle interpreted text roles."""
        role_name = node.get("role")
        if role_name == "ref":
            # Extract the target from the node text
            target = node.astext()
            # Create a Markdown link to the target
            self.output.append(f"[{target}](#{target})")
            # Skip processing children
            raise SkipNode

    def visit_substitution_definition(self, node):
        raise SkipNode

    def visit_comment(self, node):
        raise SkipNode

    def visit_system_message(self, node):
        raise SkipNode

    def unknown_visit(self, node):
        # node_type = node.__class__.__name__
        # self.output.append(f"<!-- Unsupported RST element: {node_type} -->")
        pass

    def unknown_departure(self, node):
        pass


class MarkdownWriter(Writer):
    """Writer for converting reStructuredText to GitHub Flavored Markdown."""

    def __init__(self):
        super().__init__()
        self.translator_class = MarkdownTranslator

    def translate(self):
        visitor = self.translator_class(self.document)
        self.document.walkabout(visitor)
        self.output = visitor.astext()


def convert_rst_to_md(rst_content: str) -> str:
    """Convert reStructuredText to GitHub Flavored Markdown."""
    parts = publish_parts(
        source=rst_content,
        writer=MarkdownWriter(),
        settings_overrides={"report_level": 5, "syntax_highlight": "short"},
    )
    return parts["whole"]


def main():
    """Run the CLI"""
    parser = argparse.ArgumentParser(
        description="Convert reStructuredText to GitHub Flavored Markdown"
    )
    parser.add_argument("input", nargs="?", help="Input RST file (default: stdin)")
    parser.add_argument("-o", "--output", help="Output Markdown file (default: stdout)")
    args = parser.parse_args()

    # Read input
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            rst_content = f.read()
    else:
        rst_content = sys.stdin.read()

    # Convert content
    md_content = convert_rst_to_md(rst_content)

    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md_content)
    else:
        print(md_content)


if __name__ == "__main__":
    main()
