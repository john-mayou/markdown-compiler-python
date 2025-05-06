import compiler

def test_lexer_paragraph() -> None:
  assert(
    compiler.Lexer('text').tokenize() ==
    [
      compiler.Lexer.TextToken(text='text', bold=False, italic=False),
      compiler.Lexer.NewLineToken()
    ]
  )