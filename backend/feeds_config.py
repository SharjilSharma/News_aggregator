"""All data source configurations for NeuroPulse — multi-domain AI intelligence aggregator.

Source types:
  rss       — Standard RSS/Atom feed
  reddit    — Reddit JSON API
  github    — GitHub Trending HTML scrape
  hf_models — HuggingFace Models API (AI domain only)

Domains:
  ai          — AI & Machine Learning
  cybersec    — Cybersecurity & Infosec
  finance     — Finance & FinTech
  biotech     — Biotech & Health
  web3        — Web3 & Blockchain
"""

# ── Auto-refresh interval (2 hours) ─────────────────────────────────────────
REFRESH_INTERVAL_MINUTES = 120

# ── Domain Metadata (for UI) ─────────────────────────────────────────────────
DOMAIN_META = {
    "ai": {
        "label": "AI & Machine Learning",
        "icon": "🤖",
        "color": "#7c3aed",
        "description": "Models, research papers, company releases & breakthroughs",
    },
    "cybersec": {
        "label": "Cybersecurity",
        "icon": "🛡️",
        "color": "#ef4444",
        "description": "Vulnerabilities, exploits, threat intelligence & infosec news",
    },
    "finance": {
        "label": "Finance & FinTech",
        "icon": "📈",
        "color": "#10b981",
        "description": "Markets, fintech startups, banking tech & economic trends",
    },
    "biotech": {
        "label": "Biotech & Health",
        "icon": "🧬",
        "color": "#06b6d4",
        "description": "Drug trials, genomics, medical AI & life sciences research",
    },
    "web3": {
        "label": "Web3 & Blockchain",
        "icon": "⛓️",
        "color": "#f59e0b",
        "description": "Crypto, DeFi, NFTs, protocol updates & blockchain tech",
    },
}

# ── AI & Machine Learning ─────────────────────────────────────────────────────
DOMAIN_AI = [
    # AI Lab Blogs (Official)
    {"url": "https://openai.com/blog/rss.xml",                     "name": "OpenAI Blog",       "type": "rss"},
    {"url": "https://deepmind.google/blog/rss.xml",                "name": "DeepMind Blog",     "type": "rss"},
    {"url": "https://www.anthropic.com/rss.xml",                   "name": "Anthropic Blog",    "type": "rss"},
    {"url": "https://ai.meta.com/blog/rss/",                       "name": "Meta AI Blog",      "type": "rss"},
    {"url": "https://ai.googleblog.com/feeds/posts/default",       "name": "Google AI Blog",    "type": "rss"},
    {"url": "https://mistral.ai/news/rss",                         "name": "Mistral Blog",      "type": "rss"},
    {"url": "https://stability.ai/news/rss.xml",                   "name": "Stability AI",      "type": "rss"},
    {"url": "https://blogs.microsoft.com/ai/feed/",                "name": "Microsoft AI",      "type": "rss"},
    {"url": "https://aws.amazon.com/blogs/machine-learning/feed/", "name": "AWS ML Blog",       "type": "rss"},
    {"url": "https://blog.xai.com/rss",                            "name": "xAI (Grok) Blog",  "type": "rss"},
    {"url": "https://www.cohere.com/blog/rss.xml",                 "name": "Cohere Blog",       "type": "rss"},
    # AI-Focused Tech News
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/",         "name": "TechCrunch AI",     "type": "rss"},
    {"url": "https://venturebeat.com/category/ai/feed/",                             "name": "VentureBeat AI",    "type": "rss"},
    {"url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",     "name": "The Verge AI",      "type": "rss"},
    {"url": "https://www.wired.com/feed/category/artificial-intelligence/latest/rss","name": "Wired AI",          "type": "rss"},
    {"url": "https://www.technologyreview.com/topic/artificial-intelligence/feed",   "name": "MIT Tech Review AI","type": "rss"},
    {"url": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",           "name": "ZDNet AI",          "type": "rss"},
    {"url": "https://thenextweb.com/feed/",                                          "name": "The Next Web",      "type": "rss"},
    # AI Newsletters
    {"url": "https://read.deeplearning.ai/the-batch/rss/",   "name": "The Batch (DeepLearning.AI)", "type": "rss"},
    {"url": "https://importai.substack.com/feed",             "name": "Import AI",              "type": "rss"},
    {"url": "https://thesequence.substack.com/feed",          "name": "The Sequence",           "type": "rss"},
    {"url": "https://aisnakeoil.substack.com/feed",           "name": "AI Snake Oil",           "type": "rss"},
    {"url": "https://tldr.tech/ai/rss",                       "name": "TLDR AI",                "type": "rss"},
    {"url": "https://lastweekinai.substack.com/feed",         "name": "Last Week in AI",        "type": "rss"},
    # Research
    {"url": "https://arxiv.org/rss/cs.AI",                    "name": "arXiv AI",               "type": "rss"},
    {"url": "https://arxiv.org/rss/cs.LG",                    "name": "arXiv ML",               "type": "rss"},
    {"url": "https://arxiv.org/rss/cs.CL",                    "name": "arXiv NLP",              "type": "rss"},
    {"url": "https://paperswithcode.com/latest.rss",          "name": "Papers With Code",       "type": "rss"},
    {"url": "https://huggingface.co/papers.rss",              "name": "HuggingFace Papers",     "type": "rss"},
    # Policy & Ethics
    {"url": "https://futureoflife.org/feed/",                 "name": "Future of Life",         "type": "rss"},
    {"url": "https://hai.stanford.edu/news/feed",             "name": "Stanford HAI",           "type": "rss"},
    # Infra & Hardware
    {"url": "https://semiengineering.com/feed/",              "name": "SemiEngineering",        "type": "rss"},
    {"url": "https://www.tomshardware.com/feeds/all",         "name": "Tom's Hardware",         "type": "rss"},
    # Reddit
    {"url": "https://www.reddit.com/r/MachineLearning/.json?limit=15&sort=hot",  "name": "r/MachineLearning", "type": "reddit"},
    {"url": "https://www.reddit.com/r/artificial/.json?limit=15&sort=hot",       "name": "r/artificial",      "type": "reddit"},
    {"url": "https://www.reddit.com/r/LocalLLaMA/.json?limit=15&sort=hot",       "name": "r/LocalLLaMA",      "type": "reddit"},
    # GitHub Trending
    {"url": "https://github.com/trending?since=daily&spoken_language_code=en",   "name": "GitHub Trending",   "type": "github"},
]

# ── Cybersecurity ─────────────────────────────────────────────────────────────
DOMAIN_CYBERSEC = [
    # Security News
    {"url": "https://feeds.feedburner.com/TheHackersNews",              "name": "The Hacker News",      "type": "rss"},
    {"url": "https://krebsonsecurity.com/feed/",                        "name": "Krebs on Security",    "type": "rss"},
    {"url": "https://www.bleepingcomputer.com/feed/",                   "name": "BleepingComputer",     "type": "rss"},
    {"url": "https://www.darkreading.com/rss.xml",                      "name": "Dark Reading",         "type": "rss"},
    {"url": "https://www.securityweek.com/feed",                        "name": "Security Week",        "type": "rss"},
    {"url": "https://isc.sans.edu/rssfeed.xml",                         "name": "SANS Internet Storm",  "type": "rss"},
    {"url": "https://feeds.feedburner.com/Securityweek",               "name": "SecurityWeek Feed",    "type": "rss"},
    {"url": "https://www.csoonline.com/feed/",                          "name": "CSO Online",           "type": "rss"},
    {"url": "https://www.infosecurity-magazine.com/rss/news/",         "name": "Infosecurity Mag",     "type": "rss"},
    {"url": "https://portswigger.net/daily-swig/rss",                   "name": "The Daily Swig",       "type": "rss"},
    {"url": "https://feeds.feedburner.com/NakedSecurity",              "name": "Naked Security (Sophos)","type": "rss"},
    {"url": "https://googleprojectzero.blogspot.com/feeds/posts/default","name":"Google Project Zero",  "type": "rss"},
    {"url": "https://blog.cloudflare.com/rss/",                        "name": "Cloudflare Blog",      "type": "rss"},
    # CVE / Vulnerability feeds
    {"url": "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml",    "name": "NVD CVE Feed",         "type": "rss"},
    # Reddit
    {"url": "https://www.reddit.com/r/netsec/.json?limit=15&sort=hot",     "name": "r/netsec",        "type": "reddit"},
    {"url": "https://www.reddit.com/r/cybersecurity/.json?limit=15&sort=hot","name": "r/cybersecurity","type": "reddit"},
    {"url": "https://www.reddit.com/r/hacking/.json?limit=15&sort=hot",     "name": "r/hacking",      "type": "reddit"},
    # GitHub
    {"url": "https://github.com/trending?since=daily&spoken_language_code=en", "name": "GitHub Trending (Security)", "type": "github"},
]

# ── Finance & FinTech ─────────────────────────────────────────────────────────
DOMAIN_FINANCE = [
    # FinTech & Tech Finance News
    {"url": "https://techcrunch.com/category/fintech/feed/",            "name": "TechCrunch FinTech",  "type": "rss"},
    {"url": "https://venturebeat.com/category/financial-services/feed/","name": "VentureBeat Finance", "type": "rss"},
    {"url": "https://www.finextra.com/rss/headlines.aspx",              "name": "Finextra",            "type": "rss"},
    {"url": "https://www.pymnts.com/feed/",                             "name": "PYMNTS",              "type": "rss"},
    {"url": "https://www.fintechfutures.com/feed/",                     "name": "FinTech Futures",     "type": "rss"},
    {"url": "https://www.crowdfundinsider.com/feed/",                   "name": "Crowdfund Insider",   "type": "rss"},
    {"url": "https://bankinnovation.net/feed/",                         "name": "Bank Innovation",     "type": "rss"},
    # Bloomberg / Reuters Tech Finance
    {"url": "https://feeds.bloomberg.com/technology/news.rss",         "name": "Bloomberg Tech",      "type": "rss"},
    {"url": "https://feeds.reuters.com/reuters/businessNews",           "name": "Reuters Business",    "type": "rss"},
    # Newsletters
    {"url": "https://www.thefinancialbrand.com/feed/",                  "name": "The Financial Brand", "type": "rss"},
    {"url": "https://a16z.com/feed/",                                   "name": "a16z Blog",           "type": "rss"},
    # Reddit
    {"url": "https://www.reddit.com/r/fintech/.json?limit=15&sort=hot",    "name": "r/fintech",       "type": "reddit"},
    {"url": "https://www.reddit.com/r/investing/.json?limit=15&sort=hot",  "name": "r/investing",     "type": "reddit"},
    {"url": "https://www.reddit.com/r/stocks/.json?limit=10&sort=hot",     "name": "r/stocks",        "type": "reddit"},
    # GitHub
    {"url": "https://github.com/trending?since=daily&spoken_language_code=en", "name": "GitHub Trending (Finance)", "type": "github"},
]

# ── Biotech & Health ──────────────────────────────────────────────────────────
DOMAIN_BIOTECH = [
    # Biotech & Life Sciences News
    {"url": "https://www.statnews.com/feed/",                          "name": "STAT News",            "type": "rss"},
    {"url": "https://www.biospace.com/rss/news/",                      "name": "BioSpace",             "type": "rss"},
    {"url": "https://www.fiercebiotech.com/rss/xml",                   "name": "Fierce Biotech",       "type": "rss"},
    {"url": "https://www.nature.com/nm.rss",                           "name": "Nature Medicine",      "type": "rss"},
    {"url": "https://www.nature.com/nbt.rss",                          "name": "Nature Biotechnology", "type": "rss"},
    {"url": "https://www.science.org/rss/news_current.xml",            "name": "Science News",         "type": "rss"},
    # ArXiv for biology/medicine
    {"url": "https://arxiv.org/rss/q-bio",                             "name": "arXiv Quantitative Bio","type": "rss"},
    {"url": "https://arxiv.org/rss/cs.CE",                             "name": "arXiv Comp. Engineering","type": "rss"},
    # Medical AI
    {"url": "https://techcrunch.com/category/health/feed/",            "name": "TechCrunch Health",    "type": "rss"},
    {"url": "https://www.mobihealthnews.com/feed",                     "name": "MobiHealth News",      "type": "rss"},
    {"url": "https://medcitynews.com/feed/",                           "name": "MedCity News",         "type": "rss"},
    # Reddit
    {"url": "https://www.reddit.com/r/biology/.json?limit=15&sort=hot",   "name": "r/biology",        "type": "reddit"},
    {"url": "https://www.reddit.com/r/genetics/.json?limit=10&sort=hot",  "name": "r/genetics",       "type": "reddit"},
    {"url": "https://www.reddit.com/r/medicine/.json?limit=10&sort=hot",  "name": "r/medicine",       "type": "reddit"},
    # GitHub
    {"url": "https://github.com/trending?since=daily&spoken_language_code=en", "name": "GitHub Trending (Biotech)", "type": "github"},
]

# ── Web3 & Blockchain ─────────────────────────────────────────────────────────
DOMAIN_WEB3 = [
    # Crypto & Blockchain News
    {"url": "https://www.coindesk.com/arc/outboundfeeds/rss/",         "name": "CoinDesk",            "type": "rss"},
    {"url": "https://decrypt.co/feed",                                 "name": "Decrypt",             "type": "rss"},
    {"url": "https://cointelegraph.com/rss",                           "name": "CoinTelegraph",       "type": "rss"},
    {"url": "https://thedefiant.io/feed",                              "name": "The Defiant (DeFi)",  "type": "rss"},
    {"url": "https://www.theblockcrypto.com/rss.xml",                  "name": "The Block",           "type": "rss"},
    {"url": "https://blockworks.co/feed/",                             "name": "Blockworks",          "type": "rss"},
    {"url": "https://www.coinbureau.com/feed/",                        "name": "Coin Bureau",         "type": "rss"},
    # Protocol / Dev blogs
    {"url": "https://blog.ethereum.org/en/feed.xml",                   "name": "Ethereum Blog",       "type": "rss"},
    {"url": "https://solana.com/news/rss.xml",                         "name": "Solana News",         "type": "rss"},
    {"url": "https://medium.com/feed/uniswap-lab",                     "name": "Uniswap Blog",        "type": "rss"},
    # Newsletters
    {"url": "https://newsletter.banklesshq.com/feed",                  "name": "Bankless",            "type": "rss"},
    # Reddit
    {"url": "https://www.reddit.com/r/ethereum/.json?limit=15&sort=hot",    "name": "r/ethereum",    "type": "reddit"},
    {"url": "https://www.reddit.com/r/CryptoCurrency/.json?limit=10&sort=hot","name": "r/CryptoCurrency","type": "reddit"},
    {"url": "https://www.reddit.com/r/defi/.json?limit=10&sort=hot",        "name": "r/defi",        "type": "reddit"},
    # GitHub
    {"url": "https://github.com/trending?since=daily&spoken_language_code=en", "name": "GitHub Trending (Web3)", "type": "github"},
]

# ── Domain → Feed mapping ─────────────────────────────────────────────────────
DOMAIN_FEEDS = {
    "ai":       DOMAIN_AI,
    "cybersec": DOMAIN_CYBERSEC,
    "finance":  DOMAIN_FINANCE,
    "biotech":  DOMAIN_BIOTECH,
    "web3":     DOMAIN_WEB3,
}

# Default: all AI feeds (backward-compat with existing scheduler)
FEEDS = DOMAIN_AI

# ── Full-text extraction sources (AI domain) ──────────────────────────────────
EXTRACT_FULL_TEXT_SOURCES = {
    "TechCrunch AI", "The Verge AI", "Wired AI",
    "VentureBeat AI", "The Next Web",
    "ZDNet AI", "MIT Tech Review AI",
    "OpenAI Blog", "DeepMind Blog", "Google AI Blog", "Anthropic Blog",
    "Meta AI Blog", "Mistral Blog", "Stability AI",
    "Microsoft AI", "AWS ML Blog",
    "The Batch (DeepLearning.AI)", "Import AI", "The Sequence",
    "AI Snake Oil", "TLDR AI", "Last Week in AI",
    "Future of Life", "Stanford HAI", "Papers With Code",
    "xAI (Grok) Blog", "Cohere Blog",
    # Cybersec
    "Krebs on Security", "BleepingComputer", "Dark Reading",
    "SANS Internet Storm", "CSO Online",
    # Finance
    "TechCrunch FinTech", "Finextra", "a16z Blog",
    # Biotech
    "STAT News", "Fierce Biotech",
    # Web3
    "CoinDesk", "Decrypt", "CoinTelegraph", "Ethereum Blog",
}
