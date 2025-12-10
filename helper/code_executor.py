"""
Code execution module supporting multiple programming languages.
Uses Piston API for secure sandboxed execution + local Python fallback.
"""

import subprocess
import tempfile
import os
import logging
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class CodeExecutor:
    """Execute code in multiple programming languages using Piston API or local Python."""
    
    # Piston API endpoint (free public API)
    PISTON_API = "https://emkc.org/api/v2/piston"
    
    # Language mapping to Piston runtime names
    LANGUAGE_MAP = {
        'python': 'python',
        'javascript': 'javascript',
        'java': 'java',
        'cpp': 'cpp',
        'c': 'c',
        'csharp': 'csharp',
        'go': 'go',
        'rust': 'rust',
        'ruby': 'ruby',
        'php': 'php',
        'swift': 'swift',
        'kotlin': 'kotlin',
        'typescript': 'typescript',
    }
    
    # Version preferences for Piston
    VERSION_MAP = {
        'python': '3.10.0',
        'javascript': '18.15.0',
        'java': '15.0.2',
        'cpp': '10.2.0',
        'csharp': '6.12.0',
        'go': '1.16.2',
    }
    
    @staticmethod
    def execute_with_piston(code: str, language: str, stdin: str = "") -> dict:
        """
        Execute code using Piston API (sandboxed cloud execution).
        
        Args:
            code: Source code to execute
            language: Programming language
            stdin: Standard input for the program
            
        Returns:
            dict with keys: success, output, error, returncode
        """
        try:
            # Map language to Piston runtime name
            piston_lang = CodeExecutor.LANGUAGE_MAP.get(language)
            if not piston_lang:
                return {
                    'success': False,
                    'output': '',
                    'error': f'Language {language} not supported by Piston',
                    'returncode': -1
                }
            
            # Get preferred version
            version = CodeExecutor.VERSION_MAP.get(language, '*')
            
            # Get file extension
            ext = CodeExecutor._get_extension(language)
            
            # Clean code - ensure proper line endings and encoding
            clean_code = code.replace('\r\n', '\n').replace('\r', '\n')
            
            # Prepare request payload
            payload = {
                "language": piston_lang,
                "version": version,
                "files": [
                    {
                        "name": f"main.{ext}",
                        "content": clean_code
                    }
                ],
                "stdin": stdin,
                "args": [],
                "compile_timeout": 10000,  # 10 seconds
                "run_timeout": 5000,        # 5 seconds
                "compile_memory_limit": -1,
                "run_memory_limit": -1
            }
            
            # Make API request
            response = requests.post(
                f"{CodeExecutor.PISTON_API}/execute",
                json=payload,
                timeout=15
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'output': '',
                    'error': f'Piston API error: {response.status_code}',
                    'returncode': -1
                }
            
            result = response.json()
            
            # Check for compilation errors
            if result.get('compile') and result['compile'].get('code') != 0:
                return {
                    'success': False,
                    'output': result['compile'].get('stdout', ''),
                    'error': result['compile'].get('stderr', 'Compilation failed'),
                    'returncode': result['compile'].get('code', -1)
                }
            
            # Get runtime results
            run_result = result.get('run', {})
            output = run_result.get('stdout', '').strip()
            error = run_result.get('stderr', '').strip()
            exit_code = run_result.get('code', 0)
            
            # Clean output - remove code echo if present
            # Some Piston runtimes echo the source code in stdout
            if output and clean_code in output:
                # Remove the code portion and keep only the execution output
                output = output.replace(clean_code, '').strip()
            
            # Additional cleaning: if output still contains code-like patterns
            # and actual output looks like it's at the end, extract it
            if output and '\n' in output:
                lines = output.split('\n')
                # Look for lines that appear to be actual output (often at the end)
                # Check if the last non-empty line looks like output (starts with [, {, numbers, etc.)
                for i in range(len(lines) - 1, -1, -1):
                    line = lines[i].strip()
                    if line and (line.startswith('[') or line.startswith('{') or 
                                line.startswith('"') or line[0].isdigit() or
                                line == 'true' or line == 'false' or line == 'null'):
                        # Found potential output, take from here to end
                        output = '\n'.join(lines[i:]).strip()
                        break
            
            return {
                'success': exit_code == 0,
                'output': output,
                'error': error if exit_code != 0 else '',
                'returncode': exit_code
            }
            
        except requests.Timeout:
            return {
                'success': False,
                'output': '',
                'error': 'Execution timed out (15 seconds)',
                'returncode': -1
            }
        except requests.RequestException as e:
            logger.error(f"Piston API request failed: {e}")
            return {
                'success': False,
                'output': '',
                'error': f'API request failed: {str(e)}',
                'returncode': -1
            }
        except Exception as e:
            logger.error(f"Error executing code with Piston: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'returncode': -1
            }
    
    @staticmethod
    def execute_python_local(code: str) -> dict:
        """
        Execute Python code locally using subprocess (faster for Python).
        
        Args:
            code: Python source code
            
        Returns:
            dict with keys: success, output, error, returncode
        """
        temp_file = None
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_file = f.name
            
            # Execute Python code
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=os.path.dirname(temp_file)
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout.strip(),
                'error': result.stderr.strip() if result.returncode != 0 else '',
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': 'Execution timed out (5 seconds)',
                'returncode': -1
            }
        except Exception as e:
            logger.error(f"Error executing Python locally: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'returncode': -1
            }
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    @staticmethod
    def execute(code: str, language: str, use_local_python: bool = True) -> dict:
        """
        Execute code using the best available method.
        - Python: Local execution (faster, no API dependency)
        - Other languages: Piston API (sandboxed, no installation needed)
        
        Args:
            code: Source code to execute
            language: Programming language
            use_local_python: Use local Python instead of Piston for Python code
            
        Returns:
            dict with keys: success, output, error, returncode
        """
        # Use local Python execution for better performance
        if language == 'python' and use_local_python:
            return CodeExecutor.execute_python_local(code)
        
        # Use Piston API for other languages
        return CodeExecutor.execute_with_piston(code, language)
    
    @staticmethod
    def _get_extension(language: str) -> str:
        """Get file extension for a language."""
        extensions = {
            'python': 'py',
            'javascript': 'js',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'csharp': 'cs',
            'go': 'go',
            'rust': 'rs',
            'ruby': 'rb',
            'php': 'php',
            'swift': 'swift',
            'kotlin': 'kt',
            'typescript': 'ts',
        }
        return extensions.get(language, 'txt')
    
    @staticmethod
    def get_supported_languages() -> list:
        """Get list of supported languages."""
        return list(CodeExecutor.LANGUAGE_MAP.keys())
    
    @staticmethod
    def is_piston_available() -> bool:
        """Check if Piston API is accessible."""
        try:
            response = requests.get(f"{CodeExecutor.PISTON_API}/runtimes", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def is_language_available(language: str) -> bool:
        """
        Check if a language is available for execution.
        - Python: Always available (local)
        - Others: Available via Piston API
        """
        if language == 'python':
            # Check if Python is installed locally
            try:
                subprocess.run(['python', '--version'], capture_output=True, timeout=2)
                return True
            except:
                return False
        
        # For other languages, they're available via Piston API (no installation needed)
        return language in CodeExecutor.LANGUAGE_MAP
    
    @staticmethod
    def get_available_runtimes() -> dict:
        """
        Get available runtimes from Piston API.
        
        Returns:
            dict mapping language names to available versions
        """
        try:
            response = requests.get(f"{CodeExecutor.PISTON_API}/runtimes", timeout=5)
            if response.status_code == 200:
                runtimes = response.json()
                available = {}
                for runtime in runtimes:
                    lang = runtime.get('language')
                    version = runtime.get('version')
                    if lang and version:
                        if lang not in available:
                            available[lang] = []
                        available[lang].append(version)
                return available
            return {}
        except Exception as e:
            logger.error(f"Error fetching Piston runtimes: {e}")
            return {}
