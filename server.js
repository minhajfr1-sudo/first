import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(express.json());
app.use(express.static(__dirname));

const PORT = process.env.PORT || 3000;
const ANTHROPIC_KEY = process.env.ANTHROPIC_API_KEY || '';
const SERPER_KEY = process.env.SERPER_API_KEY || '';

// ─── Source Fetchers ──────────────────────────────────────────────────────────

async function fetchGoogle(query) {
  if (!SERPER_KEY) return [];
  try {
    const r = await fetch('https://google.serper.dev/search', {
      method: 'POST',
      headers: { 'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ q: query, num: 8 }),
    });
    const d = await r.json();
    return (d.organic || []).map(x => ({
      title: x.title,
      url: x.link,
      snippet: x.snippet || '',
      source: 'web',
      favicon: `https://www.google.com/s2/favicons?domain=${new URL(x.link).hostname}&sz=32`,
    }));
  } catch { return []; }
}

async function fetchReddit(query) {
  try {
    const url = `https://www.reddit.com/search.json?q=${encodeURIComponent(query)}&sort=relevance&limit=6&t=year`;
    const r = await fetch(url, { headers: { 'User-Agent': 'arca-search/2.0' } });
    const d = await r.json();
    return (d.data?.children || []).map(c => {
      const p = c.data;
      return {
        title: p.title,
        url: `https://www.reddit.com${p.permalink}`,
        snippet: p.selftext ? p.selftext.slice(0, 180) : `r/${p.subreddit} · ${p.score} points`,
        source: 'reddit',
        favicon: 'https://www.redditstatic.com/desktop2x/img/favicon/favicon-32x32.png',
        meta: { subreddit: p.subreddit, score: p.score, comments: p.num_comments },
      };
    });
  } catch { return []; }
}

async function fetchHackerNews(query) {
  try {
    const url = `https://hn.algolia.com/api/v1/search?query=${encodeURIComponent(query)}&tags=story&hitsPerPage=6`;
    const r = await fetch(url);
    const d = await r.json();
    return (d.hits || []).filter(h => h.url).map(h => ({
      title: h.title,
      url: h.url,
      snippet: `HN · ${h.points} points · ${h.num_comments} comments`,
      source: 'hackernews',
      favicon: 'https://news.ycombinator.com/favicon.ico',
      meta: { hnUrl: `https://news.ycombinator.com/item?id=${h.objectID}`, points: h.points },
    }));
  } catch { return []; }
}

async function fetchWikipedia(query) {
  try {
    const url = `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(query)}&srlimit=3&srprop=snippet&format=json&origin=*`;
    const r = await fetch(url);
    const d = await r.json();
    return (d.query?.search || []).map(p => ({
      title: p.title,
      url: `https://en.wikipedia.org/wiki/${encodeURIComponent(p.title.replace(/ /g, '_'))}`,
      snippet: p.snippet.replace(/<[^>]+>/g, ''),
      source: 'wikipedia',
      favicon: 'https://en.wikipedia.org/favicon.ico',
    }));
  } catch { return []; }
}

async function fetchPubMed(query) {
  try {
    const searchUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=${encodeURIComponent(query)}&retmax=4&retmode=json`;
    const sr = await fetch(searchUrl);
    const sd = await sr.json();
    const ids = sd.esearchresult?.idlist || [];
    if (!ids.length) return [];
    const summaryUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=${ids.join(',')}&retmode=json`;
    const dr = await fetch(summaryUrl);
    const dd = await dr.json();
    return ids.map(id => {
      const a = dd.result?.[id];
      if (!a) return null;
      return {
        title: a.title,
        url: `https://pubmed.ncbi.nlm.nih.gov/${id}/`,
        snippet: a.authors?.map(x => x.name).slice(0, 3).join(', ') || '',
        source: 'pubmed',
        favicon: 'https://pubmed.ncbi.nlm.nih.gov/favicon.ico',
      };
    }).filter(Boolean);
  } catch { return []; }
}

async function fetchSemanticScholar(query) {
  try {
    const url = `https://api.semanticscholar.org/graph/v1/paper/search?query=${encodeURIComponent(query)}&limit=4&fields=title,url,abstract,year,authors`;
    const r = await fetch(url, { headers: { 'User-Agent': 'arca-search/2.0' } });
    const d = await r.json();
    return (d.data || []).map(p => ({
      title: p.title,
      url: p.url || `https://www.semanticscholar.org/paper/${p.paperId}`,
      snippet: p.abstract ? p.abstract.slice(0, 180) : `${p.year || ''} · ${(p.authors || []).map(a => a.name).slice(0, 2).join(', ')}`,
      source: 'scholar',
      favicon: 'https://www.semanticscholar.org/favicon.ico',
    }));
  } catch { return []; }
}

async function fetchArxiv(query) {
  try {
    const url = `https://export.arxiv.org/api/query?search_query=all:${encodeURIComponent(query)}&start=0&max_results=4`;
    const r = await fetch(url);
    const text = await r.text();
    const entries = [...text.matchAll(/<entry>([\s\S]*?)<\/entry>/g)];
    return entries.map(m => {
      const e = m[1];
      const title = (e.match(/<title>([\s\S]*?)<\/title>/) || [])[1]?.trim() || '';
      const summary = (e.match(/<summary>([\s\S]*?)<\/summary>/) || [])[1]?.trim().slice(0, 180) || '';
      const link = (e.match(/<id>([\s\S]*?)<\/id>/) || [])[1]?.trim() || '';
      return { title, url: link, snippet: summary, source: 'arxiv', favicon: 'https://arxiv.org/favicon.ico' };
    }).filter(x => x.url);
  } catch { return []; }
}

async function fetchStackExchange(query) {
  try {
    const url = `https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance&q=${encodeURIComponent(query)}&site=stackoverflow&pagesize=4&filter=default`;
    const r = await fetch(url, { headers: { 'Accept-Encoding': 'identity' } });
    const d = await r.json();
    return (d.items || []).map(q => ({
      title: q.title,
      url: q.link,
      snippet: `${q.answer_count} answers · ${q.score} score · ${(q.tags || []).slice(0, 3).join(', ')}`,
      source: 'stackexchange',
      favicon: 'https://cdn.sstatic.net/Sites/stackoverflow/img/favicon.ico',
    }));
  } catch { return []; }
}

async function fetchGitHub(query) {
  try {
    const url = `https://api.github.com/search/repositories?q=${encodeURIComponent(query)}&sort=stars&per_page=4`;
    const r = await fetch(url, { headers: { 'User-Agent': 'arca-search/2.0', 'Accept': 'application/vnd.github.v3+json' } });
    const d = await r.json();
    return (d.items || []).map(repo => ({
      title: repo.full_name,
      url: repo.html_url,
      snippet: repo.description || `★ ${repo.stargazers_count}`,
      source: 'github',
      favicon: 'https://github.com/favicon.ico',
      meta: { stars: repo.stargazers_count, language: repo.language },
    }));
  } catch { return []; }
}

async function fetchMarginalia(query) {
  try {
    const url = `https://search.marginalia.nu/api/search?query=${encodeURIComponent(query)}&count=4`;
    const r = await fetch(url, { headers: { 'User-Agent': 'arca-search/2.0' } });
    const d = await r.json();
    return (d.results || []).map(p => ({
      title: p.title || p.url,
      url: p.url,
      snippet: p.description || '',
      source: 'marginalia',
      favicon: `https://www.google.com/s2/favicons?domain=${new URL(p.url).hostname}&sz=32`,
    }));
  } catch { return []; }
}

async function fetchOpenLibrary(query) {
  try {
    const url = `https://openlibrary.org/search.json?q=${encodeURIComponent(query)}&limit=3&fields=title,author_name,first_sentence,key`;
    const r = await fetch(url);
    const d = await r.json();
    return (d.docs || []).map(b => ({
      title: b.title,
      url: `https://openlibrary.org${b.key}`,
      snippet: b.first_sentence?.[0] || (b.author_name || []).join(', '),
      source: 'openlibrary',
      favicon: 'https://openlibrary.org/favicon.ico',
    }));
  } catch { return []; }
}

// ─── Normalise ────────────────────────────────────────────────────────────────

const SOURCE_LABELS = {
  web: 'Web', reddit: 'Reddit', hackernews: 'HN', wikipedia: 'Wiki',
  pubmed: 'PubMed', scholar: 'Scholar', arxiv: 'arXiv',
  stackexchange: 'Stack', github: 'GitHub', marginalia: 'Indie',
  openlibrary: 'Books', gdelt: 'News', youtube: 'YouTube', ted: 'TED',
};

function normalizeSrc(src) {
  let displayUrl = src.url;
  try { displayUrl = new URL(src.url).hostname.replace(/^www\./, ''); } catch {}
  return { ...src, displayUrl, sourceLabel: SOURCE_LABELS[src.source] || src.source };
}

// ─── Source Grouping ──────────────────────────────────────────────────────────

function groupSources(allSources) {
  const groups = [
    { label: 'Discussions', icon: '💬', keys: ['reddit', 'hackernews'], sources: [] },
    { label: 'Reference', icon: '📖', keys: ['wikipedia', 'openlibrary'], sources: [] },
    { label: 'Research', icon: '🔬', keys: ['pubmed', 'scholar', 'arxiv'], sources: [] },
    { label: 'Technical', icon: '⚙️', keys: ['stackexchange', 'github'], sources: [] },
    { label: 'Web', icon: '🌐', keys: ['web', 'marginalia'], sources: [] },
  ];
  for (const src of allSources) {
    const group = groups.find(g => g.keys.includes(src.source));
    if (group) group.sources.push(src);
  }
  return groups.filter(g => g.sources.length > 0);
}

// ─── API Routes ───────────────────────────────────────────────────────────────

app.post('/api/search', async (req, res) => {
  const { query } = req.body;
  if (!query?.trim()) return res.status(400).json({ error: 'query required' });

  const q = query.trim();

  const [web, reddit, hn, wiki, pubmed, scholar, arxiv, se, gh, marginalia, books] = await Promise.all([
    fetchGoogle(q),
    fetchReddit(q),
    fetchHackerNews(q),
    fetchWikipedia(q),
    fetchPubMed(q),
    fetchSemanticScholar(q),
    fetchArxiv(q),
    fetchStackExchange(q),
    fetchGitHub(q),
    fetchMarginalia(q),
    fetchOpenLibrary(q),
  ]);

  const all = [...web, ...reddit, ...hn, ...wiki, ...pubmed, ...scholar, ...arxiv, ...se, ...gh, ...marginalia, ...books].map(normalizeSrc);
  const groups = groupSources(all);

  res.json({ groups, total: all.length });
});

app.post('/api/read', async (req, res) => {
  const { url } = req.body;
  if (!url) return res.status(400).json({ error: 'url required' });

  try {
    const jinaUrl = `https://r.jina.ai/${url}`;
    const r = await fetch(jinaUrl, {
      headers: {
        'Accept': 'text/plain',
        'X-Return-Format': 'markdown',
        'X-Timeout': '15',
      },
      signal: AbortSignal.timeout(20000),
    });

    if (!r.ok) throw new Error(`Jina returned ${r.status}`);
    const content = await r.text();

    const titleMatch = content.match(/^#\s+(.+)$/m) || content.match(/^Title:\s*(.+)$/m);
    const title = titleMatch ? titleMatch[1].trim() : new URL(url).hostname;

    res.json({ content, title });
  } catch (err) {
    res.status(502).json({ error: 'Could not fetch page content', detail: err.message });
  }
});

app.post('/api/orient', async (req, res) => {
  const { trail, query } = req.body;
  if (!ANTHROPIC_KEY) return res.json({ tensions: [], paths: [], questions: [] });

  const trailText = (trail || []).slice(-6).map((s, i) =>
    `${i + 1}. [${s.source}] ${s.title}${s.snippet ? ' — ' + s.snippet.slice(0, 100) : ''}`
  ).join('\n');

  const prompt = `The user is exploring: "${query}"

Their inquiry trail:
${trailText || '(just started)'}

Provide ambient orientation — NOT a summary. Surface what's beneath the surface.

Return JSON exactly:
{
  "tensions": ["short tension 1", "short tension 2"],
  "paths": ["unexplored path 1", "unexplored path 2", "unexplored path 3"],
  "questions": ["question 1", "question 2", "question 3"]
}

Rules:
- tensions: real contradictions or debates in this domain (2 max, under 12 words each)
- paths: adjacent directions the user hasn't gone yet (3 max, under 10 words each)
- questions: genuinely interesting questions this exploration raises (3 max, under 15 words each)
- Do not summarize what they've read. Point forward and sideways, not backward.
- Be specific, not generic.`;

  try {
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': ANTHROPIC_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 400,
        messages: [{ role: 'user', content: prompt }],
      }),
      signal: AbortSignal.timeout(12000),
    });

    const d = await r.json();
    const text = d.content?.[0]?.text || '';
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error('No JSON in response');
    const parsed = JSON.parse(jsonMatch[0]);
    res.json({
      tensions: parsed.tensions || [],
      paths: parsed.paths || [],
      questions: parsed.questions || [],
    });
  } catch {
    res.json({ tensions: [], paths: [], questions: [] });
  }
});

app.post('/api/glance', async (req, res) => {
  const { url, title, snippet } = req.body;
  if (!ANTHROPIC_KEY) return res.json({ glance: snippet || '' });

  try {
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': ANTHROPIC_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 80,
        messages: [{
          role: 'user',
          content: `In one sentence (max 20 words), what is the essential point of this source?\n\nTitle: ${title}\nSnippet: ${snippet}\nURL: ${url}`,
        }],
      }),
      signal: AbortSignal.timeout(8000),
    });
    const d = await r.json();
    res.json({ glance: d.content?.[0]?.text?.trim() || snippet || '' });
  } catch {
    res.json({ glance: snippet || '' });
  }
});

app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'index.html')));

app.listen(PORT, () => console.log(`Arca running on http://localhost:${PORT}`));
