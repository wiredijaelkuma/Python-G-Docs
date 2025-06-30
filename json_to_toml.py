"""
Simple utility to convert credentials.json to TOML format for Streamlit Cloud
"""
import json
import sys

def json_to_toml(json_file):
    """Convert JSON credentials to TOML format for Streamlit Cloud"""
    try:
        # Read JSON file
        with open(json_file, 'r') as f:
            creds = json.load(f)
        
        # Create TOML output
        toml = ["[gcp_service_account]"]
        for key, value in creds.items():
            if isinstance(value, str):
                # Escape backslashes and quotes in strings
                value = value.replace('\\', '\\\\').replace('"', '\\"')
                toml.append(f'{key} = "{value}"')
            else:
                toml.append(f'{key} = {value}')
        
        return "\n".join(toml)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = "credentials.json"
    
    toml_content = json_to_toml(json_file)
    print("\n=== TOML Format for Streamlit Cloud Secrets ===\n")
    print(toml_content)
    print("\n=== Copy the above content to your Streamlit Cloud secrets ===")