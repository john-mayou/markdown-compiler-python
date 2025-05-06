import compiler

def test_lexer_paragraph() -> None:
  assert(
    compiler.Compiler().tokenize('text') ==
    [
      compiler.Lexer.TextToken(text='text', bold=False, italic=False),
      compiler.Lexer.NewLineToken()
    ]
  )
  
def test_parser() -> None:
  assert(
    compiler.Compiler().parse([
      compiler.Lexer.TextToken(text='text', bold=False, italic=False),
      compiler.Lexer.NewLineToken()
    ]) ==
    compiler.Parser.ASTRootNode(children=[
      compiler.Parser.ASTParagraphNode(children=[
        compiler.Parser.ASTTextNode(text='text', bold=False, italic=False)
      ])
    ])
  )
  
def test_code_gen() -> None:
  assert(
    compiler.Compiler().gen(
      compiler.Parser.ASTRootNode(children=[
        compiler.Parser.ASTParagraphNode(children=[
          compiler.Parser.ASTTextNode(text='text', bold=False, italic=False)
        ])
      ])
    ) == '<p>text</p>'
  )