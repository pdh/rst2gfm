import argparse
import sys
from docutils.core import publish_parts
from docutils.writers import Writer
from docutils.nodes import NodeVisitor
import re


class SkipNode(Exception):
    """Exception to skip processing of a node's children."""

    pass


class MarkdownTranslator(NodeVisitor):
    """Translates reStructuredText nodes to GitHub Flavored Markdown."""

    def __init__(self, document):
        super().__init__(document)
        self.output = []
        self.list_depth = 0
        self.section_level = 0
        self.in_code_block = False
        self.code_language = "python"
        self.in_table = False
        self.table_data = []
        self.table_has_header = True
        self.current_row = []
        self.entry_text = []
        self.list_type = []
        self.reference_stack = []
        self.pending_refs = []
        self.refs_map = {}

    def _make_anchor(self, ref_id):
        """Convert RST reference ID to GitHub-compatible anchor."""
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

    def visit_document(self, node):
        pass

    def depart_document(self, node):
        # Add any pending reference definitions at the end
        if self.pending_refs:
            self.output.append("\n\n")
            for ref_id, refname in self.pending_refs:
                if refname in self.refs_map:
                    self.output.append(f"[{ref_id}]: {self.refs_map[refname]}\n")

    def visit_section(self, node):
        self.section_level += 1

    def depart_section(self, node):
        self.section_level -= 1

    def visit_subtitle(self, node):
        self.output.append("## ")
        self.section_level += 1

    def depart_subtitle(self, node):
        self.output.append("\n\n")
        # TODO not sure if this section leveling is quite right
        # self.section_level -= 1

    def visit_title(self, node):
        if self.in_table:
            # This is a table caption/title
            self.table_caption = node.astext()
        else:
            # Regular section title
            self.output.append(f"{'#' * (self.section_level + 1)} ")

    def depart_title(self, node):
        self.output.append("\n\n")

    def visit_paragraph(self, node):
        pass

    def depart_paragraph(self, node):
        self.output.append("\n\n")

    def visit_Text(self, node):
        text = node.astext()
        if self.in_table and self.entry_text is not None:
            self.entry_text.append(text)
        else:
            self.output.append(text)

    def depart_Text(self, node):
        pass

    def visit_emphasis(self, node):
        self.output.append("*")

    def depart_emphasis(self, node):
        self.output.append("*")

    def visit_strong(self, node):
        self.output.append("**")

    def depart_strong(self, node):
        self.output.append("**")

    def visit_literal(self, node):
        self.output.append("`")

    def depart_literal(self, node):
        self.output.append("`")

    def visit_bullet_list(self, node):
        self.list_depth += 1
        self.list_type.append("bullet")
        # Add blank line before sublist if we're already in a list
        if self.list_depth > 1:
            self.output.append("\n")

    def depart_bullet_list(self, node):
        self.list_depth -= 1
        self.list_type.pop()
        self.output.append("\n")

    def visit_list_item(self, node):
        # Calculate proper indentation based on list_depth
        # For Markdown, typically 2-4 spaces per level is recommended
        if self.list_type[-1] == "bullet":
            indent = "  " * (self.list_depth - 1)
            self.output.append(f"\n{indent}- ")
        else:  # enumerated
            indent = "   " * (self.list_depth - 1)
            self.output.append(f"\n{indent}1. ")  # Always start with 1 in Markdown

    def depart_list_item(self, node):
        pass

    def visit_reference(self, node):
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
        self.in_code_block = True
        language = ""

        # Check for language in various attributes
        if "language" in node:
            language = node["language"]
        elif "classes" in node and len(node["classes"]) > 0:
            # RST often puts language in classes
            potential_lang = node["classes"]
            if potential_lang != "code":  # Skip generic "code" class
                language = potential_lang

        # Handle highlighting options if present
        highlight_args = node.get("highlight_args", {})
        line_nums = "linenos" in highlight_args

        # Add language specifier to code block
        self.output.append(f"\n```{language}")

    def depart_literal_block(self, node):
        self.in_code_block = False
        self.output.append("\n```\n\n")

    def visit_table(self, node):
        self.table_data = []
        self.in_table = True
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
        if not self.table_data or len(self.table_data) == 0:
            return

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
        for row in data_rows:
            # Ensure row has enough columns
            while len(row) < col_count:
                row.append("")
            table_md.append("| " + " | ".join(row) + " |")
        if hasattr(self, "table_caption"):
            table_md.append(f"\n*Table: {self.table_caption}*\n")
            delattr(self, "table_caption")

        self.output.append("\n" + "\n".join(table_md) + "\n\n")
        self.in_table = False

    def visit_row(self, node):
        self.current_row = []

    def depart_row(self, node):
        self.table_data.append(self.current_row)

    def visit_entry(self, node):
        self.entry_text = []

        # Track cell spans if present
        self.current_cell_colspan = node.get("morecols", 0) + 1
        self.current_cell_rowspan = node.get("morerows", 0) + 1

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

    def visit_image(self, node):
        uri = node.get("uri", "")
        alt = node.get("alt", "")
        self.output.append(f"![{alt}]({uri})")

    def depart_image(self, node):
        pass

    def visit_block_quote(self, node):
        self.output.append("\n> ")

    def depart_block_quote(self, node):
        self.output.append("\n\n")

    def visit_enumerated_list(self, node):
        self.list_counter = 1
        self.list_type.append("enumerated")

    def depart_enumerated_list(self, node):
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

    def visit_target(self, node):
        if "refid" in node:
            # This is an anchor target
            anchor = self._make_anchor(node["refid"])
            self.output.append(f'<a id="{anchor}"></a>')
        elif "refuri" in node:
            # This is a reference definition
            if "names" in node and node["names"]:
                ref_id = self._normalize_refname(node["names"][0])
                self.refs_map[node["names"][0]] = node["refuri"]

    def depart_target(self, node):
        pass

    def visit_substitution_definition(self, node):
        raise SkipNode

    def visit_comment(self, node):
        raise SkipNode

    def visit_system_message(self, node):
        raise SkipNode

    def unknown_visit(self, node):
        node_type = node.__class__.__name__
        # self.output.append(f"<!-- Unsupported RST element: {node_type} -->")

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


def convert_rst_to_md(rst_content):
    """Convert reStructuredText to GitHub Flavored Markdown."""
    parts = publish_parts(
        source=rst_content,
        writer=MarkdownWriter(),
        settings_overrides={"report_level": 5},
    )
    return parts["whole"]


def main():
    parser = argparse.ArgumentParser(
        description="Convert reStructuredText to GitHub Flavored Markdown"
    )
    parser.add_argument("input", nargs="?", help="Input RST file (default: stdin)")
    parser.add_argument("-o", "--output", help="Output Markdown file (default: stdout)")
    args = parser.parse_args()

    # Read input
    if args.input:
        with open(args.input, "r") as f:
            rst_content = f.read()
    else:
        rst_content = sys.stdin.read()

    # Convert content
    md_content = convert_rst_to_md(rst_content)

    # Write output
    if args.output:
        with open(args.output, "w") as f:
            f.write(md_content)
    else:
        print(md_content)


if __name__ == "__main__":
    main()
