import argparse
import sys
from docutils.core import publish_parts
from docutils.writers import Writer
from docutils.nodes import NodeVisitor


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
        self.code_language = ""
        self.in_table = False
        self.table_data = []
        self.current_row = []
        self.entry_text = []

    def astext(self):
        return "".join(self.output)

    def visit_document(self, node):
        pass

    def depart_document(self, node):
        pass

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

    def depart_bullet_list(self, node):
        self.list_depth -= 1
        self.output.append("\n")

    def visit_list_item(self, node):
        self.output.append("\n" + "  " * (self.list_depth - 1) + "- ")

    def depart_list_item(self, node):
        pass

    def visit_reference(self, node):
        self.output.append("[")
        self.reference_text = node.astext()

        # We need to handle the children differently, but not skip them completely
        # Store the current output length to replace the content later
        self.reference_start = len(self.output)

    def depart_reference(self, node):
        # Replace the content with the reference text if needed
        if hasattr(self, "reference_start"):
            # Remove any content added by children
            self.output = self.output[: self.reference_start]
            # Add the reference text
            self.output.append(self.reference_text)
            delattr(self, "reference_start")

        if "refuri" in node:
            self.output.append(f"]({node['refuri']})")
        else:
            self.output.append("]")

    def visit_literal_block(self, node):
        self.in_code_block = True
        language = node.get("language", "")
        self.output.append(f"\n```{language}")

    def depart_literal_block(self, node):
        self.in_code_block = False
        self.output.append("\n```\n\n")

    def visit_table(self, node):
        self.table_data = []
        self.in_table = True
        self.in_table_header = True

    def depart_table(self, node):
        if not self.table_data:
            return

        # Process table data into markdown table
        col_count = max(len(row) for row in self.table_data)

        table_md = []
        # Add header row
        if self.table_data:
            header = self.table_data[0]
            # Ensure header has enough columns
            while len(header) < col_count:
                header.append("")
            table_md.append("| " + " | ".join(header) + " |")
            table_md.append("| " + " | ".join(["---"] * len(header)) + " |")

        # Add data rows
        for row in self.table_data[1:]:
            # Ensure row has enough columns
            while len(row) < col_count:
                row.append("")
            table_md.append("| " + " | ".join(row) + " |")

        self.output.append("\n" + "\n".join(table_md) + "\n\n")
        self.in_table = False

    def visit_row(self, node):
        self.current_row = []

    def depart_row(self, node):
        self.table_data.append(self.current_row)
        if self.in_table_header:
            self.in_table_header = False

    def visit_entry(self, node):
        self.entry_text = []

    def depart_entry(self, node):
        text = "".join(self.entry_text).replace("\n", " ").strip()
        self.current_row.append(text)
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

    def depart_enumerated_list(self, node):
        self.output.append("\n")

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
        pass

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
