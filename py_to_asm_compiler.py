from enum import Enum
import re
from typing import List, Optional

# Token types for lexical analysis
class TokenType(Enum):
    NUMBER = 'NUMBER'
    IDENTIFIER = 'IDENTIFIER'
    OPERATOR = 'OPERATOR'
    KEYWORD = 'KEYWORD'
    INDENT = 'INDENT'
    DEDENT = 'DEDENT'
    NEWLINE = 'NEWLINE'
    EOF = 'EOF'

class Token:
    def __init__(self, type: TokenType, value: str, line: int, column: int):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.indent_stack = [0]
        self.tokens = []

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            char = self.source[self.pos]
            
            # Handle whitespace and indentation
            if char.isspace():
                if char == '\n':
                    self.tokens.append(Token(TokenType.NEWLINE, '\n', self.line, self.column))
                    self.line += 1
                    self.column = 1
                    self.pos += 1
                    self.handle_indentation()
                else:
                    self.column += 1
                    self.pos += 1
                continue

            # Handle comments
            if char == '#':
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self.pos += 1
                    self.column += 1
                continue

            # Handle numbers
            if char.isdigit():
                token = self.tokenize_number()
                self.tokens.append(token)
                continue

            # Handle identifiers and keywords
            if char.isalpha() or char == '_':
                token = self.tokenize_identifier()
                self.tokens.append(token)
                continue

            # Handle operators
            if char in '+-*/<>=':
                token = self.tokenize_operator()
                self.tokens.append(token)
                continue

            self.pos += 1
            self.column += 1

        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens

    def tokenize_number(self) -> Token:
        start_pos = self.pos
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            self.pos += 1
            self.column += 1
        value = self.source[start_pos:self.pos]
        return Token(TokenType.NUMBER, value, self.line, self.column - len(value))

    def tokenize_identifier(self) -> Token:
        start_pos = self.pos
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.pos += 1
            self.column += 1
        value = self.source[start_pos:self.pos]
        token_type = TokenType.KEYWORD if value in ['if', 'while', 'for', 'def', 'return'] else TokenType.IDENTIFIER
        return Token(token_type, value, self.line, self.column - len(value))

    def tokenize_operator(self) -> Token:
        start_pos = self.pos
        self.pos += 1
        self.column += 1
        value = self.source[start_pos:self.pos]
        return Token(TokenType.OPERATOR, value, self.line, self.column - len(value))

    def handle_indentation(self):
        indent_level = 0
        while self.pos < len(self.source) and self.source[self.pos] in ' \t':
            if self.source[self.pos] == ' ':
                indent_level += 1
            else:  # tab character
                indent_level += 4  # Convert tabs to spaces (4 spaces per tab)
            self.pos += 1
            self.column += 1

        if indent_level > self.indent_stack[-1]:
            self.indent_stack.append(indent_level)
            self.tokens.append(Token(TokenType.INDENT, ' ' * indent_level, self.line, 1))
        while indent_level < self.indent_stack[-1]:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, '', self.line, 1))

# AST Node classes
class ASTNode:
    pass

class NumberNode(ASTNode):
    def __init__(self, value: int):
        self.value = value

class BinaryOpNode(ASTNode):
    def __init__(self, left: ASTNode, operator: str, right: ASTNode):
        self.left = left
        self.operator = operator
        self.right = right

class VariableNode(ASTNode):
    def __init__(self, name: str):
        self.name = name

class AssignmentNode(ASTNode):
    def __init__(self, name: str, value: ASTNode):
        self.name = name
        self.value = value

class IfNode(ASTNode):
    def __init__(self, condition: ASTNode, body: List[ASTNode]):
        self.condition = condition
        self.body = body

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> List[ASTNode]:
        nodes = []
        while not self.is_at_end():
            nodes.append(self.parse_statement())
        return nodes

    def parse_statement(self) -> ASTNode:
        # Skip any newlines before the statement
        while self.check(TokenType.NEWLINE):
            self.consume()
            
        token = self.current_token()
        
        if token.type == TokenType.IDENTIFIER:
            if self.peek_next().value == '=':
                node = self.parse_assignment()
                self.consume_newline()
                return node
        elif token.type == TokenType.KEYWORD and token.value == 'if':
            return self.parse_if_statement()

        node = self.parse_expression()
        self.consume_newline()
        return node

    def parse_assignment(self) -> AssignmentNode:
        name = self.consume().value
        self.consume()  # consume '='
        value = self.parse_expression()
        return AssignmentNode(name, value)

    def parse_if_statement(self) -> IfNode:
        self.consume()  # consume 'if'
        condition = self.parse_expression()
        self.consume_newline()
        
        # Ensure we have an indented block
        if not self.check(TokenType.INDENT):
            raise Exception("Expected indented block after if statement")
        self.consume_indent()
        
        body = []
        while not self.check(TokenType.DEDENT) and not self.is_at_end():
            body.append(self.parse_statement())
            
        if not self.is_at_end():
            self.consume_dedent()
        
        return IfNode(condition, body)

    def parse_expression(self) -> ASTNode:
        return self.parse_comparison()

    def parse_comparison(self) -> ASTNode:
        expr = self.parse_term()
        
        while self.match(['<', '>', '<=', '>=', '==', '!=']):
            operator = self.previous().value
            right = self.parse_term()
            expr = BinaryOpNode(expr, operator, right)
            
        return expr

    def parse_term(self) -> ASTNode:
        expr = self.parse_factor()
        
        while self.match(['+', '-']):
            operator = self.previous().value
            right = self.parse_factor()
            expr = BinaryOpNode(expr, operator, right)
            
        return expr

    def parse_factor(self) -> ASTNode:
        expr = self.parse_primary()
        
        while self.match(['*', '/']):
            operator = self.previous().value
            right = self.parse_primary()
            expr = BinaryOpNode(expr, operator, right)
            
        return expr

    def parse_primary(self) -> ASTNode:
        if self.match([TokenType.NUMBER]):
            return NumberNode(int(self.previous().value))
        elif self.match([TokenType.IDENTIFIER]):
            return VariableNode(self.previous().value)
        
        raise Exception(f"Unexpected token: {self.current_token()}")

    # Helper methods
    def current_token(self) -> Token:
        return self.tokens[self.pos]

    def peek_next(self) -> Token:
        if self.pos + 1 >= len(self.tokens):
            return Token(TokenType.EOF, '', -1, -1)
        return self.tokens[self.pos + 1]

    def consume(self) -> Token:
        token = self.current_token()
        self.pos += 1
        return token

    def consume_newline(self):
        if self.check(TokenType.NEWLINE):
            self.consume()

    def consume_indent(self):
        if self.check(TokenType.INDENT):
            self.consume()
        else:
            raise Exception("Expected indentation")

    def consume_dedent(self):
        if self.check(TokenType.DEDENT):
            self.consume()

    def check(self, type: TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.current_token().type == type

    def match(self, types) -> bool:
        for t in types:
            if isinstance(t, TokenType):
                if self.check(t):
                    self.consume()
                    return True
            elif isinstance(t, str) and not self.is_at_end():
                if self.current_token().value == t:
                    self.consume()
                    return True
        return False

    def is_at_end(self) -> bool:
        return self.current_token().type == TokenType.EOF

    def previous(self) -> Token:
        return self.tokens[self.pos - 1]