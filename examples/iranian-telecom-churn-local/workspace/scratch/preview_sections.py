from pathlib import Path
import re
p=Path(__file__).parent
s=(p.parent/'brief.html').read_text()
start=s.index('<section><h2>The scorecard improves')
end=s.index('<section><h2>A randomized trial')
(p/'charts-preview.html').write_text(s[:s.index('<body>')]+'<body><main class="page">'+s[start:end]+'</main></body></html>')
