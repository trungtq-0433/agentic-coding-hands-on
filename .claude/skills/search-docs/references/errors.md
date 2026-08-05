# When Things Fail, and How to Recover

## Error Codes

**404 Not Found**
- No topic-specific URL for this library
- The library was never indexed on context7.com
- There simply is no llms.txt

**Timeout**
- The network is struggling
- A large repository is taking time to clone
- The API is answering slowly

**Invalid Response**
- The llms.txt came back malformed
- The body was empty
- The URLs inside it don't parse

## Fallback Chain

### For Topic-Specific Queries

```
1. Try topic-specific URL
   https://context7.com/{library}/llms.txt?topic={keyword}
   ↓ 404
2. Try general library URL
   https://context7.com/{library}/llms.txt
   ↓ 404
3. WebSearch for llms.txt
   "[library] llms.txt site:[official domain]"
   ↓ Not found
4. Repository analysis
   Use Repomix on GitHub repo
```

### For General Library Queries

```
1. Try context7.com
   https://context7.com/{library}/llms.txt
   ↓ 404
2. WebSearch for llms.txt
   "[library] llms.txt"
   ↓ Not found
3. Repository analysis
   Clone + Repomix
   ↓ No repo
4. Research agents
   Deploy multiple Researcher agents
```

## Timeout Handling

**Caps to enforce:**
- WebFetch: 60s
- Repository clone: 5min
- Repomix: 10min

**Move on quickly:** once a method fails, don't keep retrying it — drop down the chain.

## Empty Results

**When llms.txt comes back with no URLs:**
→ Record it in the report
→ Fall back to repository analysis
→ Open the official website and check by hand
