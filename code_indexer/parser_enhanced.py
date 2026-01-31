# code_indexer/parser_enhanced.py
"""
Enhanced AST-based parser with advanced chunking strategies for microservices.

Improvements over basic parser:
1. Recursive AST splitting for long methods (>100 lines)
2. Enhanced metadata (class, package, signature, complexity)
3. Service topology detection from package structure
4. Call chain awareness (method invocations)
5. Logical block preservation (try-catch, if-else blocks)
"""

from tree_sitter_languages import get_parser
from typing import List, Dict, Tuple
import re
import os

# Import cAST compressor
try:
    from c_ast_compressor import CCompressor
    CAST_AVAILABLE = True
except ImportError:
    CAST_AVAILABLE = False
    print("Warning: cAST compressor not available")

# Get a pre-configured parser for the Java language
parser = get_parser('java')

# Configuration
MAX_METHOD_LINES = 100  # Split methods longer than this
MIN_BLOCK_LINES = 10    # Minimum lines for a code block chunk
MAX_BLOCK_LINES = 50    # Maximum lines for a code block chunk

# cAST Configuration
USE_CAST = os.getenv('USE_CAST', 'false').lower() == 'true'
CAST_SIMILARITY_THRESHOLD = float(os.getenv('CAST_SIMILARITY_THRESHOLD', '0.7'))
CAST_MAX_COMPRESSION_RATIO = float(os.getenv('CAST_MAX_COMPRESSION_RATIO', '0.6'))


def extract_package_and_class(file_path: str, source_code: str) -> tuple:
    """Extract package name and class name from Java source code."""
    package_name = ""
    class_name = ""

    # Extract package
    package_match = re.search(r'package\s+([\w.]+);', source_code)
    if package_match:
        package_name = package_match.group(1)

    # Extract class name from file path
    class_match = re.search(r'class\s+(\w+)', source_code)
    if class_match:
        class_name = class_match.group(1)

    return package_name, class_name


def detect_microservice_from_package(package_name: str, file_path: str) -> str:
    """
    Detect microservice name from package structure or file path.

    Common patterns:
    - com.company.{service}.*
    - {service}/src/main/java/...
    """
    if not package_name:
        # Try extracting from file path
        parts = file_path.split('/')
        for i, part in enumerate(parts):
            if part in ['src', 'main', 'java']:
                if i > 0:
                    return parts[i - 1]
        return "unknown-service"

    # Extract from package (e.g., com.train.ticket.booking -> booking)
    parts = package_name.split('.')
    for i, part in enumerate(parts):
        if part in ['service', 'services', 'microservice', 'api', 'rest']:
            if i + 1 < len(parts):
                return parts[i + 1]

    # Return second-level package if available
    if len(parts) >= 3:
        return parts[2]

    return "unknown-service"


def extract_method_signature(method_node) -> str:
    """Extract the full method signature including parameters."""
    # Get method name
    name_node = method_node.child_by_field_name('name')
    if not name_node:
        return "unknown"

    method_name = name_node.text.decode('utf8')

    # Get parameters
    params_node = method_node.child_by_field_name('parameters')
    if params_node:
        params = params_node.text.decode('utf8')
    else:
        params = "()"

    return f"{method_name}{params}"


def extract_called_methods(method_node) -> List[str]:
    """Extract method calls within a method for call chain analysis."""
    called_methods = []

    def traverse(node):
        if node.type == 'method_invocation':
            # Extract the method being called
            name_node = node.child_by_field_name('name')
            if name_node:
                called_methods.append(name_node.text.decode('utf8'))

        for child in node.children:
            traverse(child)

    traverse(method_node)
    return list(set(called_methods))  # Remove duplicates


def calculate_complexity(method_node) -> Dict:
    """Calculate basic complexity metrics for a method."""
    metrics = {
        'lines': method_node.end_point[0] - method_node.start_point[0] + 1,
        'cyclomatic_complexity': 1,  # Base complexity
        'has_try_catch': False,
        'has_loops': False,
        'has_conditionals': False
    }

    def traverse(node):
        if node.type == 'if_statement':
            metrics['cyclomatic_complexity'] += 1
            metrics['has_conditionals'] = True
        elif node.type in ['for_statement', 'while_statement', 'enhanced_for_statement']:
            metrics['cyclomatic_complexity'] += 1
            metrics['has_loops'] = True
        elif node.type == 'try_statement':
            metrics['cyclomatic_complexity'] += 1
            metrics['has_try_catch'] = True
        elif node.type == 'catch_clause':
            metrics['cyclomatic_complexity'] += 1

        for child in node.children:
            traverse(child)

    traverse(method_node)
    return metrics


def should_split_method(method_node, complexity_metrics: dict) -> bool:
    """Determine if a method should be split into smaller chunks."""
    # Split if too long
    if complexity_metrics['lines'] > MAX_METHOD_LINES:
        return True

    # Split if very complex
    if complexity_metrics['cyclomatic_complexity'] > 10:
        return True

    return False


def split_method_into_blocks(method_node, method_name: str, file_path: str) -> List[Dict]:
    """
    Split a large method into logical code blocks.

    Strategy:
    1. Extract try-catch blocks as separate chunks
    2. Extract if-else blocks for complex conditionals
    3. Extract loop bodies
    4. Fall back to line-based splitting if needed
    """
    chunks = []
    method_code = method_node.text.decode('utf8')
    start_line = method_node.start_point[0] + 1
    end_line = method_node.end_point[0] + 1

    # If method is moderately long, try semantic splitting
    if end_line - start_line > MAX_METHOD_LINES:
        # Try to split by logical blocks
        blocks = extract_logical_blocks(method_node)
        if len(blocks) > 1:
            for i, block in enumerate(blocks):
                block_start = block['node'].start_point[0] + 1
                block_end = block['node'].end_point[0] + 1
                block_lines = block_end - block_start + 1

                # Only create chunk if block is significant
                if MIN_BLOCK_LINES <= block_lines <= MAX_BLOCK_LINES:
                    chunk_id = f"{file_path}::{method_name}::block_{i+1}::{block_start}-{block_end}"
                    chunks.append({
                        "id": chunk_id,
                        "code": block['node'].text.decode('utf8'),
                        "metadata": {
                            "file_path": file_path,
                            "method_name": method_name,
                            "block_type": block['type'],
                            "block_number": i + 1,
                            "start_line": block_start,
                            "end_line": block_end,
                            "is_split_chunk": True
                        }
                    })

    # If no good blocks found or splitting didn't work, return empty
    # The caller will handle this by keeping the original method
    return chunks


def extract_logical_blocks(method_node) -> List[Dict]:
    """Extract logical code blocks from a method."""
    blocks = []

    # Look for try-catch blocks
    for child in method_node.children:
        if child.type == 'try_statement':
            blocks.append({'node': child, 'type': 'try_catch'})

    # Look for if statements with large bodies
    for child in method_node.children:
        if child.type == 'if_statement':
            # Check if the if statement is substantial
            lines = child.end_point[0] - child.start_point[0] + 1
            if lines >= MIN_BLOCK_LINES:
                blocks.append({'node': child, 'type': 'conditional'})

    # Look for loops
    for child in method_node.children:
        if child.type in ['for_statement', 'while_statement', 'enhanced_for_statement']:
            lines = child.end_point[0] - child.start_point[0] + 1
            if lines >= MIN_BLOCK_LINES:
                blocks.append({'node': child, 'type': 'loop'})

    return blocks


def apply_cast_compression(chunks: List[Dict]) -> List[Dict]:
    """
    Apply cAST compression to code chunks if enabled.

    Args:
        chunks: List of code chunks with 'code' field

    Returns:
        Same chunks with added 'compressed_code' and compression metadata
    """
    if not USE_CAST or not CAST_AVAILABLE:
        # cAST not enabled, return chunks unchanged
        for chunk in chunks:
            chunk['compressed_code'] = chunk['code']
            chunk['metadata']['uses_cast'] = False
        return chunks

    # Create compressor
    compressor = CCompressor(
        similarity_threshold=CAST_SIMILARITY_THRESHOLD,
        max_compression_ratio=CAST_MAX_COMPRESSION_RATIO
    )

    # Apply compression to each chunk
    for chunk in chunks:
        code = chunk['code']
        result = compressor.compress(code)

        # Add compressed code
        chunk['compressed_code'] = result['compressed_code']
        chunk['metadata']['uses_cast'] = True
        chunk['metadata']['cast_compression_ratio'] = result['compression_ratio']
        chunk['metadata']['cast_char_compression_ratio'] = result['stats'].get('char_compression_ratio', 1.0)
        chunk['metadata']['cast_merged_nodes'] = result['stats'].get('merged_nodes', 0)
        chunk['metadata']['cast_preserved_nodes'] = result['stats'].get('preserved_nodes', 0)

    return chunks


def extract_method_chunks_enhanced(file_path: str) -> List[Dict]:
    """
    Enhanced parser that extracts method-level chunks with rich metadata.

    Returns:
        List of chunks with enhanced metadata including:
        - Package and class information
        - Method signature
        - Complexity metrics
        - Called methods (for call chain analysis)
        - Microservice detection
    """
    try:
        with open(file_path, 'rb') as f:
            source_code_bytes = f.read()
            source_code = source_code_bytes.decode('utf8')

        tree = parser.parse(source_code_bytes)
        chunks = []

        # Extract package and class info
        package_name, class_name = extract_package_and_class(file_path, source_code)
        microservice = detect_microservice_from_package(package_name, file_path)

        # Parse methods
        for node in tree.root_node.children:
            if node.type == 'class_declaration':
                for class_body_node in node.children:
                    if class_body_node.type == 'class_body':
                        for method_node in class_body_node.children:
                            if method_node.type == 'method_declaration':
                                method_name_node = method_node.child_by_field_name('name')
                                if method_name_node:
                                    method_name = method_name_node.text.decode('utf8')
                                    start_line = method_node.start_point[0] + 1
                                    end_line = method_node.end_point[0] + 1
                                    code_snippet = method_node.text.decode('utf8')

                                    # Extract enhanced information
                                    signature = extract_method_signature(method_node)
                                    called_methods = extract_called_methods(method_node)
                                    complexity = calculate_complexity(method_node)

                                    # Create chunk ID
                                    chunk_id = f"{file_path}::{method_name}::{start_line}-{end_line}"

                                    # Build enhanced metadata
                                    metadata = {
                                        "file_path": file_path,
                                        "method_name": method_name,
                                        "signature": signature,
                                        "start_line": start_line,
                                        "end_line": end_line,
                                        "lines_of_code": complexity['lines'],
                                        "cyclomatic_complexity": complexity['cyclomatic_complexity'],
                                        "package": package_name,
                                        "class": class_name,
                                        "microservice": microservice,
                                        "called_methods": called_methods,
                                        "has_try_catch": complexity['has_try_catch'],
                                        "has_loops": complexity['has_loops'],
                                        "has_conditionals": complexity['has_conditionals']
                                    }

                                    # Check if method should be split
                                    if should_split_method(method_node, complexity):
                                        # Try to split into logical blocks
                                        block_chunks = split_method_into_blocks(
                                            method_node, method_name, file_path
                                        )

                                        if block_chunks:
                                            # Add block chunks with inherited metadata
                                            for block in block_chunks:
                                                block['metadata'].update({
                                                    "signature": signature,
                                                    "package": package_name,
                                                    "class": class_name,
                                                    "microservice": microservice,
                                                    "parent_method": method_name
                                                })
                                                chunks.append(block)
                                        else:
                                            # Couldn't split effectively, keep original
                                            chunks.append({
                                                "id": chunk_id,
                                                "code": code_snippet,
                                                "metadata": metadata
                                            })
                                    else:
                                        # Method is reasonable size, keep as-is
                                        chunks.append({
                                            "id": chunk_id,
                                            "code": code_snippet,
                                            "metadata": metadata
                                        })

        # Apply cAST compression if enabled
        chunks = apply_cast_compression(chunks)

        return chunks

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_statistics(chunks: List[Dict]) -> Dict:
    """Generate statistics about the indexed code."""
    if not chunks:
        return {"total_chunks": 0}

    stats = {
        "total_chunks": len(chunks),
        "total_methods": sum(1 for c in chunks if not c['metadata'].get('is_split_chunk', False)),
        "split_chunks": sum(1 for c in chunks if c['metadata'].get('is_split_chunk', False)),
        "microservices": len(set(c['metadata'].get('microservice', 'unknown') for c in chunks)),
        "avg_complexity": sum(c['metadata'].get('cyclomatic_complexity', 1) for c in chunks) / len(chunks),
        "large_methods": sum(1 for c in chunks if c['metadata'].get('lines_of_code', 0) > MAX_METHOD_LINES),
        "complex_methods": sum(1 for c in chunks if c['metadata'].get('cyclomatic_complexity', 1) > 10)
    }

    return stats


# Backward compatibility: keep the original function name
def extract_method_chunks(file_path: str) -> List[Dict]:
    """Parses a Java file and extracts all method declarations as chunks.

    This is the original function - use extract_method_chunks_enhanced for new features.
    """
    return extract_method_chunks_enhanced(file_path)
