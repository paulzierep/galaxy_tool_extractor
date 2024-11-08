import argparse
import os
from typing import List

import pandas as pd
from ruamel.yaml import YAML as yaml
from ruamel.yaml.scalarstring import LiteralScalarString


def add_tools_url(tools) -> None:
    return tools


def main() -> None:
    parser = argparse.ArgumentParser(description="Create community tools.yml from tool.tsv.")

    # Adding positional arguments with short options
    parser.add_argument(
        "-c", "--tool_tsv", type=str, required=True, help="Path to the TSV file (e.g., curated_tools.tsv)"
    )
    parser.add_argument(
        "-y", "--tool_yml", type=str, required=True, help="Path to the output YAML file (e.g., tools.yml)"
    )

    args = parser.parse_args()

    # Check if the tool TSV file exists
    if not os.path.exists(args.tool_tsv):
        print(f"Error: The file '{args.tool_tsv}' does not exist.")
        return

    try:
        # Read the TSV file with pandas (use tab delimiter)
        data = pd.read_csv(args.tool_tsv, sep="\t")

        # Construct the YAML data structure
        yaml_data = {
            "id": "tools",
            "title": "Community Tools",
            "tabs": [
                {"id": "tool_list", "title": "List of community curated tools available for microGalaxy", "content": []}
            ],
        }

        # Populate the content section with each row from the TSV
        for _, row in data.iterrows():
            # Use the first column (assumed to be the tool title) as the title_md
            title_md = row[data.columns[0]]  # Get the first column's value as title_md

            # Prepare the description with an HTML unordered list and links for each Galaxy tool ID
            description = f"{row['Description']}"
            tool_ids = row["Galaxy tool ids"]
            owner = row["Galaxy wrapper owner"]
            wrapper_id = row["Galaxy wrapper id"]

            # Split the tool IDs by comma if it's a valid string, otherwise handle as an empty list
            tool_ids_list = tool_ids.split(",") if isinstance(tool_ids, str) else []

            # Create the base URL template for each tool link
            url_template = (
                "{{ galaxy_base_url }}/tool_runner?tool_id=toolshed.g2.bx.psu.edu%Frepos%{owner}%{wrapper_id}%{tool_id}"
            )

            # Build HTML list items with links
            description += "\n<ul>\n"
            for tool_id in tool_ids_list:
                tool_id = tool_id.strip()  # Trim whitespace
                # Format the URL with owner, wrapper ID, and tool ID
                url = url_template.format(owner=owner, wrapper_id=wrapper_id, tool_id=tool_id)
                description += f'  <li><a href="{url}">{tool_id}</a></li>\n'
            description += "</ul>"

            # Use LiteralScalarString to enforce literal block style for the description
            description_md = LiteralScalarString(description.strip())

            # Create the tool entry
            tool_entry = {
                "title_md": title_md,
                "description_md": description_md,
            }
            yaml_data["tabs"][0]["content"].append(tool_entry)

        # Write the YAML data to the output file
        with open(args.tool_yml, "w") as yaml_file:
            yaml().dump(yaml_data, yaml_file)
        print(f"Data successfully written to '{args.tool_yml}'")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
