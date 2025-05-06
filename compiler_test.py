import compiler

def test_lexer_paragraph() -> None:
  assert(
    compiler.Lexer('text').tokenize() ==
    [
      compiler.Lexer.TextToken(text='text', bold=False, italic=False),
      compiler.Lexer.NewLineToken()
    ]
  )
  
def test_parser() -> None:
  assert(
    compiler.Parser([
      compiler.Lexer.TextToken(text='text', bold=False, italic=False),
      compiler.Lexer.NewLineToken()
    ]).parse() ==
    compiler.Parser.ASTRootNode(children=[
      compiler.Parser.ASTParagraphNode(children=[
        compiler.Parser.ASTTextNode(text='text', bold=False, italic=False)
      ])
    ])
  )
  
def test_code_gen() -> None:
  assert(
    compiler.CodeGen(
      compiler.Parser.ASTRootNode(children=[
        compiler.Parser.ASTParagraphNode(children=[
          compiler.Parser.ASTTextNode(text='text', bold=False, italic=False)
        ])
      ])
    ).gen() == '<p>text</p>'
  )