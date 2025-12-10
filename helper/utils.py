import pandas as pd
import pandasql as ps

# Load dataset function from file uploader or file path
def load_dataset(uploaded_file):
    """Load dataset from uploaded file or file path."""
    try:
        # Check if it's a file path (string) or file object
        if isinstance(uploaded_file, str):
            # It's a file path
            file_path = uploaded_file
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.json'):
                df = pd.read_json(file_path)
            else:
                raise ValueError("Unsupported file type.")
        else:
            # It's a file object (from Streamlit)
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith('.json'):
                df = pd.read_json(uploaded_file)
            else:
                raise ValueError("Unsupported file type.")
        return df
    except Exception as e:
        raise ValueError(f"Error loading dataset: {e}")
    
# Extract the column names from the dataframe
def get_column_names(df):
    """Get column names from dataframe."""
    return df.columns.tolist()

# Generate a summary of the dataframe
def summarize_dataframe(df):
    """Generate a summary of the dataframe."""
    return df.describe(include='all').to_dict()

# Sample row data for preview
def get_sample_rows(df, n=3):
    """Get sample rows from dataframe."""
    return df.sample(n).to_dict(orient='records')

# Merge it as an information dictionary
def generate_dataframe_info(df):
    """Generate a comprehensive info dictionary about the dataframe."""
    info = {
        "columns": get_column_names(df),
        "summary": summarize_dataframe(df),
        "sample_rows": get_sample_rows(df)
    }
    return info

# Build information dictionary for multiple dataframes
def build_dataframes_info(dfs, table_names=None):
    """Build information dictionary for multiple dataframes."""
    info_dict = {}
    for idx, df in enumerate(dfs):
        table_name = table_names[idx] if table_names else f"dataset_{idx+1}"
        info_dict[table_name] = generate_dataframe_info(df)
    return info_dict

# Create a sql running function
def run_sql_query(dfs, query, table_names=None):
    """Run SQL query on the dataframe."""
    try:
        tables = {}
        for idx, df in enumerate(dfs):
            df_name = table_names[idx] if table_names else f"dataset_{idx+1}"
            tables[df_name] = df
        
        result = ps.sqldf(query, tables)
        return result
    except Exception as e:
        raise ValueError(f"Error running SQL query: {e}")


# ============= INTERVIEW UTILITIES =============

def get_output_instructions_by_language():
    """Get language-specific output instructions for coding exercises."""
    return {
        'python': 'Use print() for all outputs',
        'javascript': 'Use console.log() for outputs',
        'java': 'Use System.out.println() for outputs',
        'cpp': 'Use cout << result << endl; for outputs',
        'c': 'Use printf() with appropriate format specifiers',
        'csharp': 'Use Console.WriteLine() for outputs',
        'typescript': 'Use console.log() for outputs',
        'go': 'Use fmt.Println() for arrays/slices',
        'rust': 'Use println! macro with debug formatting',
        'php': 'Use echo json_encode($array) for arrays',
        'ruby': 'Use puts array.inspect for arrays',
        'kotlin': 'Use println(array.contentToString()) for arrays',
        'swift': 'Use print(array) for arrays'
    }


def get_example_code_by_language():
    """Get example test case code snippets by language."""
    return {
        'python': 'print(function_name(test_input))',
        'javascript': 'console.log(functionName(testInput));',
        'java': 'System.out.println(functionName(testInput));',
        'cpp': 'cout << functionName(testInput) << endl;',
        'c': 'printf("%d", functionName(testInput));',
        'csharp': 'Console.WriteLine(FunctionName(testInput));',
        'typescript': 'console.log(functionName(testInput));',
        'go': 'fmt.Println(functionName(testInput))',
        'rust': 'println!("{:?}", function_name(test_input));',
        'php': 'echo functionName($testInput);',
        'ruby': 'puts function_name(test_input)',
        'kotlin': 'println(functionName(testInput))',
        'swift': 'print(functionName(testInput))'
    }


def clean_json_response(response):
    """Clean LLM response to extract valid JSON."""
    import re
    
    # Remove markdown code blocks if present
    cleaned = response.strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```(?:json)?\n', '', cleaned)
        cleaned = re.sub(r'\n```$', '', cleaned)
    
    # Try to extract JSON from response
    json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if json_match:
        return json_match.group()
    
    return cleaned


def generate_variation_seed():
    """Generate a variation seed to ensure different questions on retry."""
    import time
    return int(time.time() * 1000) % 1000