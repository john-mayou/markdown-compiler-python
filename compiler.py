from dataclasses import dataclass
from typing import Union
import re

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
  
  Token = Union[HeaderToken, TextToken, ListItemToken, CodeBlockToken, CodeInlineToken, BlockQuoteToken, ImageToken, LinkToken, HorizontalRuleToken, NewLineToken]
  
  def __init__(self, md: str) -> None:
    self.md = md
    self.tks: list[Lexer.Token] = []
    
  def tokenize(self) -> list[Token]:
    while self.md:
      print('here')
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
    
    codeStart = 0
    while True:
      codeStart += 1
      if codeStart >= len(self.md):
        return False # no ending to code block
      if self.md[codeStart] == '\n':
        codeStart += 1
        break
    
    codeEnd = codeStart
    while True:
      if codeEnd + 2 >= len(self.md):
        return False # no ending to code block
      if self.md[codeEnd] == '`' and self.md[codeEnd + 1] == '`' and self.md[codeEnd + 2]:
        codeEnd -= 2 # go backwards through `, \n
        break
      codeEnd += 1
      
    # make sure we haven't altered self.md up until this point since we need to ensure there
    # is an ending block. If there is no ending block, we would have returned False somewhere
    # above. In that case, we should try tokenizing a different token with the original self.md.
    
    code = self.md[codeStart: codeEnd + 1]
    self.md = self.md[codeEnd + 4:] # move to after the ```
    self.tks.append(Lexer.CodeBlockToken(lang=match.group(1) or "", code=code))
    self.tks.append(Lexer.NewLineToken())
    
    return True
  
  def try_tokenize_block_quote(self) -> bool:
    match = re.match(r"\A(<(?: >)* ?).*$", self.md)
    if not match: return False
    
    indent = 0
    for ch in match.group(1):
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
    hsizeCh = self.md[pointer + 1] # go to beginning of next line
    if hsizeCh == '=':
      self.tks.append(Lexer.HeaderToken(size=1))
    elif hsizeCh == '-':
      self.tks.append(Lexer.HeaderToken(size=2))
    else:
      raise RuntimeError(f"Invalid char found for header alt: {hsizeCh}")
      
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
    lineEnd = 0
    while True:
      lineEnd += 1
      if lineEnd == len(self.md): # EOF
        break
      if self.md[lineEnd] == '\n':
        break
    line = self.md[:lineEnd + 1]
    self.md = self.md[len(line):]
    
    # keep track of current substring
    currStr: list[str] = []
    currPush = lambda: (
      self.tks.append(Lexer.TextToken(text=''.join(currStr), bold=False, italic=False)),
      currStr.clear()
    )
    
    while line:
      # == bold and italic ==
      match = re.match(r"\A(\*{3}[^\*]+?\*{3}|_{3}[^_]+?_{3})", line)
      if match:
        if currStr: currPush()
        
        self.tks.append(Lexer.TextToken(text=match.group(1).replace('*', '').replace('_', ''), bold=True, italic=True))
        line = line[len(match.group(1)):]
        
        continue
      
      # == bold ==
      match = re.match(r"\A(\*{2}[^\*]+?\*{2}|_{2}[^_]+?_{2})", line)
      if match:
        if currStr: currPush()
        
        self.tks.append(Lexer.TextToken(text=match.group(1).replace('*', '').replace('_', ''), bold=True, italic=False))
        line = line[len(match.group(1)):]
        
        continue
      
      # == italic ==
      match = re.match(r"\A(\*[^\*]+?\*|_[^_]+?_)", line)
      if match:
        if currStr: currPush()
        
        self.tks.append(Lexer.TextToken(text=match.group(1).replace('*', '').replace('_', ''), bold=False, italic=True))
        line = line[len(match.group(1)):]
        
        continue
      
      # == image ==
      match = re.match(r"\A!\[(.*)\]\((.*)\)", line)
      if match:
        if currStr: currPush()
        
        self.tks.append(Lexer.ImageToken(alt=match.group(1), src=match.group(2)))
        line = line[len(match.group(1)) + len(match.group(2)) + 5:] # 5 = ![]()
        
        continue
      
      # == link ==
      match = re.match(r"\A\[(.*)\]\((.*)\)", line)
      if match:
        if currStr: currPush()
        
        self.tks.append(Lexer.LinkToken(text=match.group(1), href=match.group(2)))
        line = line[len(match.group(1)) + len(match.group(2)) + 4:] # 4 = []()
        
        continue
      
      # == code ==
      match = re.match(r"\A`(.+?)`([a-z]*)", line)
      if match:
        if currStr: currPush()
        
        code = match.group(1)
        lang = match.group(2) or ""
        self.tks.append(Lexer.CodeInlineToken(lang=lang, code=code))
        line = line[len(code) + len(lang) + 2:] # 2 = ``
        
        continue
      
      # == new line ==
      if line[0] == '\n':
        if currStr: currPush()
        
        self.tks.append(Lexer.NewLineToken())
        break
      
      # == default ==
      currStr.append(line[0])
      line = line[1:]
      
    if currStr: currPush()
    
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