'use strict';
const express = require('express');
const path = require('path');
const app = express();

app.use(express.json({ limit: '10mb' }));
app.use(express.static(path.join(__dirname, 'public')));

const SERPER_KEY = process.env.SERPER_API_KEY || '';
const CLAUDE_KEY = process.env.CLAUDE_API_KEY || '';
const PORT       = process.env.PORT || 3000;

const SOURCES = {
  google:           { symbol: '🔵', label: 'Google',           color: 'blue'   },
  reddit:           { symbol: '🟠', label: 'Reddit',           color: 'amber'  },
  hackernews:       { symbol: '🟡', label: 'Hacker News',      color: 'amber'  },
  pubmed:           { symbol: '🔬', label: 'PubMed',           color: 'green'  },
  semantic_scholar: { symbol: '📚', label: 'Semantic Scholar',  color: 'green'  },
  arxiv:            { symbol: '📄', label: 'arXiv',            color: 'green'  },
  stackexchange:    { symbol: '🟤', label: 'StackExchange',    color: 'gray'   },
  wikipedia:        { symbol: '📖', label: 'Wikipedia',        color: 'gray'   },
  github:           { symbol: '⚫', label: 'GitHub',           color: 'gray'   },
  gdelt:            { symbol: '🌍', label: 'News',             color: 'blue'   },
  openlibrary:      { symbol: '📕', label: 'Open Library',     color: 'purple' },
  marginalia:       { symbol: '🕸',  label: 'Independent Web',  color: 'purple' },
  youtube:          { symbol: '▶',  label: 'YouTube',          color: 'red'    },
  archive:          { symbol: '📼', label: 'Internet Archive', color: 'gray'   },
  ted:              { symbol: '🎤', label: 'TED',              color: 'red'    },
};

const PROFILE_WEIGHTS = {
  General:   { google:1.0, reddit:0.8, hackernews:0.7, pubmed:0.5, semantic_scholar:0.5, arxiv:0.5, stackexchange:0.7, wikipedia:0.9, github:0.5, marginalia:0.7 },
  Student:   { google:0.9, reddit:0.9, hackernews:0.7, pubmed:0.7, semantic_scholar:0.9, arxiv:0.8, stackexchange:0.8, wikipedia:1.0, github:0.6, marginalia:0.8 },
  Medical:   { google:0.7, reddit:0.6, hackernews:0.4, pubmed:1.5, semantic_scholar:1.3, arxiv:1.1, stackexchange:0.5, wikipedia:0.7, github:0.2, marginalia:0.4 },
  Developer: { google:0.8, reddit:0.9, hackernews:1.3, pubmed:0.2, semantic_scholar:0.6, arxiv:0.7, stackexchange:1.4, wikipedia:0.7, github:1.5, marginalia:0.8 },
  Research:  { google:0.7, reddit:0.5, hackernews:0.8, pubmed:1.4, semantic_scholar:1.5, arxiv:1.4, stackexchange:0.6, wikipedia:0.8, github:0.6, marginalia:0.7 },
};

async function get(url, headers = {}, timeout = 10000) {
  try {
    const r = await fetch(url, { headers, signal: AbortSignal.timeout(timeout) });
    if (!r.ok) return null;
    return r.json();
  } catch { return null; }
}

async function getText(url, headers = {}, timeout = 10000) {
  try {
    const r = await fetch(url, { headers, signal: AbortSignal.timeout(timeout) });
    if (!r.ok) return null;
    return r.text();
  } catch { return null; }
}

async function serperSearch(query, num = 10, start = 0, type = 'search') {
  const body = { q: query, num, hl: 'en' };
  if (start > 0) body.start = start;
  const r = await fetch(`https://google.serper.dev/${type}`, {
    method: 'POST',
    headers: { 'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!r.ok) throw new Error(`Serper ${r.status}`);
  return r.json();
}

async function claude(prompt, maxTokens = 3000) {
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': CLAUDE_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({ model: 'claude-haiku-4-5-20251001', max_tokens: maxTokens, messages: [{ role: 'user', content: prompt }] })
  });
  if (!r.ok) throw new Error(`Claude ${r.status}`);
  const d = await r.json();
  return d.content[0].text.trim().replace(/^```json\s*/i,'').replace(/^```\s*/i,'').replace(/\s*```$/i,'');
}

async function jinaFetch(url) {
  try {
    const r = await fetch(`https://r.jina.ai/${url}`, { headers:{'Accept':'text/plain'}, signal: AbortSignal.timeout(14000) });
    return (await r.text()).slice(0, 5000);
  } catch { return ''; }
}

function safeJson(raw, fallback = {}) { try { return JSON.parse(raw); } catch { return fallback; } }
function getDomain(url) { try { return new URL(url).hostname.replace('www.',''); } catch { return url; } }

function getQueryTerms(query) {
  const stopwords = new Set(['the','a','an','is','in','on','at','to','for','of','and','or','with','by','from','how','what','when','where','who','why','can','do','does','did','be','been','are','was','were','i','my','me','we','you','it','its']);
  return query.toLowerCase().replace(/[^\w\s]/g,' ').split(/\s+/).filter(t => t.length > 2 && !stopwords.has(t));
}

function relevanceScore(result, queryTerms) {
  if (!queryTerms.length) return 1;
  const text = (result.title + ' ' + result.snippet).toLowerCase();
  const matched = queryTerms.filter(t => text.includes(t));
  return matched.length / queryTerms.length;
}

function mkResult(title, url, snippet, source, extra = {}) {
  const m = SOURCES[source] || SOURCES.google;
  return { title:title?.trim()||'', url:url?.trim()||'', snippet:snippet?.trim()||'', displayUrl:getDomain(url), source, sourceMarker:m.symbol, sourceLabel:m.label, sourceColor:m.color, tags:[], isVideo:false, ...extra };
}

async function expandQuery(query, location) {
  const locationCtx = location ? ` Location context: ${location}.` : '';
  const raw = await claude(`You are a search query engineer.${locationCtx}
User query: "${query}"
Generate exactly 5 Google search query variants. Return ONLY a JSON array of 5 strings.`, 400);
  try {
    const variants = JSON.parse(raw);
    if (Array.isArray(variants) && variants.length >= 3) return variants.slice(0, 5);
  } catch {}
  return [
    query,
    `${query} "experience" OR "review" OR "honest"`,
    `${query} site:reddit.com OR site:quora.com`,
    `${query} -inurl:booking -inurl:shop`,
    query
  ];
}

function detectIntents(query) {
  const q = query.toLowerCase();
  const intents = new Set();
  if (/symptom|disease|medical|health|drug|treatment|diagnosis|medicine|cancer|pain|virus/.test(q)) intents.add('medical');
  if (/research|paper|study|journal|academic|university|thesis|scholar|phd|science/.test(q)) intents.add('academic');
  if (/job|work|career|hiring|salary|employ|internship|resume|cv|vacancy/.test(q)) intents.add('jobs');
  if (/code|programming|developer|software|api|javascript|python|github|library|framework/.test(q)) intents.add('tech');
  if (/travel|visit|trip|hotel|flight|visa|tourist|expat|moving|living in/.test(q)) intents.add('travel');
  if (/book|novel|author|read|literature|fiction/.test(q)) intents.add('books');
  if (/news|latest|today|breaking|current|recent/.test(q)) intents.add('news');
  if (/how to|tutorial|watch|video|explained|guide/.test(q)) intents.add('video');
  if (intents.size === 0) intents.add('general');
  return [...intents];
}

async function fetchGoogle5Calls(query, location) {
  const variants = await expandQuery(query, location);
  const results = await Promise.all(variants.map(v => serperSearch(v, 10, 0).catch(() => ({ organic: [] }))));
  const seen = new Set();
  return results.flatMap(r => (r.organic||[]))
    .filter(r => { if (!r.link||seen.has(r.link)) return false; seen.add(r.link); return true; })
    .map(r => mkResult(r.title, r.link, r.snippet||'', 'google'));
}

async function fetchReddit(query, terms) {
  try {
    const d = await get(`https://www.reddit.com/search.json?q=${encodeURIComponent(query)}&sort=relevance&limit=20&type=link`, {'User-Agent':'Arca-Search/1.0'});
    if (!d?.data?.children) return [];
    return d.data.children
      .map(c => { const p=c.data; return mkResult(p.title, `https://reddit.com${p.permalink}`, p.selftext?.slice(0,200)||'', 'reddit', {upvotes:p.score,comments:p.num_comments}); })
      .filter(r => relevanceScore(r, terms) >= 0.3);
  } catch { return []; }
}

async function fetchHN(query, terms) {
  try {
    const d = await get(`https://hn.algolia.com/api/v1/search?query=${encodeURIComponent(query)}&tags=story&hitsPerPage=10&numericFilters=points>5`);
    if (!d?.hits) return [];
    return d.hits.filter(h=>h.url||h.story_text)
      .map(h => mkResult(h.title, h.url||`https://news.ycombinator.com/item?id=${h.objectID}`, h.story_text?.slice(0,200)||'', 'hackernews', {points:h.points}))
      .filter(r => relevanceScore(r, terms) >= 0.25);
  } catch { return []; }
}

async function fetchWikipedia(query, terms) {
  try {
    const d = await get(`https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(query)}&srlimit=4&format=json&origin=*`);
    if (!d?.query?.search) return [];
    return d.query.search
      .map(r => mkResult(r.title, `https://en.wikipedia.org/wiki/${encodeURIComponent(r.title.replace(/ /g,'_'))}`, r.snippet?.replace(/<[^>]+>/g,'')||'', 'wikipedia'))
      .filter(r => relevanceScore(r, terms) >= 0.35);
  } catch { return []; }
}

async function fetchMarginalia(query, terms) {
  try {
    const d = await get(`https://api.marginalia.nu/public/api/search/${encodeURIComponent(query)}?count=8`);
    if (!d?.results) return [];
    return d.results
      .map(r => mkResult(r.title||r.url, r.url, r.description||'', 'marginalia'))
      .filter(r => r.url && relevanceScore(r, terms) >= 0.15);
  } catch { return []; }
}

async function fetchPubMed(query, terms) {
  try {
    const search = await get(`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=${encodeURIComponent(query)}&retmax=6&sort=relevance&retmode=json`);
    if (!search?.esearchresult?.idlist?.length) return [];
    const ids = search.esearchresult.idlist.join(',');
    const summary = await get(`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=${ids}&retmode=json`);
    if (!summary?.result) return [];
    return Object.values(summary.result).filter(r=>r.uid&&r.title)
      .map(r => mkResult(r.title, `https://pubmed.ncbi.nlm.nih.gov/${r.uid}/`, `${r.source||''} ${r.pubdate||''}`, 'pubmed', {journal:r.source,year:r.pubdate?.slice(0,4)}))
      .filter(r => relevanceScore(r, terms) >= 0.2);
  } catch { return []; }
}

async function fetchSemanticScholar(query, terms) {
  try {
    const d = await get(`https://api.semanticscholar.org/graph/v1/paper/search?query=${encodeURIComponent(query)}&limit=6&fields=title,abstract,year,authors,url,citationCount`);
    if (!d?.data) return [];
    return d.data.filter(p=>p.title)
      .map(p => mkResult(p.title, p.url||`https://www.semanticscholar.org/paper/${p.paperId}`, p.abstract?.slice(0,200)||'', 'semantic_scholar', {year:p.year,citations:p.citationCount}))
      .filter(r => relevanceScore(r, terms) >= 0.2);
  } catch { return []; }
}

async function fetchArxiv(query, terms) {
  try {
    const xml = await getText(`https://export.arxiv.org/api/query?search_query=all:${encodeURIComponent(query)}&max_results=5&sortBy=relevance`);
    if (!xml) return [];
    const entries = xml.match(/<entry>([\s\S]*?)<\/entry>/g)||[];
    return entries.map(e => {
      const title = e.match(/<title>([\s\S]*?)<\/title>/)?.[1]?.trim().replace(/\n/g,' ')||'';
      const summary = e.match(/<summary>([\s\S]*?)<\/summary>/)?.[1]?.trim().slice(0,200)||'';
      const link = e.match(/<id>([\s\S]*?)<\/id>/)?.[1]?.trim()||'';
      const year = e.match(/<published>([\s\S]*?)<\/published>/)?.[1]?.slice(0,4)||'';
      return mkResult(title, link, summary, 'arxiv', {year});
    }).filter(r=>r.title&&r.url&&relevanceScore(r,terms)>=0.2);
  } catch { return []; }
}

async function fetchStackExchange(query, terms, site='stackoverflow') {
  try {
    const d = await get(`https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance&q=${encodeURIComponent(query)}&site=${site}&pagesize=6&filter=withbody`);
    if (!d?.items) return [];
    return d.items
      .map(i => mkResult(i.title, i.link, i.body?.replace(/<[^>]+>/g,'').slice(0,200)||'', 'stackexchange', {score:i.score,answers:i.answer_count,site}))
      .filter(r => relevanceScore(r, terms) >= 0.25);
  } catch { return []; }
}

async function fetchGitHub(query, terms) {
  try {
    const [repos, issues] = await Promise.all([
      get(`https://api.github.com/search/repositories?q=${encodeURIComponent(query)}&sort=stars&per_page=4`, {'Accept':'application/vnd.github.v3+json','User-Agent':'Arca-Search/1.0'}),
      get(`https://api.github.com/search/issues?q=${encodeURIComponent(query)}&sort=relevance&per_page=3`, {'Accept':'application/vnd.github.v3+json','User-Agent':'Arca-Search/1.0'})
    ]);
    const r1 = (repos?.items||[]).map(r=>mkResult(r.full_name,r.html_url,r.description||'','github',{stars:r.stargazers_count,language:r.language})).filter(r=>relevanceScore(r,terms)>=0.25);
    const r2 = (issues?.items||[]).map(r=>mkResult(r.title,r.html_url,r.body?.slice(0,200)||'','github')).filter(r=>relevanceScore(r,terms)>=0.3);
    return [...r1,...r2];
  } catch { return []; }
}

async function fetchGDELT(query, terms) {
  try {
    const d = await get(`https://api.gdeltproject.org/api/v2/doc/doc?query=${encodeURIComponent(query)}&mode=artlist&maxrecords=8&format=json&sort=relevance`);
    if (!d?.articles) return [];
    return d.articles
      .map(a=>mkResult(a.title,a.url,`${a.domain} — ${a.seendate?.slice(0,8)||''}`, 'gdelt',{domain:a.domain}))
      .filter(r=>r.title&&r.url&&relevanceScore(r,terms)>=0.25);
  } catch { return []; }
}

async function fetchOpenLibrary(query, terms) {
  try {
    const d = await get(`https://openlibrary.org/search.json?q=${encodeURIComponent(query)}&limit=5&fields=title,author_name,first_publish_year,key`);
    if (!d?.docs) return [];
    return d.docs
      .map(r=>mkResult(r.title,`https://openlibrary.org${r.key}`,`By ${(r.author_name||[]).slice(0,2).join(', ')} (${r.first_publish_year||'?'})`,'openlibrary'))
      .filter(r=>relevanceScore(r,terms)>=0.3);
  } catch { return []; }
}

async function fetchYouTube(query) {
  try {
    const d = await serperSearch(query, 8, 0, 'videos').catch(()=>null);
    if (!d?.videos) return [];
    return d.videos.map(v => mkResult(v.title, v.link, v.snippet||'', 'youtube', {
      isVideo:true, thumbnail:v.imageUrl||null, duration:v.duration||null, channel:v.channel||null
    }));
  } catch { return []; }
}

async function fetchTED(query, terms) {
  try {
    const d = await get(`https://api.ted.com/v1/talks.json?api-key=&q=${encodeURIComponent(query)}&limit=4`);
    if (!d?.talks) return [];
    return d.talks
      .map(t=>mkResult(t.name,t.canonical_url||`https://ted.com/talks/${t.slug}`,t.description?.slice(0,200)||'','ted',{isVideo:true}))
      .filter(r=>relevanceScore(r,terms)>=0.2);
  } catch { return []; }
}

async function fetchAllSources(query, profile='General', location=null) {
  const terms = getQueryTerms(query);
  const intents = detectIntents(query);
  const weights = PROFILE_WEIGHTS[profile] || PROFILE_WEIGHTS.General;
  const enrichedQuery = location ? `${query} ${location}` : query;

  console.log(`[sources] "${query}" | profile:${profile} | intents:${intents.join(',')}`);

  const always = [
    fetchGoogle5Calls(enrichedQuery, location),
    fetchReddit(query, terms),
    fetchHN(query, terms),
    fetchWikipedia(query, terms),
    fetchMarginalia(query, terms),
  ];

  const conditional = [];
  if (intents.includes('medical')) { conditional.push(fetchPubMed(query,terms)); conditional.push(fetchStackExchange(query,terms,'health')); }
  if (intents.includes('academic')) { conditional.push(fetchSemanticScholar(query,terms)); conditional.push(fetchArxiv(query,terms)); }
  if (intents.includes('tech')) { conditional.push(fetchGitHub(query,terms)); conditional.push(fetchStackExchange(query,terms,'stackoverflow')); }
  if (intents.includes('jobs')) { conditional.push(fetchStackExchange(query,terms,'workplace')); }
  if (intents.includes('travel')) { conditional.push(fetchStackExchange(query,terms,'travel')); }
  if (intents.includes('books')) { conditional.push(fetchOpenLibrary(query,terms)); }
  if (intents.includes('news')||intents.includes('general')) { conditional.push(fetchGDELT(query,terms)); }
  if (intents.includes('academic')||intents.includes('general')) { conditional.push(fetchSemanticScholar(query,terms)); }

  const videoFetchers = [fetchYouTube(query), fetchTED(query,terms)];

  const allBatches = await Promise.all([...always,...conditional,...videoFetchers]);
  const allRaw = allBatches.flat().filter(r=>r.title&&r.url);

  const seen = new Set();
  const unique = allRaw.filter(r => { if(seen.has(r.url)) return false; seen.add(r.url); return true; });

  const scored = unique.map(r => ({
    ...r,
    _score: relevanceScore(r, terms) * (weights[r.source] || 0.7)
  }));

  scored.sort((a,b) => {
    if (a.source==='google'&&b.source!=='google') return -1;
    if (b.source==='google'&&a.source!=='google') return 1;
    return b._score - a._score;
  });

  const videos = scored.filter(r=>r.isVideo);
  const nonVideos = scored.filter(r=>!r.isVideo);

  const breakdown = {};
  for (const r of scored) { const k=r.sourceLabel; breakdown[k]=(breakdown[k]||0)+1; }

  console.log(`[sources] ${scored.length} results (${videos.length} videos)`);
  return { results:nonVideos, videos, intents, breakdown };
}

app.get('/api/config', (_req,res) => res.json({ serper:!!SERPER_KEY, claude:!!CLAUDE_KEY }));

app.post('/api/search', async (req,res) => {
  const { query, profile='General', location=null } = req.body;
  if (!query?.trim()) return res.status(400).json({ error:'Query required' });
  const q = query.trim();

  try {
    const { results, videos, intents, breakdown } = await fetchAllSources(q, profile, location);
    const top = results.slice(0,40);
    const topVideos = videos.slice(0,8);
    const resultsList = top.map((r,i)=>`[${i}] [${r.sourceLabel}] "${r.title}" | ${r.snippet.slice(0,100)} | ${r.url}`).join('\n');

    const prompt = `Search engine. Query: "${q}" | Profile: ${profile} | Intents: ${intents.join(',')}

Results:
${resultsList}

Create 4-6 semantic lanes. Classify ALL ${top.length} results. Give 2-3 tags per result.
Tag colors: blue=info, green=positive/official, amber=community, purple=research, red=warning, gray=neutral.
Generate 5 refine options as filter dimensions.
Answer card: 2-3 concrete sentences.

Return ONLY minified JSON:
{"answerCard":{"title":"title","summary":"summary","sources":["d1","d2"],"readingTime":"X min","sourceCount":${top.length}},"refineOptions":[{"label":"Label","options":["opt1","opt2","opt3"]}],"lanes":[{"id":"id","label":"Label","icon":"emoji","results":[{"index":0,"tags":[{"label":"tag","color":"blue"}]}]}]}`;

    const aiRaw = await claude(prompt, 4500);
    const ai = safeJson(aiRaw, { answerCard:{title:q,summary:''},refineOptions:[],lanes:[] });

    const classified = new Set();
    const lanes = [];
    for (const lane of (ai.lanes||[])) {
      const laneResults = [];
      for (const item of (lane.results||[])) {
        const r = top[item.index];
        if (!r||classified.has(item.index)) continue;
        classified.add(item.index);
        laneResults.push({...r, tags:item.tags||[]});
      }
      if (laneResults.length) lanes.push({ id:lane.id||lane.label.toLowerCase().replace(/\s+/g,'-'), label:lane.label, icon:lane.icon||'🌐', results:laneResults });
    }

    const unclassified = top.filter((_,i)=>!classified.has(i));
    if (unclassified.length && lanes.length) lanes[0].results.push(...unclassified.map(r=>({...r,tags:[]})));
    else if (unclassified.length) lanes.push({id:'results',label:'Results',icon:'🌐',results:unclassified.map(r=>({...r,tags:[]}))});

    if (topVideos.length) lanes.push({ id:'videos', label:'Videos', icon:'▶', results:topVideos, isVideoLane:true });

    res.json({
      query:q, profile, intents, location,
      answerCard: ai.answerCard||{title:q,summary:''},
      refineOptions: ai.refineOptions||[],
      lanes,
      sourceBreakdown: breakdown
    });

  } catch(err) {
    console.error('[search]', err.message);
    res.status(500).json({ error:err.message });
  }
});

app.post('/api/context-chat', async (req, res) => {
  const { sources, query, question } = req.body;
  if (!sources?.length || !question?.trim()) return res.status(400).json({ error: 'Sources and question required' });
  try {
    const contents = await Promise.all(
      sources.slice(0, 10).map(s => jinaFetch(s.url).then(t => t || s.snippet || ''))
    );
    const txt = sources.slice(0, 10).map((s, i) =>
      `SOURCE ${i+1} [${s.sourceLabel || s.displayUrl || 'Web'}] — ${s.title}:\n${contents[i].slice(0, 2000)}`
    ).join('\n\n---\n\n');
    const answer = await claude(
      `Answer the following question based ONLY on the provided sources. Keep your answer under 200 words. Reference sources by number when relevant.\n\nSearch context: "${query}"\nQuestion: "${question}"\n\n${txt}\n\nAnswer:`,
      800
    );
    res.json({ answer });
  } catch(err) { res.status(500).json({ error: err.message }); }
});

app.post('/api/glance', async (req,res) => {
  const { url, query, profile='General', snippet='' } = req.body;
  if (!url) return res.status(400).json({ error:'URL required' });
  try {
    let content = '';
    if (url.includes('reddit.com')) {
      try {
        const jsonUrl = url.replace(/\/?$/, '.json?limit=5&sort=top');
        const d = await get(jsonUrl, {'User-Agent':'Arca-Search/1.0'});
        if (d?.[0]?.data?.children?.[0]) {
          const post = d[0].data.children[0].data;
          const comments = (d[1]?.data?.children||[]).slice(0,4).map(c=>c.data.body).filter(Boolean);
          content = `POST: ${post.title}\n${post.selftext?.slice(0,300)||''}\n\nTOP COMMENTS:\n${comments.map((c,i)=>`${i+1}. ${c.slice(0,200)}`).join('\n')}`;
        }
      } catch {}
    }
    if (!content) content = (await jinaFetch(url)) || snippet || 'No content available';
    const isReddit = url.includes('reddit.com');
    const summaryStyle = isReddit
      ? 'Give a vague thread summary. Do NOT reproduce comments verbatim.'
      : `Summarise for a ${profile} user searching "${query}". Extract direct answer if present, list 3 key points.`;
    const raw = await claude(`${summaryStyle}\n\nContent: ${content}\n\nReturn ONLY minified JSON:\n{"title":"title","directAnswer":"1-2 sentences or null","keyPoints":["p1","p2","p3"],"relevance":"high|medium|low","readTime":"X min read"}`, 600);
    res.json(safeJson(raw, {title:'Preview',keyPoints:[],directAnswer:null,relevance:'medium',readTime:'?'}));
  } catch(err) { res.status(500).json({ error:err.message }); }
});

app.listen(PORT, () => {
  console.log(`\n🔍  Arca Search  →  http://localhost:${PORT}\n`);
  if (!SERPER_KEY) console.warn('  ⚠️  SERPER_API_KEY not set');
  if (!CLAUDE_KEY) console.warn('  ⚠️  CLAUDE_API_KEY not set');
  console.log('  Sources: Google(5x) · Reddit · HN · Wikipedia · Marginalia + intent-based\n');
});