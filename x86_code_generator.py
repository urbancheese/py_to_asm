from typing import Dict, List
from py_to_asm_compiler import ASTNode, NumberNode, BinaryOpNode, VariableNode, AssignmentNode, IfNode

class X86CodeGenerator:
    def __init__(self):
        self.variables: Dict[str, int] = {}
        self.next_var_offset = 4
        self.label_counter = 0
        self.output = []

    def generate(self, nodes: List[ASTNode]) -> str:
        # Setup stack frame
        self.emit('global _start')
        self.emit('section .text')
        self.emit('_start:')
        self.emit('push ebp')
        self.emit('mov ebp, esp')
        
        # Generate code for each node
        for node in nodes:
            self.generate_node(node)
        
        # Clean up and exit
        self.emit('mov esp, ebp')
        self.emit('pop ebp')
        self.emit('mov eax, 1')  # sys_exit
        self.emit('xor ebx, ebx')  # status = 0
        self.emit('int 0x80')
        
        return '\n'.join(self.output)

    def generate_node(self, node: ASTNode) -> None:
        if isinstance(node, NumberNode):
            self.emit(f'mov eax, {node.value}')
        
        elif isinstance(node, BinaryOpNode):
            self.generate_binary_op(node)
        
        elif isinstance(node, VariableNode):
            if node.name in self.variables:
                offset = self.variables[node.name]
                self.emit(f'mov eax, [ebp-{offset}]')
            else:
                raise Exception(f"Undefined variable: {node.name}")
        
        elif isinstance(node, AssignmentNode):
            self.generate_assignment(node)
        
        elif isinstance(node, IfNode):
            self.generate_if_statement(node)

    def generate_binary_op(self, node: BinaryOpNode) -> None:
        # Generate code for right operand first
        self.generate_node(node.right)
        self.emit('push eax')  # Save right operand
        
        # Generate code for left operand
        self.generate_node(node.left)
        
        # Now eax contains left operand, and top of stack contains right operand
        self.emit('pop ebx')  # Get right operand into ebx
        
        if node.operator == '+':
            self.emit('add eax, ebx')
        elif node.operator == '-':
            self.emit('sub eax, ebx')
        elif node.operator == '*':
            self.emit('imul eax, ebx')
        elif node.operator == '/':
            self.emit('cdq')  # Sign extend eax into edx
            self.emit('idiv ebx')
        elif node.operator in ['<', '>', '<=', '>=', '==', '!=']:
            self.emit('cmp eax, ebx')
            if node.operator == '<':
                self.emit('setl al')
            elif node.operator == '>':
                self.emit('setg al')
            elif node.operator == '<=':
                self.emit('setle al')
            elif node.operator == '>=':
                self.emit('setge al')
            elif node.operator == '==':
                self.emit('sete al')
            elif node.operator == '!=':
                self.emit('setne al')
            self.emit('movzx eax, al')  # Zero extend al to eax

    def generate_assignment(self, node: AssignmentNode) -> None:
        # Generate code for the value
        self.generate_node(node.value)
        
        # Allocate space for variable if it doesn't exist
        if node.name not in self.variables:
            self.variables[node.name] = self.next_var_offset
            self.next_var_offset += 4
        
        # Store the value in the variable
        offset = self.variables[node.name]
        self.emit(f'mov [ebp-{offset}], eax')

    def generate_if_statement(self, node: IfNode) -> None:
        end_label = self.get_new_label()
        
        # Generate condition code
        self.generate_node(node.condition)
        self.emit('test eax, eax')
        self.emit(f'jz {end_label}')
        
        # Generate code for the body
        for stmt in node.body:
            self.generate_node(stmt)
        
        self.emit(f'{end_label}:')

    def get_new_label(self) -> str:
        label = f'L{self.label_counter}'
        self.label_counter += 1
        return label

    def emit(self, instruction: str) -> None:
        self.output.append(instruction)