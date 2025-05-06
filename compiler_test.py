from pathlib import Path
import subprocess
import compiler
import os

UPDATE = os.getenv('UPDATE') == 'true' # to force write golden files

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
  
def test_golden() -> None:
  for filepath in list(Path('testdata').glob('*.text')):
    actual = prettify_html(compiler.Compiler().compile(filepath.read_text()))
    
    golden = filepath.with_suffix('.html')
    if UPDATE:
      golden.write_text(actual)
      
    expected = golden.read_text()
    assert(expected == actual)
    
def prettify_html(html: str) -> str:
  result = subprocess.run(['prettier', '--parser', 'html'], input=html, text=True, capture_output=True)
  assert(result.returncode == 0)
  return result.stdout