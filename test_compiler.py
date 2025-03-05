from py_to_asm_compiler import Lexer, Parser
from x86_code_generator import X86CodeGenerator

def compile_python_to_asm(source_code: str) -> str:
    # Initialize components
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    
    parser = Parser(tokens)
    ast = parser.parse()
    
    code_generator = X86CodeGenerator()
    assembly = code_generator.generate(ast)
    
    return assembly

# Test program with various features
test_program = """
# Variable assignment and arithmetic
x = 42
y = 10
z = x + y * 2

# If statement with comparison
if z > 50:
    result = 1    # Using 4 spaces for indentation
"""

# Compile and print the assembly output
assembly_code = compile_python_to_asm(test_program)
print("Generated x86 Assembly:")
print(assembly_code)