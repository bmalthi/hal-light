from pathlib import Path
S=Path(__file__).resolve().parent
s=(S.parent/'brief.html').read_text();head=s.split('<body>')[0]
start=s.index('<h2>A simple forecast');end=s.index('<h2>Question &amp; Framing')
(S/'qa-lower.html').write_text(head+'<body><main class="page">'+s[start:end]+'</main></body></html>')
