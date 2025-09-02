#!/usr/bin/env python3
"""
Generate a UML-like class diagram from the actual codebase.
This ensures documentation is always accurate and up-to-date.
"""

import os
import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class ClassExtractor(ast.NodeVisitor):
    """Extract class and method information from Python AST."""
    
    def __init__(self):
        self.classes = {}
        self.imports = set()
        self.current_class = None
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
    
    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")
    
    def visit_ClassDef(self, node):
        self.current_class = node.name
        bases = [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
        
        self.classes[node.name] = {
            'bases': bases,
            'methods': [],
            'docstring': ast.get_docstring(node) or '',
            'is_abstract': any(decorator.id == 'abstractmethod' if isinstance(decorator, ast.Name) 
                             else False for decorator in getattr(node, 'decorator_list', []))
        }
        
        self.generic_visit(node)
        self.current_class = None
    
    def visit_FunctionDef(self, node):
        if self.current_class:
            is_abstract = any(
                (isinstance(decorator, ast.Name) and decorator.id == 'abstractmethod') or
                (isinstance(decorator, ast.Attribute) and decorator.attr == 'abstractmethod')
                for decorator in node.decorator_list
            )
            
            # Get method signature
            args = []
            for arg in node.args.args:
                if arg.arg != 'self':
                    args.append(arg.arg)
            
            signature = f"{node.name}({', '.join(args)})"
            
            self.classes[self.current_class]['methods'].append({
                'name': node.name,
                'signature': signature,
                'is_abstract': is_abstract,
                'docstring': ast.get_docstring(node) or ''
            })


def analyze_file(file_path: Path) -> Tuple[Dict, Set]:
    """Analyze a Python file and extract class information."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        extractor = ClassExtractor()
        extractor.visit(tree)
        
        return extractor.classes, extractor.imports
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return {}, set()


def generate_mermaid_diagram(project_root: Path) -> str:
    """Generate a Mermaid class diagram from the codebase."""
    
    # Define directories to scan
    backend_dirs = [
        project_root / "backend" / "app" / "services",
        project_root / "backend" / "app" / "models", 
        project_root / "backend" / "app" / "api",
        project_root / "backend" / "app" / "core"
    ]
    
    all_classes = {}
    all_imports = set()
    
    # Scan all Python files
    for directory in backend_dirs:
        if directory.exists():
            for py_file in directory.rglob("*.py"):
                if py_file.name != "__init__.py":
                    classes, imports = analyze_file(py_file)
                    for class_name, class_info in classes.items():
                        # Add file path for context
                        class_info['file'] = str(py_file.relative_to(project_root))
                        all_classes[class_name] = class_info
                    all_imports.update(imports)
    
    # Generate Mermaid diagram
    mermaid = ["classDiagram"]
    
    # Add class definitions
    for class_name, class_info in all_classes.items():
        file_path = class_info['file']
        
        # Class declaration with file annotation
        if class_info['is_abstract']:
            mermaid.append(f"    class {class_name} {{")
            mermaid.append(f"        <<abstract>>")
        else:
            mermaid.append(f"    class {class_name} {{")
        
        # Add key methods (limit to avoid clutter)
        key_methods = class_info['methods'][:5]  # Show first 5 methods
        for method in key_methods:
            prefix = "+" if not method['name'].startswith('_') else "-"
            abstract_marker = "*" if method['is_abstract'] else ""
            mermaid.append(f"        {prefix}{method['signature']}{abstract_marker}")
        
        if len(class_info['methods']) > 5:
            mermaid.append(f"        ... ({len(class_info['methods']) - 5} more methods)")
        
        mermaid.append("    }")
        
        # Add file path as note
        mermaid.append(f"    {class_name} : {file_path}")
    
    # Add inheritance relationships
    for class_name, class_info in all_classes.items():
        for base in class_info['bases']:
            if base in all_classes:  # Only show relationships between our classes
                mermaid.append(f"    {base} <|-- {class_name}")
    
    return "\n".join(mermaid)


def main():
    """Generate and display the class diagram."""
    # Find project root
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    
    print("🔍 Scanning codebase for classes...")
    print(f"📁 Project root: {project_root}")
    
    # Generate diagram
    diagram = generate_mermaid_diagram(project_root)
    
    # Save to file
    output_file = project_root / "docs" / "current_class_diagram.md"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write("# Current Class Diagram\n\n")
        f.write("*Auto-generated from codebase - always current*\n\n")
        f.write("```mermaid\n")
        f.write(diagram)
        f.write("\n```\n")
    
    print(f"✅ Class diagram generated: {output_file}")
    print("\n📊 Preview:")
    print("=" * 50)
    print(diagram)
    print("=" * 50)
    
    # Also generate a simple text summary
    print("\n📋 Quick Class Reference:")
    backend_dirs = [
        project_root / "backend" / "app" / "services",
        project_root / "backend" / "app" / "models", 
    ]
    
    for directory in backend_dirs:
        if directory.exists():
            for py_file in directory.rglob("*.py"):
                if py_file.name != "__init__.py":
                    classes, _ = analyze_file(py_file)
                    if classes:
                        rel_path = py_file.relative_to(project_root)
                        print(f"\n📄 {rel_path}:")
                        for class_name, class_info in classes.items():
                            inheritance = f" -> {', '.join(class_info['bases'])}" if class_info['bases'] else ""
                            print(f"  🏗️  {class_name}{inheritance}")


if __name__ == "__main__":
    main()
