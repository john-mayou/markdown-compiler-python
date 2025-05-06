from __future__ import annotations
from dataclasses import dataclass, field
from typing import Type, TypeVar, Union
import re

class Compiler():
  def compile(self, md: str) -> str:
    return self.gen(self.parse(self.tokenize(md)))
  
  def tokenize(self, md: str) -> list[Lexer.Token]:
    return Lexer(md).tokenize()
  
  def parse(self, tks: list[Lexer.Token]) -> Parser.ASTRootNode:
    return Parser(tks).parse()
  
  def gen(self, ast: Parser.ASTRootNode) -> str:
    return CodeGen(ast).gen()

class Lexer:
  
  LIST_INDENT_SIZE = 2
  
  @dataclass
  class HeaderToken:
    size: int
    
  @dataclass
  class TextToken:
    text: str
    bold: bool
    italic: bool
    
  @dataclass
  class ListItemToken:
    indent: int
    ordered: bool
    digit: int
    
  @dataclass
  class CodeBlockToken:
    lang: str
    code: str
    
  @dataclass
  class CodeInlineToken:
    lang: str
    code: str
    
  @dataclass
  class BlockQuoteToken:
    indent: int
    
  @dataclass
  class ImageToken:
    alt: str
    src: str
    
  @dataclass
  class LinkToken:
    text: str
    href: str
    
  @dataclass
  class HorizontalRuleToken: pass
  
  @dataclass  
  class NewLineToken: pass
  
  Token = Union[HeaderToken, TextToken, ListItemToken, CodeBlockToken, CodeInlineToken,
                BlockQuoteToken, ImageToken, LinkToken, HorizontalRuleToken, NewLineToken]
  
  def __init__(self, md: str) -> None:
    self.md = md
    self.tks: list[Lexer.Token] = []
    
  def tokenize(self) -> list[Token]:
    while self.md:
      if self.try_tokenize_header(): continue
      if self.try_tokenize_code_block(): continue
      if self.try_tokenize_block_quote(): continue
      if self.try_tokenize_horizontal_rule(): continue
      if self.try_tokenize_list(): continue
      if self.try_tokenize_header_alt(): continue
      if self.try_tokenize_new_line(): continue
      self.tokenize_current_line()
      
    if self.tks and not isinstance(self.tks[-1], Lexer.NewLineToken):
      self.tks.append(Lexer.NewLineToken())
      
    return self.tks
      
  def try_tokenize_header(self) -> bool:
    match = re.match(r"\A(######|#####|####|###|##|#) ", self.md)
    if not match: return False
    
    hsize = len(match.group(1))
    self.tks.append(Lexer.HeaderToken(size=hsize))
    self.md = self.md[hsize + 1:]
    self.tokenize_current_line()
    self.tks.append(Lexer.HorizontalRuleToken())
    self.tks.append(Lexer.NewLineToken())
    
    return True
  
  def try_tokenize_code_block(self) -> bool:
    match = re.match(r"\A```(.*?)\s*\n", self.md)
    if not match: return False
    
    code_start = 0
    while True:
      code_start += 1
      if code_start >= len(self.md):
        return False # no ending to code block
      if self.md[code_start] == '\n':
        code_start += 1
        break
    
    code_end = code_start
    while True:
      if code_end + 2 >= len(self.md):
        return False # no ending to code block
      if self.md[code_end] == '`' and self.md[code_end + 1] == '`' and self.md[code_end + 2]:
        code_end -= 2 # go backwards through `, \n
        break
      code_end += 1
      
    # make sure we haven't altered self.md up until this point since we need to ensure there
    # is an ending block. If there is no ending block, we would have returned False somewhere
    # above. In that case, we should try tokenizing a different token with the original self.md.
    
    code = self.md[code_start: code_end + 1]
    self.md = self.md[code_end + 4:] # move to after the ```
    self.tks.append(Lexer.CodeBlockToken(lang=match.group(1) or "", code=code))
    self.tks.append(Lexer.NewLineToken())
    
    return True
  
  def try_tokenize_block_quote(self) -> bool:
    match = re.match(r"\A(>(?: >)* ?)", self.md)
    if not match: return False
    
    indent = 0
    for ch in str(match.group(1)):
      if ch == '>': indent += 1
      
    self.tks.append(Lexer.BlockQuoteToken(indent=indent))
    self.md = self.md[len(match.group(1)):]
    self.tokenize_current_line()
    
    return True
  
  def try_tokenize_horizontal_rule(self) -> bool:
    match = re.match(r"\A(\*{3,}[\* ]*|-{3,}[- ]*)$", self.md)
    if not match: return False
    
    self.tks.append(Lexer.HorizontalRuleToken())
    self.tks.append(Lexer.NewLineToken())
    self.md = self.md[len(match.group(1)) + 1:] # 1 = new line
    
    return True
  
  def try_tokenize_list(self) -> bool:
    match = re.match(r"\A *(?:([0-9]\.)|(\*|-)) ", self.md)
    if not match: return False
    
    spaces = 0
    while self.md[spaces] == ' ':
      spaces += 1
      
    if self.md[spaces] == '*' or self.md[spaces] == '-': # un-ordered
      self.tks.append(Lexer.ListItemToken(indent=spaces // self.LIST_INDENT_SIZE, ordered=False, digit=-1))
      self.md = self.md[spaces + 2:] # 2 = */- + space
    else: # ordered
      # only support one digit for now
      self.tks.append(Lexer.ListItemToken(indent=spaces // self.LIST_INDENT_SIZE, ordered=True, digit=int(self.md[spaces])))
      self.md = self.md[spaces + 3:] # 3 = digit + period + space
    
    self.tokenize_current_line()
    
    return True
  
  def try_tokenize_header_alt(self) -> bool:
    match = re.match(r"\A.+\n(=+|-+) *", self.md)
    if not match: return False
    
    # search next line for header size (=== for h1, --- for h2)
    pointer = 0
    while self.md[pointer] != '\n':
      pointer += 1
    hsize_ch = self.md[pointer + 1] # go to beginning of next line
    if hsize_ch == '=':
      self.tks.append(Lexer.HeaderToken(size=1))
    elif hsize_ch == '-':
      self.tks.append(Lexer.HeaderToken(size=2))
    else:
      raise RuntimeError(f"Invalid char found for header alt: {hsize_ch}")
      
    self.tokenize_current_line()
    self.del_current_line() # ---/=== line
    self.tks.append(Lexer.HorizontalRuleToken())
    self.tks.append(Lexer.NewLineToken())
    
    return True
  
  def try_tokenize_new_line(self) -> bool:
    match = re.match(r"\A\n", self.md)
    if not match: return False
    
    self.tks.append(Lexer.NewLineToken())
    self.md = self.md[1:]
    
    return True
  
  def tokenize_current_line(self) -> None:
    if not self.md:
      return
    if self.md[0] == '\n': # already at end of line
      self.tks.append(Lexer.NewLineToken())
      self.md = self.md[1]
      return
    
    # find current line
    line_end = 0
    while True:
      line_end += 1
      if line_end == len(self.md): # EOF
        break
      if self.md[line_end] == '\n':
        break
    line = self.md[:line_end + 1]
    self.md = self.md[len(line):]
    
    # keep track of current substring
    curr_str: list[str] = []
    def curr_push() -> None:
      self.tks.append(Lexer.TextToken(text=''.join(curr_str), bold=False, italic=False))
      curr_str.clear()
    
    while line:
      # == bold and italic ==
      match = re.match(r"\A(\*{3}[^\*]+?\*{3}|_{3}[^_]+?_{3})", line)
      if match:
        if curr_str: curr_push()
        
        self.tks.append(Lexer.TextToken(text=str(match.group(1)).replace('*', '').replace('_', ''), bold=True, italic=True))
        line = line[len(match.group(1)):]
        
        continue
      
      # == bold ==
      match = re.match(r"\A(\*{2}[^\*]+?\*{2}|_{2}[^_]+?_{2})", line)
      if match:
        if curr_str: curr_push()
        
        self.tks.append(Lexer.TextToken(text=str(match.group(1)).replace('*', '').replace('_', ''), bold=True, italic=False))
        line = line[len(match.group(1)):]
        
        continue
      
      # == italic ==
      match = re.match(r"\A(\*[^\*]+?\*|_[^_]+?_)", line)
      if match:
        if curr_str: curr_push()
        
        self.tks.append(Lexer.TextToken(text=str(match.group(1)).replace('*', '').replace('_', ''), bold=False, italic=True))
        line = line[len(match.group(1)):]
        
        continue
      
      # == image ==
      match = re.match(r"\A!\[(.*)\]\((.*)\)", line)
      if match:
        if curr_str: curr_push()
        
        self.tks.append(Lexer.ImageToken(alt=match.group(1), src=match.group(2)))
        line = line[len(match.group(1)) + len(match.group(2)) + 5:] # 5 = ![]()
        
        continue
      
      # == link ==
      match = re.match(r"\A\[(.*)\]\((.*)\)", line)
      if match:
        if curr_str: curr_push()
        
        self.tks.append(Lexer.LinkToken(text=match.group(1), href=match.group(2)))
        line = line[len(match.group(1)) + len(match.group(2)) + 4:] # 4 = []()
        
        continue
      
      # == code ==
      match = re.match(r"\A`(.+?)`([a-z]*)", line)
      if match:
        if curr_str: curr_push()
        
        code = match.group(1)
        lang = match.group(2) or ""
        self.tks.append(Lexer.CodeInlineToken(lang=lang, code=code))
        line = line[len(code) + len(lang) + 2:] # 2 = ``
        
        continue
      
      # == new line ==
      if line[0] == '\n':
        if curr_str: curr_push()
        
        self.tks.append(Lexer.NewLineToken())
        break
      
      # == default ==
      curr_str.append(line[0])
      line = line[1:]
      
    if curr_str: curr_push()
    
  def del_current_line(self) -> None:
    pointer = 0
    while True:
      pointer += 1
      if pointer == len(self.md): # EOF
        self.md = ""
        break
      if self.md[pointer] == '\n':
        self.md = self.md[pointer + 1:]
        break
      
class Parser:
  
  @dataclass
  class ASTRootNode:
    children: list[Parser.ASTNode] = field(default_factory=list)
    
  @dataclass
  class ASTHeaderNode:
    size: int
    children: list[Parser.ASTNode] = field(default_factory=list)
  
  @dataclass
  class ASTCodeBlockNode:
    lang: str
    code: str
  
  @dataclass
  class ASTCodeInlineNode:
    lang: str
    code: str
  
  @dataclass
  class ASTQuoteNode:
    children: list[Parser.ASTNode]
  
  @dataclass
  class ASTQuoteItemNode:
    children: list[Parser.ASTNode] = field(default_factory=list)
  
  @dataclass
  class ASTParagraphNode:
    children: list[Parser.ASTNode] = field(default_factory=list)
  
  @dataclass
  class ASTTextNode:
    text: str
    bold: bool
    italic: bool
  
  @dataclass
  class ASTHorizontalRuleNode: pass
  
  @dataclass
  class ASTImageNode:
    alt: str
    src: str
  
  @dataclass
  class ASTLinkNode:
    text: str
    href: str
  
  @dataclass
  class ASTListNode:
    ordered: bool
    children: list[Parser.ASTNode] = field(default_factory=list)
  
  @dataclass
  class ASTListItemNode:
    children: list[Parser.ASTNode] = field(default_factory=list)
    
  ASTNode = Union[ASTRootNode, ASTHeaderNode, ASTCodeBlockNode, ASTCodeInlineNode, ASTQuoteNode,
                  ASTQuoteItemNode, ASTParagraphNode, ASTTextNode, ASTHorizontalRuleNode,
                  ASTImageNode, ASTLinkNode, ASTListNode, ASTListItemNode]
  
  def __init__(self, tks: list[Lexer.Token]) -> None:
    self.tks = tks
    self.tks_start = 0
    self.root = Parser.ASTRootNode()
    
  def parse(self) -> Parser.ASTRootNode:
    while self.tks_start < len(self.tks):
      if self.peek(1, Lexer.HeaderToken):
        self.root.children.append(self.parse_header())
      elif self.peek(1, Lexer.CodeBlockToken):
        self.root.children.append(self.parse_code_block())
      elif self.peek(1, Lexer.BlockQuoteToken):
        self.root.children.append(self.parse_block_quote())
      elif self.peek(1, Lexer.HorizontalRuleToken):
        self.root.children.append(self.parse_horizontal_rule())
      elif self.peek(1, Lexer.ListItemToken):
        self.root.children.append(self.parse_list())
      elif self.peek(1, Lexer.ImageToken):
        self.root.children.append(self.parse_image())
      elif self.peek_any(1, Lexer.TextToken, Lexer.CodeInlineToken, Lexer.LinkToken):
        self.root.children.append(self.parse_paragraph())
      elif self.peek(1, Lexer.NewLineToken):
        self.consume(Lexer.NewLineToken)
      else:
        raise RuntimeError(f"Invalid token to parse:\n{self.tks[self.tks_start]}")
    
    return self.root
  
  def parse_header(self) -> Parser.ASTHeaderNode:
    token = self.consume(Lexer.HeaderToken)
    return Parser.ASTHeaderNode(size=token.size, children=self.parse_inline())
  
  def parse_code_block(self) -> Parser.ASTCodeBlockNode:
    token = self.consume(Lexer.CodeBlockToken)
    self.consume(Lexer.NewLineToken)
    return Parser.ASTCodeBlockNode(lang=token.lang, code=token.code)
  
  def parse_block_quote(self) -> Parser.ASTQuoteNode:
    root_indent = self.consume(Lexer.BlockQuoteToken).indent
    root_node = Parser.ASTQuoteNode(children=[self.parse_quote_item()])
    
    node_indent_map = {root_indent: root_node}
    while self.peek(1, Lexer.BlockQuoteToken):
      token = self.consume(Lexer.BlockQuoteToken)
      if self.peek(1, Lexer.NewLineToken):
        self.consume(Lexer.NewLineToken)
        continue
      
      node = node_indent_map.get(token.indent)
      if node:
        node.children.append(self.parse_quote_item())
      else:
        node = Parser.ASTQuoteNode(children=[self.parse_quote_item()])
        node_indent_map[token.indent] = node
        parent = node_indent_map.get(token.indent - 1, root_node)
        parent.children.append(node)
    
    return root_node
    
  def parse_quote_item(self) -> Parser.ASTQuoteItemNode:    
    return Parser.ASTQuoteItemNode(children=self.parse_inline_block_quote())
  
  @dataclass
  class ListStackItem:
    node: Parser.ASTListNode
    indent: int
  
  def parse_list(self) -> Parser.ASTListNode:
    root = Parser.ASTListNode(ordered=self.consume(Lexer.ListItemToken).ordered)
    root.children.append(Parser.ASTListItemNode(children=self.parse_inline()))
    
    list_stack: list[Parser.ListStackItem] = []
    list_stack.append(Parser.ListStackItem(node=root, indent=0))
    
    while self.peek(1, Lexer.ListItemToken):
      curr_token = self.consume(Lexer.ListItemToken)
      curr_indent = min(list_stack[-1].indent + 1, curr_token.indent) # only allow 1 additional level at a time
      last_indent= list_stack[-1].indent
      if curr_indent > last_indent: # deeper indent
        # create new node
        node = Parser.ASTListNode(ordered=curr_token.ordered)
        node.children.append(Parser.ASTListItemNode(children=self.parse_inline()))
        
        # append to last child of top (of stack) node
        top_node_last_child = list_stack[-1].node.children[-1]
        if isinstance(top_node_last_child, Parser.ASTListItemNode):
          top_node_last_child.children.append(node)
        else:
          raise RuntimeError(f"Invalid last child of top node: {type(top_node_last_child)}")
        
        # append to stack
        list_stack.append(Parser.ListStackItem(node=node, indent=curr_indent))
      elif curr_indent < last_indent: # lost indentation
        # pop from stack until we find current level
        while list_stack[-1].indent > curr_indent:
          list_stack.pop()
        list_stack[-1].node.children.append(Parser.ASTListItemNode(children=self.parse_inline()))
      else: # same indentation
        list_stack[-1].node.children.append(Parser.ASTListItemNode(children=self.parse_inline()))
  
    return root
  
  def parse_horizontal_rule(self) -> Parser.ASTHorizontalRuleNode:
    self.consume(Lexer.HorizontalRuleToken)
    self.consume(Lexer.NewLineToken)
    return Parser.ASTHorizontalRuleNode()
  
  def parse_image(self) -> Parser.ASTImageNode:
    token = self.consume(Lexer.ImageToken)
    self.consume(Lexer.NewLineToken)
    return Parser.ASTImageNode(alt=token.alt, src=token.src)
  
  def parse_paragraph(self) -> Parser.ASTParagraphNode:
    return Parser.ASTParagraphNode(children=self.parse_inline())
  
  INLINE_TOKENS: tuple[Type[Lexer.Token], ...] = (Lexer.TextToken, Lexer.CodeInlineToken, Lexer.LinkToken)
  
  def parse_inline(self) -> list[ASTNode]:
    nodes: list[Parser.ASTNode] = []
    
    while self.peek_any(1, *Parser.INLINE_TOKENS) or (self.peek(1, Lexer.NewLineToken) and self.peek_any(2, *Parser.INLINE_TOKENS)):
      if self.peek(1, Lexer.NewLineToken):
        self.consume(Lexer.NewLineToken)
        nodes.append(Parser.ASTTextNode(text='', bold=False, italic=False))
        
      nodes.append(self.parse_inline_single())
    self.consume(Lexer.NewLineToken)
    
    return nodes
  
  def parse_inline_block_quote(self) -> list[ASTNode]:
    nodes: list[Parser.ASTNode] = []
    
    while self.peek_any(1, *Parser.INLINE_TOKENS) or (self.peek(1, Lexer.NewLineToken) and self.peek(2, Lexer.BlockQuoteToken) and self.peek_any(3, *Parser.INLINE_TOKENS)):
      if self.peek(1, Lexer.NewLineToken):
        self.consume(Lexer.NewLineToken)
        self.consume(Lexer.BlockQuoteToken)
        nodes.append(Parser.ASTTextNode(text='', bold=True, italic=True))
        
      nodes.append(self.parse_inline_single())
    self.consume(Lexer.NewLineToken)
    
    return nodes
  
  def parse_inline_single(self) -> ASTNode:
    if self.peek(1, Lexer.TextToken):
      text_token = self.consume(Lexer.TextToken)
      return Parser.ASTTextNode(text=text_token.text, bold=text_token.bold, italic=text_token.italic)
    elif self.peek(1, Lexer.CodeInlineToken):
      code_token = self.consume(Lexer.CodeInlineToken)
      return Parser.ASTCodeInlineNode(lang=code_token.lang, code=code_token.code)
    elif self.peek(1, Lexer.LinkToken):
      link_token = self.consume(Lexer.LinkToken)
      return Parser.ASTLinkNode(text=link_token.text, href=link_token.href)
    else:
      raise RuntimeError(f"Invalid inline token type: {type(self.tks[self.tks_start])}")
  
  def peek(self, depth: int, tokenType: Type[Lexer.Token]) -> bool:
    index = self.tks_start + depth - 1
    if index >= len(self.tks):
      return False
    return isinstance(self.tks[index], tokenType)
  
  def peek_any(self, depth: int, *tokenTypes: Type[Lexer.Token]) -> bool:
    for tokenType in tokenTypes:
      if self.peek(depth, tokenType):
        return True
    return False
  
  TokenT = TypeVar("TokenT", bound=Lexer.Token)
  
  def consume(self, tokenType: Type[TokenT]) -> TokenT:
    if self.tks_start == len(self.tks):
      raise RuntimeError(f"Expected to find token type {tokenType} but did not find a token")
    
    token = self.tks[self.tks_start]
    self.tks_start += 1
    if not isinstance(token, tokenType):
      raise RuntimeError(f"Expected to find token type {tokenType} but found {type(token)}")
    
    return token
  
class CodeGen:
  def __init__(self, ast: Parser.ASTRootNode) -> None:
    self.ast = ast
    self.html: list[str] = []
    
  def gen(self) -> str:
    for node in self.ast.children:
      if isinstance(node, Parser.ASTHeaderNode):
        self.html.append(self.gen_header(node))
      elif isinstance(node, Parser.ASTCodeBlockNode):
        self.html.append(self.gen_code_block(node))
      elif isinstance(node, Parser.ASTQuoteNode):
        self.html.append(self.gen_quote_block(node))
      elif isinstance(node, Parser.ASTListNode):
        self.html.append(self.gen_list(node))
      elif isinstance(node, Parser.ASTHorizontalRuleNode):
        self.html.append(self.gen_horizontal_rule(node))
      elif isinstance(node, Parser.ASTImageNode):
        self.html.append(self.gen_image(node))
      elif isinstance(node, Parser.ASTLinkNode):
        self.html.append(self.gen_link(node))
      elif isinstance(node, Parser.ASTCodeInlineNode):
        self.html.append(self.gen_code_inline(node))
      elif isinstance(node, Parser.ASTParagraphNode):
        self.html.append(self.gen_paragraph(node))
      else:
        raise RuntimeError(f"Invalid node type: {node}")
    
    return ''.join(self.html)
  
  def gen_header(self, node: Parser.ASTHeaderNode) -> str:
    return f'<h{node.size}>{self.gen_line(node.children)}<h{node.size}>'
  
  def gen_code_block(self, node: Parser.ASTCodeBlockNode) -> str:
    return f'<pre><code class="{self.escape_html(node.lang)}">{node.code}</code></pre>'
  
  def gen_quote_block(self, node: Parser.ASTQuoteNode) -> str:
    html: list[str] = ['<blockquote>']
    
    for child in node.children:
      if isinstance(child, Parser.ASTQuoteNode):
        html.append(self.gen_quote_block(node))
      elif isinstance(child, Parser.ASTQuoteItemNode):
        html.append(f"<p>{self.gen_line(child.children)}</p>")
      else:
        raise RuntimeError(f"Invalid child node: {child}")
      
    html.append('</blockquote>')
    return ''.join(html)
  
  def gen_list(self, node: Parser.ASTListNode) -> str:
    html: list[str] = ['<ol>'] if node.ordered else ['<ul>']
    
    for child in node.children:
      html.append("<li>")
      if not isinstance(child, Parser.ASTListItemNode):
        raise RuntimeError("Invalid child type of list node: {type(child)}")
      for inner_child in child.children:
        if isinstance(inner_child, Parser.ASTListNode):
          html.append(self.gen_list(inner_child))
        else:
          html.append(self.gen_line([inner_child]))
      html.append("</li>")
    
    html.append('</ol>' if node.ordered else '</ul>')
    return ''.join(html)
  
  def gen_horizontal_rule(self, node: Parser.ASTHorizontalRuleNode) -> str:
    return '<hr>'
  
  def gen_image(self, node: Parser.ASTImageNode) -> str:
    return f'<img alt="{self.escape_html(node.alt)}" src="{self.escape_html(node.src)}"/>'
  
  def gen_link(self, node: Parser.ASTLinkNode) -> str:
    return f'<a href="{self.escape_html(node.href)}">{self.escape_html(node.text)}</a>'
  
  def gen_code_inline(self, node: Parser.ASTCodeInlineNode) -> str:
    return f'<code class"{self.escape_html(node.lang)}">{node.code}</code>'
  
  def gen_paragraph(self, node: Parser.ASTParagraphNode) -> str:
    return f'<p>{self.gen_line(node.children)}</p>'
  
  def gen_line(self, nodes: list[Parser.ASTNode]) -> str:
    html: list[str] = []
    
    for node in nodes:
      if isinstance(node, Parser.ASTLinkNode):
        html.append(self.gen_link(node))
      elif isinstance(node, Parser.ASTCodeInlineNode):
        html.append(self.gen_code_inline(node))
      elif isinstance(node, Parser.ASTTextNode):
        html.append(self.gen_text(node))
      else:
        raise RuntimeError(f"Invalid inline node: {node}")
      
    return ''.join(html)
  
  def gen_text(self, node: Parser.ASTTextNode) -> str:
    html: list[str] = []
    
    if node.italic:
      html.append('<i>')
    if node.bold:
      html.append('<b>')
    
    html.append(self.escape_html(node.text))
    
    if node.bold:
      html.append('</b>')
    if node.italic:
      html.append('</i>')
    
    return ''.join(html)
  
  ESCAPE_HTML_MAP: dict[str, str] = {
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;',
    '"': '&quot;',
  }
  
  def escape_html(self, string: str) -> str:
    # wait until we know we need a replacement before creating new string object and allocating an array
    new_html: Union[list[str], None] = None
    
    for i in range(len(string)):
      replacement = CodeGen.ESCAPE_HTML_MAP.get(string[i])
      if replacement:
        if new_html is None:
          new_html = [string[:i + 1]] # copy everything up to first replacement
        new_html.append(replacement)
      elif new_html:
        new_html.append(string[i])
        
    return ''.join(new_html) if new_html else string