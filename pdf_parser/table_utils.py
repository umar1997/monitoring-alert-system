def generate_markdown_table(total_columns, total_rows, cell_data):
    # Create an empty 2D array for the table
    table = [["" for _ in range(total_columns)] for _ in range(total_rows)]

    # Fill the table with provided cell data
    for cell in cell_data:
        row_idx, col_idx, content = cell
        table[row_idx][col_idx] = content

    # Generate the markdown table string
    markdown_table = []
    header_separator = "| " + " | ".join(["---"] * total_columns) + " |"

    for row in table:
        markdown_table.append("| " + " | ".join(row) + " |")
    
    # Insert header separator after the first row (header)
    if markdown_table:
        markdown_table.insert(1, header_separator)

    return "\n".join(markdown_table)

# Example usage:
# total_columns = 3
# total_rows = 3
# cell_data = [
#     (0, 0, "Header1"), (0, 1, "Header2"), (0, 2, "Header3"),
#     (1, 0, "Row1Col1"), (1, 1, "Row1Col2"), (1, 2, "Row1Col3"),
#     (2, 0, "Row2Col1"), (2, 1, "Row2Col2"), (2, 2, "Row2Col3")
# ]

# print(generate_markdown_table(total_columns, total_rows, cell_data))